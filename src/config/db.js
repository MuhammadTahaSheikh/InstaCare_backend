import dns from 'dns';
import mysql from 'mysql2/promise';
import './env.js';

// Hostinger Remote MySQL whitelists IPv4; prefer it over IPv6 on VPS
dns.setDefaultResultOrder('ipv4first');

const pool = mysql.createPool({
  host: process.env.DB_HOST || 'localhost',
  user: process.env.DB_USER || 'root',
  password: process.env.DB_PASSWORD || '',
  database: process.env.DB_NAME || 'bestechcare',
  waitForConnections: true,
  connectionLimit: 10,
});

export default pool;
