# Kế hoạch triển khai Backend API — Sàn Dịch Vụ (Phase 1)

Tài liệu mô tả scope, API spec, stack, cấu trúc thư mục, **thứ tự ưu tiên khi làm API**, và các điểm rà soát với `database.sql`. Cập nhật tiến độ bằng cách tick các mục dưới phần "Tiến độ hiện tại".

---

## Tiến độ hiện tại

| Phase | Trạng thái | Phiên bản | Ngày cập nhật | Ghi chú |
|-------|------------|-----------|---------------|---------|
| Phase 1 — Auth + Common | Hoàn thành | 0.1.1 | 2026-03-25 | RBAC implemented, Auth flow secured. |
| Phase 2 — Admin | Hoàn thành | 0.2.1 | 2026-03-25 | Role-based access enforced. Taxonomy & Post OK. |
| Phase 3 — Customer | Hoàn thành | 0.2.0 | 2026-03-26 | **AI Search**, Provider Search (Approved > Pending). |
| Phase 4 — Provider Owner | Hoàn thành | 0.1.5 | 2026-03-26 | Unified Profile Update, Service Management OK. |

### Chi tiết công việc gần đây (26/03/2026)
- **AI Search Integration**: Thêm endpoint `/api/v1/customer/search` sử dụng `AIService` để bóc tách ý định người dùng (từ khóa, địa điểm).
- **Tối ưu tìm kiếm Provider**: Sửa logic `list_providers` và `search_providers` để hiển thị cả thợ `pending` (sau thợ `approved`), giúp platform có nhiều data hơn lúc khởi đầu.
- **Củng cố Security (RBAC)**: Áp dụng `check_user_role` cho các Admin route và bảo vệ endpoint của Provider.
- **Đồng bộ Schema**: Cập nhật Pydantic schemas cho `ProviderProfile` để khớp với database (hỗ trợ `business_phone`, các trường nullable).

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

| # | Method | Path | Notes | Trạng thái |
|---|--------|------|-------|------------|
| 1 | POST | `/api/v1/auth/otp/send` | phone → session + TTL | OK |
| 2 | POST | `/api/v1/auth/otp/verify` | → `otp_verification_token` | OK |
| 3 | POST | `/api/v1/auth/register` | + role customer + profile | OK |
| 4 | POST | `/api/v1/auth/login/otp` | | OK |
| 5 | POST | `/api/v1/auth/login/password` | | OK |
| 6 | POST | `/api/v1/auth/refresh` | | OK |
| 7 | POST | `/api/v1/auth/logout` | revoke refresh | OK |
| 8 | GET | `/api/v1/common/me` | Bearer | OK |
| 9 | PUT | `/api/v1/common/me` | Bearer | OK |
| 10 | GET | `/api/v1/common/me/roles` | Bearer | OK |
| 11 | GET | `/api/v1/common/posts` | optional | OK |
| 12 | GET | `/api/v1/common/posts/{slug}` | optional | OK |

### MODULE C — Customer (Phase 3)

| # | Method | Path | Notes | Trạng thái |
|---|--------|------|-------|------------|
| 301 | GET | `/api/v1/customer/industry-categories` | | OK |
| 302 | GET | `/api/v1/customer/industry-categories/{id}/service-categories` | | OK |
| 303 | GET | `/api/v1/customer/service-categories/{id}/skills` | | OK |
| 304 | GET | `/api/v1/customer/providers` | Hiện cả `approved` & `pending` | OK |
| 305 | GET | `/api/v1/customer/providers/{id}` | Chi tiết thợ | OK |
| 306 | GET | `/api/v1/customer/search` | **AI Search** theo prompt | OK |
| 307 | POST | `/api/v1/customer/become-provider` | Đăng ký làm thợ | OK |

### MODULE P — Provider Owner (Phase 4)

