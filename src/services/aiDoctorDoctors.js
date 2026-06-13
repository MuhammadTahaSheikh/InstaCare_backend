import pool from '../config/db.js';

export async function fetchRecommendedDoctors(specialtySlug, citySlug) {
  let query = `
    SELECT d.id, d.consultation_fee, d.rating, d.online_consultation, d.in_clinic,
           u.name, s.name AS specialty_name, s.slug AS specialty_slug,
           h.name AS hospital_name, c.name AS city_name, c.slug AS city_slug
    FROM doctors d
    JOIN users u ON d.user_id = u.id
    JOIN specialties s ON d.specialty_id = s.id
    LEFT JOIN hospitals h ON d.hospital_id = h.id
    LEFT JOIN cities c ON h.city_id = c.id
    WHERE d.is_verified = TRUE
  `;
  const params = [];

  if (specialtySlug) {
    query += ' AND s.slug = ?';
    params.push(specialtySlug);
  }
  if (citySlug) {
    query += ' AND c.slug = ?';
    params.push(citySlug);
  }

  query += ' ORDER BY d.rating DESC LIMIT 5';
  const [doctors] = await pool.query(query, params);

  if (doctors.length === 0 && specialtySlug) {
    const [fallback] = await pool.query(
      `SELECT d.id, d.consultation_fee, d.rating, d.online_consultation, d.in_clinic,
              u.name, s.name AS specialty_name, s.slug AS specialty_slug,
              h.name AS hospital_name, c.name AS city_name, c.slug AS city_slug
       FROM doctors d
       JOIN users u ON d.user_id = u.id
       JOIN specialties s ON d.specialty_id = s.id
       LEFT JOIN hospitals h ON d.hospital_id = h.id
       LEFT JOIN cities c ON h.city_id = c.id
       WHERE d.is_verified = TRUE AND s.slug = ?
       ORDER BY d.rating DESC LIMIT 5`,
      [specialtySlug]
    );
    return fallback;
  }

  return doctors;
}

export function sanitizeBotReply(reply) {
  if (!reply) return reply;
  return reply
    .split('\n')
    .filter((line) => !line.trim().toUpperCase().startsWith('LANGUAGE LOCK'))
    .join('\n')
    .trim();
}

export function appendDoctorRecommendations(reply, doctors, { language = 'en', roman = false, specialtySlug } = {}) {
  if (!doctors?.length) return reply;

  const alreadyMentioned = doctors.some((d) => reply.includes(d.name));
  if (alreadyMentioned) return reply;

  const frontend = (process.env.FRONTEND_URL || 'https://bestech-care.vercel.app').replace(/\/$/, '');
  const specialty = doctors[0]?.specialty_name || specialtySlug?.replace(/-/g, ' ');
  const lines = [];

  if (roman) {
    lines.push(`**BestechCare par ${specialty} jo aap ki madad kar sakte hain:**`);
  } else if (language === 'ur') {
    lines.push(`**BestechCare پر ${specialty} جو آپ کی مدد کر سکتے ہیں:**`);
  } else {
    lines.push(`**Doctors on BestechCare who can help with this (${specialty}):**`);
  }

  for (const d of doctors) {
    const location = d.hospital_name ? ` — ${d.hospital_name}` : d.city_name ? ` — ${d.city_name}` : '';
    const modes = [];
    if (d.online_consultation) modes.push(roman ? 'Online' : 'Online');
    if (d.in_clinic) modes.push(roman ? 'Clinic' : 'In-clinic');
    const modeStr = modes.length ? ` (${modes.join(', ')})` : '';
    lines.push(
      `• **${d.name}** — ${d.specialty_name}${location}${modeStr} · ★ ${d.rating} · PKR ${Number(d.consultation_fee).toLocaleString()}`
    );
    lines.push(`  Book: ${frontend}/doctors/${d.id}`);
  }

  lines.push(`View all: ${frontend}/doctors?specialty=${specialtySlug || doctors[0]?.specialty_slug || 'general-physician'}`);

  return `${reply}\n\n${lines.join('\n')}`;
}
