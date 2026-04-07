"""Admin Notification API — Phase 9.2.

Endpoints:
  POST  /admin/notifications/broadcast  ANF1 — Gửi thông báo hàng loạt
"""
from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_admin_user
from app.db.session import get_db
from app.models.user import User, UserRole
from app.schemas.notification import (
    BroadcastNotificationRequest,
    BroadcastNotificationResponse,
)
from app.services import notification_service

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Admin / Notifications"])


# ─────────────────────────────────────────────────────────────────────
# ANF1 — Admin broadcast notification
# ─────────────────────────────────────────────────────────────────────


@router.post(
    "/notifications/broadcast",
    response_model=BroadcastNotificationResponse,
    status_code=status.HTTP_200_OK,
    summary="Gửi thông báo hàng loạt",
    description=(
        "Admin gửi thông báo đến tất cả user hoặc theo vai trò (customer/provider). "
        "Tự động bỏ qua user đã tắt loại thông báo này."
    ),
)
async def admin_broadcast_notification(
    payload: BroadcastNotificationRequest,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin_user),
) -> BroadcastNotificationResponse:
    """Admin gửi thông báo hàng loạt đến user theo role.

    Kiểm tra notification_settings của từng user — skip nếu đã tắt.
    Tạo 1 notification record per target user.

    Args:
        payload: Nội dung, loại thông báo, target_roles và data bổ sung.
        db: Async DB session.
        current_admin: Admin đang đăng nhập.

    Returns:
        BroadcastNotificationResponse chứa sent_count và skipped_count.
    """
    logger.info(
        "[NOTIFICATION] Admin %s broadcasting type='%s' to roles=%s",
        current_admin.id,
        payload.type,
        payload.target_roles,
    )

    # Build query lấy user_ids theo target_roles
    stmt = select(User.id).where(User.status == "active")
    if payload.target_roles:
        # Filter theo role — join UserRole
        stmt = (
            select(User.id)
            .join(UserRole, UserRole.user_id == User.id)
            .where(
                User.status == "active",
                UserRole.role_code.in_(payload.target_roles),
            )
            .distinct()
        )


    user_ids = list((await db.execute(stmt)).scalars().all())

    if not user_ids:
        return BroadcastNotificationResponse(sent_count=0, skipped_count=0)

    sent, skipped = await notification_service.bulk_create_notifications(
        db,
        user_ids=user_ids,
        notification_type=payload.type,
        title=payload.title,
        body=payload.body,
        data=payload.data,
    )
    await db.commit()

    return BroadcastNotificationResponse(sent_count=sent, skipped_count=skipped)