| # | Method | Path | Notes | Trạng thái |
|---|--------|------|-------|------------|
| 401 | GET | `/api/v1/provider/me` | Tổng quan thợ | OK |
| 402 | GET | `/api/v1/provider/me/profile` | Chi tiết hồ sơ thợ | OK |
| 403 | PUT | `/api/v1/provider/me/profile` | Update profile (cá nhân/DN) | OK |
| 404 | GET | `/api/v1/provider/services` | Danh sách dịch vụ thợ làm | OK |
| 405 | POST | `/api/v1/provider/services` | Đăng ký dịch vụ mới | OK |
| 406 | PATCH | `/api/v1/provider/services/{id}/attributes` | Cập nhật thuộc tính động | OK |
| 407 | DELETE | `/api/v1/provider/services/{id}` | Tạm ngừng cung cấp dịch vụ | OK |
| 408 | GET | `/api/v1/provider/service-options` | (Optional) Options cho service | N/A |

### MODULE D — Admin (Phase 2)

#### D1. Taxonomy (Làm đầu tiên trong Admin)

| # | Method | Path | Notes | Trạng thái |
|---|--------|------|-------|------------|
| A1 | GET | `/api/v1/admin/industry-categories` | | OK |
| A2 | POST | `/api/v1/admin/industry-categories` | | OK |
| A3 | PUT | `/api/v1/admin/industry-categories/{id}` | | OK |
| A4 | PATCH | `/api/v1/admin/industry-categories/{id}/status` | | OK |
| A5 | GET | `/api/v1/admin/service-categories` | | OK |
| A6 | POST | `/api/v1/admin/service-categories` | | OK |
| A7 | PUT | `/api/v1/admin/service-categories/{id}` | | OK |
| A8 | PATCH | `/api/v1/admin/service-categories/{id}/status` | | OK |
| A9 | GET | `/api/v1/admin/service-skills` | | OK |
| A10 | POST | `/api/v1/admin/service-skills` | | OK |
| A11 | PUT | `/api/v1/admin/service-skills/{id}` | | OK |
| A12 | PATCH | `/api/v1/admin/service-skills/{id}/status` | | OK |
| A13 | GET | `/api/v1/admin/service-categories/{id}/attributes` | | OK |
| A14 | POST | `/api/v1/admin/service-categories/{id}/attributes` | | OK |
| A15 | PUT | `/api/v1/admin/service-category-attributes/{attrId}` | | OK |
| A16 | DELETE | `/api/v1/admin/service-category-attributes/{attrId}` | | OK |
| A17 | GET | `/api/v1/admin/service-categories/{id}/requirements` | | OK |
| A18 | POST | `/api/v1/admin/service-categories/{id}/requirements` | | OK |
| A19 | PUT | `/api/v1/admin/service-category-requirements/{id}` | | OK |
| A20 | DELETE | `/api/v1/admin/service-category-requirements/{id}` | | OK |

#### D2. User (sau taxonomy)

| # | Method | Path | Notes | Trạng thái |
|---|--------|------|-------|------------|
| B1 | GET | `/api/v1/admin/users` | List users + filters | OK |
| B2 | GET | `/api/v1/admin/users/{id}` | Detail user | OK |
| B3 | PATCH | `/api/v1/admin/users/{id}/status` | Block/Unblock | OK |
| B4 | POST | `/api/v1/admin/users/create-provider-owner` | | OK |

#### D3. Provider (sau user)

| # | Method | Path | Notes | Trạng thái |
|---|--------|------|-------|------------|
| C1 | GET | `/api/v1/admin/providers` | Duyệt tiến độ xác minh | OK |
| C2 | GET | `/api/v1/admin/providers/{id}` | Hồ sơ chi tiết | OK |
| C3 | PATCH | `/api/v1/admin/providers/{id}/status` | Cập nhật verification status | OK |
| C4 | POST | `/api/v1/admin/providers/import` | | OK |
| C5 | POST | `/api/v1/admin/providers/manual-create` | | OK |

#### D4. Posts (tùy chọn)

