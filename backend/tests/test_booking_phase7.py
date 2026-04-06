"""Integration tests — Phase 7: Booking & Orders.

Covers all endpoints created in Phase 7:
  Customer API:
    POST   /customer/transport/estimate
    POST   /customer/transport/booking
    GET    /customer/transport/booking/{id}
    POST   /customer/transport/booking/{id}/cancel

  Provider API:
    GET    /provider/transport/booking/available
    POST   /provider/transport/booking/{id}/accept
    POST   /provider/transport/booking/{id}/arrive
    POST   /provider/transport/booking/{id}/board
    POST   /provider/transport/booking/{id}/complete
    POST   /provider/transport/booking/availability/online
    POST   /provider/transport/booking/availability/offline
    POST   /provider/transport/booking/location

Tests validate: happy paths, error paths, authorization, pagination,
                state-machine transitions, OTP verification.
"""

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token
from app.models.booking import PriceConfig
from app.models.provider import Provider
from tests.conftest import auth_headers, create_provider, create_service_category, create_user

pytestmark = pytest.mark.asyncio


# ─────────────────────────────────────────────────────────────────────
# Shared Helpers
# ─────────────────────────────────────────────────────────────────────

async def _setup_customer(db: AsyncSession, phone: str = "+84100000001"):
    """Seed a customer user and return (user, token)."""
    user = await create_user(db, phone=phone, role="customer")
    token = create_access_token(str(user.id), ["customer"])
    return user, token


async def _setup_provider(db: AsyncSession, phone: str = "+84200000001"):
    """Seed a provider user+profile and return (user, provider, token)."""
    user = await create_user(db, phone=phone, role="provider")
    provider = await create_provider(db, user)
    token = create_access_token(str(user.id), ["provider"])
    return user, provider, token


async def _seed_price_config(db: AsyncSession, service_type: str = "xe_may"):
    """Seed a ServiceCategory + PriceConfig for given service_type."""
    await create_service_category(db, code=service_type)
    config = PriceConfig(
        id=uuid.uuid4(),
        service_type=service_type,
        pricing_mode="formula",
        base_fare=10000,
        fare_per_km=5000,
        fare_per_min=500,
        surge_enabled=False,
        is_active=True,
    )
    db.add(config)
    await db.commit()
    return config


BOOKING_PAYLOAD = {
    "service_type": "xe_may",
    "pickup_lat": 10.762622,
    "pickup_lng": 106.660172,
    "pickup_address": "Điểm A",
    "dropoff_lat": 10.776889,
    "dropoff_lng": 106.700806,
    "dropoff_address": "Điểm B",
}


