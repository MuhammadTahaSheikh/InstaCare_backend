import pool from '../config/db.js';

export async function getLabs(req, res) {
  try {
    const { city, search } = req.query;
    let query = `
      SELECT l.*, c.name AS city_name, c.slug AS city_slug
      FROM labs l
      JOIN cities c ON l.city_id = c.id
      WHERE 1=1
    `;
    const params = [];

    if (city) {
      query += ' AND c.slug = ?';
      params.push(city);
    }
    if (search) {
      query += ' AND l.name LIKE ?';
      params.push(`%${search}%`);
    }

    query += ' ORDER BY l.rating DESC';
    const [labs] = await pool.query(query, params);
    res.json(labs);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
}

export async function getLabById(req, res) {
  try {
    const [labs] = await pool.query(
      `SELECT l.*, c.name AS city_name
       FROM labs l
       JOIN cities c ON l.city_id = c.id
       WHERE l.id = ?`,
      [req.params.id]
    );

    if (labs.length === 0) {
      return res.status(404).json({ error: 'Lab not found' });
    }

    const [tests] = await pool.query('SELECT * FROM lab_tests WHERE lab_id = ?', [req.params.id]);
    res.json({ ...labs[0], tests });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
}

export async function getLabTests(req, res) {
  try {
    const { lab_id, search } = req.query;
    let query = `
      SELECT lt.*, l.name AS lab_name, l.discount_percent
      FROM lab_tests lt
      JOIN labs l ON lt.lab_id = l.id
      WHERE 1=1
    `;
    const params = [];

    if (lab_id) {
      query += ' AND lt.lab_id = ?';
      params.push(lab_id);
    }
    if (search) {
      query += ' AND lt.name LIKE ?';
      params.push(`%${search}%`);
    }

    const [tests] = await pool.query(query, params);
    res.json(tests);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
}
