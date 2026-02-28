#!/bin/bash
#
# Production server setup for Teamflow (Ubuntu 22.04)
# Run as: sudo bash setup_server.sh
# Configure variables below before running.
#
set -e

# === CONFIGURATION (edit before run) ===
GITHUB_REPO="${GITHUB_REPO:-https://github.com/USERNAME/teamflow.git}"
DEPLOY_DIR="${DEPLOY_DIR:-/opt/teamflow}"
DOMAIN="${DOMAIN:-yourdomain.uz}"
CERTBOT_EMAIL="${CERTBOT_EMAIL:-admin@yourdomain.uz}"
CURRENT_USER="${SUDO_USER:-$USER}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_step() { echo -e "${BLUE}[*]${NC} $1"; }
log_ok()   { echo -e "${GREEN}[OK]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[!]${NC} $1"; }
log_err()  { echo -e "${RED}[ERR]${NC} $1"; }

[[ "$EUID" -eq 0 ]] || { log_err "Run as root (sudo)"; exit 1; }

# ---------------------------------------------------------------------------
# 1. System update and essential packages
# ---------------------------------------------------------------------------
log_step "System update and essential packages..."
apt-get update -qq && apt-get upgrade -y -qq
apt-get install -y -qq curl git ufw certbot python3-certbot-nginx nginx
log_ok "Packages installed"

# ---------------------------------------------------------------------------
# 2. Docker installation
# ---------------------------------------------------------------------------
log_step "Installing Docker..."
if command -v docker &>/dev/null; then
  log_warn "Docker already installed"
else
  curl -fsSL https://get.docker.com | sh
  log_ok "Docker installed"
fi

log_step "Installing Docker Compose plugin..."
apt-get install -y -qq docker-compose-plugin 2>/dev/null || {
  mkdir -p /usr/local/lib/docker/cli-plugins
  curl -sSL "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/lib/docker/cli-plugins/docker-compose
  chmod +x /usr/local/lib/docker/cli-plugins/docker-compose
}
log_ok "Docker Compose plugin ready"

log_step "Adding user to docker group and enabling service..."
usermod -aG docker "$CURRENT_USER" 2>/dev/null || true
systemctl enable --now docker
log_ok "Docker enabled and started"

# ---------------------------------------------------------------------------
# 3. UFW Firewall
# ---------------------------------------------------------------------------
log_step "Configuring UFW..."
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable
log_ok "UFW enabled (22, 80, 443 allowed)"

# ---------------------------------------------------------------------------
# 4. Deployment directory
# ---------------------------------------------------------------------------
log_step "Creating deployment directory..."
mkdir -p "$DEPLOY_DIR"
chown -R "$CURRENT_USER:$CURRENT_USER" "$DEPLOY_DIR"
log_ok "Directory $DEPLOY_DIR ready"

# ---------------------------------------------------------------------------
# 5. Production .env template
# ---------------------------------------------------------------------------
log_step "Creating .env template..."
cat > "$DEPLOY_DIR/.env" << 'ENVEOF'
# Django
SECRET_KEY=change-me-to-a-long-random-secret-key
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1,yourdomain.uz

# Database (DB_HOST=db for docker compose)
DB_NAME=teamflow
DB_USER=teamflow_user
DB_PASSWORD=your_db_password_here
DB_HOST=db
DB_PORT=5432

POSTGRES_DB=teamflow
POSTGRES_USER=teamflow_user
POSTGRES_PASSWORD=your_db_password_here

SECURE_SSL_REDIRECT=True

DJANGO_SUPERUSER_USERNAME=admin
DJANGO_SUPERUSER_EMAIL=admin@example.com
DJANGO_SUPERUSER_PASSWORD=admin
ENVEOF
sed -i "s/yourdomain.uz/$DOMAIN/g" "$DEPLOY_DIR/.env"
chown "$CURRENT_USER:$CURRENT_USER" "$DEPLOY_DIR/.env"
log_ok ".env template created at $DEPLOY_DIR/.env (edit before first deploy)"

# ---------------------------------------------------------------------------
# 6. Clone or pull code
# ---------------------------------------------------------------------------
log_step "Cloning repository..."
if [[ -d "$DEPLOY_DIR/.git" ]]; then
  (cd "$DEPLOY_DIR" && git pull) || true
