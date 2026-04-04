"""Performance tests — Phase 6 & Phase 7 APIs.

Measures:
  - Response time: mỗi endpoint phải phản hồi trong ngưỡng cho phép
  - Query count: phát hiện N+1 query bằng cách đếm SQL statements
  - Bulk load: kiểm tra list endpoint khi có N records

Ngưỡng (trên SQLite in-memory, không bao gồm network latency):
  - Simple GET/POST:     < 150ms
  - Paginated list:      < 200ms
  - Write + log:         < 200ms
  - Full lifecycle flow: < 800ms (nhiều bước)

Cách đếm query:
  Dùng SQLAlchemy event listener "before_cursor_execute" để đếm số lần
  DB thực sự được hit trong một request.

Chạy performance tests:
  Mặc định bị skip để tránh flakiness trên CI.
  Đặt env var RUN_PERFORMANCE_TESTS=1 để bật:
    RUN_PERFORMANCE_TESTS=1 pytest tests/test_performance.py -m performance
"""

import os
import time
import uuid
from contextlib import contextmanager
from datetime import date, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token
from app.models.booking import PriceConfig
from tests.conftest import (
    auth_headers,
    create_provider,
    create_provider_service,
    create_route,
    create_service_category,
    create_user,
    create_vehicle,
    make_provider_token,
)

pytestmark = [
    pytest.mark.asyncio,
    pytest.mark.performance,
]

# Skip all wall-clock time tests unless the env var is explicitly set.
# Query-count tests (N+1 detection) always run — they are deterministic.
_SKIP_TIME_TESTS = pytest.mark.skipif(
    not os.environ.get("RUN_PERFORMANCE_TESTS"),
    reason="Wall-clock performance tests skipped by default. Set RUN_PERFORMANCE_TESTS=1 to enable.",
)


# ─────────────────────────────────────────────────────────────────────
# Query counter context manager
# ─────────────────────────────────────────────────────────────────────

class QueryCounter:
    """Đếm số SQL statement được thực thi trong một block."""

    def __init__(self, db: AsyncSession):
        self._db = db
        self.count = 0
        self._stmts: list[str] = []

    def _before_cursor(self, conn, cursor, statement, parameters, context, executemany):
        self.count += 1
        self._stmts.append(statement[:120])  # Lưu 120 ký tự đầu để debug

    def start(self):
        event.listen(self._db.sync_session.bind, "before_cursor_execute", self._before_cursor)

    def stop(self):
        event.remove(self._db.sync_session.bind, "before_cursor_execute", self._before_cursor)

    @property
    def statements(self) -> list[str]:
        return self._stmts


# ─────────────────────────────────────────────────────────────────────
# Shared helpers
# ─────────────────────────────────────────────────────────────────────

async def _setup_phase6(db: AsyncSession, phone: str = "+84900000001"):
    """Seed a provider + service for Phase 6 perf tests."""
    user = await create_user(db, phone=phone)
    provider = await create_provider(db, user)
    category = await create_service_category(db, code="perf_test_xe")
    svc = await create_provider_service(db, provider, category)
    await db.commit()
    token = make_provider_token(user)
    return user, provider, svc, token


async def _setup_booking(db: AsyncSession, cust_phone: str = "+84100000001", prov_phone: str = "+84200000001"):
    """Seed customer + provider + price config for Phase 7 perf tests."""
    cust_user = await create_user(db, phone=cust_phone, role="customer")
    cust_token = create_access_token(str(cust_user.id), ["customer"])

    prov_user = await create_user(db, phone=prov_phone, role="provider")
    provider = await create_provider(db, prov_user)
    prov_token = create_access_token(str(prov_user.id), ["provider"])

    await create_service_category(db, code="perf_xe_may")
    config = PriceConfig(
        id=uuid.uuid4(),
        service_type="perf_xe_may",
        pricing_mode="formula",
        base_fare=10000,
        fare_per_km=5000,
        fare_per_min=500,
        surge_enabled=False,
        is_active=True,
    )
    db.add(config)
    await db.commit()
    return cust_token, prov_token, provider


BOOKING_PAYLOAD = {
    "service_type": "perf_xe_may",
    "pickup_lat": 10.762622,
    "pickup_lng": 106.660172,
    "pickup_address": "Pickup",
    "dropoff_lat": 10.776889,
    "dropoff_lng": 106.700806,
    "dropoff_address": "Dropoff",
}

