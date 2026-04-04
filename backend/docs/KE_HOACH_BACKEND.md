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
| Phase 5 — Trust & Qualification | Hoàn thành | 0.3.0 | 2026-04-03 | Identity verify, Provider documents, Service qualification. |
| Phase 6 — Vận tải & Logistics | Hoàn thành | 0.4.0 | 2026-04-04 | Taxonomy seed → Vehicles → Routes → Rental (Logging & Pagination Refactor). |
| Phase 7 — Booking & Orders | Lên kế hoạch | — | — | Booking flow, driver accept/reject, trip states, pricing engine. |
| Phase 8 — Payment & Wallet | Lên kế hoạch | — | — | In-app wallet, VNPay/MoMo, refund, driver earnings. |
| Phase 9 — Rating, Notifications & Analytics | Lên kế hoạch | — | — | 2-way reviews, push notifications, admin dashboard. |
| Phase 10A — App Store Compliance | Lên kế hoạch | — | — | Sign in with Apple, Account deletion, Consent, PDPA. |
| Phase 10B — CRM Integration | Lên kế hoạch | — | — | Support tickets, Tags/Notes, Campaign broadcast. |
| Phase 11 — WebSocket & Real-time Chat | Lên kế hoạch | — | — | WS server riêng, in-trip chat, booking events real-time. |

### Chi tiết công việc gần đây (04/04/2026)
- **Chuẩn hóa hệ thống Logging (L4J Pattern)**: Tích hợp `logger` vào toàn bộ cấu trúc API (Auth, Admin, Customer, Provider), chuyển đổi chuẩn format (loại bỏ emojis, custom prefixes `[VEHICLE]`, `[AUTH]`), và thêm middleware tracking API calls (`request_logging.py`).
- **Refactor Pagination (Phase 6)**: Điểu chỉnh hàng loạt 10 API danh sách ở module Vận Tải (Phase 6) trả về đúng định dạng danh sách có phân trang chuẩn (`items`, `page`, `page_size`, `total`) thay vì mảng trơn, tuân thủ nghiêm ngặt Rule 13.
  - Fix test scripts và tự động verify toàn bộ 71/71 unit tests của Phase 6 API thành công xuất sắc (chính thức đóng gói xong Phase 6).
- **AI Search Integration**: Thêm endpoint `/api/v1/customer/search` sử dụng `AIService` để bóc tách ý định người dùng (từ khóa, địa điểm).
- **Tối ưu tìm kiếm Provider**: Sửa logic `list_providers` và `search_providers` để hiển thị cả thợ `pending` (sau thợ `approved`), giúp platform có nhiều data hơn lúc khởi đầu.
- **Củng cố Security (RBAC)**: Áp dụng `check_user_role` cho các Admin route và bảo vệ endpoint của Provider.
- **Đồng bộ Schema**: Cập nhật Pydantic schemas cho `ProviderProfile` để khớp với database (hỗ trợ `business_phone`, các trường nullable).

---

## MVP Roadmap — Phân tích ưu tiên (Việt Nam, 2026)

> Phân tầng toàn bộ tính năng theo mức độ ưu tiên cho MVP tại thị trường Việt Nam.  
> Dựa trên: nghiệp vụ vận tải, pháp lý VN (NĐ10/2020, NĐ13/2023), hành vi người dùng, ecosystem thanh toán, cạnh tranh Grab/XanhSM.

---

### 🔴 MUST HAVE — Phải có khi launch MVP

| # | Tính năng | Phase | Lý do bắt buộc |
|---|---|---|---|
| 1 | Auth OTP SMS + đăng ký | 1 ✅ | Nền tảng |
| 2 | **Zalo Login** | Bổ sung | 75M user VN — friction đăng ký thấp nhất |
| 3 | Provider onboarding + documents | 4–5 ✅ | Trust layer cốt lõi |
| 4 | Taxonomy seed vận tải (15 loại) | 6.1 | Category nền để provider đăng ký dịch vụ |
| 5 | Vehicle registration (cơ bản) | 6.2 | Tài xế phải khai báo xe trước khi nhận chuyến |
| 6 | Pricing: **formula mode** | 7.1 | Bắt buộc theo NĐ10/2020 — phải hiển thị giá trước khi đặt |
| 7 | Driver availability (online/offline) | 7.2 | Toggle nhận chuyến |
| 8 | Driver GPS update | 7.2 | Matching + customer tracking |
| 9 | **Booking core flow** (tiền mặt) | 7.3 | Trung tâm của sản phẩm |
| 10 | **Commission config** | 7.1b | Dòng tiền nền tảng — thu phí tài xế từ ngày 1 |
| 11 | **OTP xác nhận lên xe** | 7.4 | Safety cạnh tranh bắt buộc — Grab/XanhSM đều có |
| 12 | FCM push (booking events) | 9.2 | Tài xế nhận chuyến, khách nhận thông báo |
| 13 | Customer 1-way rating | 9.1 | Trust tối thiểu sau chuyến |
| 14 | **Sign in with Apple** | Bổ sung | 🔴 BẮT BUỘC (Apple Rule 4.8) nếu app có Zalo/Google Login |
| 15 | **Xóa tài khoản** (DELETE /common/me) | Bổ sung | 🔴 BẮT BUỘC từ 2022 — Apple 5.1.1(v) + Google Play đều yêu cầu |
| 16 | **Consent management** (terms/privacy/push) | 10A | 🔴 BẮT BUỘC nộp lên App Store + PDPA NĐ13/2023 |
| 17 | Data export (PDPA) | 10A | Quyền xuất dữ liệu cá nhân — bắt buộc theo luật VN |

> **MVP launch criteria:** Khách đặt xe → tìm tài xế → nhận → OTP lên xe → chạy → thanh toán tiền mặt → đánh giá. Hệ thống tự trừ hoa hồng vào ví tài xế.

---

### 🟠 SHOULD HAVE — Trong vòng 4 tuần sau launch

| # | Tính năng | Phase | Lý do |
|---|---|---|---|
| 1 | **Driver quote mode** | 7.1 | Xe ghép, hàng hóa VN hay thương lượng giá |
| 2 | MoMo / VNPay | 8.2 | Top 2 ví điện tử VN — giảm rủi ro tiền mặt |
| 3 | In-app wallet (cơ bản) | 8.1 | Driver earnings + customer topup |
| 4 | **Dispute / báo cáo sự cố** | 7.4 | Người dùng VN hay khiếu nại — thiếu là mất trust ngay |
| 5 | **Chia sẻ hành trình** | 7.4 | Safety — link track gửi người thân |
| 6 | Vehicle documents + admin review | 6.2 | Đăng kiểm/bảo hiểm hết hạn → vi phạm pháp lý |
| 7 | Driver earnings dashboard | 8.1 | Tài xế VN theo dõi thu nhập hàng ngày |
| 8 | 2-way rating | 9.1 | Tài xế đánh giá khách — tính năng cạnh tranh |
| 9 | Zalo OA notification | 9.2 | Tỷ lệ đọc >80%, rẻ hơn SMS ~10x |
| 10 | Cảnh báo giấy tờ sắp hết hạn | 6.2 | Đăng kiểm 1 năm, bảo hiểm 1 năm — auto alert |
| 11 | **Support ticket cơ bản** | 10B | Khách gửi khiếu nại/hỏi tất cả — bắt buộc cho App Store review account |
| 12 | **CRM: Tag + note khách hàng** | 10B | Admin đánh dấu VIP/churned/riskflag, ghi chú nội bộ |

---

### 🟡 NICE TO HAVE — 1–3 tháng sau launch

| # | Tính năng | Phase |
|---|---|---|
| 1 | Routes & schedules (xe liên tỉnh) | 6.3 |
| 2 | Rental availability calendar | 6.4 |
| 3 | Scheduled booking (đặt lịch trước) | Mới |
| 4 | Tỉnh/Huyện/Xã chuẩn hóa ĐVHC | Mới |
| 5 | Hóa đơn VAT điện tử (MISA/VNPT Invoice) | Mới |
| 6 | eKYC tự động (VNPT/FPT eKYC) | Upgrade Phase 5 |
| 7 | Admin analytics dashboard | 9.3 |
| 8 | Promotions & vouchers | 8.3 |
| 9 | SOS / nút khẩn cấp | Mới |
| 10 | Google Login | Bổ sung |
| 11 | **In-trip chat** (WS) | 11 |

---

### 🟢 POST-MVP — 3+ tháng

| # | Tính năng | Lý do chưa cần ngay |
|---|---|---|
| 1 | Fleet owner (chủ xe + nhiều tài xế) | Cần supply base trước |
| 2 | Surge pricing giờ cao điểm | Cần đủ data để calibrate |
| 3 | VNeID chip integration | Phức tạp pháp lý, VNPT eKYC đủ cho giai đoạn đầu |
| 4 | AI route optimization | Cần đủ trip history |
| 5 | Consent logs đầy đủ (PDPA VN NĐ13/2023) | Cần tư vấn pháp lý trước |
| 6 | Hợp đồng điện tử với tài xế | Cần khi scale, không cần MVP |

---

### Sprint Plan — 8 tuần đến MVP launch

