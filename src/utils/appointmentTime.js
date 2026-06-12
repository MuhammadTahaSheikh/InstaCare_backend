const PKT_OFFSET = '+05:00';

function normalizeTime(timeStr) {
  if (!timeStr) return '00:00:00';
  const value = String(timeStr);
  if (value.length === 5) return `${value}:00`;
  return value;
}

/** Appointment instant in PKT (Asia/Karachi). */
export function getAppointmentDateTime(dateStr, timeStr) {
  return new Date(`${dateStr}T${normalizeTime(timeStr)}${PKT_OFFSET}`);
}

/** ISO timestamp for n8n Wait Until — one hour before appointment (PKT). */
export function getReminderAt(dateStr, timeStr) {
  const appointmentAt = getAppointmentDateTime(dateStr, timeStr);
  return new Date(appointmentAt.getTime() - 60 * 60 * 1000);
}

export function formatAppointmentDisplay(dateStr, timeStr) {
  const dt = getAppointmentDateTime(dateStr, timeStr);
  return dt.toLocaleString('en-PK', {
    timeZone: 'Asia/Karachi',
    weekday: 'long',
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
    hour12: true,
  });
}
