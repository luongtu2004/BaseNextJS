"""Unit tests for Phase 8 — Payment & Wallet.

Tests cover:
  - PaymentService: wallet CRUD, credit, debit, settlement, withdrawal, promotion validation
  - Customer Wallet API: GET wallet, transactions, topup, validate promotion, list promotions
  - Provider Wallet API: GET wallet, transactions, earnings, withdrawal
  - Admin Payment API: list wallets, adjust, approve/reject withdrawal, promotions CRUD
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token
from app.models.booking import Booking, CommissionConfig
from app.models.payment import (
    Promotion,
    PromotionUsage,
    Wallet,
    WalletTransaction,
)
from app.models.taxonomy import ServiceCategory
from tests.conftest import (
    auth_headers,
    create_provider,
    create_service_category,
    create_user,
    make_admin_token,
)


# ── Helpers ──────────────────────────────────────────────────────────

def make_customer_token(user) -> str:
    """Tạo JWT cho customer."""
    return create_access_token(str(user.id), ["customer"])


def make_provider_token(user) -> str:
    """Tạo JWT cho provider."""
    return create_access_token(str(user.id), ["provider_owner"])


async def seed_customer(db: AsyncSession):
    """Tạo customer user."""
    return await create_user(db, phone="+84111111111", role="customer")


async def seed_provider_pair(db: AsyncSession):
    """Tạo provider owner + provider record."""
    owner = await create_user(db, phone="+84222222222", role="provider_owner")
    provider = await create_provider(db, owner)
    return owner, provider


async def seed_admin(db: AsyncSession):
    """Tạo admin user."""
    return await create_user(db, phone="+84999999999", role="admin")


async def seed_commission_config(db: AsyncSession, service_type: str = "taxi"):
    """Tạo commission config."""
    config = CommissionConfig(
        id=uuid.uuid4(),
        service_type=service_type,
        rate_percent=20.0,
        fixed_fee=0,
        is_active=True,
        created_at=datetime.now(tz=timezone.utc),
        updated_at=datetime.now(tz=timezone.utc),
    )
    db.add(config)
    await db.flush()
    return config


async def seed_booking(
    db: AsyncSession,
    customer_id: uuid.UUID,
    provider_id: uuid.UUID,
    category_id: uuid.UUID,
    *,
    status: str = "completed",
    payment_method: str = "cash",
    final_fare: float = 100000,
):
    """Tạo booking cho test."""
    now = datetime.now(tz=timezone.utc)
    booking = Booking(
        id=uuid.uuid4(),
        customer_id=customer_id,
        provider_id=provider_id,
        service_category_id=category_id,
        service_type="taxi",
        pickup_address="123 Test Street",
        estimated_fare=final_fare,
        final_fare=final_fare,
        status=status,
        payment_method=payment_method,
        requested_at=now,
        completed_at=now if status == "completed" else None,
        created_at=now,
        updated_at=now,
    )
    db.add(booking)
    await db.flush()
    return booking


async def seed_promotion(
    db: AsyncSession,
    *,
    code: str = "TEST10",
    promo_type: str = "percent",
    value: float = 10,
    max_discount: float | None = None,
    min_fare: float | None = None,
    usage_limit: int | None = None,
    per_user_limit: int = 1,
    service_types: list | None = None,
    is_active: bool = True,
    valid_days: int = 30,
):
    """Tạo promotion cho test."""
    now = datetime.now(tz=timezone.utc)
    promo = Promotion(
        id=uuid.uuid4(),
        code=code,
        name=f"Test Promotion {code}",
        type=promo_type,
        value=value,
        max_discount=max_discount,
        min_fare=min_fare,
        usage_limit=usage_limit,
        per_user_limit=per_user_limit,
        valid_from=now - timedelta(days=1),
        valid_to=now + timedelta(days=valid_days),
        service_types=service_types,
        is_active=is_active,
        created_at=now,
        updated_at=now,
    )
    db.add(promo)
    await db.flush()
    return promo


# ═════════════════════════════════════════════════════════════════════
# 1. PaymentService — Unit Tests
# ═════════════════════════════════════════════════════════════════════

class TestPaymentServiceWallet:
    """Test get_or_create_wallet, credit_wallet, debit_wallet."""

    @pytest.mark.asyncio
    async def test_get_or_create_wallet_creates_new(self, db: AsyncSession):
        """Auto-create ví mới cho user chưa có ví."""
        from app.services.payment_service import PaymentService

        user = await seed_customer(db)
        await db.commit()

        wallet = await PaymentService.get_or_create_wallet(db, user.id)
        await db.commit()

        assert wallet is not None
        assert wallet.user_id == user.id
        assert float(wallet.balance) == 0
        assert wallet.currency == "VND"
        assert wallet.is_frozen is False

    @pytest.mark.asyncio
    async def test_get_or_create_wallet_idempotent(self, db: AsyncSession):
        """Gọi lại trả về cùng 1 ví."""
        from app.services.payment_service import PaymentService

        user = await seed_customer(db)
        await db.commit()

        w1 = await PaymentService.get_or_create_wallet(db, user.id)
        await db.commit()
        w2 = await PaymentService.get_or_create_wallet(db, user.id)
        await db.commit()

        assert w1.id == w2.id

    @pytest.mark.asyncio
    async def test_credit_wallet(self, db: AsyncSession):
        """Credit thành công, balance tăng."""
        from app.services.payment_service import PaymentService

        user = await seed_customer(db)
        await db.commit()
        wallet = await PaymentService.get_or_create_wallet(db, user.id)
        await db.commit()

        txn = await PaymentService.credit_wallet(
            db, wallet, 50000, txn_type="topup", description="Test topup",
        )
        await db.commit()

        assert txn.amount == 50000
        assert txn.type == "topup"
        assert txn.status == "completed"
        assert float(wallet.balance) == 50000

    @pytest.mark.asyncio
    async def test_credit_negative_amount_fails(self, db: AsyncSession):
        """Credit amount <= 0 phải fail."""
        from app.services.payment_service import PaymentService
        from fastapi import HTTPException

        user = await seed_customer(db)
        await db.commit()
        wallet = await PaymentService.get_or_create_wallet(db, user.id)
        await db.commit()

        with pytest.raises(HTTPException) as exc:
            await PaymentService.credit_wallet(db, wallet, -100, txn_type="topup")
        assert exc.value.status_code == 400

    @pytest.mark.asyncio
    async def test_debit_wallet_success(self, db: AsyncSession):
        """Debit thành công khi đủ số dư."""
        from app.services.payment_service import PaymentService

        user = await seed_customer(db)
        await db.commit()
        wallet = await PaymentService.get_or_create_wallet(db, user.id)
        await db.commit()

        await PaymentService.credit_wallet(db, wallet, 100000, txn_type="topup")
        await db.commit()
        txn = await PaymentService.debit_wallet(
            db, wallet, 30000, txn_type="payment", description="Test payment",
        )
        await db.commit()

        assert txn.amount == -30000
        assert float(wallet.balance) == 70000

    @pytest.mark.asyncio
    async def test_debit_insufficient_balance(self, db: AsyncSession):
        """Debit khi thiếu tiền phải fail (allow_negative=False)."""
        from app.services.payment_service import PaymentService
        from fastapi import HTTPException

        user = await seed_customer(db)
        await db.commit()
        wallet = await PaymentService.get_or_create_wallet(db, user.id)
        await db.commit()

        with pytest.raises(HTTPException) as exc:
            await PaymentService.debit_wallet(db, wallet, 50000, txn_type="payment")
        assert exc.value.status_code == 400
        assert "Insufficient" in str(exc.value.detail)

    @pytest.mark.asyncio
    async def test_debit_allow_negative(self, db: AsyncSession):
        """Debit allow_negative=True cho phép ví âm (commission cash)."""
        from app.services.payment_service import PaymentService

        user = await seed_customer(db)
        await db.commit()
        wallet = await PaymentService.get_or_create_wallet(db, user.id)
        await db.commit()

        txn = await PaymentService.debit_wallet(
            db, wallet, 20000, txn_type="commission", allow_negative=True,
        )
        await db.commit()

        assert float(wallet.balance) == -20000
        assert txn.amount == -20000

    @pytest.mark.asyncio
    async def test_frozen_wallet_blocks_operations(self, db: AsyncSession):
        """Ví bị frozen không cho credit/debit."""
        from app.services.payment_service import PaymentService
        from fastapi import HTTPException

        user = await seed_customer(db)
        await db.commit()
        wallet = await PaymentService.get_or_create_wallet(db, user.id)
        wallet.is_frozen = True
        await db.commit()

        with pytest.raises(HTTPException) as exc:
            await PaymentService.credit_wallet(db, wallet, 10000, txn_type="topup")
        assert exc.value.status_code == 400
        assert "frozen" in str(exc.value.detail)


class TestPaymentServiceSettlement:
    """Test settle_booking_commission."""

    @pytest.mark.asyncio
    async def test_settlement_cash_debit_commission(self, db: AsyncSession):
        """Cash ride: debit commission từ ví driver."""
        from app.services.payment_service import PaymentService

        customer = await seed_customer(db)
        driver, provider = await seed_provider_pair(db)
        category = await create_service_category(db, code="taxi")
        await seed_commission_config(db, "taxi")
        await db.commit()

        booking = await seed_booking(
            db, customer.id, provider.id, category.id,
            payment_method="cash", final_fare=100000,
        )
        await db.commit()

        await PaymentService.settle_booking_commission(db, booking)
        await db.commit()

        wallet = (
            await db.execute(select(Wallet).where(Wallet.user_id == driver.id))
        ).scalars().first()

        assert wallet is not None
        # 20% commission of 100000 = 20000
        assert float(wallet.balance) == -20000

    @pytest.mark.asyncio
    async def test_settlement_online_credit_earning(self, db: AsyncSession):
        """Online payment: credit earning (fare - commission) cho driver."""
        from app.services.payment_service import PaymentService

        customer = await seed_customer(db)
        driver, provider = await seed_provider_pair(db)
        category = await create_service_category(db, code="taxi")
        await seed_commission_config(db, "taxi")
        await db.commit()

        booking = await seed_booking(
            db, customer.id, provider.id, category.id,
            payment_method="wallet", final_fare=100000,
        )
        await db.commit()

        await PaymentService.settle_booking_commission(db, booking)
        await db.commit()

        wallet = (
            await db.execute(select(Wallet).where(Wallet.user_id == driver.id))
        ).scalars().first()

        assert wallet is not None
        # Earning = 100000 - 20000 = 80000
        assert float(wallet.balance) == 80000

    @pytest.mark.asyncio
    async def test_settlement_no_config_skips(self, db: AsyncSession):
        """Không có commission config → skip settlement."""
        from app.services.payment_service import PaymentService

        customer = await seed_customer(db)
        driver, provider = await seed_provider_pair(db)
        category = await create_service_category(db, code="unknown_service")
        await db.commit()

        booking = await seed_booking(
            db, customer.id, provider.id, category.id,
            payment_method="cash", final_fare=100000,
        )
        await db.commit()

        # Should not raise
        await PaymentService.settle_booking_commission(db, booking)
        await db.commit()

        wallet_exists = (
            await db.execute(select(Wallet).where(Wallet.user_id == driver.id))
        ).scalars().first()
        # Wallet may or may not be created — no transaction should exist
        if wallet_exists:
            txns = (
                await db.execute(
                    select(WalletTransaction).where(WalletTransaction.wallet_id == wallet_exists.id)
                )
            ).scalars().all()
            assert len(txns) == 0


class TestPaymentServiceWithdrawal:
    """Test create_withdrawal_request."""

    @pytest.mark.asyncio
    async def test_withdrawal_success(self, db: AsyncSession):
        """Rút tiền thành công — hold balance ngay."""
        from app.services.payment_service import PaymentService

        user = await seed_customer(db)
        await db.commit()
        wallet = await PaymentService.get_or_create_wallet(db, user.id)
        await PaymentService.credit_wallet(db, wallet, 100000, txn_type="earning")
        await db.commit()

        txn = await PaymentService.create_withdrawal_request(
            db, wallet, 50000, "Withdrawal to VCB 123456",
        )
        await db.commit()

        assert txn.type == "withdrawal"
        assert txn.status == "pending"
        assert txn.amount == -50000
        assert float(wallet.balance) == 50000  # Hold ngay

    @pytest.mark.asyncio
    async def test_withdrawal_insufficient_balance(self, db: AsyncSession):
        """Rút tiền thiếu tiền phải fail."""
        from app.services.payment_service import PaymentService
        from fastapi import HTTPException

        user = await seed_customer(db)
        await db.commit()
        wallet = await PaymentService.get_or_create_wallet(db, user.id)
        await db.commit()

        with pytest.raises(HTTPException) as exc:
            await PaymentService.create_withdrawal_request(db, wallet, 50000, "Test")
        assert exc.value.status_code == 400
        assert "Insufficient" in str(exc.value.detail)

    @pytest.mark.asyncio
    async def test_withdrawal_duplicate_pending_fails(self, db: AsyncSession):
        """2 withdrawal pending cùng lúc phải fail."""
        from app.services.payment_service import PaymentService
        from fastapi import HTTPException

        user = await seed_customer(db)
        await db.commit()
        wallet = await PaymentService.get_or_create_wallet(db, user.id)
        await PaymentService.credit_wallet(db, wallet, 200000, txn_type="earning")
        await db.commit()

        await PaymentService.create_withdrawal_request(db, wallet, 50000, "First")
        await db.commit()

        with pytest.raises(HTTPException) as exc:
            await PaymentService.create_withdrawal_request(db, wallet, 50000, "Second")
        assert exc.value.status_code == 400
        assert "pending" in str(exc.value.detail).lower()


class TestPaymentServicePromotion:
    """Test validate_promotion."""

    @pytest.mark.asyncio
    async def test_validate_percent_promotion(self, db: AsyncSession):
        """Validate mã giảm giá percent."""
        from app.services.payment_service import PaymentService

        user = await seed_customer(db)
        promo = await seed_promotion(db, code="SAVE10", promo_type="percent", value=10)
        await db.commit()

        valid, promotion, discount, msg = await PaymentService.validate_promotion(
            db, "SAVE10", user.id, "taxi", 100000,
        )

        assert valid is True
        assert promotion is not None
        assert discount == 10000  # 10% of 100000
        assert msg is None

    @pytest.mark.asyncio
    async def test_validate_fixed_promotion(self, db: AsyncSession):
        """Validate mã giảm giá fixed."""
        from app.services.payment_service import PaymentService

        user = await seed_customer(db)
        await seed_promotion(db, code="FLAT20K", promo_type="fixed", value=20000)
        await db.commit()

        valid, _, discount, _ = await PaymentService.validate_promotion(
            db, "FLAT20K", user.id, "taxi", 100000,
        )

        assert valid is True
        assert discount == 20000

    @pytest.mark.asyncio
    async def test_validate_free_trip(self, db: AsyncSession):
        """Validate mã giảm giá free_trip."""
        from app.services.payment_service import PaymentService

        user = await seed_customer(db)
        await seed_promotion(db, code="FREETAXI", promo_type="free_trip", value=1)
        await db.commit()

        valid, _, discount, _ = await PaymentService.validate_promotion(
            db, "FREETAXI", user.id, "taxi", 80000,
        )

        assert valid is True
        assert discount == 80000  # Full fare

    @pytest.mark.asyncio
    async def test_validate_percent_with_max_discount(self, db: AsyncSession):
        """Giảm theo % nhưng cap bởi max_discount."""
        from app.services.payment_service import PaymentService

        user = await seed_customer(db)
        await seed_promotion(
            db, code="MAX50", promo_type="percent", value=50, max_discount=30000,
        )
        await db.commit()

        valid, _, discount, _ = await PaymentService.validate_promotion(
            db, "MAX50", user.id, "taxi", 100000,
        )

        assert valid is True
        assert discount == 30000  # 50% of 100k = 50k, but capped at 30k

    @pytest.mark.asyncio
    async def test_validate_inactive_promo_fails(self, db: AsyncSession):
        """Mã khuyến mãi inactive phải fail."""
        from app.services.payment_service import PaymentService

        user = await seed_customer(db)
        await seed_promotion(db, code="DEAD", is_active=False)
        await db.commit()

        valid, _, _, msg = await PaymentService.validate_promotion(
            db, "DEAD", user.id, "taxi", 100000,
        )

        assert valid is False
        assert "inactive" in msg.lower()

    @pytest.mark.asyncio
    async def test_validate_expired_promo_fails(self, db: AsyncSession):
        """Mã khuyến mãi hết hạn phải fail."""
        from app.services.payment_service import PaymentService

        user = await seed_customer(db)
        await seed_promotion(db, code="OLD", valid_days=-1)
        await db.commit()

        valid, _, _, msg = await PaymentService.validate_promotion(
            db, "OLD", user.id, "taxi", 100000,
        )

        assert valid is False
        assert "expired" in msg.lower() or "not yet valid" in msg.lower()

    @pytest.mark.asyncio
    async def test_validate_min_fare_fails(self, db: AsyncSession):
        """Đơn hàng không đủ min_fare phải fail."""
        from app.services.payment_service import PaymentService

        user = await seed_customer(db)
        await seed_promotion(db, code="MINFARE", min_fare=50000)
        await db.commit()

        valid, _, _, msg = await PaymentService.validate_promotion(
            db, "MINFARE", user.id, "taxi", 30000,
        )

        assert valid is False
        assert "Minimum" in msg

    @pytest.mark.asyncio
    async def test_validate_wrong_service_type_fails(self, db: AsyncSession):
        """Mã không áp dụng cho service type phải fail."""
        from app.services.payment_service import PaymentService

        user = await seed_customer(db)
        await seed_promotion(db, code="ONLYBIKE", service_types=["xe_om"])
        await db.commit()

        valid, _, _, msg = await PaymentService.validate_promotion(
            db, "ONLYBIKE", user.id, "taxi", 100000,
        )

        assert valid is False
        assert "service type" in msg.lower()

    @pytest.mark.asyncio
    async def test_validate_not_found(self, db: AsyncSession):
        """Mã không tồn tại phải fail."""
        from app.services.payment_service import PaymentService

        user = await seed_customer(db)
        await db.commit()

        valid, _, _, msg = await PaymentService.validate_promotion(
            db, "NONEXIST", user.id, "taxi", 100000,
        )

        assert valid is False
        assert "not found" in msg.lower()

    @pytest.mark.asyncio
    async def test_validate_usage_limit_reached(self, db: AsyncSession):
        """Mã hết lượt dùng phải fail."""
        from app.services.payment_service import PaymentService

        user = await seed_customer(db)
        promo = await seed_promotion(db, code="LIMIT1", usage_limit=1)
        promo.used_count = 1
        await db.commit()

        valid, _, _, msg = await PaymentService.validate_promotion(
            db, "LIMIT1", user.id, "taxi", 100000,
        )

        assert valid is False
        assert "limit" in msg.lower()

    @pytest.mark.asyncio
    async def test_consume_promotion_success(self, db: AsyncSession):
        """Lưu PromotionUsage và tăng used_count."""
        from app.services.payment_service import PaymentService

        user = await seed_customer(db)
        promo = await seed_promotion(db, code="CONSUME", usage_limit=10)

        # Create a real Booking row (required by FK constraint on promotion_usages)
        category = await create_service_category(db)
        booking = Booking(
            id=uuid.uuid4(),
            customer_id=user.id,
            service_category_id=category.id,
            service_type="taxi",
            pickup_address="Test Address",
        )
        db.add(booking)
        await db.commit()

        usage = await PaymentService.consume_promotion(
            db, "CONSUME", user.id, booking.id, 25000.0,
        )
        await db.commit()
        await db.refresh(promo)

        assert usage is not None
        assert usage.discount_amount == 25000.0
        assert promo.used_count == 1


# ═════════════════════════════════════════════════════════════════════
# 2. Customer Wallet API Tests
# ═════════════════════════════════════════════════════════════════════

class TestCustomerWalletAPI:
    """Test customer wallet endpoints."""

    @pytest.mark.asyncio
    async def test_get_wallet_auto_create(self, client: AsyncClient, db: AsyncSession):
        """GET /customer/wallet tự tạo ví mới."""
        customer = await seed_customer(db)
        await db.commit()
        token = make_customer_token(customer)

        resp = await client.get("/api/v1/customer/wallet", headers=auth_headers(token))

        assert resp.status_code == 200
        data = resp.json()
        assert data["balance"] == 0
        assert data["currency"] == "VND"
        assert data["is_frozen"] is False

    @pytest.mark.asyncio
    async def test_get_wallet_transactions(self, client: AsyncClient, db: AsyncSession):
        """GET /customer/wallet/transactions trả về phân trang."""
        from app.services.payment_service import PaymentService

        customer = await seed_customer(db)
        await db.commit()
        wallet = await PaymentService.get_or_create_wallet(db, customer.id)
        await PaymentService.credit_wallet(db, wallet, 50000, txn_type="topup")
        await db.commit()

        token = make_customer_token(customer)
        resp = await client.get(
            "/api/v1/customer/wallet/transactions",
            headers=auth_headers(token),
        )

        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        assert len(data["items"]) == 1
        assert data["items"][0]["type"] == "topup"

    @pytest.mark.asyncio
    async def test_topup_wallet(self, client: AsyncClient, db: AsyncSession):
        """POST /customer/wallet/topup tạo pending transaction."""
        customer = await seed_customer(db)
        await db.commit()
        token = make_customer_token(customer)

        resp = await client.post(
            "/api/v1/customer/wallet/topup",
            json={"amount": 100000, "method": "vnpay"},
            headers=auth_headers(token),
        )

        assert resp.status_code == 201
        data = resp.json()
        assert data["amount"] == 100000
        assert data["method"] == "vnpay"
        assert "payment_url" in data
        assert "sandbox" in data["payment_url"]

    @pytest.mark.asyncio
    async def test_validate_promotion_api(self, client: AsyncClient, db: AsyncSession):
        """POST /customer/promotions/validate trả kết quả."""
        customer = await seed_customer(db)
        await seed_promotion(db, code="API10", promo_type="percent", value=10)
        await db.commit()
        token = make_customer_token(customer)

        resp = await client.post(
            "/api/v1/customer/promotions/validate",
            json={"code": "API10", "service_type": "taxi", "fare": 80000},
            headers=auth_headers(token),
        )

        assert resp.status_code == 200
        data = resp.json()
        assert data["valid"] is True
        assert data["discount_amount"] == 8000
        assert data["final_fare"] == 72000

    @pytest.mark.asyncio
    async def test_list_available_promotions(self, client: AsyncClient, db: AsyncSession):
        """GET /customer/promotions trả DS khuyến mãi active."""
        customer = await seed_customer(db)
        await seed_promotion(db, code="ACTIVE1")
        await seed_promotion(db, code="INACTIVE1", is_active=False)
        await db.commit()
        token = make_customer_token(customer)

        resp = await client.get(
            "/api/v1/customer/promotions",
            headers=auth_headers(token),
        )

        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1  # Only active one
        assert data["items"][0]["code"] == "ACTIVE1"


# ═════════════════════════════════════════════════════════════════════
# 3. Provider Wallet API Tests
# ═════════════════════════════════════════════════════════════════════

class TestProviderWalletAPI:
    """Test provider wallet endpoints."""

    @pytest.mark.asyncio
    async def test_get_driver_wallet(self, client: AsyncClient, db: AsyncSession):
        """GET /provider/wallet tự tạo ví."""
        driver, _ = await seed_provider_pair(db)
        await db.commit()
        token = make_provider_token(driver)

        resp = await client.get("/api/v1/provider/wallet", headers=auth_headers(token))

        assert resp.status_code == 200
        data = resp.json()
        assert data["balance"] == 0

    @pytest.mark.asyncio
    async def test_get_earnings_summary(self, client: AsyncClient, db: AsyncSession):
        """GET /provider/me/earnings trả summary tổng hợp."""
        driver, _ = await seed_provider_pair(db)
        await db.commit()
        token = make_provider_token(driver)

        resp = await client.get("/api/v1/provider/me/earnings", headers=auth_headers(token))

        assert resp.status_code == 200
        data = resp.json()
        assert data["today"] == 0
        assert data["this_week"] == 0
        assert data["this_month"] == 0
        assert data["total_trips_today"] == 0

    @pytest.mark.asyncio
    async def test_get_earnings_history(self, client: AsyncClient, db: AsyncSession):
        """GET /provider/me/earnings/history trả lịch sử rỗng."""
        driver, _ = await seed_provider_pair(db)
        await db.commit()
        token = make_provider_token(driver)

        resp = await client.get(
            "/api/v1/provider/me/earnings/history",
            headers=auth_headers(token),
        )

        assert resp.status_code == 200
        data = resp.json()
        assert data["items"] == []

    @pytest.mark.asyncio
    async def test_request_withdrawal_success(self, client: AsyncClient, db: AsyncSession):
        """POST /provider/wallet/withdraw thành công khi đủ tiền."""
        from app.services.payment_service import PaymentService

        driver, _ = await seed_provider_pair(db)
        await db.commit()
        wallet = await PaymentService.get_or_create_wallet(db, driver.id)
        await PaymentService.credit_wallet(db, wallet, 200000, txn_type="earning")
        await db.commit()

        token = make_provider_token(driver)
        resp = await client.post(
            "/api/v1/provider/wallet/withdraw",
            json={"amount": 100000, "bank_name": "VCB", "bank_account": "123456"},
            headers=auth_headers(token),
        )

        assert resp.status_code == 201
        data = resp.json()
        assert data["type"] == "withdrawal"
        assert data["status"] == "pending"
        assert data["amount"] == -100000

    @pytest.mark.asyncio
    async def test_request_withdrawal_insufficient(self, client: AsyncClient, db: AsyncSession):
        """POST /provider/wallet/withdraw fail khi thiếu tiền."""
        driver, _ = await seed_provider_pair(db)
        await db.commit()
        token = make_provider_token(driver)

        resp = await client.post(
            "/api/v1/provider/wallet/withdraw",
            json={"amount": 100000},
            headers=auth_headers(token),
        )

        assert resp.status_code == 400


# ═════════════════════════════════════════════════════════════════════
# 4. Admin Payment API Tests
# ═════════════════════════════════════════════════════════════════════

class TestAdminPaymentAPI:
    """Test admin payment endpoints."""

    @pytest.mark.asyncio
    async def test_admin_list_wallets(self, client: AsyncClient, db: AsyncSession):
        """GET /admin/wallets trả phân trang."""
        from app.services.payment_service import PaymentService

        admin = await seed_admin(db)
        customer = await seed_customer(db)
        await db.commit()
        await PaymentService.get_or_create_wallet(db, customer.id)
        await db.commit()

        token = make_admin_token(admin)
        resp = await client.get("/api/v1/admin/wallets", headers=auth_headers(token))

        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 1

    @pytest.mark.asyncio
    async def test_admin_adjust_wallet_credit(self, client: AsyncClient, db: AsyncSession):
        """POST /admin/wallets/{user_id}/adjust credit thành công."""
        admin = await seed_admin(db)
        customer = await seed_customer(db)
        await db.commit()

        token = make_admin_token(admin)
        resp = await client.post(
            f"/api/v1/admin/wallets/{customer.id}/adjust",
            json={"amount": 50000, "description": "Bonus for testing purposes"},
            headers=auth_headers(token),
        )

        assert resp.status_code == 200
        data = resp.json()
        assert data["balance"] == 50000

    @pytest.mark.asyncio
    async def test_admin_adjust_wallet_debit(self, client: AsyncClient, db: AsyncSession):
        """POST /admin/wallets/{user_id}/adjust debit thành công."""
        from app.services.payment_service import PaymentService

        admin = await seed_admin(db)
        customer = await seed_customer(db)
        await db.commit()
        wallet = await PaymentService.get_or_create_wallet(db, customer.id)
        await PaymentService.credit_wallet(db, wallet, 100000, txn_type="topup")
        await db.commit()

        token = make_admin_token(admin)
        resp = await client.post(
            f"/api/v1/admin/wallets/{customer.id}/adjust",
            json={"amount": -30000, "description": "Penalty for violation test"},
            headers=auth_headers(token),
        )

        assert resp.status_code == 200
        data = resp.json()
        assert data["balance"] == 70000

    @pytest.mark.asyncio
    async def test_admin_adjust_zero_fails(self, client: AsyncClient, db: AsyncSession):
        """POST /admin/wallets/{user_id}/adjust amount=0 phải fail."""
        admin = await seed_admin(db)
        customer = await seed_customer(db)
        await db.commit()

        token = make_admin_token(admin)
        resp = await client.post(
            f"/api/v1/admin/wallets/{customer.id}/adjust",
            json={"amount": 0, "description": "Zero adjustment test"},
            headers=auth_headers(token),
        )

        assert resp.status_code == 400

    @pytest.mark.asyncio
    async def test_admin_approve_withdrawal(self, client: AsyncClient, db: AsyncSession):
        """POST /admin/withdrawals/{txn_id}/approve thành công."""
        from app.services.payment_service import PaymentService

        admin = await seed_admin(db)
        customer = await seed_customer(db)
        await db.commit()
        wallet = await PaymentService.get_or_create_wallet(db, customer.id)
        await PaymentService.credit_wallet(db, wallet, 100000, txn_type="earning")
        await db.commit()
        txn = await PaymentService.create_withdrawal_request(db, wallet, 50000, "Test withdrawal")
        await db.commit()

        token = make_admin_token(admin)
        resp = await client.post(
            f"/api/v1/admin/withdrawals/{txn.id}/approve",
            headers=auth_headers(token),
        )

        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "completed"

    @pytest.mark.asyncio
    async def test_admin_reject_withdrawal_refunds(self, client: AsyncClient, db: AsyncSession):
        """POST /admin/withdrawals/{txn_id}/reject hoàn lại balance."""
        from app.services.payment_service import PaymentService

        admin = await seed_admin(db)
        customer = await seed_customer(db)
        await db.commit()
        wallet = await PaymentService.get_or_create_wallet(db, customer.id)
        await PaymentService.credit_wallet(db, wallet, 100000, txn_type="earning")
        await db.commit()

        balance_before_withdraw = float(wallet.balance)

        txn = await PaymentService.create_withdrawal_request(db, wallet, 50000, "Test withdrawal")
        await db.commit()

        assert float(wallet.balance) == 50000  # Held

        token = make_admin_token(admin)
        resp = await client.post(
            f"/api/v1/admin/withdrawals/{txn.id}/reject",
            headers=auth_headers(token),
        )

        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "failed"

        # Balance should be refunded
        await db.refresh(wallet)
        assert float(wallet.balance) == balance_before_withdraw

    @pytest.mark.asyncio
    async def test_admin_create_promotion(self, client: AsyncClient, db: AsyncSession):
        """POST /admin/promotions tạo mới thành công."""
        admin = await seed_admin(db)
        await db.commit()
        token = make_admin_token(admin)

        resp = await client.post(
            "/api/v1/admin/promotions",
            json={
                "code": "NEWPROMO",
                "name": "New Promotion",
                "type": "percent",
                "value": 15,
                "valid_from": (datetime.now(tz=timezone.utc) - timedelta(days=1)).isoformat(),
                "valid_to": (datetime.now(tz=timezone.utc) + timedelta(days=30)).isoformat(),
            },
            headers=auth_headers(token),
        )

        assert resp.status_code == 201
        data = resp.json()
        assert data["code"] == "NEWPROMO"
        assert data["is_active"] is True

    @pytest.mark.asyncio
    async def test_admin_create_duplicate_code_fails(self, client: AsyncClient, db: AsyncSession):
        """POST /admin/promotions code trùng phải 409."""
        admin = await seed_admin(db)
        await seed_promotion(db, code="DUP")
        await db.commit()
        token = make_admin_token(admin)

        resp = await client.post(
            "/api/v1/admin/promotions",
            json={
                "code": "DUP",
                "name": "Duplicate",
                "type": "fixed",
                "value": 10000,
                "valid_from": datetime.now(tz=timezone.utc).isoformat(),
                "valid_to": (datetime.now(tz=timezone.utc) + timedelta(days=30)).isoformat(),
            },
            headers=auth_headers(token),
        )

        assert resp.status_code == 409

    @pytest.mark.asyncio
    async def test_admin_update_promotion(self, client: AsyncClient, db: AsyncSession):
        """PUT /admin/promotions/{id} cập nhật thành công."""
        admin = await seed_admin(db)
        promo = await seed_promotion(db, code="EDIT")
        await db.commit()
        token = make_admin_token(admin)

        resp = await client.put(
            f"/api/v1/admin/promotions/{promo.id}",
            json={"name": "Updated Promotion", "value": 25},
            headers=auth_headers(token),
        )

        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "Updated Promotion"
        assert data["value"] == 25

    @pytest.mark.asyncio
    async def test_admin_toggle_promotion(self, client: AsyncClient, db: AsyncSession):
        """PATCH /admin/promotions/{id}/status toggle is_active."""
        admin = await seed_admin(db)
        promo = await seed_promotion(db, code="TOGGLE")
        await db.commit()
        token = make_admin_token(admin)

        resp = await client.patch(
            f"/api/v1/admin/promotions/{promo.id}/status",
            json={"is_active": False},
            headers=auth_headers(token),
        )

        assert resp.status_code == 200
        data = resp.json()
        assert data["is_active"] is False

    @pytest.mark.asyncio
    async def test_admin_list_promotions(self, client: AsyncClient, db: AsyncSession):
        """GET /admin/promotions trả phân trang."""
        admin = await seed_admin(db)
        await seed_promotion(db, code="PROMO1")
        await seed_promotion(db, code="PROMO2")
        await db.commit()
        token = make_admin_token(admin)

        resp = await client.get("/api/v1/admin/promotions", headers=auth_headers(token))

        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 2

    @pytest.mark.asyncio
    async def test_admin_get_revenue(self, client: AsyncClient, db: AsyncSession):
        """GET /admin/finance/revenue trả kết quả."""
        admin = await seed_admin(db)
        await db.commit()
        token = make_admin_token(admin)

        resp = await client.get("/api/v1/admin/finance/revenue", headers=auth_headers(token))

        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        assert "total_commission" in data


# ═════════════════════════════════════════════════════════════════════
# 5. Internal Payment Callback Tests
# ═════════════════════════════════════════════════════════════════════

class TestInternalPaymentCallbacks:
    """Test payment gateway callback skeletons."""

    @pytest.mark.asyncio
    async def test_vnpay_callback_success(self, client: AsyncClient):
        """GET /internal/payments/vnpay/callback validation."""
        # Simple test to verify the route accepts GET mapping appropriately
        # Because we don't have valid sandbox keys in test environment for signature,
        # it should return 97 (checksum failed) but the route should be reachable.
        resp = await client.get(
            "/api/v1/internal/payments/vnpay/callback?vnp_ResponseCode=00&vnp_TxnRef=xyz&vnp_SecureHash=fake"
        )
        assert resp.status_code == 200
        # Will fail signature validation, so returns 97
        assert resp.json()["RspCode"] == "97"

    @pytest.mark.asyncio
    async def test_momo_callback_invalid(self, client: AsyncClient):
        """POST /internal/payments/momo/callback trả 99 khi sai chữ ký."""
        resp = await client.post(
            "/api/v1/internal/payments/momo/callback",
            json={"resultCode": 0, "orderId": "test", "signature": "fakesig"},
        )
        assert resp.status_code == 200
        assert resp.json()["resultCode"] == 99

    @pytest.mark.asyncio
    async def test_zalopay_callback_invalid(self, client: AsyncClient):
        """POST /internal/payments/zalopay/callback trả -1 khi sai mac."""
        resp = await client.post(
            "/api/v1/internal/payments/zalopay/callback",
            json={"data": "test", "mac": "fakemac"},
        )
        assert resp.status_code == 200
        assert resp.json()["return_code"] == -1

    @pytest.mark.asyncio
    async def test_momo_callback_success(self, client: AsyncClient, db: AsyncSession):
        """POST /internal/payments/momo/callback với chữ ký hợp lệ."""
        from app.services.payment_service import PaymentService
        from app.services.momo_service import MomoService
        from app.core.config import get_settings
        import uuid

        settings = get_settings()
        secret_key = settings.momo_secret_key or "MOMO_SECRET"
        # override key in settings for this test if it's empty
        settings.momo_secret_key = secret_key

        user_id = uuid.uuid4()
        wallet = await PaymentService.get_or_create_wallet(db, user_id)
        from app.models.payment import WalletTransaction
        txn = WalletTransaction(
            wallet_id=wallet.id,
            type="topup",
            amount=50000,
            status="pending",
            balance_after=0
        )
        db.add(txn)
        await db.commit()
        await db.refresh(txn)

        payload = {
            "partnerCode": "MOMO",
            "orderId": str(txn.id),
            "requestId": str(txn.id),
            "amount": 50000,
            "orderInfo": "Topup",
            "orderType": "momo_wallet",
            "transId": 123456789,
            "resultCode": 0,
            "message": "Success",
            "payType": "qr",
            "responseTime": 162983726,
            "extraData": "",
            "accessKey": "access"
        }

        # generate signature
        import hmac, hashlib
        fields = [
            "accessKey", "amount", "extraData", "message", "orderId",
            "orderInfo", "orderType", "partnerCode", "payType", "requestId",
            "responseTime", "resultCode", "transId"
        ]
        raw_data = "&".join([f"{k}={payload.get(k, '')}" for k in fields])
        signature = hmac.new(secret_key.encode("utf-8"), raw_data.encode("utf-8"), hashlib.sha256).hexdigest()
        payload["signature"] = signature

        resp = await client.post(
            "/api/v1/internal/payments/momo/callback",
            json=payload,
        )
        assert resp.status_code == 200
        assert resp.json()["resultCode"] == 0

        # Check in DB
        await db.refresh(txn)
        assert txn.status == "completed"
        await db.refresh(wallet)
        assert wallet.balance == 50000

    @pytest.mark.asyncio
    async def test_zalopay_callback_success(self, client: AsyncClient, db: AsyncSession):
        """POST /internal/payments/zalopay/callback với chữ ký hợp lệ."""
        from app.services.payment_service import PaymentService
        from app.services.zalopay_service import ZaloPayService
        import json, hmac, hashlib
        from app.core.config import get_settings
        import uuid

        settings = get_settings()
        key2 = settings.zalopay_key2 or "ZALOPAY_KEY2"
        settings.zalopay_key2 = key2

        user_id = uuid.uuid4()
        wallet = await PaymentService.get_or_create_wallet(db, user_id)
        from app.models.payment import WalletTransaction
        txn = WalletTransaction(
            wallet_id=wallet.id,
            type="topup",
            amount=60000,
            status="pending",
            balance_after=0
        )
        db.add(txn)
        await db.commit()
        await db.refresh(txn)

        data_dict = {
            "app_id": 2553,
            "app_trans_id": str(txn.id),
            "app_user": "u",
            "amount": 60000,
            "app_time": 162983726,
            "item": "[]",
            "embed_data": "{}",
            "zp_trans_id": 987654321
        }
        data_str = json.dumps(data_dict)
        mac = hmac.new(key2.encode("utf-8"), data_str.encode("utf-8"), hashlib.sha256).hexdigest()

        resp = await client.post(
            "/api/v1/internal/payments/zalopay/callback",
            json={"data": data_str, "mac": mac},
        )
        assert resp.status_code == 200
        assert resp.json()["return_code"] == 1

        # Check in DB
        await db.refresh(txn)
        assert txn.status == "completed"
        await db.refresh(wallet)
        assert float(wallet.balance) == 60000

    @pytest.mark.asyncio
    async def test_double_webhook_callback(self, client: AsyncClient, db: AsyncSession):
        """POST /internal/payments/momo/callback 2 lần (idempotent test)."""
        from app.services.payment_service import PaymentService
        from app.models.payment import WalletTransaction
        import uuid
        from app.core.config import get_settings
        import hmac, hashlib

        settings = get_settings()
        secret_key = settings.momo_secret_key or "MOMO_SECRET"
        settings.momo_secret_key = secret_key

        user_id = uuid.uuid4()
        wallet = await PaymentService.get_or_create_wallet(db, user_id)
        
        txn = WalletTransaction(
            wallet_id=wallet.id,
            type="topup",
            amount=50000,
            status="pending",
            balance_after=0
        )
        db.add(txn)
        await db.commit()
        await db.refresh(txn)

        payload = {
            "partnerCode": "MOMO",
            "orderId": str(txn.id),
            "requestId": str(txn.id),
            "amount": 50000,
            "orderInfo": "Topup",
            "orderType": "momo_wallet",
            "transId": 123456789,
            "resultCode": 0,
            "message": "Success",
            "payType": "qr",
            "responseTime": 162983726,
            "extraData": "",
            "accessKey": "access"
        }
        fields = [
            "accessKey", "amount", "extraData", "message", "orderId",
            "orderInfo", "orderType", "partnerCode", "payType", "requestId",
            "responseTime", "resultCode", "transId"
        ]
        raw_data = "&".join([f"{k}={payload.get(k, '')}" for k in fields])
        payload["signature"] = hmac.new(secret_key.encode("utf-8"), raw_data.encode("utf-8"), hashlib.sha256).hexdigest()

        # Gọi lần 1
        resp1 = await client.post("/api/v1/internal/payments/momo/callback", json=payload)
        assert resp1.status_code == 200
        assert resp1.json()["resultCode"] == 0

        # Gọi lần 2 (Webhook retry)
        resp2 = await client.post("/api/v1/internal/payments/momo/callback", json=payload)
        assert resp2.status_code == 200
        assert resp2.json()["resultCode"] == 0 # Idempotent returns success to stop retry

        # Database Check: Balance must be credited ONLY ONCE
        await db.refresh(wallet)
        assert float(wallet.balance) == 50000

    @pytest.mark.asyncio
    async def test_decimal_precision(self, db: AsyncSession):
        """Kiểm tra độ chính xác của Decimal khi cộng trừ số dư, chống sai số float IEEE 754."""
        from app.services.payment_service import PaymentService
        import uuid
        from decimal import Decimal

        user_id = uuid.uuid4()
        wallet = await PaymentService.get_or_create_wallet(db, user_id)
        
        # Test nạp tiền lần 1: 10,000,000.01 (10 triệu vnđ linh 1 xu)
        await PaymentService.credit_wallet(db, wallet, amount=10000000.01, txn_type="topup")
        
        # Test nạp tiền lần 2: 10,000,000.02
        await PaymentService.credit_wallet(db, wallet, amount=10000000.02, txn_type="topup")
        
        # Check in DB
        await db.refresh(wallet)
        
        # Nếu dùng float IEEE 754: 10000000.01 + 10000000.02 = 20000000.029999999999
        # Nếu dùng DB Numeric(18,2) và Decimal python thì sẽ chính xác 20_000_000.03
        assert str(wallet.balance) == "20000000.03"
