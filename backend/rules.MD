# Cursor Rules for Sàn Dịch Vụ API - FastAPI Project

## Project Overview

REST API được xây dựng với **FastAPI + Python**, sử dụng kiến trúc phân lớp. Dự án dùng Python 3.12+, SQLAlchemy 2.x (async), PostgreSQL, Pydantic v2.

**Tech Stack:**
- **Framework**: FastAPI 0.115+
- **ORM**: SQLAlchemy 2.x (async via `asyncio`)
- **Database**: PostgreSQL (driver: `psycopg[binary]`)
- **Migrations**: Alembic
- **Validation**: Pydantic v2
- **Auth**: JWT (python-jose), OTP + phone-based auth, passlib[bcrypt]
- **Linter**: ruff
- **Type Checker**: mypy (strict)
- **Tests**: pytest + pytest-asyncio

---

## Architecture Principles

### Layered Architecture

```
backend/
├── app/
│   ├── main.py                  # FastAPI app factory, middleware, lifespan
│   ├── api/
│   │   ├── deps.py              # Shared dependencies (auth, DB session)
│   │   └── v1/                  # Versioned routers (presentation layer)
│   │       ├── router.py        # Main router aggregator
│   │       ├── auth.py          # Auth endpoints
│   │       ├── customer.py      # Customer endpoints
│   │       ├── provider.py      # Provider endpoints
│   │       └── admin/           # Admin-only endpoints
│   ├── core/
│   │   ├── config.py            # Settings via pydantic-settings
│   │   ├── security.py          # JWT, OTP, password utilities
│   │   └── constants.py         # App-wide constants (enums, literals)
│   ├── db/
│   │   ├── base.py              # Declarative Base
│   │   └── session.py           # Async engine, session factory, get_db
│   ├── models/                  # SQLAlchemy ORM models (persistence layer)
│   ├── schemas/                 # Pydantic models — request/response shapes
│   └── services/                # Business logic (optional service layer)
├── alembic/                     # Database migrations
└── requirements.txt
```

**Layer Responsibilities:**
- **`models/`**: SQLAlchemy ORM — maps to database tables. No business logic.
- **`schemas/`**: Pydantic models — validates requests, serialises responses. No DB imports.
- **`api/v1/`**: FastAPI routers — HTTP concerns only. Calls DB/services directly (or via service layer for complex logic).
- **`services/`**: Business logic that is too complex for a single router function. Use when:
  - Logic is reused across multiple routers.
  - A single operation involves > 2-3 DB queries / external calls.
  - Complex orchestration (e.g., register user → send OTP → create profile atomically).
  - If a router function exceeds ~40 lines, extract to a service function.
- **`core/`**: Configuration, security helpers, constants.
- **`db/`**: Engine, session factory, `get_db` dependency.

**CRITICAL RULES:**
- Never import SQLAlchemy models inside Pydantic schemas.
- Never put business logic inside Pydantic schemas.
- Never import `app.api` inside `app.models` or `app.schemas`.
- All database I/O must be `async` — use `await db.execute(...)`, `await db.get(...)`, never synchronous SQLAlchemy.

---

## Code Quality Standards

### 1. Docstrings (REQUIRED)

All public functions and router endpoints MUST have docstrings. Use Google-style.
Include: description, `Args:`, `Returns:`, `Raises:` where applicable.
Explain **what** and **why**, not **how** — code explains how.

**Router endpoint:**
```python
@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(body: RegisterRequest, db: AsyncSession = Depends(get_db)) -> AuthResponse:
    """Register a new user account via phone number.

    Args:
        body: Registration payload (see RegisterRequest schema for field details).
        db: Async database session injected by FastAPI.

    Returns:
        AuthResponse containing access_token and refresh_token.

    Raises:
        HTTPException 400: When OTP verification token is invalid.
        HTTPException 409: When phone number is already registered.
    """
```

**Helper / service function:**
```python
async def _verify_otp_for_phone(
    db: AsyncSession,
    phone: str,
    otp_code: str,
    otp_session_id: uuid.UUID,
) -> None:
    """Validate an OTP code against the stored OTP session.

    Increments the attempt counter on each call. Marks the session as used
    on success so it cannot be replayed.

    Args:
        db: Async database session.
        phone: The phone number the OTP was issued to.
        otp_code: The plain-text OTP entered by the user.
        otp_session_id: UUID of the OtpSession record.

    Raises:
        HTTPException 400: When session is not found, expired, already used,
            attempts exceeded, or OTP code is wrong.
    """
```

**Pydantic schema class:**
```python
class RegisterRequest(BaseModel):
    """Payload for phone-based user registration.

    Either otp_verification_token (preferred) or the combination of
    otp_code + otp_session_id must be supplied.
    """
    phone: str
    otp_verification_token: str | None = None
    otp_code: str | None = None
    otp_session_id: uuid.UUID | None = None
```

**Field-level schema documentation** — describe each field with `Field(description=...)`:
```python
class CreateProviderRequest(BaseModel):
    """Request body for registering a new service provider."""

    name: str = Field(min_length=2, max_length=255, description="Provider display name")
    phone: str = Field(min_length=8, max_length=20, description="Contact phone number")
    address: str | None = Field(default=None, max_length=500, description="Physical address")
    category_id: int = Field(gt=0, description="ID of the service category")
```

#### Inline Comments
- Add inline comments for complex business logic, security decisions, or non-obvious workarounds.
- Explain **why**, not **what**.
- Do not leave commented-out code — delete it or open a ticket.

---

### 2. Logging Standards

```python
import logging
logger = logging.getLogger(__name__)
```

Use Python standard `logging`. **NEVER use `print()`**.

Log levels:
- `logger.info()`: Normal operations, important state changes.
- `logger.warning()`: Unexpected but recoverable situations.
- `logger.error()`: Errors preventing an operation from completing.
- `logger.debug()`: Detailed debug info (development only).
- `logger.exception()`: Inside `except` blocks - logs message + full traceback automatically.

#### Strategic Logging (Log Only When Necessary)

**CRITICAL: Log enough for debugging and auditing, but avoid log noise that impacts performance.**

**DO log:**
- Critical write operations: user registration, login, OTP send/verify, provider create/update/delete, admin actions.
- Authentication and authorisation failures.
- Unexpected exceptions with context (user ID, entity ID, operation).
- External API calls (AI service, third-party) with latency when notable.
- State changes: status transitions, verification approvals/rejections, document reviews.
- Phase 6 Transport: vehicle CRUD, route CRUD, availability block/unblock, schedule changes, document uploads.

