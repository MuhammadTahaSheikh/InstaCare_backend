import pool from '../src/config/db.js';

// Matches frontend PKR_PER_USD (280) × $100
const CONSULTATION_FEE_PKR = 28000;

async function migrate() {
  console.log(`Setting all doctor consultation fees to $100 (${CONSULTATION_FEE_PKR} PKR)...`);

  const [result] = await pool.query(
    'UPDATE doctors SET consultation_fee = ?',
    [CONSULTATION_FEE_PKR]
  );

  console.log(`Updated ${result.affectedRows} doctor(s).`);
  await pool.end();
  console.log('Migration complete.');
}

migrate().catch((err) => {
  console.error('Migration failed:', err.message);
  process.exit(1);
});
