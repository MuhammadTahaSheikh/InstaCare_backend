-- Run once on existing databases (phpMyAdmin or mysql CLI on VPS):
-- mysql -u user -p dbname < database/migrations/add_jazzcash_payments.sql

ALTER TABLE payments
  ADD COLUMN gateway_txn_ref VARCHAR(50) NULL AFTER transaction_id,
  ADD COLUMN cnic_last6 VARCHAR(6) NULL AFTER phone;
