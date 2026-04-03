-- sql/seed_taxonomy_vantai.sql
-- Phase 6 — Vận tải & Logistics: Taxonomy Seed
-- Chạy SAU khi seed_taxonomy.sql gốc đã được áp dụng.
-- Script idempotent: an toàn khi chạy nhiều lần.

\set ON_ERROR_STOP on
BEGIN;

-- ────────────────────────────────────────────────────────────────────
-- A. UNIQUE CONSTRAINTS (nếu chưa có)
-- ────────────────────────────────────────────────────────────────────
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'uq_sca_category_key'
    ) THEN
        ALTER TABLE service_category_attributes
            ADD CONSTRAINT uq_sca_category_key UNIQUE (service_category_id, attr_key);
    END IF;
END $$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'uq_scr_category_code'
    ) THEN
        ALTER TABLE service_category_requirements
            ADD CONSTRAINT uq_scr_category_code UNIQUE (service_category_id, requirement_code);
    END IF;
END $$;

-- ────────────────────────────────────────────────────────────────────
-- B. SERVICE CATEGORIES (13 loại, fixed UUIDs)
-- ────────────────────────────────────────────────────────────────────
INSERT INTO service_categories
    (id, industry_category_id, code, name, slug, description, is_active)
VALUES
  -- [A] Vận tải hành khách nội thành
  ('b1aabc11-0001-4000-aa00-000000000001'::uuid,
   'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11'::uuid,
   'taxi_cong_nghe', 'Taxi công nghệ', 'taxi-cong-nghe',
   'Dịch vụ taxi đặt qua ứng dụng công nghệ', true),

  ('b1aabc11-0001-4000-aa00-000000000002'::uuid,
   'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11'::uuid,
   'xe_om_cn', 'Xe ôm công nghệ (app)', 'xe-om-cong-nghe-app',
   'Vận chuyển hành khách bằng xe máy qua ứng dụng', true),

  -- [B] Vận tải hành khách liên tỉnh
  ('b1aabc11-0001-4000-aa00-000000000003'::uuid,
   'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11'::uuid,
   'xe_khach_lien_tinh', 'Xe khách liên tỉnh', 'xe-khach-lien-tinh',
   'Vận tải hành khách tuyến cố định liên tỉnh', true),

  ('b1aabc11-0001-4000-aa00-000000000004'::uuid,
   'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11'::uuid,
   'xe_ghep_tien_chuyen', 'Xe ghép tiện chuyến', 'xe-ghep-tien-chuyen',
   'Dịch vụ xe ghép theo chuyến liên tỉnh', true),

  ('b1aabc11-0001-4000-aa00-000000000005'::uuid,
   'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11'::uuid,
   'xe_limousine', 'Xe Limousine cao cấp', 'xe-limousine',
   'Vận chuyển cao cấp bằng xe Limousine: sân bay, sự kiện, VIP', true),

  -- [C] Lái xe hộ
  ('b1aabc11-0001-4000-aa00-000000000006'::uuid,
   'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11'::uuid,
   'lai_xe_oto_ho', 'Lái xe ô tô hộ', 'lai-xe-oto-ho',
   'Lái xe ô tô hộ theo chuyến hoặc theo ngày', true),

  ('b1aabc11-0001-4000-aa00-000000000007'::uuid,
   'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11'::uuid,
   'lai_xe_thue_chuyen', 'Lái xe thuê theo chuyến / ngày', 'lai-xe-thue-theo-chuyen',
   'Tài xế chuyên nghiệp cho thuê theo chuyến hoặc ngày', true),

  -- [D] Giao nhận & Hàng hóa
  ('b1aabc11-0001-4000-aa00-000000000008'::uuid,
   'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11'::uuid,
   'shipper_noi_thanh', 'Shipper giao hàng nội thành', 'shipper-noi-thanh',
   'Giao nhận hàng hóa nội thành bằng xe máy hoặc xe tải nhỏ', true),

  ('b1aabc11-0001-4000-aa00-000000000009'::uuid,
   'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11'::uuid,
   'xe_tai_hop_dong', 'Xe tải hợp đồng', 'xe-tai-hop-dong',
   'Vận tải hàng hóa bằng xe tải theo hợp đồng', true),

  ('b1aabc11-0001-4000-aa00-000000000010'::uuid,
   'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11'::uuid,
   'van_tai_bac_nam', 'Vận tải Bắc-Trung-Nam', 'van-tai-bac-nam',
   'Vận tải hàng hóa tuyến dài xuyên Bắc-Trung-Nam', true),

  -- [E] Hỗ trợ & Cho thuê xe
  ('b1aabc11-0001-4000-aa00-000000000011'::uuid,
   'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11'::uuid,
   'cuu_ho_giao_thong', 'Cứu hộ giao thông 24/7', 'cuu-ho-giao-thong-24h',
   'Hỗ trợ sự cố giao thông 24/7: kéo xe, vá lốp, sạc ắc-quy, hộ tống', true),

  ('b1aabc11-0001-4000-aa00-000000000012'::uuid,
   'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11'::uuid,
   'cho_thue_xe_tu_lai_oto', 'Cho thuê xe ô tô tự lái', 'cho-thue-xe-tu-lai-oto',
   'Cho thuê xe ô tô tự lái theo ngày, giờ hoặc tuần', true),

  ('b1aabc11-0001-4000-aa00-000000000013'::uuid,
   'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11'::uuid,
   'cho_thue_xe_may', 'Cho thuê xe máy tự lái', 'cho-thue-xe-may-tu-lai',
   'Cho thuê xe máy (xe số, xe ga, xe điện) tự lái theo ngày', true)

