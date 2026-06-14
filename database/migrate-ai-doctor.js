import pool from '../src/config/db.js';

async function tableExists(table) {
  const [rows] = await pool.query(
    `SELECT COUNT(*) AS count FROM information_schema.TABLES
     WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = ?`,
    [table]
  );
  return rows[0].count > 0;
}

async function migrate() {
  console.log('Running AI Doctor migration...');

  if (!(await tableExists('ai_consultations'))) {
    await pool.query(`
      CREATE TABLE ai_consultations (
        id VARCHAR(36) PRIMARY KEY,
        user_id INT NULL,
        city_slug VARCHAR(100) DEFAULT 'lahore',
        status ENUM('active', 'completed') DEFAULT 'active',
        summary JSON NULL,
        recommended_doctors JSON NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        completed_at TIMESTAMP NULL,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
      )
    `);
    console.log('Created ai_consultations table');
  }

  if (!(await tableExists('ai_consultation_messages'))) {
    await pool.query(`
      CREATE TABLE ai_consultation_messages (
        id INT AUTO_INCREMENT PRIMARY KEY,
        consultation_id VARCHAR(36) NOT NULL,
        role ENUM('user', 'assistant') NOT NULL,
        content TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (consultation_id) REFERENCES ai_consultations(id) ON DELETE CASCADE,
        INDEX idx_consultation (consultation_id)
      )
    `);
    console.log('Created ai_consultation_messages table');
  }

  const [genderCol] = await pool.query(
    `SELECT COUNT(*) AS count FROM information_schema.COLUMNS
     WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'ai_consultations' AND COLUMN_NAME = 'doctor_gender'`
  );
  if (genderCol[0].count === 0) {
    await pool.query(`
      ALTER TABLE ai_consultations
        ADD COLUMN doctor_gender ENUM('male', 'female') NOT NULL DEFAULT 'male' AFTER city_slug,
        ADD COLUMN preferred_language VARCHAR(5) NOT NULL DEFAULT 'en' AFTER doctor_gender,
        ADD COLUMN roman_urdu TINYINT(1) NOT NULL DEFAULT 0 AFTER preferred_language
    `);
    console.log('Added AI Doctor preference columns');
  }

  await pool.end();
  console.log('Migration complete.');
}

migrate().catch((err) => {
  console.error('Migration failed:', err.message);
  process.exit(1);
});
