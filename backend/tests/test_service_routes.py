"""Unit tests — Service Routes & Schedules (Phase 6.3).

Tests cover: route CRUD, province validation, schedule CRUD,
             duplicate-time conflict, ownership enforcement.
"""

import uuid
from datetime import datetime, time, timezone

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
    make_provider_token,
)


pytestmark = pytest.mark.asyncio


# ─────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────

async def _setup(db: AsyncSession):
    """Seed provider + service for route tests."""
    user = await create_user(db)
    provider = await create_provider(db, user)
    category = await create_service_category(db, code="xe_khach_lien_tinh")
    svc = await create_provider_service(db, provider, category)
    await db.commit()
    token = make_provider_token(user)
    return user, provider, svc, token


def _route_url(svc_id) -> str:
    return f"/api/v1/provider/services/{svc_id}/routes"


def _schedule_url(route_id) -> str:
    return f"/api/v1/provider/routes/{route_id}/schedules"


# ─────────────────────────────────────────────────────────────────────
# POST /provider/services/{svc_id}/routes
# ─────────────────────────────────────────────────────────────────────

class TestCreateRoute:
    async def test_create_route_success(self, client: AsyncClient, db: AsyncSession):
        """Provider can create a route between different provinces."""
        user, provider, svc, token = await _setup(db)
        payload = {
            "from_province": "Hà Nội",
            "to_province": "Đà Nẵng",
            "price": 350000,
            "distance_km": 764,
            "duration_min": 720,
        }
        response = await client.post(
            _route_url(svc.id), json=payload, headers=auth_headers(token)
        )
        assert response.status_code == 201, response.text
        data = response.json()
        assert data["from_province"] == "Hà Nội"
        assert data["to_province"] == "Đà Nẵng"
        assert data["is_active"] is True
        assert data["schedules"] == []

    async def test_create_route_same_province_rejected(
        self, client: AsyncClient, db: AsyncSession
    ):
        """Returns 400 when from_province == to_province."""
        user, provider, svc, token = await _setup(db)
        payload = {
            "from_province": "Hà Nội",
            "to_province": "Hà Nội",
            "price": 100000,
        }
        response = await client.post(
            _route_url(svc.id), json=payload, headers=auth_headers(token)
        )
        assert response.status_code == 400

    async def test_create_route_service_not_owned(
        self, client: AsyncClient, db: AsyncSession
    ):
        """Returns 404 when service_id belongs to another provider."""
        user1, provider1, svc1, token1 = await _setup(db)
        user2 = await create_user(db, phone="+84900000002")
        provider2 = await create_provider(db, user2)
        cat2 = await create_service_category(db, code="xe_khach_lienz")
        svc2 = await create_provider_service(db, provider2, cat2)
        await db.commit()

        response = await client.post(
            _route_url(svc2.id),
            json={"from_province": "Hà Nội", "to_province": "HCM", "price": 500000},
            headers=auth_headers(token1),
        )
        # API returns 404 to avoid disclosing resource existence to unauthorized callers
        assert response.status_code == 404

    async def test_create_route_missing_price(self, client: AsyncClient, db: AsyncSession):
        """Returns 422 when required price is missing."""
        user, provider, svc, token = await _setup(db)
        response = await client.post(
            _route_url(svc.id),
            json={"from_province": "Hà Nội", "to_province": "HCM"},
            headers=auth_headers(token),
        )
        assert response.status_code == 422


# ─────────────────────────────────────────────────────────────────────
# GET /provider/services/{svc_id}/routes
# ─────────────────────────────────────────────────────────────────────

class TestListRoutes:
    async def test_list_routes_returns_own_only(
        self, client: AsyncClient, db: AsyncSession
    ):
        """Provider only sees their own routes."""
        user, provider, svc, token = await _setup(db)
        await create_route(db, svc)
        await create_route(db, svc, from_province="Hà Nội", to_province="Cần Thơ")

        user2 = await create_user(db, phone="+84900000002")
        provider2 = await create_provider(db, user2)
        cat2 = await create_service_category(db, code="xe_khach2")
        svc2 = await create_provider_service(db, provider2, cat2)
        await create_route(db, svc2)
        await db.commit()

        response = await client.get(_route_url(svc.id), headers=auth_headers(token))
        assert response.status_code == 200
        assert len(response.json()["items"]) == 2

    async def test_list_routes_empty(self, client: AsyncClient, db: AsyncSession):
        """Returns empty list when no routes exist."""
        user, provider, svc, token = await _setup(db)
        response = await client.get(_route_url(svc.id), headers=auth_headers(token))
        assert response.status_code == 200
        assert response.json()["items"] == []


