-- Run once on existing databases
ALTER TABLE doctors ADD COLUMN is_online BOOLEAN DEFAULT FALSE;