| # | Method | Path | Notes | Trạng thái |
|---|--------|------|-------|------------|
| D1 | GET | `/api/v1/admin/post-categories` | | OK |
| D2 | POST | `/api/v1/admin/post-categories` | | OK |
| D3 | PUT | `/api/v1/admin/post-categories/{id}` | | OK |
| D4 | GET | `/api/v1/admin/posts` | | OK |
| D5 | POST | `/api/v1/admin/posts` | | OK |
| D6 | GET | `/api/v1/admin/posts/{id}` | | OK |
| D7 | PUT | `/api/v1/admin/posts/{id}` | | OK |
| D8 | PATCH | `/api/v1/admin/posts/{id}/status` | | OK |
| D9 | POST | `/api/v1/admin/posts/{id}/media` | | OK |
| D10 | DELETE | `/api/v1/admin/post-media/{mediaId}` | | OK |

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

## Phase 5 — API SPEC VER 2 (Trust & Qualification)

**Mục tiêu Ver 2:**
Tập trung vào lớp Trust & Qualification:
- User xác minh danh tính.
- Provider hoàn thiện hồ sơ.
- Provider upload document/chứng chỉ.
- Hệ thống kiểm tra provider service có đủ điều kiện hoạt động hay không.
- Admin có công cụ duyệt và quản lý.

*(Các API từ Ver 1 như Auth, Customer search, Become-provider, Admin taxonomy, Provider basic profile/service CRUD không làm lại, chỉ sử dụng lại).*

### MODULE C — Common (User Identity Verification)

Xác minh danh tính user ở cấp tài khoản. Flow: Tạo hồ sơ -> Upload CCCD/Selfie -> Submit -> Admin duyệt.

| # | Method | Path | Notes | Trạng thái |
|---|--------|------|-------|------------|
| C1 | GET | `/api/v1/common/me/verification-status` | Lấy trạng thái hiện tại | OK |
| C2 | GET | `/api/v1/common/me/identity-verifications` | Lịch sử hồ sơ | OK |
| C3 | POST | `/api/v1/common/me/identity-verifications` | Tạo hồ sơ draft | OK |
| C4 | GET | `/api/v1/common/me/identity-verifications/{id}` | Chi tiết hồ sơ | OK |
| C5 | POST | `/api/v1/common/me/identity-verifications/{id}/files` | Upload file (CCCD, selfie) | OK |
| C6 | POST | `/api/v1/common/me/identity-verifications/{id}/submit` | Nộp hồ sơ | OK |
| C7 | POST | `/api/v1/common/me/identity-verifications/{id}/cancel` | Hủy hồ sơ nháp | OK |

### MODULE P — Provider Owner (Profile & Documents)

Bắt buộc provider hoàn thiện hồ sơ, upload giấy tờ và xem xét điều kiện dịch vụ.

**Profile Completion:**
| # | Method | Path | Notes | Trạng thái |
|---|--------|------|-------|------------|
| P1 | GET | `/api/v1/provider/me` | Dùng lại từ Ver 1 | OK |
| P2 | PUT | `/api/v1/provider/me` | Cập nhật basic fields | OK |
| P3 | GET | `/api/v1/provider/me/profile` | Dùng lại từ Ver 1 | OK |
| P4 | PUT | `/api/v1/provider/me/profile/individual` | Cập nhật hồ sơ cá nhân | TODO |
| P5 | PUT | `/api/v1/provider/me/profile/business` | Cập nhật hồ sơ doanh nghiệp | TODO |
| P6 | GET | `/api/v1/provider/me/profile/completion` | Xem % hoàn thiện & fields thiếu | TODO |

