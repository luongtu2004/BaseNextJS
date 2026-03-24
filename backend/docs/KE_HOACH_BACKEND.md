# Kế hoạch triển khai Backend API — Sàn Dịch Vụ (Phase 1)

Tài liệu mô tả scope, API spec, stack, cấu trúc thư mục, **thứ tự ưu tiên khi làm API**, và các điểm rà soát với `database.sql`. Cập nhật tiến độ bằng cách tick các mục dưới phần "Tiến độ hiện tại".

---

## Tiến độ hiện tại

| Phase | Trạng thái | Phiên bản | Ngày cập nhật | Ghi chú |
|-------|------------|-----------|---------------|---------|
| Phase 1 — Auth + Common | Đang làm | 0.1.0 | 2026-03-23 | `/health`, `/health/db` OK |
| Phase 2 — Admin | Hoàn thành | 0.2.0 | 2026-03-23 | Full Admin API: taxonomy, users, providers, posts |
| Phase 3 — Customer | Chưa làm | 0.1.0 | 2026-03-23 | Chờ Admin taxonomy |
| Phase 4 — Provider Owner | Chưa làm | 0.1.0 | 2026-03-23 | Chờ Customer và Admin |

---

## Giới thiệu: Thứ tự làm API (ưu tiên)

**Làm theo đúng thứ tự này để có data nền và test được ngay.**

### Phase 1 — Auth ( foundational layer)

Làm xong trước để có **user, token, role, auth middleware**:

- `GET /health` — kiểm tra server chạy
- `GET /health/db` — kiểm tra DB connection
- `POST /auth/otp/send`
- `POST /auth/otp/verify`
- `POST /auth/register`
- `POST /auth/login`
- `POST /auth/refresh`
- `GET /common/me`

**Sau phase này bạn đã có:**
- user model
- token (JWT)
- role system
- auth middleware (guards)

---

### Phase 2 — Admin (data foundation)

**Làm trước nhất: A. Taxonomy dịch vụ**

Vì mọi thứ sau đều phụ thuộc taxonomy (industry categories, service categories, skills).

#### A. Admin quản lý taxonomy dịch vụ

**API nên làm:**

| # | Method | Path |
|---|--------|------|
| A1 | GET | `/api/v1/admin/industry-categories` |
| A2 | POST | `/api/v1/admin/industry-categories` |
| A3 | PUT | `/api/v1/admin/industry-categories/{id}` |
| A4 | PATCH | `/api/v1/admin/industry-categories/{id}/status` |
| A5 | GET | `/api/v1/admin/service-categories` |
| A6 | POST | `/api/v1/admin/service-categories` |
| A7 | PUT | `/api/v1/admin/service-categories/{id}` |
| A8 | PATCH | `/api/v1/admin/service-categories/{id}/status` |
| A9 | GET | `/api/v1/admin/service-skills` |
| A10 | POST | `/api/v1/admin/service-skills` |
| A11 | PUT | `/api/v1/admin/service-skills/{id}` |
| A12 | PATCH | `/api/v1/admin/service-skills/{id}/status` |
| A13 | GET | `/api/v1/admin/service-categories/{id}/attributes` |
| A14 | POST | `/api/v1/admin/service-categories/{id}/attributes` |
| A15 | PUT | `/api/v1/admin/service-category-attributes/{attrId}` |
| A16 | DELETE | `/api/v1/admin/service-category-attributes/{attrId}` |
| A17 | GET | `/api/v1/admin/service-categories/{id}/requirements` |
| A18 | POST | `/api/v1/admin/service-categories/{id}/requirements` |
| A19 | PUT | `/api/v1/admin/service-category-requirements/{id}` |
| A20 | DELETE | `/api/v1/admin/service-category-requirements/{id}` |

**Vì sao làm phần này trước?**
- Customer có data để duyệt dịch vụ
- Provider có data để chọn dịch vụ phục vụ
- Admin có thể seed toàn bộ hệ thống ngay

#### B. Admin quản lý user (sau taxonomy)

**API nên làm:**

| # | Method | Path |
|---|--------|------|
| B1 | GET | `/api/v1/admin/users` |
| B2 | GET | `/api/v1/admin/users/{id}` |
| B3 | PATCH | `/api/v1/admin/users/{id}/status` |

