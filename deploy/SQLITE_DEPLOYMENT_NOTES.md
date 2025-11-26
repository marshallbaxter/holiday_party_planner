# SQLite Deployment Notes

## Overview

The Holiday Party Planner deployment has been updated to use **SQLite** as the default database instead of PostgreSQL. This makes deployment significantly simpler while still providing excellent performance for most use cases.

## Why SQLite?

### ✅ Advantages

1. **Simplicity** - No separate database server to install or manage
2. **Zero Configuration** - Works out of the box, no setup required
3. **File-Based** - Easy to backup (just copy the file)
4. **Fast** - Excellent performance for read-heavy workloads
5. **Reliable** - Battle-tested, used by millions of applications
6. **Perfect for Getting Started** - Deploy in minutes, not hours

### 📊 Performance

SQLite is suitable for:
- ✅ Small to medium deployments (up to ~100 concurrent users)
- ✅ Read-heavy workloads (typical for event management)
- ✅ Single-server deployments
- ✅ Databases up to several GB in size
- ✅ Most small business and family applications

### ⚠️ When to Consider PostgreSQL

Migrate to PostgreSQL when you need:
- Multiple application servers (load balancing)
- 100+ concurrent users
- Heavy write workloads
- Advanced database features (full-text search, JSON queries, etc.)
- Database size exceeds 1GB
- Geographic replication

## What Changed

### Files Updated

1. **`deploy/UBUNTU_DEPLOYMENT_GUIDE.md`**
   - Removed PostgreSQL installation steps (Step 2.2)
   - Updated database configuration to use SQLite
   - Updated verification commands
   - Added "Appendix A: Migrating to PostgreSQL" for future scaling

2. **`deploy/holiday-party.service`**
   - Removed PostgreSQL dependency from systemd service
   - Service now starts faster (no waiting for PostgreSQL)

3. **`deploy/config-template.env`**
   - Changed default DATABASE_URL to SQLite
   - Added comments about when to use PostgreSQL

4. **`deploy/backup-database.sh`**
   - Already supported both SQLite and PostgreSQL
   - No changes needed (automatically detects database type)

### Configuration

**SQLite Configuration (Default):**
```bash
DATABASE_URL=sqlite:///instance/holiday_party.db
```

**PostgreSQL Configuration (Optional):**
```bash
DATABASE_URL=postgresql://username:password@localhost/database_name
```

## Deployment Differences

### Simplified Steps

**Removed:**
- PostgreSQL installation (~10 minutes)
- Database user creation
- Password management for database
- Database connection testing

**Kept:**
- All other deployment steps remain the same
- Backup automation works identically
- Migration system works identically

### Time Savings

- **Before (PostgreSQL):** ~2-3 hours initial deployment
- **Now (SQLite):** ~1.5-2 hours initial deployment
- **Saved:** ~30-45 minutes on initial setup

## Database File Location

```
/home/holiday-party/app/instance/holiday_party.db
```

**Important:**
- This file contains all your data
- It's automatically backed up daily by the backup script
- File permissions are managed by the application user
- The `instance/` directory is in `.gitignore` (not committed to Git)

## Backup & Recovery

### Backup

The backup script (`deploy/backup-database.sh`) automatically:
1. Detects SQLite database
2. Copies the database file
3. Compresses it with gzip
4. Stores in `/home/holiday-party/app/backups/`
5. Keeps last 30 days of backups

**Manual Backup:**
```bash
# Simple file copy
sudo -u holiday-party cp /home/holiday-party/app/instance/holiday_party.db \
    /home/holiday-party/app/backups/manual_backup_$(date +%Y%m%d).db
```

### Recovery

**Restore from Backup:**
```bash
# Stop application
sudo systemctl stop holiday-party

# Restore backup
sudo -u holiday-party gunzip -c /home/holiday-party/app/backups/sqlite_backup_TIMESTAMP.db.gz > \
    /home/holiday-party/app/instance/holiday_party.db

# Restart application
sudo systemctl start holiday-party
```

## Monitoring

### Check Database Size

```bash
ls -lh /home/holiday-party/app/instance/holiday_party.db
```

### Query Database

```bash
# Count users
sqlite3 /home/holiday-party/app/instance/holiday_party.db "SELECT COUNT(*) FROM persons;"

# List tables
sqlite3 /home/holiday-party/app/instance/holiday_party.db ".tables"

# Database info
sqlite3 /home/holiday-party/app/instance/holiday_party.db ".dbinfo"
```

### Check Database Integrity

```bash
sqlite3 /home/holiday-party/app/instance/holiday_party.db "PRAGMA integrity_check;"
# Should return: ok
```

## Migration Path

When you're ready to scale up, see **Appendix A** in the deployment guide for step-by-step instructions on migrating to PostgreSQL.

The migration process:
1. Export data from SQLite
2. Install and configure PostgreSQL
3. Import data to PostgreSQL
4. Update configuration
5. Test and verify

**Estimated Time:** 30-45 minutes

## Troubleshooting

### Database Locked Error

If you see "database is locked" errors:

```bash
# Check for processes using the database
sudo lsof /home/holiday-party/app/instance/holiday_party.db

# Restart the application
sudo systemctl restart holiday-party
```

### Database Corrupted

```bash
# Try to recover
sqlite3 /home/holiday-party/app/instance/holiday_party.db ".recover" | \
    sqlite3 /home/holiday-party/app/instance/holiday_party_recovered.db

# If recovery works, replace the database
sudo systemctl stop holiday-party
sudo -u holiday-party mv /home/holiday-party/app/instance/holiday_party.db \
    /home/holiday-party/app/instance/holiday_party.db.corrupted
sudo -u holiday-party mv /home/holiday-party/app/instance/holiday_party_recovered.db \
    /home/holiday-party/app/instance/holiday_party.db
sudo systemctl start holiday-party
```

## Best Practices

1. **Regular Backups** - The automated daily backup is enabled by default
2. **Monitor Size** - Check database size monthly
3. **Test Backups** - Verify backups can be restored
4. **Plan for Growth** - Monitor concurrent users and performance
5. **Migrate When Needed** - Don't wait until you have problems

## Summary

✅ **Simpler deployment** - No database server to manage
✅ **Faster setup** - Save 30-45 minutes on initial deployment
✅ **Same features** - All application features work identically
✅ **Easy backups** - Simple file-based backups
✅ **Migration path** - Can upgrade to PostgreSQL when needed

**SQLite is the perfect choice for getting started with Holiday Party Planner!**

