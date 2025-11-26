#!/bin/bash
# Initial Server Setup Script for Holiday Party Planner
# 
# This script sets up a fresh Ubuntu/Debian server for the Holiday Party Planner application
# Run this script ONCE during initial server setup
#
# Usage:
#   sudo bash deploy/setup-server.sh
#
# Requirements:
#   - Ubuntu 20.04+ or Debian 11+
#   - Root or sudo access
#   - Internet connection

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
APP_USER="holiday-party"
APP_GROUP="holiday-party"
APP_DIR="/home/$APP_USER/app"
PYTHON_VERSION="3.11"
REPO_URL=""  # Will be prompted

print_step() {
    echo -e "\n${BLUE}==>${NC} ${YELLOW}$1${NC}"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

error_exit() {
    print_error "ERROR: $1"
    exit 1
}

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    error_exit "Please run this script as root or with sudo"
fi

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Holiday Party Planner - Server Setup${NC}"
echo -e "${GREEN}========================================${NC}\n"

# Prompt for repository URL
echo -e "${YELLOW}Enter your GitHub repository URL:${NC}"
read -p "Repository URL: " REPO_URL

if [ -z "$REPO_URL" ]; then
    error_exit "Repository URL is required"
fi

# Prompt for domain name
echo -e "\n${YELLOW}Enter your domain name (e.g., party.example.com):${NC}"
read -p "Domain: " DOMAIN_NAME

if [ -z "$DOMAIN_NAME" ]; then
    error_exit "Domain name is required"
fi

# Confirm settings
echo -e "\n${BLUE}Configuration:${NC}"
echo "  App User: $APP_USER"
echo "  App Directory: $APP_DIR"
echo "  Python Version: $PYTHON_VERSION"
echo "  Repository: $REPO_URL"
echo "  Domain: $DOMAIN_NAME"
echo ""
read -p "Continue with these settings? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Setup cancelled"
    exit 0
fi

# ============================================================================
# STEP 1: Update System
# ============================================================================

print_step "Step 1: Updating system packages..."
apt update
apt upgrade -y
print_success "System updated"

# ============================================================================
# STEP 2: Install Dependencies
# ============================================================================

print_step "Step 2: Installing system dependencies..."
apt install -y \
    python${PYTHON_VERSION} \
    python${PYTHON_VERSION}-venv \
    python3-pip \
    postgresql \
    postgresql-contrib \
    nginx \
    git \
    supervisor \
    certbot \
    python3-certbot-nginx \
    ufw \
    fail2ban \
    build-essential \
    libpq-dev \
    python3-dev

print_success "Dependencies installed"

# ============================================================================
# STEP 3: Create Application User
# ============================================================================

print_step "Step 3: Creating application user..."
if id "$APP_USER" &>/dev/null; then
    print_success "User $APP_USER already exists"
else
    useradd -m -s /bin/bash "$APP_USER"
    usermod -aG www-data "$APP_USER"
    print_success "User $APP_USER created"
fi

# ============================================================================
# STEP 4: Set Up PostgreSQL Database
# ============================================================================

print_step "Step 4: Setting up PostgreSQL database..."

# Generate random password
DB_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)
DB_NAME="holiday_party_prod"
DB_USER="holiday_party_user"

sudo -u postgres psql <<EOF
CREATE DATABASE $DB_NAME;
CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD';
GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;
\q
EOF

print_success "Database created"
echo -e "${YELLOW}Database credentials (save these):${NC}"
echo "  Database: $DB_NAME"
echo "  User: $DB_USER"
echo "  Password: $DB_PASSWORD"

# ============================================================================
# STEP 5: Clone Repository
# ============================================================================

print_step "Step 5: Cloning repository..."
if [ -d "$APP_DIR" ]; then
    print_success "Directory $APP_DIR already exists"
else
    sudo -u "$APP_USER" git clone "$REPO_URL" "$APP_DIR"
    print_success "Repository cloned"
fi

cd "$APP_DIR"

# ============================================================================
# STEP 6: Create Virtual Environment
# ============================================================================

print_step "Step 6: Creating Python virtual environment..."
sudo -u "$APP_USER" python${PYTHON_VERSION} -m venv "$APP_DIR/venv"
sudo -u "$APP_USER" "$APP_DIR/venv/bin/pip" install --upgrade pip
sudo -u "$APP_USER" "$APP_DIR/venv/bin/pip" install -r "$APP_DIR/requirements.txt"
print_success "Virtual environment created and dependencies installed"

# ============================================================================
# STEP 7: Create Directories
# ============================================================================

print_step "Step 7: Creating necessary directories..."
sudo -u "$APP_USER" mkdir -p "$APP_DIR/logs"
sudo -u "$APP_USER" mkdir -p "$APP_DIR/backups"
sudo -u "$APP_USER" mkdir -p "$APP_DIR/instance"
print_success "Directories created"

# ============================================================================
# STEP 8: Configure Environment Variables
# ============================================================================

print_step "Step 8: Creating .env file..."

# Generate SECRET_KEY
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")

# Create .env file
sudo -u "$APP_USER" cat > "$APP_DIR/.env" <<EOF
# Flask Configuration
FLASK_APP=run.py
FLASK_ENV=production
SECRET_KEY=$SECRET_KEY

