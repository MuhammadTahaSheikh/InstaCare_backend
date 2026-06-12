const PKT_OFFSET = '+05:00';

/** MySQL DATE/TIME may arrive as Date objects or ISO strings — normalize to YYYY-MM-DD. */
export function normalizeAppointmentDate(dateInput) {
  if (!dateInput) return '';
  if (dateInput instanceof Date) {
    return dateInput.toISOString().slice(0, 10);
  }
  const value = String(dateInput);
  if (value.includes('T')) return value.slice(0, 10);
  return value.slice(0, 10);
}

/** MySQL TIME may arrive as HH:MM:SS or HH:MM:SS.000000. */
export function normalizeAppointmentTime(timeInput) {
  if (!timeInput) return '00:00:00';
  if (timeInput instanceof Date) {
    const h = timeInput.getUTCHours();
    const m = timeInput.getUTCMinutes();
    const s = timeInput.getUTCSeconds();
    return `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
  }
  const value = String(timeInput);
  const timePart = value.includes('T') ? value.split('T')[1] : value;
  const clean = timePart.split('.')[0];
  if (clean.length === 5) return `${clean}:00`;
  return clean.slice(0, 8);
}

/** Appointment instant in PKT (Asia/Karachi). */
export function getAppointmentDateTime(dateInput, timeInput) {
  const dateStr = normalizeAppointmentDate(dateInput);
  const timeStr = normalizeAppointmentTime(timeInput);
  const dt = new Date(`${dateStr}T${timeStr}${PKT_OFFSET}`);
  if (Number.isNaN(dt.getTime())) {
    throw new Error(`Invalid appointment datetime: ${dateStr} ${timeStr}`);
  }
  return dt;
}

/** ISO timestamp for n8n Wait Until — one hour before appointment (PKT). */
export function getReminderAt(dateInput, timeInput) {
  const appointmentAt = getAppointmentDateTime(dateInput, timeInput);
  return new Date(appointmentAt.getTime() - 60 * 60 * 1000);
}

export function formatAppointmentDisplay(dateInput, timeInput) {
  const dt = getAppointmentDateTime(dateInput, timeInput);
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
