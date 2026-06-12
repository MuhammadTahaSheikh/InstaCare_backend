import pool from '../config/db.js';

async function updateDoctorRating(doctorId) {
  await pool.query(
    `UPDATE doctors SET rating = (
      SELECT COALESCE(ROUND(AVG(rating), 1), 0) FROM reviews WHERE doctor_id = ?
    ) WHERE id = ?`,
    [doctorId, doctorId]
  );
}

export async function getDoctorReviews(req, res) {
  try {
    const [reviews] = await pool.query(
      `SELECT r.*, u.name AS user_name
       FROM reviews r
       JOIN users u ON r.user_id = u.id
       WHERE r.doctor_id = ?
       ORDER BY r.created_at DESC`,
      [req.params.doctorId]
    );
    res.json(reviews);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
}

export async function createReview(req, res) {
  try {
    const { doctor_id, rating, comment } = req.body;

    if (!doctor_id || !rating || rating < 1 || rating > 5) {
      return res.status(400).json({ error: 'Doctor ID and rating (1-5) are required' });
    }

    const [existing] = await pool.query(
      'SELECT id FROM reviews WHERE user_id = ? AND doctor_id = ?',
      [req.user.id, doctor_id]
    );
    if (existing.length > 0) {
      return res.status(409).json({ error: 'You have already reviewed this doctor' });
    }

    const [result] = await pool.query(
      'INSERT INTO reviews (user_id, doctor_id, rating, comment) VALUES (?, ?, ?, ?)',
      [req.user.id, doctor_id, rating, comment || null]
    );

    await updateDoctorRating(doctor_id);

    res.status(201).json({ message: 'Review submitted', id: result.insertId });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
}
