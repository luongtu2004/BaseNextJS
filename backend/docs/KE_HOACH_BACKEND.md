# Kế hoạch triển khai Backend API — Sàn Dịch Vụ (Phase 1)

Tài liệu mô tả phạm vi, stack, cấu trúc thư mục, thứ tự công việc và các điểm rà soát với `database.sql`. **Cập nhật tiến độ** bằng cách tick các mục dưới mục 7.

## Tiến độ nhanh

| Sprint | Trạng thái |
|--------|------------|
| Sprint 0 — Hạ tầng | **Hoàn thành** (2026-03-23) |
| Sprint 1 — Auth / Common | **Đang làm** (2026-03-23) |
| Sprint 2 — Customer | Chưa làm |
| Sprint 3 — Provider | Chưa làm |
| Sprint 4 — Admin | Chưa làm |
| Sprint 5 — Cứng hóa | Chưa làm |

**Chạy API sau Sprint 0:** từ thư mục `backend/`, tạo `.env` từ `.env.example`, cấu hình `DATABASE_URL`, rồi:

`uvicorn app.main:app --reload --host 0.0.0.0 --port 8000`

- `GET /health` — không cần DB.
- `GET /health/db` — kiểm tra `SELECT 1` qua pool async.

**Alembic (DB đã có sẵn từ `database.sql`):** một lần trên môi trường đó: `alembic stamp 001_baseline` (hoặc `alembic stamp head`) để đồng bộ revision baseline, không chạy `upgrade` tạo bảng trùng.

---

## 1. Mục tiêu Phase 1

- **Nền tảng:** Python (REST API) + PostgreSQL, đồng bộ với schema hiện có trong `database.sql`.
- **Nghiệp vụ giai đoạn đầu:** quản lý **thông tin người dùng**, **danh mục dịch vụ**, **hồ sơ provider**, **bài viết công khai**; một người có thể vừa **khách** vừa **thợ** (role `customer` + `provider_owner`).
- **Chưa ưu tiên:** đặt lịch / job / thanh toán / chat realtime / đánh giá thực tế (các cột `avg_rating`, `total_jobs_completed` có thể giữ mặc định hoặc cập nhật thủ công/admin cho tới khi có module giao dịch).

---

## 2. Stack đề xuất

| Thành phần | Gợi ý | Ghi chú |
|------------|--------|---------|
| Framework | **FastAPI** | OpenAPI sẵn, async, phù hợp mobile app. |
| DB driver / ORM | **SQLAlchemy 2.x (async)** + **psycopg 3** (binary) hoặc **asyncpg** | URL mẫu: `postgresql+psycopg://...` (đã tránh lỗi build asyncpg trên Windows/Python mới nếu thiếu MSVC). Có thể đổi lại `postgresql+asyncpg://` khi môi trường hỗ trợ. Migration: **Alembic**. |
| Validation / config | **Pydantic v2** + **pydantic-settings** | Env tách khỏi code. |
| Auth | **JWT** (access + refresh) | `python-jose` hoặc `PyJWT`; refresh token lưu DB hoặc Redis (xem mục 6). |
| Password | **bcrypt** / **argon2** (qua `passlib` hoặc `argon2-cffi`) | Lưu `users.password_hash`. |
| OTP | Tầng service + adapter SMS | Dev: log/mock; Prod: gateway thật (ESMS, Twilio, v.v.). |
| HTTP server | **uvicorn** | Chạy local / Docker. |

File `requirements.txt` ở thư mục `backend/` liệt kê package khởi điểm; khi bắt đầu code nên **đóng version** (pin) theo môi trường CI/production.

---

## 3. Cấu trúc thư mục backend (đề xuất)

Tạo dần khi code, không bắt buộc đủ ngay ngày đầu:

