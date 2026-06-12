import http from 'http';
import express from 'express';
import cors from 'cors';
import './config/env.js';
import routes from './routes/index.js';
import { initSocket } from './socket.js';

const app = express();
const server = http.createServer(app);
const PORT = process.env.PORT || 5000;

const allowedOrigins = [
  'https://bestech-care.vercel.app',
  'http://localhost:3000',
  'http://127.0.0.1:3000',
];

app.use(
  cors({
    origin(origin, callback) {
      if (!origin || allowedOrigins.includes(origin)) callback(null, true);
      else callback(new Error('Not allowed by CORS'));
    },
    credentials: true,
  })
);
app.use(express.json());

app.get('/api/health', (_req, res) => {
  res.json({ status: 'ok', message: 'BestechCare API is running' });
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
