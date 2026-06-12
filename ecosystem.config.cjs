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
      },
    },
  ],
};
