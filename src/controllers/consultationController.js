import pool from '../config/db.js';

export async function getConsultationRoom(req, res) {
  try {
    const appointmentId = req.params.id;
    const userId = req.user.id;

    const [appointments] = await pool.query(
      `SELECT a.*, d.user_id AS doctor_user_id, d.id AS doc_id,
              pu.name AS patient_name, du.name AS doctor_name
       FROM appointments a
       JOIN doctors d ON a.doctor_id = d.id
       JOIN users pu ON a.patient_id = pu.id
       JOIN users du ON d.user_id = du.id
       WHERE a.id = ?`,
      [appointmentId]
    );

    if (appointments.length === 0) {
      return res.status(404).json({ error: 'Appointment not found' });
    }

    const appt = appointments[0];

    const isPatient = appt.patient_id === userId;
    const isDoctor = appt.doctor_user_id === userId;
    const isAdmin = req.user.role === 'admin';

    if (!isPatient && !isDoctor && !isAdmin) {
      return res.status(403).json({ error: 'Not authorized for this consultation' });
    }

    if (appt.type !== 'online') {
      return res.status(400).json({ error: 'This is not an online consultation' });
    }

    if (appt.payment_status !== 'paid') {
      return res.status(400).json({ error: 'Payment required before joining consultation' });
    }

    if (!['confirmed', 'completed'].includes(appt.status)) {
      return res.status(400).json({ error: 'Consultation is not active yet' });
    }

    res.json({
      room_id: appt.room_id,
      appointment_id: appt.id,
      patient_name: appt.patient_name,
      doctor_name: appt.doctor_name,
      role: isDoctor ? 'doctor' : 'patient',
      appointment_date: appt.appointment_date,
      appointment_time: appt.appointment_time,
    });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
}

export async function getDoctorConsultations(req, res) {
  try {
    const [doctor] = await pool.query('SELECT id FROM doctors WHERE user_id = ?', [req.user.id]);
    if (doctor.length === 0) {
      return res.status(404).json({ error: 'Doctor profile not found' });
    }

    const [appointments] = await pool.query(
      `SELECT a.*, u.name AS patient_name, s.name AS specialty_name
       FROM appointments a
       JOIN users u ON a.patient_id = u.id
       JOIN doctors d ON a.doctor_id = d.id
       JOIN specialties s ON d.specialty_id = s.id
       WHERE a.doctor_id = ? AND a.type = 'online'
       ORDER BY a.appointment_date DESC, a.appointment_time DESC`,
      [doctor[0].id]
    );
    res.json(appointments);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
}
