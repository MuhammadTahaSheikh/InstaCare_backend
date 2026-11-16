import crypto from 'crypto';
import pool from '../config/db.js';
import * as jazzcash from './jazzcashService.js';
import { notifyAppointmentConfirmed } from './appointmentNotificationService.js';
import { sendPaymentOtpEmail } from './emailService.js';
import { sendPaymentOtpSms, isSmsConfigured } from './smsService.js';
import { maskPhone, isValidPakistaniMobile } from '../utils/phone.js';
import { generateOtp, hashOtp, verifyOtp, getOtpExpiry, isOtpExpired } from '../utils/otp.js';

export function isPaymentLive() {
  const mode = (process.env.PAYMENT_MODE || '').toLowerCase().trim();
  if (mode === 'test') return false;
  if (mode === 'live') return jazzcash.isJazzCashConfigured();
  return jazzcash.isProduction() && jazzcash.isJazzCashConfigured();
}

export function isJazzCashLive() {
  return isPaymentLive();
}

export async function getPaymentPreview(type, referenceId, userId) {
  const live = isPaymentLive();

  if (type === 'appointment') {
    const [rows] = await pool.query(
      `SELECT a.*, d.consultation_fee AS amount, u.name AS doctor_name
       FROM appointments a
       JOIN doctors d ON a.doctor_id = d.id
       JOIN users u ON d.user_id = u.id
       WHERE a.id = ? AND a.patient_id = ?`,
      [referenceId, userId]
    );
    if (rows.length === 0) return null;
    const row = rows[0];
    return {
      reference_type: 'appointment',
      reference_id: row.id,
      amount: row.amount,
      title: `Consultation with ${row.doctor_name}`,
      payment_status: row.payment_status,
      status: row.status,
      payment_live: live,
      jazzcash_live: live,
    };
  }

  if (type === 'order') {
    const [rows] = await pool.query(
      'SELECT * FROM orders WHERE id = ? AND user_id = ?',
      [referenceId, userId]
    );
    if (rows.length === 0) return null;
    const row = rows[0];
    return {
      reference_type: 'order',
      reference_id: row.id,
      amount: row.total_amount,
      title: `Medicine Order #${row.id}`,
      payment_status: row.payment_status,
      status: row.status,
      payment_live: live,
      jazzcash_live: live,
    };
  }

  return null;
}

async function completePayment(payment) {
  const transactionId =
    payment.gateway_txn_ref || generateTransactionId(payment.method);

  await pool.query(
    'UPDATE payments SET status = ?, transaction_id = ? WHERE id = ?',
    ['completed', transactionId, payment.id]
  );

  if (payment.reference_type === 'appointment') {
    const roomId = `room-${payment.reference_id}-${crypto.randomBytes(4).toString('hex')}`;
    await pool.query(
      `UPDATE appointments SET payment_status = 'paid', status = 'confirmed', room_id = ?
       WHERE id = ? AND type = 'online'`,
      [roomId, payment.reference_id]
    );
    await pool.query(
      `UPDATE appointments SET payment_status = 'paid', status = 'confirmed'
       WHERE id = ? AND type = 'in_clinic'`,
      [payment.reference_id]
    );

    notifyAppointmentConfirmed(payment.reference_id).catch((err) => {
      console.error('[appointment] post-payment notify failed:', err.message);
    });
  } else if (payment.reference_type === 'order') {
    await pool.query(
      `UPDATE orders SET payment_status = 'paid', status = 'confirmed' WHERE id = ?`,
      [payment.reference_id]
    );
  }

  return {
    success: true,
    transaction_id: transactionId,
    reference_type: payment.reference_type,
    reference_id: payment.reference_id,
  };
}

export function generateTransactionId(method) {
  const prefix = method === 'jazzcash' ? 'JC' : 'EP';
  return `${prefix}${Date.now()}${crypto.randomBytes(3).toString('hex').toUpperCase()}`;
}

async function getUserContact(userId) {
  const [rows] = await pool.query('SELECT email, name FROM users WHERE id = ?', [userId]);
  return rows[0] || null;
}