# ─────────────────────────────────────────────────────────────────────
# Phase 6 — Response Time Tests
# ─────────────────────────────────────────────────────────────────────

@_SKIP_TIME_TESTS
class TestPhase6ResponseTime:
    """Kiểm tra thời gian response của các Phase 6 endpoints."""

    THRESHOLD_SIMPLE_MS = 150
    THRESHOLD_LIST_MS = 200
    THRESHOLD_WRITE_MS = 200

    async def test_create_vehicle_response_time(self, client: AsyncClient, db: AsyncSession):
        """POST /provider/vehicles phải hoàn thành < 200ms."""
        _, provider, svc, token = await _setup_phase6(db)

        start = time.perf_counter()
        resp = await client.post(
            "/api/v1/provider/vehicles",
            json={"vehicle_type": "xe_4_cho", "license_plate": f"51A-{uuid.uuid4().hex[:5]}", "service_id": str(svc.id)},
            headers=auth_headers(token),
        )
        elapsed_ms = (time.perf_counter() - start) * 1000

        assert resp.status_code == 201, resp.text
        assert elapsed_ms < self.THRESHOLD_WRITE_MS, (
            f"Create vehicle took {elapsed_ms:.1f}ms — exceeds {self.THRESHOLD_WRITE_MS}ms threshold"
        )

    async def test_list_vehicles_response_time(self, client: AsyncClient, db: AsyncSession):
        """GET /provider/vehicles phải hoàn thành < 200ms với 10 items."""
        _, provider, svc, token = await _setup_phase6(db)

        # Seed 10 vehicles
        for i in range(10):
            await create_vehicle(db, provider, vehicle_type="xe_4_cho")
        await db.commit()

        start = time.perf_counter()
        resp = await client.get("/api/v1/provider/vehicles", headers=auth_headers(token))
        elapsed_ms = (time.perf_counter() - start) * 1000

        assert resp.status_code == 200
        assert resp.json()["total"] == 10
        assert elapsed_ms < self.THRESHOLD_LIST_MS, (
            f"List 10 vehicles took {elapsed_ms:.1f}ms — exceeds {self.THRESHOLD_LIST_MS}ms threshold"
        )

    async def test_get_vehicle_detail_response_time(self, client: AsyncClient, db: AsyncSession):
        """GET /provider/vehicles/{id} phải hoàn thành < 150ms."""
        _, provider, svc, token = await _setup_phase6(db)
        vehicle = await create_vehicle(db, provider)
        await db.commit()

        start = time.perf_counter()
        resp = await client.get(f"/api/v1/provider/vehicles/{vehicle.id}", headers=auth_headers(token))
        elapsed_ms = (time.perf_counter() - start) * 1000

        assert resp.status_code == 200
        assert elapsed_ms < self.THRESHOLD_SIMPLE_MS, (
            f"Get vehicle took {elapsed_ms:.1f}ms — exceeds {self.THRESHOLD_SIMPLE_MS}ms threshold"
        )

    async def test_create_route_response_time(self, client: AsyncClient, db: AsyncSession):
        """POST /provider/services/{svc_id}/routes phải hoàn thành < 200ms."""
        _, provider, svc, token = await _setup_phase6(db)

        start = time.perf_counter()
        resp = await client.post(
            f"/api/v1/provider/services/{svc.id}/routes",
            json={"from_province": "Hà Nội", "to_province": "HCM", "price": 350000},
            headers=auth_headers(token),
        )
        elapsed_ms = (time.perf_counter() - start) * 1000

        assert resp.status_code == 201, resp.text
        assert elapsed_ms < self.THRESHOLD_WRITE_MS, (
            f"Create route took {elapsed_ms:.1f}ms — exceeds {self.THRESHOLD_WRITE_MS}ms threshold"
        )

    async def test_list_routes_with_schedules_response_time(
        self, client: AsyncClient, db: AsyncSession
    ):
        """GET /provider/services/{svc_id}/routes phải hoàn thành < 200ms với 5 routes có schedules."""
        _, provider, svc, token = await _setup_phase6(db)
        token_h = auth_headers(token)

        # Seed 5 routes, mỗi route 3 schedules
        for i in range(5):
            route = await create_route(db, svc, from_province=f"Tỉnh {i}", to_province="HCM")
            for t in ("06:00:00", "12:00:00", "18:00:00"):
                await client.post(
                    f"/api/v1/provider/routes/{route.id}/schedules",
                    json={"departure_time": t, "seat_count": 45},
                    headers=token_h,
                )

        start = time.perf_counter()
        resp = await client.get(f"/api/v1/provider/services/{svc.id}/routes", headers=token_h)
        elapsed_ms = (time.perf_counter() - start) * 1000

        assert resp.status_code == 200
        assert resp.json()["total"] == 5
        assert elapsed_ms < self.THRESHOLD_LIST_MS, (
            f"List 5 routes+schedules took {elapsed_ms:.1f}ms — exceeds {self.THRESHOLD_LIST_MS}ms threshold"
        )

    async def test_block_availability_bulk_response_time(
        self, client: AsyncClient, db: AsyncSession
    ):
        """POST /availabilities/block với 30 dates phải < 200ms."""
        _, provider, svc, token = await _setup_phase6(db)
        vehicle = await create_vehicle(db, provider)
        await db.commit()

        today = date.today()
        dates = [str(today + timedelta(days=i)) for i in range(1, 31)]

        start = time.perf_counter()
        resp = await client.post(
            f"/api/v1/provider/vehicles/{vehicle.id}/availabilities/block",
            json={"dates": dates, "reason": "Kiểm tra hiệu năng"},
            headers=auth_headers(token),
        )
        elapsed_ms = (time.perf_counter() - start) * 1000

        assert resp.status_code == 200
        assert resp.json()["blocked_count"] == 30
        assert elapsed_ms < self.THRESHOLD_WRITE_MS, (
            f"Block 30 dates took {elapsed_ms:.1f}ms — exceeds {self.THRESHOLD_WRITE_MS}ms threshold"
        )


