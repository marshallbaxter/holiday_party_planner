#!/bin/bash
# Holiday Party Planner Deployment Script
# This script safely deploys updates from GitHub to production

set -e  # Exit on any error

# ============================================================================
# CONFIGURATION - Edit these values for your environment
# ============================================================================

APP_DIR="/opt/holiday-party/app"
REPO_URL="https://github.com/yourusername/holiday_party_planner.git"
VENV_DIR="$APP_DIR/venv"
BACKUP_DIR="$APP_DIR/backups"
SERVICE_NAME="holiday-party"  # systemd service name
BRANCH="main"  # Git branch to deploy

# ============================================================================
# DO NOT EDIT BELOW THIS LINE UNLESS YOU KNOW WHAT YOU'RE DOING
# ============================================================================

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_step() {
    echo -e "\n${BLUE}[$(date '+%H:%M:%S')]${NC} ${YELLOW}$1${NC}"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

# Function to handle errors
error_exit() {
    print_error "ERROR: $1"
    echo -e "\n${RED}Deployment failed!${NC}" >&2
    exit 1
}

# ============================================================================
# PRE-FLIGHT CHECKS
# ============================================================================

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Holiday Party Planner Deployment${NC}"
echo -e "${GREEN}Started at: $(date)${NC}"
echo -e "${GREEN}========================================${NC}"

# Check if running as root
if [ "$EUID" -eq 0 ]; then 
    error_exit "Do not run this script as root. Use your application user."
fi

# Check if app directory exists
if [ ! -d "$APP_DIR" ]; then
    error_exit "App directory does not exist: $APP_DIR"
fi

# Navigate to app directory
cd "$APP_DIR" || error_exit "Cannot access app directory"

# Check if virtual environment exists
if [ ! -d "$VENV_DIR" ]; then
    error_exit "Virtual environment not found: $VENV_DIR"
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    error_exit ".env file not found. Please create it from .env.example"
fi

# ============================================================================
# STEP 1: BACKUP DATABASE
# ============================================================================

print_step "[1/9] Backing up database..."
mkdir -p "$BACKUP_DIR"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

if [ -f "instance/holiday_party.db" ]; then
    cp instance/holiday_party.db "$BACKUP_DIR/holiday_party_${TIMESTAMP}.db"
    print_success "SQLite database backed up to $BACKUP_DIR/holiday_party_${TIMESTAMP}.db"
elif [ ! -z "$DATABASE_URL" ] && [[ "$DATABASE_URL" == postgresql* ]]; then
    # PostgreSQL backup
    DB_NAME=$(echo $DATABASE_URL | sed -n 's/.*\/\([^?]*\).*/\1/p')
    if [ ! -z "$DB_NAME" ]; then
        pg_dump "$DB_NAME" > "$BACKUP_DIR/db_backup_${TIMESTAMP}.sql" 2>/dev/null || \
            print_warning "PostgreSQL backup failed (continuing anyway)"
        if [ -f "$BACKUP_DIR/db_backup_${TIMESTAMP}.sql" ]; then
            print_success "PostgreSQL database backed up"
        fi
    fi
else
    print_warning "No database found to backup (first deployment?)"
fi

# Keep only last 30 backups
find "$BACKUP_DIR" -name "holiday_party_*.db" -o -name "db_backup_*.sql" | \
    sort -r | tail -n +31 | xargs -r rm
print_success "Old backups cleaned up (keeping last 30)"

# ============================================================================
# STEP 2: STASH LOCAL CHANGES (if any)
# ============================================================================

print_step "[2/9] Checking for local changes..."
if ! git diff-index --quiet HEAD --; then
    print_warning "Local changes detected, stashing..."
    git stash save "Auto-stash before deployment at $TIMESTAMP"
    print_success "Local changes stashed"
else
    print_success "No local changes to stash"
fi

# ============================================================================
# STEP 3: PULL LATEST CODE
# ============================================================================

print_step "[3/9] Pulling latest code from GitHub..."
git fetch origin || error_exit "Failed to fetch from GitHub"

# Show what will be updated
CURRENT_COMMIT=$(git rev-parse HEAD)
LATEST_COMMIT=$(git rev-parse origin/$BRANCH)

if [ "$CURRENT_COMMIT" = "$LATEST_COMMIT" ]; then
    print_success "Already up to date (no new commits)"
else
    echo "Updating from $CURRENT_COMMIT to $LATEST_COMMIT"
    git log --oneline $CURRENT_COMMIT..$LATEST_COMMIT | head -5
    
    git pull origin $BRANCH || error_exit "Failed to pull from GitHub"
    print_success "Code updated successfully"
fi

# ============================================================================
# STEP 4: ACTIVATE VIRTUAL ENVIRONMENT
# ============================================================================

print_step "[4/9] Activating virtual environment..."
source "$VENV_DIR/bin/activate" || error_exit "Failed to activate virtual environment"
print_success "Virtual environment activated"

# ============================================================================
# STEP 5: INSTALL/UPDATE DEPENDENCIES
# ============================================================================

print_step "[5/9] Installing/updating dependencies..."
pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet || error_exit "Failed to install dependencies"
print_success "Dependencies updated"

# ============================================================================
# STEP 6: RUN DATABASE MIGRATIONS
# ============================================================================

print_step "[6/9] Running database migrations..."
export FLASK_APP=run.py

# Check if there are pending migrations
if flask db current &>/dev/null; then
    flask db upgrade || error_exit "Database migration failed"
    print_success "Database migrations applied"
else
    print_warning "Database not initialized. Run 'flask db upgrade' manually."
fi

# ============================================================================
# STEP 7: COLLECT STATIC FILES
# ============================================================================

print_step "[7/9] Preparing static assets..."
# Create necessary directories if they don't exist
mkdir -p logs
mkdir -p instance
print_success "Static assets ready"

# ============================================================================
# STEP 8: RUN TESTS (OPTIONAL)
# ============================================================================

print_step "[8/9] Running tests..."
if [ -d "tests" ] && [ -f "pytest.ini" ]; then
    if pytest tests/ -v --tb=short -q 2>&1 | tee /tmp/test_output.txt; then
        print_success "All tests passed"
    else
        print_warning "Some tests failed"
        echo -e "\n${YELLOW}Test failures detected. Continue with deployment? (y/n)${NC}"
        read -r response
        if [[ ! "$response" =~ ^[Yy]$ ]]; then
            error_exit "Deployment cancelled due to test failures"
        fi
        print_warning "Continuing deployment despite test failures"
    fi
else
    print_warning "No tests found, skipping"
fi

# ============================================================================
# STEP 9: RESTART APPLICATION SERVICE
# ============================================================================

print_step "[9/9] Restarting application service..."

# Check if service exists
if ! systemctl list-unit-files | grep -q "^${SERVICE_NAME}.service"; then
    print_warning "Service $SERVICE_NAME not found. Skipping restart."
    print_warning "You may need to start the application manually."
else
    sudo systemctl restart "$SERVICE_NAME" || error_exit "Failed to restart service"
    sleep 3

    if sudo systemctl is-active --quiet "$SERVICE_NAME"; then
        print_success "Service restarted successfully"
    else
        error_exit "Service failed to start. Check logs: sudo journalctl -u $SERVICE_NAME -n 50"
    fi
fi

# ============================================================================
# DEPLOYMENT COMPLETE
# ============================================================================

echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}✓ Deployment completed successfully!${NC}"
echo -e "${GREEN}========================================${NC}"

# Show service status
if systemctl list-unit-files | grep -q "^${SERVICE_NAME}.service"; then
    echo -e "\n${BLUE}Service Status:${NC}"
    sudo systemctl status "$SERVICE_NAME" --no-pager -l | head -15

    echo -e "\n${BLUE}Recent Logs:${NC}"
    sudo journalctl -u "$SERVICE_NAME" -n 10 --no-pager
fi

echo -e "\n${GREEN}Deployment finished at $(date)${NC}"
echo -e "${GREEN}========================================${NC}\n"

# Show helpful commands
echo -e "${BLUE}Useful commands:${NC}"
echo "  View logs:        sudo journalctl -u $SERVICE_NAME -f"
echo "  Restart service:  sudo systemctl restart $SERVICE_NAME"
echo "  Check status:     sudo systemctl status $SERVICE_NAME"
echo "  View app logs:    tail -f $APP_DIR/logs/app.log"
echo ""

