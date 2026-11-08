#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

python -m pip install --upgrade pip
python -m pip install -r requirements.txt
mkdir -p data

if [ ! -f .env ]; then
  SECRET_KEY="$(python -c 'import secrets; print(secrets.token_urlsafe(48))')"
  ADMIN_PASSWORD="$(python -c 'import secrets; print(secrets.token_urlsafe(24))')"
  cat > .env <<EOF
DATABASE_URL=sqlite:///data/payder.db
ADMIN_PASSWORD=${ADMIN_PASSWORD}
SECRET_KEY=${SECRET_KEY}
COOKIE_SECURE=false
EOF
  chmod 600 .env
  echo
  echo "Payder: создан локальный .env с уникальными секретами."
  echo "Пароль администратора для тестовой среды: ${ADMIN_PASSWORD}"
  echo "Сохраните его в менеджере паролей; не отправляйте и не добавляйте в Git."
else
  echo "Payder: существующий .env оставлен без изменений."
fi