| Sprint | Tuần | Nội dung | Output kiểm chứng |
|---|---|---|---|
| **S1** | 1–2 | Taxonomy seed vận tải + Vehicle registration cơ bản | Provider đăng ký được loại dịch vụ + xe |
| **S2** | 3–4 | Pricing formula + Commission config + Driver availability + GPS | Tài xế online, hệ thống hiển thị giá |
| **S3** | 5–6 | Booking flow đầy đủ (tiền mặt) + OTP lên xe + FCM push | Đặt và hoàn thành được chuyến |
| **S4** | 7–8 | Zalo Login + **Sign in with Apple** + 1-way rating + Admin CMS booking/commission view | Sẵn sàng launch |
| 🚀 | **Tuần 9** | **MVP LAUNCH** | — |
| **S5** | 9–10 | Driver quote mode + MoMo/VNPay + Wallet cơ bản | Thanh toán điện tử |
| **S6** | 11–12 | Dispute/report + Trip sharing + 2-way rating + Driver earnings | Trust & safety layer |
| **S7** | 13–14 | **WS Server** + In-trip chat + Live booking events | Real-time UX |
| **S8** | 15–16 | Account deletion + Consent + Data export + Support tickets | App Store compliance + CRM |
| **S9** | 17–18 | CRM Tags/Notes + Campaign broadcast + Auto-tagging | Admin CRM đầy đủ |

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
| WebSocket | **FastAPI WebSocket** hoặc **Socket.IO** | Server riêng port 8001, scale độc lập |
| Pub/Sub | **Redis 7** | Fanout WS messages giữa các instance |
| Realtime cache | **Redis** | Driver location, presence, message cache |

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
| 0a | POST | `/api/v1/auth/login/zalo` | OAuth Zalo — **🔴 MVP** (75M user VN) | TODO |
| 0b | POST | `/api/v1/auth/login/google` | OAuth Google — 🟡 Nice to have | TODO |
| 0c | POST | `/api/v1/auth/login/apple` | **Sign in with Apple — 🔴 BẮT BUỘC** nếu app có bất kỳ social login nào (Apple Rule 4.8) | TODO |
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
| 13 | DELETE | `/api/v1/common/me` | **🔴 BẮT BUỘC** — xóa tài khoản vĩnh viễn (Apple 5.1.1(v) + Google Play) | TODO |
| 14 | POST | `/api/v1/common/me/deactivate` | Tạm khóa tài khoản (soft-delete trước khi xóa hẳn) | TODO |
| 15 | GET | `/api/v1/common/me/data-export` | Xuất toàn bộ dữ liệu cá nhân (ZIP) — PDPA NĐ13/2023 | TODO |
| 16 | GET | `/api/v1/common/me/consents` | Xem trạng thái các consent đã cấp | TODO |
| 17 | POST | `/api/v1/common/me/consents` | Ghi nhận consent (terms/privacy/marketing/push) + version | TODO |
| 18 | POST | `/api/v1/common/me/consents/withdraw` | Thu hồi consent marketing (không xóa terms/privacy) | TODO |
| 19 | POST | `/api/v1/common/me/cancel-deletion` | Hủy yêu cầu xóa tài khoản (trong grace period 30 ngày) | TODO |

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
| P4 | PUT | `/api/v1/provider/me/profile/individual` | Cập nhật hồ sơ cá nhân | OK |
| P5 | PUT | `/api/v1/provider/me/profile/business` | Cập nhật hồ sơ doanh nghiệp | OK |
| P6 | GET | `/api/v1/provider/me/profile/completion` | Xem % hoàn thiện & fields thiếu | OK |

**Provider Documents:**
| # | Method | Path | Notes | Trạng thái |
|---|--------|------|-------|------------|
| P7 | GET | `/api/v1/provider/me/documents` | Danh sách giấy tờ | OK |
| P8 | POST | `/api/v1/provider/me/documents` | Tạo document mới (pending) | OK |
| P9 | POST | `/api/v1/provider/me/documents/{id}/files` | Upload file (front, back, extra) | OK |
| P10 | GET | `/api/v1/provider/me/documents/{id}` | Chi tiết giấy tờ | OK |
| P11 | PUT | `/api/v1/provider/me/documents/{id}` | Cập nhật khi pending/rejected | OK |
| P12 | DELETE | `/api/v1/provider/me/documents/{id}` | Xóa / hủy document | OK |
| P13 | GET | `/api/v1/provider/me/documents/summary` | Trạng thái document | OK |

**Service Qualification:**
| # | Method | Path | Notes | Trạng thái |
|---|--------|------|-------|------------|
| P14 | GET | `/api/v1/provider/me/services` | Dùng lại từ Ver 1 | OK |
| P15 | GET | `/api/v1/provider/me/services/{id}/requirements` | Xem requirement của service | OK |
| P16 | GET | `/api/v1/provider/me/services/{id}/qualification` | Check đủ điều kiện chưa | OK |
| P17 | PUT | `/api/v1/provider/me/services/{id}/documents` | Gắn document vào service | OK |
| P18 | GET | `/api/v1/provider/me/services/{id}/documents` | Lấy tài liệu đã gắn | OK |

### MODULE A — Admin (Verification & Qualification Console)

Admin quản lý các phiên bản xét duyệt.

**User Verification Console:**
| # | Method | Path | Notes | Trạng thái |
|---|--------|------|-------|------------|
| A21 | GET | `/api/v1/admin/user-verifications` | Danh sách hồ sơ xác minh | OK |
| A22 | GET | `/api/v1/admin/user-verifications/{id}` | Chi tiết hồ sơ | OK |
| A23 | POST | `/api/v1/admin/user-verifications/{id}/approve` | Duyệt | OK |
| A24 | POST | `/api/v1/admin/user-verifications/{id}/reject` | Từ chối | OK |
| A25 | POST | `/api/v1/admin/user-verifications/{id}/request-resubmission` | Yêu cầu bổ sung | OK |

**Provider Document Review:**
| # | Method | Path | Notes | Trạng thái |
|---|--------|------|-------|------------|
| A26 | GET | `/api/v1/admin/provider-providers/documents` | Danh sách giấy tờ provider | OK |
| A27 | GET | `/api/v1/admin/provider-providers/documents/{id}` | Chi tiết giấy tờ | OK |
| A28 | POST | `/api/v1/admin/provider-providers/documents/{id}/review` | Duyệt/Từ chối chứng chỉ | OK |

**Provider Qualification Console:**
| # | Method | Path | Notes | Trạng thái |
|---|--------|------|-------|------------|
| A30 | GET | `/api/v1/admin/provider-providers/provider-services/qualification` | Các dịch vụ cần check | OK |
| A31 | GET | `/api/v1/admin/provider-providers/provider-services/{id}/qualification` | Chi tiết qualification | OK |
| A32 | POST | `/api/v1/admin/provider-providers/provider-services/{id}/qualification/recheck` | Ép check lại điều kiện | OK |

**Provider Completion:**
| # | Method | Path | Notes | Trạng thái |
|---|--------|------|-------|------------|
| A33 | GET | `/api/v1/admin/provider-providers/incomplete` | Provider chưa hoàn thiện hồ sơ | OK |
| A34 | GET | `/api/v1/admin/provider-providers/{id}/completion-summary` | Thống kê thiếu gì | OK |

### MODULE I — Internal (Auto eKYC / Callback)

| # | Method | Path | Notes | Trạng thái |
|---|--------|------|-------|------------|
| I1 | POST | `/api/v1/internal/ekyc/callback` | Webhook từ vendor OCR/eKYC | TODO |
| I2 | POST | `/api/v1/internal/ekyc/process/{id}` | Gọi xử lý nền bằng worker | TODO |

---

## Phase 6 — API SPEC VER 3 (Vận tải & Logistics)

**Mục tiêu:** Mở rộng hệ thống cho nhóm ngành **Vận tải & Logistics** — taxonomy, quản lý phương tiện, tuyến đường, lịch, và cho thuê xe tự lái.  
**Tài liệu chi tiết:** `docs/KE_HOACH_VAN_TAI_LOGISTICS.md`

### Phase 6.1 — Taxonomy Seed (không cần code mới)

**Việc cần làm:**
- [x] Tạo `sql/seed_taxonomy_vantai.sql` — 15 `service_categories` cho nhóm `vantaidichuyen`
- [x] Seed `service_category_attributes` (~120 records)
- [x] Seed `service_category_requirements` (~45 records)
- [x] Seed `service_skills`
- [x] Verify qua `/api/v1/customer/industry-categories`

### Phase 6.2 — Quản lý Phương tiện

**Migration:** tạo `provider_vehicles`, `provider_vehicle_documents`

#### MODULE P — Provider Vehicles

| # | Method | Path | Notes | Trạng thái |
|---|--------|------|-------|------------|
| V1 | POST | `/api/v1/provider/vehicles` | Thêm xe mới | OK |
| V2 | GET | `/api/v1/provider/vehicles` | Danh sách xe của tôi | OK |
| V3 | GET | `/api/v1/provider/vehicles/{id}` | Chi tiết xe | OK |
| V4 | PUT | `/api/v1/provider/vehicles/{id}` | Cập nhật xe | OK |
| V4b | PATCH | `/api/v1/provider/vehicles/{id}/status` | Kích hoạt / tạm ngừng xe | OK |
| V5 | DELETE | `/api/v1/provider/vehicles/{id}` | Xóa xe | OK |
| V6 | GET | `/api/v1/provider/vehicles/{id}/documents` | Danh sách giấy tờ xe | OK |
| V7 | POST | `/api/v1/provider/vehicles/{id}/documents` | Thêm giấy tờ xe | OK |
| V8 | GET | `/api/v1/provider/vehicles/{id}/documents/{doc_id}` | Chi tiết giấy tờ xe | OK |
| V9 | PUT | `/api/v1/provider/vehicles/{id}/documents/{doc_id}` | Cập nhật giấy tờ xe | OK |
| V10 | DELETE | `/api/v1/provider/vehicles/{id}/documents/{doc_id}` | Xóa giấy tờ xe | OK |

#### MODULE A — Admin Vehicles

| # | Method | Path | Notes | Trạng thái |
|---|--------|------|-------|------------|
| AV1 | GET | `/api/v1/admin/vehicles` | Danh sách tất cả xe | OK |
| AV2 | GET | `/api/v1/admin/vehicles/{id}` | Chi tiết xe | OK |
| AV3 | PATCH | `/api/v1/admin/vehicles/{id}/status` | Kích hoạt / khóa xe | OK |
| AV4 | GET | `/api/v1/admin/vehicle-documents` | Queue giấy tờ xe chờ duyệt | OK |
| AV5 | POST | `/api/v1/admin/vehicle-documents/{doc_id}/review` | Duyệt / từ chối giấy tờ xe | OK |

### Phase 6.3 — Tuyến đường & Lịch khởi hành

**Migration:** tạo `service_routes`, `service_route_schedules`

#### MODULE P — Provider Routes & Schedules

| # | Method | Path | Notes | Trạng thái |
|---|--------|------|-------|------------|
| R1 | POST | `/api/v1/provider/services/{svc_id}/routes` | Tạo tuyến → `service_routes` | OK |
| R2 | GET | `/api/v1/provider/services/{svc_id}/routes` | Danh sách tuyến | OK |
| R2b | GET | `/api/v1/provider/services/{svc_id}/routes/{id}` | Chi tiết tuyến | OK |
| R3 | PUT | `/api/v1/provider/services/{svc_id}/routes/{id}` | Cập nhật tuyến | OK |
| R3b | PATCH | `/api/v1/provider/services/{svc_id}/routes/{id}/status` | Bật / tắt tuyến | OK |
| R4 | DELETE | `/api/v1/provider/services/{svc_id}/routes/{id}` | Xóa tuyến | OK |
| R5 | POST | `/api/v1/provider/routes/{route_id}/schedules` | Thêm lịch → `service_route_schedules` | OK |
| R6 | GET | `/api/v1/provider/routes/{route_id}/schedules` | Danh sách lịch | OK |
| R7 | PUT | `/api/v1/provider/routes/{route_id}/schedules/{id}` | Cập nhật lịch | OK |
| R7b | PATCH | `/api/v1/provider/routes/{route_id}/schedules/{id}/status` | Bật / tắt lịch | OK |
| R8 | DELETE | `/api/v1/provider/routes/{route_id}/schedules/{id}` | Xóa lịch | OK |

#### MODULE C — Customer Transport Search

