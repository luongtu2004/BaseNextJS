"""Test configuration and shared fixtures for Phase 6 tests.

Uses pytest-asyncio with in-memory SQLite for fast unit tests.
All tests hit the Router layer directly via FastAPI TestClient / AsyncClient.
"""

# ── MUST be set BEFORE any app import so get_settings() caches SQLite config ──
import os
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
os.environ.setdefault("JWT_ACCESS_SECRET", "test-access-secret-32-chars-min!")
os.environ.setdefault("JWT_REFRESH_SECRET", "test-refresh-secret-32-chars-min!")
os.environ.setdefault("JWT_ACCESS_EXPIRE_MINUTES", "15")
os.environ.setdefault("JWT_REFRESH_EXPIRE_DAYS", "30")
# ──────────────────────────────────────────────────────────────────────────────

import uuid
from datetime import date, datetime, timezone
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy import select
from sqlalchemy.dialects.sqlite.base import SQLiteTypeCompiler
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

# ── SQLite compat: render PostgreSQL JSONB as TEXT ────────────────────
SQLiteTypeCompiler.visit_JSONB = lambda self, type_, **kw: "TEXT"  # type: ignore[attr-defined]
# ─────────────────────────────────────────────────────────────────────

from app.db.base import Base
from app.db.session import get_db
from app.models import *  # noqa: F401,F403 — registers all ORM models
from app.models.provider import Provider, ProviderIndividualProfile
from app.models.transport import (
    ProviderVehicle,
    ProviderVehicleDocument,
    ServiceRoute,
    ServiceRouteSchedule,
)
from app.models.user import User, UserRole
from app.models.provider_service import ProviderService
from app.models.taxonomy import IndustryCategory, ServiceCategory
from app.core.security import create_access_token
from app.main import app

# ── SQLite in-memory engine ──────────────────────────────────────────
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False,
)
TestSessionLocal = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False, autoflush=False
)


@pytest_asyncio.fixture(scope="function", autouse=True)
async def setup_db():
    """Create all tables before each test, drop after."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture()
async def db() -> AsyncGenerator[AsyncSession, None]:
    """Provide a test DB session."""
    async with TestSessionLocal() as session:
        yield session


@pytest_asyncio.fixture()
async def client(db: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Provide an HTTP test client with overridden DB dependency."""

    async def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac
    app.dependency_overrides.clear()


# ── Seed helpers ─────────────────────────────────────────────────────


async def create_user(
    db: AsyncSession,
    *,
    phone: str = "+84900000001",
    role: str = "provider_owner",
) -> User:
    """Create a test user with a role."""
    now = datetime.now(tz=timezone.utc)
    user = User(
        id=uuid.uuid4(),
        phone=phone,
        password_hash="$2b$12$fakehash",
        status="active",
        created_at=now,
        updated_at=now,
    )
    db.add(user)
    db.add(UserRole(
        id=uuid.uuid4(),
        user_id=user.id,
        role_code=role,
        created_at=now,
    ))
    await db.flush()
    return user


async def create_provider(db: AsyncSession, owner: User) -> Provider:
    """Create a test provider."""
    now = datetime.now(tz=timezone.utc)
    provider = Provider(
        id=uuid.uuid4(),
        owner_user_id=owner.id,
        provider_type="individual",
        status="active",
        verification_status="approved",
        avg_rating=4.5,
        created_at=now,
        updated_at=now,
    )
    profile = ProviderIndividualProfile(
        provider_id=provider.id,
        full_name="Test Provider",
        created_at=now,
        updated_at=now,
    )
    db.add(provider)
    db.add(profile)
    await db.flush()
    return provider


async def create_service_category(
    db: AsyncSession,
    *,
    code: str = "cho_thue_xe_tu_lai_oto",
) -> ServiceCategory:
    """Create a test service category, reusing industry if it already exists."""
    now = datetime.now(tz=timezone.utc)
    # Reuse existing IndustryCategory to avoid unique constraint violation
    existing = (
        await db.execute(select(IndustryCategory).where(IndustryCategory.code == "vantaidichuyen"))
    ).scalar_one_or_none()

    if existing:
        industry = existing
    else:
        industry = IndustryCategory(
            id=uuid.uuid4(),
            code="vantaidichuyen",
            name="Vận tải",
            is_active=True,
            created_at=now,
            updated_at=now,
        )
        db.add(industry)
        await db.flush()

    category = ServiceCategory(
        id=uuid.uuid4(),
        industry_category_id=industry.id,
        code=code,
        name=code,
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    db.add(category)
    await db.flush()
    return category


async def create_provider_service(
    db: AsyncSession,
    provider: Provider,
    category: ServiceCategory,
) -> ProviderService:
    """Create a test provider service."""
    now = datetime.now(tz=timezone.utc)
    svc = ProviderService(
        id=uuid.uuid4(),
        provider_id=provider.id,
        industry_category_id=category.industry_category_id,
        service_category_id=category.id,
        pricing_type="negotiable",
        is_active=True,
        verification_status="approved",
        created_at=now,
        updated_at=now,
    )
    db.add(svc)
    await db.flush()
    return svc


async def create_vehicle(
    db: AsyncSession,
    provider: Provider,
    *,
    vehicle_type: str = "xe_4_cho",
    service_id: uuid.UUID | None = None,
) -> ProviderVehicle:
    """Create a test vehicle."""
    vehicle = ProviderVehicle(
        id=uuid.uuid4(),
        provider_id=provider.id,
        service_id=service_id,
        vehicle_type=vehicle_type,
        vehicle_brand="Toyota",
        vehicle_model="Vios",
        year_of_manufacture=2022,
        license_plate="51A-12345",
        seat_count=4,
        status="active",
        created_at=datetime.now(tz=timezone.utc),
        updated_at=datetime.now(tz=timezone.utc),
    )
    db.add(vehicle)
    await db.flush()
    return vehicle


async def create_route(
    db: AsyncSession,
    svc: ProviderService,
    *,
    from_province: str = "Hà Nội",
    to_province: str = "Hồ Chí Minh",
    price: float = 250000,
) -> ServiceRoute:
    """Create a test service route."""
    route = ServiceRoute(
        id=uuid.uuid4(),
        provider_service_id=svc.id,
        from_province=from_province,
        to_province=to_province,
        price=price,
        is_active=True,
        created_at=datetime.now(tz=timezone.utc),
        updated_at=datetime.now(tz=timezone.utc),
    )
    db.add(route)
    await db.flush()
    return route


def make_provider_token(user: User) -> str:
    """Generate a JWT access token for a provider user."""
    return create_access_token(str(user.id), ["provider_owner"])


def make_admin_token(user: User) -> str:
    """Generate a JWT access token for an admin user."""
    return create_access_token(str(user.id), ["admin"])


def auth_headers(token: str) -> dict:
    """Return Bearer auth headers."""
    return {"Authorization": f"Bearer {token}"}
