#!/bin/bash
# Database Backup Script for Holiday Party Planner
# 
# This script backs up the database and cleans up old backups
# Add to crontab for automated backups:
#   crontab -e
#   0 2 * * * /home/holiday-party/app/deploy/backup-database.sh
#
# This will run daily at 2:00 AM

set -e

# Configuration
APP_DIR="/home/holiday-party/app"
BACKUP_DIR="$APP_DIR/backups"
RETENTION_DAYS=30  # Keep backups for 30 days
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
DATE_ONLY=$(date +%Y%m%d)

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

# Load environment variables
if [ -f "$APP_DIR/.env" ]; then
    export $(grep -v '^#' "$APP_DIR/.env" | xargs)
fi

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Database Backup${NC}"
echo -e "${GREEN}Started at: $(date)${NC}"
echo -e "${GREEN}========================================${NC}\n"

# Determine database type and backup accordingly
if [ -f "$APP_DIR/instance/holiday_party.db" ]; then
    # SQLite backup
    echo -e "${YELLOW}Backing up SQLite database...${NC}"
    
    BACKUP_FILE="$BACKUP_DIR/sqlite_backup_${TIMESTAMP}.db"
    cp "$APP_DIR/instance/holiday_party.db" "$BACKUP_FILE"
    
    if [ -f "$BACKUP_FILE" ]; then
        # Compress the backup
        gzip "$BACKUP_FILE"
        BACKUP_FILE="${BACKUP_FILE}.gz"
        
        SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
        echo -e "${GREEN}✓${NC} SQLite backup created: $BACKUP_FILE ($SIZE)"
    else
        echo -e "${RED}✗${NC} Failed to create SQLite backup"
        exit 1
    fi
    
elif [ ! -z "$DATABASE_URL" ] && [[ "$DATABASE_URL" == postgresql* ]]; then
    # PostgreSQL backup
    echo -e "${YELLOW}Backing up PostgreSQL database...${NC}"
    
    # Extract database name from DATABASE_URL
    DB_NAME=$(echo $DATABASE_URL | sed -n 's/.*\/\([^?]*\).*/\1/p')
    
    if [ -z "$DB_NAME" ]; then
        echo -e "${RED}✗${NC} Could not determine database name from DATABASE_URL"
        exit 1
    fi
    
    BACKUP_FILE="$BACKUP_DIR/postgres_backup_${TIMESTAMP}.sql"
    
    # Perform backup
    if pg_dump "$DB_NAME" > "$BACKUP_FILE" 2>/dev/null; then
        # Compress the backup
        gzip "$BACKUP_FILE"
        BACKUP_FILE="${BACKUP_FILE}.gz"
        
        SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
        echo -e "${GREEN}✓${NC} PostgreSQL backup created: $BACKUP_FILE ($SIZE)"
    else
        echo -e "${RED}✗${NC} Failed to create PostgreSQL backup"
        exit 1
    fi
else
    echo -e "${RED}✗${NC} No database found to backup"
    exit 1
fi

# Clean up old backups
echo -e "\n${YELLOW}Cleaning up old backups (older than $RETENTION_DAYS days)...${NC}"

DELETED_COUNT=0
while IFS= read -r old_backup; do
    rm "$old_backup"
    DELETED_COUNT=$((DELETED_COUNT + 1))
done < <(find "$BACKUP_DIR" -name "*.db.gz" -o -name "*.sql.gz" -mtime +$RETENTION_DAYS)

if [ $DELETED_COUNT -gt 0 ]; then
    echo -e "${GREEN}✓${NC} Deleted $DELETED_COUNT old backup(s)"
else
    echo -e "${GREEN}✓${NC} No old backups to delete"
fi

# Show backup statistics
echo -e "\n${YELLOW}Backup Statistics:${NC}"
TOTAL_BACKUPS=$(find "$BACKUP_DIR" -name "*.db.gz" -o -name "*.sql.gz" | wc -l)
TOTAL_SIZE=$(du -sh "$BACKUP_DIR" | cut -f1)
echo "  Total backups: $TOTAL_BACKUPS"
echo "  Total size: $TOTAL_SIZE"
echo "  Retention: $RETENTION_DAYS days"

# List recent backups
echo -e "\n${YELLOW}Recent Backups:${NC}"
find "$BACKUP_DIR" -name "*.db.gz" -o -name "*.sql.gz" | sort -r | head -5 | while read backup; do
    SIZE=$(du -h "$backup" | cut -f1)
    FILENAME=$(basename "$backup")
    echo "  $FILENAME ($SIZE)"
done

echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}Backup completed successfully!${NC}"
echo -e "${GREEN}Finished at: $(date)${NC}"
echo -e "${GREEN}========================================${NC}\n"

# Optional: Send notification (uncomment if you want email notifications)
# echo "Database backup completed successfully" | mail -s "Holiday Party Planner Backup - $DATE_ONLY" admin@example.com

