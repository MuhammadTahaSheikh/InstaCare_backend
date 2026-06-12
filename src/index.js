import http from 'http';
import express from 'express';
import cors from 'cors';
import './config/env.js';
import routes from './routes/index.js';
import { initSocket } from './socket.js';

const app = express();
const server = http.createServer(app);
const PORT = process.env.PORT || 5000;

app.use(cors());
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
