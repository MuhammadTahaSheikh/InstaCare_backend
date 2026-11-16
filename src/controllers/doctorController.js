import pool from '../config/db.js';

export async function getDoctors(req, res) {
  try {
    const { specialty, city, online, search } = req.query;
    let query = `
      SELECT d.*, u.name, u.email, u.phone,
             s.name AS specialty_name, s.slug AS specialty_slug,
             h.name AS hospital_name, c.name AS city_name
      FROM doctors d
      JOIN users u ON d.user_id = u.id
      JOIN specialties s ON d.specialty_id = s.id
      LEFT JOIN hospitals h ON d.hospital_id = h.id
      LEFT JOIN cities c ON h.city_id = c.id
      WHERE 1=1
    `;
    const params = [];

    if (specialty) {
      query += ' AND s.slug = ?';
      params.push(specialty);
    }
    if (city) {
      query += ' AND c.slug = ?';
      params.push(city);
    }
    if (online === 'true') {
      query += ' AND d.online_consultation = TRUE AND d.is_online = TRUE';
    }
    if (search) {
      query += ' AND (u.name LIKE ? OR s.name LIKE ?)';
      params.push(`%${search}%`, `%${search}%`);
    }

    query += ' ORDER BY d.rating DESC';
    const [doctors] = await pool.query(query, params);
    res.json(doctors);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
}

export async function getDoctorById(req, res) {
  try {
    const [doctors] = await pool.query(
      `SELECT d.*, u.name, u.email, u.phone,
              s.name AS specialty_name, s.slug AS specialty_slug,
              h.name AS hospital_name, h.address AS hospital_address,
              c.name AS city_name
       FROM doctors d
       JOIN users u ON d.user_id = u.id
       JOIN specialties s ON d.specialty_id = s.id
       LEFT JOIN hospitals h ON d.hospital_id = h.id
       LEFT JOIN cities c ON h.city_id = c.id
       WHERE d.id = ?`,
      [req.params.id]
    );

    if (doctors.length === 0) {
      return res.status(404).json({ error: 'Doctor not found' });
    }
    res.json(doctors[0]);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
}

export async function getMyAvailability(req, res) {
  try {
    const [rows] = await pool.query(
      'SELECT id, online_consultation, is_online FROM doctors WHERE user_id = ?',
      [req.user.id]
    );
    if (rows.length === 0) {
      return res.status(404).json({ error: 'Doctor profile not found' });
    }
    res.json(rows[0]);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
}

export async function setMyAvailability(req, res) {
  try {
    const { is_online } = req.body;
    if (typeof is_online !== 'boolean') {
      return res.status(400).json({ error: 'is_online must be true or false' });
    }

    const [rows] = await pool.query(
      'SELECT id, online_consultation FROM doctors WHERE user_id = ?',
      [req.user.id]
    );
    if (rows.length === 0) {
      return res.status(404).json({ error: 'Doctor profile not found' });
    }
    if (is_online && !rows[0].online_consultation) {
      return res.status(400).json({
        error: 'Online consultations are not enabled for your profile. Contact admin.',
      });
    }

    await pool.query('UPDATE doctors SET is_online = ? WHERE user_id = ?', [is_online, req.user.id]);
    res.json({ is_online, online_consultation: rows[0].online_consultation });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
}
