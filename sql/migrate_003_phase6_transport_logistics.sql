-- =========================================================
-- PHASE 6 — VẬN TẢI & LOGISTICS
-- Tables: provider_vehicles, provider_vehicle_documents,
--         service_routes, service_route_schedules,
--         provider_vehicle_availabilities
-- =========================================================

-- ── provider_vehicles ─────────────────────────────────────────────────────────

create table if not exists provider_vehicles (
    id                  uuid        primary key default gen_random_uuid(),
    provider_id         uuid        not null references providers(id) on delete cascade,
    service_id          uuid        references provider_services(id) on delete set null,
    vehicle_type        varchar(50) not null,
    vehicle_brand       varchar(100),
    vehicle_model       varchar(100),
    year_of_manufacture integer,
    license_plate       varchar(20),
    seat_count          integer,
    fuel_type           varchar(20),
    transmission        varchar(20),
    has_ac              boolean     not null default false,
    has_wifi            boolean     not null default false,
    color               varchar(50),
    status              varchar(20) not null default 'active',
    notes               text,
    created_at          timestamptz not null default now(),
    updated_at          timestamptz not null default now(),
    created_by          uuid        references users(id) on delete set null,
    updated_by          uuid        references users(id) on delete set null,
    constraint chk_provider_vehicles_status
        check (status in ('active', 'inactive', 'blocked'))
);

create index if not exists ix_provider_vehicles_provider_id
    on provider_vehicles(provider_id);

-- ── provider_vehicle_documents ─────────────────────────────────────────────────

create table if not exists provider_vehicle_documents (
    id              uuid        primary key default gen_random_uuid(),
    vehicle_id      uuid        not null references provider_vehicles(id) on delete cascade,
    document_type   varchar(50) not null,
    document_number varchar(100),
    issued_date     date,
    expiry_date     date,
    file_url        text,
    review_status   varchar(20) not null default 'pending',
    reviewed_by     uuid        references users(id) on delete set null,
    reviewed_at     timestamptz,
    review_note     text,
    created_at      timestamptz not null default now(),
    updated_at      timestamptz not null default now(),
    created_by      uuid        references users(id) on delete set null,
    updated_by      uuid        references users(id) on delete set null,
    constraint chk_pvd_review_status
        check (review_status in ('pending', 'approved', 'rejected', 'expired'))
);

create index if not exists ix_pvd_vehicle_id
    on provider_vehicle_documents(vehicle_id);
create index if not exists ix_pvd_review_status
    on provider_vehicle_documents(review_status);

-- ── service_routes ─────────────────────────────────────────────────────────────

create table if not exists service_routes (
    id                  uuid        primary key default gen_random_uuid(),
    provider_service_id uuid        not null references provider_services(id) on delete cascade,
    from_province       varchar(100) not null,
    to_province         varchar(100) not null,
    distance_km         numeric(8,2),
    duration_min        integer,
    price               numeric(18,2) not null,
    is_active           boolean     not null default true,
    notes               text,
    created_at          timestamptz not null default now(),
    updated_at          timestamptz not null default now()
);

create index if not exists ix_service_routes_svc_id
    on service_routes(provider_service_id);
create index if not exists ix_service_routes_from_to
    on service_routes(from_province, to_province);

-- ── service_route_schedules ────────────────────────────────────────────────────

create table if not exists service_route_schedules (
    id              uuid        primary key default gen_random_uuid(),
    route_id        uuid        not null references service_routes(id) on delete cascade,
    departure_time  time        not null,
    seat_count      integer     not null,
    is_active       boolean     not null default true,
    notes           text,
    created_at      timestamptz not null default now(),
    updated_at      timestamptz not null default now(),
    constraint uq_schedule_route_time unique (route_id, departure_time)
);

create index if not exists ix_srs_route_id
    on service_route_schedules(route_id);

-- ── provider_vehicle_availabilities ───────────────────────────────────────────

create table if not exists provider_vehicle_availabilities (
    id              uuid    primary key default gen_random_uuid(),
    vehicle_id      uuid    not null references provider_vehicles(id) on delete cascade,
    date            date    not null,
    is_blocked      boolean not null default true,
    blocked_reason  text,
    constraint uq_vehicle_availability_date unique (vehicle_id, date)
);

create index if not exists ix_pva_vehicle_id
    on provider_vehicle_availabilities(vehicle_id);
create index if not exists ix_pva_date
    on provider_vehicle_availabilities(date);
