import bcrypt from 'bcryptjs';
import pool from '../config/db.js';

function toSlug(name) {
  return name.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');
}

export async function getStats(req, res) {
  try {
    const [[users]] = await pool.query('SELECT COUNT(*) AS count FROM users');
    const [[doctors]] = await pool.query('SELECT COUNT(*) AS count FROM doctors');
    const [[hospitals]] = await pool.query('SELECT COUNT(*) AS count FROM hospitals');
    const [[appointments]] = await pool.query('SELECT COUNT(*) AS count FROM appointments');
    const [[orders]] = await pool.query('SELECT COUNT(*) AS count FROM orders');
    const [[medicines]] = await pool.query('SELECT COUNT(*) AS count FROM medicines WHERE is_active = TRUE');
    const [[pendingAppts]] = await pool.query(
      "SELECT COUNT(*) AS count FROM appointments WHERE status = 'pending'"
    );
    const [[revenue]] = await pool.query(
      "SELECT COALESCE(SUM(total_amount), 0) AS total FROM orders WHERE status != 'cancelled'"
    );

    res.json({
      users: users.count,
      doctors: doctors.count,
      hospitals: hospitals.count,
      appointments: appointments.count,
      pending_appointments: pendingAppts.count,
      orders: orders.count,
      medicines: medicines.count,
      revenue: revenue.total,
    });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
}

export async function getAllAppointments(req, res) {
  try {
    const [appointments] = await pool.query(
      `SELECT a.*, u.name AS patient_name, du.name AS doctor_name, s.name AS specialty_name
       FROM appointments a
       JOIN users u ON a.patient_id = u.id
       JOIN doctors d ON a.doctor_id = d.id
       JOIN users du ON d.user_id = du.id
       JOIN specialties s ON d.specialty_id = s.id
       ORDER BY a.appointment_date DESC, a.appointment_time DESC`
    );
    res.json(appointments);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
}

export async function updateAppointmentStatus(req, res) {
  try {
    const { status } = req.body;
    const valid = ['pending', 'confirmed', 'completed', 'cancelled'];
    if (!valid.includes(status)) {
      return res.status(400).json({ error: 'Invalid status' });
    }

    const [result] = await pool.query(
      'UPDATE appointments SET status = ? WHERE id = ?',
      [status, req.params.id]
    );
    if (result.affectedRows === 0) {
      return res.status(404).json({ error: 'Appointment not found' });
    }
    res.json({ message: 'Status updated' });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
}

export async function getAllDoctors(req, res) {
  try {
    const [doctors] = await pool.query(
      `SELECT d.*, u.name, u.email, s.name AS specialty_name
       FROM doctors d
       JOIN users u ON d.user_id = u.id
       JOIN specialties s ON d.specialty_id = s.id
       ORDER BY d.created_at DESC`
    );
    res.json(doctors);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
}

export async function verifyDoctor(req, res) {
  try {
    const { is_verified } = req.body;
    await pool.query('UPDATE doctors SET is_verified = ? WHERE id = ?', [!!is_verified, req.params.id]);
    res.json({ message: 'Doctor updated' });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
}

export async function createDoctor(req, res) {
  const conn = await pool.getConnection();
  try {
    const {
      name, email, password, phone, city_id,
      specialty_id, hospital_id, qualification, experience_years,
      consultation_fee, online_consultation, in_clinic, bio, is_verified,
    } = req.body;

    if (!name || !email || !password || !specialty_id) {
      return res.status(400).json({ error: 'Name, email, password, and specialty are required' });
    }

    const normalizedEmail = email.trim().toLowerCase();
    const [existing] = await conn.query('SELECT id FROM users WHERE email = ?', [normalizedEmail]);
    if (existing.length > 0) {
      return res.status(409).json({ error: 'Email already registered' });
    }

    await conn.beginTransaction();
    const hashed = await bcrypt.hash(password, 10);
    const [userResult] = await conn.query(
      `INSERT INTO users (name, email, password, phone, role, city_id, email_verified)
       VALUES (?, ?, ?, ?, 'doctor', ?, TRUE)`,
      [name, normalizedEmail, hashed, phone || null, city_id || null]
    );

    const [doctorResult] = await conn.query(
      `INSERT INTO doctors (user_id, specialty_id, hospital_id, qualification, experience_years,
        consultation_fee, online_consultation, in_clinic, bio, is_verified)
       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`,
      [
        userResult.insertId,
        specialty_id,
        hospital_id || null,
        qualification || null,
        experience_years || 0,
        consultation_fee || 0,
        online_consultation !== false,
        in_clinic !== false,
        bio || null,
        is_verified !== false,
      ]
    );

    await conn.commit();
    res.status(201).json({ id: doctorResult.insertId, user_id: userResult.insertId });
  } catch (err) {
    await conn.rollback();
    res.status(500).json({ error: err.message });
  } finally {
    conn.release();
  }
}

export async function getAllHospitals(req, res) {
  try {
    const [hospitals] = await pool.query(
      `SELECT h.*, c.name AS city_name FROM hospitals h
       JOIN cities c ON h.city_id = c.id ORDER BY h.name`
    );
    res.json(hospitals);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
}

export async function verifyHospital(req, res) {
  try {
    const { is_verified } = req.body;
    await pool.query('UPDATE hospitals SET is_verified = ? WHERE id = ?', [!!is_verified, req.params.id]);
    res.json({ message: 'Hospital updated' });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
}

export async function createHospital(req, res) {
  try {
    const { name, slug, description, address, city_id, phone, is_verified } = req.body;
    if (!name || !city_id) {
      return res.status(400).json({ error: 'Name and city are required' });
    }

    const hospitalSlug = slug || toSlug(name);
    const [result] = await pool.query(
      `INSERT INTO hospitals (name, slug, description, address, city_id, phone, is_verified)
       VALUES (?, ?, ?, ?, ?, ?, ?)`,
      [name, hospitalSlug, description || null, address || null, city_id, phone || null, is_verified !== false]
    );
    res.status(201).json({ id: result.insertId });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
}

export async function getAllLabs(req, res) {
  try {
    const [labs] = await pool.query(
      `SELECT l.*, c.name AS city_name FROM labs l
       JOIN cities c ON l.city_id = c.id ORDER BY l.name`
    );
    res.json(labs);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
}

export async function createLab(req, res) {
  try {
    const { name, slug, description, city_id, phone, discount_percent } = req.body;
    if (!name || !city_id) {
      return res.status(400).json({ error: 'Name and city are required' });
    }

    const labSlug = slug || toSlug(name);
    const [result] = await pool.query(
      `INSERT INTO labs (name, slug, description, city_id, phone, discount_percent)
       VALUES (?, ?, ?, ?, ?, ?)`,
      [name, labSlug, description || null, city_id, phone || null, discount_percent || 0]
    );
    res.status(201).json({ id: result.insertId });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
}

export async function getAllLabTests(req, res) {
  try {
    const [tests] = await pool.query(
      `SELECT t.*, l.name AS lab_name FROM lab_tests t
       JOIN labs l ON t.lab_id = l.id ORDER BY l.name, t.name`
    );
    res.json(tests);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
}

export async function createLabTest(req, res) {
  try {
    const { lab_id, name, description, price, discounted_price } = req.body;
    if (!lab_id || !name || price == null) {
      return res.status(400).json({ error: 'Lab, name, and price are required' });
    }

    const [result] = await pool.query(
      `INSERT INTO lab_tests (lab_id, name, description, price, discounted_price)
       VALUES (?, ?, ?, ?, ?)`,
      [lab_id, name, description || null, price, discounted_price || null]
    );
    res.status(201).json({ id: result.insertId });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
}

export async function getAllOrders(req, res) {
  try {
    const [orders] = await pool.query(
      `SELECT o.*, u.name AS customer_name, u.email AS customer_email
       FROM orders o JOIN users u ON o.user_id = u.id
       ORDER BY o.created_at DESC`
    );
    for (const order of orders) {
      const [items] = await pool.query(
        `SELECT oi.*, m.name AS medicine_name FROM order_items oi
         JOIN medicines m ON oi.medicine_id = m.id WHERE oi.order_id = ?`,
        [order.id]
      );
      order.items = items;
    }
    res.json(orders);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
}

export async function updateOrderStatus(req, res) {
  try {
    const { status } = req.body;
    const valid = ['pending', 'confirmed', 'shipped', 'delivered', 'cancelled'];
    if (!valid.includes(status)) {
      return res.status(400).json({ error: 'Invalid status' });
    }
    await pool.query('UPDATE orders SET status = ? WHERE id = ?', [status, req.params.id]);
    res.json({ message: 'Order status updated' });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
}

export async function createMedicine(req, res) {
  try {
    const { name, slug, category_id, description, price, discounted_price, requires_prescription, stock } = req.body;
    const [result] = await pool.query(
      `INSERT INTO medicines (name, slug, category_id, description, price, discounted_price, requires_prescription, stock)
       VALUES (?, ?, ?, ?, ?, ?, ?, ?)`,
      [name, slug, category_id, description, price, discounted_price || null, !!requires_prescription, stock || 100]
    );
    res.status(201).json({ id: result.insertId });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
}

export async function updateMedicine(req, res) {
  try {
    const { name, price, discounted_price, stock, is_active, requires_prescription } = req.body;
    await pool.query(
      `UPDATE medicines SET name = COALESCE(?, name), price = COALESCE(?, price),
       discounted_price = ?, stock = COALESCE(?, stock), is_active = COALESCE(?, is_active),
       requires_prescription = COALESCE(?, requires_prescription) WHERE id = ?`,
      [name, price, discounted_price, stock, is_active, requires_prescription, req.params.id]
    );
    res.json({ message: 'Medicine updated' });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
}

export async function deleteMedicine(req, res) {
  try {
    await pool.query('UPDATE medicines SET is_active = FALSE WHERE id = ?', [req.params.id]);
    res.json({ message: 'Medicine deactivated' });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
}
