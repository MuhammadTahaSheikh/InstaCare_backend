const SPECIALTY_SLUGS = [
  'gynecologist',
  'dentist',
  'dermatologist',
  'cardiologist',
  'neurologist',
  'ent-specialist',
  'pediatrician',
  'gastroenterologist',
  'general-physician',
  'plastic-surgeon',
  'urologist',
  'psychiatrist',
];

const SYSTEM_PROMPT = `You are BestechCare AI Doctor — a helpful health guidance assistant for users in Pakistan.

IMPORTANT RULES:
- You are NOT a licensed doctor. Always remind users this is informational guidance only.
- Ask relevant follow-up questions about symptoms, duration, severity, age, and medical history before giving detailed advice.
- Never diagnose definitively — suggest possible conditions with clear disclaimers.
- Recommend over-the-counter medicines available in Pakistan when appropriate; mention generic names and typical dosages with "consult a pharmacist/doctor" disclaimers.
- Provide precautions, self-care, and lifestyle recommendations.
- Suggest diagnostic tests or lab work when they seem necessary.
- Clearly flag emergencies (chest pain, difficulty breathing, severe bleeding, stroke signs, etc.) and urge immediate ER/911-style care.
- Be empathetic, concise, and use plain language.
- Do not prescribe controlled substances or antibiotics without emphasizing a real doctor visit is required.

During the conversation, gather enough information through questions. Keep responses focused and readable.`;

const SUMMARY_PROMPT = `Based on the full consultation conversation, produce a final structured report.

Respond with ONLY valid JSON (no markdown fences) in this exact shape:
{
  "summary": "2-4 paragraph consultation summary",
  "symptoms_discussed": ["symptom1", "symptom2"],
  "possible_conditions": [{"name": "...", "likelihood": "low|moderate|high", "note": "disclaimer text"}],
  "medicines": [{"name": "...", "type": "OTC|prescription", "usage": "...", "precaution": "..."}],
  "suggested_tests": ["test1"],
  "precautions": ["precaution1"],
  "self_care": ["tip1"],
  "urgent_care_required": false,
  "urgent_care_reason": null,
  "recommended_specialty_slug": "general-physician",
  "disclaimer": "Always consult a qualified doctor for professional evaluation."
}

For recommended_specialty_slug, use one of: ${SPECIALTY_SLUGS.join(', ')}`;

function getAiConfig() {
  const apiKey = process.env.OPENAI_API_KEY;
  const model = process.env.OPENAI_MODEL || 'gpt-4o-mini';
  const baseUrl = (process.env.OPENAI_BASE_URL || 'https://api.openai.com/v1').replace(/\/$/, '');

  if (!apiKey) {
    return null;
  }

  return { apiKey, model, baseUrl };
}

async function callChat(messages, { temperature = 0.6, maxTokens = 1200 } = {}) {
  const config = getAiConfig();
  if (!config) {
    throw new Error('AI Doctor is not configured. Set OPENAI_API_KEY in backend environment.');
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
    throw new Error(`AI request failed (${res.status}): ${body.slice(0, 200)}`);
  }

  const data = await res.json();
  return data.choices?.[0]?.message?.content?.trim() || '';
}

export async function generateChatReply(conversationMessages) {
  const messages = [
    { role: 'system', content: SYSTEM_PROMPT },
    ...conversationMessages.map((m) => ({ role: m.role, content: m.content })),
  ];

  return callChat(messages);
}

export async function generateConsultationSummary(conversationMessages) {
  const messages = [
    { role: 'system', content: SUMMARY_PROMPT },
    {
      role: 'user',
      content: conversationMessages
        .map((m) => `${m.role === 'user' ? 'Patient' : 'AI Doctor'}: ${m.content}`)
        .join('\n\n'),
    },
  ];

  const raw = await callChat(messages, { temperature: 0.3, maxTokens: 2000 });

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

export function isAiDoctorConfigured() {
  return Boolean(getAiConfig());
}
