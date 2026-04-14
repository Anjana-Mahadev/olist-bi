#!/usr/bin/env bash
# ==============================================================
# Olist BI Orchestrator — EC2 Deployment Script (Ubuntu 22.04+)
# Nginx reverse-proxy → Gunicorn → Flask
# ==============================================================
# Usage:
#   1. Launch an Ubuntu EC2 instance (t3.small+ recommended)
#   2. Open ports 22, 80, 443 in the Security Group
#   3. SSH in and clone/upload this repo
#   4. Run:  chmod +x deploy.sh && sudo ./deploy.sh
# ==============================================================

set -euo pipefail

# ---------- configurable variables ----------------------------
APP_NAME="olist-bi"
APP_DIR="/opt/$APP_NAME"
APP_USER="olist"
REPO_SRC="$(cd "$(dirname "$0")" && pwd)"   # directory where this script lives
PYTHON_VERSION="python3"
VENV_DIR="$APP_DIR/venv"
GUNICORN_WORKERS=3
GUNICORN_TIMEOUT=120
APP_PORT=5000                                # internal Gunicorn port
DOMAIN="_"                                   # set your domain or leave _ for IP access
# --------------------------------------------------------------

echo "===== Olist BI — EC2 Deployment ====="

# --- Must run as root ---
if [[ $EUID -ne 0 ]]; then
  echo "Error: run this script with sudo" >&2
  exit 1
fi

# --- 1. System packages ---
echo "[1/7] Installing system packages..."
apt-get update -y
apt-get install -y \
  $PYTHON_VERSION ${PYTHON_VERSION}-venv ${PYTHON_VERSION}-dev \
  python3-pip nginx curl

# --- 2. Create app user ---
echo "[2/7] Creating application user..."
if ! id "$APP_USER" &>/dev/null; then
  useradd --system --create-home --shell /usr/sbin/nologin "$APP_USER"
fi

# --- 3. Copy application code ---
echo "[3/7] Deploying application to $APP_DIR..."
mkdir -p "$APP_DIR"
rsync -a --exclude='venv' --exclude='__pycache__' --exclude='.git' \
  "$REPO_SRC/" "$APP_DIR/"

# --- 4. Python virtual environment & dependencies ---
echo "[4/7] Setting up Python environment..."
$PYTHON_VERSION -m venv "$VENV_DIR"
"$VENV_DIR/bin/pip" install --upgrade pip
"$VENV_DIR/bin/pip" install -r "$APP_DIR/requirements.txt"

# --- 5. Initialize SQLite database from CSVs ---
echo "[5/7] Initializing database..."
cd "$APP_DIR"
"$VENV_DIR/bin/python" src/database.py

# Fix ownership
chown -R "$APP_USER:$APP_USER" "$APP_DIR"

# --- 6. Systemd service for Gunicorn ---
echo "[6/7] Configuring Gunicorn systemd service..."

cat > /etc/systemd/system/${APP_NAME}.service <<EOF
[Unit]
Description=Olist BI Orchestrator (Gunicorn)
After=network.target

[Service]
User=$APP_USER
Group=$APP_USER
WorkingDirectory=$APP_DIR
EnvironmentFile=$APP_DIR/.env
ExecStart=$VENV_DIR/bin/gunicorn \
    --workers $GUNICORN_WORKERS \
    --timeout $GUNICORN_TIMEOUT \
    --bind 127.0.0.1:$APP_PORT \
    --access-logfile /var/log/${APP_NAME}/access.log \
    --error-logfile  /var/log/${APP_NAME}/error.log \
    app:flask_app
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

mkdir -p /var/log/${APP_NAME}
chown -R "$APP_USER:$APP_USER" /var/log/${APP_NAME}

systemctl daemon-reload
systemctl enable ${APP_NAME}
systemctl restart ${APP_NAME}

# --- 7. Nginx reverse proxy ---
echo "[7/7] Configuring Nginx..."

cat > /etc/nginx/sites-available/${APP_NAME} <<EOF
server {
    listen 80;
    server_name $DOMAIN;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;

    # Max request body (matches Flask 1 MB limit)
    client_max_body_size 1M;

    location / {
        proxy_pass         http://127.0.0.1:$APP_PORT;
        proxy_set_header   Host              \$host;
        proxy_set_header   X-Real-IP         \$remote_addr;
        proxy_set_header   X-Forwarded-For   \$proxy_add_x_forwarded_for;
        proxy_set_header   X-Forwarded-Proto \$scheme;
        proxy_read_timeout 120s;
        proxy_connect_timeout 10s;
    }

    # Deny access to hidden files
    location ~ /\. {
        deny all;
    }
}
EOF

# Enable site, remove default
ln -sf /etc/nginx/sites-available/${APP_NAME} /etc/nginx/sites-enabled/${APP_NAME}
rm -f /etc/nginx/sites-enabled/default

nginx -t          # validate config
systemctl enable nginx
systemctl restart nginx

# --- Done ---
PUBLIC_IP=$(curl -s --max-time 5 http://169.254.169.254/latest/meta-data/public-ipv4 2>/dev/null || echo "<your-ec2-public-ip>")
echo ""
echo "======================================"
echo " Deployment complete!"
echo " App URL:  http://$PUBLIC_IP"
echo " Logs:     /var/log/$APP_NAME/"
echo " Service:  systemctl status $APP_NAME"
echo "======================================"
echo ""
echo "REMINDER: Make sure $APP_DIR/.env exists with at least:"
echo "  GROQ_API_KEY=<your-key>"
echo ""