**Tùy chọn:**
- `POST /api/v1/admin/users/create-provider-owner` — admin tạo sẵn user/provider

**Mục đích:**
- Xem danh sách user
- Khóa/mở user
- Quản trị cơ bản

#### C. Admin quản lý provider (sau user)

**API nên làm:**

| # | Method | Path |
|---|--------|------|
| C1 | GET | `/api/v1/admin/providers` |
| C2 | GET | `/api/v1/admin/providers/{id}` |
| C3 | PATCH | `/api/v1/admin/providers/{id}/status` |

**Tùy chọn:**
- `POST /api/v1/admin/providers/import`
- `POST /api/v1/admin/providers/manual-create`

**Mục đích:**
- Xem provider nào đang có
- Duyệt / ẩn / khóa provider
- Chuẩn bị data provider để test customer search

#### D. Admin quản lý bài viết (tùy chọn)

**API nên làm:**

| # | Method | Path |
|---|--------|------|
| D1 | GET | `/api/v1/admin/post-categories` |
| D2 | POST | `/api/v1/admin/post-categories` |
| D3 | PUT | `/api/v1/admin/post-categories/{id}` |
| D4 | GET | `/api/v1/admin/posts` |
| D5 | POST | `/api/v1/admin/posts` |
| D6 | GET | `/api/v1/admin/posts/{id}` |
| D7 | PUT | `/api/v1/admin/posts/{id}` |
| D8 | PATCH | `/api/v1/admin/posts/{id}/status` |
| D9 | POST | `/api/v1/admin/posts/{id}/media` |
| D10 | DELETE | `/api/v1/admin/post-media/{mediaId}` |

**Mục đích:**
- Admin có thể đăng bài quảng bá ngay
- Web có content sớm để test UI

---

### Phase 3 — Customer (sau Admin đã có data)

Sau khi admin đã tạo taxonomy/provider/post rồi mới làm customer sẽ rất dễ test.

**API nên làm:**

| # | Method | Path |
|---|--------|------|
| 301 | GET | `/api/v1/customer/industry-categories` |
| 302 | GET | `/api/v1/customer/industry-categories/{id}/service-categories` |
| 303 | GET | `/api/v1/customer/service-categories/{id}/skills` |
| 304 | GET | `/api/v1/customer/providers` |
| 305 | GET | `/api/v1/customer/providers/{id}` |
| 306 | GET | `/api/v1/customer/providers/{id}/services` |
| 307 | POST | `/api/v1/customer/become-provider` |

**Vì sao để sau Admin?**
- Đã có taxonomy
- Đã có provider mẫu
- Customer search test được ngay

---

### Phase 4 — Provider Owner (sau Customer)

Khi customer đã xem được danh sách rồi mới làm màn quản lý provider.

**API nên làm:**

| # | Method | Path |
|---|--------|------|
| 401 | GET | `/api/v1/provider/me` |
| 402 | PUT | `/api/v1/provider/me` |
| 403 | GET | `/api/v1/provider/me/profile` |
| 404 | PUT | `/api/v1/provider/me/profile/individual` |
| 405 | PUT | `/api/v1/provider/me/profile/business` |
| 406 | GET | `/api/v1/provider/service-options` |
| 407 | POST | `/api/v1/provider/services` |
| 408 | GET | `/api/v1/provider/services` |
| 409 | GET | `/api/v1/provider/services/{id}` |
| 410 | PUT | `/api/v1/provider/services/{id}` |
| 411 | PATCH | `/api/v1/provider/services/{id}` (update attributes) |
| 412 | DELETE | `/api/v1/provider/services/{id}/deactivate` |

---

## Stack đề xuất

