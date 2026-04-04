"""Unit tests — Provider Vehicle management (Phase 6.2).

Tests cover: create, list, get, update, status patch, delete,
             document CRUD, availability block/unblock.
"""

import uuid
from datetime import date, timedelta

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.conftest import (
    auth_headers,
    create_provider,
    create_provider_service,
    create_service_category,
    create_user,
    create_vehicle,
    make_provider_token,
)


pytestmark = pytest.mark.asyncio


# ─────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────

async def _setup(db: AsyncSession):
    """Seed a provider + service for vehicle tests."""
    user = await create_user(db)
    provider = await create_provider(db, user)
    category = await create_service_category(db, code="cho_thue_xe_tu_lai_oto")
    svc = await create_provider_service(db, provider, category)
    await db.commit()
    token = make_provider_token(user)
    return user, provider, svc, token


# ─────────────────────────────────────────────────────────────────────
# POST /provider/vehicles
# ─────────────────────────────────────────────────────────────────────

class TestCreateVehicle:
    async def test_create_vehicle_success(self, client: AsyncClient, db: AsyncSession):
        """Provider can create a new vehicle."""
        user, provider, svc, token = await _setup(db)
        payload = {
            "vehicle_type": "xe_4_cho",
            "vehicle_brand": "Toyota",
            "vehicle_model": "Vios",
            "year_of_manufacture": 2022,
            "license_plate": "51A-99999",
            "seat_count": 4,
            "fuel_type": "xang",
            "transmission": "auto",
            "has_ac": True,
            "has_wifi": False,
            "service_id": str(svc.id),
        }
        response = await client.post(
            "/api/v1/provider/vehicles",
            json=payload,
            headers=auth_headers(token),
        )
        assert response.status_code == 201, response.text
        data = response.json()
        assert data["vehicle_type"] == "xe_4_cho"
        assert data["provider_id"] == str(provider.id)
        assert data["service_id"] == str(svc.id)
        assert data["has_ac"] is True
        assert data["status"] == "active"

    async def test_create_vehicle_invalid_service_id(self, client: AsyncClient, db: AsyncSession):
        """Returns 404 if service_id does not belong to provider."""
        _, _, _, token = await _setup(db)
        payload = {
            "vehicle_type": "xe_4_cho",
            "service_id": str(uuid.uuid4()),
        }
        response = await client.post(
            "/api/v1/provider/vehicles",
            json=payload,
            headers=auth_headers(token),
        )
        assert response.status_code == 404

    async def test_create_vehicle_unauthenticated(self, client: AsyncClient, db: AsyncSession):
        """Returns 401 without auth token."""
        response = await client.post("/api/v1/provider/vehicles", json={"vehicle_type": "test"})
        assert response.status_code == 401

    async def test_create_vehicle_missing_required_field(self, client: AsyncClient, db: AsyncSession):
        """Returns 422 when vehicle_type is missing."""
        _, _, _, token = await _setup(db)
        response = await client.post(
            "/api/v1/provider/vehicles",
            json={},
            headers=auth_headers(token),
        )
        assert response.status_code == 422


# ─────────────────────────────────────────────────────────────────────
# GET /provider/vehicles
# ─────────────────────────────────────────────────────────────────────

class TestListVehicles:
    async def test_list_returns_own_vehicles_only(self, client: AsyncClient, db: AsyncSession):
        """Provider sees only their own vehicles."""
        user, provider, svc, token = await _setup(db)
        await create_vehicle(db, provider, vehicle_type="xe_tai")
        await create_vehicle(db, provider, vehicle_type="xe_may")

        # Create a second provider with a vehicle
        user2 = await create_user(db, phone="+84900000002")
        provider2 = await create_provider(db, user2)
        await create_vehicle(db, provider2, vehicle_type="xe_7_cho")
        await db.commit()

        response = await client.get("/api/v1/provider/vehicles", headers=auth_headers(token))
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        types = {v["vehicle_type"] for v in data}
        assert types == {"xe_tai", "xe_may"}

    async def test_list_empty_when_no_vehicles(self, client: AsyncClient, db: AsyncSession):
        """Returns empty list when provider has no vehicles."""
        _, _, _, token = await _setup(db)
        response = await client.get("/api/v1/provider/vehicles", headers=auth_headers(token))
        assert response.status_code == 200
        assert response.json() == []


# ─────────────────────────────────────────────────────────────────────
# GET /provider/vehicles/{id}
# ─────────────────────────────────────────────────────────────────────

