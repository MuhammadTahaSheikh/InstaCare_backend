import pool from '../config/db.js';

const UPCOMING_FILTER = `
  (a.appointment_date > CURDATE()
   OR (a.appointment_date = CURDATE() AND a.appointment_time >= CURTIME()))
  AND a.status IN ('pending', 'confirmed')
`;

async function getAppointmentStats(whereClause, params) {
  const [[stats]] = await pool.query(
    `SELECT
       COUNT(*) AS total,
       SUM(CASE WHEN ${UPCOMING_FILTER} THEN 1 ELSE 0 END) AS upcoming,
       SUM(CASE WHEN a.status = 'completed' THEN 1 ELSE 0 END) AS completed,
       SUM(CASE WHEN a.status = 'cancelled' THEN 1 ELSE 0 END) AS cancelled
     FROM appointments a
     WHERE ${whereClause}`,
    params
  );
  return {
    total_appointments: Number(stats.total) || 0,
    upcoming: Number(stats.upcoming) || 0,
    completed: Number(stats.completed) || 0,
    cancelled: Number(stats.cancelled) || 0,
  };
}

async function getDoctorUpcoming(doctorId) {
  const [rows] = await pool.query(
    `SELECT a.id, a.appointment_date, a.appointment_time, a.type, a.status,
            a.payment_status, u.name AS patient_name, u.id AS patient_id
     FROM appointments a
     JOIN users u ON a.patient_id = u.id
     WHERE a.doctor_id = ? AND ${UPCOMING_FILTER}
     ORDER BY a.appointment_date ASC, a.appointment_time ASC`,
    [doctorId]
  );
  return rows;
}

async function getDoctorPatients(doctorId) {
  const [rows] = await pool.query(
    `SELECT u.id AS patient_id, u.name AS patient_name, u.email AS patient_email,
            COUNT(a.id) AS total_appointments,
            MAX(a.appointment_date) AS last_visit_date,
            MAX(a.appointment_time) AS last_visit_time
     FROM appointments a
     JOIN users u ON a.patient_id = u.id
     WHERE a.doctor_id = ? AND a.status != 'cancelled'
     GROUP BY u.id, u.name, u.email
     ORDER BY last_visit_date DESC, last_visit_time DESC`,
    [doctorId]
  );
  return rows;
}

async function getPatientUpcoming(patientId) {
  const [rows] = await pool.query(
    `SELECT a.id, a.appointment_date, a.appointment_time, a.type, a.status,
            a.payment_status, du.name AS doctor_name, d.id AS doctor_id, s.name AS specialty_name
     FROM appointments a
     JOIN doctors d ON a.doctor_id = d.id
     JOIN users du ON d.user_id = du.id
     JOIN specialties s ON d.specialty_id = s.id
     WHERE a.patient_id = ? AND ${UPCOMING_FILTER}
     ORDER BY a.appointment_date ASC, a.appointment_time ASC`,
    [patientId]
  );
  return rows;
}

async function getPatientDoctors(patientId) {
  const [rows] = await pool.query(
    `SELECT d.id AS doctor_id, du.name AS doctor_name, s.name AS specialty_name,
            COUNT(a.id) AS total_appointments,
            MAX(a.appointment_date) AS last_visit_date,
            MAX(a.appointment_time) AS last_visit_time
     FROM appointments a
     JOIN doctors d ON a.doctor_id = d.id
     JOIN users du ON d.user_id = du.id
     JOIN specialties s ON d.specialty_id = s.id
     WHERE a.patient_id = ? AND a.status != 'cancelled'
     GROUP BY d.id, du.name, s.name
     ORDER BY last_visit_date DESC, last_visit_time DESC`,
    [patientId]
  );
  return rows;
}

async function buildDoctorSummary(doctorId, doctorName, specialtyName) {
  const [stats, upcoming_appointments, patients] = await Promise.all([
    getAppointmentStats('a.doctor_id = ?', [doctorId]),
    getDoctorUpcoming(doctorId),
    getDoctorPatients(doctorId),
  ]);

  return {
    doctor_id: doctorId,
    doctor_name: doctorName,
    specialty_name: specialtyName,
    stats: { ...stats, patients_count: patients.length },
    upcoming_appointments,
    patients,
  };
}

async function buildPatientSummary(patientId, patientName, patientEmail) {
  const [stats, upcoming_appointments, doctors] = await Promise.all([
    getAppointmentStats('a.patient_id = ?', [patientId]),
    getPatientUpcoming(patientId),
    getPatientDoctors(patientId),
  ]);

  return {
    patient_id: patientId,
    patient_name: patientName,
    patient_email: patientEmail,
    stats: { ...stats, doctors_count: doctors.length },
    upcoming_appointments,
    doctors,
  };
}

export async function getMySummary(req, res) {
  try {
    const { role, id: userId } = req.user;

    if (role === 'doctor') {
      const [doctor] = await pool.query(
        `SELECT d.id, u.name, s.name AS specialty_name
         FROM doctors d
         JOIN users u ON d.user_id = u.id
         JOIN specialties s ON d.specialty_id = s.id
         WHERE d.user_id = ?`,
        [userId]
      );

      if (doctor.length === 0) {
        return res.status(404).json({ error: 'Doctor profile not found' });
      }

      const summary = await buildDoctorSummary(
        doctor[0].id,
        doctor[0].name,
        doctor[0].specialty_name
      );

      return res.json({ role: 'doctor', ...summary });
    }

    if (role === 'patient') {
      const [user] = await pool.query(
        'SELECT id, name, email FROM users WHERE id = ?',
        [userId]
      );

      const summary = await buildPatientSummary(
        user[0].id,
        user[0].name,
        user[0].email
      );

      return res.json({ role: 'patient', ...summary });
    }

    if (role === 'admin') {
      const [doctors] = await pool.query(
        `SELECT d.id, u.name, s.name AS specialty_name
         FROM doctors d
         JOIN users u ON d.user_id = u.id
         JOIN specialties s ON d.specialty_id = s.id
         ORDER BY u.name ASC`
      );

      const [patients] = await pool.query(
        `SELECT id, name, email FROM users WHERE role = 'patient' ORDER BY name ASC`
      );

      const doctorSummaries = await Promise.all(
        doctors.map((d) => buildDoctorSummary(d.id, d.name, d.specialty_name))
      );
      const patientSummaries = await Promise.all(
        patients.map((p) => buildPatientSummary(p.id, p.name, p.email))
      );

      return res.json({
        role: 'admin',
        doctors: doctorSummaries,
        patients: patientSummaries,
      });
    }

    res.status(400).json({ error: 'Unsupported role' });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
}

export async function getAllSummaries(req, res) {
  try {
    const [doctors] = await pool.query(
      `SELECT d.id, u.name, s.name AS specialty_name
       FROM doctors d
       JOIN users u ON d.user_id = u.id
       JOIN specialties s ON d.specialty_id = s.id
       ORDER BY u.name ASC`
    );

    const [patients] = await pool.query(
      `SELECT id, name, email FROM users WHERE role = 'patient' ORDER BY name ASC`
    );

    const doctorSummaries = await Promise.all(
      doctors.map((d) => buildDoctorSummary(d.id, d.name, d.specialty_name))
    );
    const patientSummaries = await Promise.all(
      patients.map((p) => buildPatientSummary(p.id, p.name, p.email))
    );

    res.json({
      doctors: doctorSummaries,
      patients: patientSummaries,
    });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
}
