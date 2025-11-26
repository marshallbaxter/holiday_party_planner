# Multi-Project Deployment Guide

## Overview

You can easily run multiple Flask applications on the same Ubuntu server. This guide shows you how to install Holiday Party Planner alongside your existing Flask project.

## Architecture

```
Server
├── /opt/existing-project/          # Your existing Flask app
│   ├── venv/
│   ├── app.py
│   └── ...
│
├── /opt/holiday-party-planner/     # New Holiday Party Planner
│   ├── venv/
│   ├── run.py
│   └── ...
│
├── Systemd Services
│   ├── existing-project.service    # Your existing service
│   └── holiday-party.service       # New service
│
└── Nginx
    ├── existing-project (config)   # Your existing site
    └── holiday-party (config)      # New site
```

## Key Principles

1. **Separate Directories** - Each project in its own directory
2. **Separate Virtual Environments** - Each project has its own venv
3. **Separate Systemd Services** - Each project runs independently
4. **Separate Nginx Configs** - Each project has its own site config
5. **Separate Domains/Subdomains** - Each project on different domain

## Installation Options

### Option 1: Install in /opt (Recommended for Multi-Project)

**Advantages:**
- ✅ Standard location for optional software
- ✅ Keeps all projects together
- ✅ Easy to manage multiple projects
- ✅ Clear separation from system files

**Directory Structure:**
```
/opt/
├── existing-project/
└── holiday-party-planner/
```

### Option 2: Install in /home (Original Guide)

**Advantages:**
- ✅ Easier permissions management
- ✅ User-specific isolation
- ✅ Follows original guide

**Directory Structure:**
```
/home/
├── existing-user/existing-project/
└── holiday-party/app/
```

## Step-by-Step: Installing in /opt

### Step 1: Create Application User (Optional)

You can either:
- **Option A:** Use the same user as your existing project
- **Option B:** Create a new dedicated user (recommended for isolation)

**Option B - Create New User:**
```bash
# Create dedicated user
sudo useradd -r -s /bin/bash -d /opt/holiday-party-planner holiday-party

# Add to www-data group
sudo usermod -aG www-data holiday-party
```

**Option A - Use Existing User:**
```bash
# Just note your existing user (e.g., "webapps" or "deploy")
EXISTING_USER="your-existing-user"
```

### Step 2: Create Project Directory

```bash
# Create directory in /opt
sudo mkdir -p /opt/holiday-party-planner

# Set ownership (choose one):
# Option A - New dedicated user:
sudo chown -R holiday-party:holiday-party /opt/holiday-party-planner

# Option B - Existing user:
sudo chown -R $EXISTING_USER:$EXISTING_USER /opt/holiday-party-planner
```

### Step 3: Clone Repository

```bash
# Switch to the appropriate user
# Option A - New user:
sudo -u holiday-party -i

# Option B - Existing user:
sudo -u $EXISTING_USER -i

# Clone repository
cd /opt/holiday-party-planner
git clone YOUR_GITHUB_REPO_URL .

# Note the dot (.) at the end - clones into current directory
```

### Step 4: Create Virtual Environment

```bash
# Still as the application user
cd /opt/holiday-party-planner

# Create virtual environment
python3.11 -m venv venv

# Activate
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt
```

### Step 5: Create Required Directories

```bash
# Still in /opt/holiday-party-planner
mkdir -p logs backups instance

# Make scripts executable
chmod +x deploy/*.sh
```

### Step 6: Configure Environment

```bash
# Copy example env file
cp .env.example .env

# Generate SECRET_KEY
python3 -c "import secrets; print(secrets.token_hex(32))"

# Edit .env file
nano .env
```

**Update these values:**
```bash
FLASK_APP=run.py
FLASK_ENV=production
SECRET_KEY=YOUR_GENERATED_SECRET_KEY

# Database (SQLite)
DATABASE_URL=sqlite:///instance/holiday_party.db

# Brevo credentials
BREVO_API_KEY=YOUR_BREVO_API_KEY
BREVO_SENDER_EMAIL=YOUR_SENDER_EMAIL
BREVO_SENDER_NAME=Holiday Party Planner

# Application settings
APP_NAME=Family Holiday Party Planner
APP_URL=https://YOUR_DOMAIN_COM
SUPPORT_EMAIL=support@YOUR_DOMAIN_COM

# Email settings
MAIL_SERVER=smtp-relay.brevo.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=YOUR_BREVO_USERNAME
MAIL_PASSWORD=YOUR_BREVO_PASSWORD

# Feature flags
SCHEDULER_ENABLED=True
REMINDER_CHECK_HOUR=9
ENABLE_SMS=False
ENABLE_MESSAGE_WALL=True
ENABLE_POTLUCK=True

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/app.log
```

