import crypto from 'crypto';

const OTP_TTL_MS = 5 * 60 * 1000;

export function generateOtp() {
  return String(crypto.randomInt(100000, 1000000));
}

export function hashOtp(otp) {
  return crypto.createHash('sha256').update(otp).digest('hex');
}

export function verifyOtp(otp, hash) {
  if (!otp || !hash) return false;
  const candidate = hashOtp(String(otp).trim());
  return crypto.timingSafeEqual(Buffer.from(candidate), Buffer.from(hash));
}

export function getOtpExpiry() {
  return new Date(Date.now() + OTP_TTL_MS);
}

export function isOtpExpired(expiresAt) {
  if (!expiresAt) return true;
  return new Date(expiresAt).getTime() < Date.now();
}
