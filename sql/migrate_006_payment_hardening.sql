-- =========================================================
-- PHASE 8.5 — PAYMENT HARDENING
-- Bổ sung các unique index, constraint và cột để chống các
-- lỗ hổng bảo mật: Double-spending, Idempotency, etc.
-- =========================================================

-- 1. Chống Double Credit (Nạp tiền 2 lần từ webhook retry)
-- Bổ sung cột gateway_ref để lưu mã giao dịch từ VNPAY/MoMo/ZaloPay.
-- Thêm Unique Index chỉ nhắm vào giao dịch nạp tiền thành công.

ALTER TABLE wallet_transactions 
ADD COLUMN IF NOT EXISTS gateway_ref VARCHAR(200);

-- Unique index ngăn ngừa ghi đúp giao dịch nạp tiền
CREATE UNIQUE INDEX IF NOT EXISTS uq_wt_topup_gateway_ref
ON wallet_transactions (gateway_ref)
WHERE type = 'topup' AND status = 'completed' AND gateway_ref IS NOT NULL;

-- 2. Hàng rào cuối cùng cho số dư (Floor limit)
-- WALLET_NEGATIVE_FLOOR trong constants = -500,000 VND 
-- (sử dụng khi thu tiền hoa hồng mà driver chạy cuốc tiền mặt).
-- Không cho phép số dư âm quá mức này.

ALTER TABLE wallets
ADD CONSTRAINT chk_wallets_balance_floor
CHECK (balance >= -500000);

-- 3. Payment Transactions Unique Index
-- Đảm bảo mỗi giao dịch từ cổng thanh toán cũng chỉ được lưu 1 lần
CREATE UNIQUE INDEX IF NOT EXISTS uq_pt_gateway_ref
ON payment_transactions (gateway_ref)
WHERE status = 'completed' AND gateway_ref IS NOT NULL AND method != 'cash';
