import pool from '../config/db.js';

export async function getHospitals(req, res) {
  try {
    const { city, search } = req.query;
    let query = `
      SELECT h.*, c.name AS city_name, c.slug AS city_slug
      FROM hospitals h
      JOIN cities c ON h.city_id = c.id
      WHERE 1=1
    `;
    const params = [];

    if (city) {
      query += ' AND c.slug = ?';
      params.push(city);
    }
    if (search) {
      query += ' AND h.name LIKE ?';
      params.push(`%${search}%`);
    }

    query += ' ORDER BY h.rating DESC';
    const [hospitals] = await pool.query(query, params);
    res.json(hospitals);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
}

export async function getHospitalById(req, res) {
  try {
    const [hospitals] = await pool.query(
      `SELECT h.*, c.name AS city_name
       FROM hospitals h
       JOIN cities c ON h.city_id = c.id
       WHERE h.id = ?`,
      [req.params.id]
    );

    if (hospitals.length === 0) {
      return res.status(404).json({ error: 'Hospital not found' });
    }

    const [doctors] = await pool.query(
      `SELECT d.id, u.name, s.name AS specialty_name, d.consultation_fee, d.rating
       FROM doctors d
       JOIN users u ON d.user_id = u.id
       JOIN specialties s ON d.specialty_id = s.id
       WHERE d.hospital_id = ?`,
      [req.params.id]
    );

    res.json({ ...hospitals[0], doctors });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
}
