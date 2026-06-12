-- OTP fallback when JazzCash SMS is unavailable (sandbox / API errors)
ALTER TABLE payments
  ADD COLUMN otp_hash VARCHAR(64) NULL AFTER cnic_last6,
  ADD COLUMN otp_expires_at DATETIME NULL AFTER otp_hash;
