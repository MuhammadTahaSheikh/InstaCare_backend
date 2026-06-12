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
  console.log('Running email verification migration...');

  if (!(await columnExists('users', 'email_verified'))) {
    await pool.query('ALTER TABLE users ADD COLUMN email_verified BOOLEAN DEFAULT FALSE');
    console.log('Added email_verified column');
  }

  if (!(await columnExists('users', 'verification_token'))) {
    await pool.query('ALTER TABLE users ADD COLUMN verification_token VARCHAR(255) NULL');
    console.log('Added verification_token column');
  }

  if (!(await columnExists('users', 'verification_token_expires_at'))) {
    await pool.query('ALTER TABLE users ADD COLUMN verification_token_expires_at TIMESTAMP NULL');
    console.log('Added verification_token_expires_at column');
  }

  const [result] = await pool.query(
    `UPDATE users SET email_verified = TRUE
     WHERE verification_token IS NULL AND (email_verified = FALSE OR email_verified IS NULL)`
  );
  console.log(`Marked ${result.affectedRows} existing user(s) as verified`);

  await pool.end();
  console.log('Migration complete.');
}

migrate().catch((err) => {
  console.error('Migration failed:', err.message);
  process.exit(1);
});