**Secure the file:**
```bash
chmod 600 .env
```

### Step 7: Initialize Database

```bash
# Make sure venv is activated
source venv/bin/activate

# Run migrations
export FLASK_APP=run.py
flask db upgrade

# Exit back to your sudo user
exit
```

### Step 8: Configure Systemd Service

**Edit the service file to use /opt paths:**

```bash
# Copy the service file
sudo cp /opt/holiday-party-planner/deploy/holiday-party.service /etc/systemd/system/

# Edit it
sudo nano /etc/systemd/system/holiday-party.service
```

**Update these lines:**

```ini
[Unit]
Description=Holiday Party Planner Flask Application
After=network.target

[Service]
Type=notify

# Update user (choose one):
# Option A - New dedicated user:
User=holiday-party
Group=holiday-party

# Option B - Existing user:
# User=your-existing-user
# Group=your-existing-user

# Update all paths to /opt
WorkingDirectory=/opt/holiday-party-planner
Environment="PATH=/opt/holiday-party-planner/venv/bin"
Environment="FLASK_ENV=production"
EnvironmentFile=/opt/holiday-party-planner/.env

# Update socket path to avoid conflicts
ExecStart=/opt/holiday-party-planner/venv/bin/gunicorn \
    --workers 4 \
    --worker-class sync \
    --bind unix:/run/holiday-party/holiday-party.sock \
    --timeout 120 \
    --graceful-timeout 30 \
    --keep-alive 5 \
    --max-requests 1000 \
    --max-requests-jitter 50 \
    --access-logfile /opt/holiday-party-planner/logs/access.log \
    --error-logfile /opt/holiday-party-planner/logs/error.log \
    --log-level info \
    --capture-output \
    "run:app"

ExecReload=/bin/kill -s HUP $MAINPID
KillMode=mixed
KillSignal=SIGTERM
TimeoutStopSec=30
Restart=always
RestartSec=10

# Security settings
PrivateTmp=true
NoNewPrivileges=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/opt/holiday-party-planner/logs /opt/holiday-party-planner/instance /opt/holiday-party-planner/backups
RuntimeDirectory=holiday-party
RuntimeDirectoryMode=0755

# Resource limits
LimitNOFILE=65536
LimitNPROC=512

[Install]
WantedBy=multi-user.target
```

**Save and enable:**
```bash
sudo systemctl daemon-reload
sudo systemctl enable holiday-party
sudo systemctl start holiday-party
sudo systemctl status holiday-party
```

### Step 9: Configure Nginx

**Create a new Nginx site configuration:**

```bash
sudo nano /etc/nginx/sites-available/holiday-party
```

**For Cloudflare Tunnel (HTTP only):**

```nginx
server {
    listen 80;
    server_name YOUR_DOMAIN_COM;
    
    access_log /var/log/nginx/holiday-party-access.log;
    error_log /var/log/nginx/holiday-party-error.log;
    
    client_max_body_size 10M;
    
    location /static {
        alias /opt/holiday-party-planner/app/static;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
    
    location / {
        proxy_pass http://unix:/run/holiday-party/holiday-party.sock;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto https;
        proxy_redirect off;
    }
}
```

**For Let's Encrypt (HTTPS):**

```nginx
server {
    listen 80;
    server_name YOUR_DOMAIN_COM;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name YOUR_DOMAIN_COM;
    
    # SSL will be configured by certbot
    
    access_log /var/log/nginx/holiday-party-access.log;
    error_log /var/log/nginx/holiday-party-error.log;
    
    client_max_body_size 10M;
    
    location /static {
        alias /opt/holiday-party-planner/app/static;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
    
    location / {
        proxy_pass http://unix:/run/holiday-party/holiday-party.sock;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
    }
}
```

**Enable the site:**
```bash
sudo ln -s /etc/nginx/sites-available/holiday-party /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### Step 10: Set Up SSL (if using Let's Encrypt)

```bash
# Skip if using Cloudflare Tunnel
sudo certbot --nginx -d YOUR_DOMAIN_COM
```

### Step 11: Create Admin Account

```bash
# Switch to application user
sudo -u holiday-party -i  # or your existing user