ON CONFLICT (id) DO UPDATE SET
    code        = EXCLUDED.code,
    slug        = EXCLUDED.slug,
    description = EXCLUDED.description,
    is_active   = EXCLUDED.is_active;

-- ────────────────────────────────────────────────────────────────────
-- C. SERVICE CATEGORY ATTRIBUTES
-- ────────────────────────────────────────────────────────────────────
INSERT INTO service_category_attributes
    (id, service_category_id, attr_key, attr_label, data_type, is_required, is_filterable, options_json)
VALUES
  -- [A1] taxi_cong_nghe
  (gen_random_uuid(), 'b1aabc11-0001-4000-aa00-000000000001'::uuid,
   'vehicle_type', 'Loại xe', 'select', true, true,
   '["sedan","suv","7_cho"]'::jsonb),
  (gen_random_uuid(), 'b1aabc11-0001-4000-aa00-000000000001'::uuid,
   'seat_count', 'Số chỗ ngồi', 'number', true, true, null),
  (gen_random_uuid(), 'b1aabc11-0001-4000-aa00-000000000001'::uuid,
   'service_provinces', 'Tỉnh/TP phục vụ', 'select', true, true, null),
  (gen_random_uuid(), 'b1aabc11-0001-4000-aa00-000000000001'::uuid,
   'has_ac', 'Có điều hòa', 'boolean', false, true, null),
  (gen_random_uuid(), 'b1aabc11-0001-4000-aa00-000000000001'::uuid,
   'has_child_seat', 'Có ghế trẻ em', 'boolean', false, true, null),
  (gen_random_uuid(), 'b1aabc11-0001-4000-aa00-000000000001'::uuid,
   'has_wheelchair', 'Hỗ trợ xe lăn', 'boolean', false, true, null),
  (gen_random_uuid(), 'b1aabc11-0001-4000-aa00-000000000001'::uuid,
   'pricing_model', 'Mô hình tính giá', 'select', true, false,
   '["theo_km","theo_thoi_gian","co_dinh"]'::jsonb),

  -- [A2] xe_om_cong_nghe
  (gen_random_uuid(), 'b1aabc11-0001-4000-aa00-000000000002'::uuid,
   'vehicle_type', 'Loại xe máy', 'select', true, true,
   '["xe_may","xe_so","xe_dien"]'::jsonb),
  (gen_random_uuid(), 'b1aabc11-0001-4000-aa00-000000000002'::uuid,
   'service_provinces', 'Tỉnh/TP phục vụ', 'select', true, true, null),
  (gen_random_uuid(), 'b1aabc11-0001-4000-aa00-000000000002'::uuid,
   'has_helmet', 'Cung cấp mũ bảo hiểm', 'boolean', true, true, null),
  (gen_random_uuid(), 'b1aabc11-0001-4000-aa00-000000000002'::uuid,
   'has_raincoat', 'Cung cấp áo mưa', 'boolean', false, true, null),
  (gen_random_uuid(), 'b1aabc11-0001-4000-aa00-000000000002'::uuid,
   'max_load_kg', 'Tải trọng hành lý tối đa (kg)', 'number', false, false, null),

  -- [B1] xe_khach_lien_tinh
  (gen_random_uuid(), 'b1aabc11-0001-4000-aa00-000000000003'::uuid,
   'seat_type', 'Loại ghế', 'select', true, true,
   '["ngoi","nam","giuong"]'::jsonb),
  (gen_random_uuid(), 'b1aabc11-0001-4000-aa00-000000000003'::uuid,
   'seat_count', 'Số chỗ', 'number', true, true, null),
  (gen_random_uuid(), 'b1aabc11-0001-4000-aa00-000000000003'::uuid,
   'route_type', 'Loại tuyến', 'select', true, true,
   '["co_dinh","hop_dong"]'::jsonb),
  (gen_random_uuid(), 'b1aabc11-0001-4000-aa00-000000000003'::uuid,
   'has_ac', 'Có điều hòa', 'boolean', false, true, null),
  (gen_random_uuid(), 'b1aabc11-0001-4000-aa00-000000000003'::uuid,
   'has_wifi', 'Có WiFi', 'boolean', false, true, null),
  (gen_random_uuid(), 'b1aabc11-0001-4000-aa00-000000000003'::uuid,
   'has_usb', 'Có cổng sạc USB', 'boolean', false, true, null),
  (gen_random_uuid(), 'b1aabc11-0001-4000-aa00-000000000003'::uuid,
   'luggage_allowance_kg', 'Hành lý cho phép (kg)', 'number', false, false, null),

  -- [B2] xe_ghep_tien_chuyen
  (gen_random_uuid(), 'b1aabc11-0001-4000-aa00-000000000004'::uuid,
   'route_from_province', 'Tỉnh/TP đi', 'select', true, true, null),
  (gen_random_uuid(), 'b1aabc11-0001-4000-aa00-000000000004'::uuid,
   'route_to_province', 'Tỉnh/TP đến', 'select', true, true, null),
  (gen_random_uuid(), 'b1aabc11-0001-4000-aa00-000000000004'::uuid,
   'vehicle_type', 'Loại xe', 'select', true, true,
   '["xe_4_cho","xe_7_cho","xe_16_cho"]'::jsonb),
  (gen_random_uuid(), 'b1aabc11-0001-4000-aa00-000000000004'::uuid,
   'seat_count_per_trip', 'Số chỗ / chuyến', 'number', true, true, null),
  (gen_random_uuid(), 'b1aabc11-0001-4000-aa00-000000000004'::uuid,
   'pricing_type', 'Loại giá vé', 'select', true, false,
   '["per_seat","full_car"]'::jsonb),

  -- [B3] xe_limousine
  (gen_random_uuid(), 'b1aabc11-0001-4000-aa00-000000000005'::uuid,
   'seat_count', 'Số chỗ ngồi', 'number', true, true, null),
  (gen_random_uuid(), 'b1aabc11-0001-4000-aa00-000000000005'::uuid,
   'vehicle_brand', 'Hãng xe', 'select', true, true,
   '["Mercedes","Dcar","Solati","Ford"]'::jsonb),
  (gen_random_uuid(), 'b1aabc11-0001-4000-aa00-000000000005'::uuid,
   'vehicle_model', 'Dòng xe', 'text', false, false, null),
  (gen_random_uuid(), 'b1aabc11-0001-4000-aa00-000000000005'::uuid,
   'has_wifi', 'Có WiFi', 'boolean', false, true, null),
  (gen_random_uuid(), 'b1aabc11-0001-4000-aa00-000000000005'::uuid,
   'has_mini_bar', 'Có mini bar', 'boolean', false, true, null),
  (gen_random_uuid(), 'b1aabc11-0001-4000-aa00-000000000005'::uuid,
   'service_type', 'Hình thức dịch vụ', 'select', true, true,
   '["airport","event","vip_transfer","tour"]'::jsonb),
  (gen_random_uuid(), 'b1aabc11-0001-4000-aa00-000000000005'::uuid,
   'route_type', 'Phạm vi hoạt động', 'select', true, true,
   '["noi_tinh","lien_tinh","bac_nam"]'::jsonb),

  -- [C1] lai_xe_oto_ho
  (gen_random_uuid(), 'b1aabc11-0001-4000-aa00-000000000006'::uuid,
   'service_type', 'Hình thức', 'select', true, true,
   '["theo_chuyen","theo_ngay","theo_gio"]'::jsonb),
  (gen_random_uuid(), 'b1aabc11-0001-4000-aa00-000000000006'::uuid,
   'vehicle_types_accepted', 'Loại xe nhận lái', 'multiselect', true, true,
   '["4_cho","7_cho","16_cho","29_cho","45_cho"]'::jsonb),
  (gen_random_uuid(), 'b1aabc11-0001-4000-aa00-000000000006'::uuid,
   'service_provinces', 'Khu vực hoạt động', 'select', true, true, null),
  (gen_random_uuid(), 'b1aabc11-0001-4000-aa00-000000000006'::uuid,
   'night_service', 'Phục vụ ban đêm', 'boolean', false, true, null),
  (gen_random_uuid(), 'b1aabc11-0001-4000-aa00-000000000006'::uuid,
   'available_24h', 'Sẵn sàng 24/7', 'boolean', false, true, null),

  -- [C2] lai_xe_thue_theo_chuyen
  (gen_random_uuid(), 'b1aabc11-0001-4000-aa00-000000000007'::uuid,
   'service_type', 'Hình thức thuê', 'select', true, true,
   '["per_trip","per_day","per_hour"]'::jsonb),
  (gen_random_uuid(), 'b1aabc11-0001-4000-aa00-000000000007'::uuid,
   'vehicle_types_accepted', 'Loại xe nhận lái', 'multiselect', true, true,
   '["4_cho","7_cho","16_cho"]'::jsonb),
  (gen_random_uuid(), 'b1aabc11-0001-4000-aa00-000000000007'::uuid,
   'min_hours', 'Số giờ tối thiểu', 'number', false, false, null),
  (gen_random_uuid(), 'b1aabc11-0001-4000-aa00-000000000007'::uuid,
   'service_provinces', 'Khu vực hoạt động', 'select', true, true, null),

  -- [D1] shipper_noi_thanh
  (gen_random_uuid(), 'b1aabc11-0001-4000-aa00-000000000008'::uuid,
   'vehicle_type', 'Loại phương tiện', 'select', true, true,
   '["xe_may","xe_ba_banh","xe_tai_nho"]'::jsonb),
  (gen_random_uuid(), 'b1aabc11-0001-4000-aa00-000000000008'::uuid,
   'max_load_kg', 'Tải trọng tối đa (kg)', 'number', true, true, null),
  (gen_random_uuid(), 'b1aabc11-0001-4000-aa00-000000000008'::uuid,
   'max_size_cm3', 'Kích thước tối đa (cm3)', 'number', false, false, null),
  (gen_random_uuid(), 'b1aabc11-0001-4000-aa00-000000000008'::uuid,
   'has_refrigeration', 'Thùng lạnh', 'boolean', false, true, null),
  (gen_random_uuid(), 'b1aabc11-0001-4000-aa00-000000000008'::uuid,
   'cargo_types', 'Loại hàng nhận', 'multiselect', false, true,
   '["thuc_pham","do_dung","tai_lieu","dong_lanh","de_vo"]'::jsonb),
  (gen_random_uuid(), 'b1aabc11-0001-4000-aa00-000000000008'::uuid,
   'service_provinces', 'Tỉnh/TP hoạt động', 'select', true, true, null),
  (gen_random_uuid(), 'b1aabc11-0001-4000-aa00-000000000008'::uuid,
   'same_day_delivery', 'Giao trong ngày', 'boolean', false, true, null),

  -- [D2] xe_tai_hop_dong
  (gen_random_uuid(), 'b1aabc11-0001-4000-aa00-000000000009'::uuid,
   'max_load_ton', 'Tải trọng tối đa (tấn)', 'number', true, true, null),
  (gen_random_uuid(), 'b1aabc11-0001-4000-aa00-000000000009'::uuid,
   'has_refrigeration', 'Thùng lạnh', 'boolean', false, true, null),
  (gen_random_uuid(), 'b1aabc11-0001-4000-aa00-000000000009'::uuid,
   'has_crane', 'Có cẩu', 'boolean', false, true, null),
  (gen_random_uuid(), 'b1aabc11-0001-4000-aa00-000000000009'::uuid,
   'body_type', 'Loại thùng xe', 'select', true, true,
   '["bat","mui_kin","dong_lanh","cau"]'::jsonb),
  (gen_random_uuid(), 'b1aabc11-0001-4000-aa00-000000000009'::uuid,
   'service_area', 'Phạm vi hoạt động', 'select', true, true,
   '["noi_tinh","lien_tinh","bac_nam"]'::jsonb),

  -- [D3] van_tai_bac_nam
  (gen_random_uuid(), 'b1aabc11-0001-4000-aa00-000000000010'::uuid,
   'route_coverage', 'Tuyến vận tải', 'select', true, true,
   '["bac_nam","bac_trung","trung_nam"]'::jsonb),
  (gen_random_uuid(), 'b1aabc11-0001-4000-aa00-000000000010'::uuid,
   'max_load_ton', 'Tải trọng tối đa (tấn)', 'number', true, true, null),
  (gen_random_uuid(), 'b1aabc11-0001-4000-aa00-000000000010'::uuid,
   'has_GPS', 'Có GPS theo dõi', 'boolean', false, true, null),
  (gen_random_uuid(), 'b1aabc11-0001-4000-aa00-000000000010'::uuid,
   'delivery_days_avg', 'Số ngày giao hàng trung bình', 'number', false, false, null),
  (gen_random_uuid(), 'b1aabc11-0001-4000-aa00-000000000010'::uuid,
   'cargo_insurance', 'Có bảo hiểm hàng hóa', 'boolean', false, true, null),

  -- [E1] cuu_ho_giao_thong
  (gen_random_uuid(), 'b1aabc11-0001-4000-aa00-000000000011'::uuid,
   'service_types', 'Loại cứu hộ', 'multiselect', true, true,
   '["keo_xe","va_lop","sua_xe","ho_tong","day_ach"]'::jsonb),
  (gen_random_uuid(), 'b1aabc11-0001-4000-aa00-000000000011'::uuid,
   'vehicle_types_supported', 'Loại xe hỗ trợ', 'multiselect', true, true,
   '["xe_may","o_to_con","xe_tai","xe_khach"]'::jsonb),
  (gen_random_uuid(), 'b1aabc11-0001-4000-aa00-000000000011'::uuid,
   'response_time_min', 'Thời gian đến (phút)', 'number', true, true, null),
  (gen_random_uuid(), 'b1aabc11-0001-4000-aa00-000000000011'::uuid,
   'service_provinces', 'Khu vực hoạt động', 'select', true, true, null),
  (gen_random_uuid(), 'b1aabc11-0001-4000-aa00-000000000011'::uuid,
   'available_24h', 'Phục vụ 24/7', 'boolean', true, true, null),

  -- [E2] cho_thue_xe_tu_lai_oto
  (gen_random_uuid(), 'b1aabc11-0001-4000-aa00-000000000012'::uuid,
   'vehicle_brand', 'Hãng xe', 'select', true, true,
   '["Toyota","Honda","Kia","Mazda","Ford","Hyundai","VinFast","Mitsubishi"]'::jsonb),
  (gen_random_uuid(), 'b1aabc11-0001-4000-aa00-000000000012'::uuid,
   'vehicle_model', 'Dòng xe', 'text', true, false, null),
  (gen_random_uuid(), 'b1aabc11-0001-4000-aa00-000000000012'::uuid,
   'year_of_manufacture', 'Năm sản xuất', 'number', true, true, null),
  (gen_random_uuid(), 'b1aabc11-0001-4000-aa00-000000000012'::uuid,
   'seat_count', 'Số chỗ ngồi', 'number', true, true, null),
  (gen_random_uuid(), 'b1aabc11-0001-4000-aa00-000000000012'::uuid,
   'fuel_type', 'Nhiên liệu', 'select', true, true,
   '["xang","dau","dien","hybrid"]'::jsonb),
  (gen_random_uuid(), 'b1aabc11-0001-4000-aa00-000000000012'::uuid,
   'transmission', 'Hộp số', 'select', true, true,
   '["auto","manual"]'::jsonb),
  (gen_random_uuid(), 'b1aabc11-0001-4000-aa00-000000000012'::uuid,
   'rental_type', 'Hình thức thuê', 'select', true, true,
   '["theo_ngay","theo_gio","theo_tuan"]'::jsonb),
  (gen_random_uuid(), 'b1aabc11-0001-4000-aa00-000000000012'::uuid,
   'price_per_day', 'Giá/ngày (VNĐ)', 'number', false, true, null),
  (gen_random_uuid(), 'b1aabc11-0001-4000-aa00-000000000012'::uuid,
   'price_per_hour', 'Giá/giờ (VNĐ)', 'number', false, false, null),
  (gen_random_uuid(), 'b1aabc11-0001-4000-aa00-000000000012'::uuid,
   'deposit_required', 'Cần đặt cọc', 'boolean', false, true, null),
  (gen_random_uuid(), 'b1aabc11-0001-4000-aa00-000000000012'::uuid,
   'has_driver_option', 'Có tài xế đi kèm', 'boolean', false, true, null),
  (gen_random_uuid(), 'b1aabc11-0001-4000-aa00-000000000012'::uuid,
   'delivery_available', 'Giao xe tận nơi', 'boolean', false, true, null),
  (gen_random_uuid(), 'b1aabc11-0001-4000-aa00-000000000012'::uuid,
   'min_rental_days', 'Thuê tối thiểu (ngày)', 'number', false, false, null),

  -- [E3] cho_thue_xe_may
  (gen_random_uuid(), 'b1aabc11-0001-4000-aa00-000000000013'::uuid,
   'vehicle_type', 'Loại xe máy', 'select', true, true,
   '["xe_so","xe_ga","xe_dien"]'::jsonb),
  (gen_random_uuid(), 'b1aabc11-0001-4000-aa00-000000000013'::uuid,
   'vehicle_brand', 'Hãng xe', 'select', false, true,
   '["Honda","Yamaha","Suzuki","VinFast","Piaggio"]'::jsonb),
  (gen_random_uuid(), 'b1aabc11-0001-4000-aa00-000000000013'::uuid,
   'vehicle_model', 'Dòng xe', 'text', false, false, null),
  (gen_random_uuid(), 'b1aabc11-0001-4000-aa00-000000000013'::uuid,
   'engine_cc', 'Dung tích xi-lanh (cc)', 'number', false, false, null),
  (gen_random_uuid(), 'b1aabc11-0001-4000-aa00-000000000013'::uuid,
   'rental_type', 'Hình thức thuê', 'select', true, true,
   '["theo_ngay","theo_gio"]'::jsonb),
  (gen_random_uuid(), 'b1aabc11-0001-4000-aa00-000000000013'::uuid,
   'price_per_day', 'Giá/ngày (VNĐ)', 'number', true, true, null),
  (gen_random_uuid(), 'b1aabc11-0001-4000-aa00-000000000013'::uuid,
   'has_helmet', 'Kèm mũ bảo hiểm', 'boolean', true, true, null),
  (gen_random_uuid(), 'b1aabc11-0001-4000-aa00-000000000013'::uuid,
   'delivery_available', 'Giao xe tận nơi', 'boolean', false, true, null),
  (gen_random_uuid(), 'b1aabc11-0001-4000-aa00-000000000013'::uuid,
   'service_provinces', 'Tỉnh/TP hoạt động', 'select', true, true, null)

