#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
BACKEND_ROOT="$(cd "$ROOT/.." && pwd)"
cd "$ROOT"

# Load AI Doctor / LLM vars from backend .env (do not source whole file — SMTP values break bash)
if [[ -f "$BACKEND_ROOT/.env" ]]; then
  while IFS= read -r line || [[ -n "$line" ]]; do
    [[ "$line" =~ ^[[:space:]]*# ]] && continue
    [[ -z "${line// }" ]] && continue
    if [[ "$line" =~ ^(GROQ_|OLLAMA_|AI_DOCTOR_|OPENAI_) ]]; then
      export "$line"
    fi
  done < "$BACKEND_ROOT/.env"
fi

if [[ ! -d venv ]]; then
  python3 -m venv venv
fi

source venv/bin/activate
pip install -q -r requirements.txt

exec uvicorn app:app --host 127.0.0.1 --port "${AI_DOCTOR_BOT_PORT:-5003}"
