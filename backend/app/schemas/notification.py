"""Pydantic schemas for Phase 9.2 — Notifications & Notification Settings."""
from __future__ import annotations

import uuid
from datetime import datetime


from pydantic import BaseModel, ConfigDict, Field


# ─────────────────────────────────────────────────────────────────────
# Notification types — tham chiếu (không enforce ở schema level)
# booking_accepted / trip_completed / payment_received / review_received
# admin_broadcast / promotion / system / booking_updates
# ─────────────────────────────────────────────────────────────────────

VALID_NOTIFICATION_TYPES = {
    "booking_updates",
    "review_received",
    "promotion",
    "admin_broadcast",
    "system",
}


# ─────────────────────────────────────────────────────────────────────
# Notification response schemas
# ─────────────────────────────────────────────────────────────────────


class NotificationItem(BaseModel):
    """Một thông báo in-app."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID = Field(description="UUID thông báo")
    user_id: uuid.UUID = Field(description="UUID user nhận thông báo")
    type: str = Field(description="Loại thông báo")
    title: str = Field(description="Tiêu đề thông báo")
    body: str | None = Field(description="Nội dung chi tiết")
    # dict without type params: JSONB payload with dynamic structure from various modules
    data: dict | None = Field(description="Payload bổ sung (deep link, booking_id, ...)")
    is_read: bool = Field(description="Đã đọc hay chưa")
    read_at: datetime | None = Field(description="Thời điểm đọc")
    created_at: datetime = Field(description="Thời điểm tạo")


class NotificationListResponse(BaseModel):
    """Pagination wrapper cho danh sách thông báo."""

    items: list[NotificationItem] = Field(description="Danh sách thông báo")
    page: int = Field(description="Trang hiện tại")
    page_size: int = Field(description="Số item mỗi trang")
    total: int = Field(description="Tổng số thông báo")


class UnreadCountResponse(BaseModel):
    """Số thông báo chưa đọc — dùng cho badge icon trên app."""

    count: int = Field(description="Số thông báo chưa đọc")


# ─────────────────────────────────────────────────────────────────────
# Notification settings schemas
# ─────────────────────────────────────────────────────────────────────


class NotificationSettingItem(BaseModel):
    """Cấu hình on/off cho một loại thông báo."""

    model_config = ConfigDict(from_attributes=True)

    notification_type: str = Field(description="Loại thông báo")
    is_enabled: bool = Field(description="True = bật, False = tắt")


class NotificationSettingsResponse(BaseModel):
    """Toàn bộ cấu hình notification của user."""

    settings: list[NotificationSettingItem] = Field(
        description="Danh sách cấu hình theo từng loại thông báo"
    )


class NotificationSettingUpdate(BaseModel):
    """Một item trong batch update cấu hình."""

    notification_type: str = Field(
        description="Loại thông báo cần cập nhật", max_length=50
    )
    is_enabled: bool = Field(description="True = bật, False = tắt")


class UpdateNotificationSettingsRequest(BaseModel):
    """Batch update cấu hình thông báo — upsert theo từng type."""

    settings: list[NotificationSettingUpdate] = Field(
        min_length=1,
        description="Danh sách cấu hình cần cập nhật",
    )


# ─────────────────────────────────────────────────────────────────────
# Admin broadcast schema
# ─────────────────────────────────────────────────────────────────────


class BroadcastNotificationRequest(BaseModel):
    """Admin gửi thông báo hàng loạt."""

    title: str = Field(max_length=200, description="Tiêu đề thông báo")
    body: str | None = Field(default=None, description="Nội dung chi tiết")
    type: str = Field(
        default="admin_broadcast",
        max_length=50,
        description="Loại thông báo (mặc định: admin_broadcast)",
    )
    target_roles: list[str] | None = Field(
        default=None,
        description="Vai trò nhận: ['customer'] / ['provider'] / ['customer','provider']. None = tất cả",
    )
    # dict without type params: JSONB payload with dynamic structure from admin broadcast
    data: dict | None = Field(
        default=None,
        description="Payload bổ sung (deep link, promotion_id, ...)",
    )


class BroadcastNotificationResponse(BaseModel):
    """Kết quả sau khi admin broadcast."""

    sent_count: int = Field(description="Số notification đã tạo")
    skipped_count: int = Field(description="Số user bị skip do đã tắt loại notification này")