**DO NOT log:**
- Simple reads (GET by ID, list queries) - no value, just noise.
- Every iteration of a loop.
- Pydantic validation failures (FastAPI + 422 handles these).
- Successful trivial operations (e.g., "session opened", "query returned N rows").
- Internal helper methods or private utility functions.

#### Log Message Format

**CRITICAL: Log messages MUST be plain text - no icons, emojis, or special characters (no em-dashes, arrows, etc.).**

Use `[PREFIX]` tags for easy log filtering. Standard prefixes:

| Prefix | Module |
|--------|--------|
| `[AUTH]` | Authentication, login, registration, OTP |
| `[OTP]` | OTP send/verify operations |
| `[PROVIDER]` | Provider profile, documents, services |
| `[CUSTOMER]` | Customer search, provider lookup |
| `[VEHICLE]` | Phase 6 - vehicle CRUD, status changes |
| `[ROUTE]` | Phase 6 - route CRUD, schedule management |
| `[TRANSPORT]` | Phase 6 - general transport operations |
| `[BOOKING]` | Phase 7 - booking lifecycle, status transitions |
| `[PAYMENT]` | Phase 8 - payment transactions, wallet operations |
| `[REVIEW]` | Phase 9 - rating/review create, visibility toggle |
| `[NOTIFICATION]` | Phase 9 - notification create, broadcast, settings |
| `[ANALYTICS]` | Phase 9 - analytics queries, dashboard KPIs |
| `[ADMIN]` | Admin panel operations |
| `[SECURITY]` | Ownership violations, auth failures |
| `[AI]` | AI service calls |
| `[DB]` | Database errors, transaction failures |

#### Log Message Examples

```python
# GOOD - critical operation entry + exit
logger.info("[PROVIDER] Creating provider - user_id=%s name=%s", current_user.id, body.name)
# ... operation ...
logger.info("[PROVIDER] Provider created - provider_id=%s", provider.id)

# GOOD - simple read: no logging needed
async def get_provider(provider_id: uuid.UUID, db: AsyncSession) -> Provider | None:
    return await db.get(Provider, provider_id)

# GOOD - error log with context before raising
logger.warning("[AUTH] OTP session expired - session_id=%s phone=%s", otp_session_id, phone[:4] + "***")
raise HTTPException(status_code=400, detail="OTP expired")

# GOOD - state change logging
logger.info("[VEHICLE] Status change - vehicle_id=%s old=%s new=%s", vehicle.id, old_status, new_status)

# GOOD - admin audit logging
logger.info("[ADMIN] Provider status changed - provider_id=%s %s->%s by admin=%s",
            provider_id, old_status, new_status, admin_user.id)

# GOOD - error with exception context
logger.exception("[DB] Transaction failed during provider create")

# BAD - never log passwords, tokens, OTP codes, full phone numbers
logger.info("OTP=%s token=%s password=%s", otp_code, jwt_token, password)

# BAD - logging simple reads (noise)
logger.info("Fetching user by ID: %s", user_id)  # unnecessary

# BAD - using emojis or special characters
logger.info("[AUTH] Login success ✅ - user_id=%s", user_id)  # no emojis!
```

#### Sensitive Data Protection - NEVER Log

**CRITICAL: Never log sensitive information:**
- **Passwords**: Never log passwords (plain or hashed) or password-related operations
- **Tokens**: Never log JWT tokens, refresh tokens, API keys, session tokens
- **OTP codes**: Never log actual OTP values in production
- **Full phone numbers**: Use `phone[:4] + "***"` if needed
- **Personal information**: Never log full addresses, ID numbers in plain text

**Safe to log:**
- User IDs, entity IDs (non-sensitive identifiers)
- Operation names, status codes, timestamps
- Error messages (without sensitive context)
- Request paths, HTTP methods

#### Error Handling Logging

**ALWAYS log errors with context before throwing:**

```python
# In except blocks - use logger.exception() for full traceback
try:
    await db.commit()
except Exception:
    await db.rollback()
    logger.exception("[PROVIDER] Transaction failed during create - user_id=%s", current_user.id)
    raise HTTPException(status_code=500, detail="Internal server error")

# For expected failures - use logger.warning()
if not user or not verify_password(payload.password, user.password_hash):
    logger.warning("[AUTH] Password login failed - phone=%s", phone[:4] + "***")
    raise HTTPException(status_code=401, detail="Invalid credentials")
```

#### Phase 6 Transport Logging Guidelines

Transport modules (vehicles, routes, schedules, documents) follow the same strategic approach:

```python
# Vehicle operations
logger.info("[VEHICLE] Creating vehicle - provider_id=%s type=%s", provider.id, body.vehicle_type)
logger.info("[VEHICLE] Vehicle created - vehicle_id=%s", vehicle.id)
logger.info("[VEHICLE] Status change - vehicle_id=%s old=%s new=%s", vehicle.id, old, new)
logger.info("[VEHICLE] Deleting vehicle - vehicle_id=%s provider_id=%s", vehicle.id, provider.id)

# Route operations
logger.info("[ROUTE] Creating route - provider_id=%s from=%s to=%s", provider.id, body.origin, body.destination)
logger.info("[ROUTE] Route created - route_id=%s", route.id)

# Admin transport operations
logger.info("[ADMIN] Vehicle document reviewed - doc_id=%s status=%s by admin=%s", doc.id, status, admin.id)
```

---


### 3. Error Handling

Use `HTTPException` for all API errors:

```python
from fastapi import HTTPException, status

raise HTTPException(
    status_code=status.HTTP_404_NOT_FOUND,
    detail="User not found",
)
```

**Standard Status Codes:**
| Code | When to use |
|------|-------------|
| 200 | Successful GET, PUT, PATCH |
| 201 | Successful POST creating resource |
| 204 | Successful DELETE |
| 400 | Invalid input, bad OTP, business rule violation |
| 401 | Missing or invalid JWT token |
| 403 | Authenticated but insufficient permissions / ownership mismatch |
| 404 | Resource does not exist |
| 409 | Duplicate phone/email, unique constraint violated |
| 422 | Pydantic validation error (automatic) |
| 500 | Unexpected server errors |

**Error helper pattern — extract to `deps.py` or inline:**
```python
async def get_user_or_404(db: AsyncSession, user_id: uuid.UUID) -> User:
    """Fetch user by ID or raise 404."""
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user
```

**Always log before re-raising when there is context worth preserving:**
```python
except JWTError as exc:
    logger.warning("[AUTH] JWT decode failed: %s", exc)
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
```