```text
backend/
  app/
    main.py                 # FastAPI app, CORS, router mount
    core/
      config.py             # Settings từ env
      security.py           # JWT, password, OTP helpers
    db/
      session.py            # Async engine, session factory
      base.py               # Declarative base (nếu dùng ORM)
    models/                 # SQLAlchemy models (mirror database.sql)
    schemas/                # Pydantic request/response
    api/
      deps.py               # get_db, get_current_user, role guards
      v1/
        auth.py
        common.py
        customer.py
        provider.py
        admin/
          users.py
          providers.py
          taxonomy.py
          posts.py
    services/               # OTP, auth, provider, taxonomy, posts...
  alembic/                  # Sinh sau khi có models
  tests/
  docs/
    KE_HOACH_BACKEND.md     # (file này)
  .env.example
  requirements.txt
  .gitignore
```

---

## 4. Rà soát schema `database.sql` ↔ API đặc tả

### 4.1. Đã có và khớp tốt

- `users`, `user_roles`, `user_profiles`, `user_status_logs`
- `providers`, `provider_individual_profiles`, `provider_business_profiles`, `provider_documents`, `provider_status_logs`
- Taxonomy: `industry_categories`, `service_categories`, `service_skills`, `service_category_attributes`, `service_category_requirements`
- `provider_services`, `provider_service_attributes`, `provider_document_services`
- eKYC: `user_identity_*` (Phase 1 có thể **chưa** mở API; chỉ dùng cột tổng quát trên `users` nếu cần)
- CMS: `post_categories`, `posts`, `post_media`

### 4.2. Lệch / cần quyết định trước khi code

| Vấn đề | API yêu cầu | Trạng thái DB | Hành động đề xuất |
|--------|-------------|----------------|-------------------|
| Lọc provider theo **tỉnh / quận** | `province_code`, `district_code` | **Chưa có** cột/bảng địa giới trên `providers` | **Phase 1a:** bỏ query hoặc trả toàn bộ + lọc client; **Phase 1b:** migration thêm `province_code`, `district_code` (hoặc bảng `provider_locations`). |
| **OTP session** | `otp_session_id`, TTL | Không có bảng | Thêm bảng `otp_sessions` hoặc dùng **Redis** (TTL native). |
| **Refresh token** revoke (logout) | `POST /auth/logout` | Không có bảng | Thêm `refresh_tokens` (user_id, jti, expires_at, revoked_at) hoặc Redis blacklist. |
| `verification_token` sau verify OTP | JWT ngắn hạn one-time | — | Ký JWT riêng (scope `otp_register` / `otp_login`) TTL 5–10 phút. |

Ghi chép quyết định cuối vào phần “Chốt schema bổ sung” trước sprint code Auth.

---

## 5. Nguyên tắc thiết kế API

- **Prefix:** `/api/v1` cho mọi route (đồng nhất với đặc tả).
- **Phiên bản:** header `Accept` hoặc chỉ dùng path; Phase 1 chỉ cần v1.
- **Lỗi:** JSON thống nhất (`code`, `message`, `details`); mã HTTP chuẩn (401, 403, 404, 422, 409).
- **Phân quyền:** dependency FastAPI — `customer` cho B, `provider_owner` cho C, `admin` cho D; module A/Common một số endpoint public hoặc `Authorization: Bearer`.
- **Idempotency:** đăng ký provider (`become-provider`) — nếu đã có `provider` cho `owner_user_id` thì trả 409 hoặc trả provider hiện có (chốt một luồng).

---

## 6. Auth & OTP — luồng kỹ thuật (chuẩn bị trước khi code)

1. **POST `/auth/otp/send`:** tạo `otp_session_id` (UUID), lưu hash mã OTP + `expires_at` + `attempt_count`; gửi SMS (hoặc log dev).
2. **POST `/auth/otp/verify`:** so khớp mã, tăng attempt; thành công → phát **`otp_verification_token`** (JWT có `sub`=phone, `typ`=register|login, `sid`=session).
3. **POST `/auth/register`:** verify JWT OTP + tạo `users` (phone unique), `phone_verified=true`, role `customer`, `user_profiles` mặc định; phát access + refresh.
4. **POST `/auth/login/otp`:** user đã tồn tại + OTP verified → cập nhật `last_login_at`, phát token.
5. **POST `/auth/login/password`:** bcrypt verify `password_hash`.
6. **Refresh / logout:** lưu refresh token để revoke; logout set revoked hoặc xóa device row.

