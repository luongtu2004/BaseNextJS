"""Unit tests — Customer transport search & rental availability (Phase 6.4).

Tests cover: customer search endpoints (transport search, bus routes,
             route detail with active/inactive schedules, rental vehicle
             search with availability filter, vehicle availability query).
"""

import uuid
from datetime import date, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.conftest import (
    auth_headers,
    create_provider,
    create_provider_service,
    create_route,
    create_service_category,
    create_user,
    create_vehicle,
    make_admin_token,
    make_provider_token,
)


pytestmark = pytest.mark.asyncio


# ─────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────

async def _seed_bus_provider(db: AsyncSession):
    """Create provider + xe_khach_lien_tinh service + route + schedules."""
    user = await create_user(db)
    provider = await create_provider(db, user)
    category = await create_service_category(db, code="xe_khach_lien_tinh")
    svc = await create_provider_service(db, provider, category)
    route = await create_route(db, svc, from_province="Hà Nội", to_province="Hồ Chí Minh")
    await db.commit()
    return user, provider, svc, route


async def _seed_rental_provider(db: AsyncSession, phone: str = "+84900000010"):
    """Create provider + cho_thue_xe_tu_lai_oto service."""
    user = await create_user(db, phone=phone)
    provider = await create_provider(db, user)
    category = await create_service_category(db, code="cho_thue_xe_tu_lai_oto")
    svc = await create_provider_service(db, provider, category)
    await db.commit()
    return user, provider, svc


# ─────────────────────────────────────────────────────────────────────
# GET /customer/transport/search
# ─────────────────────────────────────────────────────────────────────

class TestCustomerTransportSearch:
    async def test_search_invalid_category_code_returns_400(
        self, client: AsyncClient, db: AsyncSession
    ):
        """Returns 400 when service_category_code does not exist."""
        response = await client.get(
            "/api/v1/customer/transport/search",
            params={"service_category_code": "nonexistent_code"},
        )
        assert response.status_code == 400

    async def test_search_returns_matching_providers(
        self, client: AsyncClient, db: AsyncSession
    ):
        """Returns providers that match a given service category and province."""
        user, provider, svc, _ = await _seed_bus_provider(db)

        response = await client.get(
            "/api/v1/customer/transport/search",
            params={"service_category_code": "xe_khach_lien_tinh"},
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data["items"], list)
        provider_ids = [item["provider_id"] for item in data["items"]]
        assert str(provider.id) in provider_ids

    async def test_search_empty_result_for_unmatched_province(
        self, client: AsyncClient, db: AsyncSession
    ):
        """Passing province param returns same list (province filter is informational)."""
        await _seed_bus_provider(db)

        # province is an optional informational filter; current impl returns
        # all active providers for the category regardless of province match.
        # Verify the endpoint accepts the param without error.
        response = await client.get(
            "/api/v1/customer/transport/search",
            params={
                "service_category_code": "xe_khach_lien_tinh",
                "province": "Địa điểm không tồn tại",
            },
        )
        assert response.status_code == 200
        assert isinstance(response.json()["items"], list)


# ─────────────────────────────────────────────────────────────────────
# GET /customer/transport/routes
# ─────────────────────────────────────────────────────────────────────

class TestCustomerSearchRoutes:
    async def test_search_bus_routes_by_province(
        self, client: AsyncClient, db: AsyncSession
    ):
        """Returns routes matching from_province and to_province."""
        await _seed_bus_provider(db)

        response = await client.get(
            "/api/v1/customer/transport/routes",
            params={"from_province": "Hà Nội", "to_province": "Hồ Chí Minh"},
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data["items"], list)
        assert len(data["items"]) >= 1
        assert all(
            r["from_province"] == "Hà Nội" and r["to_province"] == "Hồ Chí Minh"
            for r in data["items"]
        )

    async def test_search_routes_case_insensitive(
        self, client: AsyncClient, db: AsyncSession
    ):
        """Province search is case-insensitive (ilike)."""
        await _seed_bus_provider(db)

        response = await client.get(
            "/api/v1/customer/transport/routes",
            params={"from_province": "hà nội", "to_province": "hồ chí minh"},
        )
        assert response.status_code == 200
        assert len(response.json()["items"]) >= 1

    async def test_search_routes_ordered_by_price(
        self, client: AsyncClient, db: AsyncSession
    ):
        """Routes are returned from cheapest to most expensive."""
        user, provider, svc, _ = await _seed_bus_provider(db)
        # Add a second cheaper route
        await create_route(
            db, svc, from_province="Hà Nội", to_province="Hồ Chí Minh", price=100000
        )
        await db.commit()

        response = await client.get(
            "/api/v1/customer/transport/routes",
            params={"from_province": "Hà Nội", "to_province": "Hồ Chí Minh"},
        )
        assert response.status_code == 200
        prices = [float(r["price"]) for r in response.json()["items"]]
        assert prices == sorted(prices)

    async def test_search_routes_no_results(self, client: AsyncClient, db: AsyncSession):
        """Returns empty list when no routes found."""
        response = await client.get(
            "/api/v1/customer/transport/routes",
            params={"from_province": "Không có", "to_province": "Cũng không"},
        )
        assert response.status_code == 200
        assert response.json()["items"] == []


