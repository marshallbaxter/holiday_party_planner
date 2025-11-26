# Holiday Party Planner - Complete Ubuntu Deployment Guide

**Target Platform:** Ubuntu 22.04 LTS or Ubuntu 24.04 LTS
**Estimated Total Time:** 2-3 hours for initial deployment
**Skill Level:** Basic Linux command-line knowledge required
**Database:** SQLite (simple, file-based - perfect for getting started)

> **Note:** This guide uses SQLite for simplicity. SQLite is perfect for small to medium deployments (up to ~100 concurrent users). If you need to scale beyond that, see [Appendix A: Migrating to PostgreSQL](#appendix-a-migrating-from-sqlite-to-postgresql).

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Phase 1: Pre-Deployment Preparation](#phase-1-pre-deployment-preparation-30-minutes)
3. [Phase 2: Server Initial Setup](#phase-2-server-initial-setup-45-minutes)
4. [Phase 3: Application Installation](#phase-3-application-installation-30-minutes)
5. [Phase 4: Web Server & SSL Configuration](#phase-4-web-server--ssl-configuration-30-minutes)
6. [Phase 5: Application Configuration](#phase-5-application-configuration-15-minutes)
7. [Phase 6: First Admin Account](#phase-6-first-admin-account-5-minutes)
8. [Phase 7: Automated Backups](#phase-7-automated-backups-10-minutes)
9. [Phase 8: Final Verification](#phase-8-final-verification-15-minutes)
10. [Ongoing Deployments](#ongoing-deployments)
11. [Troubleshooting](#troubleshooting)
12. [Maintenance & Monitoring](#maintenance--monitoring)

---

## Prerequisites

### What You Need Before Starting

#### 1. Server Requirements
- [ ] Ubuntu 22.04 LTS or 24.04 LTS server (fresh installation)
- [ ] Minimum 2GB RAM (4GB recommended)
- [ ] Minimum 20GB disk space
- [ ] Root or sudo access
- [ ] SSH access configured

#### 2. Domain & DNS
- [ ] Domain name registered (e.g., `party.example.com`)
- [ ] DNS A record pointing to your server's IP address
- [ ] DNS propagation completed (check with `nslookup YOUR_DOMAIN_COM`)
- [ ] Wait 15-30 minutes after DNS changes before proceeding

#### 3. Email Service (Brevo)
- [ ] Brevo account created at https://app.brevo.com
- [ ] Sender email address verified in Brevo
- [ ] API key generated (Settings → API Keys)
- [ ] SMTP credentials obtained (Settings → SMTP & API)

#### 4. Development Environment
- [ ] Code pushed to GitHub repository
- [ ] Repository is accessible (public or you have SSH keys set up)
- [ ] All migrations committed to repository

#### 5. Information to Have Ready
- [ ] GitHub repository URL: `YOUR_GITHUB_REPO_URL`
- [ ] Domain name: `YOUR_DOMAIN_COM`
- [ ] Brevo API key: `YOUR_BREVO_API_KEY`
- [ ] Brevo sender email: `YOUR_SENDER_EMAIL`
- [ ] Brevo SMTP username: `YOUR_BREVO_USERNAME`
- [ ] Brevo SMTP password: `YOUR_BREVO_PASSWORD`

---

## Phase 1: Pre-Deployment Preparation (30 minutes)

### Step 1.1: Verify DNS Configuration

On your local machine, verify DNS is working:

```bash
# Check if your domain resolves to your server IP
nslookup YOUR_DOMAIN_COM

# Or use dig
dig YOUR_DOMAIN_COM +short
```

**Expected Result:** Should return your server's IP address.

⚠️ **IMPORTANT:** If DNS is not resolving correctly, STOP and fix DNS before proceeding. SSL certificate generation will fail without proper DNS.

### Step 1.2: Connect to Your Server

```bash
# SSH to your server
ssh root@YOUR_SERVER_IP

# Or if using a non-root user with sudo:
ssh your-username@YOUR_SERVER_IP
```

### Step 1.3: Update System Packages

```bash
# Update package lists
sudo apt update

# Upgrade all packages
sudo apt upgrade -y

# Reboot if kernel was updated (check if /var/run/reboot-required exists)
if [ -f /var/run/reboot-required ]; then
    echo "Reboot required. Rebooting in 10 seconds..."
    sleep 10
    sudo reboot
fi
```

**Time Required:** 10-15 minutes (depending on updates)

**Verification:**
```bash
# Check Ubuntu version
lsb_release -a

# Should show Ubuntu 22.04 or 24.04
```

### Step 1.4: Set Server Timezone (Optional but Recommended)

```bash
# List available timezones
timedatectl list-timezones | grep America  # or your region

# Set your timezone (example: US Eastern)
sudo timedatectl set-timezone America/New_York

# Verify
timedatectl
```

---

## Phase 2: Server Initial Setup (45 minutes)

### Step 2.1: Install System Dependencies

```bash
# Install Python 3.11 and development tools
sudo apt install -y \
    python3.11 \
    python3.11-venv \
    python3.11-dev \
    python3-pip \
    build-essential \
    git \
    curl \
    wget
```

**For Ubuntu 22.04:** Python 3.11 is available in the deadsnakes PPA:
```bash
# Only needed for Ubuntu 22.04
sudo apt install -y software-properties-common
sudo add-apt-repository -y ppa:deadsnakes/ppa
sudo apt update
sudo apt install -y python3.11 python3.11-venv python3.11-dev
```

**Verification:**
```bash
python3.11 --version
# Should show: Python 3.11.x
```

### Step 2.2: Install SQLite (Already Included)

SQLite comes pre-installed with Ubuntu, but let's verify:

```bash
# Check SQLite version
sqlite3 --version

# Should show SQLite 3.x.x
```

**Expected Output:** `3.37.2` or higher (version varies by Ubuntu release)

**Note:** SQLite is perfect for:
- Getting started quickly
- Small to medium deployments (up to ~100 concurrent users)
- Single-server setups
- Development and testing

**When to upgrade to PostgreSQL:**
- High traffic (100+ concurrent users)
- Multiple application servers
- Advanced database features needed
- See the PostgreSQL migration guide in the appendix

### Step 2.3: Install Nginx

```bash
# Install Nginx
sudo apt install -y nginx

# Start and enable Nginx
sudo systemctl start nginx
sudo systemctl enable nginx

# Verify Nginx is running
sudo systemctl status nginx
```

**Verification:**
```bash
# Check if Nginx is serving the default page
curl http://localhost

# Should return HTML content with "Welcome to nginx"
```

### Step 2.4: Install Certbot (for SSL)

```bash
# Install Certbot and Nginx plugin
sudo apt install -y certbot python3-certbot-nginx

# Verify installation
certbot --version
```

### Step 2.5: Install Security Tools

```bash
# Install UFW firewall
sudo apt install -y ufw

# Install Fail2ban
sudo apt install -y fail2ban

# Start and enable Fail2ban
sudo systemctl start fail2ban
sudo systemctl enable fail2ban
```

### Step 2.6: Create Application User

```bash
# Create a dedicated user for the application
sudo useradd -m -s /bin/bash holiday-party

# Add to www-data group (for Nginx integration)
sudo usermod -aG www-data holiday-party

# Verify user was created
id holiday-party
```

**Expected Output:** Should show uid, gid, and groups including www-data.

### Step 2.7: Configure Firewall

```bash
# Allow SSH (IMPORTANT: Do this first!)
sudo ufw allow OpenSSH

# Allow HTTP and HTTPS
sudo ufw allow 'Nginx Full'

# Enable firewall
sudo ufw --force enable

# Check firewall status
sudo ufw status
```

**Expected Output:**
```
Status: active

To                         Action      From
--                         ------      ----
OpenSSH                    ALLOW       Anywhere
Nginx Full                 ALLOW       Anywhere
OpenSSH (v6)               ALLOW       Anywhere (v6)
Nginx Full (v6)            ALLOW       Anywhere (v6)
```

⚠️ **IMPORTANT:** Make sure SSH is allowed before enabling the firewall, or you'll lock yourself out!

**Verification:**
```bash
# Test that you can still SSH (open a new terminal, don't close current one)
ssh your-username@YOUR_SERVER_IP
```

---

## Phase 3: Application Installation (30 minutes)

### Step 3.1: Clone Repository

```bash
# Switch to application user
sudo -u holiday-party -i

# You should now be in /home/holiday-party
pwd
# Should show: /home/holiday-party

# Clone your repository
# ⚠️ REPLACE YOUR_GITHUB_REPO_URL with your actual repository URL
git clone YOUR_GITHUB_REPO_URL app

# Navigate to app directory
cd app

# Verify files are present
ls -la
```

**Expected Output:** Should see your application files including `run.py`, `requirements.txt`, `deploy/` directory, etc.

**If using a private repository:**
```bash
# Option 1: Use HTTPS with personal access token
git clone https://YOUR_GITHUB_TOKEN@github.com/username/repo.git app

# Option 2: Set up SSH key (recommended)
ssh-keygen -t ed25519 -C "holiday-party@YOUR_DOMAIN_COM"
cat ~/.ssh/id_ed25519.pub
# Copy the output and add to GitHub: Settings → SSH Keys → New SSH key
# Then clone with SSH:
git clone git@github.com:username/repo.git app
```

### Step 3.2: Create Python Virtual Environment

```bash
# Make sure you're in the app directory as holiday-party user
cd /home/holiday-party/app

# Create virtual environment with Python 3.11
python3.11 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Verify Python version
python --version
# Should show: Python 3.11.x

# Upgrade pip
pip install --upgrade pip
```

**Verification:**
```bash
which python
# Should show: /home/holiday-party/app/venv/bin/python
```

### Step 3.3: Install Python Dependencies

```bash
# Make sure virtual environment is activated
# You should see (venv) in your prompt

# Install all dependencies
pip install -r requirements.txt

# This will take a few minutes
```

**Expected Output:** Should install all packages without errors. You may see some warnings, which are usually okay.

**If you encounter errors:**
```bash
# For PostgreSQL adapter issues:
sudo apt install -y libpq-dev python3.11-dev

# For other compilation issues:
sudo apt install -y build-essential

# Then retry:
pip install -r requirements.txt
```

### Step 3.4: Create Required Directories

```bash
# Still as holiday-party user in /home/holiday-party/app
mkdir -p logs
mkdir -p backups
mkdir -p instance

# Verify directories
ls -la
```

### Step 3.5: Make Scripts Executable

```bash
# Make deployment scripts executable
chmod +x deploy/deploy.sh
chmod +x deploy/backup-database.sh
chmod +x deploy/setup-server.sh
chmod +x deploy/make-executable.sh

# Verify
ls -la deploy/*.sh
```

### Step 3.6: Create Environment Configuration

```bash
# Copy the example environment file
cp .env.example .env

# Generate a secure SECRET_KEY
python3 -c "import secrets; print(secrets.token_hex(32))"
# Copy the output - you'll need it in the next step
```

Now edit the `.env` file:

```bash
nano .env
```

**Update these values in the file:**

```bash
# Flask Configuration
FLASK_APP=run.py
FLASK_ENV=production
SECRET_KEY=PASTE_THE_SECRET_KEY_YOU_GENERATED_HERE

# Database Configuration
# Using SQLite (file-based database)
DATABASE_URL=sqlite:///instance/holiday_party.db

# Brevo Email Configuration
# ⚠️ REPLACE with your actual Brevo credentials
BREVO_API_KEY=YOUR_BREVO_API_KEY
BREVO_SENDER_EMAIL=YOUR_SENDER_EMAIL
BREVO_SENDER_NAME=Holiday Party Planner

# Application Settings
# ⚠️ REPLACE with your actual domain
APP_NAME=Family Holiday Party Planner
APP_URL=https://YOUR_DOMAIN_COM
SUPPORT_EMAIL=support@YOUR_DOMAIN_COM

# Security & Authentication
TOKEN_EXPIRATION_DAYS=90
MAGIC_LINK_EXPIRATION_MINUTES=30
PASSWORD_RESET_EXPIRATION_MINUTES=60
AUTH_TOKEN_RATE_LIMIT=5

# Email Settings (Flask-Mail fallback)
MAIL_SERVER=smtp-relay.brevo.com
MAIL_PORT=587
MAIL_USE_TLS=True
# ⚠️ REPLACE with your actual Brevo SMTP credentials
MAIL_USERNAME=YOUR_BREVO_USERNAME
MAIL_PASSWORD=YOUR_BREVO_PASSWORD

# Background Jobs
SCHEDULER_ENABLED=True
REMINDER_CHECK_HOUR=9

# Feature Flags
ENABLE_SMS=False
ENABLE_MESSAGE_WALL=True
ENABLE_POTLUCK=True

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/app.log
```

**Save and exit:** Press `Ctrl+X`, then `Y`, then `Enter`

**Secure the .env file:**
```bash
chmod 600 .env
ls -la .env
# Should show: -rw------- (only owner can read/write)
```

### Step 3.7: Initialize Database

```bash
# Make sure virtual environment is activated and you're in /home/holiday-party/app
export FLASK_APP=run.py

# Run database migrations
flask db upgrade

# You should see migration messages
```

**Expected Output:**
```
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Will assume transactional DDL.
INFO  [alembic.runtime.migration] Running upgrade  -> xxxxx, Initial migration
```

**Verification:**
```bash
# Check database tables were created
sqlite3 instance/holiday_party.db ".tables"
# Should show a list of tables: persons, households, events, etc.

# Or check database file exists
ls -lh instance/holiday_party.db
# Should show the database file with size > 0
```

### Step 3.8: Test Application Locally

```bash
# Quick test to ensure app starts
python run.py &
APP_PID=$!

# Wait a moment
sleep 3

# Test if it's responding
curl http://localhost:5000/api/health

# Should return: {"status":"healthy","timestamp":"..."}

# Stop the test app
kill $APP_PID
```

**If the test fails:**
- Check logs: `tail -f logs/app.log`
- Verify database connection
- Check .env file for typos

### Step 3.9: Exit Application User Shell

```bash
# Exit back to your sudo user
exit

# You should now be back to your regular user prompt
```

---

## Phase 4: Web Server & SSL Configuration (30 minutes)

### Step 4.1: Configure Systemd Service

```bash
# Copy the service file
sudo cp /home/holiday-party/app/deploy/holiday-party.service /etc/systemd/system/

# Reload systemd to recognize the new service
sudo systemctl daemon-reload

# Enable the service to start on boot
sudo systemctl enable holiday-party

# Start the service
sudo systemctl start holiday-party

# Check service status
sudo systemctl status holiday-party
```

**Expected Output:** Should show "active (running)" in green.

**If the service fails to start:**
```bash
# Check detailed logs
sudo journalctl -u holiday-party -n 50 --no-pager

# Common issues:
# - Wrong paths in service file
# - .env file not readable
# - Database connection issues
```

**Verification:**
```bash
# Check if the socket file was created
ls -la /run/holiday-party/
# Should show: holiday-party.sock

# Test the socket
curl --unix-socket /run/holiday-party/holiday-party.sock http://localhost/api/health
# Should return: {"status":"healthy",...}
```

### Step 4.2: Configure Nginx

```bash
# Edit the nginx config to add your domain
sudo cp /home/holiday-party/app/deploy/nginx-config /etc/nginx/sites-available/holiday-party

# Edit the file to replace placeholders
sudo nano /etc/nginx/sites-available/holiday-party
```

**Find and replace these values:**
- `your-domain.com` → `YOUR_DOMAIN_COM` (your actual domain)
- `/home/holiday-party/app` → should already be correct

**Save and exit:** `Ctrl+X`, `Y`, `Enter`

```bash
# Remove default Nginx site
sudo rm /etc/nginx/sites-enabled/default

# Enable your site
sudo ln -s /etc/nginx/sites-available/holiday-party /etc/nginx/sites-enabled/

# Test Nginx configuration
sudo nginx -t
```

**Expected Output:**
```
nginx: the configuration file /etc/nginx/nginx.conf syntax is ok
nginx: configuration file /etc/nginx/nginx.conf test is successful
```

**If test fails:**
- Check for typos in the config file
- Ensure all paths are correct
- Look for the specific line number mentioned in the error

```bash
# Reload Nginx
sudo systemctl reload nginx

# Check Nginx status
sudo systemctl status nginx
```

**Verification:**
```bash
# Test HTTP access (should work now)
curl http://YOUR_DOMAIN_COM

# Should return HTML content (the homepage)
```

### Step 4.3: Obtain SSL Certificate

⚠️ **IMPORTANT:** Make sure your domain's DNS is pointing to this server before proceeding!

```bash
# Obtain SSL certificate from Let's Encrypt
# ⚠️ REPLACE YOUR_DOMAIN_COM with your actual domain
sudo certbot --nginx -d YOUR_DOMAIN_COM

# If you want www subdomain too:
# sudo certbot --nginx -d YOUR_DOMAIN_COM -d www.YOUR_DOMAIN_COM
```

**You'll be prompted for:**
1. Email address (for renewal notifications)
2. Agree to Terms of Service (yes)
3. Share email with EFF (optional)
4. Redirect HTTP to HTTPS (choose option 2: Redirect)

**Expected Output:**
```
Successfully received certificate.
Certificate is saved at: /etc/letsencrypt/live/YOUR_DOMAIN_COM/fullchain.pem
Key is saved at: /etc/letsencrypt/live/YOUR_DOMAIN_COM/privkey.pem
```

**Verification:**
```bash
# Test HTTPS access
curl https://YOUR_DOMAIN_COM

# Should return HTML content

# Check SSL certificate
sudo certbot certificates
```

### Step 4.4: Test Auto-Renewal

```bash
# Test certificate renewal (dry run)
sudo certbot renew --dry-run
```

**Expected Output:** Should say "Congratulations, all simulated renewals succeeded"

**Note:** Certbot automatically sets up a systemd timer for auto-renewal. Verify:
```bash
sudo systemctl status certbot.timer
# Should show: active (waiting)
```

---

## Phase 5: Application Configuration (15 minutes)

### Step 5.1: Update .env with Production Settings

```bash
# Edit .env as the application user
sudo -u holiday-party nano /home/holiday-party/app/.env
```

**Verify these settings are correct:**

1. **FLASK_ENV** should be `production`
2. **APP_URL** should be `https://YOUR_DOMAIN_COM` (with https://)
3. **All Brevo credentials** are filled in
4. **DATABASE_URL** has the correct password
5. **SECRET_KEY** is a long random string (not the default)

**Save and exit:** `Ctrl+X`, `Y`, `Enter`

### Step 5.2: Restart Application

```bash
# Restart the application to pick up any config changes
sudo systemctl restart holiday-party

# Wait a moment
sleep 3

# Check status
sudo systemctl status holiday-party
```

**Should show:** "active (running)" in green

### Step 5.3: Test Email Configuration

```bash
# Switch to application user
sudo -u holiday-party -i
cd app
source venv/bin/activate

# Test email sending with Python
python3 << 'EOF'
from app import create_app
from app.services.notification_service import NotificationService

app = create_app('production')
with app.app_context():
    # Test email (replace with your email)
    result = NotificationService.send_email(
        to_email='YOUR_EMAIL@example.com',
        to_name='Test User',
        subject='Holiday Party Planner - Test Email',
        html_content='<p>This is a test email from your Holiday Party Planner installation.</p>'
    )
    print(f"Email sent: {result}")
EOF

# Exit application user
exit
```

**Expected Output:** `Email sent: True`

**If email fails:**
- Check Brevo API key is correct
- Verify sender email is verified in Brevo
- Check logs: `sudo journalctl -u holiday-party -n 50`

---

## Phase 6: First Admin Account (5 minutes)

### Step 6.1: Create Admin Account

```bash
# Switch to application user
sudo -u holiday-party -i
cd app
source venv/bin/activate

# Run the create-admin command
flask create-admin
```

**You'll be prompted for:**
1. First name
2. Last name
3. Email address (this will be your login)
4. Phone number (optional)
5. Password (minimum 8 characters, hidden as you type)
6. Confirm password
7. Household name (defaults to "LastName Family")

**Example:**
```
First name: John
Last name: Doe
Email address: john@example.com
Phone number (optional): 555-1234
Password (min 8 characters): ********
Confirm password: ********
Household name (default: Doe Family):
```

**Expected Output:**
```
============================================================
✅ Admin account created successfully!
============================================================

Name: John Doe
Email: john@example.com
Household: Doe Family

You can now log in at: https://YOUR_DOMAIN_COM/organizer/login
============================================================
```

**📝 SAVE THESE CREDENTIALS:**
- Email: (your admin email)
- Password: (your admin password)

### Step 6.2: Test Admin Login

```bash
# Exit application user
exit

# Open your browser and visit:
# https://YOUR_DOMAIN_COM/organizer/login
```

**Try logging in with your admin credentials.**

**Expected Result:** You should be redirected to the organizer dashboard.

**If login fails:**
- Verify email and password are correct
- Check application logs: `sudo journalctl -u holiday-party -n 50`
- Verify database has the user:
  ```bash
  sudo -u holiday-party psql -d holiday_party_prod -c "SELECT email FROM persons;"
  ```

---

## Phase 7: Automated Backups (10 minutes)

### Step 7.1: Test Backup Script

```bash
# Test the backup script manually
sudo -u holiday-party /home/holiday-party/app/deploy/backup-database.sh
```

**Expected Output:**
```
========================================
Database Backup
Started at: ...
========================================

Backing up PostgreSQL database...
✓ PostgreSQL backup created: /home/holiday-party/app/backups/postgres_backup_TIMESTAMP.sql.gz (XXX KB)

Cleaning up old backups (older than 30 days)...
✓ No old backups to delete

Backup Statistics:
  Total backups: 1
  Total size: XXX KB
  Retention: 30 days

Recent Backups:
  postgres_backup_TIMESTAMP.sql.gz (XXX KB)

========================================
Backup completed successfully!
Finished at: ...
========================================
```

**Verification:**
```bash
# Check backup file was created
ls -lh /home/holiday-party/app/backups/
```

### Step 7.2: Schedule Automated Backups

```bash
# Edit crontab for the application user
sudo -u holiday-party crontab -e

# If prompted, choose nano (option 1)
```

**Add this line at the end of the file:**
```
# Daily database backup at 2:00 AM
0 2 * * * /home/holiday-party/app/deploy/backup-database.sh >> /home/holiday-party/app/logs/backup.log 2>&1
```

**Save and exit:** `Ctrl+X`, `Y`, `Enter`

**Verification:**
```bash
# List crontab to verify
sudo -u holiday-party crontab -l

# Should show the backup job
```

**Note:** The backup will run daily at 2:00 AM server time. To test immediately:
```bash
# Run the backup script again
sudo -u holiday-party /home/holiday-party/app/deploy/backup-database.sh
```

---

## Phase 8: Final Verification (15 minutes)

### Step 8.1: Complete System Check

Run through this checklist:

```bash
# 1. Check all services are running
sudo systemctl status holiday-party
sudo systemctl status nginx
sudo systemctl status postgresql
sudo systemctl status fail2ban

# All should show "active (running)"

# 2. Check firewall
sudo ufw status
# Should show OpenSSH and Nginx Full allowed

# 3. Check SSL certificate
sudo certbot certificates
# Should show your domain with valid dates

# 4. Check application logs
sudo journalctl -u holiday-party -n 20 --no-pager
# Should not show any errors

# 5. Check Nginx logs
sudo tail -20 /var/log/nginx/holiday-party-error.log
# Should be empty or minimal errors

# 6. Check disk space
df -h
# Should have plenty of free space

# 7. Check memory usage
free -h
# Should have free memory available

# 8. Check database
ls -lh /home/holiday-party/app/instance/holiday_party.db
# Should show the database file
sqlite3 /home/holiday-party/app/instance/holiday_party.db "SELECT COUNT(*) FROM persons;"
# Should return count of users
```

### Step 8.2: Test All Major Features

Open your browser and test:

1. **Homepage**
   - Visit: `https://YOUR_DOMAIN_COM`
   - Should load without errors
   - Check browser console (F12) for JavaScript errors

2. **Admin Login**
   - Visit: `https://YOUR_DOMAIN_COM/organizer/login`
   - Log in with your admin credentials
   - Should redirect to dashboard

3. **Create Test Event**
   - Click "Create Event" or similar
   - Fill in event details
   - Save the event
   - Verify it appears in the list

4. **Test Email (Optional)**
   - Create an invitation
   - Send a test invitation to yourself
   - Check if email arrives

5. **Test RSVP Flow**
   - Use the invitation link from email
   - Submit an RSVP
   - Verify it appears in the event dashboard

### Step 8.3: Performance Check

```bash
# Check response time
time curl -s https://YOUR_DOMAIN_COM > /dev/null

# Should complete in under 2 seconds

# Check if gzip compression is working
curl -H "Accept-Encoding: gzip" -I https://YOUR_DOMAIN_COM | grep -i "content-encoding"
# Should show: content-encoding: gzip
```

### Step 8.4: Security Check

```bash
# Check SSL rating (optional, requires internet)
# Visit: https://www.ssllabs.com/ssltest/analyze.html?d=YOUR_DOMAIN_COM
# Should get A or A+ rating

# Check security headers
curl -I https://YOUR_DOMAIN_COM | grep -i "strict-transport-security"
# Should show HSTS header

curl -I https://YOUR_DOMAIN_COM | grep -i "x-frame-options"
# Should show X-Frame-Options header

# Check that .env file is secure
ls -la /home/holiday-party/app/.env
# Should show: -rw------- (600 permissions)

# Check that only necessary ports are open
sudo ufw status numbered
# Should only show: 22 (SSH), 80 (HTTP), 443 (HTTPS)
```

### Step 8.5: Document Your Deployment

Create a file with your deployment information:

```bash
# Create a deployment info file (NOT in the git repo)
sudo -u holiday-party nano /home/holiday-party/DEPLOYMENT_INFO.txt
```

**Add this information:**
```
Holiday Party Planner - Deployment Information
==============================================

Deployment Date: [TODAY'S DATE]
Server: [YOUR_SERVER_IP]
Domain: YOUR_DOMAIN_COM
Ubuntu Version: [22.04 or 24.04]

Database:
- Name: holiday_party_prod
- User: holiday_party_user
- Password: [YOUR_DB_PASSWORD]

Admin Account:
- Email: [YOUR_ADMIN_EMAIL]
- Created: [TODAY'S DATE]

Brevo Configuration:
- API Key: [FIRST 10 CHARS]...
- Sender Email: [YOUR_SENDER_EMAIL]

Important Paths:
- App Directory: /home/holiday-party/app
- Logs: /home/holiday-party/app/logs
- Backups: /home/holiday-party/app/backups
- Nginx Config: /etc/nginx/sites-available/holiday-party
- Systemd Service: /etc/systemd/system/holiday-party.service

SSL Certificate:
- Issued: [CHECK WITH: sudo certbot certificates]
- Expires: [CHECK WITH: sudo certbot certificates]
- Auto-renewal: Enabled

Backup Schedule:
- Daily at 2:00 AM
- Retention: 30 days
- Location: /home/holiday-party/app/backups

Notes:
- [Add any custom configurations or notes]
```

**Save and secure the file:**
```bash
sudo chmod 600 /home/holiday-party/DEPLOYMENT_INFO.txt
```

---

## 🎉 Deployment Complete!

**Congratulations!** Your Holiday Party Planner is now live at `https://YOUR_DOMAIN_COM`

### What You've Accomplished:

✅ Secure Ubuntu server setup
✅ PostgreSQL database configured
✅ Python application installed
✅ Nginx web server with SSL/TLS
✅ Automated backups scheduled
✅ Admin account created
✅ Firewall and security configured
✅ All services running and monitored

### Next Steps:

1. **Bookmark important URLs:**
   - Application: `https://YOUR_DOMAIN_COM`
   - Admin Login: `https://YOUR_DOMAIN_COM/organizer/login`

2. **Set up monitoring** (optional):
   - Consider setting up uptime monitoring (UptimeRobot, Pingdom, etc.)
   - Set up log monitoring alerts

3. **Create your first event:**
   - Log in to the admin dashboard
   - Create your first holiday party event
   - Invite guests and test the full workflow

4. **Regular maintenance:**
   - Check logs weekly
   - Monitor disk space
   - Keep system updated (see Maintenance section)

---

## Ongoing Deployments

After initial setup, deploying updates is simple.

### When You Make Changes Locally:

```bash
# On your local machine
git add .
git commit -m "Description of changes"
git push origin main
```

### Deploy to Server:

```bash
# SSH to your server
ssh your-username@YOUR_SERVER_IP

# Switch to application user
sudo -u holiday-party -i

# Navigate to app directory
cd app

# Run deployment script
./deploy/deploy.sh
```

**The script will automatically:**
1. ✅ Backup the database
2. ✅ Pull latest code from GitHub
3. ✅ Update dependencies
4. ✅ Run database migrations
5. ✅ Run tests (optional)
6. ✅ Restart the application

**Time Required:** 2-5 minutes

### Deployment Best Practices:

1. **Always test locally first**
   ```bash
   pytest
   flask db upgrade
   ```

2. **Deploy during low-traffic times** (if possible)

3. **Monitor logs after deployment**
   ```bash
   sudo journalctl -u holiday-party -f
   ```

4. **Keep a deployment log**
   - Document what was deployed
   - Note any issues encountered
   - Record rollback procedures if needed

---

## Troubleshooting

### Common Issues and Solutions

#### Issue 1: Service Won't Start

**Symptoms:**
```bash
sudo systemctl status holiday-party
# Shows: failed (Result: exit-code)
```

**Solutions:**

1. **Check detailed logs:**
   ```bash
   sudo journalctl -u holiday-party -n 100 --no-pager
   ```

2. **Common causes:**
   - **Database connection failed:** Check DATABASE_URL in .env
   - **Port already in use:** Check if another process is using the socket
   - **Permission issues:** Check file ownership
   - **Missing dependencies:** Reinstall requirements

3. **Verify configuration:**
   ```bash
   # Check .env file exists and is readable
   sudo -u holiday-party cat /home/holiday-party/app/.env | head -5

   # Test database exists
   ls -lh /home/holiday-party/app/instance/holiday_party.db

   # Check if virtual environment is intact
   sudo -u holiday-party /home/holiday-party/app/venv/bin/python --version
   ```

4. **Restart from scratch:**
   ```bash
   sudo systemctl stop holiday-party
   sudo -u holiday-party -i
   cd app
   source venv/bin/activate
   python run.py  # Run manually to see errors
   # Press Ctrl+C to stop
   exit
   sudo systemctl start holiday-party
   ```

#### Issue 2: 502 Bad Gateway Error

**Symptoms:** Browser shows "502 Bad Gateway" when accessing the site.

**Solutions:**

1. **Check if application is running:**
   ```bash
   sudo systemctl status holiday-party
   # Should be "active (running)"
   ```

2. **Check if socket exists:**
   ```bash
   ls -la /run/holiday-party/
   # Should show holiday-party.sock
   ```

3. **Check Nginx error logs:**
   ```bash
   sudo tail -50 /var/log/nginx/holiday-party-error.log
   ```

4. **Restart both services:**
   ```bash
   sudo systemctl restart holiday-party
   sleep 3
   sudo systemctl restart nginx
   ```

#### Issue 3: SSL Certificate Issues

**Symptoms:** Browser shows "Your connection is not private" or certificate errors.

**Solutions:**

1. **Check certificate status:**
   ```bash
   sudo certbot certificates
   ```

2. **Renew certificate manually:**
   ```bash
   sudo certbot renew --force-renewal
   sudo systemctl reload nginx
   ```

3. **Check Nginx SSL configuration:**
   ```bash
   sudo nginx -t
   # Should show "syntax is ok"
   ```

4. **Verify DNS is correct:**
   ```bash
   nslookup YOUR_DOMAIN_COM
   # Should return your server IP
   ```

#### Issue 4: Email Not Sending

**Symptoms:** Invitations or notifications not arriving.

**Solutions:**

1. **Check Brevo credentials:**
   ```bash
   sudo -u holiday-party grep BREVO /home/holiday-party/app/.env
   # Verify API key and sender email
   ```

2. **Test Brevo API:**
   ```bash
   sudo -u holiday-party -i
   cd app
   source venv/bin/activate
   python3 << 'EOF'
   from app import create_app
   app = create_app('production')
   with app.app_context():
       print(f"Brevo API Key: {app.config['BREVO_API_KEY'][:10]}...")
       print(f"Sender Email: {app.config['BREVO_SENDER_EMAIL']}")
   EOF
   exit
   ```

3. **Check application logs:**
   ```bash
   sudo journalctl -u holiday-party -n 100 | grep -i email
   ```

4. **Verify sender email in Brevo:**
   - Log in to https://app.brevo.com
   - Go to Settings → Senders & IP
   - Ensure your sender email is verified

#### Issue 5: Database Migration Fails

**Symptoms:** `flask db upgrade` shows errors.

**Solutions:**

1. **Check current migration status:**
   ```bash
   sudo -u holiday-party -i
   cd app
   source venv/bin/activate
   flask db current
   ```

2. **Check for migration conflicts:**
   ```bash
   ls -la migrations/versions/
   # Look for multiple head revisions
   ```

3. **Rollback and retry:**
   ```bash
   flask db downgrade
   flask db upgrade
   ```

4. **If all else fails, backup and recreate:**
   ```bash
   # Backup first!
   ./deploy/backup-database.sh

   # Drop and recreate (CAUTION: loses data)
   # Only do this if you have a backup and it's a fresh install
   sudo -u postgres psql -c "DROP DATABASE holiday_party_prod;"
   sudo -u postgres psql -c "CREATE DATABASE holiday_party_prod;"
   sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE holiday_party_prod TO holiday_party_user;"

   # Reinitialize
   flask db upgrade
   ```

#### Issue 6: Out of Disk Space

**Symptoms:** Application crashes, logs show disk space errors.

**Solutions:**

1. **Check disk usage:**
   ```bash
   df -h
   # Look for filesystems at 100%
   ```

2. **Find large files:**
   ```bash
   sudo du -sh /home/holiday-party/app/* | sort -h
   ```

3. **Clean up old backups:**
   ```bash
   # Remove backups older than 7 days (adjust as needed)
   find /home/holiday-party/app/backups -name "*.gz" -mtime +7 -delete
   ```

4. **Clean up logs:**
   ```bash
   # Truncate large log files
   sudo truncate -s 0 /home/holiday-party/app/logs/app.log
   sudo truncate -s 0 /home/holiday-party/app/logs/error.log

   # Or rotate logs
   sudo logrotate -f /etc/logrotate.conf
   ```

5. **Clean up system logs:**
   ```bash
   sudo journalctl --vacuum-time=7d
   ```

#### Issue 7: High Memory Usage

**Symptoms:** Server becomes slow, application crashes.

**Solutions:**

1. **Check memory usage:**
   ```bash
   free -h
   htop  # Install with: sudo apt install htop
   ```

2. **Reduce Gunicorn workers:**
   ```bash
   sudo nano /etc/systemd/system/holiday-party.service
   # Change --workers 4 to --workers 2
   sudo systemctl daemon-reload
   sudo systemctl restart holiday-party
   ```

3. **Add swap space (if needed):**
   ```bash
   # Create 2GB swap file
   sudo fallocate -l 2G /swapfile
   sudo chmod 600 /swapfile
   sudo mkswap /swapfile
   sudo swapon /swapfile

   # Make permanent
   echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
   ```

#### Issue 8: Can't SSH to Server

**Symptoms:** SSH connection refused or times out.

**Solutions:**

1. **Check if you locked yourself out with firewall:**
   - Use your hosting provider's console/VNC access
   - Run: `sudo ufw allow OpenSSH`
   - Run: `sudo ufw reload`

2. **Check SSH service:**
   ```bash
   sudo systemctl status ssh
   sudo systemctl restart ssh
   ```

3. **Check firewall rules:**
   ```bash
   sudo ufw status numbered
   # Ensure OpenSSH is allowed
   ```

#### Issue 9: Application Running Slow

**Symptoms:** Pages take a long time to load.

**Solutions:**

1. **Check database performance:**
   ```bash
   sudo -u holiday-party psql -d holiday_party_prod -c "
   SELECT schemaname, tablename,
          pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
   FROM pg_tables
   WHERE schemaname = 'public'
   ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;"
   ```

2. **Check for slow queries:**
   ```bash
   sudo journalctl -u holiday-party -n 1000 | grep -i "slow"
   ```

3. **Restart services:**
   ```bash
   sudo systemctl restart holiday-party
   sudo systemctl restart postgresql
   ```

4. **Check server resources:**
   ```bash
   top
   # Look for high CPU or memory usage
   ```

### Getting Help

If you're still stuck:

1. **Check application logs:**
   ```bash
   sudo journalctl -u holiday-party -n 200 --no-pager
   tail -100 /home/holiday-party/app/logs/app.log
   ```

2. **Check Nginx logs:**
   ```bash
   sudo tail -100 /var/log/nginx/holiday-party-error.log
   sudo tail -100 /var/log/nginx/holiday-party-access.log
   ```

3. **Check system logs:**
   ```bash
   sudo journalctl -xe
   ```

4. **Document the issue:**
   - What were you trying to do?
   - What error messages did you see?
   - What have you tried already?
   - Include relevant log excerpts

---

## Maintenance & Monitoring

### Daily Checks (Automated)

These happen automatically:
- ✅ Database backups (2:00 AM daily)
- ✅ SSL certificate renewal checks (twice daily)
- ✅ Log rotation

### Weekly Maintenance (5 minutes)

```bash
# 1. Check service status
sudo systemctl status holiday-party nginx postgresql

# 2. Check disk space
df -h

# 3. Check recent errors
sudo journalctl -u holiday-party --since "1 week ago" | grep -i error

# 4. Check backup status
ls -lh /home/holiday-party/app/backups/ | tail -10

# 5. Check SSL certificate expiry
sudo certbot certificates
```

### Monthly Maintenance (15 minutes)

```bash
# 1. Update system packages
sudo apt update
sudo apt upgrade -y

# 2. Check for security updates
sudo apt list --upgradable | grep -i security

# 3. Review logs for patterns
sudo journalctl -u holiday-party --since "1 month ago" | grep -i error | sort | uniq -c | sort -rn | head -20

# 4. Check database size
ls -lh /home/holiday-party/app/instance/holiday_party.db

# 5. Test backup restoration (on a test server)
# This is important but requires a separate test environment

# 6. Review and clean old backups if needed
find /home/holiday-party/app/backups -name "*.gz" -mtime +60 -ls
```

### Quarterly Maintenance (30 minutes)

```bash
# 1. Review and update Python dependencies
sudo -u holiday-party -i
cd app
source venv/bin/activate
pip list --outdated

# Update if needed (test first!)
# pip install --upgrade package-name

# 2. Review security settings
sudo ufw status
sudo fail2ban-client status

# 3. Check SSL rating
# Visit: https://www.ssllabs.com/ssltest/analyze.html?d=YOUR_DOMAIN_COM

# 4. Review application performance
# Check response times, error rates, etc.

# 5. Update documentation
# Update DEPLOYMENT_INFO.txt with any changes
```

### Monitoring Commands Reference

```bash
# Service status
sudo systemctl status holiday-party
sudo systemctl status nginx
sudo systemctl status postgresql

# Real-time logs
sudo journalctl -u holiday-party -f
tail -f /home/holiday-party/app/logs/app.log
tail -f /var/log/nginx/holiday-party-error.log

# Resource usage
htop
df -h
free -h

# Network connections
sudo netstat -tulpn | grep -E '(80|443|5432)'

# Recent errors
sudo journalctl -u holiday-party --since "1 hour ago" | grep -i error

# Database info
ls -lh /home/holiday-party/app/instance/holiday_party.db
sqlite3 /home/holiday-party/app/instance/holiday_party.db "SELECT COUNT(*) FROM persons;"

# Check response time
time curl -s https://YOUR_DOMAIN_COM > /dev/null
```

### Setting Up Monitoring Alerts (Optional)

#### Option 1: Simple Email Alerts

Create a monitoring script:

```bash
sudo nano /usr/local/bin/check-holiday-party.sh
```

Add:
```bash
#!/bin/bash
if ! systemctl is-active --quiet holiday-party; then
    echo "Holiday Party service is down!" | mail -s "ALERT: Service Down" your-email@example.com
fi
```

Make executable and schedule:
```bash
sudo chmod +x /usr/local/bin/check-holiday-party.sh
sudo crontab -e
# Add: */5 * * * * /usr/local/bin/check-holiday-party.sh
```

#### Option 2: External Monitoring

Consider using:
- **UptimeRobot** (free tier available): https://uptimerobot.com
- **Pingdom**: https://www.pingdom.com
- **StatusCake**: https://www.statuscake.com

Set up monitoring for:
- `https://YOUR_DOMAIN_COM` (homepage)
- `https://YOUR_DOMAIN_COM/api/health` (health check)

### Backup Verification

**Test your backups regularly!**

```bash
# 1. List recent backups
ls -lh /home/holiday-party/app/backups/

# 2. Test backup integrity
gunzip -t /home/holiday-party/app/backups/sqlite_backup_LATEST.db.gz

# 3. Test restoration (on a test database)
# Create test directory
mkdir -p /tmp/db_test

# Restore backup
gunzip -c /home/holiday-party/app/backups/sqlite_backup_LATEST.db.gz > /tmp/db_test/test.db

# Verify data
sqlite3 /tmp/db_test/test.db "SELECT COUNT(*) FROM persons;"

# Clean up
rm -rf /tmp/db_test
```

### Security Maintenance

```bash
# 1. Check for failed login attempts
sudo journalctl -u ssh --since "1 week ago" | grep -i "failed"

# 2. Check fail2ban status
sudo fail2ban-client status sshd

# 3. Review firewall logs
sudo tail -100 /var/log/ufw.log

# 4. Check for security updates
sudo apt update
sudo apt list --upgradable | grep -i security

# 5. Review user accounts
cat /etc/passwd | grep -v nologin

# 6. Check for unusual processes
ps aux | grep -v "\[" | sort -k3 -rn | head -10
```

---

## Appendix: Quick Reference

### Important File Locations

```
Application:
  /home/holiday-party/app/                 - Application root
  /home/holiday-party/app/.env             - Environment configuration
  /home/holiday-party/app/logs/            - Application logs
  /home/holiday-party/app/backups/         - Database backups
  /home/holiday-party/app/instance/        - SQLite database (if used)

Configuration:
  /etc/systemd/system/holiday-party.service - Systemd service
  /etc/nginx/sites-available/holiday-party  - Nginx configuration
  /etc/letsencrypt/live/YOUR_DOMAIN_COM/    - SSL certificates

Logs:
  /var/log/nginx/holiday-party-access.log   - Nginx access log
  /var/log/nginx/holiday-party-error.log    - Nginx error log
  /home/holiday-party/app/logs/app.log      - Application log
  /home/holiday-party/app/logs/error.log    - Gunicorn error log
```

### Essential Commands

```bash
# Service Management
sudo systemctl start holiday-party
sudo systemctl stop holiday-party
sudo systemctl restart holiday-party
sudo systemctl status holiday-party
sudo systemctl reload nginx

# View Logs
sudo journalctl -u holiday-party -f
tail -f /home/holiday-party/app/logs/app.log
sudo tail -f /var/log/nginx/holiday-party-error.log

# Application Management
sudo -u holiday-party -i
cd app && source venv/bin/activate
flask create-admin
flask shell
flask db upgrade

# Database
sudo -u holiday-party psql -d holiday_party_prod
./deploy/backup-database.sh

# Deployment
./deploy/deploy.sh

# SSL Certificate
sudo certbot certificates
sudo certbot renew
sudo certbot renew --dry-run
```

### Emergency Procedures

#### If Site is Down

```bash
# 1. Check service status
sudo systemctl status holiday-party nginx

# 2. Check logs for errors
sudo journalctl -u holiday-party -n 50

# 3. Restart services
sudo systemctl restart holiday-party
sudo systemctl restart nginx

# 4. If still down, check database
sudo systemctl status postgresql
sudo -u holiday-party psql -d holiday_party_prod -c "SELECT 1;"

# 5. Check disk space
df -h

# 6. Check memory
free -h
```

#### If Need to Rollback

```bash
# 1. Stop service
sudo systemctl stop holiday-party

# 2. Switch to application user
sudo -u holiday-party -i
cd app

# 3. Checkout previous version
git log --oneline -10  # Find the commit to rollback to
git checkout COMMIT_HASH

# 4. Rollback database if needed
source venv/bin/activate
flask db downgrade

# 5. Restart service
exit
sudo systemctl start holiday-party
```

#### If Database is Corrupted

```bash
# 1. Stop application
sudo systemctl stop holiday-party

# 2. Find latest backup
ls -lt /home/holiday-party/app/backups/ | head -5

# 3. Backup the corrupted database (just in case)
sudo -u holiday-party cp /home/holiday-party/app/instance/holiday_party.db \
    /home/holiday-party/app/instance/holiday_party.db.corrupted

# 4. Restore from backup
sudo -u holiday-party gunzip -c /home/holiday-party/app/backups/sqlite_backup_TIMESTAMP.db.gz > \
    /home/holiday-party/app/instance/holiday_party.db

# 5. Restart application
sudo systemctl start holiday-party

# 6. Verify restoration
sqlite3 /home/holiday-party/app/instance/holiday_party.db "SELECT COUNT(*) FROM persons;"
```

---

## Appendix A: Migrating from SQLite to PostgreSQL

If your application grows and you need to migrate to PostgreSQL for better performance and scalability, follow these steps:

### When to Migrate

Consider migrating to PostgreSQL when:
- You have 100+ concurrent users
- Database file size exceeds 1GB
- You need multiple application servers
- You experience database locking issues
- You need advanced database features (full-text search, JSON queries, etc.)

### Migration Steps

#### 1. Install PostgreSQL

```bash
# Install PostgreSQL
sudo apt install -y postgresql postgresql-contrib libpq-dev

# Start and enable
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

#### 2. Create PostgreSQL Database

```bash
# Switch to postgres user
sudo -u postgres psql

# In PostgreSQL prompt:
CREATE DATABASE holiday_party_prod;
CREATE USER holiday_party_user WITH PASSWORD 'YOUR_STRONG_PASSWORD';
GRANT ALL PRIVILEGES ON DATABASE holiday_party_prod TO holiday_party_user;

-- For PostgreSQL 15+ (Ubuntu 24.04)
\c holiday_party_prod
GRANT ALL ON SCHEMA public TO holiday_party_user;

\q
```

#### 3. Export Data from SQLite

```bash
# Stop the application
sudo systemctl stop holiday-party

# Backup SQLite database
sudo -u holiday-party cp /home/holiday-party/app/instance/holiday_party.db \
    /home/holiday-party/app/backups/sqlite_before_migration_$(date +%Y%m%d).db

# Export to SQL
sudo -u holiday-party sqlite3 /home/holiday-party/app/instance/holiday_party.db .dump > \
    /tmp/sqlite_export.sql
```

#### 4. Convert and Import to PostgreSQL

```bash
# Install conversion tool
pip install pgloader

# Or manually convert (simpler for small databases)
# Edit the SQL file to make it PostgreSQL compatible
# Then import:
sudo -u postgres psql holiday_party_prod < /tmp/sqlite_export.sql
```

#### 5. Update Configuration

```bash
# Edit .env file
sudo -u holiday-party nano /home/holiday-party/app/.env

# Change DATABASE_URL from:
# DATABASE_URL=sqlite:///instance/holiday_party.db
# To:
# DATABASE_URL=postgresql://holiday_party_user:YOUR_PASSWORD@localhost/holiday_party_prod
```

#### 6. Update Systemd Service

```bash
# Edit service file
sudo nano /etc/systemd/system/holiday-party.service

# Change After= line to:
# After=network.target postgresql.service

# Add Wants= line:
# Wants=postgresql.service

# Reload and restart
sudo systemctl daemon-reload
sudo systemctl start holiday-party
```

#### 7. Verify Migration

```bash
# Check application logs
sudo journalctl -u holiday-party -n 50

# Test database connection
sudo -u holiday-party psql -d holiday_party_prod -c "SELECT COUNT(*) FROM persons;"

# Test the application
curl https://YOUR_DOMAIN_COM
```

#### 8. Update Backup Script

The backup script (`deploy/backup-database.sh`) already supports PostgreSQL, so it will automatically detect and backup PostgreSQL once you've migrated.

### Rollback Plan

If migration fails:

```bash
# Stop application
sudo systemctl stop holiday-party

# Restore SQLite configuration in .env
sudo -u holiday-party nano /home/holiday-party/app/.env
# Change DATABASE_URL back to: sqlite:///instance/holiday_party.db

# Restart application
sudo systemctl start holiday-party
```

---

## Support & Additional Resources

### Documentation Files

- `deploy/README.md` - Detailed deployment documentation
- `deploy/QUICKSTART.md` - Quick reference guide
- `deploy/DEPLOYMENT_CHECKLIST.md` - Step-by-step checklist
- `deploy/FILES_CREATED.md` - File inventory
- `DEPLOYMENT_SUMMARY.md` - High-level overview

### Useful Links

- **Ubuntu Documentation:** https://help.ubuntu.com/
- **Nginx Documentation:** https://nginx.org/en/docs/
- **PostgreSQL Documentation:** https://www.postgresql.org/docs/
- **Flask Documentation:** https://flask.palletsprojects.com/
- **Let's Encrypt:** https://letsencrypt.org/docs/
- **Brevo (Sendinblue):** https://developers.brevo.com/

### Getting Help

If you encounter issues not covered in this guide:

1. Check the troubleshooting section above
2. Review application logs for specific error messages
3. Search for the error message online
4. Check the project's GitHub issues (if applicable)
5. Consult the official documentation for the relevant component

---

## Changelog

### Version 1.0 (2025-11-26)
- Initial comprehensive Ubuntu deployment guide
- Covers Ubuntu 22.04 LTS and 24.04 LTS
- Complete walkthrough from fresh server to production
- Includes troubleshooting and maintenance sections

---

**End of Guide**

Good luck with your deployment! 🎉


