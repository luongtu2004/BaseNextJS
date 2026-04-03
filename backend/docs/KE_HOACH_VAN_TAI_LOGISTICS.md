# Kế hoạch Tích hợp & Mở rộng — Nhóm Vận tải & Logistics

**Ngày:** 04/2026  
**Phạm vi:** Xây dựng đầy đủ taxonomy, bảng mở rộng, và API cho nhóm ngành **Vận tải & Logistics** trên nền hệ thống hiện tại.

---

## 1. Cấu trúc Phân cấp Dịch vụ

```
industry_categories
└── vantaidichuyen (đã có)
    ├── [A] Vận tải hành khách — nội thành
    │   ├── taxi_cong_nghe
    │   └── xe_om_cong_nghe
    ├── [B] Vận tải hành khách — liên tỉnh
    │   ├── xe_khach_lien_tinh
    │   ├── xe_hop_dong_khach
    │   ├── xe_ghep_tien_chuyen
    │   └── xe_limousine
    ├── [C] Lái xe hộ
    │   ├── lai_xe_oto_ho
    │   ├── lai_xe_may_ho
    │   └── lai_xe_thue_theo_chuyen
    ├── [D] Giao nhận & Hàng hóa
    │   ├── shipper_noi_thanh
    │   ├── xe_tai_hop_dong
    │   └── van_tai_bac_trung_nam
    └── [E] Hỗ trợ & Cho thuê xe
        ├── cuu_ho_giao_thong
        ├── cho_thue_xe_tu_lai_oto
        └── cho_thue_xe_may_tu_lai
```

---

## 2. Chi tiết Attributes & Requirements từng Service Category

### [A] Vận tải hành khách — nội thành

#### `taxi_cong_nghe`
**Attributes:**
| attr_key | attr_label | data_type | required | filterable |
|---|---|---|---|---|
| vehicle_type | Loại xe | select | Y | Y |
| seat_count | Số chỗ ngồi | number | Y | Y |
| service_provinces | Tỉnh/TP phục vụ | select | Y | Y |
| has_ac | Có điều hòa | boolean | N | Y |
| has_child_seat | Có ghế trẻ em | boolean | N | Y |
| has_wheelchair | Hỗ trợ xe lăn | boolean | N | Y |
| pricing_model | Mô hình tính giá | select | Y | N |

**Requirements:**
| code | name | type | applies_to |
|---|---|---|---|
| gplx_b1_plus | GPLX từ B1 trở lên | license | all |
| dang_ky_xe | Đăng ký xe | document | all |
| dang_kiem_xe | Đăng kiểm còn hạn | document | all |
| bao_hiem_tnds | Bảo hiểm TNDS bắt buộc | document | all |
| ly_lich_tu_phap | Lý lịch tư pháp | certificate | all |

#### `xe_om_cong_nghe`
**Attributes:** vehicle_type (xe_may/xe_so/xe_dien), service_provinces, has_helmet (Y), has_raincoat, max_load_kg  
**Requirements:** gplx_a1_plus, dang_ky_xe, bao_hiem_tnds, ly_lich_tu_phap

---

### [B] Vận tải hành khách — liên tỉnh

#### `xe_khach_lien_tinh`
**Attributes:**
| attr_key | attr_label | data_type |
|---|---|---|
| seat_type | Loại ghế | select (ngoi/nam/giuong) |
| seat_count | Số chỗ | number |
| route_type | Loại tuyến | select (co_dinh/hop_dong) |
| has_ac | Điều hòa | boolean |
| has_wifi | WiFi | boolean |
| has_usb | Sạc USB | boolean |
| luggage_allowance_kg | Hành lý cho phép (kg) | number |

**Requirements:** gplx_d_plus, chung_chi_lai_xe_chuyen_nghiep, phep_tuyen, dang_ky_xe, dang_kiem_xe, bao_hiem_tnds

Cần thêm bảng `service_routes` + `service_route_schedules` *(xem mục 3)*