---

## 7. Thứ tự triển khai (sprint gợi ý)

### Sprint 0 — Hạ tầng (1–2 ngày)

- [x] Cài PostgreSQL local; chạy / chỉnh `database.sql` (extensions `pgcrypto`, `pg_trgm`). *(Do phía bạn đã tạo DB — giữ nguyên.)*
- [x] Tạo venv Python, `pip install -r requirements.txt`.
- [x] Scaffold FastAPI `app/main.py`, healthcheck `GET /health`, `GET /health/db`, CORS từ env.
- [x] Kết nối DB async (`app/db/session.py`, `psycopg`); **ORM models** mirror `database.sql` trong `app/models/`; Alembic khởi tạo + revision baseline rỗng `001_baseline` (DB có sẵn → dùng `alembic stamp`).
- [x] Copy `.env.example` → `.env`, không commit `.env`. *(Việc trên máy dev — tick khi bạn đã tạo file.)*

### Sprint 1 — Module A (Auth + Common) + seed tối thiểu

- [x] Bảng bổ sung (nếu chọn): `otp_sessions`, `refresh_tokens` (migration).
- [x] A1: OTP send/verify, register, login OTP, login password, refresh, logout.
- [x] A2: `GET/PUT /common/me`, `GET /common/me/roles`.
- [x] A2: `GET /common/posts`, `GET /common/posts/{slug}` (chỉ `status=published`, `visibility=public`).
- [ ] Test Postman/OpenAPI; tài liệu hóa example request.

### Sprint 2 — Module B (Customer)

- [ ] B1: industry / service-categories / skills (read-only, `is_active=true`).
- [ ] B2: list providers + detail + services (JOIN profile individual/business để lấy tên hiển thị).
- [ ] B2: filter `keyword` (ILIKE / `pg_trgm` nếu thêm index tên — có thể phase sau).
- [ ] B3: `POST /customer/become-provider` (transaction: role + `providers` + profile subtable).
- [ ] Quyết định và (nếu cần) migration **địa chỉ provider** cho filter tỉnh/huyện.

### Sprint 3 — Module C (Provider owner)

- [ ] Guard `provider_owner` + resolve `provider` theo `owner_user_id`.
- [ ] C1: `GET/PUT /provider/me`, profile GET/PUT individual & business.
- [ ] C2: `service-options` (cây taxonomy), CRUD `provider_services` (unique key như DB), **deactivate = `is_active=false`** thay vì DELETE cứng.
- [ ] C3: attributes template + `PUT .../attributes` (ghi `provider_service_attributes`; validate theo `service_category_attributes`).

### Sprint 4 — Module D (Admin)

- [ ] Guard `admin`.
- [ ] D1: users list/detail/PATCH status + `user_status_logs`.
- [ ] D2: providers list/detail/PATCH status + `provider_status_logs`.
- [ ] D3: CRUD taxonomy + attributes + requirements (đúng route đặc tả; chú ý `PATCH .../status` cho `is_active`).
- [ ] D4: post categories, posts, status, media upload (URL lưu DB; upload thực tế có thể presigned S3/MinIO — phase sau nếu chỉ lưu URL).

### Sprint 5 — Cứng hóa

- [ ] Test tự động (pytest) cho auth + một vài flow customer/provider.
- [ ] CORS, rate limit OTP (theo IP + phone).
- [ ] Chuẩn bị Docker Compose (API + Postgres [+ Redis]) cho team app.

---

## 8. Checklist endpoint (đối chiếu đặc tả)

### MODULE A — Auth / Common