**Never expose internal details to clients:**
```python
# BAD — leaks implementation detail
raise HTTPException(status_code=500, detail=str(exc))

# GOOD — generic client message, full detail in log
logger.exception("[DB] Unexpected database error - operation=create_user")
raise HTTPException(status_code=500, detail="Internal server error")
```

---

### 4. Validation

#### 4.1 Pydantic Schema Validation

- Use `Field(...)` for required fields with constraints (`min_length`, `gt`, `pattern`, etc.).
- Use `Field(default=None)` for optional fields.
- Use `@field_validator` for single-field normalisation / transformation.
- Use `@model_validator(mode="after")` for cross-field validation.

```python
class OtpSendRequest(BaseModel):
    phone: str = Field(min_length=8, max_length=20)

    @field_validator("phone")
    @classmethod
    def normalise_phone(cls, v: str) -> str:
        """Normalise phone: keep digits and leading +."""
        cleaned = "".join(ch for ch in v if ch.isdigit() or ch == "+")
        if len(cleaned) < 8:
            raise ValueError("Invalid phone number")
        return cleaned
```

#### 4.2 Business Rule Validation (REQUIRED)

Perform in the router function (or service layer) **after** Pydantic validation passes.

**1. Uniqueness Validation — MUST validate before create/update:**
```python
async def create_user(body: RegisterRequest, db: AsyncSession) -> User:
    # Validate phone uniqueness before inserting
    existing = (await db.execute(
        select(User).where(User.phone == body.phone).limit(1)
    )).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Phone already registered")
    # proceed with insert
```

**2. Foreign Key / Reference Validation — MUST check referenced entities exist:**
```python
async def create_provider_service(body: CreateServiceRequest, db: AsyncSession) -> ProviderService:
    # Validate provider exists and belongs to current user
    provider = await db.get(Provider, body.provider_id)
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")

    # Validate taxonomy/category exists
    taxonomy = await db.get(Taxonomy, body.taxonomy_id)
    if not taxonomy:
        raise HTTPException(status_code=400, detail="Invalid category")
```

**3. Master Data Validation — validate status/type/category is active and valid:**
```python
if taxonomy.status != "active":
    raise HTTPException(status_code=400, detail="Category is not active")
```

**4. Data Integrity Validation — validate logical constraints:**
```python
if body.end_date and body.start_date and body.end_date <= body.start_date:
    raise HTTPException(status_code=400, detail="end_date must be after start_date")

if body.price is not None and body.price < 0:
    raise HTTPException(status_code=400, detail="Price must be non-negative")
```

**5. Ownership / Authorisation Validation (REQUIRED):**
```python
async def update_provider(
    provider_id: uuid.UUID,
    body: ProviderUpdateRequest,
    current_user: User,
    db: AsyncSession,
) -> Provider:
    provider = await db.get(Provider, provider_id)
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")

    # Check ownership — admin can bypass
    is_admin = await _has_role(db, current_user.id, "admin")
    if not is_admin and provider.owner_user_id != current_user.id:
        logger.warning(
            "[PROVIDER] Ownership check failed - user_id=%s provider_id=%s",
            current_user.id, provider_id,
        )
        raise HTTPException(status_code=403, detail="Access forbidden")
```

**Validation Order (always follow this sequence):**
1. **Pydantic** — format, type, required fields (automatic).
2. **Uniqueness** — phone, email, unique codes.
3. **FK / Reference existence** — provider_id, category_id, etc.
4. **Master data validity** — active status, valid ranges.
5. **Ownership / authorisation** — user owns the resource.
6. **Data integrity** — logical constraints (date ranges, numeric rules).
7. **Database operation** — insert / update / delete.

**Validation Checklist:**
- [ ] Uniqueness constraints validated (phone, email, unique fields) before create/update
- [ ] Foreign key references validated (all relationships) before operations
- [ ] Master data validated (categories, statuses, types) if applicable
- [ ] Data integrity validated (date ranges, numeric ranges, business rules)
- [ ] Ownership validated — user can only modify their own resources
- [ ] Admin role bypasses ownership check
- [ ] HTTPException thrown with appropriate status code and clear message
- [ ] Validation errors logged when they indicate suspicious activity

---

### 5. FastAPI Route Standards

**Router Organisation:**
```python
router = APIRouter(prefix="/providers", tags=["providers"])
```

- Each module gets its own `APIRouter`.
- Register in `app/api/v1/router.py`.
- Use `tags=` for Swagger grouping.
- Use `prefix=` at router level — do NOT repeat it on each endpoint.

**Endpoint definition (full example):**
```python
@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    summary="Đăng ký nhà cung cấp dịch vụ",
    description="Tạo hồ sơ nhà cung cấp mới. Người dùng phải xác thực trước.",
    response_model=ProviderResponse,
    responses={
        400: {"description": "Dữ liệu không hợp lệ"},
        409: {"description": "Nhà cung cấp đã tồn tại"},
    },
)
async def create_provider(
    body: CreateProviderRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ProviderResponse:
    """Create a new service provider profile for the authenticated user.

    Args:
        body: Provider creation payload (see CreateProviderRequest for field details).
        current_user: Authenticated user from JWT token.
        db: Async database session.

    Returns:
        ProviderResponse with the created provider data.

    Raises:
        HTTPException 409: When user already has a provider profile.
        HTTPException 400: When category_id does not exist.
    """
```

**HTTP Status Codes:**
- `200 OK`: GET, PUT, PATCH
- `201 Created`: POST
- `204 No Content`: DELETE
- `400 Bad Request`: Input/business rule errors
- `401 Unauthorized`: Missing/invalid token
- `403 Forbidden`: Insufficient permissions
- `404 Not Found`: Resource not found
- `409 Conflict`: Duplicate/conflict
- `422 Unprocessable Entity`: Pydantic validation (automatic)

**Response Models (REQUIRED):**
- Always declare `response_model=` on endpoints that return data.
- Never return raw SQLAlchemy ORM objects — always map to Pydantic schema.

```python
# BAD — exposes ORM internals
return user

# GOOD — explicit mapping
return UserItem(id=user.id, phone=user.phone, full_name=user.full_name, status=user.status)

# GOOD — using model_validate with ORM model (requires model_config with from_attributes=True)
return UserItem.model_validate(user)
```

**Dependency Injection — shared logic in `app/api/deps.py`:**
```python
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Extract and validate the current user from JWT bearer token."""
    ...

def check_user_role(role_code: str):
    """Factory for role-based access control dependencies."""
    async def role_checker(current_user: User = Depends(get_current_user), ...) -> User:
        ...
    return role_checker
```

