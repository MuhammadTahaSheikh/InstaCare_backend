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
  console.log('Running doctor online status migration...');

  if (!(await columnExists('doctors', 'is_online'))) {
    await pool.query('ALTER TABLE doctors ADD COLUMN is_online BOOLEAN DEFAULT FALSE');
    console.log('Added is_online column');
  }

  await pool.end();
  console.log('Migration complete.');
}

migrate().catch((err) => {
  console.error('Migration failed:', err.message);
  process.exit(1);
});
