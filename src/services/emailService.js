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