---

### 6. SQLAlchemy Async Patterns

**Always use async — never call synchronous SQLAlchemy in async context:**
```python
# GOOD
user = await db.get(User, user_id)
result = await db.execute(select(User).where(User.phone == phone))
users = result.scalars().all()
await db.commit()
await db.refresh(user)

# BAD — blocks the event loop
result = db.execute(select(User))
```

**Avoid N+1 Query Problem:**
```python
# BAD — N+1: one extra query per user
users = (await db.execute(select(User))).scalars().all()
for user in users:
    roles = await db.execute(select(UserRole).where(UserRole.user_id == user.id))  # N queries!

# GOOD — single query with selectinload
stmt = select(User).options(selectinload(User.roles))
users = (await db.execute(stmt)).scalars().all()
# Access user.roles with no further queries

# GOOD — single query with In_() for multiple IDs
from sqlalchemy import select
user_ids = [u.id for u in users]
roles = (await db.execute(
    select(UserRole).where(UserRole.user_id.in_(user_ids))
)).scalars().all()
```

**Query Best Practices:**
- Use `select()` + `where()` — never `session.query()` (legacy SQLAlchemy 1.x).
- Use `db.get(Model, pk)` for single primary-key lookups (hits identity map).
- Use `.limit(1)` with `scalar_one_or_none()` for existence / uniqueness checks.
- Use `.offset()` + `.limit()` for pagination — never fetch entire tables.
- Select only needed columns for large tables: `select(User.id, User.phone)`.
- Use `In_()` for multi-ID queries instead of looping `db.get()`.

**Transactions — when to use:**

Use `await db.commit()` after every single write. For **multi-step atomicity**:
```python
# GOOD — atomic multi-step write
try:
    db.add(provider)
    await db.flush()                   # gets provider.id without committing
    db.add(ProviderService(provider_id=provider.id, ...))
    await db.commit()
    await db.refresh(provider)
except Exception:
    await db.rollback()
    logger.exception("[PROVIDER] Transaction failed during create")
    raise HTTPException(status_code=500, detail="Internal server error")
```

**DO NOT use transactions for:**
- Read-only operations (SELECT only)
- Single INSERT/UPDATE/DELETE (SQLAlchemy auto-wraps in transaction)

---

### 7. Security Standards

#### 7.1 Authentication — JWT
- Access token: short-lived (15 min), payload: `sub` (user_id), `roles`, `typ: "access"`.
- Refresh token: long-lived (30 days), stored in `refresh_tokens` table, single-use with rotation.
- Never put sensitive data (passwords, phone numbers) in JWT payload.
- Always validate `typ` claim after decoding to prevent token type confusion.

```python
# GOOD — validate typ claim
payload = safe_decode(token, "access")
if not payload or payload.get("typ") != "access":
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid access token")
```

#### 7.2 Passwords
- Hash with `passlib[bcrypt]` (CryptContext) — default rounds >= 12.
- Use `pwd_context.verify(plain, hashed)` — never compare manually.
- Never log, return, or expose password hashes.

#### 7.3 OTP Security
- Hash OTP codes with SHA-256 + pepper (app secret) before storing — never plain-text.
- OTP sessions: TTL enforced, attempt counter enforced, `is_used` flag single-use.
- Mark `is_used = True` **immediately** and commit before returning success — prevents replay.

#### 7.4 Resource Ownership Validation (REQUIRED)

Always validate that the authenticated user owns the resource before GET / UPDATE / DELETE.

```python
async def update_provider(
    provider_id: uuid.UUID,
    body: ProviderUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ProviderResponse:
    """Update provider profile — only owner or admin can update."""
    provider = await db.get(Provider, provider_id)
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")

    # Admin can access all; others must own the resource
    is_admin = await _has_role(db, current_user.id, "admin")
    if not is_admin and provider.owner_user_id != current_user.id:
        logger.warning(
            "[SECURITY] Ownership violation - user_id=%s provider_id=%s",
            current_user.id, provider_id,
        )
        raise HTTPException(status_code=403, detail="Access forbidden")

    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(provider, field, value)
    await db.commit()
    await db.refresh(provider)
    return ProviderResponse.model_validate(provider)
```

**When to validate ownership:**
- GET: validate before returning resource data
- UPDATE: validate before modifying
- DELETE: validate before deleting
- LIST: filter by owner automatically (unless admin)

#### 7.5 Input Sanitisation
- All inputs validated by Pydantic before reaching router logic.
- Use ORM queries only — SQLAlchemy parameterises automatically.
- Never interpolate user input into raw SQL strings.

```python
# DANGEROUS — SQL injection
await db.execute(text(f"SELECT * FROM users WHERE phone = '{phone}'"))

# SAFE — parameterised
await db.execute(text("SELECT * FROM users WHERE phone = :phone"), {"phone": phone})

# SAFEST — use ORM
await db.execute(select(User).where(User.phone == phone))
```

---

### 8. Configuration & Environment

```python
from app.core.config import get_settings
settings = get_settings()
```

- All secrets and config from `.env` via `pydantic-settings`.
- `@lru_cache` on `get_settings()` — instantiated once per process.
- Never hardcode secrets, database URLs, or credentials in source code.
- Add new config by extending the `Settings` class in `app/core/config.py` with a `validation_alias` matching the env var name.

---

### 9. Database Migrations (Alembic)

- All schema changes **must** go through Alembic migrations in `alembic/versions/`.
- Name: `{revision}_{short_description}.py` — e.g., `002_add_provider_status.py`.
- Always implement both `upgrade()` and `downgrade()`.
- Never edit migration files that have been applied to any environment.
- Test every migration round-trip locally:
  ```bash
  alembic upgrade head
  alembic downgrade -1
  alembic upgrade head
  ```

---

### 10. Python & Type Safety Standards

**Type Annotations (REQUIRED for all function signatures):**
- Use `from __future__ import annotations` at the top of every file.
- Never use `Any` — use `object` or proper generics and narrow with type guards.
- Use `X | None` (Python 3.10+) instead of `Optional[X]`.
- Use `list[X]`, `dict[K, V]`, `tuple[A, B]` (lowercase, Python 3.9+).

```python
# GOOD
async def create_user(phone: str, full_name: str | None = None) -> User: ...

# BAD — no annotations
async def create_user(phone, full_name=None): ...
```

**Null / None Safety:**
```python
# Always handle None explicitly — never assume a query returns a row
user = await db.get(User, user_id)
if not user:
    raise HTTPException(status_code=404, detail="User not found")
# Below this line, `user` is guaranteed non-None
```

