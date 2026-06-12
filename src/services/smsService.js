import { normalizePhone, maskPhone } from '../utils/phone.js';

export function isSmsConfigured() {
  const { TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_FROM_NUMBER } = process.env;
  return Boolean(
    TWILIO_ACCOUNT_SID &&
      TWILIO_AUTH_TOKEN &&
      TWILIO_FROM_NUMBER &&
      !TWILIO_ACCOUNT_SID.includes('paste_')
  );
}

export function toE164Pakistan(phone) {
  const normalized = normalizePhone(phone);
  if (!/^03\d{9}$/.test(normalized)) return null;
  return `+92${normalized.slice(1)}`;
}

export async function sendPaymentOtpSms({ to, otp, amount, title }) {
  if (!isSmsConfigured()) {
    return { sent: false, reason: 'not_configured' };
  }

  const e164 = toE164Pakistan(to);
  if (!e164) {
    return { sent: false, reason: 'invalid_phone' };
  }

  const body =
    `BestechCare: Your payment OTP for "${title}" ` +
    `(Rs. ${Number(amount).toLocaleString()}) is ${otp}. ` +
    `Valid for 5 minutes. Do not share this code.`;

  const accountSid = process.env.TWILIO_ACCOUNT_SID;
  const authToken = process.env.TWILIO_AUTH_TOKEN;
  const from = process.env.TWILIO_FROM_NUMBER;
  const url = `https://api.twilio.com/2010-04-01/Accounts/${accountSid}/Messages.json`;
  const params = new URLSearchParams({ To: e164, From: from, Body: body });

  const res = await fetch(url, {
    method: 'POST',
    headers: {
      Authorization: `Basic ${Buffer.from(`${accountSid}:${authToken}`).toString('base64')}`,
      'Content-Type': 'application/x-www-form-urlencoded',
    },
    body: params.toString(),
  });

  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    const errMsg = data.message || `Twilio error (${res.status})`;
    console.error('[sms] Twilio error:', errMsg);
    throw new Error(errMsg);
  }

  return { sent: true, to: maskPhone(to) };
}