#### `xe_ghep_tien_chuyen`
**Attributes:** route_from_province, route_to_province, vehicle_type, seat_count_per_trip, pricing_type (per_seat/full_car)  
**Requirements:** gplx_b2_plus, dang_ky_xe, bao_hiem_tnds

#### `xe_limousine`
**Attributes:** seat_count, vehicle_brand, vehicle_model, has_ac (mặc định Y), has_wifi, has_mini_bar, service_type (airport/event/vip_transfer), route_type  
**Requirements:** gplx_d_plus, dang_ky_xe, dang_kiem_xe, bao_hiem_tnds, ly_lich_tu_phap

---

### [C] Lái xe hộ

#### `lai_xe_oto_ho`
**Attributes:**
| attr_key | attr_label | data_type |
|---|---|---|
| service_type | Hình thức | select (theo_chuyen/theo_ngay) |
| vehicle_types_accepted | Loại xe nhận lái | multi_select |
| service_provinces | Khu vực hoạt động | select |
| night_service | Dịch vụ ban đêm | boolean |
| available_24h | Sẵn sàng 24/7 | boolean |

**Requirements:** gplx_b2_plus, ly_lich_tu_phap, chung_chi_ban_thi_bai

#### `lai_xe_thue_theo_chuyen`
**Attributes:** service_type (per_trip/per_day/per_hour), vehicle_types_accepted, min_hours, service_provinces  
**Requirements:** gplx_b2_plus, ly_lich_tu_phap

---

### [D] Giao nhận & Hàng hóa

#### `shipper_noi_thanh`
**Attributes:**
| attr_key | attr_label | data_type |
|---|---|---|
| vehicle_type | Loại phương tiện | select (xe_may/xe_ba_banh/xe_tai_nho) |
| max_load_kg | Tải trọng tối đa (kg) | number |
| max_size_cm3 | Kích thước tối đa (cm³) | number |
| has_refrigeration | Thùng lạnh | boolean |
| cargo_types | Loại hàng nhận | multi_select |
| service_provinces | Tỉnh/TP hoạt động | select |
| same_day_delivery | Giao trong ngày | boolean |

**Requirements:** gplx_phu_hop, dang_ky_xe, bao_hiem_tnds

#### `xe_tai_hop_dong`
**Attributes:** vehicle_type (xe_tai), max_load_ton, has_refrigeration, has_crane, body_type (bat/mui_kin/dong_lanh), service_area (noi_tinh/lien_tinh/bac_nam)  
**Requirements:** gplx_c_plus, dang_ky_xe, dang_kiem_xe, bao_hiem_tnds, giay_phep_kinh_doanh_van_tai

#### `van_tai_bac_trung_nam`
**Attributes:** route_coverage (bac_nam/bac_trung/trung_nam), max_load_ton, vehicle_type, has_GPS, delivery_days_avg, cargo_insurance  
**Requirements:** gplx_c_plus, giay_phep_kinh_doanh_van_tai, dang_ky_xe, dang_kiem_xe

---

### [E] Hỗ trợ & Cho thuê xe

#### `cuu_ho_giao_thong`
**Attributes:**
| attr_key | attr_label | data_type |
|---|---|---|
| service_types | Loại cứu hộ | multi_select (keo_xe/va_lop/sua_xe/ho_tong/day_ach) |
| vehicle_types_supported | Xe hỗ trợ được | multi_select |
| response_time_min | Thời gian đến (phút) | number |
| service_provinces | Khu vực | select |
| available_24h | 24/7 | boolean |

**Requirements:** chung_chi_ky_thuat_o_to, giay_phep_kinh_doanh

