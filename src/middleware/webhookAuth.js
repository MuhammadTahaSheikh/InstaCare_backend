export function requireWebhookSecret(req, res, next) {
  const expected = process.env.N8N_WEBHOOK_SECRET;
  if (!expected) {
    return res.status(503).json({ error: 'Webhook secret not configured' });
  }

  const provided = req.headers['x-webhook-secret'];
  if (!provided || provided !== expected) {
    return res.status(401).json({ error: 'Invalid webhook secret' });
  }

  next();
}