**Async Best Practices:**
- `await` every async call — a missing `await` is a silent bug.
- Use `asyncio.gather()` for independent parallel tasks.
- Never call blocking I/O (`requests.get`, `time.sleep`, file reads) inside async functions — use async alternatives or `run_in_executor`.

```python
# GOOD — run independent queries in parallel
user, provider = await asyncio.gather(
    db.get(User, user_id),
    db.get(Provider, provider_id),
)
```

**Constants and Enums:**
```python
from enum import StrEnum

class UserStatus(StrEnum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    DELETED = "deleted"

class RoleCode(StrEnum):
    ADMIN = "admin"
    PROVIDER = "provider"
    CUSTOMER = "customer"
```

Define all constants in `app/core/constants.py` — never use magic strings/numbers.

**Imports Order (enforced by ruff):**
1. `from __future__ import annotations`
2. Standard library (`uuid`, `datetime`, `logging`, `asyncio`, ...)
3. Third-party (`fastapi`, `sqlalchemy`, `pydantic`, `jose`, ...)
4. Internal (`app.core`, `app.db`, `app.models`, `app.schemas`, `app.api.deps`)

---

### 11. Code Duplication Prevention (DRY)

**1. Extract common DB helpers into `deps.py` or a shared module:**
```python
# app/api/deps.py
async def get_user_or_404(db: AsyncSession, user_id: uuid.UUID) -> User:
    """Fetch user by ID or raise HTTP 404."""
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

async def get_provider_or_404(db: AsyncSession, provider_id: uuid.UUID) -> Provider:
    """Fetch provider by ID or raise HTTP 404."""
    provider = await db.get(Provider, provider_id)
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")
    return provider
```

**2. Extract pagination helper:**
```python
def apply_pagination(stmt: Select, page: int, page_size: int) -> Select:
    """Apply LIMIT/OFFSET pagination to a SQLAlchemy select statement."""
    return stmt.offset((page - 1) * page_size).limit(page_size)
```

**3. Extract ownership check helper:**
```python
async def assert_owner_or_admin(
    db: AsyncSession,
    owner_user_id: uuid.UUID,
    current_user: User,
    resource_name: str = "resource",
) -> None:
    """Raise 403 if current_user is not the owner and not an admin."""
    is_admin = await _has_role(db, current_user.id, RoleCode.ADMIN)
    if not is_admin and owner_user_id != current_user.id:
        raise HTTPException(status_code=403, detail=f"Access to {resource_name} forbidden")
```

**4. Extract constants — never use magic values:**
```python
# app/core/constants.py
DEFAULT_PAGE_SIZE = 10
MAX_PAGE_SIZE = 100
OTP_PURPOSE_LOGIN = "login"
OTP_PURPOSE_REGISTER = "register"
```

**5. Avoid copy-pasting validation logic** across routers — extract into `deps.py` or `services/`.

---

### 12. Performance Considerations

#### Avoid N+1 Queries (CRITICAL)
Use `selectinload` or `joinedload` for related data — never query in a loop:
```python
# BAD — N queries for N users
for user in users:
    profile = await db.get(UserProfile, user.id)

# GOOD — one query
stmt = select(User).options(selectinload(User.profile)).where(...)
users = (await db.execute(stmt)).scalars().all()
```

#### Pagination (REQUIRED for all list endpoints)
Never load entire tables. Always use `.limit()` + `.offset()`:
```python
base = select(Provider).where(Provider.status == "active").order_by(Provider.created_at.desc())
total = (await db.execute(select(func.count()).select_from(base.subquery()))).scalar_one()
rows = (await db.execute(base.offset((page - 1) * page_size).limit(page_size))).scalars().all()
```

#### Select Only Needed Columns
For large tables or high-traffic endpoints, avoid `SELECT *`:
```python
stmt = select(User.id, User.phone, User.full_name, User.status)
rows = (await db.execute(stmt)).all()
```

#### Parallel Async Queries
Use `asyncio.gather()` for independent lookups:
```python
user, categories = await asyncio.gather(
    db.get(User, user_id),
    db.execute(select(Taxonomy).where(Taxonomy.status == "active")),
)
```

**Dashboard / Analytics endpoints:** When computing multiple independent KPIs,
always use `asyncio.gather()` to run all queries in parallel — never sequentially.

#### Batch Operations (REQUIRED for bulk writes)
When processing multiple records (e.g., broadcast notifications, bulk status updates):
- **Batch SELECT** settings/permissions in one query, then filter in-memory.
- **Avoid N+1 loops** — never call a helper function per-item that issues its own SELECT.
- Use `db.add_all()` or loop `db.add()` then flush once — not commit per item.

```python
# BAD — N+1: 1 SELECT + 1 INSERT per user
for user_id in user_ids:
    setting = await check_setting(db, user_id)  # N queries!
    if setting:
        db.add(Notification(...))

# GOOD — batch fetch, filter in memory, bulk insert
disabled = set((await db.execute(
    select(NotificationSetting.user_id).where(
        NotificationSetting.user_id.in_(user_ids),
        NotificationSetting.is_enabled.is_(False),
    )
)).scalars().all())
eligible = [uid for uid in user_ids if uid not in disabled]
for uid in eligible:
    db.add(Notification(user_id=uid, ...))
await db.commit()  # single commit at the end
```

#### Code Complexity Limits
- Keep functions under 50 lines — extract private helpers if longer.
- Avoid deeply nested conditionals (> 3 levels) — use early returns / guard clauses.
- One function should do one thing.

#### PostgreSQL UPSERT (INSERT ON CONFLICT) — High-Frequency Writes
For **write-heavy endpoints** (driver location heartbeat, session toggle, status updates):
- Use `INSERT ... ON CONFLICT DO UPDATE ... RETURNING` — **1 round-trip instead of 2**.
- Only applicable when the conflict target is a PRIMARY KEY or UNIQUE constraint.
- For tables without a unique key on the conflict column, use `UPDATE RETURNING` with INSERT fallback.