| Thành phần | Gợi ý | Ghi chú |
|------------|--------|---------|
| Framework | **FastAPI** | OpenAPI sẵn, async, phù hợp mobile app. |
| DB driver / ORM | **SQLAlchemy 2.x (async)** + **psycopg 3** (binary) | URL mẫu: `postgresql+psycopg://...` |
| Migration | **Alembic** | — |
| Validation / config | **Pydantic v2** + **pydantic-settings** | Env tách khỏi code. |
| Auth | **JWT** (access + refresh) | `python-jose` hoặc `PyJWT` |
| Password | **bcrypt** (qua `passlib`) | `passlib[bcrypt]` |
| OTP | Tầng service + adapter SMS | Dev: log/mock; Prod: gateway thật |
| HTTP server | **uvicorn** | Chạy local / Docker |

---

## Cấu trúc thư mục backend

```text
backend/
  app/
    main.py                 # FastAPI app, CORS, router mount
    core/
      config.py             # Settings từ env
      security.py           # JWT, password, OTP helpers
    db/
      session.py            # Async engine, session factory
      base.py               # Declarative base
    models/                 # SQLAlchemy models
    schemas/                # Pydantic request/response
    api/
      deps.py               # get_db, get_current_user, role guards
      v1/
        auth.py             # Phase 1
        common.py           # Phase 1
        customer.py         # Phase 3
        provider.py         # Phase 4
        admin/
          taxonomy.py       # Phase 2A
          users.py          # Phase 2B
          providers.py      # Phase 2C
          posts.py          # Phase 2D
  services/
  alembic/
  docs/
    KE_HOACH_BACKEND.md
  .env.example
  requirements.txt
  .gitignore
```

---

## Checklist endpoint đầy đủ

### MODULE A — Auth / Common (Phase 1)

| # | Method | Path | Notes |
|---|--------|------|-------|
| 1 | POST | `/api/v1/auth/otp/send` | phone → session + TTL |
| 2 | POST | `/api/v1/auth/otp/verify` | → `otp_verification_token` |
| 3 | POST | `/api/v1/auth/register` | + role customer + profile |
| 4 | POST | `/api/v1/auth/login/otp` | |
| 5 | POST | `/api/v1/auth/login/password` | |
| 6 | POST | `/api/v1/auth/refresh` | |
| 7 | POST | `/api/v1/auth/logout` | revoke refresh |
| 8 | GET | `/api/v1/common/me` | Bearer |
| 9 | PUT | `/api/v1/common/me` | Bearer |
| 10 | GET | `/api/v1/common/me/roles` | Bearer |
| 11 | GET | `/api/v1/common/posts` | optional |
| 12 | GET | `/api/v1/common/posts/{slug}` | optional |

### MODULE C — Customer (Phase 3)

| # | Method | Path |
|---|--------|------|
| 301 | GET | `/api/v1/customer/industry-categories` |
| 302 | GET | `/api/v1/customer/industry-categories/{industryId}/service-categories` |
| 303 | GET | `/api/v1/customer/service-categories/{categoryId}/skills` |
| 304 | GET | `/api/v1/customer/providers` |
| 305 | GET | `/api/v1/customer/providers/{providerId}` |
| 306 | GET | `/api/v1/customer/providers/{providerId}/services` |
| 307 | POST | `/api/v1/customer/become-provider` |

### MODULE P — Provider Owner (Phase 4)

| # | Method | Path |
|---|--------|------|
| 401 | GET | `/api/v1/provider/me` |
| 402 | PUT | `/api/v1/provider/me` |
| 403 | GET | `/api/v1/provider/me/profile` |
| 404 | PUT | `/api/v1/provider/me/profile/individual` |
| 405 | PUT | `/api/v1/provider/me/profile/business` |
| 406 | GET | `/api/v1/provider/service-options` |
| 407 | POST | `/api/v1/provider/services` |
| 408 | GET | `/api/v1/provider/services` |
| 409 | GET | `/api/v1/provider/services/{id}` |
| 410 | PUT | `/api/v1/provider/services/{id}` |
| 411 | PATCH | `/api/v1/provider/services/{id}` |
| 412 | DELETE | `/api/v1/provider/services/{id}/deactivate` |

### MODULE D — Admin (Phase 2)

#### D1. Taxonomy (Làm đầu tiên trong Admin)