/** Test mode: OTP to phone via SMS (or email fallback). No wallet deduction. */
async function startTestOtpPayment({ paymentId, userId, preview, phone, method }) {
  if (!isValidPakistaniMobile(phone)) {
    throw new Error('Enter a valid Pakistani mobile number (03XX-XXXXXXX)');
  }

  const otp = generateOtp();
  await pool.query(
    'UPDATE payments SET otp_hash = ?, otp_expires_at = ?, gateway_txn_ref = NULL WHERE id = ?',
    [hashOtp(otp), getOtpExpiry(), paymentId]
  );

  let smsSent = false;
  if (isSmsConfigured()) {
    try {
      const smsResult = await sendPaymentOtpSms({
        to: phone,
        otp,
        amount: preview.amount,
        title: preview.title,
      });
      if (smsResult.sent) {
        smsSent = true;
        return {
          payment_id: paymentId,
          amount: preview.amount,
          method,
          mode: 'sms',
          payment_mode: 'test',
          otp_required: true,
          message: `OTP sent to ${smsResult.to}. Check your SMS (valid 5 minutes). No money will be deducted in test mode.`,
        };
      }
    } catch (err) {
      console.warn('[payment] SMS OTP failed, trying email fallback:', err.message);
    }
  }

  const user = await getUserContact(userId);
  if (user?.email) {
    await sendPaymentOtpEmail({
      to: user.email,
      name: user.name,
      otp,
      amount: preview.amount,
      title: preview.title,
      phone,
    });

    const response = {
      payment_id: paymentId,
      amount: preview.amount,
      method,
      mode: smsSent ? 'sms' : 'email',
      payment_mode: 'test',
      otp_required: true,
      message: smsSent
        ? `OTP sent to ${maskPhone(phone)}. Check your SMS.`
        : `SMS unavailable — OTP sent to ${user.email}. No money will be deducted in test mode.`,
    };

    if (!smsSent && process.env.NODE_ENV !== 'production') {
      response.demo_otp = otp;
    }
    return response;
  }

  if (process.env.NODE_ENV !== 'production') {
    return {
      payment_id: paymentId,
      amount: preview.amount,
      method,
      mode: 'test',
      payment_mode: 'test',
      otp_required: true,
      message: `Test mode — configure Twilio for SMS OTP to ${maskPhone(phone)}. No money deducted.`,
      demo_otp: otp,
    };
  }

  throw new Error(
    'SMS OTP is not configured. Add TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, and TWILIO_FROM_NUMBER to backend/.env'
  );
}

export async function initiatePayment({ userId, type, referenceId, method, phone, cnic }) {
  const preview = await getPaymentPreview(type, referenceId, userId);
  if (!preview) throw new Error('Payment reference not found');
  if (preview.payment_status === 'paid') throw new Error('Already paid');

  const [pending] = await pool.query(
    `SELECT id FROM payments WHERE reference_type = ? AND reference_id = ? AND status = 'pending'`,
    [type, referenceId]
  );
  if (pending.length > 0) {
    await pool.query('UPDATE payments SET status = ? WHERE id = ?', ['failed', pending[0].id]);
  }

  const cnicLast6 = cnic ? String(cnic).replace(/\D/g, '').slice(-6) : null;

  const [result] = await pool.query(
    `INSERT INTO payments (user_id, amount, method, reference_type, reference_id, phone, cnic_last6)
     VALUES (?, ?, ?, ?, ?, ?, ?)`,
    [userId, preview.amount, method, type, referenceId, phone, cnicLast6]
  );

  const paymentId = result.insertId;
  const live = isPaymentLive();

  // Live mode: JazzCash deducts real money from the wallet after OTP verification.
  if (method === 'jazzcash' && live) {
    if (!cnicLast6 || cnicLast6.length !== 6) {
      await pool.query('UPDATE payments SET status = ? WHERE id = ?', ['failed', paymentId]);
      throw new Error('Last 6 digits of CNIC are required for JazzCash payments');
    }

    try {
      const jc = await jazzcash.initiateWalletPayment({
        paymentId,
        amount: preview.amount,
        phone,
        cnicLast6,
        billReference: `${type}-${referenceId}`,
        description: preview.title,
      });

      await pool.query('UPDATE payments SET gateway_txn_ref = ? WHERE id = ?', [
        jc.txnRefNo,
        paymentId,
      ]);

      if (jc.success) {
        const [rows] = await pool.query('SELECT * FROM payments WHERE id = ?', [paymentId]);
        const completed = await completePayment({
          ...rows[0],
          gateway_txn_ref: jc.retrievalRef || jc.txnRefNo,
        });
        return {
          payment_id: paymentId,
          amount: preview.amount,
          method,
          mode: 'jazzcash',
          payment_mode: 'live',
          completed: true,
          message: jc.message,
          ...completed,
        };
      }

      if (jc.otpPending) {
        return {
          payment_id: paymentId,
          amount: preview.amount,
          method,
          mode: 'jazzcash',
          payment_mode: 'live',
          otp_required: true,
          message: `OTP sent to ${jazzcash.normalizePhone(phone)} via JazzCash. Amount will be deducted from your wallet after verification.`,
        };
      }

      await pool.query('UPDATE payments SET status = ? WHERE id = ?', ['failed', paymentId]);
      throw new Error(jc.message || 'JazzCash payment initiation failed');
    } catch (err) {
      await pool.query('UPDATE payments SET status = ? WHERE id = ?', ['failed', paymentId]);
      throw new Error(err.message || 'JazzCash payment initiation failed');
    }
  }

  // Test mode (sandbox) or EasyPaisa: SMS OTP, no wallet deduction.
  try {
    return await startTestOtpPayment({ paymentId, userId, preview, phone, method });
  } catch (err) {
    await pool.query('UPDATE payments SET status = ? WHERE id = ?', ['failed', paymentId]);
    throw err;
  }
}

