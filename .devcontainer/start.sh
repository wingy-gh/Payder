#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

if python -c 'import urllib.request; urllib.request.urlopen("http://127.0.0.1:8000/", timeout=1)' >/dev/null 2>&1; then
  echo "Payder уже запущен."
  exit 0
fi

nohup python -m uvicorn main:app --host 0.0.0.0 --port 8000 > .codespaces.log 2>&1 < /dev/null &
echo "Payder запускается на порту 8000. Лог: .codespaces.log"
