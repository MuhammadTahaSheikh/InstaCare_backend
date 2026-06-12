-- Run once on existing databases:
-- mysql -u user -p dbname < database/migrations/add_email_verification.sql

ALTER TABLE users
  ADD COLUMN email_verified BOOLEAN DEFAULT FALSE,
  ADD COLUMN verification_token VARCHAR(255) NULL,
  ADD COLUMN verification_token_expires_at TIMESTAMP NULL;

-- Mark existing accounts as verified (skip pending signups that already have a token)
UPDATE users SET email_verified = TRUE
WHERE verification_token IS NULL AND (email_verified = FALSE OR email_verified IS NULL);
