import * as paymentService from '../services/paymentService.js';

export async function getPreview(req, res) {
  try {
    const { type, id } = req.query;
    if (!type || !id) {
      return res.status(400).json({ error: 'Type and id are required' });
    }

    const preview = await paymentService.getPaymentPreview(type, id, req.user.id);
    if (!preview) {
      return res.status(404).json({ error: 'Not found' });
    }
    res.json(preview);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
}

export async function initiate(req, res) {
  try {
    const { type, reference_id, method, phone } = req.body;

    if (!type || !reference_id || !method || !phone) {
      return res.status(400).json({ error: 'All payment fields are required' });
    }
    if (!['jazzcash', 'easypaisa'].includes(method)) {
      return res.status(400).json({ error: 'Invalid payment method' });
    }

    const result = await paymentService.initiatePayment({
      userId: req.user.id,
      type,
      referenceId: reference_id,
      method,
      phone,
    });
    res.json(result);
  } catch (err) {
    res.status(400).json({ error: err.message });
  }
}

export async function verify(req, res) {
  try {
    const { payment_id, otp } = req.body;
    if (!payment_id || !otp) {
      return res.status(400).json({ error: 'Payment ID and OTP are required' });
    }

    const result = await paymentService.verifyPayment({
      paymentId: payment_id,
      userId: req.user.id,
      otp,
    });
    res.json(result);
  } catch (err) {
    res.status(400).json({ error: err.message });
  }
}