export async function verifyPayment({ paymentId, userId, otp }) {
  const [payments] = await pool.query(
    'SELECT * FROM payments WHERE id = ? AND user_id = ?',
    [paymentId, userId]
  );
  if (payments.length === 0) throw new Error('Payment not found');

  const payment = payments[0];
  if (payment.status === 'completed') throw new Error('Payment already completed');

  // Test mode: verify locally stored OTP — no money deducted.
  if (payment.otp_hash) {
    if (isOtpExpired(payment.otp_expires_at)) {
      await pool.query('UPDATE payments SET status = ? WHERE id = ?', ['failed', paymentId]);
      throw new Error('OTP expired. Please start payment again.');
    }
    if (!verifyOtp(otp, payment.otp_hash)) {
      await pool.query('UPDATE payments SET status = ? WHERE id = ?', ['failed', paymentId]);
      throw new Error('Invalid OTP. Please try again.');
    }
    await pool.query(
      'UPDATE payments SET otp_hash = NULL, otp_expires_at = NULL WHERE id = ?',
      [paymentId]
    );
    return completePayment(payment);
  }

  // Live mode: JazzCash verifies OTP and deducts from wallet.
  if (
    payment.method === 'jazzcash' &&
    payment.gateway_txn_ref &&
    isPaymentLive()
  ) {
    const preview = await getPaymentPreview(
      payment.reference_type,
      payment.reference_id,
      userId
    );

    try {
      const jc = await jazzcash.verifyWalletPayment({
        paymentId: payment.id,
        txnRefNo: payment.gateway_txn_ref,
        amount: payment.amount,
        phone: payment.phone,
        cnicLast6: payment.cnic_last6,
        billReference: `${payment.reference_type}-${payment.reference_id}`,
        description: preview?.title || 'BestechCare payment',
        otp,
      });

      if (!jc.success) {
        throw new Error(jc.message || 'Invalid OTP. Please try again.');
      }

      payment.gateway_txn_ref = jc.retrievalRef || payment.gateway_txn_ref;
      return completePayment(payment);
    } catch (err) {
      const msg = err.message?.toLowerCase() || '';
      const isUserRetryable =
        msg.includes('otp') || msg.includes('invalid') || msg.includes('incorrect');
      if (!isUserRetryable) {
        await pool.query('UPDATE payments SET status = ? WHERE id = ?', ['failed', paymentId]);
      }
      throw err;
    }
  }

  await pool.query('UPDATE payments SET status = ? WHERE id = ?', ['failed', paymentId]);
  throw new Error('Invalid OTP. Please try again.');
}

export async function handleJazzCashCallback(responseData) {
  if (!isPaymentLive()) {
    throw new Error('JazzCash callbacks are only handled in live mode');
  }

  if (!jazzcash.verifyCallbackHash(responseData)) {
    throw new Error('Invalid JazzCash callback signature');
  }

  if (!jazzcash.isSuccessResponse(responseData)) {
    throw new Error(jazzcash.getResponseMessage?.(responseData) || 'Payment was not successful');
  }

  const paymentId = Number(responseData.ppmpf_1);
  if (!paymentId) throw new Error('Payment reference missing in callback');

  const [payments] = await pool.query('SELECT * FROM payments WHERE id = ?', [paymentId]);
  if (payments.length === 0) throw new Error('Payment not found');

  const payment = payments[0];
  if (payment.status === 'completed') {
    return { already_completed: true, payment_id: payment.id };
  }

  payment.gateway_txn_ref =
    responseData.pp_RetrievalReferenceNo ||
    responseData.pp_RetreivalReferenceNo ||
    responseData.pp_TxnRefNo ||
    payment.gateway_txn_ref;

  const result = await completePayment(payment);
  return { ...result, payment_id: payment.id };
}
