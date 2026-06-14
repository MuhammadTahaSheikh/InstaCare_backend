import crypto from 'crypto';
import pool from '../config/db.js';
import {
  generateChatReply,
  generateConsultationSummary,
  isAiDoctorConfigured,
  getAiDoctorStatus,
  getBotOpening,
  buildSessionPrefs,
} from '../services/aiDoctorService.js';
import { buildConsultationPdf } from '../services/aiDoctorPdfService.js';
import { notifyAiDoctorComplete } from '../services/n8nService.js';
import { fetchRecommendedDoctors } from '../services/aiDoctorDoctors.js';

function parseJsonField(value, fallback) {
  if (value == null) return fallback;
  if (typeof value === 'object') return value;
  try {
    return JSON.parse(value);
  } catch {
    return fallback;
  }
}

async function getConsultation(id) {
  const [rows] = await pool.query('SELECT * FROM ai_consultations WHERE id = ?', [id]);
  return rows[0] || null;
}

async function getMessages(consultationId) {
  const [rows] = await pool.query(
    'SELECT id, role, content, created_at FROM ai_consultation_messages WHERE consultation_id = ? ORDER BY id ASC',
    [consultationId]
  );
  return rows;
}

function canAccessConsultation(consultation, req) {
  if (!consultation) return false;
  if (consultation.user_id && req.user?.id !== consultation.user_id) return false;
  return true;
}

export async function getStatus(req, res) {
  const status = await getAiDoctorStatus();
  res.json(status);
}

export async function createSession(req, res) {
  try {
    if (!(await isAiDoctorConfigured())) {
      return res.status(503).json({
        error: 'AI Doctor bot is not running. Start the Python bot service on port 5003.',
      });
    }

    const id = crypto.randomUUID();
    const userId = req.user?.id || null;
    const citySlug = req.body.city || 'lahore';
    const doctorGender = req.body.doctor_gender === 'female' ? 'female' : 'male';
    const preferredLanguage = ['en', 'ur', 'hi', 'ar'].includes(req.body.preferred_language)
      ? req.body.preferred_language
      : 'en';
    const romanUrdu = Boolean(req.body.roman_urdu);

    await pool.query(
      `INSERT INTO ai_consultations
       (id, user_id, city_slug, doctor_gender, preferred_language, roman_urdu)
       VALUES (?, ?, ?, ?, ?, ?)`,
      [id, userId, citySlug, doctorGender, preferredLanguage, romanUrdu ? 1 : 0]
    );

    const { message: welcome, language, voice_lang: voiceLang } = await getBotOpening({
      doctorGender,
      preferredLanguage,
      romanUrdu,
    });

    await pool.query(
      'INSERT INTO ai_consultation_messages (consultation_id, role, content) VALUES (?, ?, ?)',
      [id, 'assistant', welcome]
    );

    res.status(201).json({
      id,
      message: welcome,
      language,
      voice_lang: voiceLang,
      doctor_gender: doctorGender,
      preferred_language: preferredLanguage,
      roman_urdu: romanUrdu,
    });
  } catch (err) {
    if (err.code === 'ER_NO_SUCH_TABLE') {
      return res.status(503).json({ error: 'AI Doctor database not set up. Run: npm run db:migrate:ai-doctor' });
    }
    res.status(500).json({ error: err.message });
  }
}

export async function getSession(req, res) {
  try {
    const consultation = await getConsultation(req.params.id);
    if (!canAccessConsultation(consultation, req)) {
      return res.status(404).json({ error: 'Consultation not found' });
    }

    const messages = await getMessages(consultation.id);
    res.json({
      ...consultation,
      summary: parseJsonField(consultation.summary, null),
      recommended_doctors: parseJsonField(consultation.recommended_doctors, null),
      messages,
    });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
}

export async function sendMessage(req, res) {
  try {
    const { message } = req.body;
    if (!message?.trim()) {
      return res.status(400).json({ error: 'Message is required' });
    }

    const consultation = await getConsultation(req.params.id);
    if (!canAccessConsultation(consultation, req)) {
      return res.status(404).json({ error: 'Consultation not found' });
    }
    if (consultation.status !== 'active') {
      return res.status(400).json({ error: 'This consultation has ended' });
    }

    await pool.query(
      'INSERT INTO ai_consultation_messages (consultation_id, role, content) VALUES (?, ?, ?)',
      [consultation.id, 'user', message.trim()]
    );

    const history = await getMessages(consultation.id);
    const sessionPrefs = buildSessionPrefs(consultation);
    const { reply, language, voice_lang: voiceLang, recommended_doctors: recommendedDoctors } =
      await generateChatReply(history, consultation.city_slug || 'lahore', sessionPrefs);

    await pool.query(
      'INSERT INTO ai_consultation_messages (consultation_id, role, content) VALUES (?, ?, ?)',
      [consultation.id, 'assistant', reply]
    );

    res.json({
      reply,
      language,
      voice_lang: voiceLang,
      recommended_doctors: recommendedDoctors || [],
    });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
}

export async function completeSession(req, res) {
  try {
    const consultation = await getConsultation(req.params.id);
    if (!canAccessConsultation(consultation, req)) {
      return res.status(404).json({ error: 'Consultation not found' });
    }
    if (consultation.status === 'completed') {
      const summary = parseJsonField(consultation.summary, {});
      const doctors = parseJsonField(consultation.recommended_doctors, []);
      return res.json({ summary, recommended_doctors: doctors });
    }

    const messages = await getMessages(consultation.id);
    const userMessages = messages.filter((m) => m.role === 'user');
    if (userMessages.length === 0) {
      return res.status(400).json({ error: 'Please describe your symptoms before ending the consultation' });
    }

    const summary = await generateConsultationSummary(messages, buildSessionPrefs(consultation));
    const doctors = await fetchRecommendedDoctors(
      summary.recommended_specialty_slug,
      consultation.city_slug
    );

    await pool.query(
      `UPDATE ai_consultations
       SET status = 'completed', summary = ?, recommended_doctors = ?, completed_at = NOW()
       WHERE id = ?`,
      [JSON.stringify(summary), JSON.stringify(doctors), consultation.id]
    );

    notifyAiDoctorComplete({
      event: 'ai_doctor.completed',
      consultation_id: consultation.id,
      user_id: consultation.user_id,
      city_slug: consultation.city_slug,
      summary,
      recommended_doctors: doctors,
      frontend_url: process.env.FRONTEND_URL,
      pdf_url: `${process.env.BACKEND_URL || ''}/api/ai-doctor/sessions/${consultation.id}/pdf`,
    }).catch(() => {});

    res.json({ summary, recommended_doctors: doctors });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
}

export async function downloadPdf(req, res) {
  try {
    const consultation = await getConsultation(req.params.id);
    if (!canAccessConsultation(consultation, req)) {
      return res.status(404).json({ error: 'Consultation not found' });
    }

    const messages = await getMessages(consultation.id);
    const summary = consultation.summary ? parseJsonField(consultation.summary, null) : null;
    const doctors = consultation.recommended_doctors
      ? parseJsonField(consultation.recommended_doctors, [])
      : [];

    const pdf = await buildConsultationPdf({ consultation, messages, summary, doctors });

    res.setHeader('Content-Type', 'application/pdf');
    res.setHeader(
      'Content-Disposition',
      `attachment; filename="bestechcare-ai-consultation-${consultation.id.slice(0, 8)}.pdf"`
    );
    res.send(pdf);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
}
