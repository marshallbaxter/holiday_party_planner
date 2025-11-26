# Deployment Configuration

This directory contains all the necessary files for deploying the Holiday Party Planner application to a production server.

## Files

- **deploy.sh** - Main deployment script for updating the application
- **holiday-party.service** - Systemd service configuration
- **nginx-config** - Nginx web server configuration
- **setup-server.sh** - Initial server setup script (one-time use)
- **backup-database.sh** - Database backup script for cron jobs

## Quick Start

### 1. Initial Server Setup

Before first deployment, you need to set up your server. See the main deployment documentation for detailed instructions.

### 2. Configure Deployment Script

Edit `deploy.sh` and update these variables:

```bash
APP_DIR="/home/holiday-party/app"
REPO_URL="https://github.com/yourusername/holiday_party_planner.git"
SERVICE_NAME="holiday-party"
BRANCH="main"
```

### 3. Configure Systemd Service

Edit `holiday-party.service` and update:
- User and Group
- WorkingDirectory paths
- EnvironmentFile path
- ExecStart paths

Then install:

```bash
sudo cp deploy/holiday-party.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable holiday-party
sudo systemctl start holiday-party
```

### 4. Configure Nginx

Edit `nginx-config` and update:
- server_name (your domain)
- All file paths

Then install:

```bash
sudo cp deploy/nginx-config /etc/nginx/sites-available/holiday-party
sudo ln -s /etc/nginx/sites-available/holiday-party /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 5. Set Up SSL

```bash
sudo certbot --nginx -d your-domain.com -d www.your-domain.com
```

### 6. Deploy Updates

After initial setup, deploy updates with:

```bash
cd /path/to/holiday_party_planner
./deploy/deploy.sh
```

## Deployment Workflow

1. **Local Development:**
   ```bash
   git add .
   git commit -m "Your changes"
   git push origin main
   ```

2. **Server Deployment:**
   ```bash
   ssh your-server
   cd /path/to/app
   ./deploy/deploy.sh
   ```

The deployment script will:
- Backup the database
- Pull latest code from GitHub
- Install/update dependencies
- Run database migrations
- Run tests (optional)
- Restart the application service

## Monitoring

### View Logs

```bash
# Application logs
tail -f /path/to/app/logs/app.log

# Gunicorn logs
tail -f /path/to/app/logs/error.log

# Systemd service logs
sudo journalctl -u holiday-party -f

# Nginx logs
sudo tail -f /var/log/nginx/holiday-party-error.log
```

### Check Service Status

```bash
sudo systemctl status holiday-party
```

### Restart Service

```bash
sudo systemctl restart holiday-party
```

## Troubleshooting

### Service won't start

```bash
# Check logs
sudo journalctl -u holiday-party -n 50

# Check if socket file exists
ls -la /run/holiday-party/

# Check permissions
sudo systemctl status holiday-party
```

### Database migration fails

```bash
# Check current migration status
flask db current

# Try manual migration
flask db upgrade

# Rollback if needed
flask db downgrade
```

### Nginx errors

```bash
# Test configuration
sudo nginx -t

# Check error logs
sudo tail -f /var/log/nginx/holiday-party-error.log

# Restart nginx
sudo systemctl restart nginx
```

## Security Notes

- Never commit `.env` files to Git
- Keep `.env` file permissions at 600
- Use strong passwords for database and SECRET_KEY
- Keep SSL certificates up to date (certbot auto-renews)
- Regularly update system packages and Python dependencies
- Monitor logs for suspicious activity

## Backup and Recovery

### Manual Database Backup

```bash
# SQLite
cp instance/holiday_party.db backups/backup_$(date +%Y%m%d).db

# PostgreSQL
pg_dump holiday_party_prod > backups/backup_$(date +%Y%m%d).sql
```

### Restore from Backup

```bash
# SQLite
cp backups/backup_YYYYMMDD.db instance/holiday_party.db
sudo systemctl restart holiday-party

# PostgreSQL
psql holiday_party_prod < backups/backup_YYYYMMDD.sql
sudo systemctl restart holiday-party
```

## Support

For detailed deployment documentation, see the main project documentation.

