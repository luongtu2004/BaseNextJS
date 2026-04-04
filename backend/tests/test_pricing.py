import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.conftest import create_user, make_admin_token, make_provider_token


@pytest.mark.asyncio
async def test_admin_create_and_list_price_config(client: AsyncClient, db: AsyncSession):
    admin_user = await create_user(db, phone="+84999999999", role="admin")
    token = make_admin_token(admin_user)
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Create a formula config
    resp = await client.post(
        "/api/v1/admin/price-configs",
        json={
            "service_type": "taxi",
            "pricing_mode": "formula",
            "base_fare": 15000,
            "fare_per_km": 12000,
            "fare_per_min": 500,
            "min_fare": 20000,
            "surge_enabled": False
        },
        headers=headers,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["service_type"] == "taxi"
    assert data["pricing_mode"] == "formula"
    assert data["base_fare"] == 15000
    config_id = data["id"]
    
    # 2. List configs
    resp2 = await client.get("/api/v1/admin/price-configs", headers=headers)
    assert resp2.status_code == 200
    list_data = resp2.json()
    assert list_data["total"] >= 1
    assert any(item["id"] == config_id for item in list_data["items"])
    
    # 3. Create a driver_quote config for same service_type -> should make old one inactive
    resp3 = await client.post(
        "/api/v1/admin/price-configs",
        json={
            "service_type": "taxi",
            "pricing_mode": "driver_quote",
            "min_quote": 50000,
            "max_quote": 200000,
            "quote_timeout_sec": 120,
            "accept_timeout_sec": 60
        },
        headers=headers,
    )
    assert resp3.status_code == 201
    data3 = resp3.json()
    assert data3["pricing_mode"] == "driver_quote"
    
    # List again to check old is inactive
    resp4 = await client.get("/api/v1/admin/price-configs", headers=headers)
    list_data4 = resp4.json()
    old_config = next(item for item in list_data4["items"] if item["id"] == config_id)
    assert old_config["is_active"] is False
    new_config = next(item for item in list_data4["items"] if item["id"] == data3["id"])
    assert new_config["is_active"] is True


@pytest.mark.asyncio
async def test_customer_estimate_fare(client: AsyncClient, db: AsyncSession):
    # Setup admin
    admin_user = await create_user(db, phone="+84888888888", role="admin")
    admin_token = make_admin_token(admin_user)
    
    # 1. Setup active price config (formula)
    await client.post(
        "/api/v1/admin/price-configs",
        json={
            "service_type": "xe_om",
            "pricing_mode": "formula",
            "base_fare": 10000,
            "fare_per_km": 5000, # 5km = 25000
            "fare_per_min": 0,
            "min_fare": 15000,
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    
    # 2. Setup active price config (quote)
    await client.post(
        "/api/v1/admin/price-configs",
        json={
            "service_type": "xe_tai",
            "pricing_mode": "driver_quote",
            "min_quote": 100000,
            "max_quote": 500000,
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    
    # 3. Customer estimates formula
    resp = await client.post(
        "/api/v1/customer/transport/estimate",
        json={
            "service_type": "xe_om",
            "distance_km": 5.0,
            "duration_min": 10
        }
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["pricing_mode"] == "formula"
    assert data["estimated_fare"] == 35000.0 # 10000 + 5000*5 + 0
    assert data["min_fare"] is None
    
    # 4. Customer estimates quote
    resp2 = await client.post(
        "/api/v1/customer/transport/estimate",
        json={
            "service_type": "xe_tai",
            "distance_km": 10.0,
            "duration_min": 20
        }
    )
    assert resp2.status_code == 200
    data2 = resp2.json()
    assert data2["pricing_mode"] == "driver_quote"
    assert data2["estimated_fare"] is None
    assert data2["min_fare"] == 100000.0
    assert data2["max_fare"] == 500000.0
