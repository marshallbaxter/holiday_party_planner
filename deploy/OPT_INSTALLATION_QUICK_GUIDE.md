# Quick Guide: Installing in /opt

## Overview

This is a condensed guide for installing Holiday Party Planner in `/opt/holiday-party-planner` alongside your existing Flask project.

## Prerequisites

- ✅ Existing Flask project already running in `/opt`
- ✅ Ubuntu 22.04 or 24.04 LTS
- ✅ Python 3.11 already installed
- ✅ Nginx already installed and configured
- ✅ Domain name ready

## Quick Installation Steps

### 1. Create User (Optional - or use existing user)

```bash
# Option A: Create new dedicated user
sudo useradd -r -s /bin/bash -d /opt/holiday-party-planner holiday-party
sudo usermod -aG www-data holiday-party

# Option B: Use your existing user (skip user creation)
EXISTING_USER="your-existing-user"
```

### 2. Create Directory and Clone

```bash
# Create directory
sudo mkdir -p /opt/holiday-party-planner

# Set ownership (choose one):
sudo chown -R holiday-party:holiday-party /opt/holiday-party-planner
# OR
sudo chown -R $EXISTING_USER:$EXISTING_USER /opt/holiday-party-planner

# Clone repository (as the appropriate user)
sudo -u holiday-party git clone YOUR_GITHUB_REPO_URL /opt/holiday-party-planner
# OR
sudo -u $EXISTING_USER git clone YOUR_GITHUB_REPO_URL /opt/holiday-party-planner
```

### 3. Set Up Virtual Environment

```bash
# Switch to application user
sudo -u holiday-party -i
# OR
sudo -u $EXISTING_USER -i

cd /opt/holiday-party-planner
python3.11 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Create directories
mkdir -p logs backups instance
chmod +x deploy/*.sh
```

### 4. Configure Environment

```bash
# Copy and edit .env
cp .env.example .env
python3 -c "import secrets; print(secrets.token_hex(32))"  
# Generate SECRET_KEY
nano .env
```

**Minimal .env configuration:**
```bash
FLASK_APP=run.py
FLASK_ENV=production
SECRET_KEY=YOUR_GENERATED_SECRET_KEY
DATABASE_URL=sqlite:///instance/holiday_party.db
BREVO_API_KEY=YOUR_BREVO_API_KEY
BREVO_SENDER_EMAIL=YOUR_SENDER_EMAIL
APP_URL=https://YOUR_DOMAIN_COM
```

```bash
chmod 600 .env
```

### 5. Initialize Database

```bash
# Still as application user
export FLASK_APP=run.py
flask db upgrade
exit  # Back to sudo user
```

### 6. Configure Systemd Service

```bash
# Copy and edit service file
sudo cp /opt/holiday-party-planner/deploy/holiday-party.service /etc/systemd/system/
sudo nano /etc/systemd/system/holiday-party.service
```

**Key changes to make:**
- Change `User=` and `Group=` to your user
- Change all paths from `/home/holiday-party/app` to `/opt/holiday-party-planner`
- Verify socket path: `/run/holiday-party/holiday-party.sock`

```bash
# Enable and start
sudo systemctl daemon-reload
sudo systemctl enable holiday-party
sudo systemctl start holiday-party
sudo systemctl status holiday-party
```

### 7. Configure Nginx

```bash
sudo nano /etc/nginx/sites-available/holiday-party
```

**Minimal HTTP config (for Cloudflare Tunnel):**
```nginx
server {
    listen 80;
    server_name YOUR_DOMAIN_COM;
    
    location /static {
        alias /opt/holiday-party-planner/app/static;
        expires 30d;
    }
    
    location / {
        proxy_pass http://unix:/run/holiday-party/holiday-party.sock;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto https;
    }
}
```

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/holiday-party /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 8. Set Up SSL (Choose One)

**Option A: Cloudflare Tunnel**
```bash
# Follow: deploy/CLOUDFLARE_TUNNEL_GUIDE.md
# No additional steps needed for SSL
```

**Option B: Let's Encrypt**
```bash
sudo certbot --nginx -d YOUR_DOMAIN_COM
```

### 9. Create Admin Account