class TestGetVehicle:
    async def test_get_own_vehicle_success(self, client: AsyncClient, db: AsyncSession):
        """Provider can get detail of their own vehicle."""
        user, provider, svc, token = await _setup(db)
        vehicle = await create_vehicle(db, provider)
        await db.commit()

        response = await client.get(
            f"/api/v1/provider/vehicles/{vehicle.id}",
            headers=auth_headers(token),
        )
        assert response.status_code == 200
        assert response.json()["id"] == str(vehicle.id)

    async def test_get_other_provider_vehicle_returns_404(
        self, client: AsyncClient, db: AsyncSession
    ):
        """Cannot access another provider's vehicle."""
        user1, provider1, _, token1 = await _setup(db)
        user2 = await create_user(db, phone="+84900000002")
        provider2 = await create_provider(db, user2)
        vehicle2 = await create_vehicle(db, provider2)
        await db.commit()

        response = await client.get(
            f"/api/v1/provider/vehicles/{vehicle2.id}",
            headers=auth_headers(token1),
        )
        assert response.status_code == 404

    async def test_get_nonexistent_vehicle_returns_404(self, client: AsyncClient, db: AsyncSession):
        """Returns 404 for non-existent vehicle ID."""
        _, _, _, token = await _setup(db)
        response = await client.get(
            f"/api/v1/provider/vehicles/{uuid.uuid4()}",
            headers=auth_headers(token),
        )
        assert response.status_code == 404


# ─────────────────────────────────────────────────────────────────────
# PUT /provider/vehicles/{id}
# ─────────────────────────────────────────────────────────────────────

class TestUpdateVehicle:
    async def test_update_vehicle_partial(self, client: AsyncClient, db: AsyncSession):
        """Partial update: only sent fields are changed."""
        user, provider, svc, token = await _setup(db)
        vehicle = await create_vehicle(db, provider, vehicle_type="xe_4_cho")
        await db.commit()

        response = await client.put(
            f"/api/v1/provider/vehicles/{vehicle.id}",
            json={"vehicle_brand": "Honda", "has_wifi": True},
            headers=auth_headers(token),
        )
        assert response.status_code == 200
        data = response.json()
        assert data["vehicle_brand"] == "Honda"
        assert data["has_wifi"] is True
        assert data["vehicle_type"] == "xe_4_cho"  # unchanged

    async def test_update_vehicle_with_invalid_service(self, client: AsyncClient, db: AsyncSession):
        """Returns 404 if updating to a service that does not belong to provider."""
        user, provider, svc, token = await _setup(db)
        vehicle = await create_vehicle(db, provider)
        await db.commit()

        response = await client.put(
            f"/api/v1/provider/vehicles/{vehicle.id}",
            json={"service_id": str(uuid.uuid4())},
            headers=auth_headers(token),
        )
        assert response.status_code == 404


# ─────────────────────────────────────────────────────────────────────
# PATCH /provider/vehicles/{id}/status
# ─────────────────────────────────────────────────────────────────────

class TestPatchVehicleStatus:
    async def test_deactivate_vehicle(self, client: AsyncClient, db: AsyncSession):
        """Provider can deactivate their vehicle."""
        user, provider, _, token = await _setup(db)
        vehicle = await create_vehicle(db, provider)
        await db.commit()

        response = await client.patch(
            f"/api/v1/provider/vehicles/{vehicle.id}/status",
            json={"status": "inactive"},
            headers=auth_headers(token),
        )
        assert response.status_code == 200
        assert response.json()["status"] == "inactive"

    async def test_invalid_status_returns_400(self, client: AsyncClient, db: AsyncSession):
        """Returns 422 (Pydantic Literal validation) for invalid status value."""
        user, provider, _, token = await _setup(db)
        vehicle = await create_vehicle(db, provider)
        await db.commit()

        response = await client.patch(
            f"/api/v1/provider/vehicles/{vehicle.id}/status",
            json={"status": "suspended"},  # only provider can set active/inactive; Literal rejects suspended
            headers=auth_headers(token),
        )
        assert response.status_code == 422

    async def test_reactivate_vehicle(self, client: AsyncClient, db: AsyncSession):
        """Provider can reactivate an inactive vehicle."""
        user, provider, _, token = await _setup(db)
        vehicle = await create_vehicle(db, provider)
        vehicle.status = "inactive"
        await db.commit()

        response = await client.patch(
            f"/api/v1/provider/vehicles/{vehicle.id}/status",
            json={"status": "active"},
            headers=auth_headers(token),
        )
        assert response.status_code == 200
        assert response.json()["status"] == "active"


# ─────────────────────────────────────────────────────────────────────
# DELETE /provider/vehicles/{id}
# ─────────────────────────────────────────────────────────────────────

