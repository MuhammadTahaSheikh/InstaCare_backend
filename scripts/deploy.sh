#!/usr/bin/env bash
# Run on the VPS after pulling latest backend code:
#   cd /path/to/backend && bash scripts/deploy.sh
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo "==> BestechCare API deploy"
echo "    Directory: $ROOT"

if [[ ! -f .env ]]; then
  echo "ERROR: .env not found. Copy .env.example and fill in production values."
  exit 1
fi

if [[ -f .env.local ]] && [[ "${KEEP_ENV_LOCAL:-}" != "1" ]]; then
  echo "WARNING: Removing .env.local on server (local dev overrides must not run in production)."
  rm -f .env.local
fi

echo "==> Installing dependencies..."
npm install

echo "==> Running database migrations..."
npm run db:migrate:email
npm run db:migrate:payments

echo "==> Restarting PM2..."
if pm2 describe instacare-api >/dev/null 2>&1; then
  pm2 reload ecosystem.config.cjs --update-env
else
  pm2 start ecosystem.config.cjs
fi

pm2 save

echo "==> Deploy complete. API health:"
sleep 2
curl -sf "http://127.0.0.1:${PORT:-5002}/api/health" || echo "(health check skipped — set PORT or check pm2 logs)"
