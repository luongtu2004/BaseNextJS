"""Pydantic schemas for Phase 9.1 — Rating & Reviews."""
from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


# ─────────────────────────────────────────────────────────────────────
# Request schemas
# ─────────────────────────────────────────────────────────────────────


class CreateReviewRequest(BaseModel):
    """Payload gửi lên khi đánh giá sau chuyến."""

    rating: int = Field(
        ge=1, le=5, description="Điểm đánh giá từ 1 (tệ nhất) đến 5 (xuất sắc)"
    )
    comment: str | None = Field(
        default=None,
        max_length=1000,
        description="Nhận xét bổ sung (tùy chọn)",
    )


# ─────────────────────────────────────────────────────────────────────
# Response schemas
# ─────────────────────────────────────────────────────────────────────


class ReviewItem(BaseModel):
    """Một review sau chuyến — dùng trong danh sách và chi tiết."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID = Field(description="UUID review")
    booking_id: uuid.UUID = Field(description="UUID chuyến đi liên quan")
    reviewer_id: uuid.UUID = Field(description="UUID người đánh giá")
    reviewee_id: uuid.UUID = Field(description="UUID người được đánh giá")
    reviewer_role: str = Field(description="Vai trò người đánh giá: 'customer' | 'provider'")
    rating: int = Field(description="Điểm đánh giá 1-5")
    comment: str | None = Field(description="Nhận xét")
    is_visible: bool = Field(description="True nếu review đang hiển thị công khai")
    created_at: datetime = Field(description="Thời điểm tạo review")


class ReviewListResponse(BaseModel):
    """Pagination wrapper cho danh sách reviews."""

    items: list[ReviewItem] = Field(description="Danh sách review")
    page: int = Field(description="Trang hiện tại")
    page_size: int = Field(description="Số item mỗi trang")
    total: int = Field(description="Tổng số review")


class ReviewVisibilityUpdate(BaseModel):
    """Admin toggle visibility của review."""

    is_visible: bool = Field(description="True = hiển thị, False = ẩn")