| # | Method | Path | Notes | Trạng thái |
|---|--------|------|-------|------------|
| CT1 | GET | `/api/v1/customer/transport/search` | Tìm provider theo loại + khu vực | OK |
| CT2 | GET | `/api/v1/customer/transport/routes` | Tìm tuyến xe (from → to + ngày) | OK |
| CT3 | GET | `/api/v1/customer/transport/routes/{id}` | Chi tiết tuyến + danh sách lịch khởi hành | OK |

#### MODULE A — Admin Routes

| # | Method | Path | Notes | Trạng thái |
|---|--------|------|-------|------------|
| AR1 | GET | `/api/v1/admin/routes` | Tất cả tuyến đường | OK |
| AR2 | GET | `/api/v1/admin/routes/{id}` | Chi tiết tuyến + lịch khởi hành | OK |
| AR3 | PATCH | `/api/v1/admin/routes/{id}/status` | Bật / tắt tuyến | OK |

### Phase 6.4 — Cho thuê xe & Lịch trống

**Migration:** tạo `provider_vehicle_availabilities`

#### MODULE P — Provider Rental Availability

| # | Method | Path | Notes | Trạng thái |
|---|--------|------|-------|------------|
| RA1 | GET | `/api/v1/provider/vehicles/{id}/availabilities` | Xem lịch → `provider_vehicle_availabilities` | OK |
| RA2 | POST | `/api/v1/provider/vehicles/{id}/availabilities/block` | Block ngày không cho thuê | OK |
| RA3 | POST | `/api/v1/provider/vehicles/{id}/availabilities/unblock` | Mở lại ngày | OK |

#### MODULE C — Customer Rental

| # | Method | Path | Notes | Trạng thái |
|---|--------|------|-------|------------|
| CR1 | GET | `/api/v1/customer/transport/rental-vehicles` | Tìm xe cho thuê (loại + ngày + khu vực) | OK |
| CR1b | GET | `/api/v1/customer/transport/rental-vehicles/{id}` | Chi tiết xe cho thuê | OK |
| CR2 | GET | `/api/v1/customer/transport/rental-vehicles/{id}/availabilities` | Kiểm tra lịch trống | OK |

---

## Phase 7 — API SPEC VER 4 (Booking & Orders)

**Mục tiêu:** Xây dựng luồng đặt xe hoàn chỉnh theo mô hình XanhSM — từ báo giá → đặt chuyến → tài xế nhận → đang chạy → hoàn thành.  
**Bảng DB mới:** `bookings`, `booking_status_logs`, `price_configs`, `driver_availability_sessions`, `driver_locations`

*(Các API từ Phase 1–6 không làm lại, chỉ sử dụng lại.)*

---

### 7.1 — Pricing Engine

**Bảng:** `price_configs`

Admin có thể cấu hình **2 chế độ tính giá** cho từng loại dịch vụ:

| `pricing_mode` | Mô tả | Luồng |
|---|---|---|
| `formula` | Hệ thống tự tính giá theo công thức `base_fare + fare_per_km × km + fare_per_min × min` | Customer nhận giá ngay sau khi nhập điểm đi/đến |
| `driver_quote` | Tài xế xem km → tự đặt giá → gửi báo giá cho khách → khách accept/reject | Thêm bước thương lượng giá trước khi xác nhận |

```sql
CREATE TABLE price_configs (
    id               UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    service_type     VARCHAR(50)  NOT NULL,   -- taxi/xe_om/cho_thue_xe_oto/xe_khach/...
    pricing_mode     VARCHAR(20)  NOT NULL DEFAULT 'formula',
    --   'formula'      : hệ thống tự tính giá
    --   'driver_quote' : tài xế tự ra giá, khách confirm trước khi đi

    -- Dùng khi pricing_mode = 'formula'
    base_fare        NUMERIC(18,2),           -- Giá mở cửa
    fare_per_km      NUMERIC(18,2),           -- Giá/km
    fare_per_min     NUMERIC(18,2),           -- Giá/phút (kẹt xe)
    min_fare         NUMERIC(18,2),           -- Giá tối thiểu
    surge_enabled    BOOLEAN NOT NULL DEFAULT false,
    surge_multiplier NUMERIC(4,2)  DEFAULT 1.0,

    -- Dùng khi pricing_mode = 'driver_quote'
    quote_timeout_sec INTEGER      DEFAULT 120,  -- Giây khách chờ báo giá từ tài xế
    accept_timeout_sec INTEGER     DEFAULT 60,   -- Giây khách có để accept/reject
    min_quote        NUMERIC(18,2),              -- Tài xế không được báo giá dưới mức này
    max_quote        NUMERIC(18,2),              -- Tài xế không được báo giá vượt mức này

    effective_from   TIMESTAMPTZ NOT NULL DEFAULT now(),
    effective_to     TIMESTAMPTZ,
    is_active        BOOLEAN NOT NULL DEFAULT true,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

#### MODULE C — Customer Pricing

| # | Method | Path | Notes | Trạng thái |
|---|--------|------|-------|------------|
| PR1 | POST | `/api/v1/customer/transport/estimate` | Báo giá ước tính — trả về `estimated_fare` nếu mode=`formula`, hoặc `{pricing_mode: "driver_quote"}` nếu tài xế tự ra giá | TODO |

#### MODULE A — Admin Pricing

| # | Method | Path | Notes | Trạng thái |
|---|--------|------|-------|------------|
| APR1 | GET | `/api/v1/admin/price-configs` | Danh sách cấu hình giá | TODO |
| APR2 | POST | `/api/v1/admin/price-configs` | Tạo cấu hình giá (chọn `pricing_mode`) | TODO |
| APR3 | PUT | `/api/v1/admin/price-configs/{id}` | Cập nhật cấu hình + đổi mode nếu cần | TODO |
| APR4 | PATCH | `/api/v1/admin/price-configs/{id}/status` | Bật / tắt cấu hình | TODO |

---

### 7.1b — Commission Config 🔴 MVP

> **Đây là dòng tiền cốt lõi của nền tảng.** Khi tài xế nhận tiền mặt, hệ thống khấu trừ hoa hồng từ ví tài xế sau mỗi chuyến hoàn thành.

**Bảng:** `commission_configs`

```sql
CREATE TABLE commission_configs (
    id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    service_type    VARCHAR(50) NOT NULL,
    rate_percent    NUMERIC(5,2) NOT NULL,    -- e.g. 20.00 = 20%
    fixed_fee       NUMERIC(18,2) DEFAULT 0, -- phí cố định/chuyến (nếu có)
    effective_from  TIMESTAMPTZ NOT NULL DEFAULT now(),
    effective_to    TIMESTAMPTZ,
    is_active       BOOLEAN NOT NULL DEFAULT true,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (service_type, effective_from)
);
```

**Logic settle sau mỗi chuyến `completed`:**
```
final_fare = 100,000đ  |  commission_rate = 20%
→ platform_fee     = 20,000đ  (debit từ ví tài xế)
→ driver_earnings  = 80,000đ  (credit vào ví tài xế)

