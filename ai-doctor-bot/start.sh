#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
BACKEND_ROOT="$(cd "$ROOT/.." && pwd)"
cd "$ROOT"

# Load backend .env (GROQ_API_KEY, etc.) for dynamic LLM
if [[ -f "$BACKEND_ROOT/.env" ]]; then
  set -a
  # shellcheck disable=SC1091
  source "$BACKEND_ROOT/.env"
  set +a
fi

if [[ ! -d venv ]]; then
  python3 -m venv venv
fi

source venv/bin/activate
pip install -q -r requirements.txt

exec uvicorn app:app --host 127.0.0.1 --port "${AI_DOCTOR_BOT_PORT:-5003}"