class TestDeleteVehicle:
    async def test_delete_own_vehicle(self, client: AsyncClient, db: AsyncSession):
        """Provider can delete their own vehicle."""
        user, provider, _, token = await _setup(db)
        vehicle = await create_vehicle(db, provider)
        await db.commit()

        response = await client.delete(
            f"/api/v1/provider/vehicles/{vehicle.id}",
            headers=auth_headers(token),
        )
        assert response.status_code == 204

        # Verify deleted
        get_resp = await client.get(
            f"/api/v1/provider/vehicles/{vehicle.id}",
            headers=auth_headers(token),
        )
        assert get_resp.status_code == 404

    async def test_delete_other_provider_vehicle_returns_404(
        self, client: AsyncClient, db: AsyncSession
    ):
        """Cannot delete another provider's vehicle."""
        user1, provider1, _, token1 = await _setup(db)
        user2 = await create_user(db, phone="+84900000002")
        provider2 = await create_provider(db, user2)
        vehicle2 = await create_vehicle(db, provider2)
        await db.commit()

        response = await client.delete(
            f"/api/v1/provider/vehicles/{vehicle2.id}",
            headers=auth_headers(token1),
        )
        assert response.status_code == 404


# ─────────────────────────────────────────────────────────────────────
# Vehicle Documents
# ─────────────────────────────────────────────────────────────────────

class TestVehicleDocuments:
    async def test_add_document_success(self, client: AsyncClient, db: AsyncSession):
        """Provider can add a document to their vehicle."""
        user, provider, _, token = await _setup(db)
        vehicle = await create_vehicle(db, provider)
        await db.commit()

        today = date.today()
        payload = {
            "document_type": "dang_kiem_xe",
            "document_number": "DK2024001",
            "issued_date": str(today),
            "expiry_date": str(today.replace(year=today.year + 1)),
        }
        response = await client.post(
            f"/api/v1/provider/vehicles/{vehicle.id}/documents",
            json=payload,
            headers=auth_headers(token),
        )
        assert response.status_code == 201
        data = response.json()
        assert data["document_type"] == "dang_kiem_xe"
        assert data["review_status"] == "pending"

    async def test_add_document_invalid_dates(self, client: AsyncClient, db: AsyncSession):
        """Returns 400 when expiry_date is before issued_date."""
        user, provider, _, token = await _setup(db)
        vehicle = await create_vehicle(db, provider)
        await db.commit()

        today = date.today()
        payload = {
            "document_type": "bao_hiem_tnds",
            "issued_date": str(today),
            "expiry_date": str(today - timedelta(days=1)),  # before issued!
        }
        response = await client.post(
            f"/api/v1/provider/vehicles/{vehicle.id}/documents",
            json=payload,
            headers=auth_headers(token),
        )
        assert response.status_code == 400

    async def test_list_documents(self, client: AsyncClient, db: AsyncSession):
        """Provider can list documents for their vehicle."""
        user, provider, _, token = await _setup(db)
        vehicle = await create_vehicle(db, provider)
        await db.commit()

        # Add two documents
        for doc_type in ("dang_ky_xe", "bao_hiem_tnds"):
            await client.post(
                f"/api/v1/provider/vehicles/{vehicle.id}/documents",
                json={"document_type": doc_type},
                headers=auth_headers(token),
            )

        response = await client.get(
            f"/api/v1/provider/vehicles/{vehicle.id}/documents",
            headers=auth_headers(token),
        )
        assert response.status_code == 200
        assert len(response.json()) == 2

    async def test_update_approved_document_returns_400(
        self, client: AsyncClient, db: AsyncSession
    ):
        """Cannot edit an already approved document."""
        from app.models.transport import ProviderVehicleDocument
        from datetime import datetime, timezone

        user, provider, _, token = await _setup(db)
        vehicle = await create_vehicle(db, provider)
        doc = ProviderVehicleDocument(
            id=uuid.uuid4(),
            vehicle_id=vehicle.id,
            document_type="dang_ky_xe",
            review_status="approved",
            created_at=datetime.now(tz=timezone.utc),
            updated_at=datetime.now(tz=timezone.utc),
        )
        db.add(doc)
        await db.commit()

        response = await client.put(
            f"/api/v1/provider/vehicles/{vehicle.id}/documents/{doc.id}",
            json={"document_number": "NEW123"},
            headers=auth_headers(token),
        )
        assert response.status_code == 400

    async def test_delete_document_success(self, client: AsyncClient, db: AsyncSession):
        """Provider can delete a vehicle document."""
        user, provider, _, token = await _setup(db)
        vehicle = await create_vehicle(db, provider)
        await db.commit()

        # Add a doc
        add_resp = await client.post(
            f"/api/v1/provider/vehicles/{vehicle.id}/documents",
            json={"document_type": "dang_ky_xe"},
            headers=auth_headers(token),
        )
        doc_id = add_resp.json()["id"]

        del_resp = await client.delete(
            f"/api/v1/provider/vehicles/{vehicle.id}/documents/{doc_id}",
            headers=auth_headers(token),
        )
        assert del_resp.status_code == 204