```python
# GOOD — 1 round-trip (PK upsert for driver_locations)
from sqlalchemy.dialects.postgresql import insert as pg_insert

stmt = (
    pg_insert(DriverLocation)
    .values(provider_id=provider.id, latitude=lat, longitude=lng, updated_at=func.now())
    .on_conflict_do_update(
        index_elements=["provider_id"],  # must be PK or UNIQUE
        set_={"latitude": lat, "longitude": lng, "updated_at": func.now()},
    )
    .returning(DriverLocation)
)
row = (await db.execute(stmt)).scalars().one()
await db.commit()

# ACCEPTABLE — 2 round-trips when no unique constraint (UPDATE + INSERT fallback)
result = (await db.execute(
    sa_update(MyModel).where(...).values(...).returning(MyModel)
)).scalars().first()
if not result:
    db.add(MyModel(...))
    await db.flush()
await db.commit()
```

#### Connection Pool — REQUIRED Configuration for Production
Never leave connection pool at SQLAlchemy defaults (pool_size=5).
Configure via `DB_POOL_SIZE`, `DB_MAX_OVERFLOW`, etc. environment variables.

| Deployment | pool_size | max_overflow | Notes |
|------------|-----------|--------------|-------|
| Dev | 5 | 10 | Default env |
| Staging | 10 | 20 | Mid-load test |
| Production (4 workers) | 20 | 40 | ~1M users |
| Production (8 workers) | 30 | 60 | High traffic |

Rule of thumb: `pool_size ≈ workers × 5`, `max_overflow ≈ pool_size × 2`.

#### Database Index Checklist (REQUIRED per table)
Every table that is queried in production **MUST** have indexes on:
- All FK columns used in WHERE clauses
- Status/type columns used in filters (especially partial indexes for low-cardinality values)
- Timestamp columns used in ORDER BY or range filters (DESC indexes)
- Composite indexes for the most common (col1 + col2) WHERE patterns

Partial indexes for categorical filters:
```sql
-- Fast: bookings WHERE status = 'pending' (< 1% of rows)
CREATE INDEX ix_bookings_pending ON bookings (requested_at DESC)
WHERE status = 'pending';
```

#### PostGIS Spatial Queries
- Use `GEOGRAPHY(POINT, 4326)` type (not Geometry) — distance in meters, no projection needed.
- `ST_MakePoint` takes **(longitude, latitude)** — opposite of Google Maps (lat, lng).
- Always use `func.ST_DWithin()` for radius queries — it utilizes the GIST index.
- Keep original Numeric lat/lng columns for API response; geography is for indexing only.
- NEVER do Haversine math in Python (Python-side distance calculation causes N+1, no index) — always use PostgreSQL with PostGIS.

```sql
-- GOOD: 5km radius using GIST index
SELECT * FROM bookings
WHERE ST_DWithin(pickup_point, ST_SetSRID(ST_MakePoint(106.6, 10.8), 4326)::geography, 5000);
```


---

### 13. Pagination Standards

All list endpoints MUST support pagination with consistent parameter names:

```python
@router.get("", response_model=dict)
async def list_providers(
    page: int = Query(default=1, ge=1, description="Trang hiện tại (bắt đầu từ 1)"),
    page_size: int = Query(default=10, ge=1, le=100, description="Số item mỗi trang"),
    status: str | None = Query(default=None, description="Lọc theo trạng thái"),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """List providers with pagination and optional filtering."""
    base = select(Provider).order_by(Provider.created_at.desc())
    if status:
        base = base.where(Provider.status == status)

    total = (await db.execute(select(func.count()).select_from(base.subquery()))).scalar_one()
    rows = (await db.execute(apply_pagination(base, page, page_size))).scalars().all()

    return {
        "items": [ProviderItem.model_validate(p) for p in rows],
        "page": page,
        "page_size": page_size,
        "total": total,
    }
```

**Standard Response Format (MUST follow):**
```json
{
  "items": [...],
  "page": 1,
  "page_size": 10,
  "total": 42
}
```

Consistent field names: `items`, `page`, `page_size`, `total`. Do NOT use `data`, `results`, `count`, `limit`, `offset`.

#### Sorting / Ordering

For list endpoints that need sorting, add `order_by` and `order` query params consistently:

```python
from typing import Literal

@router.get("", response_model=dict)
async def list_providers(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    order_by: str = Query(default="created_at", description="Field to sort by"),
    order: Literal["asc", "desc"] = Query(default="desc", description="Sort direction"),
    db: AsyncSession = Depends(get_db),
) -> dict:
    ...
```

Allowed `order_by` values MUST be validated against a whitelist to prevent SQL injection:

```python
ALLOWED_SORT_FIELDS = {"created_at", "name", "status"}

if order_by not in ALLOWED_SORT_FIELDS:
    raise HTTPException(status_code=400, detail=f"Invalid order_by. Allowed: {ALLOWED_SORT_FIELDS}")

col = getattr(Provider, order_by)
sorted_col = col.asc() if order == "asc" else col.desc()
base = select(Provider).order_by(sorted_col)
```

Consistent param names: `order_by`, `order`. Do NOT use `sort`, `sort_by`, `sort_order`, `direction`.

---

### 14. Testing Requirements

**Test structure:**
```
tests/
├── conftest.py          # Async engine, test DB, TestClient fixtures
├── api/
│   ├── test_auth.py
│   ├── test_providers.py
│   └── test_admin_users.py
└── services/
    └── test_ai_service.py
```

**Test naming:** `test_<what>_<condition>`:
- `test_register_returns_201_on_success`
- `test_register_returns_409_when_phone_already_exists`
- `test_update_provider_returns_403_when_not_owner`

```python
import pytest
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_register_success():
    """New phone number registers successfully and returns token pair."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post("/api/v1/auth/register", json={...})
    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data

@pytest.mark.asyncio
async def test_register_conflict_on_duplicate_phone():
    """Registration with an already-registered phone returns 409."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        await client.post("/api/v1/auth/register", json={...})  # first registration
        response = await client.post("/api/v1/auth/register", json={...})  # duplicate
    assert response.status_code == 409
```

- Use `pytest.mark.asyncio` for all async tests.
- Use `httpx.AsyncClient` for integration/API tests.
- Mock external I/O (AI service, SMS gateway) — never call real services in tests.
- Test both success paths and all significant error paths.

**Coverage targets:** Statements 80%, Branches 70%, Functions 75%.

---

### 15. File Naming Conventions

| Layer | Path pattern | Example |
|-------|-------------|---------|
| ORM Models | `app/models/<entity>.py` | `user.py`, `provider.py` |
| Pydantic Schemas | `app/schemas/<topic>.py` | `auth.py`, `admin.py` |
| API Routers | `app/api/v1/<topic>.py` | `auth.py`, `provider.py` |
| Admin Routers | `app/api/v1/admin/<topic>.py` | `users.py`, `posts.py` |
| Services | `app/services/<topic>_service.py` | `ai_service.py` |
| Core Utilities | `app/core/<topic>.py` | `security.py`, `config.py` |
| Migrations | `alembic/versions/<rev>_<desc>.py` | `002_add_provider_status.py` |

