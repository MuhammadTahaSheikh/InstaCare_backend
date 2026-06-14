import {
  fetchRecommendedDoctors,
  sanitizeBotReply,
  stripInventedDoctorNames,
  appendDoctorRecommendations,
} from './aiDoctorDoctors.js';

const TIMEOUT_MS = 30000;
const BOT_URL = (process.env.AI_DOCTOR_BOT_URL || 'http://127.0.0.1:5003').replace(/\/$/, '');

let botHealthCache = { checkedAt: 0, available: false, engine: null };

async function callPythonBot(path, body) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), TIMEOUT_MS);

  try {
    const res = await fetch(`${BOT_URL}${path}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
      signal: controller.signal,
    });

    if (!res.ok) {
      const text = await res.text().catch(() => '');
      throw new Error(`AI Doctor bot error (${res.status}): ${text.slice(0, 200)}`);
    }

    return res.json();
  } finally {
    clearTimeout(timer);
  }
}

export async function checkBotHealth(force = false) {
  const now = Date.now();
  if (!force && now - botHealthCache.checkedAt < 30000) {
    return botHealthCache;
  }

  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 3000);

  try {
    const res = await fetch(`${BOT_URL}/health`, { signal: controller.signal });
    if (!res.ok) {
      botHealthCache = { checkedAt: now, available: false, engine: null };
      return botHealthCache;
    }
    const data = await res.json();
    botHealthCache = {
      checkedAt: now,
      available: data.status === 'ok',
      engine: data.engine || 'python-rules',
    };
    return botHealthCache;
  } catch {
    botHealthCache = { checkedAt: now, available: false, engine: null };
    return botHealthCache;
  } finally {
    clearTimeout(timer);
  }
}

function getOpenAiConfig() {
  const apiKey = process.env.OPENAI_API_KEY;
  if (!apiKey) return null;

  return {
    apiKey,
    model: process.env.OPENAI_MODEL || 'gpt-4o-mini',
    baseUrl: (process.env.OPENAI_BASE_URL || 'https://api.openai.com/v1').replace(/\/$/, ''),
  };
}

async function callOpenAi(messages, { temperature = 0.6, maxTokens = 1200 } = {}) {
  const config = getOpenAiConfig();
  if (!config) {
    throw new Error('OpenAI is not configured.');
  }

  const res = await fetch(`${config.baseUrl}/chat/completions`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${config.apiKey}`,
    },
    body: JSON.stringify({
      model: config.model,
      messages,
      temperature,
      max_tokens: maxTokens,
    }),
  });

  if (!res.ok) {
    const body = await res.text().catch(() => '');
    throw new Error(`OpenAI request failed (${res.status}): ${body.slice(0, 200)}`);
  }

  const data = await res.json();
  return data.choices?.[0]?.message?.content?.trim() || '';
}

const OPENAI_SYSTEM_PROMPT = `You are BestechCare AI Doctor — a helpful health guidance assistant for users in Pakistan.
You are NOT a licensed doctor. Always include disclaimers. Flag emergencies. Be concise.`;

const OPENAI_SUMMARY_PROMPT = `Produce a final consultation report as valid JSON only with keys:
summary, symptoms_discussed, possible_conditions, medicines, suggested_tests, precautions, self_care,
urgent_care_required, urgent_care_reason, recommended_specialty_slug, disclaimer`;

function buildSessionPrefs(consultation) {
  if (!consultation) return null;
  return {
    doctor_gender: consultation.doctor_gender || 'male',
    preferred_language: consultation.preferred_language || 'en',
    roman_urdu: Boolean(consultation.roman_urdu),
  };
}

export async function getBotOpening({ doctorGender = 'male', preferredLanguage = 'en', romanUrdu = false } = {}) {
  const health = await checkBotHealth();
  if (!health.available) {
    throw new Error('AI Doctor bot is not running.');
  }
  const data = await callPythonBot('/chat', {
    messages: [],
    session_prefs: {
      doctor_gender: doctorGender,
      preferred_language: preferredLanguage,
      roman_urdu: Boolean(romanUrdu),
    },
  });
  return {
    message: data.reply,
    language: data.language || preferredLanguage || 'en',
    voice_lang: data.voice_lang || 'en-US',
  };
}