```bash
sudo -u holiday-party -i
cd /opt/holiday-party-planner
source venv/bin/activate
flask create-admin
exit
```

### 10. Set Up Backups

```bash
sudo -u holiday-party crontab -e
```

Add:
```
0 2 * * * /opt/holiday-party-planner/deploy/backup-database.sh >> /opt/holiday-party-planner/logs/backup.log 2>&1
```

## Path Reference

### Replace These Paths

When following the main deployment guide, replace:

| Main Guide Path | Your Path |
|----------------|-----------|
| `/home/holiday-party/app` | `/opt/holiday-party-planner` |
| `/home/holiday-party/app/venv` | `/opt/holiday-party-planner/venv` |
| `/home/holiday-party/app/logs` | `/opt/holiday-party-planner/logs` |
| `/home/holiday-party/app/backups` | `/opt/holiday-party-planner/backups` |
| `/home/holiday-party/app/instance` | `/opt/holiday-party-planner/instance` |

### Important Files

```
/opt/holiday-party-planner/
├── .env                          # Configuration
├── venv/                         # Virtual environment
├── logs/                         # Application logs
├── backups/                      # Database backups
├── instance/holiday_party.db     # SQLite database
└── deploy/                       # Deployment scripts

/etc/systemd/system/holiday-party.service    # Service config
/etc/nginx/sites-available/holiday-party     # Nginx config
/var/log/nginx/holiday-party-*.log           # Nginx logs
```

## Verification Checklist

```bash
# 1. Check service is running
sudo systemctl status holiday-party

# 2. Check socket exists
ls -la /run/holiday-party/holiday-party.sock

# 3. Check Nginx config
sudo nginx -t

# 4. Check database
ls -lh /opt/holiday-party-planner/instance/holiday_party.db

# 5. Test application
curl --unix-socket /run/holiday-party/holiday-party.sock http://localhost/api/health

# 6. Test via domain
curl https://YOUR_DOMAIN_COM
```

## Common Commands

```bash
# Service management
sudo systemctl status holiday-party
sudo systemctl restart holiday-party
sudo journalctl -u holiday-party -f

# Deploy updates
cd /opt/holiday-party-planner
sudo -u holiday-party ./deploy/deploy.sh

# Database backup
sudo -u holiday-party /opt/holiday-party-planner/deploy/backup-database.sh

# Create admin
sudo -u holiday-party bash -c 'cd /opt/holiday-party-planner && source venv/bin/activate && flask create-admin'
```

## Troubleshooting

### Service won't start
```bash
sudo journalctl -u holiday-party -n 50
# Check paths in service file
# Check .env file exists and is readable
# Check virtual environment exists
```

### Permission errors
```bash
sudo chown -R holiday-party:holiday-party /opt/holiday-party-planner
sudo chmod 600 /opt/holiday-party-planner/.env
```

### Nginx 502 error
```bash
# Check if service is running
sudo systemctl status holiday-party

# Check socket exists
ls -la /run/holiday-party/

# Check Nginx logs
sudo tail -50 /var/log/nginx/holiday-party-error.log
```

## Deployment Script Configuration

Update `/opt/holiday-party-planner/deploy/deploy.sh`:

```bash
APP_DIR="/opt/holiday-party-planner"
VENV_DIR="$APP_DIR/venv"
BACKUP_DIR="$APP_DIR/backups"
SERVICE_NAME="holiday-party"
```

## Summary

✅ **Installation Location:** `/opt/holiday-party-planner`
✅ **Service Name:** `holiday-party`
✅ **Socket:** `/run/holiday-party/holiday-party.sock`
✅ **Database:** `/opt/holiday-party-planner/instance/holiday_party.db`
✅ **Logs:** `/opt/holiday-party-planner/logs/`
✅ **Backups:** `/opt/holiday-party-planner/backups/`

**Your existing project in /opt is completely unaffected!**

---

For detailed information, see:
- `deploy/MULTI_PROJECT_DEPLOYMENT.md` - Complete multi-project guide
- `deploy/UBUNTU_DEPLOYMENT_GUIDE.md` - Main deployment guide
- `deploy/CLOUDFLARE_TUNNEL_GUIDE.md` - Cloudflare Tunnel setup

