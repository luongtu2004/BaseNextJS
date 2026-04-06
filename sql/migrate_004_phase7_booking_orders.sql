-- =========================================================
-- PHASE 7 — BOOKING & ORDERS
-- Tables: price_configs, commission_configs,
--         driver_availability_sessions, driver_locations,
--         bookings, booking_status_logs
-- =========================================================
-- Yêu cầu: Phase 6 đã được apply trước (provider_vehicles,
--           service_routes, service_route_schedules phải tồn tại)
-- =========================================================

-- ── price_configs ──────────────────────────────────────────────────────────────
-- 2 chế độ: 'formula' (hệ thống tự tính) | 'driver_quote' (tài xế tự ra giá)

create table if not exists price_configs (
    id                  uuid        primary key default gen_random_uuid(),
    service_type        varchar(50) not null,
    pricing_mode        varchar(20) not null default 'formula',

    -- Dùng khi pricing_mode = 'formula'
    base_fare           numeric(18,2),           -- Giá mở cửa
    fare_per_km         numeric(18,2),           -- Giá/km
    fare_per_min        numeric(18,2),           -- Giá/phút (kẹt xe)
    min_fare            numeric(18,2),           -- Giá tối thiểu
    surge_enabled       boolean     not null default false,
    surge_multiplier    numeric(4,2)             default 1.0,

    -- Dùng khi pricing_mode = 'driver_quote'
    quote_timeout_sec   integer                  default 120,   -- Giây khách chờ báo giá
    accept_timeout_sec  integer                  default 60,    -- Giây khách có để accept/reject
    min_quote           numeric(18,2),
    max_quote           numeric(18,2),

    effective_from      timestamptz not null default now(),
    effective_to        timestamptz,
    is_active           boolean     not null default true,
    created_at          timestamptz not null default now(),
    updated_at          timestamptz not null default now(),

    constraint chk_price_configs_pricing_mode
        check (pricing_mode in ('formula', 'driver_quote'))
);

create index if not exists ix_price_configs_service_type
    on price_configs(service_type);
create index if not exists ix_price_configs_active
    on price_configs(is_active, effective_from);

-- ── commission_configs ─────────────────────────────────────────────────────────
-- Hoa hồng nền tảng thu từ tài xế sau mỗi chuyến hoàn thành

create table if not exists commission_configs (
    id              uuid        primary key default gen_random_uuid(),
    service_type    varchar(50) not null,
    rate_percent    numeric(5,2) not null,       -- VD: 20.00 = 20%
    fixed_fee       numeric(18,2)  default 0,   -- Phí cố định/chuyến (nếu có)
    effective_from  timestamptz not null default now(),
    effective_to    timestamptz,
    is_active       boolean     not null default true,
    created_at      timestamptz not null default now(),
    updated_at      timestamptz not null default now(),
    constraint uq_commission_configs_service_effective unique (service_type, effective_from)
);

create index if not exists ix_commission_configs_service_type
    on commission_configs(service_type);

-- ── driver_locations ───────────────────────────────────────────────────────────
-- UPSERT liên tục (mỗi ~5s). Cân nhắc Redis cho real-time production.

create table if not exists driver_locations (
    provider_id uuid        primary key references providers(id) on delete cascade,
    latitude    numeric(10,7) not null,
    longitude   numeric(10,7) not null,
    heading     numeric(5,2),                   -- Hướng di chuyển (độ)
    speed_kmh   numeric(5,1),
    updated_at  timestamptz not null default now()
);

-- ── driver_availability_sessions ───────────────────────────────────────────────

create table if not exists driver_availability_sessions (
    id          uuid        primary key default gen_random_uuid(),
    provider_id uuid        not null references providers(id) on delete cascade,
    vehicle_id  uuid        references provider_vehicles(id) on delete set null,
    status      varchar(20) not null default 'offline',  -- offline / online / busy
    online_at   timestamptz,
    offline_at  timestamptz,
    created_at  timestamptz not null default now(),
    constraint chk_driver_availability_status
        check (status in ('offline', 'online', 'busy'))
);

create index if not exists ix_das_provider_id
    on driver_availability_sessions(provider_id);
create index if not exists ix_das_status
    on driver_availability_sessions(status);