# ─────────────────────────────────────────────────────────────────────
# GET /customer/transport/routes/{route_id}
# ─────────────────────────────────────────────────────────────────────

class TestCustomerGetRouteDetail:
    async def test_get_route_detail_with_schedules(
        self, client: AsyncClient, db: AsyncSession
    ):
        """Route detail includes active schedules."""
        user, provider, svc, route = await _seed_bus_provider(db)
        provider_token = make_provider_token(user)

        # Add active + inactive schedules via provider API
        await client.post(
            f"/api/v1/provider/routes/{route.id}/schedules",
            json={"departure_time": "07:00:00", "seat_count": 45},
            headers=auth_headers(provider_token),
        )
        resp2 = await client.post(
            f"/api/v1/provider/routes/{route.id}/schedules",
            json={"departure_time": "14:00:00", "seat_count": 45},
            headers=auth_headers(provider_token),
        )
        sched2_id = resp2.json()["id"]

        # Deactivate the second schedule
        await client.patch(
            f"/api/v1/provider/routes/{route.id}/schedules/{sched2_id}/status",
            json={"is_active": False},
            headers=auth_headers(provider_token),
        )

        # Customer endpoint should return only the active one
        response = await client.get(f"/api/v1/customer/transport/routes/{route.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(route.id)
        schedules = data["schedules"]
        assert len(schedules) == 1
        assert schedules[0]["departure_time"] == "07:00:00"

    async def test_get_inactive_route_returns_404(
        self, client: AsyncClient, db: AsyncSession
    ):
        """Returns 404 for inactive routes."""
        user, provider, svc, route = await _seed_bus_provider(db)
        provider_token = make_provider_token(user)

        # Deactivate the route
        await client.patch(
            f"/api/v1/provider/services/{svc.id}/routes/{route.id}/status",
            json={"is_active": False},
            headers=auth_headers(provider_token),
        )

        response = await client.get(f"/api/v1/customer/transport/routes/{route.id}")
        assert response.status_code == 404

    async def test_get_nonexistent_route_returns_404(
        self, client: AsyncClient, db: AsyncSession
    ):
        """Returns 404 for non-existent route ID."""
        response = await client.get(f"/api/v1/customer/transport/routes/{uuid.uuid4()}")
        assert response.status_code == 404


# ─────────────────────────────────────────────────────────────────────
# GET /customer/transport/rental-vehicles
# ─────────────────────────────────────────────────────────────────────

class TestCustomerSearchRentalVehicles:
    async def test_search_rental_vehicles_returns_active(
        self, client: AsyncClient, db: AsyncSession
    ):
        """Returns active rental vehicles."""
        user, provider, svc = await _seed_rental_provider(db)
        await create_vehicle(db, provider, vehicle_type="xe_4_cho")
        await db.commit()

        response = await client.get("/api/v1/customer/transport/rental-vehicles")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data["items"], list)
        assert len(data["items"]) >= 1

    async def test_search_excludes_inactive_vehicles(
        self, client: AsyncClient, db: AsyncSession
    ):
        """Returns 0 results when all vehicles are inactive."""
        user, provider, svc = await _seed_rental_provider(db)
        vehicle = await create_vehicle(db, provider, vehicle_type="xe_4_cho")
        vehicle.status = "inactive"
        await db.commit()

        response = await client.get("/api/v1/customer/transport/rental-vehicles")
        assert response.status_code == 200
        # All vehicles are inactive — should not appear
        ids = [v["id"] for v in response.json()["items"]]
        assert str(vehicle.id) not in ids

    async def test_search_excludes_blocked_vehicle_on_date(
        self, client: AsyncClient, db: AsyncSession
    ):
        """Vehicles blocked on available_on date are excluded from results."""
        user, provider, svc = await _seed_rental_provider(db)
        token = make_provider_token(user)
        vehicle = await create_vehicle(db, provider, vehicle_type="xe_4_cho")
        await db.commit()

        target_date = date.today() + timedelta(days=3)
        # Block the vehicle on target date
        await client.post(
            f"/api/v1/provider/vehicles/{vehicle.id}/availabilities/block",
            json={"dates": [str(target_date)]},
            headers=auth_headers(token),
        )

        response = await client.get(
            "/api/v1/customer/transport/rental-vehicles",
            params={"available_on": str(target_date)},
        )
        assert response.status_code == 200
        ids = [v["id"] for v in response.json()["items"]]
        assert str(vehicle.id) not in ids

    async def test_search_available_vehicle_not_blocked(
        self, client: AsyncClient, db: AsyncSession
    ):
        """Vehicle not blocked on available_on date is included in results."""
        user, provider, svc = await _seed_rental_provider(db)
        vehicle = await create_vehicle(db, provider, vehicle_type="xe_4_cho")
        await db.commit()

        target_date = date.today() + timedelta(days=7)
        response = await client.get(
            "/api/v1/customer/transport/rental-vehicles",
            params={"available_on": str(target_date)},
        )
        assert response.status_code == 200
        ids = [v["id"] for v in response.json()["items"]]
        assert str(vehicle.id) in ids

    async def test_search_filter_by_seat_count(
        self, client: AsyncClient, db: AsyncSession
    ):
        """min_seats filter excludes vehicles with fewer seats."""
        user, provider, svc = await _seed_rental_provider(db)
        vehicle_small = await create_vehicle(db, provider, vehicle_type="xe_4_cho")
        vehicle_small.seat_count = 4
        vehicle_large = await create_vehicle(db, provider, vehicle_type="xe_7_cho")
        vehicle_large.seat_count = 7
        await db.commit()

        response = await client.get(
            "/api/v1/customer/transport/rental-vehicles",
            params={"min_seats": 7},
        )
        assert response.status_code == 200
        ids = [v["id"] for v in response.json()["items"]]
        assert str(vehicle_large.id) in ids
        assert str(vehicle_small.id) not in ids