# ─────────────────────────────────────────────────────────────────────
# Vehicle Availability
# ─────────────────────────────────────────────────────────────────────

class TestVehicleAvailability:
    async def test_block_future_dates(self, client: AsyncClient, db: AsyncSession):
        """Provider can block future dates."""
        user, provider, _, token = await _setup(db)
        vehicle = await create_vehicle(db, provider)
        await db.commit()

        today = date.today()
        dates_to_block = [
            str(today + timedelta(days=1)),
            str(today + timedelta(days=2)),
            str(today + timedelta(days=3)),
        ]
        response = await client.post(
            f"/api/v1/provider/vehicles/{vehicle.id}/availabilities/block",
            json={"dates": dates_to_block, "reason": "Bảo dưỡng định kỳ"},
            headers=auth_headers(token),
        )
        assert response.status_code == 200
        data = response.json()
        assert data["blocked_count"] == 3

    async def test_block_past_dates_returns_400(self, client: AsyncClient, db: AsyncSession):
        """Cannot block dates in the past."""
        user, provider, _, token = await _setup(db)
        vehicle = await create_vehicle(db, provider)
        await db.commit()

        past_date = str(date.today() - timedelta(days=1))
        response = await client.post(
            f"/api/v1/provider/vehicles/{vehicle.id}/availabilities/block",
            json={"dates": [past_date]},
            headers=auth_headers(token),
        )
        assert response.status_code == 400

    async def test_unblock_dates(self, client: AsyncClient, db: AsyncSession):
        """Provider can unblock previously blocked dates."""
        user, provider, _, token = await _setup(db)
        vehicle = await create_vehicle(db, provider)
        await db.commit()

        future = date.today() + timedelta(days=5)
        # Block first
        await client.post(
            f"/api/v1/provider/vehicles/{vehicle.id}/availabilities/block",
            json={"dates": [str(future)]},
            headers=auth_headers(token),
        )
        # Then unblock
        unblock_resp = await client.post(
            f"/api/v1/provider/vehicles/{vehicle.id}/availabilities/unblock",
            json={"dates": [str(future)]},
            headers=auth_headers(token),
        )
        assert unblock_resp.status_code == 200
        assert unblock_resp.json()["unblocked_count"] == 1

    async def test_get_availabilities_in_range(self, client: AsyncClient, db: AsyncSession):
        """Returns blocked dates within queried range."""
        user, provider, _, token = await _setup(db)
        vehicle = await create_vehicle(db, provider)
        await db.commit()

        today = date.today()
        future1 = today + timedelta(days=2)
        future2 = today + timedelta(days=4)

        await client.post(
            f"/api/v1/provider/vehicles/{vehicle.id}/availabilities/block",
            json={"dates": [str(future1), str(future2)]},
            headers=auth_headers(token),
        )

        response = await client.get(
            f"/api/v1/provider/vehicles/{vehicle.id}/availabilities",
            params={
                "from_date": str(today),
                "to_date": str(today + timedelta(days=10)),
            },
            headers=auth_headers(token),
        )
        assert response.status_code == 200
        data = response.json()
        assert data["vehicle_id"] == str(vehicle.id)
        assert len(data["items"]) == 2

    async def test_get_availabilities_invalid_range(self, client: AsyncClient, db: AsyncSession):
        """Returns 400 when from_date > to_date."""
        user, provider, _, token = await _setup(db)
        vehicle = await create_vehicle(db, provider)
        await db.commit()

        today = date.today()
        response = await client.get(
            f"/api/v1/provider/vehicles/{vehicle.id}/availabilities",
            params={
                "from_date": str(today + timedelta(days=5)),
                "to_date": str(today),
            },
            headers=auth_headers(token),
        )
        assert response.status_code == 400

    async def test_block_same_date_twice_is_idempotent(self, client: AsyncClient, db: AsyncSession):
        """Blocking the same date twice does not create duplicate records."""
        user, provider, _, token = await _setup(db)
        vehicle = await create_vehicle(db, provider)
        await db.commit()

        future = str(date.today() + timedelta(days=3))
        await client.post(
            f"/api/v1/provider/vehicles/{vehicle.id}/availabilities/block",
            json={"dates": [future]},
            headers=auth_headers(token),
        )
        resp2 = await client.post(
            f"/api/v1/provider/vehicles/{vehicle.id}/availabilities/block",
            json={"dates": [future]},
            headers=auth_headers(token),
        )
        assert resp2.status_code == 200
        # Second call: blocked_count=0 (already exists), updated_count=1
        assert resp2.json()["blocked_count"] == 0
        assert resp2.json()["updated_count"] == 1
