create extension if not exists pgcrypto;
create extension if not exists pg_trgm;

-- =========================================================
-- USERS
-- =========================================================

create table if not exists users (
    id uuid primary key default gen_random_uuid(),
    phone varchar(20),
    full_name varchar(255),
    password_hash text,
    gender smallint,
    avatar_url text,
    dob date,
    address_line text,
    status varchar(30) not null default 'active',
    account_source varchar(30) not null default 'self_register',
    phone_verified boolean not null default false,
    claimed_at timestamptz,
    last_login_at timestamptz,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    identity_verification_status varchar(30) not null default 'unverified',
    identity_verified_at timestamptz,
    latest_identity_verification_id uuid,
    constraint chk_users_status check (status in ('active', 'pending_activation', 'suspended', 'blocked', 'deleted')),
    constraint chk_users_account_source check (account_source in ('self_register', 'admin_created', 'imported')),
    constraint chk_users_gender check (gender is null or gender in (0, 1)),
    constraint chk_users_identity_verification_status
        check (identity_verification_status in ('unverified', 'pending', 'processing', 'verified', 'rejected', 'expired'))
);

create unique index if not exists ux_users_phone
on users(phone)
where phone is not null;

create table if not exists user_roles (
    id uuid primary key default gen_random_uuid(),
    user_id uuid not null references users(id) on delete cascade,
    role_code varchar(30) not null,
    created_at timestamptz not null default now(),
    constraint chk_user_roles_role_code
        check (role_code in ('customer', 'provider_owner', 'provider_staff', 'admin')),
    constraint uq_user_roles unique (user_id, role_code)
);

