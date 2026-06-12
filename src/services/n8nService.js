const TIMEOUT_MS = 8000;

async function postWebhook(url, payload) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), TIMEOUT_MS);

  try {
    const res = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
      signal: controller.signal,
    });

    if (!res.ok) {
      const body = await res.text().catch(() => '');
      console.warn('[n8n] webhook failed', res.status, body.slice(0, 200));
      return { ok: false, status: res.status };
    }

    return { ok: true };
  } catch (err) {
    console.warn('[n8n] webhook error:', err.message);
    return { ok: false, error: err.message };
  } finally {
    clearTimeout(timer);
  }
}

export async function notifyN8n(payload) {
  const url = process.env.N8N_APPOINTMENT_WEBHOOK_URL;
  if (!url) {
    console.log('[n8n] N8N_APPOINTMENT_WEBHOOK_URL not set — skipping', payload.event);
    return { skipped: true };
  }

  return postWebhook(url, payload);
}
