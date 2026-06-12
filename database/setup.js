import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import mysql from 'mysql2/promise';
import bcrypt from 'bcryptjs';
import '../src/config/env.js';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

async function setup() {
  const dbName = process.env.DB_NAME || 'bestechcare';
  const host = process.env.DB_HOST || 'localhost';
  const user = process.env.DB_USER || 'root';
  const password = process.env.DB_PASSWORD || '';

  // Connect without database first (needed for local MySQL)
  const connection = await mysql.createConnection({
    host,
    user,
    password,
    multipleStatements: true,
  });

  const isLocal = host === 'localhost' || host === '127.0.0.1';
  console.log(`Setting up database: ${dbName} on ${host}`);

  if (isLocal) {
    await connection.query(`DROP DATABASE IF EXISTS \`${dbName}\``);
    await connection.query(`CREATE DATABASE \`${dbName}\``);
  } else {
    await connection.query(`CREATE DATABASE IF NOT EXISTS \`${dbName}\``);
  }
  await connection.query(`USE \`${dbName}\``);

  console.log('Running schema...');
  const schema = fs.readFileSync(path.join(__dirname, 'schema.sql'), 'utf8');
  await connection.query(schema);

  console.log('Seeding data...');
  const seed = fs.readFileSync(path.join(__dirname, 'seed.sql'), 'utf8');
  await connection.query(seed);

  const hashedPassword = await bcrypt.hash('password123', 10);
  await connection.query('UPDATE users SET password = ?', [hashedPassword]);

  console.log('Database setup complete!');
  console.log('Demo logins:');
  console.log('  Patient: patient@example.com / password123');
  console.log('  Doctor:  ayesha.khan@example.com / password123');
  console.log('  Admin:   admin@bestechcare.pk / password123');
  await connection.end();
}

setup().catch((err) => {
  console.error('Setup failed:', err.message);
  if (err.message.includes('Access denied')) {
    console.error('\nTip: For local dev, run `cp .env.local.example .env.local` (MySQL user: root).');
    console.error('     Hostinger DB_USER only works when deployed on Hostinger.');
  }
  process.exit(1);
});