Tiền mặt: khách trả tài xế 100k → ví tài xế trừ 20k (nợ nền tảng)
Online:   hệ thống tự phân chia khi thanh toán settle
```

#### MODULE A — Admin Commission

| # | Method | Path | Notes | Trạng thái |
|---|--------|------|-------|------------|
| CM1 | GET | `/api/v1/admin/commission-configs` | Danh sách cấu hình hoa hồng | TODO |
| CM2 | POST | `/api/v1/admin/commission-configs` | Tạo theo loại dịch vụ + effective date | TODO |
| CM3 | PUT | `/api/v1/admin/commission-configs/{id}` | Cập nhật tỷ lệ | TODO |
| CM4 | PATCH | `/api/v1/admin/commission-configs/{id}/status` | Bật / tắt | TODO |

---

### 7.2 — Driver Availability & Location

**Bảng:** `driver_availability_sessions`, `driver_locations`

```sql
CREATE TABLE driver_availability_sessions (
    id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    provider_id     UUID        NOT NULL REFERENCES providers(id),
    vehicle_id      UUID        REFERENCES provider_vehicles(id),
    status          VARCHAR(20) NOT NULL DEFAULT 'offline', -- offline/online/busy
    online_at       TIMESTAMPTZ,
    offline_at      TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE driver_locations (
    provider_id     UUID        PRIMARY KEY REFERENCES providers(id),
    latitude        NUMERIC(10,7) NOT NULL,
    longitude       NUMERIC(10,7) NOT NULL,
    heading         NUMERIC(5,2),          -- hướng di chuyển (độ)
    speed_kmh       NUMERIC(5,1),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
-- Ghi chú: driver_locations dùng UPSERT liên tục, nên cân nhắc Redis cho real-time
```

#### MODULE P — Driver Status

| # | Method | Path | Notes | Trạng thái |
|---|--------|------|-------|------------|
| DS1 | PATCH | `/api/v1/provider/me/availability` | Bật/tắt nhận chuyến (online/offline) | TODO |
| DS2 | PATCH | `/api/v1/provider/me/location` | Cập nhật GPS liên tục (gọi mỗi ~5s) | TODO |
| DS3 | GET | `/api/v1/provider/me/availability` | Xem trạng thái hiện tại | TODO |

#### MODULE C — Customer Discovery

| # | Method | Path | Notes | Trạng thái |
|---|--------|------|-------|------------|
| DD1 | GET | `/api/v1/customer/transport/nearby-drivers` | Tài xế gần nhất theo toạ độ + loại dịch vụ | TODO |

---

### 7.3 — Bookings

**Bảng:** `bookings`, `booking_status_logs`

#### Trạng thái booking theo từng pricing_mode

**Mode `formula` (hệ thống tính giá):**
```
pending → searching → accepted → arriving → in_progress → completed
                                          ↘ cancelled
```

**Mode `driver_quote` (tài xế tự ra giá):**
```
pending → searching → driver_quoted ──► customer_accepted → arriving → in_progress → completed
                    ↓                ↘ customer_rejected → searching (tìm tài xế khác)
                    ↓                ↘ quote_expired    → searching (tài xế không gửi kịp)
                    ↘ cancelled (any stage)
```

> Khi `pricing_mode = driver_quote`: tài xế nhận yêu cầu, xem km và điểm đi/đến, tự nhập giá và gửi về. Khách nhận push notification, xem giá + km, chọn **Đồng ý** hoặc **Từ chối**. Nếu từ chối → hệ thống dispatch tài xế khác.

```sql
CREATE TABLE bookings (
    id                  UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id         UUID        NOT NULL REFERENCES users(id),
    provider_id         UUID        REFERENCES providers(id),
    vehicle_id          UUID        REFERENCES provider_vehicles(id),
    service_category_id UUID        NOT NULL REFERENCES service_categories(id),
    service_type        VARCHAR(50) NOT NULL,
    pricing_mode        VARCHAR(20) NOT NULL DEFAULT 'formula',  -- formula / driver_quote
    -- Địa điểm
    pickup_address      TEXT        NOT NULL,
    pickup_lat          NUMERIC(10,7),
    pickup_lng          NUMERIC(10,7),
    dropoff_address     TEXT,
    dropoff_lat         NUMERIC(10,7),
    dropoff_lng         NUMERIC(10,7),
    -- Cho thuê/liên tỉnh
    route_id            UUID        REFERENCES service_routes(id),
    schedule_id         UUID        REFERENCES service_route_schedules(id),
    rental_start_date   DATE,
    rental_end_date     DATE,
    -- Giá
    distance_km         NUMERIC(8,2),
    duration_min        INTEGER,
    estimated_fare      NUMERIC(18,2),           -- Giá tính theo công thức (mode = formula)
    driver_quoted_fare  NUMERIC(18,2),           -- Giá tài xế tự đặt (mode = driver_quote)
    quote_expires_at    TIMESTAMPTZ,             -- Deadline khách phải accept/reject
    customer_accepted_fare NUMERIC(18,2),        -- Giá cuối sau khi khách đồng ý
    final_fare          NUMERIC(18,2),           -- Giá thực tế khi hoàn thành
    -- Trạng thái
    status              VARCHAR(30) NOT NULL DEFAULT 'pending',
    cancelled_by        VARCHAR(20),             -- customer/provider/system
    cancel_reason       TEXT,
    -- Thời gian
    requested_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    driver_quoted_at    TIMESTAMPTZ,             -- Tài xế gửi báo giá lúc
    customer_decided_at TIMESTAMPTZ,             -- Khách accept/reject lúc
    accepted_at         TIMESTAMPTZ,
    arrived_at          TIMESTAMPTZ,
    started_at          TIMESTAMPTZ,
    completed_at        TIMESTAMPTZ,
    cancelled_at        TIMESTAMPTZ,
    -- Meta
    payment_method      VARCHAR(30),
    payment_status      VARCHAR(20) NOT NULL DEFAULT 'unpaid',
    notes               TEXT,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE booking_status_logs (
    id          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    booking_id  UUID        NOT NULL REFERENCES bookings(id) ON DELETE CASCADE,
    from_status VARCHAR(30),
    to_status   VARCHAR(30) NOT NULL,
    changed_by  UUID        REFERENCES users(id),
    note        TEXT,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

#### MODULE C — Customer Bookings

| # | Method | Path | Notes | Trạng thái |
|---|--------|------|-------|------------|
| BK1 | POST | `/api/v1/customer/bookings` | Tạo yêu cầu — response trả về `pricing_mode` để app biết chờ giá hay hiện ngay | TODO |
| BK2 | GET | `/api/v1/customer/bookings` | Lịch sử đặt xe | TODO |
| BK3 | GET | `/api/v1/customer/bookings/{id}` | Chi tiết chuyến — khi `status=driver_quoted` trả về `driver_quoted_fare` + `quote_expires_at` | TODO |
| BK4 | POST | `/api/v1/customer/bookings/{id}/accept-quote` | **[driver_quote]** Đồng ý giá tài xế đưa ra → `customer_accepted → arriving` | TODO |
| BK5 | POST | `/api/v1/customer/bookings/{id}/reject-quote` | **[driver_quote]** Từ chối giá → hệ thống tìm tài xế khác | TODO |
| BK6 | POST | `/api/v1/customer/bookings/{id}/cancel` | Hủy chuyến | TODO |
| BK7 | GET | `/api/v1/customer/bookings/{id}/track` | Theo dõi vị trí tài xế real-time (WS primary, REST poll fallback) | TODO |

#### MODULE P — Driver Bookings

| # | Method | Path | Notes | Trạng thái |
|---|--------|------|-------|------------|
| PBK1 | GET | `/api/v1/provider/bookings` | Danh sách chuyến | TODO |
| PBK2 | GET | `/api/v1/provider/bookings/{id}` | Chi tiết — khi `driver_quote` trả về `distance_km` và `min_quote/max_quote` để tài xế tham khảo | TODO |
| PBK3 | POST | `/api/v1/provider/bookings/{id}/accept` | **[formula]** Nhận chuyến trực tiếp | TODO |
| PBK4 | POST | `/api/v1/provider/bookings/{id}/reject` | Từ chối chuyến | TODO |
| PBK5 | POST | `/api/v1/provider/bookings/{id}/quote` | **[driver_quote]** Gửi báo giá cho khách — body: `{quoted_fare: 85000}` | TODO |
| PBK6 | PATCH | `/api/v1/provider/bookings/{id}/status` | `arriving → in_progress → completed` | TODO |
| PBK7 | POST | `/api/v1/provider/bookings/{id}/cancel` | Hủy chuyến (trước khi chạy) | TODO |

#### MODULE A — Admin Bookings

| # | Method | Path | Notes | Trạng thái |
|---|--------|------|-------|------------|
| ABK1 | GET | `/api/v1/admin/bookings` | Toàn bộ chuyến + filter (status, pricing_mode, service_type...) | TODO |
| ABK2 | GET | `/api/v1/admin/bookings/{id}` | Chi tiết + audit log đầy đủ | TODO |
| ABK3 | POST | `/api/v1/admin/bookings/{id}/cancel` | Hủy chuyến (can thiệp) | TODO |
| ABK4 | GET | `/api/v1/admin/bookings/stats` | Thống kê chuyến theo ngày/loại/pricing_mode | TODO |

---

### 7.4 — Safety Features & Disputes 🟠 SHOULD HAVE

**Bảng:** `booking_trip_shares`, `disputes`

#### OTP Xác nhận lên xe 🔴 MVP

> Khi tài xế chuyển sang `arrived`, hệ thống sinh mã OTP 4 số gửi push về app khách.  
> Tài xế nhập mã (khách đọc) → trip chuyển sang `in_progress`.  
> **Mục đích:** Tránh khách lên nhầm xe, tài xế giả mạo chuyến, tranh chấp "tôi không đi".

Field bổ sung vào bảng `bookings`:
```sql
boarding_otp          VARCHAR(6),      -- mã 4–6 số, sinh khi status → arrived
boarding_otp_expires  TIMESTAMPTZ,     -- hết hạn sau 10 phút
boarded_at            TIMESTAMPTZ,     -- timestamp khi OTP verify thành công
```

#### Chia sẻ hành trình 🟠 SHOULD HAVE

```sql
CREATE TABLE booking_trip_shares (
    id          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    booking_id  UUID        NOT NULL REFERENCES bookings(id) ON DELETE CASCADE,
    share_token VARCHAR(64) UNIQUE NOT NULL,  -- random token, không cần auth để xem
    expires_at  TIMESTAMPTZ NOT NULL,         -- hết hạn 24h sau khi tạo
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

#### Dispute / Khiếu nại 🟠 SHOULD HAVE

```sql
CREATE TABLE disputes (
    id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    booking_id      UUID        NOT NULL REFERENCES bookings(id),
    reported_by     UUID        NOT NULL REFERENCES users(id),
    against_id      UUID        REFERENCES users(id),    -- NULL nếu report sự cố chung
    type            VARCHAR(50) NOT NULL,
    -- wrong_fare / driver_behavior / vehicle_condition / safety / accident / other
    description     TEXT        NOT NULL,
    status          VARCHAR(30) NOT NULL DEFAULT 'open',
    -- open → investigating → resolved / dismissed
    resolution      TEXT,
    fare_adjustment NUMERIC(18,2),  -- điều chỉnh tiền hoàn nếu admin quyết định
    resolved_by     UUID        REFERENCES users(id),
    resolved_at     TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

#### MODULE C / P — Safety

| # | Method | Path | Notes | Trạng thái |
|---|--------|------|-------|------------|
| SF1 | POST | `/api/v1/customer/bookings/{id}/verify-boarding` | **🔴 MVP** Khách nhập OTP lên xe → trip sang `in_progress` | TODO |
| SF2 | POST | `/api/v1/customer/bookings/{id}/share-trip` | 🟠 Tạo link chia sẻ hành trình (expires 24h) | TODO |
| SF3 | GET | `/api/v1/track/{share_token}` | 🟠 Public — xem vị trí xe không cần auth | TODO |
| SF4 | POST | `/api/v1/customer/bookings/{id}/report` | 🟠 Báo cáo sự cố / tài xế | TODO |
| SF5 | POST | `/api/v1/provider/bookings/{id}/report` | 🟠 Tài xế báo cáo khách | TODO |
| SF6 | GET | `/api/v1/customer/disputes` | Lịch sử khiếu nại của tôi | TODO |
| SF7 | GET | `/api/v1/provider/disputes` | Khiếu nại liên quan đến tôi | TODO |

#### MODULE A — Dispute Management

| # | Method | Path | Notes | Trạng thái |
|---|--------|------|-------|------------|
| ADT1 | GET | `/api/v1/admin/disputes` | Queue khiếu nại + filter (status, type, date) | TODO |
| ADT2 | GET | `/api/v1/admin/disputes/{id}` | Chi tiết + booking + lịch sử status | TODO |
| ADT3 | POST | `/api/v1/admin/disputes/{id}/resolve` | Giải quyết + `fare_adjustment` nếu cần hoàn tiền | TODO |
| ADT4 | POST | `/api/v1/admin/disputes/{id}/dismiss` | Bác bỏ + ghi lý do | TODO |

---

## Phase 8 — API SPEC VER 5 (Payment & Wallet)

**Mục tiêu:** Thanh toán sau chuyến — ví in-app, cổng thanh toán (VNPay/MoMo), driver earnings, refund.  
**Bảng DB mới:** `wallets`, `wallet_transactions`, `payment_transactions`, `payment_methods`, `promotions`, `promotion_usages`

---

### 8.1 — Wallets

```sql
CREATE TABLE wallets (
    id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID        UNIQUE NOT NULL REFERENCES users(id),
    balance         NUMERIC(18,2) NOT NULL DEFAULT 0,
    currency        VARCHAR(10) NOT NULL DEFAULT 'VND',
    is_frozen       BOOLEAN NOT NULL DEFAULT false,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE wallet_transactions (
    id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    wallet_id       UUID        NOT NULL REFERENCES wallets(id),
    type            VARCHAR(30) NOT NULL, -- topup/payment/refund/withdrawal/earning/bonus
    amount          NUMERIC(18,2) NOT NULL, -- dương = credit, âm = debit
    balance_after   NUMERIC(18,2) NOT NULL,
    reference_id    UUID,                   -- booking_id hoặc payment_transaction_id
    reference_type  VARCHAR(50),
    description     TEXT,
    status          VARCHAR(20) NOT NULL DEFAULT 'completed',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

#### MODULE C — Customer Wallet

| # | Method | Path | Notes | Trạng thái |
|---|--------|------|-------|------------|
| W1 | GET | `/api/v1/customer/wallet` | Số dư + thông tin ví | TODO |
| W2 | GET | `/api/v1/customer/wallet/transactions` | Lịch sử giao dịch ví | TODO |
| W3 | POST | `/api/v1/customer/wallet/topup` | Nạp tiền → redirect cổng thanh toán | TODO |

#### MODULE P — Driver Wallet & Earnings

| # | Method | Path | Notes | Trạng thái |
|---|--------|------|-------|------------|
| PW1 | GET | `/api/v1/provider/wallet` | Số dư ví tài xế | TODO |
| PW2 | GET | `/api/v1/provider/wallet/transactions` | Lịch sử giao dịch | TODO |
| PW3 | GET | `/api/v1/provider/me/earnings` | Tổng thu nhập (hôm nay / tuần / tháng) | TODO |
| PW4 | GET | `/api/v1/provider/me/earnings/history` | Chi tiết theo ngày | TODO |
| PW5 | POST | `/api/v1/provider/wallet/withdraw` | Rút tiền về ngân hàng | TODO |

#### MODULE A — Admin Wallet & Finance

| # | Method | Path | Notes | Trạng thái |
|---|--------|------|-------|------------|
| AW1 | GET | `/api/v1/admin/wallets` | Danh sách ví | TODO |
| AW2 | GET | `/api/v1/admin/wallets/{user_id}` | Ví + lịch sử giao dịch của user | TODO |
| AW3 | POST | `/api/v1/admin/wallets/{user_id}/adjust` | Điều chỉnh số dư (bonus/phạt) | TODO |
| AW4 | GET | `/api/v1/admin/finance/revenue` | Doanh thu nền tảng theo ngày | TODO |
| AW5 | POST | `/api/v1/admin/withdrawals/{id}/approve` | Duyệt yêu cầu rút tiền | TODO |
| AW6 | POST | `/api/v1/admin/withdrawals/{id}/reject` | Từ chối yêu cầu rút tiền | TODO |

---

### 8.2 — Payment Transactions (cổng thanh toán)

```sql
CREATE TABLE payment_transactions (
    id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    booking_id      UUID        NOT NULL REFERENCES bookings(id),
    user_id         UUID        NOT NULL REFERENCES users(id),
    amount          NUMERIC(18,2) NOT NULL,
    method          VARCHAR(30) NOT NULL,  -- cash/wallet/vnpay/momo/zalopay
    gateway_ref     VARCHAR(200),          -- mã giao dịch từ cổng
    status          VARCHAR(20) NOT NULL DEFAULT 'pending',
    -- pending → completed / failed / refunded
    paid_at         TIMESTAMPTZ,
    refunded_at     TIMESTAMPTZ,
    refund_amount   NUMERIC(18,2),
    metadata        JSONB,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

#### MODULE — Payment Callbacks

| # | Method | Path | Notes | Trạng thái |
|---|--------|------|-------|------------|
| PAY1 | POST | `/api/v1/internal/payments/vnpay/callback` | IPN webhook từ VNPay | TODO |
| PAY2 | POST | `/api/v1/internal/payments/momo/callback` | IPN webhook từ MoMo | TODO |
| PAY3 | POST | `/api/v1/internal/payments/zalopay/callback` | IPN webhook từ ZaloPay | TODO |
| PAY4 | POST | `/api/v1/customer/bookings/{id}/payment/retry` | Thử thanh toán lại | TODO |

---

### 8.3 — Promotions & Vouchers

```sql
CREATE TABLE promotions (
    id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    code            VARCHAR(50) UNIQUE NOT NULL,
    name            VARCHAR(200) NOT NULL,
    type            VARCHAR(30) NOT NULL,  -- percent/fixed/free_trip
    value           NUMERIC(18,2) NOT NULL,
    max_discount    NUMERIC(18,2),
    min_fare        NUMERIC(18,2),
    usage_limit     INTEGER,
    used_count      INTEGER NOT NULL DEFAULT 0,
    per_user_limit  INTEGER DEFAULT 1,
    valid_from      TIMESTAMPTZ NOT NULL,
    valid_to        TIMESTAMPTZ NOT NULL,
    service_types   JSONB,                 -- NULL = áp dụng tất cả
    is_active       BOOLEAN NOT NULL DEFAULT true,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE promotion_usages (
    id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    promotion_id    UUID        NOT NULL REFERENCES promotions(id),
    user_id         UUID        NOT NULL REFERENCES users(id),
    booking_id      UUID        NOT NULL REFERENCES bookings(id),
    discount_amount NUMERIC(18,2) NOT NULL,
    used_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (promotion_id, booking_id)
);
```

#### MODULE C — Customer Promotions

| # | Method | Path | Notes | Trạng thái |
|---|--------|------|-------|------------|
| PM1 | POST | `/api/v1/customer/promotions/validate` | Kiểm tra mã giảm giá | TODO |
| PM2 | GET | `/api/v1/customer/promotions` | Danh sách khuyến mãi đang áp dụng được | TODO |

#### MODULE A — Admin Promotions

| # | Method | Path | Notes | Trạng thái |
|---|--------|------|-------|------------|
| APM1 | GET | `/api/v1/admin/promotions` | Danh sách khuyến mãi | TODO |
| APM2 | POST | `/api/v1/admin/promotions` | Tạo chương trình khuyến mãi | TODO |
| APM3 | PUT | `/api/v1/admin/promotions/{id}` | Cập nhật | TODO |
| APM4 | PATCH | `/api/v1/admin/promotions/{id}/status` | Bật / tắt | TODO |
| APM5 | GET | `/api/v1/admin/promotions/{id}/usages` | Xem ai đã dùng | TODO |

---

## Phase 9 — API SPEC VER 6 (Rating, Notifications & Analytics)

**Mục tiêu:** Hoàn thiện trải nghiệm sau chuyến — đánh giá 2 chiều, push notification, dashboard analytics cho admin.  
**Bảng DB mới:** `reviews`, `notifications`, `notification_settings`

---

### 9.1 — Rating & Reviews

```sql
CREATE TABLE reviews (
    id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    booking_id      UUID        NOT NULL REFERENCES bookings(id) ON DELETE CASCADE,
    reviewer_id     UUID        NOT NULL REFERENCES users(id),
    reviewee_id     UUID        NOT NULL REFERENCES users(id),
    reviewer_role   VARCHAR(20) NOT NULL, -- customer / provider
    rating          SMALLINT    NOT NULL CHECK (rating BETWEEN 1 AND 5),
    comment         TEXT,
    is_visible      BOOLEAN NOT NULL DEFAULT true,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (booking_id, reviewer_id)
);
```

#### MODULE C — Customer Reviews

| # | Method | Path | Notes | Trạng thái |
|---|--------|------|-------|------------|
| RV1 | POST | `/api/v1/customer/bookings/{id}/review` | Đánh giá tài xế sau chuyến | TODO |
| RV2 | GET | `/api/v1/customer/providers/{id}/reviews` | Xem đánh giá của provider | TODO |

#### MODULE P — Driver Reviews

| # | Method | Path | Notes | Trạng thái |
|---|--------|------|-------|------------|
| PRV1 | POST | `/api/v1/provider/bookings/{id}/review` | Đánh giá khách sau chuyến | TODO |
| PRV2 | GET | `/api/v1/provider/me/reviews` | Xem đánh giá mình nhận được | TODO |

#### MODULE A — Admin Reviews

| # | Method | Path | Notes | Trạng thái |
|---|--------|------|-------|------------|
| ARV1 | GET | `/api/v1/admin/reviews` | Toàn bộ đánh giá + filter | TODO |
| ARV2 | PATCH | `/api/v1/admin/reviews/{id}/visibility` | Ẩn/hiện đánh giá vi phạm | TODO |

---

### 9.2 — Notifications

```sql
CREATE TABLE notifications (
    id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID        NOT NULL REFERENCES users(id),
    type            VARCHAR(50) NOT NULL,  -- booking_accepted/trip_completed/payment_received/...
    title           VARCHAR(200) NOT NULL,
    body            TEXT,
    data            JSONB,                 -- deep link, booking_id, ...
    is_read         BOOLEAN NOT NULL DEFAULT false,
    read_at         TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

#### MODULE — Notifications (Common cho cả Customer và Driver)

| # | Method | Path | Notes | Trạng thái |
|---|--------|------|-------|------------|
| NF1 | GET | `/api/v1/common/me/notifications` | Danh sách thông báo | TODO |
| NF2 | PATCH | `/api/v1/common/me/notifications/{id}/read` | Đánh dấu đã đọc | TODO |
| NF3 | POST | `/api/v1/common/me/notifications/read-all` | Đánh dấu tất cả đã đọc | TODO |
| NF4 | GET | `/api/v1/common/me/notifications/unread-count` | Số thông báo chưa đọc (badge) | TODO |
| NF5 | POST | `/api/v1/common/me/device-tokens` | Đăng ký FCM token thiết bị | TODO |
| NF6 | DELETE | `/api/v1/common/me/device-tokens/{token}` | Xóa FCM token (logout) | TODO |

#### MODULE A — Admin Push Notification

| # | Method | Path | Notes | Trạng thái |
|---|--------|------|-------|------------|
| ANF1 | POST | `/api/v1/admin/notifications/broadcast` | Gửi thông báo hàng loạt | TODO |

---

### 9.3 — Analytics Dashboard (Admin)

> Không cần bảng mới — aggregate từ dữ liệu hiện có.

| # | Method | Path | Notes | Trạng thái |
|---|--------|------|-------|------------|
| AN1 | GET | `/api/v1/admin/analytics/overview` | KPI tổng: chuyến/ngày, doanh thu, user active | TODO |
| AN2 | GET | `/api/v1/admin/analytics/bookings` | Chuyến theo ngày/tuần/tháng + tỷ lệ hoàn thành | TODO |
| AN3 | GET | `/api/v1/admin/analytics/revenue` | Doanh thu nền tảng theo kỳ | TODO |
| AN4 | GET | `/api/v1/admin/analytics/drivers` | Top tài xế: số chuyến, rating, doanh thu | TODO |
| AN5 | GET | `/api/v1/admin/analytics/customers` | Khách hàng mới vs quay lại | TODO |
| AN6 | GET | `/api/v1/admin/analytics/heatmap` | Khu vực đặt xe nhiều nhất (lat/lng aggregation) | TODO |

---

## Tổng quan kiến trúc (XanhSM model)

```
┌─────────────────────────────────────────────────────┐
│                   CLIENT LAYER                       │
│  Customer App    Driver App (Provider)    Admin CMS  │
└─────┬─────────────┬───────────────┬─────────────┬──────┘
      │ REST          │ WebSocket       │ REST          │
      │ (HTTPS)       │ (WSS)           │ (HTTPS)       │
      ▼               ▼                 ▼               ▼
┌────────────────────────┐ ┌────────────────────────┐
│   FastAPI REST (port 8000)  │ │   WS Server (port 8001)    │
│   /auth  /common           │ │   /ws/booking/{id}         │
│   /customer  /provider     │ │   /ws/chat/{id}            │
│   /admin  /internal        │ │   /ws/driver-location/{id} │
│   (stateless, scale ∞)     │ │   (stateful, persistent)   │
└───────────┬────────────┘ └───────────┬────────────┘
            │                           │
            └───────────┬───────────┘
                        │
            ┌───────────┼───────────────┐
            ▼           ▼               ▼
      PostgreSQL      Redis         FCM / Push
    (main data +   (pub/sub,      (offline fallback)
     chat_msgs)    driver loc,
                   presence,
                   msg cache)
```

**Tách REST vs WS:**
- **REST API (port 8000):** request-response, stateless, auto-scale horizontal, dùng cho tất cả CRUD + business logic
- **WS Server (port 8001):** persistent connection, stateful (room per booking), scale bằng Redis Pub/Sub fanout
- **Giao tiếp REST → WS:** khi REST API thay đổi booking status, PUBLISH lên Redis channel → WS Server broadcast đến client

**Real-time Driver Location:** Nên dùng Redis HSET để cập nhật `{provider_id} → {lat, lng, updated_at}` liên tục từ Driver App. PostgreSQL `driver_locations` chỉ dùng làm fallback/snapshot.

**Booking matching flow:**
```
POST /customer/bookings
  → Hệ thống tìm driver online gần nhất (Redis)
  → Gửi push notification đến driver
  → Driver có 30s để accept/reject
  → Nếu reject/timeout → tìm driver kế tiếp
  → booking.status: pending → searching → accepted
```

---

*Có thể chỉnh sửa theo tiến độ; mỗi lần thêm bảng migration nên cập nhật tài liệu.*

---

## Phase 10A — App Store Compliance (Tránh bị reject)

> **Mục tiêu:** Đáp ứng đủ điều kiện submit lên Apple App Store và Google Play mà không bị reject.  
> Đây là các yêu cầu kỹ thuật từ chính sách của Apple/Google — **không phải tính năng tùy chọn**.

---

### Lý do reject phổ biến nhất

| # | Lý do | Store | Guideline | Hậu quả nếu thiếu |
|---|---|---|---|---|
| 1 | Có Zalo/Google Login nhưng **không có Sign in with Apple** | Apple | Rule 4.8 | **Reject ngay, không ngoại lệ** |
| 2 | **Không có nút xóa tài khoản** trong app | Apple + Google | Apple 5.1.1(v) | Reject từ 6/2022 trở đi |
| 3 | **Không khai báo Data Safety** đầy đủ | Google Play | GDPR/PDPA | Warning → Suspend app |
| 4 | Background location không có lý do rõ ràng | Apple | 5.1.5 | Reject (driver app cần always-on location) |
| 5 | Không có **Privacy Policy URL** trong app | Apple + Google | 5.1.1 | Reject |
| 6 | App không có test account cho reviewer | Apple | 2.1 | Stuck in review / Reject |
| 7 | SMS/OTP permission không được khai báo | Google Play | Permissions policy | Reject nếu dùng SMS API |
| 8 | Consent chưa được ghi nhận rõ trước khi collect location | Cả 2 | App privacy | Reject hoặc privacy report |

> **Driver app đặc biệt:** Background location (`NSLocationAlwaysAndWhenInUseUsageDescription`) cần mô tả "tài xế cần tracking liên tục khi đang nhận chuyến". Thiếu → Apple reject.

---

### Bảng DB mới

```sql
-- Ghi nhận mỗi hành động consent của user (audit trail)
CREATE TABLE consent_logs (
    id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID        NOT NULL REFERENCES users(id),
    consent_type    VARCHAR(50) NOT NULL,
    -- terms_of_service / privacy_policy / marketing_email / marketing_push
    -- location_tracking / data_sharing / cookie
    action          VARCHAR(20) NOT NULL,   -- granted / revoked
    version         VARCHAR(20),            -- version policy đang áp dụng (e.g. "2026-04")
    ip_address      VARCHAR(50),
    user_agent      TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Yêu cầu xóa tài khoản — hàng đợi xử lý có audit
CREATE TABLE data_deletion_requests (
    id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID        NOT NULL REFERENCES users(id),
    status          VARCHAR(30) NOT NULL DEFAULT 'pending',
    -- pending → processing → completed / cancelled
    reason          TEXT,                   -- tùy chọn user ghi lý do
    requested_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    scheduled_delete_at TIMESTAMPTZ,        -- xóa sau 30 ngày (grace period)
    processed_at    TIMESTAMPTZ,
    processed_by    UUID        REFERENCES users(id)  -- admin thực hiện xóa
);
```

---

### MODULE A — Auth (bổ sung Sign in with Apple)

| # | Method | Path | Notes | Trạng thái |
|---|--------|------|-------|------------|
| 0c | POST | `/api/v1/auth/login/apple` | **🔴 BẮT BUỘC** nếu app có Zalo/Google Login (Apple Rule 4.8) | TODO |

**Logic Sign in with Apple:**
- Client gửi `identity_token` (JWT từ Apple SDK)
- Server verify signature với Apple public keys (`https://appleid.apple.com/auth/keys`)
- Lấy `sub` (Apple User ID, stable), `email` (chỉ gửi lần đầu), `name`
- Upsert user bằng `apple_sub` unique field trong bảng `users`

---

### MODULE A — Common (Account Self-Service)

> Tất cả endpoint dưới đây phải hiển thị **trong app** (không chỉ qua email/support) — đây là yêu cầu bắt buộc.

| # | Method | Path | Notes | Trạng thái |
|---|--------|------|-------|------------|
| 13 | DELETE | `/api/v1/common/me` | **🔴 BẮT BUỘC** — submit request xóa → grace period 30 ngày → xóa thật | TODO |
| 14 | POST | `/api/v1/common/me/deactivate` | Tạm khoá tài khoản (không nhìn thấy app, không xóa data) | TODO |
| 15 | GET | `/api/v1/common/me/data-export` | Xuất toàn bộ dữ liệu cá nhân (JSON/ZIP) — PDPA NĐ13/2023 | TODO |
| 16 | GET | `/api/v1/common/me/consents` | Xem trạng thái consent hiện tại theo từng `consent_type` | TODO |
| 17 | POST | `/api/v1/common/me/consents` | Ghi nhận consent — body: `{type, action, version}` | TODO |
| 18 | POST | `/api/v1/common/me/consents/withdraw` | Thu hồi consent marketing (terms/privacy không được rút) | TODO |

**Luồng xóa tài khoản (Account Deletion Flow):**
```
1. User bấm "Xóa tài khoản" trong app
2. POST DELETE /common/me   → tạo data_deletion_request, status=pending
3. Email xác nhận gửi về user + thông báo "tài khoản sẽ bị xóa sau 30 ngày"
4. User có thể cancel trong 30 ngày (POST /common/me/cancel-deletion)
5. Sau 30 ngày: cron job anonymize/xóa data (cascade toàn bộ bảng liên quan)
6. Driver app: nếu đang có booking active → từ chối xóa, hướng dẫn hoàn thành chuyến trước
```

**Ghi chú pháp lý:**
- Apple yêu cầu xóa phải xảy ra **trong app** — không được chuyển sang email/support
- Dữ liệu giao dịch (bookings, payments) cần giữ lại theo luật thuế VN (5 năm), nhưng phải **anonymize** (xóa PII: tên, SĐT, địa chỉ)

---

### MODULE A — Admin (Data Deletion Queue)

| # | Method | Path | Notes | Trạng thái |
|---|--------|------|-------|------------|
| ADL1 | GET | `/api/v1/admin/data-deletion-requests` | Queue yêu cầu xóa tài khoản + filter | TODO |
| ADL2 | POST | `/api/v1/admin/data-deletion-requests/{id}/process` | Thực thi xóa (anonymize PII) | TODO |
| ADL3 | POST | `/api/v1/admin/data-deletion-requests/{id}/cancel` | Hủy nếu user cancel trong grace period | TODO |
| ADL4 | GET | `/api/v1/admin/consent-logs` | Audit trail toàn bộ consent actions | TODO |

---

### Checklist submit App Store

**Trước khi submit:**
- [ ] Privacy Policy URL hoạt động (đặt trong app Settings + App Store listing)
- [ ] Terms of Service URL hoạt động
- [ ] Sign in with Apple đã implement và test
- [ ] Nút "Xóa tài khoản" dễ tìm trong Profile/Settings (không được ẩn > 2 tap)
- [ ] `NSLocationWhenInUseUsageDescription` — customer app
- [ ] `NSLocationAlwaysAndWhenInUseUsageDescription` — driver app (justify rõ)
- [ ] `NSCameraUsageDescription` — eKYC / upload documents
- [ ] `NSPhotoLibraryUsageDescription` — upload ảnh
- [ ] `NSUserNotificationsUsageDescription` — push notification
- [ ] App Store Connect → App Privacy → khai báo đầy đủ (location, contact info, identifiers, usage data)
- [ ] Google Play → Data Safety → khai báo đầy đủ
- [ ] Test account cho reviewer (ghi vào App Review Notes + demo ảnh/video)
- [ ] App không crash khi chạy trên iOS 16+ và Android 10+

---

## Phase 10B — CRM Integration

> **Mục tiêu:** Admin có đủ công cụ để quản lý quan hệ khách hàng — hỗ trợ (support), phân nhóm, ghi chú, và broadcast có target.  
> Kết hợp với Phase 9.2 (Notifications broadcast) để thành hệ thống CRM đầy đủ.

---

### Bảng DB mới

```sql
-- Tag / segment user (admin gán)
CREATE TABLE user_tags (
    id          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID        NOT NULL REFERENCES users(id),
    tag         VARCHAR(50) NOT NULL,
    -- vip / churned / new / flagged / corporate / driver_top / inactive_30d / ...
    created_by  UUID        REFERENCES users(id),
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (user_id, tag)
);

-- Ghi chú nội bộ của admin về user
CREATE TABLE user_notes (
    id          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID        NOT NULL REFERENCES users(id),
    note        TEXT        NOT NULL,
    is_pinned   BOOLEAN     NOT NULL DEFAULT false,
    created_by  UUID        NOT NULL REFERENCES users(id),
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Support ticket từ customer (tổng quát, không chỉ về booking)
CREATE TABLE support_tickets (
    id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID        NOT NULL REFERENCES users(id),
    booking_id      UUID        REFERENCES bookings(id),  -- tùy chọn, nếu liên quan booking
    subject         VARCHAR(200) NOT NULL,
    category        VARCHAR(50) NOT NULL,
    -- account / billing / app_bug / driver_issue / payment / general
    status          VARCHAR(30) NOT NULL DEFAULT 'open',
    -- open → assigned → in_progress → waiting_user → resolved / closed
    priority        VARCHAR(20) NOT NULL DEFAULT 'normal',  -- low / normal / high / urgent
    assigned_to     UUID        REFERENCES users(id),       -- admin/agent nhận ticket
    first_response_at TIMESTAMPTZ,                         -- SLA tracking: phản hồi đầu tiên
    resolved_at     TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE support_ticket_messages (
    id          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    ticket_id   UUID        NOT NULL REFERENCES support_tickets(id) ON DELETE CASCADE,
    sender_id   UUID        NOT NULL REFERENCES users(id),
    message     TEXT        NOT NULL,
    attachments JSONB,      -- [{url, type, name}]
    is_internal BOOLEAN     NOT NULL DEFAULT false,  -- internal note chỉ admin thấy
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Campaign notification có target segment
CREATE TABLE notification_campaigns (
    id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    name            VARCHAR(200) NOT NULL,
    -- Target audience
    target_roles    JSONB,      -- ["customer"] / ["provider"] / ["customer","provider"]
    target_tags     JSONB,      -- ["vip","new"] — NULL = tất cả tags
    target_filter   JSONB,
    -- {last_active_days: 30, min_bookings: 1, service_type: "taxi"}
    -- Channel + content
    channel         VARCHAR(30) NOT NULL DEFAULT 'push',  -- push / zalo_oa / sms / email
    title           VARCHAR(200) NOT NULL,
    body            TEXT        NOT NULL,
    deep_link       VARCHAR(500),   -- URL scheme: app://bookings hoặc web URL
    -- Scheduling
    status          VARCHAR(30) NOT NULL DEFAULT 'draft',
    -- draft → scheduled → sending → sent / failed
    scheduled_at    TIMESTAMPTZ,
    sent_at         TIMESTAMPTZ,
    -- Stats
    target_count    INTEGER     DEFAULT 0,
    sent_count      INTEGER     DEFAULT 0,
    opened_count    INTEGER     DEFAULT 0,
    created_by      UUID        REFERENCES users(id),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

---

### MODULE C — Customer Support

| # | Method | Path | Notes | Trạng thái |
|---|--------|------|-------|------------|
| ST1 | POST | `/api/v1/customer/support/tickets` | Tạo ticket — body: `{subject, category, message, booking_id?}` | TODO |
| ST2 | GET | `/api/v1/customer/support/tickets` | Danh sách ticket của tôi | TODO |
| ST3 | GET | `/api/v1/customer/support/tickets/{id}` | Chi tiết ticket + messages | TODO |
| ST4 | POST | `/api/v1/customer/support/tickets/{id}/messages` | Gửi tin nhắn (reply) | TODO |
| ST5 | POST | `/api/v1/customer/support/tickets/{id}/close` | User đóng ticket khi đã giải quyết | TODO |

---

### MODULE P — Provider Support

| # | Method | Path | Notes | Trạng thái |
|---|--------|------|-------|------------|
| PST1 | POST | `/api/v1/provider/support/tickets` | Tài xế tạo ticket | TODO |
| PST2 | GET | `/api/v1/provider/support/tickets` | Danh sách ticket | TODO |
| PST3 | GET | `/api/v1/provider/support/tickets/{id}` | Chi tiết + messages | TODO |
| PST4 | POST | `/api/v1/provider/support/tickets/{id}/messages` | Gửi tin nhắn | TODO |

---

### MODULE A — Admin CRM

#### Customer 360 View

| # | Method | Path | Notes | Trạng thái |
|---|--------|------|-------|------------|
| CR1 | GET | `/api/v1/admin/crm/customers` | Danh sách + filter (tag, role, last_booking, booking_count) | TODO |
| CR2 | GET | `/api/v1/admin/crm/customers/{id}/timeline` | Timeline đầy đủ: đăng ký → bookings → disputes → notes → tickets | TODO |
| CR3 | GET | `/api/v1/admin/crm/customers/{id}/stats` | Tổng chuyến, tổng chi tiêu, rating trung bình, churn risk | TODO |

#### Tags & Notes

| # | Method | Path | Notes | Trạng thái |
|---|--------|------|-------|------------|
| CR4 | GET | `/api/v1/admin/crm/customers/{id}/tags` | Danh sách tag của user | TODO |
| CR5 | POST | `/api/v1/admin/crm/customers/{id}/tags` | Thêm tag — body: `{tag: "vip"}` | TODO |
| CR6 | DELETE | `/api/v1/admin/crm/customers/{id}/tags/{tag}` | Xóa tag | TODO |
| CR7 | GET | `/api/v1/admin/crm/customers/{id}/notes` | Danh sách ghi chú nội bộ | TODO |
| CR8 | POST | `/api/v1/admin/crm/customers/{id}/notes` | Thêm ghi chú | TODO |
| CR9 | PUT | `/api/v1/admin/crm/customers/{id}/notes/{note_id}` | Sửa ghi chú | TODO |
| CR10 | DELETE | `/api/v1/admin/crm/customers/{id}/notes/{note_id}` | Xóa ghi chú | TODO |

#### Support Ticket Console

| # | Method | Path | Notes | Trạng thái |
|---|--------|------|-------|------------|
| AST1 | GET | `/api/v1/admin/support/tickets` | Queue tickets + filter (status, priority, category, assigned_to) | TODO |
| AST2 | GET | `/api/v1/admin/support/tickets/{id}` | Chi tiết ticket + messages (bao gồm internal notes) | TODO |
| AST3 | POST | `/api/v1/admin/support/tickets/{id}/messages` | Reply = gửi tin nhắn (có thể mark `is_internal=true`) | TODO |
| AST4 | PATCH | `/api/v1/admin/support/tickets/{id}/status` | Cập nhật status: assigned/in_progress/resolved/closed | TODO |
| AST5 | POST | `/api/v1/admin/support/tickets/{id}/assign` | Giao ticket cho agent — body: `{agent_id}` | TODO |
| AST6 | GET | `/api/v1/admin/support/stats` | SLA report: avg first response time, resolution time, open count | TODO |

#### Campaign Management (Targeted Broadcast)

| # | Method | Path | Notes | Trạng thái |
|---|--------|------|-------|------------|
| CAM1 | GET | `/api/v1/admin/campaigns` | Danh sách campaign + trạng thái + stats | TODO |
| CAM2 | POST | `/api/v1/admin/campaigns` | Tạo campaign (draft) — set target_roles, target_tags, channel, content | TODO |
| CAM3 | PUT | `/api/v1/admin/campaigns/{id}` | Cập nhật campaign (chỉ khi status=draft) | TODO |
| CAM4 | POST | `/api/v1/admin/campaigns/{id}/preview` | Ước tính số người nhận trước khi gửi | TODO |
| CAM5 | POST | `/api/v1/admin/campaigns/{id}/send` | Trigger gửi ngay (hoặc schedule) | TODO |
| CAM6 | GET | `/api/v1/admin/campaigns/{id}/stats` | Delivery stats: sent/opened/failed | TODO |

---

### Tích hợp CRM với các Phase khác

```
Phase 9.2 notifications broadcast (ANF1)
    → Upgrade thành campaign có target segment (CAM2-6)

Phase 7.4 disputes
    → Sau khi resolve dispute → tự động tạo support ticket nếu user chọn "escalate"
    → Admin dispute console link sang CRM customer timeline

Phase 8.1 wallets
    → Điều chỉnh số dư (AW3) → ghi nhận tự động vào CRM timeline

Phase 9.3 analytics
    → AN5 "customers new vs returning" → feed data cho CRM segment filter
    → Churn risk score (last booking > 30 ngày) → auto-tag "inactive_30d"
```

---

### Auto-tagging Rules (chạy bằng cron hoặc trigger)

| Rule | Điều kiện | Tag được gán |
|---|---|---|
| New user | Đăng ký < 7 ngày | `new` |
| Active driver | Hoàn thành ≥ 50 chuyến + rating ≥ 4.5 | `driver_top` |
| VIP customer | Chi tiêu tích lũy ≥ 5.000.000đ | `vip` |
| At-risk | Từng đặt xe nhưng không hoạt động 30 ngày | `inactive_30d` |
| Churned | Không hoạt động 90 ngày | `churned` |
| Flagged | Có dispute hoặc report chưa giải quyết | `flagged` |

> Auto-tag chạy qua cron job hàng đêm. Admin vẫn có thể gán/xóa thủ công bất kỳ lúc nào.

---

## Phase 11 — WebSocket Server & Real-time Chat

> **Mục tiêu:** Build **WebSocket server riêng** (tách khỏi FastAPI REST) để phục vụ 3 luồng real-time:  
> 1. **In-trip chat** giữa khách và tài xế  
> 2. **Booking events** push real-time (status change, driver location)  
> 3. **Presence** (ai đang online)  
>  
> **Vì sao tách riêng?**  
> - REST API (FastAPI) xử lý request-response, load balancing dễ (stateless)  
> - WS cần persistent connection, stateful, scale khác (ít instance nhưng nhiều concurrent connections)  
> - Tách để deploy/scale độc lập — WS server crash không ảnh hưởng REST API  
> - Dùng Redis Pub/Sub để fanout message giữa các WS instance

---

### Stack WebSocket Server

| Thành phần | Gợi ý | Lý do |
|---|---|---|
| Runtime | **Python + FastAPI WebSocket** hoặc **Node.js + Socket.IO** | FastAPI hỗ trợ WS native; Socket.IO mature hơn ở WS |
| Transport | **WebSocket** (primary) + **HTTP long-poll** (fallback cho mạng yếu) | App mobile VN hay bị 3G yếu, cần fallback |
| Pub/Sub | **Redis Pub/Sub** | Fanout message giữa nhiều WS instance |
| Message Store | **PostgreSQL** (chat_messages) + **Redis** (last N messages cache) | Persistent + fast recent fetch |
| Auth | **JWT** (cùng token với REST API) | Gửi token khi connect: `ws://host?token=xxx` |
| Protocol | JSON messages qua WS frames | Đơn giản, debug dễ |

---

### Kiến trúc WS Server

```
┌──────────────────────────────────────────────────────────┐
│                     CLIENT LAYER                          │
│  Customer App ◄──► WS    Driver App ◄──► WS    Admin CMS │
└───────┬───────────────────────┬──────────────────────────┘
        │                       │
        ▼                       ▼
┌──────────────────────────────────────────────────────────┐
│              WS SERVER (port 8001)                         │
│  ws://host/ws?token=xxx                                   │
│                                                           │
│  Handlers:                                                │
│    /ws/booking/{booking_id}   ← booking events room       │
│    /ws/chat/{booking_id}      ← in-trip chat room         │
│    /ws/driver-location/{booking_id} ← live GPS stream     │
│                                                           │
│  Auth: verify JWT → extract user_id + role                │
│  Room: mỗi booking = 1 room (customer + driver)          │
│  Redis Pub/Sub: channel = booking:{booking_id}            │
└───────────────────────┬──────────────────────────────────┘
                        │
            ┌───────────┼───────────────┐
            ▼           ▼               ▼
      PostgreSQL      Redis         FCM (offline push)
    (chat_messages)  (pub/sub,     (khi user không
                     presence,      connect WS thì
                     msg cache)     gửi FCM thay)
```

**Khi REST API thay đổi booking status:**
```
FastAPI: PATCH /provider/bookings/{id}/status → arriving
  → INSERT booking_status_logs
  → PUBLISH Redis channel "booking:{booking_id}" → {type: "status_changed", status: "arriving"}
  → WS Server nhận message → broadcast đến client trong room
  → Nếu client không connected → FCM fallback push
```

---

### Bảng DB mới

```sql
-- Tin nhắn chat trong chuyến (customer ↔ driver)
CREATE TABLE chat_conversations (
    id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    booking_id      UUID        NOT NULL REFERENCES bookings(id) ON DELETE CASCADE,
    customer_id     UUID        NOT NULL REFERENCES users(id),
    provider_id     UUID        NOT NULL REFERENCES users(id),
    status          VARCHAR(20) NOT NULL DEFAULT 'active',
    -- active: đang trong chuyến, closed: chuyến kết thúc, archived: >30 ngày
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    closed_at       TIMESTAMPTZ,
    UNIQUE (booking_id)  -- 1 booking = 1 conversation
);

CREATE TABLE chat_messages (
    id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID        NOT NULL REFERENCES chat_conversations(id) ON DELETE CASCADE,
    sender_id       UUID        NOT NULL REFERENCES users(id),
    message_type    VARCHAR(20) NOT NULL DEFAULT 'text',
    -- text / image / location / system
    content         TEXT        NOT NULL,
    metadata        JSONB,
    -- image: {url, thumbnail_url, width, height}
    -- location: {lat, lng, address}
    -- system: {event: "driver_arrived", booking_id: "..."}
    is_read         BOOLEAN     NOT NULL DEFAULT false,
    read_at         TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_chat_messages_conversation_created 
    ON chat_messages(conversation_id, created_at DESC);

-- Tracking online presence (WS connection state)
CREATE TABLE user_presence (
    user_id         UUID        PRIMARY KEY REFERENCES users(id),
    is_online       BOOLEAN     NOT NULL DEFAULT false,
    last_seen_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    connected_device VARCHAR(50),  -- ios / android / web
    ws_instance_id  VARCHAR(100), -- WS server instance đang handle
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

---

### WS Message Protocol

**Connection:**
```
ws://ws.sandichvu.vn/ws?token=<JWT_ACCESS_TOKEN>
```

**Message format (JSON):**
```json
{
  "type": "chat_message | typing | read_receipt | booking_event | location_update | presence",
  "booking_id": "uuid",
  "payload": { ... }
}
```

#### Event Types (Server → Client)

| Type | Payload | Khi nào |
|---|---|---|
| `booking_status` | `{booking_id, status, provider_id, vehicle_info}` | Mỗi khi status booking thay đổi |
| `driver_location` | `{lat, lng, heading, speed_kmh, eta_min}` | Mỗi 3-5s khi trip đang chạy |
| `chat_message` | `{message_id, sender_id, content, type, created_at}` | Tin nhắn mới |
| `typing` | `{booking_id, user_id, is_typing}` | User đang gõ |
| `read_receipt` | `{message_id, reader_id, read_at}` | Tin nhắn đã đọc |
| `boarding_otp` | `{booking_id, otp}` | OTP sinh khi driver arrived (push về customer) |
| `quote_received` | `{booking_id, quoted_fare, expires_at}` | Driver gửi báo giá (driver_quote mode) |
| `driver_assigned` | `{booking_id, driver_name, vehicle_plate, vehicle_model, rating}` | Tài xế nhận chuyến |
| `trip_completed` | `{booking_id, final_fare, payment_method, can_review}` | Chuyến hoàn thành |
| `presence` | `{user_id, is_online, last_seen_at}` | Trạng thái online |

#### Event Types (Client → Server)

| Type | Payload | Ghi chú |
|---|---|---|
| `join_booking` | `{booking_id}` | Join room lắng nghe events của booking |
| `leave_booking` | `{booking_id}` | Rời room |
| `chat_send` | `{booking_id, content, message_type}` | Gửi tin nhắn |
| `chat_typing` | `{booking_id, is_typing}` | Đang gõ indicator |
| `chat_read` | `{message_id}` | Đánh dấu đã đọc |
| `location_update` | `{lat, lng, heading, speed_kmh}` | Driver gửi GPS (thay HTTP nếu WS connected) |

---

### REST API bổ sung (Chat history — qua FastAPI, không qua WS)

#### MODULE C — Customer Chat

| # | Method | Path | Notes | Trạng thái |
|---|--------|------|-------|------------|
| CH1 | GET | `/api/v1/customer/bookings/{id}/messages` | Lịch sử chat (paginate) — load khi mở lại app | TODO |
| CH2 | POST | `/api/v1/customer/bookings/{id}/messages` | Gửi tin nhắn qua REST (fallback khi WS bị mất kết nối) | TODO |
| CH3 | POST | `/api/v1/customer/bookings/{id}/messages/read-all` | Đánh dấu tất cả đã đọc | TODO |

#### MODULE P — Driver Chat

| # | Method | Path | Notes | Trạng thái |
|---|--------|------|-------|------------|
| PCH1 | GET | `/api/v1/provider/bookings/{id}/messages` | Lịch sử chat | TODO |
| PCH2 | POST | `/api/v1/provider/bookings/{id}/messages` | Gửi tin nhắn fallback | TODO |
| PCH3 | POST | `/api/v1/provider/bookings/{id}/messages/read-all` | Đánh dấu đã đọc | TODO |

#### MODULE A — Admin Chat Monitoring

| # | Method | Path | Notes | Trạng thái |
|---|--------|------|-------|------------|
| ACH1 | GET | `/api/v1/admin/bookings/{id}/messages` | Xem toàn bộ chat (dispute investigation) | TODO |
| ACH2 | GET | `/api/v1/admin/chat/flagged` | Tin nhắn bị AI/keyword flag (safety monitoring) | TODO |

---

### Cấu trúc thư mục WS Server

```text
ws-server/
  app/
    main.py                 # WebSocket app entry point
    core/
      config.py             # WS_PORT, REDIS_URL, JWT_SECRET (shared with REST)
      auth.py               # JWT verify (shared logic)
    handlers/
      chat.py               # In-trip chat handler
      booking_events.py     # Booking status + driver location broadcast
      presence.py           # Online/offline tracking
    services/
      redis_pubsub.py       # Redis subscribe/publish
      message_store.py      # Save/load chat messages (PostgreSQL)
      fcm_fallback.py       # Push notification nếu user offline
    models/
      chat.py               # SQLAlchemy models (chat_conversations, chat_messages)
      presence.py           # user_presence model
    schemas/
      ws_message.py         # Pydantic schemas cho WS message protocol
  requirements.txt          # Tách dependencies (nhẹ hơn REST API)
  Dockerfile
  .env.example
```

---

### Deployment

```yaml
# docker-compose.yml
services:
  api:
    build: ./backend
    ports: ["8000:8000"]
    environment:
      - REDIS_URL=redis://redis:6379
      
  ws:
    build: ./ws-server
    ports: ["8001:8001"]
    environment:
      - REDIS_URL=redis://redis:6379
      - DATABASE_URL=postgresql+psycopg://...
      - JWT_SECRET=${JWT_SECRET}  # CÙNG secret với api
    deploy:
      replicas: 2  # Scale WS riêng
      
  redis:
    image: redis:7-alpine
    ports: ["6379:6379"]
    
  postgres:
    image: postgres:17
    ports: ["5432:5432"]
```

**Client connection:**
```
REST:  https://api.sandichvu.vn      → port 8000 (FastAPI)
WS:    wss://ws.sandichvu.vn/ws      → port 8001 (WS Server)
```

> **Nginx/ALB:** route `/ws` → ws-server:8001, còn lại → api:8000. Hoặc dùng subdomain riêng.

---

### Chat Flow (khi đang đi chuyến)

```
1. Customer đặt xe → POST /customer/bookings → booking created
2. Driver accept → FastAPI PUBLISH Redis "booking:{id}" → {status: "accepted"}
3. Customer app: connect WS → join_booking → nhận "driver_assigned" event
4. Driver arrived → "boarding_otp" event → customer nhập OTP
5. Trip in_progress:
   ─ Customer mở chat → load history GET /bookings/{id}/messages
   ─ Customer gõ "Anh ơi em ở cổng 2" → WS send chat_message
   ─ WS Server → save DB → PUBLISH Redis → broadcast to driver
   ─ Driver nhận tin ngay, reply "Ok em anh tới rồi"
   ─ Đồng thời: driver GPS → WS location_update → broadcast to customer
6. Trip completed → conversation.status = 'closed'
   ─ Chat vẫn xem lại được 30 ngày (GET /messages)
   ─ Sau 30 ngày → archived (admin vẫn truy cập được nếu dispute)
```

---

### Ghi chú kỹ thuật

**Offline fallback:**
- Nếu user không có WS connection → mọi event quan trọng (`booking_status`, `chat_message`, `quote_received`) đều gửi qua FCM push notification
- Chat message: lưu DB trước, push FCM notification "Bạn có tin nhắn mới" + deep link vào chat

**Rate limiting:**
- `location_update`: max 1 msg / 3s (driver GPS)
- `chat_send`: max 5 msg / 10s (spam protection)
- `typing`: max 1 msg / 2s

**Reconnection:**
- Client tự reconnect khi mất kết nối (exponential backoff: 1s → 2s → 4s → max 30s)
- Khi reconnect: gửi `join_booking` lại + fetch missed messages via REST API
- Server giữ `last_delivered_message_id` per user để biết tin nào đã gửi

**Message retention:**
- Active trip chat: real-time
- Completed trip: 30 ngày customer/driver xem lại
- Archived: chỉ admin xem (dispute/audit)
- Chat images: S3/MinIO, URL expires 7 ngày (re-generate khi cần)

**Safety moderation:**
- Keyword filter: chặn SĐT, link, ngôn từ nhạy cảm
- Tin nhắn bị flag → `ACH2 /admin/chat/flagged` để admin review
- Nếu cần: AI content moderation (POST-MVP)