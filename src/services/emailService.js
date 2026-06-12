import nodemailer from 'nodemailer';

let transporter = null;

function getTransporter() {
  if (transporter) return transporter;

  const { SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS } = process.env;
  if (!SMTP_HOST || !SMTP_USER || !SMTP_PASS) {
    return null;
  }

  transporter = nodemailer.createTransport({
    host: SMTP_HOST,
    port: Number(SMTP_PORT) || 587,
    secure: process.env.SMTP_SECURE === 'true',
    auth: { user: SMTP_USER, pass: SMTP_PASS },
  });

  return transporter;
}

export async function sendVerificationEmail({ to, name, verifyUrl }) {
  const from = process.env.SMTP_FROM || process.env.SMTP_USER || 'noreply@bestechcare.pk';
  const subject = 'Verify your BestechCare account';
  const text = `Hi ${name},\n\nPlease verify your email by opening this link:\n${verifyUrl}\n\nThis link expires in 24 hours.\n\nIf you did not create an account, you can ignore this email.`;
  const html = `
    <p>Hi ${name},</p>
    <p>Please verify your email to activate your BestechCare account:</p>
    <p><a href="${verifyUrl}">Verify my email</a></p>
    <p>Or copy this link into your browser:<br>${verifyUrl}</p>
    <p>This link expires in 24 hours.</p>
    <p>If you did not create an account, you can ignore this email.</p>
  `;

  const mailer = getTransporter();
  if (!mailer) {
    console.log('[email] SMTP not configured — verification link for', to);
    console.log(verifyUrl);
    return { devMode: true };
  }

  await mailer.sendMail({ from, to, subject, text, html });
  return { devMode: false };
}

export async function sendPaymentOtpEmail({ to, name, otp, amount, title, phone }) {
  const from = process.env.SMTP_FROM || process.env.SMTP_USER || 'noreply@bestechcare.pk';
  const subject = `Your BestechCare payment OTP — Rs. ${Number(amount).toLocaleString()}`;
  const text = `Hi ${name},\n\nYour OTP for "${title}" (Rs. ${Number(amount).toLocaleString()}) is: ${otp}\n\nWallet number: ${phone}\nThis OTP expires in 5 minutes.\n\nIf you did not request this payment, ignore this email.`;
  const html = `
    <p>Hi ${name},</p>
    <p>Your OTP for <strong>${title}</strong> (Rs. ${Number(amount).toLocaleString()}) is:</p>
    <p style="font-size:24px;font-weight:bold;letter-spacing:4px;">${otp}</p>
    <p>Wallet number: ${phone}</p>
    <p>This OTP expires in 5 minutes.</p>
    <p>If you did not request this payment, you can ignore this email.</p>
  `;

  const mailer = getTransporter();
  if (!mailer) {
    console.log('[email] SMTP not configured — payment OTP for', to, ':', otp);
    return { devMode: true };
  }

  await mailer.sendMail({ from, to, subject, text, html });
  return { devMode: false };
}

export async function sendAppointmentConfirmationEmail({
  to,
  name,
  doctorName,
  specialtyName,
  appointmentDisplay,
  typeLabel,
  roomId,
  frontendUrl,
}) {
  const from = process.env.SMTP_FROM || process.env.SMTP_USER || 'noreply@bestechcare.pk';
  const subject = `Appointment confirmed — ${doctorName}`;
  const appointmentsUrl = frontendUrl ? `${frontendUrl.replace(/\/$/, '')}/appointments` : '';

  const onlineNote = roomId
    ? `\n\nYour online consultation room will be available from your appointments page before the scheduled time.`
    : '';

  const text = `Hi ${name},

Your appointment is confirmed.

Doctor: ${doctorName} (${specialtyName})
When: ${appointmentDisplay}
Type: ${typeLabel}${onlineNote}

We will send you a reminder email one hour before your appointment.

${appointmentsUrl ? `View your appointments: ${appointmentsUrl}\n\n` : ''}Thank you for choosing BestechCare.`;

  const onlineHtml = roomId
    ? '<p>Your online consultation will be available from your <strong>Appointments</strong> page before the scheduled time.</p>'
    : '';

  const html = `
    <p>Hi ${name},</p>
    <p>Your appointment is <strong>confirmed</strong>.</p>
    <table cellpadding="6" style="border-collapse:collapse;">
      <tr><td><strong>Doctor</strong></td><td>${doctorName} (${specialtyName})</td></tr>
      <tr><td><strong>When</strong></td><td>${appointmentDisplay}</td></tr>
      <tr><td><strong>Type</strong></td><td>${typeLabel}</td></tr>
    </table>
    ${onlineHtml}
    <p>We will send you a reminder email <strong>one hour before</strong> your appointment.</p>
    ${appointmentsUrl ? `<p><a href="${appointmentsUrl}">View my appointments</a></p>` : ''}
    <p>Thank you for choosing BestechCare.</p>
  `;

  const mailer = getTransporter();
  if (!mailer) {
    console.log('[email] SMTP not configured — appointment confirmation for', to);
    console.log(text);
    return { devMode: true };
  }

  await mailer.sendMail({ from, to, subject, text, html });
  return { devMode: false };
}
