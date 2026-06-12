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
  console.log('Running JazzCash payments migration...');

  if (!(await columnExists('payments', 'gateway_txn_ref'))) {
    await pool.query('ALTER TABLE payments ADD COLUMN gateway_txn_ref VARCHAR(50) NULL AFTER transaction_id');
    console.log('Added gateway_txn_ref column');
  }

  if (!(await columnExists('payments', 'cnic_last6'))) {
    await pool.query('ALTER TABLE payments ADD COLUMN cnic_last6 VARCHAR(6) NULL AFTER phone');
    console.log('Added cnic_last6 column');
  }

  await pool.end();
  console.log('Migration complete.');
}

migrate().catch((err) => {
  console.error('Migration failed:', err.message);
  process.exit(1);
});
