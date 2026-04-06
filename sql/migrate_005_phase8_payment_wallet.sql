-- =========================================================
-- PHASE 8 — PAYMENT & WALLET
-- Tables: wallets, wallet_transactions,
--         payment_transactions,
--         promotions, promotion_usages
-- =========================================================
-- Yêu cầu: Phase 7 đã được apply trước (bookings phải tồn tại)
-- =========================================================


-- ── 8.1  wallets ───────────────────────────────────────────────────────────────
-- Mỗi user (cả customer lẫn driver) có 1 ví duy nhất.
-- Driver thu tiền mặt → nền tảng khấu trừ hoa hồng vào ví.
-- Customer topup ví (VNPay/MoMo) để thanh toán online.

create table if not exists wallets (
    id          uuid          primary key default gen_random_uuid(),
    user_id     uuid          unique not null references users(id) on delete restrict,
    balance     numeric(18,2) not null default 0,
    currency    varchar(10)   not null default 'VND',
    is_frozen   boolean       not null default false,
    created_at  timestamptz   not null default now(),
    updated_at  timestamptz   not null default now(),

    constraint chk_wallets_currency
        check (currency in ('VND', 'USD'))
);

-- ── wallet_transactions ────────────────────────────────────────────────────────
-- Mọi biến động số dư đều tạo 1 dòng ở đây (immutable ledger).
-- amount > 0 = credit (nạp/hoàn/thưởng),  amount < 0 = debit (trả/rút/phí).

create table if not exists wallet_transactions (
    id              uuid          primary key default gen_random_uuid(),
    wallet_id       uuid          not null references wallets(id) on delete restrict,
    type            varchar(30)   not null,
    amount          numeric(18,2) not null,
    balance_after   numeric(18,2) not null,
    reference_id    uuid,                       -- booking_id hoặc payment_transaction_id
    reference_type  varchar(50),                -- 'booking' | 'payment_transaction' | 'admin_adjust'
    description     text,
    status          varchar(20)   not null default 'completed',
    created_at      timestamptz   not null default now(),

    constraint chk_wt_type
        check (type in ('topup', 'payment', 'refund', 'withdrawal',
                        'earning', 'commission', 'bonus', 'penalty', 'adjust')),
    constraint chk_wt_status
        check (status in ('pending', 'completed', 'failed', 'reversed'))
);

create index if not exists ix_wallet_transactions_wallet_id
    on wallet_transactions(wallet_id);
create index if not exists ix_wallet_transactions_reference
    on wallet_transactions(reference_type, reference_id);
create index if not exists ix_wallet_transactions_created_at
    on wallet_transactions(created_at desc);


-- ── 8.2  payment_transactions ──────────────────────────────────────────────────
-- Giao dịch thanh toán qua cổng (VNPay, MoMo, ZaloPay) hoặc tiền mặt.
-- 1 booking có thể có nhiều transaction (retry khi fail).

create table if not exists payment_transactions (
    id              uuid          primary key default gen_random_uuid(),
    booking_id      uuid          not null references bookings(id) on delete restrict,
    user_id         uuid          not null references users(id) on delete restrict,
    amount          numeric(18,2) not null,
    method          varchar(30)   not null,
    gateway_ref     varchar(200),               -- Mã giao dịch từ cổng thanh toán
    status          varchar(20)   not null default 'pending',
    paid_at         timestamptz,
    refunded_at     timestamptz,
    refund_amount   numeric(18,2),
    metadata        jsonb,                      -- response gốc từ cổng, dùng đối soát
    created_at      timestamptz   not null default now(),
    updated_at      timestamptz   not null default now(),

    constraint chk_pt_method
        check (method in ('cash', 'wallet', 'vnpay', 'momo', 'zalopay')),
    constraint chk_pt_status
        check (status in ('pending', 'completed', 'failed', 'refunded'))
);

create index if not exists ix_payment_transactions_booking_id
    on payment_transactions(booking_id);
create index if not exists ix_payment_transactions_user_id
    on payment_transactions(user_id);
create index if not exists ix_payment_transactions_status
    on payment_transactions(status);
create index if not exists ix_payment_transactions_gateway_ref
    on payment_transactions(gateway_ref)
    where gateway_ref is not null;


-- ── 8.3  promotions ────────────────────────────────────────────────────────────
-- Mã giảm giá / khuyến mãi do admin tạo.
-- service_types = NULL → áp dụng tất cả loại dịch vụ.

create table if not exists promotions (
    id              uuid          primary key default gen_random_uuid(),
    code            varchar(50)   unique not null,
    name            varchar(200)  not null,
    type            varchar(30)   not null,
    value           numeric(18,2) not null,     -- Giá trị giảm (% hoặc VNĐ tùy type)
    max_discount    numeric(18,2),              -- Giới hạn giảm tối đa (dùng khi type=percent)
    min_fare        numeric(18,2),              -- Đơn hàng tối thiểu để áp dụng
    usage_limit     integer,                    -- Tổng lượt dùng tối đa (NULL = không giới hạn)
    used_count      integer       not null default 0,
    per_user_limit  integer       default 1,    -- Mỗi user được dùng tối đa bao nhiêu lần
    valid_from      timestamptz   not null,
    valid_to        timestamptz   not null,
    service_types   jsonb,                      -- ["taxi","xe_om"] hoặc NULL = tất cả
    is_active       boolean       not null default true,
    created_at      timestamptz   not null default now(),
    updated_at      timestamptz   not null default now(),

    constraint chk_promotions_type
        check (type in ('percent', 'fixed', 'free_trip')),
    constraint chk_promotions_value_positive
        check (value > 0),
    constraint chk_promotions_date_range
        check (valid_to > valid_from)
);

create index if not exists ix_promotions_code
    on promotions(code);
create index if not exists ix_promotions_active_valid
    on promotions(is_active, valid_from, valid_to);

-- ── promotion_usages ───────────────────────────────────────────────────────────
-- Ghi nhận mỗi lần user dùng mã giảm giá cho 1 booking.

create table if not exists promotion_usages (
    id              uuid          primary key default gen_random_uuid(),
    promotion_id    uuid          not null references promotions(id) on delete restrict,
    user_id         uuid          not null references users(id) on delete restrict,
    booking_id      uuid          not null references bookings(id) on delete restrict,
    discount_amount numeric(18,2) not null,
    used_at         timestamptz   not null default now(),

    constraint uq_promotion_booking unique (promotion_id, booking_id)
);

create index if not exists ix_promotion_usages_promotion_id
    on promotion_usages(promotion_id);
create index if not exists ix_promotion_usages_user_id
    on promotion_usages(user_id);
create index if not exists ix_promotion_usages_booking_id
    on promotion_usages(booking_id);
create index if not exists ix_promotion_usages_user_promo
    on promotion_usages(user_id, promotion_id);