**Casing**: Classes `PascalCase`, functions/variables `snake_case`, constants `UPPER_SNAKE_CASE`, files `snake_case.py`.

---

### 16. Git & Commit Standards

#### Commit Messages

Follow **Conventional Commits** format:

```
<type>(<scope>): <short description>

[optional body]
[optional footer]
```

Types:
| Type | When to use |
|------|-------------|
| `feat` | New endpoint, new feature |
| `fix` | Bug fix |
| `refactor` | Code restructuring without behaviour change |
| `docs` | Documentation / docstring updates |
| `test` | Test additions or changes |
| `chore` | Dependency updates, config changes, migrations |
| `perf` | Performance improvements |
| `security` | Security fixes |

**Examples:**
```
feat(auth): add phone OTP registration endpoint
fix(provider): fix ownership check skipped on PATCH
refactor(deps): extract get_user_or_404 helper
chore(alembic): add 003_add_provider_service_table migration
security(auth): rotate refresh token on each use
```

#### Branch Naming
- `feat/<short-description>` — new features
- `fix/<short-description>` — bug fixes
- `chore/<short-description>` — maintenance

#### Pre-Commit Checks (REQUIRED)
Before creating a commit, always verify:
```bash
# Lint and format
ruff check .
ruff format .

# Type check
mypy app/

# Run tests
pytest
```

Do NOT bypass pre-commit hooks or commit with known lint/type errors.

---

## Anti-Patterns to Avoid

| # | Anti-pattern |
|---|-------------|
| 1 | Using `print()` instead of `logging` |
| 2 | Synchronous SQLAlchemy calls inside async functions |
| 3 | Returning raw ORM objects from endpoints — always map to Pydantic schema |
| 4 | Missing type annotations on function signatures |
| 5 | Using `Any` from `typing` without justification |
| 6 | N+1 queries — use `selectinload`/`joinedload`/`In_()` |
| 7 | Hardcoded secrets, database URLs, or magic strings in source code |
| 8 | Logging passwords, OTP codes, JWT tokens, or PII |
| 9 | Skipping uniqueness validation before create/update |
| 10 | Skipping FK reference validation before operations |
| 11 | Skipping ownership validation before modify/delete on user-owned resources |
| 12 | Allowing admin role bypass to be forgotten — always check role first |
| 13 | Calling blocking I/O (`requests`, `time.sleep`) inside async functions |
| 14 | Writing raw SQL with f-strings — SQL injection risk |
| 15 | Modifying already-applied Alembic migration files |
| 16 | Skipping `await db.commit()` after write operations |
| 17 | Loading entire tables without `.limit()` pagination |
| 18 | Catching exceptions silently with `except Exception: pass` |
| 19 | Redefining pagination params in every router — extract to shared helper |
| 20 | Missing `response_model=` on endpoints that return data |
| 21 | Using `session.query()` (SQLAlchemy 1.x legacy) instead of `select()` |
| 22 | Using icons or emojis in log messages — plain text only |
| 23 | Functions longer than ~50 lines — extract helpers |
| 24 | Deeply nested conditionals (> 3 levels) — use early returns |
| 25 | Putting business logic (uniqueness checks, ownership) inside Pydantic validators |
| 26 | Missing `await` on async calls — silent bug, no warning at runtime |
| 27 | Not wrapping multi-step writes in try/except with `await db.rollback()` — dirty state on failure |
| 28 | Exposing internal error details to clients in 500 responses |

---

## Code Review Checklist

Before submitting or merging any code, verify:

### Documentation
- [ ] All public functions and endpoints have Google-style docstrings (Args, Returns, Raises)
- [ ] Pydantic schema classes have a class docstring
- [ ] Schema fields use `Field(description=...)` for Swagger documentation
- [ ] Inline comments added for complex business logic or security decisions
- [ ] No dead/commented-out code left in the diff

### Logging & Error Handling
- [ ] No `print()` calls - only `logging`
- [ ] Every module has `logger = logging.getLogger(__name__)` at module level
- [ ] Critical operations (create/update/delete/auth) have appropriate log entries
- [ ] Errors are logged with context before being re-raised
- [ ] `except` blocks use `logger.exception()` for full stack traces
- [ ] No sensitive data logged (passwords, tokens, OTP codes, full phone numbers)
- [ ] Log messages are plain text (no emojis, icons, em-dashes, or special chars)
- [ ] All log messages use consistent `[PREFIX]` tags (`[AUTH]`, `[PROVIDER]`, `[VEHICLE]`, `[ADMIN]`, etc.)
- [ ] Internal errors use generic client messages - details stay in logs
- [ ] Phase 6 transport operations (vehicle/route CRUD, status changes, document reviews) have audit logs

### Validation
- [ ] Pydantic schema validates format, type, and required fields
- [ ] Uniqueness constraints validated before create/update (phone, email, unique codes)
- [ ] FK references validated before operations (provider_id, category_id, etc.)
- [ ] Master data validated where applicable (active status, valid category)
- [ ] Data integrity validated (date ranges, numeric constraints)
- [ ] Ownership validated — user can only modify their own resources
- [ ] Admin role bypasses ownership check correctly
- [ ] Correct HTTP status codes used (409 conflict, 403 forbidden, 404 not found, etc.)

### FastAPI / SQLAlchemy
- [ ] All DB calls are `await`-ed — no synchronous SQLAlchemy in async context
- [ ] Write operations followed by `await db.commit()`
- [ ] Multi-step writes wrapped in try/except with `await db.rollback()` on error
- [ ] No N+1 query problems — `selectinload`/`In_()` used for related data
- [ ] List endpoints have `.limit()` + `.offset()` pagination
- [ ] `response_model=` declared on all data-returning endpoints
- [ ] Raw ORM objects are **never** returned — always mapped to Pydantic schema
- [ ] `select()` used instead of legacy `session.query()`

### Type Safety
- [ ] All function parameters and return types annotated
- [ ] No `Any` types without justification
- [ ] `X | None` used instead of `Optional[X]`
- [ ] `from __future__ import annotations` at top of file
- [ ] None/null cases explicitly handled before attribute access

### Security
- [ ] JWT `typ` claim validated after decoding
- [ ] Passwords hashed with bcrypt — never stored or logged plain
- [ ] OTP sessions marked `is_used = True` on success and committed immediately
- [ ] Parameterised queries used — no raw SQL f-strings
- [ ] Ownership check performed for all user-owned resource mutations
- [ ] Admin bypass logic applied consistently (`is_admin` checked before ownership check)

