import pool from '../config/db.js';
import {
  sendAppointmentConfirmationEmail,
  sendDoctorAppointmentNotificationEmail,
} from './emailService.js';
import { notifyN8n } from './n8nService.js';
import { formatAppointmentDisplay, getReminderAt, normalizeAppointmentDate, normalizeAppointmentTime } from '../utils/appointmentTime.js';

async function fetchAppointmentDetails(appointmentId) {
  const [rows] = await pool.query(
    `SELECT a.*,
            pu.email AS patient_email,
            pu.name AS patient_name,
            du.name AS doctor_name,
            du.email AS doctor_email,
            s.name AS specialty_name
     FROM appointments a
     JOIN users pu ON a.patient_id = pu.id
     JOIN doctors d ON a.doctor_id = d.id
     JOIN users du ON d.user_id = du.id
     JOIN specialties s ON d.specialty_id = s.id
     WHERE a.id = ?`,
    [appointmentId]
  );

  return rows[0] || null;
}

function buildStatusCheckUrl(appointmentId) {
  const base = process.env.BACKEND_URL || `http://localhost:${process.env.PORT || 5001}`;
  return `${base.replace(/\/$/, '')}/api/appointments/${appointmentId}/reminder-status`;
}

function buildPayload(appointment, event) {
  const typeLabel = appointment.type === 'online' ? 'Online consultation' : 'In-clinic visit';
  const appointmentDate = normalizeAppointmentDate(appointment.appointment_date);
  const appointmentTime = normalizeAppointmentTime(appointment.appointment_time);

  return {
    event,
    appointment_id: appointment.id,
    patient_email: appointment.patient_email,
    patient_name: appointment.patient_name,
    doctor_email: appointment.doctor_email,
    doctor_name: appointment.doctor_name,
    specialty_name: appointment.specialty_name,
    appointment_date: appointmentDate,
    appointment_time: appointmentTime,
    appointment_display: formatAppointmentDisplay(appointmentDate, appointmentTime),
    type: appointment.type,
    type_label: typeLabel,
    status: appointment.status,
    payment_status: appointment.payment_status,
    room_id: appointment.room_id || null,
    reminder_at: getReminderAt(appointmentDate, appointmentTime).toISOString(),
    status_check_url: buildStatusCheckUrl(appointment.id),
    frontend_url: process.env.FRONTEND_URL || '',
  };
}

async function fallbackConfirmationEmails(appointment, payload) {
  try {
    await sendAppointmentConfirmationEmail({
      to: appointment.patient_email,
      name: appointment.patient_name,
      doctorName: appointment.doctor_name,
      specialtyName: appointment.specialty_name,
      appointmentDisplay: payload.appointment_display,
      typeLabel: payload.type_label,
      roomId: appointment.room_id,
      frontendUrl: payload.frontend_url,
    });
    await sendDoctorConfirmationEmail(appointment, payload);
    console.log('[appointment] confirmation emails sent via SMTP fallback (patient + doctor)');
  } catch (err) {
    console.error('[appointment] SMTP fallback failed:', err.message);
  }
}

async function sendDoctorConfirmationEmail(appointment, payload) {
  if (!appointment.doctor_email) {
    console.warn('[appointment] doctor email missing — skip doctor notification');
    return;
  }

  await sendDoctorAppointmentNotificationEmail({
    to: appointment.doctor_email,
    doctorName: appointment.doctor_name,
    patientName: appointment.patient_name,
    specialtyName: appointment.specialty_name,
    appointmentDisplay: payload.appointment_display,
    typeLabel: payload.type_label,
    frontendUrl: payload.frontend_url,
  });
  console.log('[appointment] doctor confirmation email sent to', appointment.doctor_email);
}

export async function notifyAppointmentConfirmed(appointmentId) {
  const appointment = await fetchAppointmentDetails(appointmentId);
  if (!appointment) {
    console.warn('[appointment] confirmation notify — not found:', appointmentId);
    return;
  }

  if (appointment.status !== 'confirmed' || appointment.payment_status !== 'paid') {
    return;
  }

  const payload = buildPayload(appointment, 'appointment.confirmed');
  const result = await notifyN8n(payload);

  if (result?.skipped || result?.ok === false) {
    console.warn('[appointment] n8n webhook unavailable — using SMTP fallback');
    await fallbackConfirmationEmails(appointment, payload);
    return;
  }

  // n8n handles patient confirmation + reminder; doctor email always sent from backend
  try {
    await sendDoctorConfirmationEmail(appointment, payload);
  } catch (err) {
    console.error('[appointment] doctor confirmation email failed:', err.message);
  }
}

export async function notifyAppointmentCancelled(appointmentId) {
  const appointment = await fetchAppointmentDetails(appointmentId);
  if (!appointment) return;

  await notifyN8n(buildPayload(appointment, 'appointment.cancelled'));
}

export async function getReminderStatus(appointmentId) {
  const appointment = await fetchAppointmentDetails(appointmentId);
  if (!appointment) return null;

  const shouldSendReminder =
    appointment.status === 'confirmed' && appointment.payment_status === 'paid';

  return {
    id: appointment.id,
    status: appointment.status,
    payment_status: appointment.payment_status,
    should_send_reminder: shouldSendReminder,
    patient_email: appointment.patient_email,
    patient_name: appointment.patient_name,
    doctor_name: appointment.doctor_name,
    specialty_name: appointment.specialty_name,
    appointment_date: normalizeAppointmentDate(appointment.appointment_date),
    appointment_time: normalizeAppointmentTime(appointment.appointment_time),
    appointment_display: formatAppointmentDisplay(
      appointment.appointment_date,
      appointment.appointment_time
    ),
    type: appointment.type,
    type_label: appointment.type === 'online' ? 'Online consultation' : 'In-clinic visit',
  };
}