-- ── bookings ───────────────────────────────────────────────────────────────────
-- State machine:
--   formula:      pending → searching → accepted → arriving → in_progress → completed
--   driver_quote: pending → searching → driver_quoted → customer_accepted → arriving → in_progress → completed
--                                                     ↘ customer_rejected → searching
--   (cancelled bất kỳ giai đoạn nào)

create table if not exists bookings (
    id                      uuid        primary key default gen_random_uuid(),
    customer_id             uuid        not null references users(id) on delete restrict,
    provider_id             uuid        references providers(id) on delete set null,
    vehicle_id              uuid        references provider_vehicles(id) on delete set null,
    service_category_id     uuid        not null references service_categories(id) on delete restrict,
    service_type            varchar(50) not null,
    pricing_mode            varchar(20) not null default 'formula',

    -- Địa điểm
    pickup_address          text        not null,
    pickup_lat              numeric(10,7),
    pickup_lng              numeric(10,7),
    dropoff_address         text,
    dropoff_lat             numeric(10,7),
    dropoff_lng             numeric(10,7),

    -- Cho thuê / liên tỉnh
    route_id                uuid        references service_routes(id) on delete set null,
    schedule_id             uuid        references service_route_schedules(id) on delete set null,
    rental_start_date       date,
    rental_end_date         date,

    -- Giá
    distance_km             numeric(8,2),
    duration_min            integer,
    estimated_fare          numeric(18,2),        -- Giá công thức (formula mode)
    driver_quoted_fare      numeric(18,2),        -- Giá tài xế tự đặt (driver_quote mode)
    quote_expires_at        timestamptz,          -- Deadline khách phải accept/reject
    customer_accepted_fare  numeric(18,2),        -- Giá sau khi khách đồng ý
    final_fare              numeric(18,2),        -- Giá thực tế khi hoàn thành

    -- Trạng thái
    status                  varchar(30) not null default 'pending',
    cancelled_by            varchar(20),          -- customer / provider / system
    cancel_reason           text,

    -- OTP lên xe (MVP - safety feature)
    boarding_otp            varchar(6),           -- Sinh khi status → arrived
    boarding_otp_expires    timestamptz,          -- Hết hạn sau 10 phút
    boarded_at              timestamptz,          -- Timestamp khi OTP verify thành công

    -- Timeline
    requested_at            timestamptz not null default now(),
    driver_quoted_at        timestamptz,
    customer_decided_at     timestamptz,
    accepted_at             timestamptz,
    arrived_at              timestamptz,
    started_at              timestamptz,
    completed_at            timestamptz,
    cancelled_at            timestamptz,

    -- Thanh toán
    payment_method          varchar(30),          -- cash / wallet / vnpay / momo / zalopay
    payment_status          varchar(20) not null default 'unpaid',

    notes                   text,
    created_at              timestamptz not null default now(),
    updated_at              timestamptz not null default now(),

    constraint chk_bookings_pricing_mode
        check (pricing_mode in ('formula', 'driver_quote')),
    constraint chk_bookings_status
        check (status in (
            'pending', 'searching', 'driver_quoted', 'customer_accepted',
            'customer_rejected', 'quote_expired', 'accepted',
            'arriving', 'in_progress', 'completed', 'cancelled'
        )),
    constraint chk_bookings_cancelled_by
        check (cancelled_by is null or cancelled_by in ('customer', 'provider', 'system')),
    constraint chk_bookings_payment_status
        check (payment_status in ('unpaid', 'paid', 'refunded', 'failed')),
    constraint chk_bookings_payment_method
        check (payment_method is null or payment_method in ('cash', 'wallet', 'vnpay', 'momo', 'zalopay'))
);

create index if not exists ix_bookings_customer_id
    on bookings(customer_id);
create index if not exists ix_bookings_provider_id
    on bookings(provider_id);
create index if not exists ix_bookings_status
    on bookings(status);
create index if not exists ix_bookings_requested_at
    on bookings(requested_at desc);
create index if not exists ix_bookings_service_type
    on bookings(service_type);

-- ── booking_status_logs ────────────────────────────────────────────────────────

create table if not exists booking_status_logs (
    id          uuid        primary key default gen_random_uuid(),
    booking_id  uuid        not null references bookings(id) on delete cascade,
    from_status varchar(30),
    to_status   varchar(30) not null,
    changed_by  uuid        references users(id) on delete set null,
    note        text,
    created_at  timestamptz not null default now()
);

create index if not exists ix_booking_status_logs_booking_id
    on booking_status_logs(booking_id);
