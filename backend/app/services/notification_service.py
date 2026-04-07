"""Notification Service — Phase 9.2.

Helper service để tạo notification records từ các module khác (booking, review, payment).
Kiểm tra notification_settings trước khi INSERT — nếu user đã tắt loại đó thì skip.

In Phase 11 (WS Server), thêm PUBLISH Redis sau INSERT để WS broadcast real-time.
"""
from __future__ import annotations

import logging
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import Notification, NotificationSetting

logger = logging.getLogger(__name__)


async def is_notification_enabled(
    db: AsyncSession,
    user_id: uuid.UUID,
    notification_type: str,
) -> bool:
    """Kiểm tra user có bật loại notification này không.

    Nếu chưa có setting record → mặc định True (opt-in by default).

    Args:
        db: Async DB session.
        user_id: UUID của user cần kiểm tra.
        notification_type: Loại notification (booking_updates, promotion, ...).

    Returns:
        True nếu user muốn nhận, False nếu đã tắt.
    """
    stmt = select(NotificationSetting).where(
        NotificationSetting.user_id == user_id,
        NotificationSetting.notification_type == notification_type,
    )
    setting = (await db.execute(stmt)).scalar_one_or_none()
    # Không có record → opt-in by default
    return setting.is_enabled if setting else True


async def create_notification(
    db: AsyncSession,
    user_id: uuid.UUID,
    notification_type: str,
    title: str,
    body: str | None = None,
    # Any justified: JSONB payload with dynamic structure from booking/review/payment modules
    data: dict | None = None,
    *,
    check_settings: bool = True,
) -> Notification | None:
    """Tạo notification record cho user.

    Kiểm tra notification_settings trước khi INSERT.
    Notification type 'system' luôn được gửi bất kể settings.

    In Phase 11: sau INSERT, PUBLISH lên Redis channel 'notifications:{user_id}'
    để WS Server broadcast đến client đang connected.

    Args:
        db: Async DB session.
        user_id: UUID user nhận thông báo.
        notification_type: Loại thông báo.
        title: Tiêu đề thông báo.
        body: Nội dung chi tiết (tùy chọn).
        data: Payload bổ sung — deep link, booking_id, review_id, ... (tùy chọn).
        check_settings: Nếu True, kiểm tra notification_settings trước khi INSERT.
            Truyền False cho system notifications (luôn gửi).

    Returns:
        Notification object nếu tạo thành công, None nếu user đã tắt loại này.
    """
    # System notifications luôn gửi, các loại khác check settings
    if check_settings and notification_type != "system":
        enabled = await is_notification_enabled(db, user_id, notification_type)
        if not enabled:
            logger.debug(
                "[NOTIFICATION] User %s disabled type '%s', skipping",
                user_id,
                notification_type,
            )
            return None

    notification = Notification(
        id=uuid.uuid4(),
        user_id=user_id,
        type=notification_type,
        title=title,
        body=body,
        data=data,
    )
    db.add(notification)
    # NOTE: Không commit ở đây — caller chịu trách nhiệm commit (cho phép atomic với business logic)

    # TODO Phase 11: PUBLISH Redis channel f"notifications:{user_id}" để WS broadcast
    # await redis.publish(f"notifications:{user_id}", json.dumps({
    #     "type": "notification",
    #     "payload": {"title": title, "body": body, "notification_type": notification_type, "data": data}
    # }))

    logger.info(
        "[NOTIFICATION] Created notification type='%s' for user %s",
        notification_type,
        user_id,
    )
    return notification


async def bulk_create_notifications(
    db: AsyncSession,
    user_ids: list[uuid.UUID],
    notification_type: str,
    title: str,
    body: str | None = None,
    # Any justified: JSONB payload with dynamic structure from admin broadcast
    data: dict | None = None,
) -> tuple[int, int]:
    """Tạo notification hàng loạt cho nhiều users.

    Performance: batch SELECT tất cả disabled settings 1 lần,
    rồi filter in-memory trước khi bulk INSERT — tránh N+1 queries.

    Args:
        db: Async DB session.
        user_ids: Danh sách UUID users cần gửi.
        notification_type: Loại thông báo.
        title: Tiêu đề.
        body: Nội dung chi tiết.
        data: Payload bổ sung.

    Returns:
        Tuple (sent_count, skipped_count).
    """
    if not user_ids:
        return 0, 0

    # Batch fetch: 1 query lấy tất cả users đã tắt loại notification này
    disabled_stmt = select(NotificationSetting.user_id).where(
        NotificationSetting.notification_type == notification_type,
        NotificationSetting.user_id.in_(user_ids),
        NotificationSetting.is_enabled.is_(False),
    )
    disabled_user_ids = set((await db.execute(disabled_stmt)).scalars().all())

    # Filter eligible users in-memory
    eligible_ids = [uid for uid in user_ids if uid not in disabled_user_ids]
    skipped = len(user_ids) - len(eligible_ids)

    # Bulk add — single flush at the end
    for user_id in eligible_ids:
        notification = Notification(
            id=uuid.uuid4(),
            user_id=user_id,
            type=notification_type,
            title=title,
            body=body,
            data=data,
        )
        db.add(notification)

    sent = len(eligible_ids)
    logger.info(
        "[NOTIFICATION] Bulk created: sent=%d, skipped=%d, type='%s'",
        sent, skipped, notification_type,
    )
    return sent, skipped
