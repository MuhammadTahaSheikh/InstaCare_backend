import pool from '../config/db.js';

const DOCTOR_SELECT = `
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

async function queryDoctors(specialtySlug, citySlug, limit = 5) {
  let query = DOCTOR_SELECT;
  const params = [];

  if (specialtySlug) {
    query += ' AND s.slug = ?';
    params.push(specialtySlug);
  }
  if (citySlug) {
    query += ' AND c.slug = ?';
    params.push(citySlug);
  }

  query += ' ORDER BY d.rating DESC LIMIT ?';
  params.push(limit);
  const [doctors] = await pool.query(query, params);
  return doctors;
}

export async function fetchRecommendedDoctors(specialtySlug, citySlug) {
  const slug = specialtySlug || 'general-physician';
  const city = citySlug || null;

  const attempts = [
    [slug, city],
    [slug, null],
    ['general-physician', city],
    [null, city],
    ['general-physician', null],
    [null, null],
  ];

  for (const [spec, c] of attempts) {
    if (!spec && !c) continue;
    const doctors = await queryDoctors(spec, c);
    if (doctors.length) return doctors;
  }

  return queryDoctors(null, null);
}

export function sanitizeBotReply(reply) {
  if (!reply) return reply;
  return reply
    .split('\n')
    .filter((line) => !line.trim().toUpperCase().startsWith('LANGUAGE LOCK'))
    .join('\n')
    .trim();
}

export function stripInventedDoctorNames(reply) {
  if (!reply) return reply;

  return reply
    .split('\n')
    .filter((line) => {
      const trimmed = line.trim();
      if (/^\d+\.\s*Dr\.\s/i.test(trimmed)) return false;
      if (/^[-•*]\s*Dr\.\s/i.test(trimmed)) return false;
      if (/^Dr\.\s[A-Z][a-z]+\s+[A-Z][a-z]+\s*\(/i.test(trimmed)) return false;
      return true;
    })
    .join('\n')
    .replace(/\n*(?:Here are a few names:?|(?:\*\*)?Matching Specialists[^\n]*:?\*\*?)\s*\n*/gi, '\n\n')
    .replace(/\n{3,}/g, '\n\n')
    .trim();
}

export function appendDoctorRecommendations(
  reply,
  doctors,
  { language = 'en', roman = false, specialtySlug, citySlug } = {}
) {
  if (!doctors?.length) return reply;

  const frontend = (process.env.FRONTEND_URL || 'https://bestech-care.vercel.app').replace(/\/$/, '');
  const requested = specialtySlug?.replace(/-/g, ' ');
  const cityLabel = citySlug ? citySlug.replace(/-/g, ' ') : null;
  const lines = [];
  const exactMatch = doctors.some((d) => d.specialty_slug === specialtySlug);

  if (roman) {
    if (exactMatch) {
      lines.push(`**BestechCare par ${requested} jo aap ki madad kar sakte hain${cityLabel ? ` (${cityLabel})` : ''}:**`);
    } else {
      lines.push(`**BestechCare par verified doctors${cityLabel ? ` ${cityLabel} mein` : ''} jo pehle consult kar sakte hain:**`);
    }
  } else if (language === 'ur') {
    if (exactMatch) {
      lines.push(`**BestechCare پر ${requested} جو آپ کی مدد کر سکتے ہیں${cityLabel ? ` (${cityLabel})` : ''}:**`);
    } else {
      lines.push(`**BestechCare پر verified doctors${cityLabel ? ` ${cityLabel} میں` : ''} جو ابھی مدد کر سکتے ہیں:**`);
    }
  } else if (exactMatch) {
    lines.push(`**Doctors on BestechCare who can help with this (${requested}${cityLabel ? `, ${cityLabel}` : ''}):**`);
  } else if (requested && cityLabel) {
    lines.push(
      `**No ${requested} specialists listed in ${cityLabel} yet — here are verified BestechCare doctors in ${cityLabel} you can book now:**`
    );
  } else {
    lines.push(`**Verified doctors on BestechCare you can book now:**`);
  }

  for (const d of doctors) {
    const location = d.hospital_name ? ` — ${d.hospital_name}` : d.city_name ? ` — ${d.city_name}` : '';
    const modes = [];
    if (d.online_consultation) modes.push('Online');
    if (d.in_clinic) modes.push('In-clinic');
    const modeStr = modes.length ? ` (${modes.join(', ')})` : '';
    lines.push(
      `• **${d.name}** — ${d.specialty_name}${location}${modeStr} · ★ ${d.rating} · PKR ${Number(d.consultation_fee).toLocaleString()}`
    );
    lines.push(`  Book: ${frontend}/doctors/${d.id}`);
  }

  const viewSlug = exactMatch ? specialtySlug : doctors[0]?.specialty_slug || 'general-physician';
  lines.push(`View all: ${frontend}/doctors?specialty=${viewSlug}${cityLabel ? `&city=${citySlug}` : ''}`);

  const cleaned = stripInventedDoctorNames(reply);
  const alreadyMentioned = doctors.every((d) => cleaned.includes(d.name));
  if (alreadyMentioned) return cleaned;

  return `${cleaned}\n\n${lines.join('\n')}`;
}