| # | Method | Path | Ghi chú nhanh |
|---|--------|------|----------------|
| 1 | POST | `/api/v1/auth/otp/send` | phone → session + TTL |
| 2 | POST | `/api/v1/auth/otp/verify` | → `otp_verification_token` hoặc flag |
| 3 | POST | `/api/v1/auth/register` | + role customer + profile |
| 4 | POST | `/api/v1/auth/login/otp` | |
| 5 | POST | `/api/v1/auth/login/password` | |
| 6 | POST | `/api/v1/auth/refresh` | |
| 7 | POST | `/api/v1/auth/logout` | revoke refresh |
| 8 | GET | `/api/v1/common/me` | Bearer |
| 9 | PUT | `/api/v1/common/me` | user + user_profiles fields |
| 10 | GET | `/api/v1/common/me/roles` | |
| 11 | GET | `/api/v1/common/posts` | query filter + phân trang |
| 12 | GET | `/api/v1/common/posts/{slug}` | |

### MODULE B — Customer

| # | Method | Path |
|---|--------|------|
| 1 | GET | `/api/v1/customer/industry-categories` |
| 2 | GET | `/api/v1/customer/industry-categories/{industryId}/service-categories` |
| 3 | GET | `/api/v1/customer/service-categories/{categoryId}/skills` |
| 4 | GET | `/api/v1/customer/providers` |
| 5 | GET | `/api/v1/customer/providers/{providerId}` |
| 6 | GET | `/api/v1/customer/providers/{providerId}/services` |
| 7 | POST | `/api/v1/customer/become-provider` |

### MODULE C — Provider owner

| # | Method | Path |
|---|--------|------|
| 1 | GET | `/api/v1/provider/me` |
| 2 | PUT | `/api/v1/provider/me` |
| 3 | GET | `/api/v1/provider/me/profile` |
| 4 | PUT | `/api/v1/provider/me/profile/individual` |
| 5 | PUT | `/api/v1/provider/me/profile/business` |
| 6 | GET | `/api/v1/provider/service-options` |
| 7 | POST | `/api/v1/provider/services` |
| 8 | GET | `/api/v1/provider/services` |
| 9 | GET | `/api/v1/provider/services/{providerServiceId}` |
| 10 | PUT | `/api/v1/provider/services/{providerServiceId}` |
| 11 | PATCH | `/api/v1/provider/services/{providerServiceId}/deactivate` (khuyến nghị) |
| 12 | GET | `/api/v1/provider/services/attributes-template` |
| 13 | PUT | `/api/v1/provider/services/{providerServiceId}/attributes` |

### MODULE D — Admin

Theo đặc tả D1–D4 (users, providers, taxonomy đầy đủ, posts + media). Đảm bảo **một bảng mapping** giữa route `service-category-attributes` và khóa DB `service_category_attributes` để tránh nhầm ID category vs ID attribute.

---

## 9. Tiêu chí “xong Phase 1”

- App mobile có thể: đăng ký/đăng nhập, xem/me cập nhật hồ sơ, xem danh mục, tìm provider (trong phạm vi dữ liệu), xem bài viết.
- Thợ: đăng ký provider, sửa hồ sơ, đăng ký dịch vụ + thuộc tính động.
- Admin: duyệt user/provider (status), quản taxonomy và bài viết cơ bản.
- OpenAPI (`/docs`) cập nhật; env mẫu đủ để onboard dev mới trong &lt; 30 phút.

---

## 10. Việc cần chốt trước khi viết code Auth

1. Nhà cung cấp **SMS OTP** (và sandbox key).
2. **Redis** có bắt buộc không (OTP + refresh) hay chỉ PostgreSQL.
3. Có cho **đăng ký không mật khẩu** (chỉ OTP) không — ảnh hưởng `password_hash` nullable và flow login.
4. Quy ước **một user — một provider** hay nhiều provider (schema hiện tại: `owner_user_id` không unique → có thể nhiều; đặc tả “become-provider” nên chốt một record hay nhiều).

---

*Tài liệu có thể chỉnh sửa theo tiến độ; mỗi lần thêm bảng migration nên cập nhật mục 4 và 7.*
