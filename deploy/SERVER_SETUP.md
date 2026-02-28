# Teamflow Server Setup (Ubuntu 22.04)

Production deployment on a fresh Ubuntu 22.04 server (e.g. Eskiz cloud). Use the automated script or follow the manual steps below.

---

## Quick start (automated)

1. SSH into the server:
   ```bash
   ssh username@server-ip
   ```

2. Edit configuration at the top of the script, then run:
   ```bash
   sudo bash setup_server.sh
   ```

3. Edit `/opt/teamflow/.env` with real secrets and `ALLOWED_HOSTS=yourdomain.uz`, then:
   ```bash
   cd /opt/teamflow && docker compose -f docker-compose.prod.yml up -d
   ```

---

## Step-by-step manual commands

### 1. System update and essential packages

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y curl git ufw certbot python3-certbot-nginx nginx
```

### 2. Docker installation

```bash
# Install Docker (official script)
curl -fsSL https://get.docker.com | sudo sh

# Docker Compose plugin (Ubuntu 22.04)
sudo apt install -y docker-compose-plugin

# Add your user to docker group
sudo usermod -aG docker $USER

# Enable and start Docker
sudo systemctl enable --now docker

# Log out and back in (or newgrp docker) for group to apply
```

### 3. UFW firewall

```bash
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw --force enable
sudo ufw status
```

### 4. Deployment directory

```bash
sudo mkdir -p /opt/teamflow
sudo chown -R $USER:$USER /opt/teamflow
```

### 5. Production .env file

```bash
sudo -u $USER cat > /opt/teamflow/.env << 'EOF'
SECRET_KEY=your-long-random-secret-key
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1,yourdomain.uz

DB_NAME=teamflow
DB_USER=teamflow_user
DB_PASSWORD=strong_password_here
DB_HOST=db
DB_PORT=5432

POSTGRES_DB=teamflow
POSTGRES_USER=teamflow_user
POSTGRES_PASSWORD=strong_password_here

SECURE_SSL_REDIRECT=True

DJANGO_SUPERUSER_USERNAME=admin
DJANGO_SUPERUSER_EMAIL=admin@yourdomain.uz
DJANGO_SUPERUSER_PASSWORD=admin
EOF
# Edit with your domain and secrets:
nano /opt/teamflow/.env
```

### 6. Clone repository

```bash
cd /opt/teamflow
git clone https://github.com/USERNAME/teamflow.git .
# Or to update later:
# git pull
```

### 7. Build image and Docker Compose (production: db + web only)

```bash
cd /opt/teamflow
docker build -t teamflow:prod .
docker compose -f docker-compose.prod.yml up -d
docker compose -f docker-compose.prod.yml exec web python manage.py collectstatic --noinput
```

### 8. Nginx and SSL with Certbot

```bash
# Create Nginx site (replace yourdomain.uz)
sudo tee /etc/nginx/sites-available/teamflow << 'EOF'
server {
    listen 80;
    server_name yourdomain.uz;
    client_max_body_size 10M;
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
        proxy_connect_timeout 120s;
        proxy_send_timeout 120s;
        proxy_read_timeout 120s;
    }
}
EOF

sudo ln -sf /etc/nginx/sites-available/teamflow /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t && sudo systemctl reload nginx

# SSL certificate
sudo certbot --nginx -d yourdomain.uz --non-interactive --agree-tos -m admin@yourdomain.uz

# Auto-renewal cron
(sudo crontab -l 2>/dev/null | grep -v certbot; echo "0 3 * * * certbot renew --quiet --post-hook 'systemctl reload nginx'") | sudo crontab -
```

### 9. Nginx HTTPS hardening (HSTS, strong ciphers)

```bash
sudo mkdir -p /etc/nginx/snippets
sudo tee /etc/nginx/snippets/ssl-params.conf << 'EOF'
ssl_protocols TLSv1.2 TLSv1.3;
ssl_prefer_server_ciphers on;
ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384;
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
EOF

# Add inside the server { listen 443 ssl; ... } block in /etc/nginx/sites-available/teamflow:
#   include snippets/ssl-params.conf;
sudo nano /etc/nginx/sites-available/teamflow

sudo nginx -t && sudo systemctl reload nginx
```

### 10. Health check

```bash
curl -f https://yourdomain.uz || echo "Deployment failed"
```

---

## SSH into the server

```bash
ssh username@server-ip
```

Example: `ssh ubuntu@10.205.235.31`

---

## Check logs

```bash
cd /opt/teamflow
docker compose -f docker-compose.prod.yml logs -f
# Or per service:
docker compose -f docker-compose.prod.yml logs -f web
docker compose -f docker-compose.prod.yml logs -f db
```

---

## Restart services

```bash
cd /opt/teamflow
docker compose -f docker-compose.prod.yml restart

# Restart only web
docker compose -f docker-compose.prod.yml restart web

# Restart Nginx (host)
sudo systemctl restart nginx
```

---

## Useful commands

| Task | Command |
|------|---------|
| Pull latest code and rebuild | `cd /opt/teamflow && git pull && docker build -t teamflow:prod . && docker compose -f docker-compose.prod.yml up -d` |
| Run migrations | `docker compose -f docker-compose.prod.yml exec web python manage.py migrate` |
| Collect static | `docker compose -f docker-compose.prod.yml exec web python manage.py collectstatic --noinput` |
| Django shell | `docker compose -f docker-compose.prod.yml exec web python manage.py shell` |
| Create superuser | Set `DJANGO_SUPERUSER_*` in `.env` and restart: `docker compose -f docker-compose.prod.yml up -d` |
