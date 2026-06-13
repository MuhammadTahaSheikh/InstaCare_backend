const path = require('path');

module.exports = {
  apps: [
    {
      name: 'instacare-api',
      script: 'src/index.js',
      cwd: __dirname,
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '512M',
      output: path.join(__dirname, 'logs', 'pm2-out.log'),
      error: path.join(__dirname, 'logs', 'pm2-error.log'),
      merge_logs: true,
      env: {
        NODE_ENV: 'production',
        PORT: 5002,
        AI_DOCTOR_BOT_URL: 'http://127.0.0.1:5003',
      },
    },
    {
      name: 'ai-doctor-bot',
      script: 'ai-doctor-bot/start.sh',
      cwd: __dirname,
      interpreter: 'bash',
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '256M',
      output: path.join(__dirname, 'logs', 'ai-doctor-bot-out.log'),
      error: path.join(__dirname, 'logs', 'ai-doctor-bot-error.log'),
      merge_logs: true,
      env: {
        AI_DOCTOR_BOT_PORT: '5003',
      },
    },
  ],
};