ON CONFLICT ON CONSTRAINT uq_sca_category_key DO UPDATE SET
    attr_label   = EXCLUDED.attr_label,
    data_type    = EXCLUDED.data_type,
    is_required  = EXCLUDED.is_required,
    is_filterable = EXCLUDED.is_filterable,
    options_json = EXCLUDED.options_json;

-- ────────────────────────────────────────────────────────────────────
-- D. SERVICE CATEGORY REQUIREMENTS
-- ────────────────────────────────────────────────────────────────────
INSERT INTO service_category_requirements
    (id, service_category_id, requirement_type, requirement_code, requirement_name,
     is_required, applies_to_provider_type, is_active)
VALUES
  -- [A1] taxi_cong_nghe
  (gen_random_uuid(), 'b1aabc11-0001-4000-aa00-000000000001'::uuid,
   'license', 'gplx_b1_plus', 'GPLX từ hạng B1 trở lên', true, 'all', true),
  (gen_random_uuid(), 'b1aabc11-0001-4000-aa00-000000000001'::uuid,
   'document', 'dang_ky_xe', 'Đăng ký xe', true, 'all', true),
  (gen_random_uuid(), 'b1aabc11-0001-4000-aa00-000000000001'::uuid,
   'document', 'dang_kiem_xe', 'Đăng kiểm xe còn hạn', true, 'all', true),
  (gen_random_uuid(), 'b1aabc11-0001-4000-aa00-000000000001'::uuid,
   'document', 'bao_hiem_tnds', 'Bảo hiểm TNDS bắt buộc còn hạn', true, 'all', true),
  (gen_random_uuid(), 'b1aabc11-0001-4000-aa00-000000000001'::uuid,
   'certificate', 'ly_lich_tu_phap', 'Lý lịch tư pháp sạch', true, 'all', true),

  -- [A2] xe_om_cong_nghe
  (gen_random_uuid(), 'b1aabc11-0001-4000-aa00-000000000002'::uuid,
   'license', 'gplx_a1_plus', 'GPLX từ hạng A1 trở lên', true, 'all', true),
  (gen_random_uuid(), 'b1aabc11-0001-4000-aa00-000000000002'::uuid,
   'document', 'dang_ky_xe', 'Đăng ký xe', true, 'all', true),
  (gen_random_uuid(), 'b1aabc11-0001-4000-aa00-000000000002'::uuid,
   'document', 'bao_hiem_tnds', 'Bảo hiểm TNDS bắt buộc còn hạn', true, 'all', true),
  (gen_random_uuid(), 'b1aabc11-0001-4000-aa00-000000000002'::uuid,
   'certificate', 'ly_lich_tu_phap', 'Lý lịch tư pháp sạch', true, 'all', true),

  -- [B1] xe_khach_lien_tinh
  (gen_random_uuid(), 'b1aabc11-0001-4000-aa00-000000000003'::uuid,
   'license', 'gplx_d_plus', 'GPLX hạng D trở lên', true, 'all', true),
  (gen_random_uuid(), 'b1aabc11-0001-4000-aa00-000000000003'::uuid,
   'certificate', 'chung_chi_lai_xe_cn', 'Chứng chỉ lái xe chuyên nghiệp', true, 'all', true),
  (gen_random_uuid(), 'b1aabc11-0001-4000-aa00-000000000003'::uuid,
   'document', 'phep_tuyen', 'Giấy phép kinh doanh vận tải tuyến cố định', true, 'business', true),
  (gen_random_uuid(), 'b1aabc11-0001-4000-aa00-000000000003'::uuid,
   'document', 'dang_ky_xe', 'Đăng ký xe', true, 'all', true),
  (gen_random_uuid(), 'b1aabc11-0001-4000-aa00-000000000003'::uuid,
   'document', 'dang_kiem_xe', 'Đăng kiểm xe còn hạn', true, 'all', true),
  (gen_random_uuid(), 'b1aabc11-0001-4000-aa00-000000000003'::uuid,
   'document', 'bao_hiem_tnds', 'Bảo hiểm TNDS bắt buộc còn hạn', true, 'all', true),

  -- [B2] xe_ghep_tien_chuyen
  (gen_random_uuid(), 'b1aabc11-0001-4000-aa00-000000000004'::uuid,
   'license', 'gplx_b2_plus', 'GPLX hạng B2 trở lên', true, 'all', true),
  (gen_random_uuid(), 'b1aabc11-0001-4000-aa00-000000000004'::uuid,
   'document', 'dang_ky_xe', 'Đăng ký xe', true, 'all', true),
  (gen_random_uuid(), 'b1aabc11-0001-4000-aa00-000000000004'::uuid,
   'document', 'bao_hiem_tnds', 'Bảo hiểm TNDS bắt buộc còn hạn', true, 'all', true),

  -- [B3] xe_limousine
  (gen_random_uuid(), 'b1aabc11-0001-4000-aa00-000000000005'::uuid,
   'license', 'gplx_d_plus', 'GPLX hạng D trở lên', true, 'all', true),
  (gen_random_uuid(), 'b1aabc11-0001-4000-aa00-000000000005'::uuid,
   'document', 'dang_ky_xe', 'Đăng ký xe', true, 'all', true),
  (gen_random_uuid(), 'b1aabc11-0001-4000-aa00-000000000005'::uuid,
   'document', 'dang_kiem_xe', 'Đăng kiểm xe còn hạn', true, 'all', true),
  (gen_random_uuid(), 'b1aabc11-0001-4000-aa00-000000000005'::uuid,
   'document', 'bao_hiem_tnds', 'Bảo hiểm TNDS bắt buộc còn hạn', true, 'all', true),
  (gen_random_uuid(), 'b1aabc11-0001-4000-aa00-000000000005'::uuid,
   'certificate', 'ly_lich_tu_phap', 'Lý lịch tư pháp sạch', true, 'all', true),

  -- [C1] lai_xe_oto_ho
  (gen_random_uuid(), 'b1aabc11-0001-4000-aa00-000000000006'::uuid,
   'license', 'gplx_b2_plus', 'GPLX hạng B2 trở lên', true, 'all', true),
  (gen_random_uuid(), 'b1aabc11-0001-4000-aa00-000000000006'::uuid,
   'certificate', 'ly_lich_tu_phap', 'Lý lịch tư pháp sạch', true, 'all', true),
  (gen_random_uuid(), 'b1aabc11-0001-4000-aa00-000000000006'::uuid,
   'certificate', 'chung_chi_ban_thi_bai', 'Chứng chỉ thi bằng chuyên nghiệp', false, 'all', true),

  -- [C2] lai_xe_thue_theo_chuyen
  (gen_random_uuid(), 'b1aabc11-0001-4000-aa00-000000000007'::uuid,
   'license', 'gplx_b2_plus', 'GPLX hạng B2 trở lên', true, 'all', true),
  (gen_random_uuid(), 'b1aabc11-0001-4000-aa00-000000000007'::uuid,
   'certificate', 'ly_lich_tu_phap', 'Lý lịch tư pháp sạch', true, 'all', true),

  -- [D1] shipper_noi_thanh
  (gen_random_uuid(), 'b1aabc11-0001-4000-aa00-000000000008'::uuid,
   'license', 'gplx_phu_hop', 'GPLX phù hợp với loại phương tiện', true, 'all', true),
  (gen_random_uuid(), 'b1aabc11-0001-4000-aa00-000000000008'::uuid,
   'document', 'dang_ky_xe', 'Đăng ký xe', true, 'all', true),
  (gen_random_uuid(), 'b1aabc11-0001-4000-aa00-000000000008'::uuid,
   'document', 'bao_hiem_tnds', 'Bảo hiểm TNDS bắt buộc còn hạn', true, 'all', true),

  -- [D2] xe_tai_hop_dong
  (gen_random_uuid(), 'b1aabc11-0001-4000-aa00-000000000009'::uuid,
   'license', 'gplx_c_plus', 'GPLX hạng C trở lên', true, 'all', true),
  (gen_random_uuid(), 'b1aabc11-0001-4000-aa00-000000000009'::uuid,
   'document', 'dang_ky_xe', 'Đăng ký xe', true, 'all', true),
  (gen_random_uuid(), 'b1aabc11-0001-4000-aa00-000000000009'::uuid,
   'document', 'dang_kiem_xe', 'Đăng kiểm xe còn hạn', true, 'all', true),
  (gen_random_uuid(), 'b1aabc11-0001-4000-aa00-000000000009'::uuid,
   'document', 'bao_hiem_tnds', 'Bảo hiểm TNDS bắt buộc còn hạn', true, 'all', true),
  (gen_random_uuid(), 'b1aabc11-0001-4000-aa00-000000000009'::uuid,
   'document', 'gp_kd_van_tai', 'Giấy phép kinh doanh vận tải', true, 'business', true),

  -- [D3] van_tai_bac_nam
  (gen_random_uuid(), 'b1aabc11-0001-4000-aa00-000000000010'::uuid,
   'license', 'gplx_c_plus', 'GPLX hạng C trở lên', true, 'all', true),
  (gen_random_uuid(), 'b1aabc11-0001-4000-aa00-000000000010'::uuid,
   'document', 'gp_kd_van_tai', 'Giấy phép kinh doanh vận tải', true, 'business', true),
  (gen_random_uuid(), 'b1aabc11-0001-4000-aa00-000000000010'::uuid,
   'document', 'dang_ky_xe', 'Đăng ký xe', true, 'all', true),
  (gen_random_uuid(), 'b1aabc11-0001-4000-aa00-000000000010'::uuid,
   'document', 'dang_kiem_xe', 'Đăng kiểm xe còn hạn', true, 'all', true),

  -- [E1] cuu_ho_giao_thong
  (gen_random_uuid(), 'b1aabc11-0001-4000-aa00-000000000011'::uuid,
   'certificate', 'chung_chi_ky_thuat_oto', 'Chứng chỉ kỹ thuật ô tô', true, 'all', true),
  (gen_random_uuid(), 'b1aabc11-0001-4000-aa00-000000000011'::uuid,
   'document', 'gp_kinh_doanh', 'Giấy phép kinh doanh', true, 'business', true),

  -- [E2] cho_thue_xe_tu_lai_oto
  (gen_random_uuid(), 'b1aabc11-0001-4000-aa00-000000000012'::uuid,
   'document', 'dang_ky_xe', 'Đăng ký xe', true, 'all', true),
  (gen_random_uuid(), 'b1aabc11-0001-4000-aa00-000000000012'::uuid,
   'document', 'dang_kiem_xe', 'Đăng kiểm xe còn hạn', true, 'all', true),
  (gen_random_uuid(), 'b1aabc11-0001-4000-aa00-000000000012'::uuid,
   'document', 'bao_hiem_tnds_mo_rong', 'Bảo hiểm TNDS mở rộng', true, 'all', true),
  (gen_random_uuid(), 'b1aabc11-0001-4000-aa00-000000000012'::uuid,
   'document', 'bao_hiem_vat_chat', 'Bảo hiểm thiệt hại vật chất xe', true, 'all', true),

  -- [E3] cho_thue_xe_may
  (gen_random_uuid(), 'b1aabc11-0001-4000-aa00-000000000013'::uuid,
   'document', 'dang_ky_xe', 'Đăng ký xe', true, 'all', true),
  (gen_random_uuid(), 'b1aabc11-0001-4000-aa00-000000000013'::uuid,
   'document', 'bao_hiem_tnds', 'Bảo hiểm TNDS bắt buộc còn hạn', true, 'all', true)

