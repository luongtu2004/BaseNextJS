from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone

from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import WALLET_NEGATIVE_FLOOR
from app.models.booking import CommissionConfig
from app.models.payment import Promotion, PromotionUsage, Wallet, WalletTransaction
from app.models.provider import Provider

logger = logging.getLogger(__name__)


class PaymentService:
    """Business logic cho ví, settlement, và khuyến mãi."""

    # ─────────────────────────────────────────────────────────────
    # Wallet Core
    # ─────────────────────────────────────────────────────────────

    @staticmethod
    async def get_or_create_wallet(db: AsyncSession, user_id: uuid.UUID) -> Wallet:
        """Lấy ví của user hoặc tạo mới nếu chưa có (idempotent).

        Args:
            db: Async DB session.
            user_id: UUID của user.

        Returns:
            Wallet đã tồn tại hoặc mới tạo.
        """
        wallet = (
            await db.execute(
                select(Wallet).where(Wallet.user_id == user_id)
            )
        ).scalars().first()

        if wallet:
            return wallet

        # Use a savepoint (nested transaction) to safely handle concurrent wallet creations
        async with db.begin_nested():
            try:
                wallet = Wallet(user_id=user_id)
                db.add(wallet)
                await db.flush()
                logger.info("[WALLET] Created wallet - user_id=%s wallet_id=%s", user_id, wallet.id)
                return wallet
            except IntegrityError:
                pass  # Concurrently created by another request

        # If it failed, it means it was just created, so fetch it again
        wallet = (
            await db.execute(
                select(Wallet).where(Wallet.user_id == user_id)
            )
        ).scalars().one()
        logger.info("[WALLET] Retrieved concurrent wallet - user_id=%s wallet_id=%s", user_id, wallet.id)
        return wallet

    @staticmethod
    async def credit_wallet(
        db: AsyncSession,
        wallet: Wallet,
        amount: float,
        txn_type: str,
        reference_id: uuid.UUID | None = None,
        reference_type: str | None = None,
        description: str | None = None,
    ) -> WalletTransaction:
        """Credit (cộng tiền) vào ví.

        Args:
            db: Async DB session.
            wallet: Wallet object.
            amount: Số tiền cộng (phải > 0).
            txn_type: Loại giao dịch (topup/earning/refund/bonus/adjust).
            reference_id: ID tham chiếu (booking/payment).
            reference_type: Loại tham chiếu.
            description: Mô tả giao dịch.

        Returns:
            WalletTransaction đã tạo.

        Raises:
            HTTPException 400: Nếu amount <= 0 hoặc ví bị đóng băng.
        """
        if amount <= 0:
            raise HTTPException(status_code=400, detail="Credit amount must be positive")
        if wallet.is_frozen:
            raise HTTPException(status_code=400, detail="Wallet is frozen")

        # Refetch with row-level lock (FOR UPDATE) to prevent race conditions during credit
        locked_wallet = (
            await db.execute(
                select(Wallet).where(Wallet.id == wallet.id).with_for_update()
            )
        ).scalars().first()

        if not locked_wallet:
            raise HTTPException(status_code=404, detail="Wallet not found")

        locked_wallet.balance = Decimal(str(locked_wallet.balance)) + Decimal(str(amount))
        locked_wallet.updated_at = datetime.now(tz=timezone.utc)

        txn = WalletTransaction(
            wallet_id=locked_wallet.id,
            type=txn_type,
            amount=amount,
            balance_after=locked_wallet.balance,
            reference_id=reference_id,
            reference_type=reference_type,
            description=description,
            status="completed",
        )
        db.add(txn)
        await db.flush()
        logger.info(
            "[WALLET] Credit - wallet_id=%s type=%s amount=%s balance_after=%s",
            locked_wallet.id, txn_type, amount, locked_wallet.balance,
        )
        return txn

    @staticmethod
    async def debit_wallet(
        db: AsyncSession,
        wallet: Wallet,
        amount: float,
        txn_type: str,
        reference_id: uuid.UUID | None = None,
        reference_type: str | None = None,
        description: str | None = None,
        allow_negative: bool = False,
    ) -> WalletTransaction:
        """Debit (trừ tiền) từ ví.

        Args:
            db: Async DB session.
            wallet: Wallet object.
            amount: Số tiền trừ (phải > 0).
            txn_type: Loại giao dịch (payment/withdrawal/commission/penalty/adjust).
            reference_id: ID tham chiếu.
            reference_type: Loại tham chiếu.
            description: Mô tả giao dịch.
            allow_negative: Cho phép ví âm (dùng cho commission settlement cash).

        Returns:
            WalletTransaction đã tạo.

        Raises:
            HTTPException 400: Nếu amount <= 0, ví bị đóng băng, hoặc
                số dư không đủ (khi allow_negative=False).
        """
        if amount <= 0:
            raise HTTPException(status_code=400, detail="Debit amount must be positive")
        if wallet.is_frozen:
            raise HTTPException(status_code=400, detail="Wallet is frozen")

        # Refetch with row-level lock (FOR UPDATE) to prevent race conditions during debit
        locked_wallet = (
            await db.execute(
                select(Wallet).where(Wallet.id == wallet.id).with_for_update()
            )
        ).scalars().first()

        if not locked_wallet:
            raise HTTPException(status_code=404, detail="Wallet not found")

        current_balance = Decimal(str(locked_wallet.balance))
        debit_amount = Decimal(str(amount))
        if not allow_negative and current_balance < debit_amount:
            raise HTTPException(status_code=400, detail="Insufficient wallet balance")

        locked_wallet.balance = current_balance - debit_amount
        locked_wallet.updated_at = datetime.now(tz=timezone.utc)

        # Log warning nếu ví âm dưới floor limit
        if locked_wallet.balance < WALLET_NEGATIVE_FLOOR:
            logger.warning(
                "[WALLET] Balance below floor limit - wallet_id=%s balance=%s floor=%s",
                locked_wallet.id, locked_wallet.balance, WALLET_NEGATIVE_FLOOR,
            )

        txn = WalletTransaction(
            wallet_id=locked_wallet.id,
            type=txn_type,
            amount=-amount,
            balance_after=locked_wallet.balance,
            reference_id=reference_id,
            reference_type=reference_type,
            description=description,
            status="completed",
        )
        db.add(txn)
        await db.flush()
        logger.info(
            "[WALLET] Debit - wallet_id=%s type=%s amount=-%s balance_after=%s",
            locked_wallet.id, txn_type, amount, locked_wallet.balance,
        )
        return txn

    # ─────────────────────────────────────────────────────────────
    # Settlement
    # ─────────────────────────────────────────────────────────────

    @staticmethod
    async def settle_booking_commission(db: AsyncSession, booking: object) -> None:
        """Tính và khấu trừ hoa hồng sau khi booking hoàn thành.

        Khi payment_method == 'cash': driver đã nhận tiền mặt, debit commission
        (cho phép ví âm giống Grab).
        Khi payment_method online: credit driver earning (fare - commission).

        Args:
            db: Async DB session.
            booking: Booking ORM object (đã completed).
        """
        # Lấy commission config hiện hành
        config = (
            await db.execute(
                select(CommissionConfig).where(
                    CommissionConfig.service_type == booking.service_type,
                    CommissionConfig.is_active.is_(True),
                ).order_by(CommissionConfig.created_at.desc())
            )
        ).scalars().first()

        if not config:
            logger.warning(
                "[WALLET] No active commission config for service_type=%s - skipping settlement for booking=%s",
                booking.service_type, booking.id,
            )
            return

        # Tính toán
        fare = float(booking.final_fare or booking.estimated_fare or 0)
        if fare <= 0:
            logger.warning("[WALLET] Fare is zero - skipping settlement for booking=%s", booking.id)
            return

        rate = float(config.rate_percent)
        fixed = float(config.fixed_fee or 0)
        commission_amount = round(fare * rate / 100 + fixed, 0)
        driver_earning = round(fare - commission_amount, 0)

        # Lấy user_id của driver từ provider
        provider = await db.get(Provider, booking.provider_id)
        if not provider:
            logger.error("[WALLET] Provider not found for booking=%s provider_id=%s", booking.id, booking.provider_id)
            return

        wallet = await PaymentService.get_or_create_wallet(db, provider.owner_user_id)

        payment_method = booking.payment_method or "cash"

        if payment_method == "cash":
            # Driver đã nhận tiền mặt — chỉ debit commission (cho phép âm)
            await PaymentService.debit_wallet(
                db, wallet, commission_amount,
                txn_type="commission",
                reference_id=booking.id,
                reference_type="booking",
                description=f"Commission {rate}% for booking (cash)",
                allow_negative=True,
            )
        else:
            # Online payment — credit driver earning (fare - commission)
            await PaymentService.credit_wallet(
                db, wallet, driver_earning,
                txn_type="earning",
                reference_id=booking.id,
                reference_type="booking",
                description=f"Earning for booking (online) - commission {rate}%",
            )

        logger.info(
            "[WALLET] Settlement completed - booking_id=%s fare=%s commission=%s method=%s",
            booking.id, fare, commission_amount, payment_method,
        )

    # ─────────────────────────────────────────────────────────────
    # Withdrawal
    # ─────────────────────────────────────────────────────────────

    @staticmethod
    async def create_withdrawal_request(
        db: AsyncSession,
        wallet: Wallet,
        amount: float,
        description: str,
    ) -> WalletTransaction:
        """Tạo yêu cầu rút tiền (hold balance ngay lập tức).

        Args:
            db: Async DB session.
            wallet: Wallet object.
            amount: Số tiền rút (phải > 0).
            description: Mô tả (bank info).

        Returns:
            WalletTransaction pending.

        Raises:
            HTTPException 400: Nếu ví bị đóng băng, số dư không đủ,
                hoặc đã có yêu cầu rút tiền chưa xử lý.
        """
        if wallet.is_frozen:
            raise HTTPException(status_code=400, detail="Wallet is frozen")

        # Acquire row-level lock first, then validate balance and pending in one atomic block
        locked_wallet = (
            await db.execute(
                select(Wallet).where(Wallet.id == wallet.id).with_for_update()
            )
        ).scalars().first()

        if not locked_wallet:
            raise HTTPException(status_code=404, detail="Wallet not found")

        current_balance = Decimal(str(locked_wallet.balance))
        withdrawal_amount = Decimal(str(amount))
        if current_balance < withdrawal_amount:
            raise HTTPException(status_code=400, detail="Insufficient wallet balance")

        # Check pending withdrawal inside lock to prevent concurrent duplicate requests
        pending = (
            await db.execute(
                select(func.count()).where(
                    WalletTransaction.wallet_id == locked_wallet.id,
                    WalletTransaction.type == "withdrawal",
                    WalletTransaction.status == "pending",
                )
            )
        ).scalar_one()

        if pending > 0:
            raise HTTPException(status_code=400, detail="Existing pending withdrawal request")

        # Hold balance ngay (tránh double-spend)
        locked_wallet.balance = current_balance - withdrawal_amount
        locked_wallet.updated_at = datetime.now(tz=timezone.utc)

        txn = WalletTransaction(
            wallet_id=locked_wallet.id,
            type="withdrawal",
            amount=-amount,
            balance_after=locked_wallet.balance,
            description=description,
            status="pending",
        )
        db.add(txn)
        await db.flush()
        logger.info(
            "[WALLET] Withdrawal requested - wallet_id=%s amount=%s balance_after=%s",
            locked_wallet.id, amount, locked_wallet.balance,
        )
        return txn

    # ─────────────────────────────────────────────────────────────
    # Promotion Validation
    # ─────────────────────────────────────────────────────────────

    @staticmethod
    async def validate_promotion(
        db: AsyncSession,
        code: str,
        user_id: uuid.UUID,
        service_type: str,
        fare: float,
    ) -> tuple[bool, Promotion | None, float, str | None]:
        """Validate mã giảm giá và tính số tiền giảm.

        Args:
            db: Async DB session.
            code: Mã khuyến mãi.
            user_id: UUID của user đang dùng.
            service_type: Loại dịch vụ.
            fare: Cước phí trước giảm.

        Returns:
            Tuple (valid, promotion, discount_amount, error_message).
        """
        now = datetime.now(tz=timezone.utc)

        promo = (
            await db.execute(
                select(Promotion).where(Promotion.code == code)
            )
        ).scalars().first()

        if not promo:
            return False, None, 0, "Promotion code not found"

        if not promo.is_active:
            return False, None, 0, "Promotion is inactive"

        # Handle both tz-aware (PostgreSQL) and tz-naive (SQLite test) datetimes
        valid_from = promo.valid_from.replace(tzinfo=timezone.utc) if promo.valid_from.tzinfo is None else promo.valid_from
        valid_to = promo.valid_to.replace(tzinfo=timezone.utc) if promo.valid_to.tzinfo is None else promo.valid_to

        if now < valid_from or now > valid_to:
            return False, None, 0, "Promotion has expired or not yet valid"

        if promo.usage_limit and promo.used_count >= promo.usage_limit:
            return False, None, 0, "Promotion usage limit reached"

        # Per-user limit check
        if promo.per_user_limit:
            user_usage_count = (
                await db.execute(
                    select(func.count()).where(
                        PromotionUsage.promotion_id == promo.id,
                        PromotionUsage.user_id == user_id,
                    )
                )
            ).scalar_one()
            if user_usage_count >= promo.per_user_limit:
                return False, None, 0, "You have reached the usage limit for this promotion"

        # Min fare check
        if promo.min_fare and fare < float(promo.min_fare):
            return False, None, 0, f"Minimum fare required: {promo.min_fare}"

        # Service type check
        if promo.service_types:
            if service_type not in promo.service_types:
                return False, None, 0, "Promotion not valid for this service type"

        # Calculate discount
        promo_value = float(promo.value)
        if promo.type == "percent":
            discount = fare * promo_value / 100
            if promo.max_discount:
                discount = min(discount, float(promo.max_discount))
        elif promo.type == "fixed":
            discount = min(promo_value, fare)
        elif promo.type == "free_trip":
            discount = fare
        else:
            return False, None, 0, "Invalid promotion type"

        discount = round(discount, 0)
        return True, promo, discount, None

    @staticmethod
    async def consume_promotion(
        db: AsyncSession,
        code: str,
        user_id: uuid.UUID,
        booking_id: uuid.UUID,
        discount_amount: float,
    ) -> PromotionUsage:
        """Ghi nhận việc sử dụng promotion và cập nhật số lượng giới hạn. Khóa row để chống race condition.

        Args:
            db: Async DB session.
            code: Mã khuyến mãi đã validate thành công.
            user_id: UUID người dùng.
            booking_id: UUID booking được áp dụng.
            discount_amount: Khoản tiền giảm giá.

        Returns:
            PromotionUsage: Log sử dụng mã.

        Raises:
            HTTPException 400: Nếu không đủ điều kiện ghi nhận (hoặc hết lượt limit sau khi lock).
        """
        # Refetch with FOR UPDATE
        locked_promo = (
            await db.execute(
                select(Promotion).where(Promotion.code == code).with_for_update()
            )
        ).scalars().first()

        if not locked_promo:
            raise HTTPException(status_code=400, detail="Promotion not found")

        # Double check limits inside the lock
        if locked_promo.usage_limit and locked_promo.used_count >= locked_promo.usage_limit:
            raise HTTPException(status_code=400, detail="Promotion usage limit reached concurrently")

        if locked_promo.per_user_limit:
            user_usage_count = (
                await db.execute(
                    select(func.count()).where(
                        PromotionUsage.promotion_id == locked_promo.id,
                        PromotionUsage.user_id == user_id,
                    )
                )
            ).scalar_one()
            if user_usage_count >= locked_promo.per_user_limit:
                raise HTTPException(status_code=400, detail="Per-user limit reached concurrently")

        # Update and Log
        locked_promo.used_count += 1
        locked_promo.updated_at = datetime.now(tz=timezone.utc)

        usage = PromotionUsage(
            promotion_id=locked_promo.id,
            user_id=user_id,
            booking_id=booking_id,
            discount_amount=discount_amount,
            used_at=datetime.now(tz=timezone.utc),
        )
        db.add(usage)
        await db.flush()

        logger.info(
            "[PROMOTION] Consumed promo - code=%s user_id=%s discount=%s",
            code, user_id, discount_amount,
        )
        return usage

    # ─────────────────────────────────────────────────────────────
    # Gateway Callbacks (Payment Transactions)
    # ─────────────────────────────────────────────────────────────

    @staticmethod
    async def complete_payment_transaction(
        db: AsyncSession,
        transaction_id: uuid.UUID,
        gateway_ref: str | None = None,
        metadata: dict | None = None,
    ) -> PaymentTransaction:
        """Đánh dấu giao dịch thanh toán qua cổng điện tử là thành công.
        Sử dụng cơ chế row-level lock để ngăn ngừa webhook callback bị bắt 2 lần (double-crediting).

        Args:
            db: Async DB session.
            transaction_id: UUID giao dịch payment.
            gateway_ref: Mã giao dịch phía đối tác (VNPay/MoMo).
            metadata: Payload callback đối chiếu.

        Returns:
            PaymentTransaction đã update.

        Raises:
            HTTPException 404: Nếu không thấy giao dịch.
            HTTPException 400: Nếu giao dịch đã kết thúc trước đó.
        """
        from app.models.payment import PaymentTransaction

        locked_txn = (
            await db.execute(
                select(PaymentTransaction)
                .where(PaymentTransaction.id == transaction_id)
                .with_for_update()
            )
        ).scalars().first()

        if not locked_txn:
            raise HTTPException(status_code=404, detail="Payment transaction not found")

        if locked_txn.status != "pending":
            raise HTTPException(
                status_code=400,
                detail=f"Transaction already processed (current status: {locked_txn.status})"
            )

        locked_txn.status = "completed"
        locked_txn.gateway_ref = gateway_ref
        if metadata:
            locked_txn.metadata_ = metadata
        locked_txn.paid_at = datetime.now(tz=timezone.utc)
        locked_txn.updated_at = locked_txn.paid_at

        # Depending on the application flow, if this was a topup, credit the wallet here.
        # But this method specifically just safely completes the PaymentTransaction.
        await db.flush()

        logger.info(
            "[PAYMENT] Payment transaction completed - id=%s gateway_ref=%s",
            locked_txn.id, gateway_ref
        )
        return locked_txn

    @staticmethod
    async def fail_payment_transaction(
        db: AsyncSession,
        transaction_id: uuid.UUID,
        metadata: dict | None = None,
    ) -> PaymentTransaction:
        """Đánh dấu giao dịch thanh toán thất bại một cách an toàn."""
        from app.models.payment import PaymentTransaction

        locked_txn = (
            await db.execute(
                select(PaymentTransaction)
                .where(PaymentTransaction.id == transaction_id)
                .with_for_update()
            )
        ).scalars().first()

        if not locked_txn:
            raise HTTPException(status_code=404, detail="Payment transaction not found")

        if locked_txn.status != "pending":
            raise HTTPException(
                status_code=400,
                detail=f"Transaction already processed (status: {locked_txn.status})"
            )

        locked_txn.status = "failed"
        if metadata:
            locked_txn.metadata_ = metadata
        locked_txn.updated_at = datetime.now(tz=timezone.utc)
        
        await db.flush()
        logger.info("[PAYMENT] Payment transaction failed - id=%s", locked_txn.id)
        return locked_txn

    @staticmethod
    async def complete_wallet_topup(
        db: AsyncSession,
        transaction_id: uuid.UUID,
        gateway_ref: str | None = None,
    ) -> WalletTransaction:
        """Xác nhận nạp tiền ví thành công từ webhook của cổng thanh toán. Khóa row chống race condition."""
        # Lock transaction
        locked_txn = (
            await db.execute(
                select(WalletTransaction)
                .where(WalletTransaction.id == transaction_id)
                .with_for_update()
            )
        ).scalars().first()

        if not locked_txn:
            raise HTTPException(status_code=404, detail="Transaction not found")
        if locked_txn.type != "topup":
            raise HTTPException(status_code=400, detail="Transaction is not a topup")
        if locked_txn.status != "pending":
            raise HTTPException(status_code=400, detail=f"Transaction already {locked_txn.status}")

        # Lock wallet
        locked_wallet = (
            await db.execute(
                select(Wallet).where(Wallet.id == locked_txn.wallet_id).with_for_update()
            )
        ).scalars().first()

        if not locked_wallet:
            raise HTTPException(status_code=404, detail="Wallet not found")

        # Credit wallet & update txn
        amount = Decimal(str(locked_txn.amount))
        locked_wallet.balance = Decimal(str(locked_wallet.balance)) + amount
        locked_wallet.updated_at = datetime.now(tz=timezone.utc)

        locked_txn.status = "completed"
        locked_txn.balance_after = locked_wallet.balance
        locked_txn.gateway_ref = gateway_ref
        if gateway_ref:
            locked_txn.description = f"{locked_txn.description} (Ref: {gateway_ref})"

        await db.flush()
        logger.info(
            "[WALLET] Topup completed - wallet_id=%s amount=%s balance_after=%s txn_id=%s gateway_ref=%s",
            locked_wallet.id, amount, locked_wallet.balance, locked_txn.id, gateway_ref,
        )
        return locked_txn