#### `cho_thue_xe_tu_lai_oto`
**Attributes:**
| attr_key | attr_label | data_type |
|---|---|---|
| vehicle_brand | Hãng xe | select |
| vehicle_model | Dòng xe | text |
| year_of_manufacture | Năm sản xuất | number |
| seat_count | Số chỗ | number |
| fuel_type | Nhiên liệu | select (xang/dau/dien/hybrid) |
| transmission | Hộp số | select (auto/manual) |
| rental_type | Hình thức thuê | select (theo_ngay/theo_gio/theo_tuan) |
| price_per_day | Giá/ngày (VNĐ) | number |
| price_per_hour | Giá/giờ (VNĐ) | number |
| deposit_required | Cần đặt cọc | boolean |
| has_driver_option | Có tài xế đi kèm | boolean |
| delivery_available | Giao xe tận nơi | boolean |
| min_rental_days | Thuê tối thiểu (ngày) | number |

**Requirements:** dang_ky_xe, dang_kiem_xe, bao_hiem_tnds_mo_rong, bao_hiem_thiet_hai_vat_chat  
Cần thêm bảng `provider_vehicles` + `provider_vehicle_availabilities` *(xem mục 3)*

#### `cho_thue_xe_may_tu_lai`
**Attributes:** vehicle_type (xe_so/xe_ga/xe_dien), vehicle_brand, vehicle_model, engine_cc, rental_type, price_per_day, has_helmet (Y), delivery_available, service_provinces  
**Requirements:** dang_ky_xe, bao_hiem_tnds

---

## 3. Bảng DB Mới Cần Thêm

### 3.1 `provider_vehicles` — Phương tiện của provider

> Đặt tên theo pattern `provider_*` — tương tự `provider_documents`, `provider_services`.

```sql
CREATE TABLE provider_vehicles (
    id                  UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    provider_id         UUID        NOT NULL REFERENCES providers(id) ON DELETE CASCADE,
    provider_service_id UUID        REFERENCES provider_services(id) ON DELETE SET NULL,
    vehicle_type        VARCHAR(30) NOT NULL,          -- car/motorbike/truck/bus
    brand               VARCHAR(100),
    model               VARCHAR(100),
    license_plate       VARCHAR(20),
    year_of_manufacture INTEGER,
    seat_count          INTEGER,
    fuel_type           VARCHAR(20),                   -- gasoline/diesel/electric/hybrid
    transmission        VARCHAR(20),                   -- auto/manual
    color               VARCHAR(50),
    max_load_kg         NUMERIC(10,2),
    description         TEXT,
    status              VARCHAR(20) NOT NULL DEFAULT 'active',
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by          UUID        REFERENCES users(id) ON DELETE SET NULL,
    updated_by          UUID        REFERENCES users(id) ON DELETE SET NULL
);
```

### 3.2 `provider_vehicle_documents` — Giấy tờ xe

> Đặt tên theo pattern `provider_*_documents` — tương tự `provider_documents`.

```sql
CREATE TABLE provider_vehicle_documents (
    id                  UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    vehicle_id          UUID        NOT NULL REFERENCES provider_vehicles(id) ON DELETE CASCADE,
    document_type       VARCHAR(50) NOT NULL,  -- vehicle_registration/inspection/insurance/permit
    document_number     VARCHAR(100),
    issued_date         DATE,
    expiry_date         DATE,
    front_file_url      TEXT,
    back_file_url       TEXT,
    extra_file_url      TEXT,
    verification_status VARCHAR(30) NOT NULL DEFAULT 'pending',
    reviewed_by         UUID        REFERENCES users(id),
    reviewed_at         TIMESTAMPTZ,
    note                TEXT,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by          UUID        REFERENCES users(id) ON DELETE SET NULL,
    updated_by          UUID        REFERENCES users(id) ON DELETE SET NULL
);
```

### 3.3 `service_routes` — Tuyến đường cố định (xe khách liên tỉnh)

> Đặt tên theo pattern `service_*` — tương tự `service_categories`, `service_skills`.

