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
  console.log('Running Google auth migration...');

  if (!(await columnExists('users', 'google_id'))) {
    await pool.query('ALTER TABLE users ADD COLUMN google_id VARCHAR(255) NULL UNIQUE');
    console.log('Added google_id column');
  }

  const [passwordCol] = await pool.query(
    `SELECT IS_NULLABLE FROM information_schema.COLUMNS
     WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'users' AND COLUMN_NAME = 'password'`
  );
  if (passwordCol[0]?.IS_NULLABLE === 'NO') {
    await pool.query('ALTER TABLE users MODIFY password VARCHAR(255) NULL');
    console.log('Made password column nullable for Google-only accounts');
  }

  await pool.end();
  console.log('Migration complete.');
}

migrate().catch((err) => {
  console.error('Migration failed:', err.message);
  process.exit(1);
});
