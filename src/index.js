import http from 'http';
import express from 'express';
import cors from 'cors';
import './config/env.js';
import routes from './routes/index.js';
import { initSocket } from './socket.js';
import { isPaymentLive } from './services/paymentService.js';
import { isSmsConfigured } from './services/smsService.js';

const app = express();
const server = http.createServer(app);
const PORT = process.env.PORT || 5000;

const allowedOrigins = [
  'https://bestech-care.vercel.app',
  'http://localhost:3000',
  'http://127.0.0.1:3000',
];

function isAllowedOrigin(origin) {
  // Native mobile apps often omit Origin or send the literal string "null"
  if (!origin || origin === 'null') return true;
  if (allowedOrigins.includes(origin)) return true;
  // Expo / React Native dev servers (Expo Go, web, Metro)
  if (/^https?:\/\/(localhost|127\.0\.0\.1|\d+\.\d+\.\d+\.\d+)(:\d+)?$/.test(origin)) {
    return true;
  }
  return false;
}

app.use(
  cors({
    origin(origin, callback) {
      callback(null, isAllowedOrigin(origin));
    },
    credentials: true,
  })
);
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

app.get('/api/health', (_req, res) => {
  res.json({
    status: 'ok',
    message: 'BestechCare API is running',
    payment_mode: isPaymentLive() ? 'live' : 'test',
    sms_configured: isSmsConfigured(),
  });
});

app.use('/api', routes);

app.use((_req, res) => {
  res.status(404).json({ error: 'Route not found' });
});

initSocket(server);

server.listen(PORT, () => {
  console.log(`BestechCare API running on http://localhost:${PORT}`);
  console.log(`WebSocket signaling ready for video consultations`);
});