```sql
CREATE TABLE service_routes (
    id                  UUID           PRIMARY KEY DEFAULT gen_random_uuid(),
    provider_service_id UUID           NOT NULL REFERENCES provider_services(id) ON DELETE CASCADE,
    from_province       VARCHAR(100)   NOT NULL,
    to_province         VARCHAR(100)   NOT NULL,
    from_address        TEXT,
    to_address          TEXT,
    via_provinces       JSONB,                    -- ["Ha Tinh","Nghe An"]
    distance_km         NUMERIC(8,2),
    duration_hours      NUMERIC(5,2),
    is_active           BOOLEAN        NOT NULL DEFAULT true,
    created_at          TIMESTAMPTZ    NOT NULL DEFAULT now(),
    updated_at          TIMESTAMPTZ    NOT NULL DEFAULT now()
);
```

### 3.4 `service_route_schedules` — Lịch khởi hành

> Tên rõ nghĩa hơn `service_schedules`, tránh mơ hồ khi có nhiều loại schedule sau này.

```sql
CREATE TABLE service_route_schedules (
    id               UUID           PRIMARY KEY DEFAULT gen_random_uuid(),
    route_id         UUID           NOT NULL REFERENCES service_routes(id) ON DELETE CASCADE,
    departure_time   TIME           NOT NULL,
    days_of_week     JSONB          NOT NULL,  -- [1,2,3,4,5,6,7] (1=Mon)
    available_seats  INTEGER,
    price            NUMERIC(18,2),
    is_active        BOOLEAN        NOT NULL DEFAULT true,
    created_at       TIMESTAMPTZ    NOT NULL DEFAULT now(),
    updated_at       TIMESTAMPTZ    NOT NULL DEFAULT now()
);
```

### 3.5 `provider_vehicle_availabilities` — Lịch cho thuê xe

> Plural noun, prefix `provider_vehicle_*` để rõ scope — tương tự `provider_vehicle_documents`.

```sql
CREATE TABLE provider_vehicle_availabilities (
    id               UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    vehicle_id       UUID        NOT NULL REFERENCES provider_vehicles(id) ON DELETE CASCADE,
    date             DATE        NOT NULL,
    is_available     BOOLEAN     NOT NULL DEFAULT true,
    blocked_reason   VARCHAR(100),               -- maintenance/booked/personal
    created_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (vehicle_id, date)
);
```

---

## 4. API Endpoints Mới

### 4.1 Provider — Quản lý phương tiện

```
POST   /api/v1/provider/vehicles                                     Thêm xe mới
GET    /api/v1/provider/vehicles                                     Danh sách xe của tôi
GET    /api/v1/provider/vehicles/{id}                                Chi tiết xe
PUT    /api/v1/provider/vehicles/{id}                                Cập nhật xe
PATCH  /api/v1/provider/vehicles/{id}/status                         Kích hoạt / tạm ngừng xe          ← App cần để toggle
DELETE /api/v1/provider/vehicles/{id}                                Xóa xe

GET    /api/v1/provider/vehicles/{id}/documents                      Danh sách giấy tờ xe              ← App hiển thị trạng thái duyệt
POST   /api/v1/provider/vehicles/{id}/documents                      Thêm giấy tờ xe    → provider_vehicle_documents
GET    /api/v1/provider/vehicles/{id}/documents/{doc_id}             Chi tiết giấy tờ xe               ← App xem lý do từ chối
PUT    /api/v1/provider/vehicles/{id}/documents/{doc_id}             Cập nhật giấy tờ xe
DELETE /api/v1/provider/vehicles/{id}/documents/{doc_id}             Xóa giấy tờ xe
```

### 4.2 Provider — Tuyến đường & Lịch khởi hành (xe liên tỉnh)