| # | Method | Path |
|---|--------|------|
| A1 | GET | `/api/v1/admin/industry-categories` |
| A2 | POST | `/api/v1/admin/industry-categories` |
| A3 | PUT | `/api/v1/admin/industry-categories/{id}` |
| A4 | PATCH | `/api/v1/admin/industry-categories/{id}/status` |
| A5 | GET | `/api/v1/admin/service-categories` |
| A6 | POST | `/api/v1/admin/service-categories` |
| A7 | PUT | `/api/v1/admin/service-categories/{id}` |
| A8 | PATCH | `/api/v1/admin/service-categories/{id}/status` |
| A9 | GET | `/api/v1/admin/service-skills` |
| A10 | POST | `/api/v1/admin/service-skills` |
| A11 | PUT | `/api/v1/admin/service-skills/{id}` |
| A12 | PATCH | `/api/v1/admin/service-skills/{id}/status` |
| A13 | GET | `/api/v1/admin/service-categories/{id}/attributes` |
| A14 | POST | `/api/v1/admin/service-categories/{id}/attributes` |
| A15 | PUT | `/api/v1/admin/service-category-attributes/{attrId}` |
| A16 | DELETE | `/api/v1/admin/service-category-attributes/{attrId}` |
| A17 | GET | `/api/v1/admin/service-categories/{id}/requirements` |
| A18 | POST | `/api/v1/admin/service-categories/{id}/requirements` |
| A19 | PUT | `/api/v1/admin/service-category-requirements/{id}` |
| A20 | DELETE | `/api/v1/admin/service-category-requirements/{id}` |

#### D2. User (sau taxonomy)

| # | Method | Path |
|---|--------|------|
| B1 | GET | `/api/v1/admin/users` |
| B2 | GET | `/api/v1/admin/users/{id}` |
| B3 | PATCH | `/api/v1/admin/users/{id}/status` |
| B4 | POST | `/api/v1/admin/users/create-provider-owner` |

#### D3. Provider (sau user)

| # | Method | Path |
|---|--------|------|
| C1 | GET | `/api/v1/admin/providers` |
| C2 | GET | `/api/v1/admin/providers/{id}` |
| C3 | PATCH | `/api/v1/admin/providers/{id}/status` |
| C4 | POST | `/api/v1/admin/providers/import` |
| C5 | POST | `/api/v1/admin/providers/manual-create` |

#### D4. Posts (tùy chọn)

| # | Method | Path |
|---|--------|------|
| D1 | GET | `/api/v1/admin/post-categories` |
| D2 | POST | `/api/v1/admin/post-categories` |
| D3 | PUT | `/api/v1/admin/post-categories/{id}` |
| D4 | GET | `/api/v1/admin/posts` |
| D5 | POST | `/api/v1/admin/posts` |
| D6 | GET | `/api/v1/admin/posts/{id}` |
| D7 | PUT | `/api/v1/admin/posts/{id}` |
| D8 | PATCH | `/api/v1/admin/posts/{id}/status` |
| D9 | POST | `/api/v1/admin/posts/{id}/media` |
| D10 | DELETE | `/api/v1/admin/post-media/{mediaId}` |

---

## Tiêu chí "xong Phase 1"

- App mobile có thể: đăng ký/đăng nhập, xem/me cập nhật hồ sơ, xem danh mục, tìm provider (trong phạm vi dữ liệu), xem bài viết.
- Thợ: đăng ký provider, sửa hồ sơ, đăng ký dịch vụ + thuộc tính động.
- Admin: duyệt user/provider (status), quản taxonomy và bài viết cơ bản.
- OpenAPI (`/docs`) cập nhật; env mẫu đủ để onboard dev mới trong < 30 phút.

---

## Chạy API

**Từ thư mục `backend/`:**

1. Tạo `.env` từ `.env.example`:
   ```powershell
   Copy-Item .env.example .env
   ```

2. Cấu hình `DATABASE_URL` trong `.env`

3. Chạy server:
   ```powershell
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

**Health check:**
- `GET /health` — không cần DB.
- `GET /health/db` — kiểm tra `SELECT 1` qua pool async.

**Swagger UI:**
- `http://localhost:8000/docs` — OpenAPI docs
- `http://localhost:8000/redoc` — ReDoc docs

---

*Có thể chỉnh sửa theo tiến độ; mỗi lần thêm bảng migration nên cập nhật tài liệu.*