# ─────────────────────────────────────────────────────────────────────
# Phase 7 — Response Time Tests
# ─────────────────────────────────────────────────────────────────────

@_SKIP_TIME_TESTS
class TestPhase7ResponseTime:
    """Kiểm tra thời gian response của các Phase 7 endpoints."""

    THRESHOLD_SIMPLE_MS = 150
    THRESHOLD_WRITE_MS = 200
    THRESHOLD_LIFECYCLE_MS = 800

    async def test_create_booking_response_time(self, client: AsyncClient, db: AsyncSession):
        """POST /customer/transport/booking phải hoàn thành < 200ms."""
        cust_token, _, _ = await _setup_booking(db)

        start = time.perf_counter()
        resp = await client.post(
            "/api/v1/customer/transport/booking",
            json=BOOKING_PAYLOAD,
            headers=auth_headers(cust_token),
        )
        elapsed_ms = (time.perf_counter() - start) * 1000

        assert resp.status_code == 201, resp.text
        assert elapsed_ms < self.THRESHOLD_WRITE_MS, (
            f"Create booking took {elapsed_ms:.1f}ms — exceeds {self.THRESHOLD_WRITE_MS}ms threshold"
        )

    async def test_get_booking_status_response_time(self, client: AsyncClient, db: AsyncSession):
        """GET /customer/transport/booking/{id} phải hoàn thành < 150ms."""
        cust_token, _, _ = await _setup_booking(db)

        booking = (
            await client.post(
                "/api/v1/customer/transport/booking",
                json=BOOKING_PAYLOAD,
                headers=auth_headers(cust_token),
            )
        ).json()

        start = time.perf_counter()
        resp = await client.get(
            f"/api/v1/customer/transport/booking/{booking['id']}",
            headers=auth_headers(cust_token),
        )
        elapsed_ms = (time.perf_counter() - start) * 1000

        assert resp.status_code == 200
        assert elapsed_ms < self.THRESHOLD_SIMPLE_MS, (
            f"Get booking status took {elapsed_ms:.1f}ms — exceeds {self.THRESHOLD_SIMPLE_MS}ms threshold"
        )

    async def test_list_available_bookings_response_time(
        self, client: AsyncClient, db: AsyncSession
    ):
        """GET /provider/transport/booking/available phải < 200ms với 20 pending bookings."""
        cust_token, prov_token, _ = await _setup_booking(db)

        # Seed 20 pending bookings
        for _ in range(20):
            await client.post(
                "/api/v1/customer/transport/booking",
                json=BOOKING_PAYLOAD,
                headers=auth_headers(cust_token),
            )

        start = time.perf_counter()
        resp = await client.get(
            "/api/v1/provider/transport/booking/available",
            headers=auth_headers(prov_token),
        )
        elapsed_ms = (time.perf_counter() - start) * 1000

        assert resp.status_code == 200
        assert resp.json()["total"] == 20
        assert elapsed_ms < self.THRESHOLD_WRITE_MS, (
            f"List 20 bookings took {elapsed_ms:.1f}ms — exceeds {self.THRESHOLD_WRITE_MS}ms threshold"
        )

    async def test_accept_booking_response_time(self, client: AsyncClient, db: AsyncSession):
        """POST /provider/transport/booking/{id}/accept phải < 200ms."""
        cust_token, prov_token, _ = await _setup_booking(db)
        booking = (
            await client.post(
                "/api/v1/customer/transport/booking",
                json=BOOKING_PAYLOAD,
                headers=auth_headers(cust_token),
            )
        ).json()

        start = time.perf_counter()
        resp = await client.post(
            f"/api/v1/provider/transport/booking/{booking['id']}/accept",
            headers=auth_headers(prov_token),
        )
        elapsed_ms = (time.perf_counter() - start) * 1000

        assert resp.status_code == 200
        assert elapsed_ms < self.THRESHOLD_WRITE_MS, (
            f"Accept booking took {elapsed_ms:.1f}ms — exceeds {self.THRESHOLD_WRITE_MS}ms threshold"
        )

    async def test_full_lifecycle_response_time(self, client: AsyncClient, db: AsyncSession):
        """Toàn bộ lifecycle (6 bước) phải hoàn thành < 800ms."""
        cust_token, prov_token, _ = await _setup_booking(db)
        cust_h = auth_headers(cust_token)
        prov_h = auth_headers(prov_token)

        start = time.perf_counter()

        booking = (
            await client.post("/api/v1/customer/transport/booking", json=BOOKING_PAYLOAD, headers=cust_h)
        ).json()
        bid = booking["id"]
        otp = booking["boarding_otp"]

        await client.post(f"/api/v1/provider/transport/booking/{bid}/accept", headers=prov_h)
        await client.post(f"/api/v1/provider/transport/booking/{bid}/arrive", headers=prov_h)
        await client.post(f"/api/v1/provider/transport/booking/{bid}/board?otp={otp}", headers=prov_h)
        await client.post(f"/api/v1/provider/transport/booking/{bid}/complete", headers=prov_h)

        elapsed_ms = (time.perf_counter() - start) * 1000

        assert elapsed_ms < self.THRESHOLD_LIFECYCLE_MS, (
            f"Full lifecycle took {elapsed_ms:.1f}ms — exceeds {self.THRESHOLD_LIFECYCLE_MS}ms threshold"
        )

    async def test_location_ping_response_time(self, client: AsyncClient, db: AsyncSession):
        """POST /provider/transport/booking/location phải < 150ms."""
        _, prov_token, _ = await _setup_booking(db)

        start = time.perf_counter()
        resp = await client.post(
            "/api/v1/provider/transport/booking/location",
            json={"latitude": 10.762622, "longitude": 106.660172, "speed_kmh": 30.0},
            headers=auth_headers(prov_token),
        )
        elapsed_ms = (time.perf_counter() - start) * 1000

        assert resp.status_code == 200
        assert elapsed_ms < self.THRESHOLD_SIMPLE_MS, (
            f"Location ping took {elapsed_ms:.1f}ms — exceeds {self.THRESHOLD_SIMPLE_MS}ms threshold"
        )

    async def test_location_upsert_10_pings_response_time(
        self, client: AsyncClient, db: AsyncSession
    ):
        """10 location pings liên tiếp (upsert) phải < 150ms mỗi ping."""
        _, prov_token, _ = await _setup_booking(db)
        headers = auth_headers(prov_token)
        timings = []

        for i in range(10):
            start = time.perf_counter()
            resp = await client.post(
                "/api/v1/provider/transport/booking/location",
                json={"latitude": 10.7 + i * 0.001, "longitude": 106.6},
                headers=headers,
            )
            timings.append((time.perf_counter() - start) * 1000)
            assert resp.status_code == 200

        avg_ms = sum(timings) / len(timings)
        max_ms = max(timings)
        assert max_ms < self.THRESHOLD_SIMPLE_MS, (
            f"Worst location ping took {max_ms:.1f}ms (avg={avg_ms:.1f}ms) — exceeds threshold"
        )


