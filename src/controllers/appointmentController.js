import pool from '../config/db.js';
import {
  getReminderStatus,
  notifyAppointmentCancelled,
} from '../services/appointmentNotificationService.js';

export async function createAppointment(req, res) {
  try {
    const { doctor_id, appointment_date, appointment_time, type = 'in_clinic', notes } = req.body;

    if (!doctor_id || !appointment_date || !appointment_time) {
      return res.status(400).json({ error: 'Doctor, date, and time are required' });
    }

    const [result] = await pool.query(
      `INSERT INTO appointments (patient_id, doctor_id, appointment_date, appointment_time, type, notes)
       VALUES (?, ?, ?, ?, ?, ?)`,
      [req.user.id, doctor_id, appointment_date, appointment_time, type, notes || null]
    );

    const [doctor] = await pool.query(
      'SELECT consultation_fee FROM doctors WHERE id = ?',
      [doctor_id]
    );

    res.status(201).json({
      message: 'Appointment booked. Please complete payment.',
      id: result.insertId,
      payment_required: true,
      amount: doctor[0]?.consultation_fee || 0,
    });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
}

export async function getMyAppointments(req, res) {
  try {
    const [appointments] = await pool.query(
      `SELECT a.*, u.name AS doctor_name, s.name AS specialty_name, d.consultation_fee
       FROM appointments a
       JOIN doctors d ON a.doctor_id = d.id
       JOIN users u ON d.user_id = u.id
       JOIN specialties s ON d.specialty_id = s.id
       WHERE a.patient_id = ?
       ORDER BY a.appointment_date DESC, a.appointment_time DESC`,
      [req.user.id]
    );
    res.json(appointments);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
}

export async function cancelAppointment(req, res) {
  try {
    const [result] = await pool.query(
      `UPDATE appointments SET status = 'cancelled'
       WHERE id = ? AND patient_id = ?`,
      [req.params.id, req.user.id]
    );

    if (result.affectedRows === 0) {
      return res.status(404).json({ error: 'Appointment not found' });
    }

    notifyAppointmentCancelled(req.params.id).catch((err) => {
      console.error('[appointment] cancel notify failed:', err.message);
    });

    res.json({ message: 'Appointment cancelled' });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
}

/** Called by n8n before sending the 1-hour reminder email. */
export async function getAppointmentReminderStatus(req, res) {
  try {
    const status = await getReminderStatus(req.params.id);
    if (!status) {
      return res.status(404).json({ error: 'Appointment not found' });
    }
    res.json(status);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
}
