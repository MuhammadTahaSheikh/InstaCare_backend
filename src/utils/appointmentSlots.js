const SLOT_START_HOUR = 9;
const SLOT_END_HOUR = 17;
const SLOT_INTERVAL_MIN = 30;

export function generateTimeSlots() {
  const slots = [];
  for (let hour = SLOT_START_HOUR; hour < SLOT_END_HOUR; hour++) {
    for (const minute of [0, 30]) {
      slots.push(
        `${String(hour).padStart(2, '0')}:${String(minute).padStart(2, '0')}`
      );
    }
  }
  return slots;
}

export function normalizeSlotTime(time) {
  if (!time) return '';
  const value = String(time);
  const part = value.includes('T') ? value.split('T')[1] : value;
  return part.slice(0, 5);
}

export function isValidSlotTime(time) {
  return generateTimeSlots().includes(normalizeSlotTime(time));
}

function isPastSlot(dateStr, timeStr) {
  const [year, month, day] = dateStr.split('-').map(Number);
  const [hour, minute] = normalizeSlotTime(timeStr).split(':').map(Number);
  const slotAt = new Date(year, month - 1, day, hour, minute, 0, 0);
  return slotAt.getTime() <= Date.now();
}

export async function getBookedSlots(pool, doctorId, date) {
  const [rows] = await pool.query(
    `SELECT TIME_FORMAT(appointment_time, '%H:%i') AS slot_time
     FROM appointments
     WHERE doctor_id = ?
       AND appointment_date = ?
       AND status IN ('pending', 'confirmed')`,
    [doctorId, date]
  );
  return rows.map((row) => row.slot_time);
}

export async function getAvailableSlots(pool, doctorId, date) {
  const allSlots = generateTimeSlots();
  const booked = await getBookedSlots(pool, doctorId, date);

  const available = allSlots.filter((slot) => {
    if (booked.includes(slot)) return false;
    if (isPastSlot(date, slot)) return false;
    return true;
  });

  return { date, slots: available, booked };
}

export async function isSlotAvailable(pool, doctorId, date, time) {
  const normalized = normalizeSlotTime(time);
  if (!isValidSlotTime(normalized)) return false;
  if (isPastSlot(date, normalized)) return false;

  const booked = await getBookedSlots(pool, doctorId, date);
  return !booked.includes(normalized);
}