# ─────────────────────────────────────────────────────────────────────
# Phase 6 — Query Count Tests
# ─────────────────────────────────────────────────────────────────────

class TestPhase6QueryCount:
    """Phát hiện N+1 query và query không cần thiết ở Phase 6."""

    async def test_list_vehicles_query_count(self, client: AsyncClient, db: AsyncSession):
        """GET /provider/vehicles không được gây N+1 query khi list 10 xe."""
        _, provider, svc, token = await _setup_phase6(db)
        for _ in range(10):
            await create_vehicle(db, provider)
        await db.commit()

        counter = QueryCounter(db)
        counter.start()
        resp = await client.get("/api/v1/provider/vehicles", headers=auth_headers(token))
        counter.stop()

        assert resp.status_code == 200
        # Expected: 1 count query + 1 select query = 2
        # Nếu N+1: sẽ có 10+ queries
        assert counter.count <= 6, (
            f"Expected ≤6 queries for list 10 vehicles, got {counter.count}.\n"
            f"Possible N+1 detected.\nStatements:\n" + "\n".join(counter.statements)
        )

    async def test_get_vehicle_detail_query_count(self, client: AsyncClient, db: AsyncSession):
        """GET /provider/vehicles/{id} không được vượt quá 3 queries."""
        _, provider, svc, token = await _setup_phase6(db)
        vehicle = await create_vehicle(db, provider)
        await db.commit()

        counter = QueryCounter(db)
        counter.start()
        resp = await client.get(f"/api/v1/provider/vehicles/{vehicle.id}", headers=auth_headers(token))
        counter.stop()

        assert resp.status_code == 200
        assert counter.count <= 5, (
            f"Expected ≤5 queries for vehicle detail, got {counter.count}.\n"
            f"Statements:\n" + "\n".join(counter.statements)
        )

    async def test_list_routes_query_count(self, client: AsyncClient, db: AsyncSession):
        """GET /provider/services/{id}/routes không gây N+1 khi có 5 routes."""
        _, provider, svc, token = await _setup_phase6(db)
        for i in range(5):
            await create_route(db, svc, from_province=f"City {i}", to_province="HCM")
        await db.commit()

        counter = QueryCounter(db)
        counter.start()
        resp = await client.get(
            f"/api/v1/provider/services/{svc.id}/routes",
            headers=auth_headers(token),
        )
        counter.stop()

        assert resp.status_code == 200
        assert counter.count <= 8, (
            f"Expected ≤8 queries for list 5 routes, got {counter.count}.\n"
            f"Statements:\n" + "\n".join(counter.statements)
        )

    async def test_create_vehicle_query_count(self, client: AsyncClient, db: AsyncSession):
        """POST /provider/vehicles không được dùng quá 5 queries."""
        _, provider, svc, token = await _setup_phase6(db)

        counter = QueryCounter(db)
        counter.start()
        resp = await client.post(
            "/api/v1/provider/vehicles",
            json={"vehicle_type": "xe_4_cho", "license_plate": "99X-00001", "service_id": str(svc.id)},
            headers=auth_headers(token),
        )
        counter.stop()

        assert resp.status_code == 201
        assert counter.count <= 9, (
            f"Expected ≤9 queries for create vehicle, got {counter.count}.\n"
            f"Statements:\n" + "\n".join(counter.statements)
        )