```
POST   /api/v1/provider/services/{svc_id}/routes                     Tạo tuyến              → service_routes
GET    /api/v1/provider/services/{svc_id}/routes                     Danh sách tuyến
GET    /api/v1/provider/services/{svc_id}/routes/{id}                Chi tiết tuyến         ← App quản lý tuyến
PUT    /api/v1/provider/services/{svc_id}/routes/{id}                Cập nhật tuyến
PATCH  /api/v1/provider/services/{svc_id}/routes/{id}/status         Bật / tắt tuyến        ← Toggle không cần xóa
DELETE /api/v1/provider/services/{svc_id}/routes/{id}                Xóa tuyến

POST   /api/v1/provider/routes/{route_id}/schedules                  Thêm lịch              → service_route_schedules
GET    /api/v1/provider/routes/{route_id}/schedules                  Danh sách lịch
PUT    /api/v1/provider/routes/{route_id}/schedules/{id}             Cập nhật lịch
PATCH  /api/v1/provider/routes/{route_id}/schedules/{id}/status      Bật / tắt lịch         ← Tạm ngừng chuyến cụ thể
DELETE /api/v1/provider/routes/{route_id}/schedules/{id}             Xóa lịch
```

### 4.3 Provider — Lịch cho thuê xe

```
GET    /api/v1/provider/vehicles/{id}/availabilities             Xem lịch            → provider_vehicle_availabilities
POST   /api/v1/provider/vehicles/{id}/availabilities/block      Block ngày không cho thuê
POST   /api/v1/provider/vehicles/{id}/availabilities/unblock    Mở lại ngày
```

### 4.4 Customer — Tìm kiếm & đặt dịch vụ vận tải

```
GET    /api/v1/customer/transport/search                                      Tìm provider theo loại dịch vụ + khu vực
GET    /api/v1/customer/transport/routes                                      Tìm tuyến xe khách (from → to + ngày)
GET    /api/v1/customer/transport/routes/{id}                                 Chi tiết tuyến + danh sách lịch khởi hành  ← App cần trước khi đặt vé
GET    /api/v1/customer/transport/rental-vehicles                             Tìm xe cho thuê (loại + ngày + khu vực)
GET    /api/v1/customer/transport/rental-vehicles/{id}                        Chi tiết xe cho thuê                       ← App xem ảnh, thông số, giá
GET    /api/v1/customer/transport/rental-vehicles/{id}/availabilities         Kiểm tra lịch trống
```

### 4.5 Admin — Quản lý & xét duyệt

```
-- Phương tiện
GET    /api/v1/admin/vehicles                                         Danh sách tất cả xe
GET    /api/v1/admin/vehicles/{id}                                    Chi tiết xe
PATCH  /api/v1/admin/vehicles/{id}/status                             Kích hoạt / khóa xe               ← CMS can thiệp

-- Giấy tờ xe (pattern như A26-A28 Phase 5)
GET    /api/v1/admin/vehicle-documents                                Queue giấy tờ xe chờ duyệt        ← CMS dashboard duyệt tập trung
POST   /api/v1/admin/vehicle-documents/{doc_id}/review                Duyệt / từ chối giấy tờ xe

-- Tuyến đường
GET    /api/v1/admin/routes                                           Tất cả tuyến đường
GET    /api/v1/admin/routes/{id}                                      Chi tiết tuyến + lịch khởi hành   ← CMS xem chi tiết
PATCH  /api/v1/admin/routes/{id}/status                               Bật / tắt tuyến                   ← CMS can thiệp khi có vi phạm
```

---

## 5. Phân tích Điểm Đặc thù Theo Nhóm

| Nhóm | Đặc thù cần xử lý |
|---|---|
| **[A] Nội thành** | Tích hợp định vị thời gian thực (future), tính giá theo km/phút |
| **[B] Liên tỉnh** | Cần `service_routes` + `service_route_schedules`, search theo from-to-date |
| **[C] Lái xe hộ** | Booking theo slot giờ, xác minh GPLX provider |
| **[D] Hàng hóa** | Tải trọng xe là filterable attribute, search theo tuyến + tải trọng |
| **[E] Cho thuê xe** | `provider_vehicles` bắt buộc, `provider_vehicle_availabilities`, giấy tờ xe riêng |

---