async def _create_booking(client: AsyncClient, token: str, payload: dict | None = None) -> dict:
    """Helper to create a booking and return response JSON."""
    if payload is None:
        payload = BOOKING_PAYLOAD
    resp = await client.post(
        "/api/v1/customer/transport/booking",
        json=payload,
        headers=auth_headers(token),
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


# ─────────────────────────────────────────────────────────────────────
# Customer: Fare Estimate
# ─────────────────────────────────────────────────────────────────────

class TestFareEstimate:
    async def test_estimate_formula_pricing(self, client: AsyncClient, db: AsyncSession):
        """Returns estimated fare for formula-based pricing."""
        await _seed_price_config(db)
        resp = await client.post(
            "/api/v1/customer/transport/estimate",
            json={"service_type": "xe_may", "distance_km": 10, "duration_min": 20},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["pricing_mode"] == "formula"
        assert data["estimated_fare"] is not None
        assert data["estimated_fare"] > 0

    async def test_estimate_unknown_service_returns_driver_quote(self, client: AsyncClient, db: AsyncSession):
        """Falls back to driver_quote mode when no config exists."""
        resp = await client.post(
            "/api/v1/customer/transport/estimate",
            json={"service_type": "unknown_svc", "distance_km": 5, "duration_min": 10},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["pricing_mode"] == "driver_quote"
        assert data["estimated_fare"] is None

    async def test_estimate_missing_fields_returns_422(self, client: AsyncClient, db: AsyncSession):
        """Returns 422 when required fields are missing."""
        resp = await client.post(
            "/api/v1/customer/transport/estimate",
            json={"service_type": "xe_may"},
        )
        assert resp.status_code == 422

    async def test_estimate_invalid_distance_returns_422(self, client: AsyncClient, db: AsyncSession):
        """Returns 422 when distance_km <= 0."""
        resp = await client.post(
            "/api/v1/customer/transport/estimate",
            json={"service_type": "xe_may", "distance_km": 0, "duration_min": 10},
        )
        assert resp.status_code == 422


# ─────────────────────────────────────────────────────────────────────
# Customer: Create Booking
# ─────────────────────────────────────────────────────────────────────

class TestCreateBooking:
    async def test_create_booking_success(self, client: AsyncClient, db: AsyncSession):
        """Customer can create a new pending booking with OTP."""
        _, cust_token = await _setup_customer(db)
        await _seed_price_config(db)

        resp = await client.post(
            "/api/v1/customer/transport/booking",
            json=BOOKING_PAYLOAD,
            headers=auth_headers(cust_token),
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["status"] == "pending"
        assert data["service_type"] == "xe_may"
        assert data["boarding_otp"] is not None
        assert len(data["boarding_otp"]) == 4
        assert data["boarding_otp"].isdigit()
        assert data["estimated_fare"] is not None
        assert data["pickup_address"] == "Điểm A"

    async def test_create_booking_unauthenticated_returns_401(self, client: AsyncClient, db: AsyncSession):
        """Returns 401 without auth token."""
        await _seed_price_config(db)
        resp = await client.post("/api/v1/customer/transport/booking", json=BOOKING_PAYLOAD)
        assert resp.status_code == 401

    async def test_create_booking_invalid_service_type_returns_400(
        self, client: AsyncClient, db: AsyncSession
    ):
        """Returns 400 for unknown service_type (no ServiceCategory)."""
        _, cust_token = await _setup_customer(db)
        resp = await client.post(
            "/api/v1/customer/transport/booking",
            json={**BOOKING_PAYLOAD, "service_type": "phantom_svc"},
            headers=auth_headers(cust_token),
        )
        assert resp.status_code == 400

    async def test_create_booking_with_notes(self, client: AsyncClient, db: AsyncSession):
        """Customer can add notes to booking."""
        _, cust_token = await _setup_customer(db)
        await _seed_price_config(db)
        payload = {**BOOKING_PAYLOAD, "notes": "Gọi trước 5 phút"}
        data = await _create_booking(client, cust_token, payload)
        assert data["notes"] == "Gọi trước 5 phút"

    async def test_create_booking_missing_pickup_returns_422(self, client: AsyncClient, db: AsyncSession):
        """Returns 422 when pickup coordinates are missing."""
        _, cust_token = await _setup_customer(db)
        await _seed_price_config(db)
        resp = await client.post(
            "/api/v1/customer/transport/booking",
            json={"service_type": "xe_may"},
            headers=auth_headers(cust_token),
        )
        assert resp.status_code == 422


# ─────────────────────────────────────────────────────────────────────
# Customer: Get Booking Status
# ─────────────────────────────────────────────────────────────────────

class TestGetBookingStatus:
    async def test_get_own_booking_success(self, client: AsyncClient, db: AsyncSession):
        """Customer can retrieve their own booking."""
        _, cust_token = await _setup_customer(db)
        await _seed_price_config(db)
        booking = await _create_booking(client, cust_token)

        resp = await client.get(
            f"/api/v1/customer/transport/booking/{booking['id']}",
            headers=auth_headers(cust_token),
        )
        assert resp.status_code == 200
        assert resp.json()["id"] == booking["id"]
        assert resp.json()["status"] == "pending"

    async def test_get_other_customer_booking_returns_403(
        self, client: AsyncClient, db: AsyncSession
    ):
        """Cannot access another customer's booking."""
        _, cust_token_1 = await _setup_customer(db, phone="+84100000001")
        _, cust_token_2 = await _setup_customer(db, phone="+84100000002")
        await _seed_price_config(db)

        booking = await _create_booking(client, cust_token_1)

        resp = await client.get(
            f"/api/v1/customer/transport/booking/{booking['id']}",
            headers=auth_headers(cust_token_2),
        )
        assert resp.status_code == 403

    async def test_get_nonexistent_booking_returns_404(self, client: AsyncClient, db: AsyncSession):
        """Returns 404 for unknown booking ID."""
        _, cust_token = await _setup_customer(db)
        resp = await client.get(
            f"/api/v1/customer/transport/booking/{uuid.uuid4()}",
            headers=auth_headers(cust_token),
        )
        assert resp.status_code == 404


# ─────────────────────────────────────────────────────────────────────
# Customer: Cancel Booking
# ─────────────────────────────────────────────────────────────────────

class TestCancelBooking:
    async def test_cancel_pending_booking_success(self, client: AsyncClient, db: AsyncSession):
        """Customer can cancel a pending booking."""
        _, cust_token = await _setup_customer(db)
        await _seed_price_config(db)
        booking = await _create_booking(client, cust_token)

        resp = await client.post(
            f"/api/v1/customer/transport/booking/{booking['id']}/cancel",
            headers=auth_headers(cust_token),
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "cancelled"
        assert resp.json()["cancelled_at"] is not None

    async def test_cancel_sets_correct_from_status_in_log(self, client: AsyncClient, db: AsyncSession):
        """Verifies cancel does not log 'cancelled' as from_status (bug regression)."""
        from app.models.booking import BookingStatusLog
        from sqlalchemy import select

        _, cust_token = await _setup_customer(db)
        await _seed_price_config(db)
        booking = await _create_booking(client, cust_token)

        await client.post(
            f"/api/v1/customer/transport/booking/{booking['id']}/cancel",
            headers=auth_headers(cust_token),
        )

        logs = (
            await db.execute(
                select(BookingStatusLog).where(
                    BookingStatusLog.to_status == "cancelled"
                )
            )
        ).scalars().all()
        assert len(logs) == 1
        assert logs[0].from_status == "pending"  # Must NOT be "cancelled"

    async def test_cancel_other_customer_booking_returns_403(
        self, client: AsyncClient, db: AsyncSession
    ):
        """Cannot cancel another customer's booking."""
        _, token1 = await _setup_customer(db, phone="+84100000001")
        _, token2 = await _setup_customer(db, phone="+84100000002")
        await _seed_price_config(db)
        booking = await _create_booking(client, token1)

        resp = await client.post(
            f"/api/v1/customer/transport/booking/{booking['id']}/cancel",
            headers=auth_headers(token2),
        )
        assert resp.status_code == 403

    async def test_cancel_completed_booking_returns_400(self, client: AsyncClient, db: AsyncSession):
        """Cannot cancel a booking that is already completed."""
        _, cust_token = await _setup_customer(db)
        _, provider, prov_token = await _setup_provider(db)
        await _seed_price_config(db)
        booking = await _create_booking(client, cust_token)
        bid = booking["id"]
        otp = booking["boarding_otp"]

        # Complete the booking
        await client.post(f"/api/v1/provider/transport/booking/{bid}/accept", headers=auth_headers(prov_token))
        await client.post(f"/api/v1/provider/transport/booking/{bid}/arrive", headers=auth_headers(prov_token))
        await client.post(f"/api/v1/provider/transport/booking/{bid}/board?otp={otp}", headers=auth_headers(prov_token))
        await client.post(f"/api/v1/provider/transport/booking/{bid}/complete", headers=auth_headers(prov_token))

        resp = await client.post(
            f"/api/v1/customer/transport/booking/{bid}/cancel",
            headers=auth_headers(cust_token),
        )
        assert resp.status_code == 400
        assert "completed" in resp.json()["detail"]


# ─────────────────────────────────────────────────────────────────────
# Provider: Browse Available Bookings
# ─────────────────────────────────────────────────────────────────────

class TestListAvailableBookings:
    async def test_list_returns_pending_bookings(self, client: AsyncClient, db: AsyncSession):
        """Provider sees pending bookings."""
        _, cust_token = await _setup_customer(db)
        _, _, prov_token = await _setup_provider(db)
        await _seed_price_config(db)

        await _create_booking(client, cust_token)

        resp = await client.get(
            "/api/v1/provider/transport/booking/available",
            headers=auth_headers(prov_token),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "page_size" in data
        assert data["total"] >= 1

    async def test_list_filter_by_service_type(self, client: AsyncClient, db: AsyncSession):
        """Filter by service_type works correctly."""
        _, cust_token = await _setup_customer(db)
        _, _, prov_token = await _setup_provider(db)
        await _seed_price_config(db, service_type="xe_may")
        await _seed_price_config(db, service_type="xe_4_cho")

        # Create one of each type
        await _create_booking(client, cust_token, {**BOOKING_PAYLOAD, "service_type": "xe_may"})
        await _create_booking(client, cust_token, {**BOOKING_PAYLOAD, "service_type": "xe_4_cho"})

        resp = await client.get(
            "/api/v1/provider/transport/booking/available?service_type=xe_may",
            headers=auth_headers(prov_token),
        )
        assert resp.status_code == 200
        items = resp.json()["items"]
        assert all(b["service_type"] == "xe_may" for b in items)

    async def test_list_pagination_params(self, client: AsyncClient, db: AsyncSession):
        """Pagination params are reflected in response."""
        _, _, prov_token = await _setup_provider(db)
        resp = await client.get(
            "/api/v1/provider/transport/booking/available?page=2&page_size=5",
            headers=auth_headers(prov_token),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["page"] == 2
        assert data["page_size"] == 5

    async def test_list_unauthenticated_returns_401(self, client: AsyncClient, db: AsyncSession):
        """Returns 401 without token."""
        resp = await client.get("/api/v1/provider/transport/booking/available")
        assert resp.status_code == 401

    async def test_list_customer_role_returns_403(self, client: AsyncClient, db: AsyncSession):
        """Customer role cannot access provider endpoint."""
        _, cust_token = await _setup_customer(db)
        resp = await client.get(
            "/api/v1/provider/transport/booking/available",
            headers=auth_headers(cust_token),
        )
        assert resp.status_code == 403

    async def test_accepted_booking_not_in_list(self, client: AsyncClient, db: AsyncSession):
        """Already-accepted bookings do not appear in available list."""
        _, cust_token = await _setup_customer(db)
        _, _, prov_token = await _setup_provider(db)
        await _seed_price_config(db)
        booking = await _create_booking(client, cust_token)
        bid = booking["id"]

        await client.post(f"/api/v1/provider/transport/booking/{bid}/accept", headers=auth_headers(prov_token))

        resp = await client.get(
            "/api/v1/provider/transport/booking/available",
            headers=auth_headers(prov_token),
        )
        items = resp.json()["items"]
        assert not any(b["id"] == bid for b in items)


# ─────────────────────────────────────────────────────────────────────
# Provider: Accept Booking
# ─────────────────────────────────────────────────────────────────────

class TestAcceptBooking:
    async def test_accept_pending_booking_success(self, client: AsyncClient, db: AsyncSession):
        """Provider can accept a pending booking."""
        _, cust_token = await _setup_customer(db)
        _, _, prov_token = await _setup_provider(db)
        await _seed_price_config(db)
        booking = await _create_booking(client, cust_token)

        resp = await client.post(
            f"/api/v1/provider/transport/booking/{booking['id']}/accept",
            headers=auth_headers(prov_token),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "accepted"
        assert data["accepted_at"] is not None

    async def test_double_accept_returns_400(self, client: AsyncClient, db: AsyncSession):
        """Second provider cannot accept already-accepted booking."""
        _, cust_token = await _setup_customer(db)
        _, _, prov_token_1 = await _setup_provider(db, phone="+84200000001")
        _, _, prov_token_2 = await _setup_provider(db, phone="+84200000002")
        await _seed_price_config(db)
        booking = await _create_booking(client, cust_token)

        await client.post(
            f"/api/v1/provider/transport/booking/{booking['id']}/accept",
            headers=auth_headers(prov_token_1),
        )
        resp = await client.post(
            f"/api/v1/provider/transport/booking/{booking['id']}/accept",
            headers=auth_headers(prov_token_2),
        )
        assert resp.status_code == 400
        assert "no longer pending" in resp.json()["detail"]

    async def test_accept_nonexistent_booking_returns_404(self, client: AsyncClient, db: AsyncSession):
        """Returns 404 for unknown booking ID."""
        _, _, prov_token = await _setup_provider(db)
        resp = await client.post(
            f"/api/v1/provider/transport/booking/{uuid.uuid4()}/accept",
            headers=auth_headers(prov_token),
        )
        assert resp.status_code == 404

    async def test_accept_without_provider_profile_returns_400(
        self, client: AsyncClient, db: AsyncSession
    ):
        """User with provider role but no Provider profile is rejected."""
        _, cust_token = await _setup_customer(db)
        await _seed_price_config(db)
        booking = await _create_booking(client, cust_token)

        # Provider user with NO profile
        no_prof_user = await create_user(db, phone="+84300000099", role="provider")
        no_prof_token = create_access_token(str(no_prof_user.id), ["provider"])
        await db.commit()

        resp = await client.post(
            f"/api/v1/provider/transport/booking/{booking['id']}/accept",
            headers=auth_headers(no_prof_token),
        )
        assert resp.status_code == 400
        assert "Provider profile not found" in resp.json()["detail"]


# ─────────────────────────────────────────────────────────────────────
# Provider: Trip State Transitions
# ─────────────────────────────────────────────────────────────────────

class TestTripStateTransitions:
    async def _setup_accepted_booking(self, client, db):
        """Helper: returns (bid, otp, prov_token, cust_token) with booking in accepted state."""
        _, cust_token = await _setup_customer(db, phone="+84100000010")
        _, _, prov_token = await _setup_provider(db, phone="+84200000010")
        await _seed_price_config(db)
        booking = await _create_booking(client, cust_token)
        bid = booking["id"]
        otp = booking["boarding_otp"]
        await client.post(f"/api/v1/provider/transport/booking/{bid}/accept", headers=auth_headers(prov_token))
        return bid, otp, prov_token, cust_token

    async def test_arrive_from_accepted_success(self, client: AsyncClient, db: AsyncSession):
        """Provider can arrive after accepting."""
        bid, _, prov_token, _ = await self._setup_accepted_booking(client, db)
        resp = await client.post(
            f"/api/v1/provider/transport/booking/{bid}/arrive",
            headers=auth_headers(prov_token),
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "arrived"
        assert resp.json()["arrived_at"] is not None

    async def test_board_with_correct_otp_success(self, client: AsyncClient, db: AsyncSession):
        """Provider can board passenger with correct OTP."""
        bid, otp, prov_token, _ = await self._setup_accepted_booking(client, db)
        await client.post(f"/api/v1/provider/transport/booking/{bid}/arrive", headers=auth_headers(prov_token))

        resp = await client.post(
            f"/api/v1/provider/transport/booking/{bid}/board?otp={otp}",
            headers=auth_headers(prov_token),
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "boarded"
        assert resp.json()["started_at"] is not None

    async def test_complete_after_board_success(self, client: AsyncClient, db: AsyncSession):
        """Provider can complete after boarding."""
        bid, otp, prov_token, _ = await self._setup_accepted_booking(client, db)
        await client.post(f"/api/v1/provider/transport/booking/{bid}/arrive", headers=auth_headers(prov_token))
        await client.post(f"/api/v1/provider/transport/booking/{bid}/board?otp={otp}", headers=auth_headers(prov_token))

        resp = await client.post(
            f"/api/v1/provider/transport/booking/{bid}/complete",
            headers=auth_headers(prov_token),
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "completed"
        assert resp.json()["completed_at"] is not None

    async def test_cannot_board_before_arriving(self, client: AsyncClient, db: AsyncSession):
        """Returns 400 if trying to board without arriving first."""
        bid, otp, prov_token, _ = await self._setup_accepted_booking(client, db)
        resp = await client.post(
            f"/api/v1/provider/transport/booking/{bid}/board?otp={otp}",
            headers=auth_headers(prov_token),
        )
        assert resp.status_code == 400
        assert "Cannot board" in resp.json()["detail"]

    async def test_cannot_complete_before_boarding(self, client: AsyncClient, db: AsyncSession):
        """Returns 400 if trying to complete without boarding."""
        bid, _, prov_token, _ = await self._setup_accepted_booking(client, db)
        await client.post(f"/api/v1/provider/transport/booking/{bid}/arrive", headers=auth_headers(prov_token))
        resp = await client.post(
            f"/api/v1/provider/transport/booking/{bid}/complete",
            headers=auth_headers(prov_token),
        )
        assert resp.status_code == 400
        assert "Cannot complete" in resp.json()["detail"]

    async def test_wrong_otp_returns_400(self, client: AsyncClient, db: AsyncSession):
        """Returns 400 for incorrect OTP."""
        bid, otp, prov_token, _ = await self._setup_accepted_booking(client, db)
        await client.post(f"/api/v1/provider/transport/booking/{bid}/arrive", headers=auth_headers(prov_token))

        wrong_otp = "0000" if otp != "0000" else "1111"
        resp = await client.post(
            f"/api/v1/provider/transport/booking/{bid}/board?otp={wrong_otp}",
            headers=auth_headers(prov_token),
        )
        assert resp.status_code == 400
        assert "Invalid Boarding OTP" in resp.json()["detail"]

    async def test_other_provider_cannot_update_state(self, client: AsyncClient, db: AsyncSession):
        """A different provider cannot update state of another's booking."""
        bid, _, prov_token_1, _ = await self._setup_accepted_booking(client, db)
        _, _, prov_token_2 = await _setup_provider(db, phone="+84200000099")

        resp = await client.post(
            f"/api/v1/provider/transport/booking/{bid}/arrive",
            headers=auth_headers(prov_token_2),
        )
        assert resp.status_code == 403

    async def test_status_log_written_for_each_transition(self, client: AsyncClient, db: AsyncSession):
        """Each state transition generates a BookingStatusLog entry."""
        from app.models.booking import BookingStatusLog
        from sqlalchemy import select

        bid, otp, prov_token, _ = await self._setup_accepted_booking(client, db)
        await client.post(f"/api/v1/provider/transport/booking/{bid}/arrive", headers=auth_headers(prov_token))
        await client.post(f"/api/v1/provider/transport/booking/{bid}/board?otp={otp}", headers=auth_headers(prov_token))
        await client.post(f"/api/v1/provider/transport/booking/{bid}/complete", headers=auth_headers(prov_token))

        logs = (
            await db.execute(
                select(BookingStatusLog).where(
                    BookingStatusLog.booking_id == uuid.UUID(bid)
                ).order_by(BookingStatusLog.created_at)
            )
        ).scalars().all()

        statuses = [l.to_status for l in logs]
        # pending → accepted → arrived → boarded → completed
        assert "pending" in statuses
        assert "accepted" in statuses
        assert "arrived" in statuses
        assert "boarded" in statuses
        assert "completed" in statuses


# ─────────────────────────────────────────────────────────────────────
# Provider: Driver Availability (Online / Offline)
# ─────────────────────────────────────────────────────────────────────

class TestDriverAvailability:
    async def test_go_online_creates_session(self, client: AsyncClient, db: AsyncSession):
        """Calling online creates a driver session with status=online."""
        _, _, prov_token = await _setup_provider(db)

        resp = await client.post(
            "/api/v1/provider/transport/booking/availability/online",
            json={},
            headers=auth_headers(prov_token),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "online"
        assert data["online_at"] is not None
        assert data["offline_at"] is None

    async def test_go_online_with_vehicle_id(self, client: AsyncClient, db: AsyncSession):
        """Going online with a vehicle_id stores it in the session."""
        _, _, prov_token = await _setup_provider(db)
        vehicle_id = str(uuid.uuid4())

        resp = await client.post(
            "/api/v1/provider/transport/booking/availability/online",
            json={"vehicle_id": vehicle_id},
            headers=auth_headers(prov_token),
        )
        assert resp.status_code == 200
        assert resp.json()["vehicle_id"] == vehicle_id

    async def test_go_online_twice_is_idempotent(self, client: AsyncClient, db: AsyncSession):
        """Calling online twice updates the session rather than creating a duplicate."""
        _, _, prov_token = await _setup_provider(db)

        await client.post(
            "/api/v1/provider/transport/booking/availability/online",
            json={},
            headers=auth_headers(prov_token),
        )
        resp2 = await client.post(
            "/api/v1/provider/transport/booking/availability/online",
            json={},
            headers=auth_headers(prov_token),
        )
        assert resp2.status_code == 200
        assert resp2.json()["status"] == "online"

    async def test_go_offline_success(self, client: AsyncClient, db: AsyncSession):
        """Provider can go offline after being online."""
        _, _, prov_token = await _setup_provider(db)

        await client.post(
            "/api/v1/provider/transport/booking/availability/online",
            json={},
            headers=auth_headers(prov_token),
        )
        resp = await client.post(
            "/api/v1/provider/transport/booking/availability/offline",
            headers=auth_headers(prov_token),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "offline"
        assert data["offline_at"] is not None

    async def test_go_offline_without_session_returns_400(self, client: AsyncClient, db: AsyncSession):
        """Returns 400 when going offline without an active session."""
        _, _, prov_token = await _setup_provider(db)
        resp = await client.post(
            "/api/v1/provider/transport/booking/availability/offline",
            headers=auth_headers(prov_token),
        )
        assert resp.status_code == 400
        assert "No active session" in resp.json()["detail"]

    async def test_availability_without_provider_profile_returns_400(
        self, client: AsyncClient, db: AsyncSession
    ):
        """User with provider role but no Provider profile is rejected."""
        no_prof_user = await create_user(db, phone="+84300000098", role="provider")
        no_prof_token = create_access_token(str(no_prof_user.id), ["provider"])
        await db.commit()

        resp = await client.post(
            "/api/v1/provider/transport/booking/availability/online",
            json={},
            headers=auth_headers(no_prof_token),
        )
        assert resp.status_code == 400


# ─────────────────────────────────────────────────────────────────────
# Provider: Location Ping
# ─────────────────────────────────────────────────────────────────────

class TestDriverLocation:
    async def test_ping_location_creates_record(self, client: AsyncClient, db: AsyncSession):
        """First ping creates a location record."""
        _, _, prov_token = await _setup_provider(db)

        resp = await client.post(
            "/api/v1/provider/transport/booking/location",
            json={"latitude": 10.762622, "longitude": 106.660172},
            headers=auth_headers(prov_token),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert float(data["latitude"]) == pytest.approx(10.762622, abs=1e-4)
        assert float(data["longitude"]) == pytest.approx(106.660172, abs=1e-4)
        assert data["updated_at"] is not None

    async def test_ping_location_updates_existing(self, client: AsyncClient, db: AsyncSession):
        """Subsequent pings update the same record (upsert)."""
        _, _, prov_token = await _setup_provider(db)
        headers = auth_headers(prov_token)

        await client.post(
            "/api/v1/provider/transport/booking/location",
            json={"latitude": 10.0, "longitude": 106.0},
            headers=headers,
        )
        resp2 = await client.post(
            "/api/v1/provider/transport/booking/location",
            json={"latitude": 10.5, "longitude": 106.5, "heading": 180.0, "speed_kmh": 30.0},
            headers=headers,
        )
        assert resp2.status_code == 200
        data = resp2.json()
        assert float(data["latitude"]) == pytest.approx(10.5, abs=1e-4)
        assert float(data["heading"]) == pytest.approx(180.0, abs=0.1)
        assert float(data["speed_kmh"]) == pytest.approx(30.0, abs=0.1)

    async def test_ping_location_missing_coords_returns_422(
        self, client: AsyncClient, db: AsyncSession
    ):
        """Returns 422 when latitude/longitude are missing."""
        _, _, prov_token = await _setup_provider(db)
        resp = await client.post(
            "/api/v1/provider/transport/booking/location",
            json={"heading": 90.0},
            headers=auth_headers(prov_token),
        )
        assert resp.status_code == 422

    async def test_ping_location_without_provider_profile_returns_400(
        self, client: AsyncClient, db: AsyncSession
    ):
        """User with provider role but no Provider profile is rejected."""
        no_prof_user = await create_user(db, phone="+84300000097", role="provider")
        no_prof_token = create_access_token(str(no_prof_user.id), ["provider"])
        await db.commit()

        resp = await client.post(
            "/api/v1/provider/transport/booking/location",
            json={"latitude": 10.0, "longitude": 106.0},
            headers=auth_headers(no_prof_token),
        )
        assert resp.status_code == 400


# ─────────────────────────────────────────────────────────────────────
# End-to-End: Full Happy Path
# ─────────────────────────────────────────────────────────────────────

class TestFullBookingLifecycle:
    async def test_complete_happy_path(self, client: AsyncClient, db: AsyncSession):
        """Full lifecycle: estimate → create → accept → arrive → board → complete."""
        _, cust_token = await _setup_customer(db, phone="+84100000020")
        _, _, prov_token = await _setup_provider(db, phone="+84200000020")
        await _seed_price_config(db)
        cust_h = auth_headers(cust_token)
        prov_h = auth_headers(prov_token)

        # 1. Estimate
        est = await client.post(
            "/api/v1/customer/transport/estimate",
            json={"service_type": "xe_may", "distance_km": 5, "duration_min": 15},
        )
        assert est.status_code == 200
        assert est.json()["estimated_fare"] > 0

        # 2. Create booking
        booking = await _create_booking(client, cust_token)
        bid = booking["id"]
        otp = booking["boarding_otp"]
        assert booking["status"] == "pending"

        # 3. Provider browses & accepts
        avail = await client.get("/api/v1/provider/transport/booking/available", headers=prov_h)
        assert any(b["id"] == bid for b in avail.json()["items"])

        acc = await client.post(f"/api/v1/provider/transport/booking/{bid}/accept", headers=prov_h)
        assert acc.json()["status"] == "accepted"

        # 4. Arrive
        arr = await client.post(f"/api/v1/provider/transport/booking/{bid}/arrive", headers=prov_h)
        assert arr.json()["status"] == "arrived"

        # 5. Board with OTP
        brd = await client.post(f"/api/v1/provider/transport/booking/{bid}/board?otp={otp}", headers=prov_h)
        assert brd.json()["status"] == "boarded"

        # 6. Complete
        cmp = await client.post(f"/api/v1/provider/transport/booking/{bid}/complete", headers=prov_h)
        assert cmp.json()["status"] == "completed"

        # 7. Customer sees completed status
        status_resp = await client.get(f"/api/v1/customer/transport/booking/{bid}", headers=cust_h)
        assert status_resp.json()["status"] == "completed"


# ─────────────────────────────────────────────────────────────────────
# Security: OTP must NOT appear in available list
# ─────────────────────────────────────────────────────────────────────

class TestOTPNotExposedInAvailableList:
    async def test_otp_not_in_available_list_items(self, client: AsyncClient, db: AsyncSession):
        """boarding_otp must NOT be present in the provider available-bookings list."""
        _, cust_token = await _setup_customer(db)
        _, _, prov_token = await _setup_provider(db)
        await _seed_price_config(db)
        booking = await _create_booking(client, cust_token)
        assert booking["boarding_otp"] is not None  # Sanity: OTP exists in customer response

        resp = await client.get(
            "/api/v1/provider/transport/booking/available",
            headers=auth_headers(prov_token),
        )
        assert resp.status_code == 200
        items = resp.json()["items"]
        assert len(items) >= 1
        for item in items:
            assert "boarding_otp" not in item, "OTP must not be exposed in provider list"

    async def test_pickup_address_required(self, client: AsyncClient, db: AsyncSession):
        """Returns 422 when pickup_address is missing from booking payload."""
        _, cust_token = await _setup_customer(db)
        await _seed_price_config(db)
        payload_no_address = {
            "service_type": "xe_may",
            "pickup_lat": 10.762622,
            "pickup_lng": 106.660172,
        }
        resp = await client.post(
            "/api/v1/customer/transport/booking",
            json=payload_no_address,
            headers=auth_headers(cust_token),
        )
        assert resp.status_code == 422


# ─────────────────────────────────────────────────────────────────────
# Admin: Booking Management
# ─────────────────────────────────────────────────────────────────────

async def _setup_admin(db, phone: str = "+84900000099") -> tuple:
    from app.core.security import create_access_token
    user = await create_user(db, phone=phone, role="admin")
    token = create_access_token(str(user.id), ["admin"])
    return user, token


class TestAdminBookingManagement:
    async def test_admin_list_bookings(self, client: AsyncClient, db: AsyncSession):
        """Admin can list all bookings."""
        _, cust_token = await _setup_customer(db)
        _, admin_token = await _setup_admin(db)
        await _seed_price_config(db)
        await _create_booking(client, cust_token)

        resp = await client.get(
            "/api/v1/admin/bookings",
            headers=auth_headers(admin_token),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        assert "total" in data
        assert data["total"] >= 1

    async def test_admin_list_filter_by_status(self, client: AsyncClient, db: AsyncSession):
        """Admin list filtered by status returns correct results."""
        _, cust_token = await _setup_customer(db)
        _, admin_token = await _setup_admin(db)
        await _seed_price_config(db)
        await _create_booking(client, cust_token)

        resp = await client.get(
            "/api/v1/admin/bookings?status=pending",
            headers=auth_headers(admin_token),
        )
        assert resp.status_code == 200
        items = resp.json()["items"]
        assert all(b["status"] == "pending" for b in items)

    async def test_admin_get_booking_detail(self, client: AsyncClient, db: AsyncSession):
        """Admin can retrieve booking detail with status logs."""
        _, cust_token = await _setup_customer(db)
        _, admin_token = await _setup_admin(db)
        await _seed_price_config(db)
        booking = await _create_booking(client, cust_token)

        resp = await client.get(
            f"/api/v1/admin/bookings/{booking['id']}",
            headers=auth_headers(admin_token),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "booking" in data
        assert "status_logs" in data
        assert data["booking"]["id"] == booking["id"]
        assert len(data["status_logs"]) >= 1

    async def test_admin_get_booking_not_found(self, client: AsyncClient, db: AsyncSession):
        """Returns 404 for unknown booking."""
        _, admin_token = await _setup_admin(db)
        resp = await client.get(
            f"/api/v1/admin/bookings/{uuid.uuid4()}",
            headers=auth_headers(admin_token),
        )
        assert resp.status_code == 404

    async def test_admin_force_cancel_pending_booking(self, client: AsyncClient, db: AsyncSession):
        """Admin can force-cancel a pending booking."""
        _, cust_token = await _setup_customer(db)
        _, admin_token = await _setup_admin(db)
        await _seed_price_config(db)
        booking = await _create_booking(client, cust_token)

        resp = await client.patch(
            f"/api/v1/admin/bookings/{booking['id']}/cancel",
            headers=auth_headers(admin_token),
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "cancelled"

    async def test_admin_cannot_cancel_completed_booking(self, client: AsyncClient, db: AsyncSession):
        """Admin cannot cancel a completed booking."""
        _, cust_token = await _setup_customer(db)
        _, _, prov_token = await _setup_provider(db)
        _, admin_token = await _setup_admin(db)
        await _seed_price_config(db)
        booking = await _create_booking(client, cust_token)
        bid = booking["id"]
        otp = booking["boarding_otp"]

        await client.post(f"/api/v1/provider/transport/booking/{bid}/accept", headers=auth_headers(prov_token))
        await client.post(f"/api/v1/provider/transport/booking/{bid}/arrive", headers=auth_headers(prov_token))
        await client.post(f"/api/v1/provider/transport/booking/{bid}/board?otp={otp}", headers=auth_headers(prov_token))
        await client.post(f"/api/v1/provider/transport/booking/{bid}/complete", headers=auth_headers(prov_token))

        resp = await client.patch(
            f"/api/v1/admin/bookings/{bid}/cancel",
            headers=auth_headers(admin_token),
        )
        assert resp.status_code == 400

    async def test_non_admin_cannot_access_booking_management(self, client: AsyncClient, db: AsyncSession):
        """Customer cannot access admin booking endpoints."""
        _, cust_token = await _setup_customer(db)
        resp = await client.get(
            "/api/v1/admin/bookings",
            headers=auth_headers(cust_token),
        )
        assert resp.status_code == 403
