import crypto from 'crypto';
import pool from '../config/db.js';

const MOCK_OTP = '123456';

export function generateTransactionId(method) {
  const prefix = method === 'jazzcash' ? 'JC' : 'EP';
  return `${prefix}${Date.now()}${crypto.randomBytes(3).toString('hex').toUpperCase()}`;
}

export async function getPaymentPreview(type, referenceId, userId) {
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
    };
  }

  return null;
}

export async function initiatePayment({ userId, type, referenceId, method, phone }) {
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

  const [result] = await pool.query(
    `INSERT INTO payments (user_id, amount, method, reference_type, reference_id, phone)
     VALUES (?, ?, ?, ?, ?, ?)`,
    [userId, preview.amount, method, type, referenceId, phone]
  );

  // In production: call JazzCash/EasyPaisa API here to send OTP to phone
  return {
    payment_id: result.insertId,
    amount: preview.amount,
    method,
    message: `OTP sent to ${phone}. Use ${MOCK_OTP} in demo mode.`,
    demo_otp: process.env.NODE_ENV !== 'production' ? MOCK_OTP : undefined,
  };
}

export async function verifyPayment({ paymentId, userId, otp }) {
  const [payments] = await pool.query(
    'SELECT * FROM payments WHERE id = ? AND user_id = ?',
    [paymentId, userId]
  );
  if (payments.length === 0) throw new Error('Payment not found');

  const payment = payments[0];
  if (payment.status === 'completed') throw new Error('Payment already completed');

  if (otp !== MOCK_OTP) {
    await pool.query('UPDATE payments SET status = ? WHERE id = ?', ['failed', paymentId]);
    throw new Error('Invalid OTP. Please try again.');
  }

  const transactionId = generateTransactionId(payment.method);
  await pool.query(
    'UPDATE payments SET status = ?, transaction_id = ? WHERE id = ?',
    ['completed', transactionId, paymentId]
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