## 6. Kế hoạch Triển khai (4 phase)

### Phase 1 — Taxonomy Seed (ưu tiên cao, không cần code mới)

**Mục tiêu:** Có đủ taxonomy để provider đăng ký dịch vụ vận tải ngay.

**Việc cần làm:**
- [ ] Tạo SQL seed: 15 `service_categories` cho nhóm vantaidichuyen
- [ ] Tạo SQL seed: `service_category_attributes` cho tất cả 15 loại dịch vụ
- [ ] Tạo SQL seed: `service_category_requirements` (giấy tờ yêu cầu)
- [ ] Tạo SQL seed: `service_skills` (kỹ năng lái xe, chứng chỉ kỹ thuật)
- [ ] Chạy seed, verify qua `/api/v1/common/taxonomy`

**File output:** `sql/seed_taxonomy_vantai.sql`

---

### Phase 2 — Quản lý Phương tiện (provider_vehicles)

**Mục tiêu:** Provider cho thuê xe và vận tải hàng hóa có thể khai báo xe.

**Việc cần làm:**
- [ ] Migration SQL: tạo `provider_vehicles`, `provider_vehicle_documents`
- [ ] ORM models: `ProviderVehicle`, `ProviderVehicleDocument`
- [ ] Schemas: `ProviderVehicleCreate/Update/Response`, `ProviderVehicleDocumentResponse`
- [ ] API (`/provider/vehicles`): CRUD + document upload
- [ ] API (`/admin/vehicles`): list + review document
- [ ] Tests: test_provider_vehicles.py
- [ ] Cập nhật Excel DB docs

---

### Phase 3 — Tuyến đường & Lịch (xe liên tỉnh)

**Mục tiêu:** Provider xe khách liên tỉnh đăng ký tuyến + lịch cố định.

**Việc cần làm:**
- [ ] Migration SQL: `service_routes`, `service_route_schedules`
- [ ] ORM models: `ServiceRoute`, `ServiceRouteSchedule` + schemas
- [ ] API Provider: CRUD routes + schedules
- [ ] API Customer: search tuyến theo from/to/date
- [ ] Validation: from_province ≠ to_province, departure_time không trùng trong cùng tuyến
- [ ] Tests: test_service_routes.py

---

### Phase 4 — Cho thuê xe & Booking

**Mục tiêu:** Đặt xe cho thuê tự lái, kiểm tra lịch trống.

**Việc cần làm:**
- [ ] Migration SQL: `provider_vehicle_availabilities`
- [ ] ORM model: `ProviderVehicleAvailability` + schema
- [ ] API Provider: quản lý lịch block/unblock
- [ ] API Customer: search xe trống theo ngày + loại
- [ ] (Future) Booking flow: đặt cọc → xác nhận → thanh toán
- [ ] Tests: test_rental_availability.py

---

## 7. SQL Seed File Structure (Phase 1)

