import bcrypt from 'bcryptjs';
import jwt from 'jsonwebtoken';
import pool from '../config/db.js';

export async function register(req, res) {
  try {
    const { name, email, password, phone, role: requestedRole = 'patient', city_id } = req.body;
    const role = ['patient', 'doctor'].includes(requestedRole) ? requestedRole : 'patient';

    if (!name || !email || !password) {
      return res.status(400).json({ error: 'Name, email, and password are required' });
    }

    const [existing] = await pool.query('SELECT id FROM users WHERE email = ?', [email]);
    if (existing.length > 0) {
      return res.status(409).json({ error: 'Email already registered' });
    }

    const hashed = await bcrypt.hash(password, 10);
    const [result] = await pool.query(
      'INSERT INTO users (name, email, password, phone, role, city_id) VALUES (?, ?, ?, ?, ?, ?)',
      [name, email, hashed, phone || null, role, city_id || null]
    );

    const token = jwt.sign(
      { id: result.insertId, email, role },
      process.env.JWT_SECRET,
      { expiresIn: '7d' }
    );

    res.status(201).json({
      message: 'Registration successful',
      token,
      user: { id: result.insertId, name, email, role },
    });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
}

export async function login(req, res) {
  try {
    const { email, password } = req.body;

    if (!email || !password) {
      return res.status(400).json({ error: 'Email and password are required' });
    }

    const [users] = await pool.query('SELECT * FROM users WHERE email = ?', [email]);
    if (users.length === 0) {
      return res.status(401).json({ error: 'Invalid credentials' });
    }

    const user = users[0];
    const valid = await bcrypt.compare(password, user.password);
    if (!valid) {
      return res.status(401).json({ error: 'Invalid credentials' });
    }

    const token = jwt.sign(
      { id: user.id, email: user.email, role: user.role },
      process.env.JWT_SECRET,
      { expiresIn: '7d' }
    );

    res.json({
      token,
      user: { id: user.id, name: user.name, email: user.email, role: user.role, city_id: user.city_id },
    });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
}

export async function getProfile(req, res) {
  try {
    const [users] = await pool.query(
      'SELECT id, name, email, phone, role, city_id, created_at FROM users WHERE id = ?',
      [req.user.id]
    );
    if (users.length === 0) {
      return res.status(404).json({ error: 'User not found' });
    }
    res.json(users[0]);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
}
