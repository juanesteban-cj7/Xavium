#!/bin/sh
set -eu

export DISPLAY=:99

generate_secret() {
    python -c "import secrets; print(secrets.token_hex(32))"
}

RUNTIME_ENV=/data/runtime.env

if [ -f "$RUNTIME_ENV" ]; then
    set -a
    . "$RUNTIME_ENV"
    set +a
fi

FERNET_KEY="${FERNET_KEY:-$(python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")}"
HMAC_SECRET="${HMAC_SECRET:-$(generate_secret)}"
SESSION_SECRET="${SESSION_SECRET:-$(generate_secret)}"

cat > "$RUNTIME_ENV" <<EOF
FERNET_KEY=$FERNET_KEY
HMAC_SECRET=$HMAC_SECRET
SESSION_SECRET=$SESSION_SECRET
EOF

cat > /app/config/.env <<EOF
DATABASE_URL=sqlite:///database/xavium.db
INSTITUTIONAL_EMAIL_DOMAIN=${INSTITUTIONAL_EMAIL_DOMAIN:-@javeriana.edu.co}
FERNET_KEY=${FERNET_KEY}
HMAC_SECRET=${HMAC_SECRET}
SESSION_SECRET=${SESSION_SECRET}
PASSWORD_MIN_LENGTH=${PASSWORD_MIN_LENGTH:-8}
MAX_LOGIN_ATTEMPTS=${MAX_LOGIN_ATTEMPTS:-5}
LOGIN_LOCKOUT_MINUTES=${LOGIN_LOCKOUT_MINUTES:-15}
SESSION_EXPIRATION_HOURS=${SESSION_EXPIRATION_HOURS:-12}
EMAIL_VERIFICATION_TOKEN_EXPIRATION_HOURS=${EMAIL_VERIFICATION_TOKEN_EXPIRATION_HOURS:-24}
SMTP_HOST=${SMTP_HOST:-}
SMTP_PORT=${SMTP_PORT:-587}
SMTP_USER=${SMTP_USER:-}
SMTP_PASSWORD=${SMTP_PASSWORD:-}
SMTP_FROM=${SMTP_FROM:-no-reply@javeriana.edu.co}
EOF

rm -f /tmp/.X99-lock
rm -rf /tmp/.X11-unix/X99
Xvfb "${DISPLAY}" -screen 0 1280x800x24 &
sleep 1
fluxbox >/tmp/fluxbox.log 2>&1 &
x11vnc -display "${DISPLAY}" -forever -shared -nopw -listen 0.0.0.0 -rfbport 5900 >/tmp/x11vnc.log 2>&1 &
websockify --web=/usr/share/novnc 6080 0.0.0.0:5900 >/tmp/websockify.log 2>&1 &

exec python -u main.py