else
  git clone "$GITHUB_REPO" "$DEPLOY_DIR" || { log_err "Clone failed. Create $DEPLOY_DIR and clone manually."; exit 1; }
fi
chown -R "$CURRENT_USER:$CURRENT_USER" "$DEPLOY_DIR"
log_ok "Code updated"

# ---------------------------------------------------------------------------
# 7. Docker Compose deployment (use prod compose: db + web, no nginx container)
# ---------------------------------------------------------------------------
log_step "Building image and starting containers..."
cd "$DEPLOY_DIR"
docker build -t teamflow:prod . 2>/dev/null || log_warn "Build skipped (use pre-built image)"
if [[ -f docker-compose.prod.yml ]]; then
  docker compose -f docker-compose.prod.yml pull
  docker compose -f docker-compose.prod.yml up -d
  sleep 8
  docker compose -f docker-compose.prod.yml exec -T web python manage.py collectstatic --noinput 2>/dev/null || true
else
  docker compose pull
  docker compose up -d
  sleep 8
  docker compose exec -T web python manage.py collectstatic --noinput 2>/dev/null || true
fi
log_ok "Containers running"

# ---------------------------------------------------------------------------
# 8. Nginx site config (proxy to Docker web) and SSL with Certbot
# ---------------------------------------------------------------------------
log_step "Configuring Nginx for $DOMAIN..."
cat > /etc/nginx/sites-available/teamflow << NGINXEOF
server {
    listen 80;
    server_name $DOMAIN;
    client_max_body_size 10M;
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_redirect off;
        proxy_connect_timeout 120s;
        proxy_send_timeout 120s;
        proxy_read_timeout 120s;
    }
}
NGINXEOF
ln -sf /etc/nginx/sites-available/teamflow /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl reload nginx
log_ok "Nginx configured (HTTP)"

log_step "Obtaining SSL certificate..."
certbot --nginx -d "$DOMAIN" --non-interactive --agree-tos -m "$CERTBOT_EMAIL" || log_warn "Certbot failed (run manually)"
log_ok "SSL certificate done"

log_step "Adding certbot renewal cron..."
(crontab -l 2>/dev/null | grep -v certbot; echo "0 3 * * * certbot renew --quiet --post-hook 'systemctl reload nginx'") | crontab -
log_ok "Auto-renewal cron installed"

# ---------------------------------------------------------------------------
# 9. Nginx HTTPS hardening (HSTS, strong ciphers)
# ---------------------------------------------------------------------------
log_step "Adding SSL snippet (HSTS, ciphers)..."
mkdir -p /etc/nginx/snippets
cat > /etc/nginx/snippets/ssl-params.conf << 'SSLEOF'
ssl_protocols TLSv1.2 TLSv1.3;
ssl_prefer_server_ciphers on;
ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384;
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
SSLEOF
# Insert include into the 443 server block (certbot may create teamflow or .le-ssl.conf)
for f in /etc/nginx/sites-available/teamflow /etc/nginx/sites-available/teamflow.le-ssl.conf /etc/nginx/sites-available/default; do
  if [[ -f "$f" ]] && grep -q "listen 443 ssl" "$f" && ! grep -q "ssl-params.conf" "$f"; then
    sed -i '/listen 443 ssl;/a \    include snippets/ssl-params.conf;' "$f"
    break
  fi
done
nginx -t && systemctl reload nginx
log_ok "HTTPS hardening applied"

# ---------------------------------------------------------------------------
# 10. Health check
# ---------------------------------------------------------------------------
log_step "Health check..."
if curl -fsS --max-time 10 "https://$DOMAIN" > /dev/null 2>&1; then
  log_ok "Deployment OK: https://$DOMAIN"
else
  log_warn "Health check failed: curl https://$DOMAIN (check logs)"
fi

echo ""
echo -e "${GREEN}Setup complete.${NC} Edit $DEPLOY_DIR/.env then run: docker compose -f docker-compose.prod.yml up -d"
echo "Log in to the server: ssh $CURRENT_USER@<server-ip>"