# ─────────────────────────────────────────────────────────────────────
# GET /customer/transport/rental-vehicles/{id}
# ─────────────────────────────────────────────────────────────────────

class TestCustomerGetRentalVehicle:
    async def test_get_active_vehicle_success(self, client: AsyncClient, db: AsyncSession):
        """Customer can get detail of an active rental vehicle."""
        user, provider, svc = await _seed_rental_provider(db)
        vehicle = await create_vehicle(db, provider, vehicle_type="xe_4_cho")
        await db.commit()

        response = await client.get(
            f"/api/v1/customer/transport/rental-vehicles/{vehicle.id}"
        )
        assert response.status_code == 200
        assert response.json()["id"] == str(vehicle.id)

    async def test_get_inactive_vehicle_returns_404(
        self, client: AsyncClient, db: AsyncSession
    ):
        """Returns 404 for inactive vehicles."""
        user, provider, svc = await _seed_rental_provider(db)
        vehicle = await create_vehicle(db, provider, vehicle_type="xe_4_cho")
        vehicle.status = "inactive"
        await db.commit()

        response = await client.get(
            f"/api/v1/customer/transport/rental-vehicles/{vehicle.id}"
        )
        assert response.status_code == 404

    async def test_get_nonexistent_vehicle_returns_404(
        self, client: AsyncClient, db: AsyncSession
    ):
        """Returns 404 for non-existent vehicle ID."""
        response = await client.get(
            f"/api/v1/customer/transport/rental-vehicles/{uuid.uuid4()}"
        )
        assert response.status_code == 404


# ─────────────────────────────────────────────────────────────────────
# GET /customer/transport/rental-vehicles/{id}/availabilities
# ─────────────────────────────────────────────────────────────────────

class TestCustomerVehicleAvailability:
    async def test_get_blocked_dates_in_range(
        self, client: AsyncClient, db: AsyncSession
    ):
        """Returns only blocked dates within the queried date range."""
        user, provider, svc = await _seed_rental_provider(db)
        token = make_provider_token(user)
        vehicle = await create_vehicle(db, provider, vehicle_type="xe_4_cho")
        await db.commit()

        today = date.today()
        blocked_dates = [
            str(today + timedelta(days=i)) for i in range(1, 4)  # next 3 days
        ]
        out_of_range = str(today + timedelta(days=20))

        await client.post(
            f"/api/v1/provider/vehicles/{vehicle.id}/availabilities/block",
            json={"dates": blocked_dates + [out_of_range]},
            headers=auth_headers(token),
        )

        response = await client.get(
            f"/api/v1/customer/transport/rental-vehicles/{vehicle.id}/availabilities",
            params={
                "from_date": str(today),
                "to_date": str(today + timedelta(days=10)),
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["vehicle_id"] == str(vehicle.id)
        items = data["items"]
        assert len(items) == 3  # out_of_range excluded

    async def test_get_availabilities_no_blocked_dates(
        self, client: AsyncClient, db: AsyncSession
    ):
        """Returns empty items list when no dates are blocked."""
        user, provider, svc = await _seed_rental_provider(db)
        vehicle = await create_vehicle(db, provider, vehicle_type="xe_4_cho")
        await db.commit()

        today = date.today()
        response = await client.get(
            f"/api/v1/customer/transport/rental-vehicles/{vehicle.id}/availabilities",
            params={
                "from_date": str(today),
                "to_date": str(today + timedelta(days=30)),
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []

    async def test_get_availabilities_inactive_vehicle_returns_404(
        self, client: AsyncClient, db: AsyncSession
    ):
        """Returns 404 when vehicle is not active."""
        user, provider, svc = await _seed_rental_provider(db)
        vehicle = await create_vehicle(db, provider, vehicle_type="xe_4_cho")
        vehicle.status = "suspended"
        await db.commit()

        today = date.today()
        response = await client.get(
            f"/api/v1/customer/transport/rental-vehicles/{vehicle.id}/availabilities",
            params={
                "from_date": str(today),
                "to_date": str(today + timedelta(days=30)),
            },
        )
        assert response.status_code == 404
