import crypto from 'crypto';

const SANDBOX_BASE = 'https://sandbox.jazzcash.com.pk/ApplicationAPI/API';
const PRODUCTION_BASE = 'https://payments.jazzcash.com.pk/ApplicationAPI/API';

function getConfig() {
  const env = process.env.JAZZCASH_ENV === 'production' ? 'production' : 'sandbox';
  const merchantId = process.env.JAZZCASH_MERCHANT_ID;
  const password = process.env.JAZZCASH_PASSWORD;
  const integritySalt = process.env.JAZZCASH_INTEGRITY_SALT;

  if (!merchantId || !password || !integritySalt) {
    return null;
  }

  const apiBase = env === 'production' ? PRODUCTION_BASE : SANDBOX_BASE;
  const returnUrl =
    process.env.JAZZCASH_RETURN_URL ||
    `${process.env.BACKEND_URL || `http://localhost:${process.env.PORT || 5001}`}/api/payments/jazzcash/callback`;

  return {
    env,
    merchantId,
    password,
    integritySalt,
    returnUrl,
    walletUrl: `${apiBase}/2.0/Purchase/DoMWalletTransaction`,
    defaultCnic: process.env.JAZZCASH_DEFAULT_CNIC || '345678',
  };
}

export function isJazzCashConfigured() {
  return getConfig() !== null;
}

export function normalizePhone(phone) {
  const digits = String(phone).replace(/\D/g, '');
  if (digits.startsWith('92') && digits.length === 12) {
    return `0${digits.slice(2)}`;
  }
  if (digits.length === 10 && digits.startsWith('3')) {
    return `0${digits}`;
  }
  return digits;
}

function formatDateTime(date = new Date()) {
  const pad = (n) => String(n).padStart(2, '0');
  return (
    `${date.getFullYear()}${pad(date.getMonth() + 1)}${pad(date.getDate())}` +
    `${pad(date.getHours())}${pad(date.getMinutes())}${pad(date.getSeconds())}`
  );
}

export function amountToPaisa(amount) {
  return String(Math.round(Number(amount) * 100));
}

export function generateTxnRefNo(paymentId) {
  return `BC${paymentId}${Date.now()}`.slice(0, 20);
}

export function generateSecureHash(data, integritySalt) {
  const sortedKeys = Object.keys(data)
    .filter((key) => key !== 'pp_SecureHash')
    .filter((key) => {
      const value = data[key];
      return value !== undefined && value !== null && String(value).length > 0;
    })
    .sort();

  const message = [integritySalt, ...sortedKeys.map((key) => String(data[key]))].join('&');

  return crypto.createHmac('sha256', integritySalt).update(message, 'utf8').digest('hex').toUpperCase();
}

function buildWalletPayload({
  config,
  txnRefNo,
  amount,
  phone,
  cnicLast6,
  billReference,
  description,
  otp,
  paymentId,
}) {
  const now = new Date();
  const expiry = new Date(now.getTime() + 60 * 60 * 1000);

  const payload = {
    pp_Version: '1.1',
    pp_TxnType: 'MWALLET',
    pp_Language: 'EN',
    pp_MerchantID: config.merchantId,
    pp_SubMerchantID: '',
    pp_Password: config.password,
    pp_BankID: '',
    pp_ProductID: '',
    pp_TxnRefNo: txnRefNo,
    pp_MobileNumber: normalizePhone(phone),
    pp_CNIC: String(cnicLast6).slice(-6),
    pp_Amount: amountToPaisa(amount),
    pp_TxnCurrency: 'PKR',
    pp_TxnDateTime: formatDateTime(now),
    pp_BillReference: billReference,
    pp_Description: description.slice(0, 200),
    pp_TxnExpiryDateTime: formatDateTime(expiry),
    pp_ReturnURL: config.returnUrl,
    ppmpf_1: String(paymentId),
    ppmpf_2: '',
    ppmpf_3: '',
    ppmpf_4: '',
    ppmpf_5: '',
  };

  if (otp) {
    payload.pp_OTP = String(otp).trim();
  }

  payload.pp_SecureHash = generateSecureHash(payload, config.integritySalt);
  return payload;
}

async function callWalletApi(url, payload) {
  const res = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
    body: JSON.stringify(payload),
  });

  const text = await res.text();
  let data;
  try {
    data = JSON.parse(text);
  } catch {
    throw new Error('Invalid response from JazzCash. Please try again.');
  }

  if (!res.ok) {
    throw new Error(data.pp_ResponseMessage || data.responseMessage || 'JazzCash request failed');
  }

  return data;
}

function getResponseCode(data) {
  return data.pp_ResponseCode || data.responseCode || '';
}

export function getResponseMessage(data) {
  return data.pp_ResponseMessage || data.responseMessage || 'JazzCash payment failed';
}

export function isSuccessResponse(data) {
  return getResponseCode(data) === '000';
}

export function isOtpPendingResponse(data) {
  const code = getResponseCode(data);
  const message = getResponseMessage(data).toLowerCase();
  if (code === '000') return false;
  return (
    code === '121' ||
    code === '157' ||
    message.includes('otp') ||
    message.includes('pin')
  );
}

export async function initiateWalletPayment({
  paymentId,
  amount,
  phone,
  cnicLast6,
  billReference,
  description,
}) {
  const config = getConfig();
  if (!config) throw new Error('JazzCash is not configured');

  const txnRefNo = generateTxnRefNo(paymentId);
  const payload = buildWalletPayload({
    config,
    txnRefNo,
    amount,
    phone,
    cnicLast6: cnicLast6 || config.defaultCnic,
    billReference,
    description,
    paymentId,
  });

  const data = await callWalletApi(config.walletUrl, payload);

  return {
    txnRefNo,
    data,
    success: isSuccessResponse(data),
    otpPending: isOtpPendingResponse(data),
    message: getResponseMessage(data),
    retrievalRef: data.pp_RetrievalReferenceNo || data.pp_RetreivalReferenceNo || null,
  };
}

export async function verifyWalletPayment({
  paymentId,
  txnRefNo,
  amount,
  phone,
  cnicLast6,
  billReference,
  description,
  otp,
}) {
  const config = getConfig();
  if (!config) throw new Error('JazzCash is not configured');

  const payload = buildWalletPayload({
    config,
    txnRefNo,
    amount,
    phone,
    cnicLast6: cnicLast6 || config.defaultCnic,
    billReference,
    description,
    otp,
    paymentId,
  });

  const data = await callWalletApi(config.walletUrl, payload);

  return {
    data,
    success: isSuccessResponse(data),
    message: getResponseMessage(data),
    retrievalRef: data.pp_RetrievalReferenceNo || data.pp_RetreivalReferenceNo || txnRefNo,
  };
}

export function verifyCallbackHash(responseData) {
  const config = getConfig();
  if (!config || !responseData?.pp_SecureHash) return false;

  const received = String(responseData.pp_SecureHash);
  const calculated = generateSecureHash(responseData, config.integritySalt);
  if (received.length !== calculated.length) return false;
  return crypto.timingSafeEqual(Buffer.from(received), Buffer.from(calculated));
}