ON CONFLICT ON CONSTRAINT uq_scr_category_code DO UPDATE SET
    requirement_name         = EXCLUDED.requirement_name,
    requirement_type         = EXCLUDED.requirement_type,
    applies_to_provider_type = EXCLUDED.applies_to_provider_type,
    is_active                = EXCLUDED.is_active;

COMMIT;

SELECT
    sc.code,
    sc.name,
    COUNT(DISTINCT a.id) AS attribute_count,
    COUNT(DISTINCT r.id) AS requirement_count
FROM service_categories sc
LEFT JOIN service_category_attributes a ON a.service_category_id = sc.id
LEFT JOIN service_category_requirements r ON r.service_category_id = sc.id
WHERE sc.id IN (
    'b1aabc11-0001-4000-aa00-000000000001'::uuid,
    'b1aabc11-0001-4000-aa00-000000000002'::uuid,
    'b1aabc11-0001-4000-aa00-000000000003'::uuid,
    'b1aabc11-0001-4000-aa00-000000000004'::uuid,
    'b1aabc11-0001-4000-aa00-000000000005'::uuid,
    'b1aabc11-0001-4000-aa00-000000000006'::uuid,
    'b1aabc11-0001-4000-aa00-000000000007'::uuid,
    'b1aabc11-0001-4000-aa00-000000000008'::uuid,
    'b1aabc11-0001-4000-aa00-000000000009'::uuid,
    'b1aabc11-0001-4000-aa00-000000000010'::uuid,
    'b1aabc11-0001-4000-aa00-000000000011'::uuid,
    'b1aabc11-0001-4000-aa00-000000000012'::uuid,
    'b1aabc11-0001-4000-aa00-000000000013'::uuid
)
GROUP BY sc.code, sc.name
ORDER BY sc.code;
