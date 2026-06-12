import pool from '../src/config/db.js';

async function columnExists(table, column) {
  const [rows] = await pool.query(
    `SELECT COUNT(*) AS count FROM information_schema.COLUMNS
     WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = ? AND COLUMN_NAME = ?`,
    [table, column]
  );
  return rows[0].count > 0;
}

async function migrate() {
  console.log('Running payment OTP migration...');

  if (!(await columnExists('payments', 'otp_hash'))) {
    await pool.query('ALTER TABLE payments ADD COLUMN otp_hash VARCHAR(64) NULL AFTER cnic_last6');
    console.log('Added otp_hash column');
  }

  if (!(await columnExists('payments', 'otp_expires_at'))) {
    await pool.query('ALTER TABLE payments ADD COLUMN otp_expires_at DATETIME NULL AFTER otp_hash');
    console.log('Added otp_expires_at column');
  }

  await pool.end();
  console.log('Migration complete.');
}

migrate().catch((err) => {
  console.error('Migration failed:', err.message);
  process.exit(1);
});