# Database Configuration
DATABASE_URL=postgresql://$DB_USER:$DB_PASSWORD@localhost/$DB_NAME

# Brevo Email Configuration (CONFIGURE THESE MANUALLY)
BREVO_API_KEY=your-brevo-api-key-here
BREVO_SENDER_EMAIL=noreply@$DOMAIN_NAME
BREVO_SENDER_NAME=Holiday Party Planner

# Application Settings
APP_NAME=Family Holiday Party Planner
APP_URL=https://$DOMAIN_NAME
SUPPORT_EMAIL=support@$DOMAIN_NAME

# Security & Authentication
TOKEN_EXPIRATION_DAYS=90
MAGIC_LINK_EXPIRATION_MINUTES=30
PASSWORD_RESET_EXPIRATION_MINUTES=60
AUTH_TOKEN_RATE_LIMIT=5

# Email Settings
MAIL_SERVER=smtp-relay.brevo.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-brevo-username
MAIL_PASSWORD=your-brevo-smtp-key

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
EOF

chmod 600 "$APP_DIR/.env"
chown "$APP_USER:$APP_GROUP" "$APP_DIR/.env"
print_success ".env file created"

# ============================================================================
# STEP 9: Initialize Database
# ============================================================================

print_step "Step 9: Initializing database..."
cd "$APP_DIR"
sudo -u "$APP_USER" "$APP_DIR/venv/bin/flask" db upgrade
print_success "Database initialized"

# ============================================================================
# STEP 10: Install Systemd Service
# ============================================================================

print_step "Step 10: Installing systemd service..."

# Update service file with actual paths
sed -i "s|/home/holiday-party/app|$APP_DIR|g" "$APP_DIR/deploy/holiday-party.service"
sed -i "s|User=holiday-party|User=$APP_USER|g" "$APP_DIR/deploy/holiday-party.service"
sed -i "s|Group=holiday-party|Group=$APP_GROUP|g" "$APP_DIR/deploy/holiday-party.service"

cp "$APP_DIR/deploy/holiday-party.service" /etc/systemd/system/
systemctl daemon-reload
systemctl enable holiday-party
print_success "Systemd service installed"

# ============================================================================
# STEP 11: Configure Nginx
# ============================================================================

print_step "Step 11: Configuring Nginx..."

# Update nginx config with actual domain and paths
sed -i "s|your-domain.com|$DOMAIN_NAME|g" "$APP_DIR/deploy/nginx-config"
sed -i "s|/home/holiday-party/app|$APP_DIR|g" "$APP_DIR/deploy/nginx-config"

cp "$APP_DIR/deploy/nginx-config" /etc/nginx/sites-available/holiday-party
ln -sf /etc/nginx/sites-available/holiday-party /etc/nginx/sites-enabled/

# Remove default site
rm -f /etc/nginx/sites-enabled/default

# Test nginx config
nginx -t
print_success "Nginx configured"

# ============================================================================
# STEP 12: Configure Firewall
# ============================================================================

print_step "Step 12: Configuring firewall..."
ufw allow 'Nginx Full'
ufw allow OpenSSH
ufw --force enable
print_success "Firewall configured"

# ============================================================================
# STEP 13: Set Up Fail2ban
# ============================================================================

print_step "Step 13: Configuring Fail2ban..."
systemctl enable fail2ban
systemctl start fail2ban
print_success "Fail2ban configured"

# ============================================================================
# STEP 14: Start Services
# ============================================================================

print_step "Step 14: Starting services..."
systemctl start holiday-party
systemctl reload nginx
print_success "Services started"

# ============================================================================
# SETUP COMPLETE
# ============================================================================

echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}✓ Server setup completed!${NC}"
echo -e "${GREEN}========================================${NC}\n"

echo -e "${BLUE}Next Steps:${NC}\n"

echo -e "${YELLOW}1. Configure Brevo Email:${NC}"
echo "   Edit $APP_DIR/.env and add your Brevo API credentials"
echo ""

echo -e "${YELLOW}2. Set up SSL certificate:${NC}"
echo "   sudo certbot --nginx -d $DOMAIN_NAME"
echo ""

echo -e "${YELLOW}3. Create admin account:${NC}"
echo "   sudo -u $APP_USER bash -c 'cd $APP_DIR && source venv/bin/activate && flask create-admin'"
echo ""

echo -e "${YELLOW}4. Set up automated backups:${NC}"
echo "   sudo -u $APP_USER crontab -e"
echo "   Add: 0 2 * * * $APP_DIR/deploy/backup-database.sh"
echo ""

echo -e "${YELLOW}5. Test the application:${NC}"
echo "   Visit: http://$DOMAIN_NAME (or https:// after SSL setup)"
echo ""

echo -e "${BLUE}Important Information:${NC}\n"
echo "  App Directory: $APP_DIR"
echo "  App User: $APP_USER"
echo "  Database: $DB_NAME"
echo "  DB User: $DB_USER"
echo "  DB Password: $DB_PASSWORD"
echo ""
echo "  Service: sudo systemctl status holiday-party"
echo "  Logs: sudo journalctl -u holiday-party -f"
echo "  Deploy: cd $APP_DIR && ./deploy/deploy.sh"
echo ""

echo -e "${RED}IMPORTANT: Save the database password shown above!${NC}\n"


