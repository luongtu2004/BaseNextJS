from __future__ import annotations

import logging
import secrets
import string
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

from app.models.booking import Booking, BookingStatusLog, PriceConfig
from app.schemas.booking import BookingCreate

_BOARDING_OTP_TTL_SECONDS = 30 * 60  # 30 minutes



class BookingService:
    @staticmethod
    async def get_active_price_config(db: AsyncSession, service_type: str) -> PriceConfig | None:
        """Lấy cấu hình giá đang hoạt động cho loại dịch vụ.

        Args:
            db: Async DB session.
            service_type: Mã loại dịch vụ (ví dụ: 'xe_om', 'taxi').

        Returns:
            PriceConfig đang active mới nhất, hoặc None nếu chưa cấu hình.
        """
        stmt = select(PriceConfig).where(
            PriceConfig.service_type == service_type,
            PriceConfig.is_active.is_(True),
        ).order_by(PriceConfig.created_at.desc())
        return (await db.execute(stmt)).scalars().first()

    @staticmethod
    async def calculate_fare(
        db: AsyncSession, service_type: str, distance_km: float, duration_min: int
    ) -> tuple[str, float | None, float | None, float | None]:
        """Tính toán cước phí hoặc khoảng giá theo cấu hình giá hiện hành.

        Args:
            db: Async DB session.
            service_type: Mã loại dịch vụ.
            distance_km: Khoảng cách ước tính (km).
            duration_min: Thời gian ước tính (phút).

        Returns:
            Tuple (pricing_mode, estimated_fare, min_quote, max_quote) trong đó
            pricing_mode là 'formula' hoặc 'driver_quote'.
        """
        config = await BookingService.get_active_price_config(db, service_type)
        if not config:
            # Fallback nếu không có cấu hình (trong phase MVP trả default)
            return "driver_quote", None, None, None
            
        if config.pricing_mode == "formula":
            base = float(config.base_fare or 0.0)
            pkm = float(config.fare_per_km or 0.0) * distance_km
            pmin = float(config.fare_per_min or 0.0) * duration_min
            
            total = base + pkm + pmin
            if config.surge_enabled and config.surge_multiplier:
                total *= float(config.surge_multiplier)
                
            if config.min_fare and total < float(config.min_fare):
                total = float(config.min_fare)
                
            return "formula", round(total, 0), None, None
            
        else: # driver_quote
            min_q = float(config.min_quote) if config.min_quote else None
            max_q = float(config.max_quote) if config.max_quote else None
            return "driver_quote", None, min_q, max_q


    @staticmethod
    async def create_booking(
        db: AsyncSession,
        customer_id: uuid.UUID,
        payload: BookingCreate,
    ) -> Booking:
        """Tạo booking mới cho khách hàng.

        Args:
            db: Async DB session.
            customer_id: UUID của khách hàng đặt chuyến.
            payload: Thông tin booking (service_type, toạ độ, ghi chú).

        Returns:
            Booking mới với trạng thái 'pending' và mã OTP lên xe.

        Raises:
            HTTPException 400: Nếu service_type không hợp lệ.
        """
        logger.info("[BOOKING] Creating booking - customer_id=%s service_type=%s", customer_id, payload.service_type)
        from app.models.taxonomy import ServiceCategory
        
        category = (await db.execute(select(ServiceCategory).where(ServiceCategory.code == payload.service_type))).scalars().first()
        if not category:
            raise HTTPException(status_code=400, detail="Invalid service type")
            
        distance_km = 5.0
        duration_min = 15

        mode, est_fare, min_q, max_q = await BookingService.calculate_fare(
            db, payload.service_type, distance_km, duration_min
        )

        otp = "".join(secrets.choice(string.digits) for _ in range(4))
        otp_expires = datetime.now(tz=timezone.utc) + timedelta(seconds=_BOARDING_OTP_TTL_SECONDS)

        booking = Booking(
            id=uuid.uuid4(),
            customer_id=customer_id,
            service_category_id=category.id,
            service_type=payload.service_type,
            status="pending",
            pricing_mode=mode,
            estimated_fare=est_fare,
            distance_km=distance_km,
            duration_min=duration_min,
            pickup_lat=payload.pickup_lat,
            pickup_lng=payload.pickup_lng,
            pickup_address=payload.pickup_address,
            dropoff_lat=payload.dropoff_lat,
            dropoff_lng=payload.dropoff_lng,
            dropoff_address=payload.dropoff_address,
            boarding_otp=otp,
            boarding_otp_expires=otp_expires,
            notes=payload.notes,
        )
        db.add(booking)
        await db.flush()

        log = BookingStatusLog(
            id=uuid.uuid4(),
            booking_id=booking.id,
            from_status=None,
            to_status="pending",
            changed_by=customer_id,
            note="Customer created booking"
        )
        db.add(log)
        await db.flush()
        logger.info("[BOOKING] Booking created - booking_id=%s customer_id=%s", booking.id, customer_id)
        return booking

    @staticmethod
    async def get_booking(db: AsyncSession, booking_id: uuid.UUID) -> Booking:
        """Lấy booking theo ID hoặc raise 404.

        Args:
            db: Async DB session.
            booking_id: UUID của booking.

        Returns:
            Booking tìm thấy.

        Raises:
            HTTPException 404: Nếu booking không tồn tại.
        """
        bk = await db.get(Booking, booking_id)
        if not bk:
            raise HTTPException(status_code=404, detail="Booking not found")
        return bk

    @staticmethod
    async def cancel_booking(db: AsyncSession, booking_id: uuid.UUID, customer_id: uuid.UUID) -> Booking:
        """Khách hàng hủy chuyến đang ở trạng thái pending hoặc accepted.

        Args:
            db: Async DB session.
            booking_id: UUID của booking cần hủy.
            customer_id: UUID của khách hàng thực hiện hủy.

        Returns:
            Booking đã cập nhật sang trạng thái 'cancelled'.

        Raises:
            HTTPException 403: Nếu customer không phải chủ booking.
            HTTPException 400: Nếu booking không thể hủy ở trạng thái hiện tại.
        """
        bk = await BookingService.get_booking(db, booking_id)
        if bk.customer_id != customer_id:
            raise HTTPException(status_code=403, detail="Not authorized to cancel this booking")
        if bk.status not in ("pending", "accepted"):
            raise HTTPException(status_code=400, detail=f"Cannot cancel booking in '{bk.status}' state")

        old_status = bk.status  # Capture BEFORE mutation
        bk.status = "cancelled"
        bk.cancelled_at = datetime.now(tz=timezone.utc)

        log = BookingStatusLog(
            id=uuid.uuid4(),
            booking_id=bk.id,
            from_status=old_status,
            to_status="cancelled",
            changed_by=customer_id,
            note="Customer cancelled booking"
        )
        db.add(log)
        await db.flush()
        logger.info("[BOOKING] Booking cancelled by customer - booking_id=%s customer_id=%s", booking_id, customer_id)
        return bk

    @staticmethod
    async def accept_booking(db: AsyncSession, booking_id: uuid.UUID, provider_id: uuid.UUID) -> Booking:
        """Provider nhận cuốc xe.

        Args:
            db: Async DB session.
            booking_id: UUID của booking cần nhận.
            provider_id: UUID của provider.

        Returns:
            Booking đã cập nhật sang trạng thái 'accepted'.

        Raises:
            HTTPException 400: Nếu booking không còn ở trạng thái pending.
        """
        bk = await BookingService.get_booking(db, booking_id)
        if bk.status != "pending":
            raise HTTPException(status_code=400, detail="Booking is no longer pending")

        old_status = bk.status
        bk.status = "accepted"
        bk.provider_id = provider_id
        bk.accepted_at = datetime.now(tz=timezone.utc)

        log = BookingStatusLog(
            id=uuid.uuid4(),
            booking_id=bk.id,
            from_status=old_status,
            to_status="accepted",
            changed_by=provider_id,
            note="Provider accepted booking"
        )
        db.add(log)
        await db.flush()
        logger.info("[BOOKING] Booking accepted - booking_id=%s provider_id=%s", booking_id, provider_id)
        return bk

    @staticmethod
    async def update_trip_state(
        db: AsyncSession,
        booking_id: uuid.UUID,
        provider_id: uuid.UUID,
        action: str,
        otp: str | None = None,
    ) -> Booking:
        """Cập nhật trạng thái chuyến đi theo lifecycle (arrive -> board -> complete).

        Args:
            db: Async DB session.
            booking_id: UUID của booking.
            provider_id: UUID của provider đang thực hiện.
            action: Hành động cần thực hiện ('arrive', 'board', 'complete').
            otp: Mã OTP từ khách hàng (bắt buộc với action 'board').

        Returns:
            Booking đã cập nhật trạng thái mới.

        Raises:
            HTTPException 403: Nếu provider không phải chủ booking.
            HTTPException 400: Nếu chuyển trạng thái không hợp lệ hoặc OTP sai.
        """
        bk = await BookingService.get_booking(db, booking_id)
        if bk.provider_id != provider_id:
            raise HTTPException(status_code=403, detail="Not authorized to update this booking")

        old_status = bk.status
        now = datetime.now(tz=timezone.utc)

        if action == "arrive":
            if bk.status != "accepted":
                raise HTTPException(status_code=400, detail=f"Cannot arrive from '{bk.status}' state")
            bk.status = "arrived"
            bk.arrived_at = now

        elif action == "board":
            if bk.status != "arrived":
                raise HTTPException(status_code=400, detail=f"Cannot board from '{bk.status}' state")
            if not otp or bk.boarding_otp != otp:
                raise HTTPException(status_code=400, detail="Invalid Boarding OTP")
            if bk.boarding_otp_expires:
                expires = bk.boarding_otp_expires
                # SQLite returns naive datetimes; treat them as UTC for comparison
                if expires.tzinfo is None:
                    expires = expires.replace(tzinfo=timezone.utc)
                if datetime.now(tz=timezone.utc) > expires:
                    raise HTTPException(status_code=400, detail="Boarding OTP has expired")
            bk.status = "boarded"
            bk.started_at = now

        elif action == "complete":
            if bk.status != "boarded":
                raise HTTPException(status_code=400, detail=f"Cannot complete from '{bk.status}' state")
            bk.status = "completed"
            bk.completed_at = now

        else:
            raise HTTPException(status_code=400, detail=f"Invalid trip action: '{action}'")

        log = BookingStatusLog(
            id=uuid.uuid4(),
            booking_id=bk.id,
            from_status=old_status,
            to_status=bk.status,
            changed_by=provider_id,
            note=f"Provider executed action: {action}",
        )
        db.add(log)
        await db.flush()
        logger.info(
            "[BOOKING] Trip state updated - booking_id=%s action=%s new_status=%s provider_id=%s",
            booking_id, action, bk.status, provider_id,
        )
        return bk
