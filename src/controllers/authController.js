import crypto from 'crypto';
import bcrypt from 'bcryptjs';
import jwt from 'jsonwebtoken';
import pool from '../config/db.js';
import { sendVerificationEmail } from '../services/emailService.js';

const VERIFICATION_EXPIRY_HOURS = 24;

function normalizeEmail(email) {
  return email.trim().toLowerCase();
}

function createVerificationToken() {
  return crypto.randomBytes(32).toString('hex');
}

function verificationExpiry() {
  return new Date(Date.now() + VERIFICATION_EXPIRY_HOURS * 60 * 60 * 1000);
}

function buildVerifyUrl(token) {
  const base = (process.env.FRONTEND_URL || 'http://localhost:5173').replace(/\/$/, '');
  return `${base}/verify-email?token=${token}`;
}

export async function register(req, res) {
  try {
    const { name, email, password, phone, role: requestedRole = 'patient', city_id } = req.body;
    const role = ['patient', 'doctor'].includes(requestedRole) ? requestedRole : 'patient';

    if (!name || !email || !password) {
      return res.status(400).json({ error: 'Name, email, and password are required' });
    }

    const normalizedEmail = normalizeEmail(email);

    const [existing] = await pool.query('SELECT id FROM users WHERE email = ?', [normalizedEmail]);
    if (existing.length > 0) {
      return res.status(409).json({ error: 'Email already registered' });
    }

    const hashed = await bcrypt.hash(password, 10);
    const verificationToken = createVerificationToken();
    const tokenExpires = verificationExpiry();

    const [result] = await pool.query(
      `INSERT INTO users (name, email, password, phone, role, city_id, email_verified, verification_token, verification_token_expires_at)
       VALUES (?, ?, ?, ?, ?, ?, FALSE, ?, ?)`,
      [name, normalizedEmail, hashed, phone || null, role, city_id || null, verificationToken, tokenExpires]
    );

    const verifyUrl = buildVerifyUrl(verificationToken);
    await sendVerificationEmail({ to: normalizedEmail, name, verifyUrl });

    res.status(201).json({
      message: 'Registration successful. Please check your email to verify your account.',
      email: normalizedEmail,
      user: { id: result.insertId, name, email: normalizedEmail, role },
    });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
}

export async function verifyEmail(req, res) {
  try {
    const token = req.query.token || req.body.token;
    if (!token) {
      return res.status(400).json({ error: 'Verification token is required' });
    }

    const [users] = await pool.query(
      'SELECT id, email_verified, verification_token_expires_at FROM users WHERE verification_token = ?',
      [token]
    );

    if (users.length === 0) {
      return res.status(400).json({ error: 'Invalid or expired verification link' });
    }

    const user = users[0];
    if (user.email_verified) {
      return res.json({ message: 'Email already verified. You can log in.' });
    }

    if (new Date(user.verification_token_expires_at) < new Date()) {
      return res.status(400).json({ error: 'Verification link has expired. Please request a new one.' });
    }

    await pool.query(
      'UPDATE users SET email_verified = TRUE, verification_token = NULL, verification_token_expires_at = NULL WHERE id = ?',
      [user.id]
    );

    res.json({ message: 'Email verified successfully. You can now log in.' });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
}

export async function resendVerification(req, res) {
  try {
    const { email } = req.body;
    if (!email) {
      return res.status(400).json({ error: 'Email is required' });
    }

    const normalizedEmail = normalizeEmail(email);
    const [users] = await pool.query(
      'SELECT id, name, email_verified FROM users WHERE email = ?',
      [normalizedEmail]
    );

    if (users.length === 0) {
      return res.json({ message: 'If an account exists with this email, a verification link has been sent.' });
    }

    const user = users[0];
    if (user.email_verified) {
      return res.json({ message: 'This email is already verified. You can log in.' });
    }

    const verificationToken = createVerificationToken();
    const tokenExpires = verificationExpiry();

    await pool.query(
      'UPDATE users SET verification_token = ?, verification_token_expires_at = ? WHERE id = ?',
      [verificationToken, tokenExpires, user.id]
    );

    const verifyUrl = buildVerifyUrl(verificationToken);
    await sendVerificationEmail({ to: normalizedEmail, name: user.name, verifyUrl });

    res.json({ message: 'If an account exists with this email, a verification link has been sent.' });
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

    const normalizedEmail = normalizeEmail(email);
    const [users] = await pool.query('SELECT * FROM users WHERE email = ?', [normalizedEmail]);
    if (users.length === 0) {
      return res.status(401).json({ error: 'Invalid credentials' });
    }

    const user = users[0];
    const valid = await bcrypt.compare(password, user.password);
    if (!valid) {
      return res.status(401).json({ error: 'Invalid credentials' });
    }

    if (!user.email_verified) {
      return res.status(403).json({
        error: 'Please verify your email before logging in.',
        code: 'EMAIL_NOT_VERIFIED',
        email: user.email,
      });
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
      'SELECT id, name, email, phone, role, city_id, email_verified, created_at FROM users WHERE id = ?',
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
