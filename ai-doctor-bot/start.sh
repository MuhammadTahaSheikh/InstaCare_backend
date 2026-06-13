#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

if [[ ! -d venv ]]; then
  python3 -m venv venv
fi

source venv/bin/activate
pip install -q -r requirements.txt

exec uvicorn app:app --host 127.0.0.1 --port "${AI_DOCTOR_BOT_PORT:-5003}"