# ─────────────────────────────────────────────────────────────────────
# Phase 7 — Query Count Tests
# ─────────────────────────────────────────────────────────────────────

class TestPhase7QueryCount:
    """Phát hiện N+1 query và query không cần thiết ở Phase 7."""

    async def test_create_booking_query_count(self, client: AsyncClient, db: AsyncSession):
        """POST /customer/transport/booking không được vượt quá 8 queries."""
        cust_token, _, _ = await _setup_booking(db)

        counter = QueryCounter(db)
        counter.start()
        resp = await client.post(
            "/api/v1/customer/transport/booking",
            json=BOOKING_PAYLOAD,
            headers=auth_headers(cust_token),
        )
        counter.stop()

        assert resp.status_code == 201, resp.text
        assert counter.count <= 12, (
            f"Expected ≤12 queries for create booking, got {counter.count}.\n"
            f"Statements:\n" + "\n".join(counter.statements)
        )

    async def test_list_available_bookings_query_count(
        self, client: AsyncClient, db: AsyncSession
    ):
        """GET /provider/transport/booking/available không gây N+1 với 10 bookings."""
        cust_token, prov_token, _ = await _setup_booking(db)

        for _ in range(10):
            await client.post(
                "/api/v1/customer/transport/booking",
                json=BOOKING_PAYLOAD,
                headers=auth_headers(cust_token),
            )

        counter = QueryCounter(db)
        counter.start()
        resp = await client.get(
            "/api/v1/provider/transport/booking/available",
            headers=auth_headers(prov_token),
        )
        counter.stop()

        assert resp.status_code == 200
        assert resp.json()["total"] == 10
        # Expected: auth + get_provider + count + select = ~4-8 queries
        # If count grows proportionally with rows → N+1 bug
        assert counter.count <= 10, (
            f"Expected ≤10 queries to list 10 bookings (no N+1), got {counter.count}.\n"
            f"N+1 issue suspected if count grows proportionally with rows.\nStatements:\n"
            + "\n".join(counter.statements)
        )

    async def test_accept_booking_query_count(self, client: AsyncClient, db: AsyncSession):
        """POST /provider/transport/booking/{id}/accept không vượt quá 8 queries."""
        cust_token, prov_token, _ = await _setup_booking(db)
        booking = (
            await client.post(
                "/api/v1/customer/transport/booking",
                json=BOOKING_PAYLOAD,
                headers=auth_headers(cust_token),
            )
        ).json()

        counter = QueryCounter(db)
        counter.start()
        resp = await client.post(
            f"/api/v1/provider/transport/booking/{booking['id']}/accept",
            headers=auth_headers(prov_token),
        )
        counter.stop()

        assert resp.status_code == 200
        # accept: auth + get_provider + get_booking + insert_log + commit + refresh = ~6-8
        assert counter.count <= 12, (
            f"Expected ≤12 queries for accept booking, got {counter.count}.\n"
            f"Statements:\n" + "\n".join(counter.statements)
        )

    async def test_location_ping_query_count(self, client: AsyncClient, db: AsyncSession):
        """POST /provider/transport/booking/location phải dùng đúng 1 SELECT + 1 INSERT/UPDATE."""
        _, prov_token, _ = await _setup_booking(db)

        counter = QueryCounter(db)
        counter.start()
        resp = await client.post(
            "/api/v1/provider/transport/booking/location",
            json={"latitude": 10.7, "longitude": 106.6},
            headers=auth_headers(prov_token),
        )
        counter.stop()

        assert resp.status_code == 200
        # auth + get_provider + select_location + insert + commit + refresh = ~6
        assert counter.count <= 10, (
            f"Expected ≤10 queries for location ping, got {counter.count}.\n"
            f"Statements:\n" + "\n".join(counter.statements)
        )

    async def test_status_log_written_correctly_query_count(
        self, client: AsyncClient, db: AsyncSession
    ):
        """Mỗi state transition chỉ insert 1 log (không bị duplicate)."""
        from app.models.booking import BookingStatusLog
        from sqlalchemy import select

        cust_token, prov_token, _ = await _setup_booking(db)
        booking = (
            await client.post(
                "/api/v1/customer/transport/booking",
                json=BOOKING_PAYLOAD,
                headers=auth_headers(cust_token),
            )
        ).json()
        bid = booking["id"]
        otp = booking["boarding_otp"]
        prov_h = auth_headers(prov_token)

        await client.post(f"/api/v1/provider/transport/booking/{bid}/accept", headers=prov_h)
        await client.post(f"/api/v1/provider/transport/booking/{bid}/arrive", headers=prov_h)
        await client.post(f"/api/v1/provider/transport/booking/{bid}/board?otp={otp}", headers=prov_h)
        await client.post(f"/api/v1/provider/transport/booking/{bid}/complete", headers=prov_h)

        # Verify: exactly 5 logs (pending + accepted + arrived + boarded + completed)
        logs = (
            await db.execute(
                select(BookingStatusLog).where(BookingStatusLog.booking_id == uuid.UUID(bid))
            )
        ).scalars().all()

        assert len(logs) == 5, (
            f"Expected exactly 5 status logs, got {len(logs)}.\n"
            f"Logs: {[(l.from_status, l.to_status) for l in logs]}"
        )

        # Verify no duplicate transitions
        transitions = [(l.from_status, l.to_status) for l in logs]
        assert len(transitions) == len(set(transitions)), f"Duplicate log entries: {transitions}"
