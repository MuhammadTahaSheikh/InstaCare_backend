export function normalizePhone(phone) {
  const digits = String(phone || '').replace(/\D/g, '');
  if (digits.startsWith('92') && digits.length === 12) {
    return `0${digits.slice(2)}`;
  }
  if (digits.length === 10 && digits.startsWith('3')) {
    return `0${digits}`;
  }
  return digits;
}

export function isValidPakistaniMobile(phone) {
  const normalized = normalizePhone(phone);
  return /^03\d{9}$/.test(normalized);
}

export function maskPhone(phone) {
  const normalized = normalizePhone(phone);
  if (normalized.length < 7) return normalized;
  return `${normalized.slice(0, 4)}****${normalized.slice(-3)}`;
}