### Performance
- [ ] No N+1 queries
- [ ] Pagination applied to all list endpoints
- [ ] `asyncio.gather()` used for independent parallel async operations
- [ ] Functions are focused and under ~50 lines
- [ ] No blocking I/O in async context

### General
- [ ] No magic strings/numbers — constants/enums used
- [ ] No duplicate logic — extracted to shared helpers
- [ ] Imports follow ruff/isort order
- [ ] New DB models have Alembic migration
- [ ] Existing migration files not modified

---

## Quick Reference

### Creating a New Router Module

Step-by-step for adding a new feature (e.g., `reviews`):

1. **Create the ORM model** — `app/models/review.py` (inherits `Base`, `Mapped[...]` columns, FK relationships, `created_at`/`updated_at`)
2. **Create Alembic migration** — `alembic revision --autogenerate -m "add_reviews_table"`, review and clean up the generated file, test round-trip (`upgrade` then `downgrade`)
3. **Create Pydantic schemas** — `app/schemas/review.py` (`ReviewItem`, `CreateReviewRequest`, `UpdateReviewRequest`) with `Field(description=...)` on every field and class docstrings
4. **Add shared helpers** (if needed) — `get_review_or_404`, ownership check helper in `app/api/deps.py`
5. **Create the router** — `app/api/v1/review.py` (or `app/api/v1/admin/reviews.py` for admin)
   - `APIRouter(prefix="/reviews", tags=["reviews"])`
   - Implement CRUD endpoints with proper `status_code=`, `response_model=`, `summary=`
   - Add auth dependencies, ownership checks, validation
6. **Register the router** — add `api_router.include_router(review_router)` in `app/api/v1/router.py`
7. **Write tests** — `tests/api/test_reviews.py` covering success paths and key error paths (404, 403, 409)
8. **Verify**:
   - `ruff check . && ruff format .`
   - `mypy app/`
   - `pytest tests/api/test_reviews.py`

---

### New Endpoint Checklist
- [ ] `APIRouter` has `prefix=` and `tags=`
- [ ] Decorator has `status_code=`, `response_model=`, `summary=`
- [ ] Function has docstring (Args, Returns, Raises)
- [ ] Auth dependency applied (`get_current_user` / `get_current_admin_user`)
- [ ] Ownership check for user-specific resources
- [ ] All DB calls `await`-ed; writes followed by `await db.commit()`
- [ ] Validation: uniqueness, FK, ownership — in that order
- [ ] Pagination applied to list endpoints
- [ ] No sensitive data logged

### New ORM Model Checklist
- [ ] Inherits from `Base` (`app.db.base`)
- [ ] `__tablename__` defined
- [ ] `Mapped[...]` annotations on all columns
- [ ] UUID PK: `server_default=text("gen_random_uuid()")`
- [ ] `created_at` / `updated_at`: `server_default=text("now()")`
- [ ] Alembic migration created

### New Pydantic Schema Checklist
- [ ] Inherits from `pydantic.BaseModel`
- [ ] All fields type-annotated
- [ ] Optional fields: `field: type | None = None`
- [ ] `Field(description=...)` on all fields for Swagger docs
- [ ] Class docstring present
- [ ] **Response schemas** that use `model_validate(orm_obj)` MUST declare `model_config`:

```python
from pydantic import BaseModel, ConfigDict, Field

class ProviderResponse(BaseModel):
    """Response schema for a provider profile."""

    model_config = ConfigDict(from_attributes=True)  # Required for model_validate(orm_obj)

    id: uuid.UUID
    name: str
    status: str
    created_at: datetime
```

Request schemas (e.g., `CreateProviderRequest`) do **not** need `from_attributes=True`.

### Common Code Patterns

**Protected endpoint with ownership check:**
```python
@router.put("/{provider_id}", response_model=ProviderResponse)
async def update_provider(
    provider_id: uuid.UUID,
    body: ProviderUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ProviderResponse:
    """Update provider profile. Owner or admin only."""
    provider = await db.get(Provider, provider_id)
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")
    await assert_owner_or_admin(db, provider.owner_user_id, current_user, "provider")

    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(provider, field, value)
    await db.commit()
    await db.refresh(provider)
    return ProviderResponse.model_validate(provider)
```

**Paginated list with filtering:**
```python
@router.get("", response_model=dict)
async def list_providers(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    status: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """List providers with optional status filter and pagination."""
    base = select(Provider).order_by(Provider.created_at.desc())
    if status:
        base = base.where(Provider.status == status)
    total = (await db.execute(select(func.count()).select_from(base.subquery()))).scalar_one()
    rows = (await db.execute(apply_pagination(base, page, page_size))).scalars().all()
    return {
        "items": [ProviderItem.model_validate(p) for p in rows],
        "page": page,
        "page_size": page_size,
        "total": total,
    }
```

**DELETE endpoint:**
```python
@router.delete("/{provider_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_provider(
    provider_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a provider profile. Owner or admin only."""
    provider = await db.get(Provider, provider_id)
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")
    await assert_owner_or_admin(db, provider.owner_user_id, current_user, "provider")

    await db.delete(provider)
    await db.commit()
    logger.info("[PROVIDER] Deleted provider - provider_id=%s user_id=%s", provider_id, current_user.id)
    # Return None — FastAPI serialises 204 No Content automatically
```

**Atomic multi-step create:**
```python
@router.post("", status_code=201, response_model=UserResponse)
async def create_user_with_role(body: CreateUserRequest, db: AsyncSession = Depends(get_db)) -> UserResponse:
    """Create a user and assign initial role atomically."""
    existing = (await db.execute(select(User).where(User.phone == body.phone).limit(1))).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=409, detail="Phone already registered")

    try:
        user = User(phone=body.phone, full_name=body.full_name)
        db.add(user)
        await db.flush()           # Get user.id without committing
        db.add(UserRole(user_id=user.id, role_code=RoleCode.CUSTOMER))
        await db.commit()
        await db.refresh(user)
    except Exception:
        await db.rollback()
        logger.exception("[USER] Failed to create user - phone=%s", body.phone[:4] + "***")
        raise HTTPException(status_code=500, detail="Internal server error")

    logger.info("[USER] Created user - user_id=%s", user.id)
    return UserResponse.model_validate(user)
```

---

**Remember**: Every line of code should be production-ready — properly typed, async-safe, validated, secure, and documented.
