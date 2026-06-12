import { Server } from 'socket.io';
import jwt from 'jsonwebtoken';

const rooms = new Map();

export function initSocket(httpServer) {
  const io = new Server(httpServer, {
    cors: {
      origin: ['https://bestech-care.vercel.app', 'http://localhost:3000'],
      methods: ['GET', 'POST'],
    },
  });

  io.use((socket, next) => {
    const token = socket.handshake.auth?.token;
    if (!token) return next(new Error('Authentication required'));
    try {
      socket.user = jwt.verify(token, process.env.JWT_SECRET);
      next();
    } catch {
      next(new Error('Invalid token'));
    }
  });

  io.on('connection', (socket) => {
    socket.on('join-room', ({ roomId, role }) => {
      socket.join(roomId);
      socket.roomId = roomId;
      socket.role = role;

      if (!rooms.has(roomId)) rooms.set(roomId, new Set());
      rooms.get(roomId).add(socket.id);

      const others = [...socket.adapter.rooms.get(roomId) || []].filter((id) => id !== socket.id);
      if (others.length > 0) {
        socket.to(roomId).emit('user-joined', { role, socketId: socket.id });
      }

      socket.emit('room-joined', { roomId, participants: rooms.get(roomId).size });
    });

    socket.on('offer', ({ roomId, offer }) => {
      socket.to(roomId).emit('offer', { offer, from: socket.role });
    });

    socket.on('answer', ({ roomId, answer }) => {
      socket.to(roomId).emit('answer', { answer, from: socket.role });
    });

    socket.on('ice-candidate', ({ roomId, candidate }) => {
      socket.to(roomId).emit('ice-candidate', { candidate, from: socket.role });
    });

    socket.on('leave-room', ({ roomId }) => {
      socket.to(roomId).emit('user-left', { role: socket.role });
      socket.leave(roomId);
      rooms.get(roomId)?.delete(socket.id);
    });

    socket.on('disconnect', () => {
      if (socket.roomId) {
        socket.to(socket.roomId).emit('user-left', { role: socket.role });
        rooms.get(socket.roomId)?.delete(socket.id);
      }
    });
  });

  return io;
}