export async function generateChatReply(conversationMessages, citySlug = 'lahore', sessionPrefs = null) {
  const payload = conversationMessages.map((m) => ({ role: m.role, content: m.content }));

  const health = await checkBotHealth();
  if (health.available) {
    const data = await callPythonBot('/chat', {
      messages: payload,
      ...(sessionPrefs ? { session_prefs: sessionPrefs } : {}),
    });
    let reply = sanitizeBotReply(data.reply);
    if (data.suggest_doctors) {
      reply = stripInventedDoctorNames(reply);
    }
    let recommendedDoctors = [];
    const roman = (data.voice_lang || '').startsWith('hi') || data.language === 'ur' && /[a-z]{3,}/i.test(reply) && /\b(hai|hain|aap|mujhe)\b/i.test(reply);

    if (data.suggest_doctors) {
      const specialtySlug = data.recommended_specialty_slug || 'general-physician';
      recommendedDoctors = await fetchRecommendedDoctors(specialtySlug, citySlug);
      reply = appendDoctorRecommendations(reply, recommendedDoctors, {
        language: data.language || 'en',
        roman: Boolean(roman),
        specialtySlug,
        citySlug,
      });
    }

    return {
      reply,
      language: data.language || 'en',
      voice_lang: data.voice_lang || 'en-US',
      recommended_doctors: recommendedDoctors,
      recommended_specialty_slug: data.recommended_specialty_slug || null,
    };
  }

  if (getOpenAiConfig()) {
    const messages = [
      { role: 'system', content: OPENAI_SYSTEM_PROMPT },
      ...payload,
    ];
    const reply = await callOpenAi(messages);
    return { reply, language: 'en', voice_lang: 'en-US' };
  }

  throw new Error(
    'AI Doctor bot is not running. Start it with: cd ai-doctor-bot && pip install -r requirements.txt && python app.py'
  );
}

export async function generateConsultationSummary(conversationMessages, sessionPrefs = null) {
  const payload = conversationMessages.map((m) => ({ role: m.role, content: m.content }));

  const health = await checkBotHealth();
  if (health.available) {
    const data = await callPythonBot('/summary', {
      messages: payload,
      ...(sessionPrefs ? { session_prefs: sessionPrefs } : {}),
    });
    const { engine, ...summary } = data;
    return summary;
  }

  if (getOpenAiConfig()) {
    const raw = await callOpenAi(
      [
        { role: 'system', content: OPENAI_SUMMARY_PROMPT },
        {
          role: 'user',
          content: payload
            .map((m) => `${m.role === 'user' ? 'Patient' : 'AI Doctor'}: ${m.content}`)
            .join('\n\n'),
        },
      ],
      { temperature: 0.3, maxTokens: 2000 }
    );

    try {
      const cleaned = raw.replace(/^```json\s*/i, '').replace(/\s*```$/, '');
      return JSON.parse(cleaned);
    } catch {
      return {
        summary: raw,
        symptoms_discussed: [],
        possible_conditions: [],
        medicines: [],
        suggested_tests: [],
        precautions: [],
        self_care: [],
        urgent_care_required: false,
        urgent_care_reason: null,
        recommended_specialty_slug: 'general-physician',
        disclaimer: 'Always consult a qualified doctor for professional evaluation.',
      };
    }
  }

  throw new Error('AI Doctor bot is not running.');
}

export async function isAiDoctorConfigured() {
  const health = await checkBotHealth(true);
  if (health.available) return true;
  return Boolean(getOpenAiConfig());
}

export { buildSessionPrefs };

export async function getAiDoctorStatus() {
  const health = await checkBotHealth(true);
  const openai = Boolean(getOpenAiConfig());

  return {
    configured: health.available || openai,
    engine: health.available ? health.engine : openai ? 'openai' : null,
    bot_url: BOT_URL,
    openai_fallback: openai,
  };
}
