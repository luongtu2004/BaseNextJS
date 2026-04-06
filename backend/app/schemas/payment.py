from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


# ─────────────────────────────────────────────────────────────────────
# Wallet
# ─────────────────────────────────────────────────────────────────────

class WalletResponse(BaseModel):
    """Thông tin ví người dùng."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    balance: Decimal = Field(description="Số dư hiện tại")
    currency: str = Field(description="Đơn vị tiền tệ (VND/USD)")
    is_frozen: bool = Field(description="Ví bị đóng băng")
    created_at: datetime
    updated_at: datetime


class WalletTransactionResponse(BaseModel):
    """Chi tiết một giao dịch trong ví."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    wallet_id: uuid.UUID
    type: str = Field(description="Loại giao dịch (topup/payment/refund/withdrawal/earning/commission/bonus/penalty/adjust)")
    amount: float = Field(description="Số tiền (dương=credit, âm=debit)")
    balance_after: float = Field(description="Số dư sau giao dịch")
    reference_id: uuid.UUID | None = Field(default=None, description="ID tham chiếu (booking/payment)")
    reference_type: str | None = Field(default=None, description="Loại tham chiếu")
    description: str | None = None
    status: str = Field(description="pending/completed/failed/reversed")
    created_at: datetime


class WalletTopupRequest(BaseModel):
    """Yêu cầu nạp tiền vào ví."""

    amount: float = Field(gt=0, description="Số tiền nạp (VND)")
    method: Literal["vnpay", "momo", "zalopay"] = Field(description="Cổng thanh toán")


class WalletTopupResponse(BaseModel):
    """Kết quả khởi tạo nạp tiền — trả redirect URL cổng thanh toán."""

    transaction_id: uuid.UUID = Field(description="ID giao dịch nạp tiền")
    payment_url: str = Field(description="URL redirect sang cổng thanh toán")
    amount: float
    method: str


class WithdrawalRequest(BaseModel):
    """Yêu cầu rút tiền từ ví tài xế."""

    amount: float = Field(gt=0, description="Số tiền rút (VND)")
    bank_name: str | None = Field(default=None, max_length=200, description="Tên ngân hàng")
    bank_account: str | None = Field(default=None, max_length=50, description="Số tài khoản")


# ─────────────────────────────────────────────────────────────────────
# Payment Transactions
# ─────────────────────────────────────────────────────────────────────

class PaymentTransactionResponse(BaseModel):
    """Response chứa thông tin giao dịch thanh toán qua cổng."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    booking_id: uuid.UUID
    user_id: uuid.UUID
    amount: float
    method: str
    gateway_ref: str | None = None
    status: str
    paid_at: datetime | None = None
    refunded_at: datetime | None = None
    refund_amount: float | None = None
    created_at: datetime
    updated_at: datetime


# ─────────────────────────────────────────────────────────────────────
# Promotions
# ─────────────────────────────────────────────────────────────────────

class PromotionCreate(BaseModel):
    """Payload tạo chương trình khuyến mãi mới."""

    code: str = Field(min_length=2, max_length=50, description="Mã giảm giá (unique)")
    name: str = Field(min_length=2, max_length=200, description="Tên chương trình")
    type: Literal["percent", "fixed", "free_trip"] = Field(description="Loại giảm giá")
    value: float = Field(gt=0, description="Giá trị giảm (% hoặc VND)")
    max_discount: float | None = Field(default=None, ge=0, description="Giảm tối đa (dùng khi type=percent)")
    min_fare: float | None = Field(default=None, ge=0, description="Đơn tối thiểu để áp dụng")
    usage_limit: int | None = Field(default=None, ge=1, description="Tổng lượt dùng tối đa")
    per_user_limit: int = Field(default=1, ge=1, description="Số lần tối đa mỗi user")
    valid_from: datetime = Field(description="Bắt đầu hiệu lực")
    valid_to: datetime = Field(description="Hết hiệu lực")
    service_types: list[str] | None = Field(default=None, description="Loại dịch vụ áp dụng (null=tất cả)")


class PromotionUpdate(BaseModel):
    """Cập nhật khuyến mãi (exclude_unset)."""

    name: str | None = Field(default=None, min_length=2, max_length=200)
    value: float | None = Field(default=None, gt=0)
    max_discount: float | None = Field(default=None, ge=0)
    min_fare: float | None = Field(default=None, ge=0)
    usage_limit: int | None = Field(default=None, ge=1)
    per_user_limit: int | None = Field(default=None, ge=1)
    valid_from: datetime | None = None
    valid_to: datetime | None = None
    service_types: list[str] | None = None


class PromotionStatusPatch(BaseModel):
    """Bật/tắt khuyến mãi."""

    is_active: bool


class PromotionResponse(BaseModel):
    """Response chi tiết khuyến mãi."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    code: str
    name: str
    type: str
    value: float
    max_discount: float | None = None
    min_fare: float | None = None
    usage_limit: int | None = None
    used_count: int
    per_user_limit: int | None = None
    valid_from: datetime
    valid_to: datetime
    service_types: list[str] | None = None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class PromotionUsageResponse(BaseModel):
    """Lịch sử dùng mã giảm giá."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    promotion_id: uuid.UUID
    user_id: uuid.UUID
    booking_id: uuid.UUID
    discount_amount: float
    used_at: datetime


class PromotionValidateRequest(BaseModel):
    """Yêu cầu validate mã giảm giá."""

    code: str = Field(min_length=1, max_length=50, description="Mã giảm giá")
    service_type: str = Field(description="Loại dịch vụ")
    fare: float = Field(gt=0, description="Cước phí trước giảm")


class PromotionValidateResponse(BaseModel):
    """Kết quả validate mã giảm giá."""

    valid: bool
    promotion_id: uuid.UUID | None = None
    code: str
    discount_amount: float = Field(default=0, description="Số tiền giảm")
    final_fare: float = Field(description="Cước phí sau giảm")
    message: str | None = None


# ─────────────────────────────────────────────────────────────────────
# Admin Finance
# ─────────────────────────────────────────────────────────────────────

class WalletAdjustRequest(BaseModel):
    """Admin điều chỉnh số dư ví (bonus/phạt)."""

    amount: float = Field(description="Số tiền điều chỉnh (dương=bonus, âm=phạt)")
    description: str = Field(min_length=5, max_length=500, description="Lý do điều chỉnh")


class EarningsSummaryResponse(BaseModel):
    """Tổng thu nhập tài xế."""

    today: float = Field(default=0, description="Thu nhập hôm nay")
    this_week: float = Field(default=0, description="Thu nhập tuần này")
    this_month: float = Field(default=0, description="Thu nhập tháng này")
    total_trips_today: int = Field(default=0, description="Số chuyến hôm nay")
    total_commission_today: float = Field(default=0, description="Hoa hồng hôm nay")


class EarningsDailyResponse(BaseModel):
    """Thu nhập theo từng ngày."""

    date: str = Field(description="Ngày (YYYY-MM-DD)")
    earnings: float = Field(description="Thu nhập ròng")
    commission: float = Field(description="Hoa hồng")
    trips: int = Field(description="Số chuyến")


class RevenueResponse(BaseModel):
    """Doanh thu nền tảng theo ngày."""

    date: str
    total_commission: float = Field(description="Tổng hoa hồng")
    total_trips: int = Field(description="Tổng số chuyến")
    total_fare: float = Field(description="Tổng cước phí")