# ─────────────────────────────────────────────────────────────────────
# GET /provider/services/{svc_id}/routes/{route_id}
# ─────────────────────────────────────────────────────────────────────

class TestGetRoute:
    async def test_get_route_detail(self, client: AsyncClient, db: AsyncSession):
        """Provider can get route detail with schedules."""
        user, provider, svc, token = await _setup(db)
        route = await create_route(db, svc)
        await db.commit()

        response = await client.get(
            f"/api/v1/provider/services/{svc.id}/routes/{route.id}",
            headers=auth_headers(token),
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(route.id)
        assert "schedules" in data

    async def test_get_nonexistent_route(self, client: AsyncClient, db: AsyncSession):
        """Returns 404 for non-existent route."""
        user, provider, svc, token = await _setup(db)
        response = await client.get(
            f"/api/v1/provider/services/{svc.id}/routes/{uuid.uuid4()}",
            headers=auth_headers(token),
        )
        assert response.status_code == 404


# ─────────────────────────────────────────────────────────────────────
# PUT /provider/services/{svc_id}/routes/{route_id}
# ─────────────────────────────────────────────────────────────────────

class TestUpdateRoute:
    async def test_update_route_price(self, client: AsyncClient, db: AsyncSession):
        """Provider can update route price."""
        user, provider, svc, token = await _setup(db)
        route = await create_route(db, svc)
        await db.commit()

        response = await client.put(
            f"/api/v1/provider/services/{svc.id}/routes/{route.id}",
            json={"price": 450000, "notes": "Giá cao điểm"},
            headers=auth_headers(token),
        )
        assert response.status_code == 200
        data = response.json()
        assert float(data["price"]) == 450000.0

    async def test_update_route_same_province(self, client: AsyncClient, db: AsyncSession):
        """Returns 400 when updating makes from == to."""
        user, provider, svc, token = await _setup(db)
        route = await create_route(
            db, svc, from_province="Hà Nội", to_province="Đà Nẵng"
        )
        await db.commit()

        response = await client.put(
            f"/api/v1/provider/services/{svc.id}/routes/{route.id}",
            json={"to_province": "Hà Nội"},  # makes from == to
            headers=auth_headers(token),
        )
        assert response.status_code == 400


# ─────────────────────────────────────────────────────────────────────
# PATCH /provider/services/{svc_id}/routes/{route_id}/status
# ─────────────────────────────────────────────────────────────────────

class TestPatchRouteStatus:
    async def test_toggle_route_active_status(self, client: AsyncClient, db: AsyncSession):
        """Provider can toggle route active status."""
        user, provider, svc, token = await _setup(db)
        route = await create_route(db, svc)
        await db.commit()

        response = await client.patch(
            f"/api/v1/provider/services/{svc.id}/routes/{route.id}/status",
            json={"is_active": False},
            headers=auth_headers(token),
        )
        assert response.status_code == 200
        assert response.json()["is_active"] is False


# ─────────────────────────────────────────────────────────────────────
# DELETE /provider/services/{svc_id}/routes/{route_id}
# ─────────────────────────────────────────────────────────────────────

class TestDeleteRoute:
    async def test_delete_route_removes_schedules(
        self, client: AsyncClient, db: AsyncSession
    ):
        """Deleting a route cascades to its schedules."""
        user, provider, svc, token = await _setup(db)
        route = await create_route(db, svc)
        await db.commit()

        # Add a schedule
        await client.post(
            _schedule_url(route.id),
            json={"departure_time": "08:00:00", "seat_count": 45},
            headers=auth_headers(token),
        )

        # Delete route
        del_resp = await client.delete(
            f"/api/v1/provider/services/{svc.id}/routes/{route.id}",
            headers=auth_headers(token),
        )
        assert del_resp.status_code == 204

        # Route is gone
        get_resp = await client.get(
            f"/api/v1/provider/services/{svc.id}/routes/{route.id}",
            headers=auth_headers(token),
        )
        assert get_resp.status_code == 404


# ─────────────────────────────────────────────────────────────────────
# POST /provider/routes/{route_id}/schedules
# ─────────────────────────────────────────────────────────────────────

class TestCreateSchedule:
    async def test_create_schedule_success(self, client: AsyncClient, db: AsyncSession):
        """Provider can add a departure schedule to a route."""
        user, provider, svc, token = await _setup(db)
        route = await create_route(db, svc)
        await db.commit()

        response = await client.post(
            _schedule_url(route.id),
            json={"departure_time": "06:30:00", "seat_count": 45},
            headers=auth_headers(token),
        )
        assert response.status_code == 201, response.text
        data = response.json()
        assert data["departure_time"] == "06:30:00"
        assert data["seat_count"] == 45
        assert data["is_active"] is True

    async def test_create_duplicate_departure_time_returns_409(
        self, client: AsyncClient, db: AsyncSession
    ):
        """Returns 409 when creating a schedule with an existing departure time."""
        user, provider, svc, token = await _setup(db)
        route = await create_route(db, svc)
        await db.commit()

        payload = {"departure_time": "08:00:00", "seat_count": 45}
        await client.post(
            _schedule_url(route.id), json=payload, headers=auth_headers(token)
        )
        resp2 = await client.post(
            _schedule_url(route.id), json=payload, headers=auth_headers(token)
        )
        assert resp2.status_code == 409

    async def test_create_schedule_missing_seat_count(
        self, client: AsyncClient, db: AsyncSession
    ):
        """Returns 422 when seat_count is missing."""
        user, provider, svc, token = await _setup(db)
        route = await create_route(db, svc)
        await db.commit()

        response = await client.post(
            _schedule_url(route.id),
            json={"departure_time": "09:00:00"},  # missing seat_count
            headers=auth_headers(token),
        )
        assert response.status_code == 422


# ─────────────────────────────────────────────────────────────────────
# GET /provider/routes/{route_id}/schedules
# ─────────────────────────────────────────────────────────────────────

class TestListSchedules:
    async def test_list_schedules_ordered_by_time(
        self, client: AsyncClient, db: AsyncSession
    ):
        """Schedules are returned ordered by departure_time."""
        user, provider, svc, token = await _setup(db)
        route = await create_route(db, svc)
        await db.commit()

        for t in ("12:00:00", "06:00:00", "18:00:00"):
            await client.post(
                _schedule_url(route.id),
                json={"departure_time": t, "seat_count": 45},
                headers=auth_headers(token),
            )

        response = await client.get(_schedule_url(route.id), headers=auth_headers(token))
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 3
        times = [s["departure_time"] for s in data["items"]]
        assert times == sorted(times)


# ─────────────────────────────────────────────────────────────────────
# PUT /provider/routes/{route_id}/schedules/{schedule_id}
# ─────────────────────────────────────────────────────────────────────

class TestUpdateSchedule:
    async def test_update_schedule_success(self, client: AsyncClient, db: AsyncSession):
        """Provider can update schedule seat count."""
        user, provider, svc, token = await _setup(db)
        route = await create_route(db, svc)
        await db.commit()

        create_resp = await client.post(
            _schedule_url(route.id),
            json={"departure_time": "07:00:00", "seat_count": 40},
            headers=auth_headers(token),
        )
        sched_id = create_resp.json()["id"]

        response = await client.put(
            f"/api/v1/provider/routes/{route.id}/schedules/{sched_id}",
            json={"seat_count": 50},
            headers=auth_headers(token),
        )
        assert response.status_code == 200
        assert response.json()["seat_count"] == 50

    async def test_update_schedule_to_duplicate_time_returns_409(
        self, client: AsyncClient, db: AsyncSession
    ):
        """Returns 409 when updating departure_time conflicts with existing."""
        user, provider, svc, token = await _setup(db)
        route = await create_route(db, svc)
        await db.commit()

        await client.post(
            _schedule_url(route.id),
            json={"departure_time": "08:00:00", "seat_count": 45},
            headers=auth_headers(token),
        )
        resp2 = await client.post(
            _schedule_url(route.id),
            json={"departure_time": "10:00:00", "seat_count": 45},
            headers=auth_headers(token),
        )
        sched2_id = resp2.json()["id"]

        # Try to change sched2's time to 08:00 (conflict)
        response = await client.put(
            f"/api/v1/provider/routes/{route.id}/schedules/{sched2_id}",
            json={"departure_time": "08:00:00"},
            headers=auth_headers(token),
        )
        assert response.status_code == 409


# ─────────────────────────────────────────────────────────────────────
# PATCH /provider/routes/{route_id}/schedules/{schedule_id}/status
# ─────────────────────────────────────────────────────────────────────

class TestPatchScheduleStatus:
    async def test_deactivate_schedule(self, client: AsyncClient, db: AsyncSession):
        """Provider can deactivate a schedule."""
        user, provider, svc, token = await _setup(db)
        route = await create_route(db, svc)
        await db.commit()

        create_resp = await client.post(
            _schedule_url(route.id),
            json={"departure_time": "07:00:00", "seat_count": 40},
            headers=auth_headers(token),
        )
        sched_id = create_resp.json()["id"]

        response = await client.patch(
            f"/api/v1/provider/routes/{route.id}/schedules/{sched_id}/status",
            json={"is_active": False},
            headers=auth_headers(token),
        )
        assert response.status_code == 200
        assert response.json()["is_active"] is False


# ─────────────────────────────────────────────────────────────────────
# DELETE /provider/routes/{route_id}/schedules/{schedule_id}
# ─────────────────────────────────────────────────────────────────────

class TestDeleteSchedule:
    async def test_delete_schedule_success(self, client: AsyncClient, db: AsyncSession):
        """Provider can delete a schedule."""
        user, provider, svc, token = await _setup(db)
        route = await create_route(db, svc)
        await db.commit()

        create_resp = await client.post(
            _schedule_url(route.id),
            json={"departure_time": "07:00:00", "seat_count": 40},
            headers=auth_headers(token),
        )
        sched_id = create_resp.json()["id"]

        del_resp = await client.delete(
            f"/api/v1/provider/routes/{route.id}/schedules/{sched_id}",
            headers=auth_headers(token),
        )
        assert del_resp.status_code == 204

    async def test_delete_nonexistent_schedule(self, client: AsyncClient, db: AsyncSession):
        """Returns 404 when deleting a non-existent schedule."""
        user, provider, svc, token = await _setup(db)
        route = await create_route(db, svc)
        await db.commit()

        response = await client.delete(
            f"/api/v1/provider/routes/{route.id}/schedules/{uuid.uuid4()}",
            headers=auth_headers(token),
        )
        assert response.status_code == 404


# ─────────────────────────────────────────────────────────────────────
# Cross-provider ownership enforcement
# ─────────────────────────────────────────────────────────────────────

class TestOwnershipEnforcement:
    async def test_provider_cannot_list_other_provider_routes(
        self, client: AsyncClient, db: AsyncSession
    ):
        """Provider gets 404 when listing routes of another provider's service."""
        user1, _, svc1, token1 = await _setup(db)
        user2 = await create_user(db, phone="+84900000002")
        provider2 = await create_provider(db, user2)
        cat2 = await create_service_category(db, code="xe_khach_b")
        svc2 = await create_provider_service(db, provider2, cat2)
        await create_route(db, svc2)
        await db.commit()

        response = await client.get(_route_url(svc2.id), headers=auth_headers(token1))
        # 404 is correct: service not found for this provider (avoids info disclosure)
        assert response.status_code == 404

    async def test_provider_cannot_delete_other_provider_route(
        self, client: AsyncClient, db: AsyncSession
    ):
        """Provider gets 404 when deleting a route owned by another provider."""
        user1, _, svc1, token1 = await _setup(db)
        user2 = await create_user(db, phone="+84900000002")
        provider2 = await create_provider(db, user2)
        cat2 = await create_service_category(db, code="xe_khach_c")
        svc2 = await create_provider_service(db, provider2, cat2)
        route2 = await create_route(db, svc2)
        await db.commit()

        response = await client.delete(
            f"/api/v1/provider/services/{svc2.id}/routes/{route2.id}",
            headers=auth_headers(token1),
        )
        # 404 is correct: service not found for this provider (avoids info disclosure)
        assert response.status_code == 404