cd /opt/holiday-party-planner
source venv/bin/activate
flask create-admin

# Follow prompts to create admin account
exit
```

### Step 12: Set Up Automated Backups

```bash
# Edit crontab for application user
sudo -u holiday-party crontab -e  # or your existing user

# Add backup job
0 2 * * * /opt/holiday-party-planner/deploy/backup-database.sh >> /opt/holiday-party-planner/logs/backup.log 2>&1
```

## Verification

### Check Both Services

```bash
# Check your existing service
sudo systemctl status your-existing-service

# Check Holiday Party Planner
sudo systemctl status holiday-party

# Both should show "active (running)"
```

### Check Nginx Configurations

```bash
# List all enabled sites
ls -la /etc/nginx/sites-enabled/

# Should show both configurations
```

### Test Both Applications

```bash
# Test existing app
curl http://localhost:PORT_OF_EXISTING_APP

# Test Holiday Party Planner
curl --unix-socket /run/holiday-party/holiday-party.sock http://localhost/api/health
```

## Resource Management

### Monitor Resource Usage

```bash
# Check memory usage
free -h

# Check CPU usage
top

# Check disk usage
df -h

# Check per-service resource usage
systemctl status holiday-party
systemctl status your-existing-service
```

### Adjust Resources if Needed

**If memory is tight, reduce Gunicorn workers:**

```bash
sudo nano /etc/systemd/system/holiday-party.service

# Change --workers 4 to --workers 2
# Restart service
sudo systemctl daemon-reload
sudo systemctl restart holiday-party
```

## Common Configurations

### Different Domains

**Best practice - each app on its own domain:**
```
existing-app.com → /opt/existing-project
party.example.com → /opt/holiday-party-planner
```

### Subdomains

**Alternative - use subdomains:**
```
www.example.com → /opt/existing-project
party.example.com → /opt/holiday-party-planner
```

### Different Ports (Not Recommended)

**Avoid this - use domains/subdomains instead:**
```
example.com:5000 → existing project
example.com:5001 → holiday party planner
```

## Troubleshooting

### Port Conflicts

If you see "Address already in use" errors:

```bash
# Check what's using ports
sudo netstat -tulpn | grep :80
sudo netstat -tulpn | grep :443

# Each app should use a different socket file
ls -la /run/*/
```

### Permission Issues

```bash
# Fix ownership
sudo chown -R holiday-party:holiday-party /opt/holiday-party-planner

# Fix .env permissions
sudo chmod 600 /opt/holiday-party-planner/.env
```

### Service Won't Start

```bash
# Check logs
sudo journalctl -u holiday-party -n 50

# Common issues:
# - Wrong paths in service file
# - Wrong user/group
# - Virtual environment not found
# - Database file permissions
```

## Deployment Script Updates

Update the deployment script paths:

```bash
sudo -u holiday-party nano /opt/holiday-party-planner/deploy/deploy.sh
```

**Change these variables:**
```bash
APP_DIR="/opt/holiday-party-planner"
VENV_DIR="$APP_DIR/venv"
BACKUP_DIR="$APP_DIR/backups"
SERVICE_NAME="holiday-party"
```

## Summary

✅ **Multiple Flask apps can coexist peacefully**
✅ **Each app has its own:**
   - Directory
   - Virtual environment
   - Systemd service
   - Nginx configuration
   - Domain/subdomain
   - Database
   - Logs

✅ **They share:**
   - Python installation
   - Nginx (web server)
   - System resources
   - Firewall rules

**Your existing project won't be affected at all!**

## Quick Reference

### File Locations

```
Existing Project:
  /opt/existing-project/
  /etc/systemd/system/existing-project.service
  /etc/nginx/sites-available/existing-project

Holiday Party Planner:
  /opt/holiday-party-planner/
  /etc/systemd/system/holiday-party.service
  /etc/nginx/sites-available/holiday-party
```

### Common Commands

```bash
# Manage Holiday Party Planner
sudo systemctl status holiday-party
sudo systemctl restart holiday-party
sudo journalctl -u holiday-party -f

# Deploy updates
cd /opt/holiday-party-planner
sudo -u holiday-party ./deploy/deploy.sh

# Backup database
sudo -u holiday-party /opt/holiday-party-planner/deploy/backup-database.sh
```

---

**You're all set to run multiple Flask applications on the same server!** 🎉

