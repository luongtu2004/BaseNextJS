-- ==============================================================================
-- MIGRATION 007: Performance Indexes & PostGIS Spatial Support
-- ==============================================================================

-- ------------------------------------------------------------------------------
-- 1. ENABLE POSTGIS EXTENSION
-- ------------------------------------------------------------------------------
CREATE EXTENSION IF NOT EXISTS postgis;

-- ------------------------------------------------------------------------------
-- 2. PERFORMANCE INDEXES (Phase 6, 7, 8, 9)
-- ------------------------------------------------------------------------------

-- Bookings (Phase 7)
CREATE INDEX IF NOT EXISTS ix_bookings_customer_requested ON bookings (customer_id, requested_at DESC);
CREATE INDEX IF NOT EXISTS ix_bookings_provider_status ON bookings (provider_id, status);
CREATE INDEX IF NOT EXISTS ix_bookings_status_requested ON bookings (status, requested_at DESC);
CREATE INDEX IF NOT EXISTS ix_bookings_completed_at ON bookings (completed_at DESC) WHERE completed_at IS NOT NULL;
CREATE INDEX IF NOT EXISTS ix_bookings_pending_partial ON bookings (requested_at DESC) WHERE status = 'pending';
CREATE INDEX IF NOT EXISTS ix_bookings_pickup_coords ON bookings (pickup_lat, pickup_lng) WHERE pickup_lat IS NOT NULL AND pickup_lng IS NOT NULL;
CREATE INDEX IF NOT EXISTS ix_bookings_customer_payment ON bookings (customer_id, payment_status);

-- Booking Status Logs
CREATE INDEX IF NOT EXISTS ix_bsl_booking_created ON booking_status_logs (booking_id, created_at ASC);

-- Driver Availability Sessions
CREATE INDEX IF NOT EXISTS ix_das_provider_status ON driver_availability_sessions (provider_id, status);
CREATE INDEX IF NOT EXISTS ix_das_status_online_partial ON driver_availability_sessions (provider_id) WHERE status = 'online';

-- Wallets & Transactions (Phase 8)
CREATE INDEX IF NOT EXISTS ix_wallets_user_id ON wallets (user_id);
CREATE INDEX IF NOT EXISTS ix_wt_wallet_created ON wallet_transactions (wallet_id, created_at DESC);
CREATE INDEX IF NOT EXISTS ix_wt_wallet_type_created ON wallet_transactions (wallet_id, type, created_at DESC);
CREATE INDEX IF NOT EXISTS ix_wt_reference ON wallet_transactions (reference_id) WHERE reference_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS ix_wt_type_created ON wallet_transactions (type, created_at DESC);

-- Payment Transactions
CREATE INDEX IF NOT EXISTS ix_pt_booking ON payment_transactions (booking_id);
CREATE INDEX IF NOT EXISTS ix_pt_user_created ON payment_transactions (user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS ix_pt_pending_partial ON payment_transactions (gateway_ref) WHERE status = 'pending';

-- Promotions & Usages
CREATE INDEX IF NOT EXISTS ix_promotions_active ON promotions (is_active, valid_from, valid_to) WHERE is_active = true;
CREATE INDEX IF NOT EXISTS ix_pu_user_promotion ON promotion_usages (user_id, promotion_id);

-- Reviews (Phase 9)
CREATE INDEX IF NOT EXISTS ix_reviews_reviewer ON reviews (reviewer_id, created_at DESC);

-- Notification Settings
CREATE INDEX IF NOT EXISTS ix_ns_user_type_disabled ON notification_settings (notification_type, user_id) WHERE is_enabled = false;

-- ------------------------------------------------------------------------------
-- 3. POSTGIS SPATIAL COLUMNS (GEOGRAPHY POINT)
-- ------------------------------------------------------------------------------

-- ADD columns
ALTER TABLE driver_locations ADD COLUMN IF NOT EXISTS location GEOGRAPHY(POINT, 4326);
ALTER TABLE bookings ADD COLUMN IF NOT EXISTS pickup_point GEOGRAPHY(POINT, 4326);
ALTER TABLE bookings ADD COLUMN IF NOT EXISTS dropoff_point GEOGRAPHY(POINT, 4326);

-- BACKFILL existing numeric data into geography points
UPDATE driver_locations 
SET location = ST_SetSRID(ST_MakePoint(longitude::float, latitude::float), 4326)::geography 
WHERE latitude IS NOT NULL AND longitude IS NOT NULL AND location IS NULL;

UPDATE bookings 
SET pickup_point = ST_SetSRID(ST_MakePoint(pickup_lng::float, pickup_lat::float), 4326)::geography 
WHERE pickup_lat IS NOT NULL AND pickup_lng IS NOT NULL AND pickup_point IS NULL;

UPDATE bookings 
SET dropoff_point = ST_SetSRID(ST_MakePoint(dropoff_lng::float, dropoff_lat::float), 4326)::geography 
WHERE dropoff_lat IS NOT NULL AND dropoff_lng IS NOT NULL AND dropoff_point IS NULL;

-- SPATIAL GIST INDEXES
CREATE INDEX IF NOT EXISTS gix_driver_locations_loc ON driver_locations USING gist (location);
CREATE INDEX IF NOT EXISTS gix_bookings_pickup ON bookings USING gist (pickup_point);
CREATE INDEX IF NOT EXISTS gix_bookings_dropoff ON bookings USING gist (dropoff_point);

-- HOT QUERY GIST INDEX (for pending bookings spatial search)
CREATE INDEX IF NOT EXISTS gix_bookings_pending_pickup 
ON bookings USING gist (pickup_point) 
WHERE status = 'pending' AND pickup_point IS NOT NULL;