**Provider Documents:**
| # | Method | Path | Notes | Trạng thái |
|---|--------|------|-------|------------|
| P7 | GET | `/api/v1/provider/me/documents` | Danh sách giấy tờ | TODO |
| P8 | POST | `/api/v1/provider/me/documents` | Tạo document mới (pending) | TODO |
| P9 | POST | `/api/v1/provider/me/documents/{id}/files` | Upload file (front, back, extra) | TODO |
| P10 | GET | `/api/v1/provider/me/documents/{id}` | Chi tiết giấy tờ | TODO |
| P11 | PUT | `/api/v1/provider/me/documents/{id}` | Cập nhật khi pending/rejected | TODO |
| P12 | DELETE | `/api/v1/provider/me/documents/{id}` | Xóa / hủy document | TODO |
| P13 | GET | `/api/v1/provider/me/documents/summary` | Trạng thái document | TODO |

**Service Qualification:**
| # | Method | Path | Notes | Trạng thái |
|---|--------|------|-------|------------|
| P14 | GET | `/api/v1/provider/me/services` | Dùng lại từ Ver 1 | OK |
| P15 | GET | `/api/v1/provider/me/services/{id}/requirements` | Xem requirement của service | TODO |
| P16 | GET | `/api/v1/provider/me/services/{id}/qualification` | Check đủ điều kiện chưa | TODO |
| P17 | PUT | `/api/v1/provider/me/services/{id}/documents` | Gắn document vào service | TODO |
| P18 | GET | `/api/v1/provider/me/services/{id}/documents` | Lấy tài liệu đã gắn | TODO |

### MODULE A — Admin (Verification & Qualification Console)

Admin quản lý các phiên bản xét duyệt.

**User Verification Console:**
| # | Method | Path | Notes | Trạng thái |
|---|--------|------|-------|------------|
| A21 | GET | `/api/v1/admin/user-verifications` | Danh sách hồ sơ xác minh | TODO |
| A22 | GET | `/api/v1/admin/user-verifications/{id}` | Chi tiết hồ sơ | TODO |
| A23 | POST | `/api/v1/admin/user-verifications/{id}/approve` | Duyệt | TODO |
| A24 | POST | `/api/v1/admin/user-verifications/{id}/reject` | Từ chối | TODO |
| A25 | POST | `/api/v1/admin/user-verifications/{id}/request-resubmission` | Yêu cầu bổ sung | TODO |

**Provider Document Review:**
| # | Method | Path | Notes | Trạng thái |
|---|--------|------|-------|------------|
| A26 | GET | `/api/v1/admin/provider-documents` | Danh sách giấy tờ provider | TODO |
| A27 | GET | `/api/v1/admin/provider-documents/{id}` | Chi tiết giấy tờ | TODO |
| A28 | POST | `/api/v1/admin/provider-documents/{id}/approve` | Duyệt chứng chỉ | TODO |
| A29 | POST | `/api/v1/admin/provider-documents/{id}/reject` | Từ chối chứng chỉ | TODO |

**Provider Qualification Console:**
| # | Method | Path | Notes | Trạng thái |
|---|--------|------|-------|------------|
| A30 | GET | `/api/v1/admin/provider-services/qualification` | Các dịch vụ cần check | TODO |
| A31 | GET | `/api/v1/admin/provider-services/{id}/qualification` | Chi tiết qualification | TODO |
| A32 | POST | `/api/v1/admin/provider-services/{id}/qualification/recheck` | Ép check lại điều kiện | TODO |

**Provider Completion:**
| # | Method | Path | Notes | Trạng thái |
|---|--------|------|-------|------------|
| A33 | GET | `/api/v1/admin/providers/incomplete` | Provider chưa hoàn thiện hồ sơ | TODO |
| A34 | GET | `/api/v1/admin/providers/{id}/completion` | Thống kê thiếu gì | TODO |

### MODULE I — Internal (Auto eKYC / Callback)

| # | Method | Path | Notes | Trạng thái |
|---|--------|------|-------|------------|
| I1 | POST | `/api/v1/internal/ekyc/callback` | Webhook từ vendor OCR/eKYC | TODO |
| I2 | POST | `/api/v1/internal/ekyc/process/{id}` | Gọi xử lý nền bằng worker | TODO |

---

*Có thể chỉnh sửa theo tiến độ; mỗi lần thêm bảng migration nên cập nhật tài liệu.*