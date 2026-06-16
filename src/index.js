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

// Public API: web app, Expo, and native mobile (Origin may be missing or "null")
app.use(
  cors({
    origin: true,
    credentials: true,
    methods: ['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'OPTIONS'],
    allowedHeaders: ['Content-Type', 'Authorization', 'x-webhook-secret'],
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