create table if not exists user_profiles (
    user_id uuid primary key references users(id) on delete cascade,
    bio text,
    preferred_language varchar(20) default 'vi',
    timezone varchar(50) default 'Asia/Ho_Chi_Minh',
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create table if not exists user_status_logs (
    id uuid primary key default gen_random_uuid(),
    user_id uuid not null references users(id) on delete cascade,
    old_status varchar(30),
    new_status varchar(30),
    changed_by uuid references users(id),
    reason text,
    created_at timestamptz not null default now()
);

create index if not exists idx_user_roles_user_id on user_roles(user_id);
create index if not exists idx_user_status_logs_user_id on user_status_logs(user_id);

-- =========================================================
-- AUTH: OTP + REFRESH TOKENS (PHONE ONLY)
-- =========================================================

create table if not exists otp_sessions (
    id uuid primary key default gen_random_uuid(),
    phone varchar(20) not null,
    otp_code_hash text not null,
    expires_at timestamptz not null,
    attempt_count int not null default 0,
    is_used boolean not null default false,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create index if not exists idx_otp_sessions_phone_expires_at
on otp_sessions(phone, expires_at);

create table if not exists refresh_tokens (
    id uuid primary key default gen_random_uuid(),
    user_id uuid not null references users(id) on delete cascade,
    jti varchar(64) not null,
    expires_at timestamptz not null,
    revoked_at timestamptz,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    constraint uq_refresh_tokens_jti unique (jti)
);

create index if not exists idx_refresh_tokens_user_id on refresh_tokens(user_id);

-- =========================================================
-- PROVIDERS
-- =========================================================

create table if not exists providers (
    id uuid primary key default gen_random_uuid(),
    owner_user_id uuid not null references users(id) on delete restrict,
    provider_type varchar(20) not null,
    description text,
    verification_status varchar(30) not null default 'pending',
    status varchar(30) not null default 'active',
    avg_rating numeric(3,2) not null default 0,
    total_reviews int not null default 0,
    total_jobs_completed int not null default 0,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    constraint chk_providers_type check (provider_type in ('individual', 'business')),
    constraint chk_providers_verification_status check (verification_status in ('pending', 'approved', 'rejected', 'suspended')),
    constraint chk_providers_status check (status in ('active', 'inactive', 'blocked'))
);

create table if not exists provider_individual_profiles (
    provider_id uuid primary key references providers(id) on delete cascade,
    full_name varchar(255),
    exe_year int,
    cccd varchar(50),
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create table if not exists provider_business_profiles (
    provider_id uuid primary key references providers(id) on delete cascade,
    company_name varchar(255) not null,
    exe_year int,
    legal_name varchar(255),
    tax_code varchar(50),
    business_license_number varchar(100),
    representative_name varchar(255),
    representative_position varchar(255),
    founded_date date,
    hotline varchar(20),
    website_url text,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create table if not exists provider_documents (
    id uuid primary key default gen_random_uuid(),
    provider_id uuid not null references providers(id) on delete cascade,
    document_type varchar(50) not null,
    document_name varchar(255),
    document_number varchar(100),
    issued_by varchar(255),
    issued_date date,
    expiry_date date,
    front_file_url text,
    back_file_url text,
    extra_file_url text,
    verification_status varchar(30) not null default 'pending',
    reviewed_by uuid references users(id),
    reviewed_at timestamptz,
    rejection_reason text,
    note text,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    constraint chk_provider_documents_status check (verification_status in ('pending', 'approved', 'rejected', 'expired'))
);

create table if not exists provider_status_logs (
    id uuid primary key default gen_random_uuid(),
    provider_id uuid not null references providers(id) on delete cascade,
    old_status varchar(30),
    new_status varchar(30) not null,
    changed_by uuid references users(id),
    reason text,
    created_at timestamptz not null default now()
);

create index if not exists idx_providers_owner_user_id on providers(owner_user_id);
create index if not exists idx_provider_documents_provider_id on provider_documents(provider_id);
create index if not exists idx_provider_status_logs_provider_id on provider_status_logs(provider_id);

-- =========================================================
-- SERVICE TAXONOMY
-- =========================================================

create table if not exists industry_categories (
    id uuid primary key default gen_random_uuid(),
    code varchar(50),
    name varchar(50),
    description text,
    is_active boolean not null default true,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    constraint uq_industry_categories_code unique (code)
);

create table if not exists service_categories (
    id uuid primary key default gen_random_uuid(),
    industry_category_id uuid not null references industry_categories(id) on delete cascade,
    code varchar(50),
    name varchar(255),
    description text,
    is_active boolean not null default true,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    constraint uq_service_categories_code_per_industry unique (industry_category_id, code)
);

create table if not exists service_skills (
    id uuid primary key default gen_random_uuid(),
    service_category_id uuid not null references service_categories(id) on delete cascade,
    code varchar(50) not null,
    name varchar(255) not null,
    description text,
    is_active boolean not null default true,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    constraint uq_service_skills_code_per_category unique (service_category_id, code)
);

create table if not exists service_category_attributes (
    id uuid primary key default gen_random_uuid(),
    service_category_id uuid not null references service_categories(id) on delete cascade,
    attr_key varchar(100) not null,
    attr_label varchar(255) not null,
    data_type varchar(30) not null,
    is_required boolean not null default false,
    is_filterable boolean not null default false,
    is_searchable boolean not null default false,
    default_value text,
    placeholder text,
    help_text text,
    options_json jsonb,
    validation_json jsonb,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    constraint uq_service_category_attributes_key unique (service_category_id, attr_key),
    constraint chk_service_category_attributes_data_type
        check (data_type in ('text', 'textarea', 'number', 'boolean', 'date', 'select', 'multiselect', 'json'))
);

create table if not exists service_category_requirements (
    id uuid primary key default gen_random_uuid(),
    service_category_id uuid not null references service_categories(id) on delete cascade,
    requirement_type varchar(50) not null,
    requirement_code varchar(100) not null,
    requirement_name varchar(255) not null,
    description text,
    is_required boolean not null default true,
    applies_to_provider_type varchar(20) not null default 'all',
    is_active boolean not null default true,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    constraint chk_service_category_requirements_provider_type
        check (applies_to_provider_type in ('individual', 'business', 'all')),
    constraint uq_service_category_requirements unique (service_category_id, requirement_code)
);

create index if not exists idx_service_categories_industry_id on service_categories(industry_category_id);
create index if not exists idx_service_skills_category_id on service_skills(service_category_id);

-- =========================================================
-- PROVIDER SERVICES
-- =========================================================

create table if not exists provider_services (
    id uuid primary key default gen_random_uuid(),
    provider_id uuid not null references providers(id) on delete cascade,
    industry_category_id uuid not null references industry_categories(id) on delete restrict,
    service_category_id uuid not null references service_categories(id) on delete restrict,
    service_skill_id uuid references service_skills(id) on delete restrict,
    exe_year int,
    pricing_type varchar(30) not null default 'negotiable',
    base_price numeric(18,2),
    price_unit varchar(30),
    description text,
    is_primary boolean not null default false,
    is_active boolean not null default true,
    verification_status varchar(30) not null default 'pending',
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    constraint chk_provider_services_pricing_type
        check (pricing_type in ('negotiable', 'fixed', 'hourly', 'survey')),
    constraint chk_provider_services_verification_status
        check (verification_status in ('pending', 'approved', 'rejected'))
);

create unique index if not exists uq_provider_services_unique
on provider_services (
    provider_id,
    industry_category_id,
    service_category_id,
    coalesce(service_skill_id, '00000000-0000-0000-0000-000000000000'::uuid)
);

create table if not exists provider_service_attributes (
    id uuid primary key default gen_random_uuid(),
    provider_service_id uuid not null references provider_services(id) on delete cascade,
    attr_key varchar(100) not null,
    value_text text,
    value_number numeric(18,2),
    value_boolean boolean,
    value_json jsonb,
    created_at timestamptz not null default now()
);

create table if not exists provider_document_services (
    id uuid primary key default gen_random_uuid(),
    provider_document_id uuid not null references provider_documents(id) on delete cascade,
    provider_service_id uuid not null references provider_services(id) on delete cascade,
    created_at timestamptz not null default now(),
    constraint uq_provider_document_services unique (provider_document_id, provider_service_id)
);

create index if not exists idx_provider_services_provider_id on provider_services(provider_id);
create index if not exists idx_provider_services_category_id on provider_services(service_category_id);
create index if not exists idx_provider_service_attributes_service_id on provider_service_attributes(provider_service_id);
create index if not exists idx_provider_document_services_service_id on provider_document_services(provider_service_id);

-- =========================================================
-- USER IDENTITY / EKYC
-- =========================================================

create table if not exists user_identity_verifications (
    id uuid primary key default gen_random_uuid(),
    user_id uuid not null references users(id) on delete cascade,
    verification_type varchar(30) not null default 'cccd',
    status varchar(30) not null default 'draft',
    review_mode varchar(30) not null default 'hybrid',
    full_name_on_id varchar(255),
    date_of_birth_on_id date,
    gender_on_id smallint,
    id_number varchar(50),
    nationality varchar(100),
    place_of_origin text,
    place_of_residence text,
    issue_date date,
    expiry_date date,
    issuing_authority varchar(255),
    extracted_address text,
    ocr_confidence numeric(5,2),
    face_match_score numeric(5,2),
    liveness_score numeric(5,2),
    submitted_at timestamptz,
    processed_at timestamptz,
    reviewed_at timestamptz,
    reviewed_by uuid references users(id),
    rejection_reason text,
    note text,
    is_latest boolean not null default true,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    constraint chk_user_identity_verifications_type
        check (verification_type in ('cccd', 'passport', 'driver_license', 'other')),
    constraint chk_user_identity_verifications_status
        check (status in ('draft', 'submitted', 'processing', 'approved', 'rejected', 'expired', 'cancelled')),
    constraint chk_user_identity_verifications_review_mode
        check (review_mode in ('auto', 'manual', 'hybrid')),
    constraint chk_user_identity_verifications_gender
        check (gender_on_id is null or gender_on_id in (0, 1))
);

create unique index if not exists uq_user_identity_verifications_latest
on user_identity_verifications(user_id)
where is_latest = true;

create table if not exists user_identity_files (
    id uuid primary key default gen_random_uuid(),
    verification_id uuid not null references user_identity_verifications(id) on delete cascade,
    file_type varchar(30) not null,
    file_url text not null,
    storage_provider varchar(50),
    mime_type varchar(100),
    file_size bigint,
    checksum varchar(128),
    uploaded_by_user_id uuid references users(id),
    uploaded_at timestamptz not null default now(),
    is_active boolean not null default true,
    constraint chk_user_identity_files_type
        check (file_type in ('id_front', 'id_back', 'selfie', 'liveness_video', 'extracted_face', 'cropped_id_face'))
);

create table if not exists user_identity_verification_logs (
    id uuid primary key default gen_random_uuid(),
    verification_id uuid not null references user_identity_verifications(id) on delete cascade,
    step_name varchar(50) not null,
    provider_name varchar(100),
    request_payload_json jsonb,
    response_payload_json jsonb,
    status varchar(30) not null,
    score numeric(5,2),
    error_code varchar(50),
    error_message text,
    created_at timestamptz not null default now(),
    constraint chk_user_identity_verification_logs_status
        check (status in ('success', 'failed', 'skipped'))
);

create table if not exists user_identity_review_decisions (
    id uuid primary key default gen_random_uuid(),
    verification_id uuid not null references user_identity_verifications(id) on delete cascade,
    reviewer_user_id uuid not null references users(id),
    decision varchar(30) not null,
    reason text,
    metadata_json jsonb,
    created_at timestamptz not null default now(),
    constraint chk_user_identity_review_decisions_decision
        check (decision in ('approve', 'reject', 'request_resubmission'))
);

create index if not exists idx_user_identity_verifications_user_id on user_identity_verifications(user_id);
create index if not exists idx_user_identity_files_verification_id on user_identity_files(verification_id);
create index if not exists idx_user_identity_verification_logs_verification_id on user_identity_verification_logs(verification_id);
create index if not exists idx_user_identity_review_decisions_verification_id on user_identity_review_decisions(verification_id);

DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE constraint_name = 'fk_users_latest_identity_verification'
        AND table_name = 'users'
    ) THEN
        ALTER TABLE users
            ADD CONSTRAINT fk_users_latest_identity_verification
            FOREIGN KEY (latest_identity_verification_id)
            REFERENCES user_identity_verifications(id);
    END IF;
END $$;

-- =========================================================
-- POSTS / ADS CONTENT
-- =========================================================

create table if not exists post_categories (
    id uuid primary key default gen_random_uuid(),
    code varchar(50) not null,
    name varchar(255) not null,
    slug varchar(255) not null unique,
    description text,
    is_active boolean not null default true,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    constraint uq_post_categories_code unique (code)
);

create table if not exists posts (
    id uuid primary key default gen_random_uuid(),
    category_id uuid references post_categories(id) on delete set null,
    author_user_id uuid references users(id) on delete set null,
    provider_id uuid references providers(id) on delete set null,
    industry_category_id uuid references industry_categories(id) on delete set null,
    service_category_id uuid references service_categories(id) on delete set null,
    title varchar(500) not null,
    slug varchar(500) not null unique,
    summary text,
    content text not null,
    cover_image_url text,
    seo_title varchar(255),
    seo_description text,
    post_type varchar(30) not null default 'article',
    status varchar(30) not null default 'draft',
    visibility varchar(30) not null default 'public',
    published_at timestamptz,
    expired_at timestamptz,
    is_featured boolean not null default false,
    allow_indexing boolean not null default true,
    view_count int not null default 0,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    constraint chk_posts_type
        check (post_type in ('article', 'promotion', 'provider_profile', 'announcement', 'seo_landing')),
    constraint chk_posts_status
        check (status in ('draft', 'pending_review', 'published', 'hidden', 'archived')),
    constraint chk_posts_visibility
        check (visibility in ('public', 'private', 'provider_only'))
);

create table if not exists post_media (
    id uuid primary key default gen_random_uuid(),
    post_id uuid not null references posts(id) on delete cascade,
    media_type varchar(30) not null,
    file_url text not null,
    thumbnail_url text,
    title varchar(255),
    alt_text varchar(255),
    is_active boolean not null default true,
    created_at timestamptz not null default now(),
    constraint chk_post_media_type check (media_type in ('image', 'video', 'file'))
);

create index if not exists idx_posts_category_id on posts(category_id);
create index if not exists idx_posts_author_user_id on posts(author_user_id);
create index if not exists idx_posts_provider_id on posts(provider_id);
create index if not exists idx_posts_industry_category_id on posts(industry_category_id);
create index if not exists idx_posts_service_category_id on posts(service_category_id);
create index if not exists idx_posts_status on posts(status);
create index if not exists idx_posts_published_at on posts(published_at);
create index if not exists idx_post_media_post_id on post_media(post_id);
create index if not exists idx_posts_title_trgm on posts using gin (title gin_trgm_ops);