```sql
-- sql/seed_taxonomy_vantai.sql
-- Chạy SAU khi seed_taxonomy.sql gốc đã chạy

-- ── A. Vận tải hành khách nội thành ──────────────────
INSERT INTO service_categories (id, industry_category_id, code, name, slug, is_active)
VALUES
  (gen_random_uuid(), '<vantaidichuyen_id>', 'taxi_cong_nghe',    'Taxi công nghệ',          'taxi-cong-nghe',    true),
  (gen_random_uuid(), '<vantaidichuyen_id>', 'xe_om_cong_nghe',   'Xe ôm công nghệ',         'xe-om-cong-nghe',   true),
-- ── B. Liên tỉnh ──────────────────────────────────────
  (gen_random_uuid(), '<vantaidichuyen_id>', 'xe_khach_lien_tinh','Xe khách liên tỉnh',       'xe-khach-lien-tinh',true),
  (gen_random_uuid(), '<vantaidichuyen_id>', 'xe_hop_dong_khach', 'Xe hợp đồng chở khách',    'xe-hop-dong-khach', true),
  (gen_random_uuid(), '<vantaidichuyen_id>', 'xe_ghep_tien_chuyen','Xe ghép/tiện chuyến',     'xe-ghep-tien-chuyen',true),
  (gen_random_uuid(), '<vantaidichuyen_id>', 'xe_limousine',      'Xe Limousine',              'xe-limousine',      true),
-- ── C. Lái xe hộ ──────────────────────────────────────
  (gen_random_uuid(), '<vantaidichuyen_id>', 'lai_xe_oto_ho',     'Lái xe ô tô hộ',           'lai-xe-oto-ho',     true),
  (gen_random_uuid(), '<vantaidichuyen_id>', 'lai_xe_may_ho',     'Lái xe máy hộ',             'lai-xe-may-ho',     true),
  (gen_random_uuid(), '<vantaidichuyen_id>', 'lai_xe_thue_chuyen','Lái xe thuê theo chuyến/ngày','lai-xe-thue-chuyen',true),
-- ── D. Hàng hóa & Logistics ──────────────────────────
  (gen_random_uuid(), '<vantaidichuyen_id>', 'shipper_noi_thanh', 'Shipper giao hàng nội thành','shipper-noi-thanh', true),
  (gen_random_uuid(), '<vantaidichuyen_id>', 'xe_tai_hop_dong',   'Xe tải hợp đồng',           'xe-tai-hop-dong',   true),
  (gen_random_uuid(), '<vantaidichuyen_id>', 'van_tai_bac_nam',   'Vận tải Bắc-Trung-Nam',     'van-tai-bac-nam',   true),
-- ── E. Hỗ trợ & Cho thuê ─────────────────────────────
  (gen_random_uuid(), '<vantaidichuyen_id>', 'cuu_ho_giao_thong', 'Cứu hộ giao thông',         'cuu-ho-giao-thong', true),
  (gen_random_uuid(), '<vantaidichuyen_id>', 'cho_thue_xe_oto',   'Cho thuê xe ô tô tự lái',   'cho-thue-xe-oto',   true),
  (gen_random_uuid(), '<vantaidichuyen_id>', 'cho_thue_xe_may',   'Cho thuê xe máy tự lái',    'cho-thue-xe-may',   true);

-- Sau đó INSERT service_category_attributes và service_category_requirements
-- cho từng category (dùng subquery lấy id theo code)
```

---

## 8. Sơ đồ Quan hệ Bảng Mới

```
providers
  └── provider_services (service_category_id → cho_thue_xe_oto)
        └── provider_vehicles  ──────────────────────────────┐
              ├── provider_vehicle_documents                 │
              └── provider_vehicle_availabilities            │
                                                             │
  └── provider_services (service_category_id → xe_khach...) │
        └── service_routes                                   │
              └── service_route_schedules                    │
                                                             │
provider_service_attributes ──────── (link tới service_id) ─┘
  (ghi nhận vehicle_id nếu cần liên kết xe cụ thể với dịch vụ)
```

---

## 9. Checklist Tổng hợp

### Taxonomy (Phase 1)
- [ ] 15 service_categories đã seed
- [ ] service_category_attributes đủ cho mỗi loại (ước tính ~120 records)
- [ ] service_category_requirements đủ (~45 records)
- [ ] Verify qua API `/common/taxonomy?industry=vantaidichuyen`

### Vehicles (Phase 2)
- [ ] Migration 004 tạo `provider_vehicles` + `provider_vehicle_documents`
- [ ] ORM + schema + API + tests
- [ ] Admin vehicle document review hoạt động

### Routes & Schedules (Phase 3)
- [ ] Migration 005 tạo `service_routes` + `service_route_schedules`
- [ ] Customer search API hoạt động (from/to/date)

### Rental Availability (Phase 4)
- [ ] Migration 006 tạo `provider_vehicle_availabilities`
- [ ] Block/unblock API hoạt động
- [ ] Customer availability check API hoạt động
