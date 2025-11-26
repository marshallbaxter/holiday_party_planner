# Deployment Quick Start Guide

This guide provides a streamlined process for deploying the Holiday Party Planner application.

## Prerequisites

- Ubuntu 20.04+ or Debian 11+ server
- Root/sudo access
- Domain name pointed to your server
- GitHub repository set up

## Initial Deployment (One-Time Setup)

### 1. Prepare Your Repository

On your local machine:

```bash
# Ensure all changes are committed
git add .
git commit -m "Prepare for deployment"
git push origin main
```

### 2. Run Server Setup Script

On your server (as root or with sudo):

```bash
# Download the setup script
wget https://raw.githubusercontent.com/yourusername/holiday_party_planner/main/deploy/setup-server.sh

# Make it executable
chmod +x setup-server.sh

# Run the setup
sudo bash setup-server.sh
```

The script will prompt you for:
- GitHub repository URL
- Domain name

It will automatically:
- Install all dependencies (Python, PostgreSQL, Nginx, etc.)
- Create application user and directories
- Set up PostgreSQL database
- Clone your repository
- Create Python virtual environment
- Generate secure SECRET_KEY
- Configure systemd service
- Configure Nginx
- Set up firewall

### 3. Configure Brevo Email

Edit the `.env` file with your Brevo credentials:

```bash
sudo -u holiday-party nano /home/holiday-party/app/.env
```

Update these lines:
```
BREVO_API_KEY=your-actual-brevo-api-key
BREVO_SENDER_EMAIL=noreply@yourdomain.com
MAIL_USERNAME=your-brevo-username
MAIL_PASSWORD=your-brevo-smtp-key
```

Restart the service:
```bash
sudo systemctl restart holiday-party
```

### 4. Set Up SSL Certificate

```bash
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
```

Follow the prompts. Certbot will automatically:
- Obtain SSL certificate
- Configure Nginx for HTTPS
- Set up auto-renewal

### 5. Create Admin Account

```bash
sudo -u holiday-party bash -c 'cd /home/holiday-party/app && source venv/bin/activate && flask create-admin'
```

Follow the prompts to create your first admin account.

### 6. Set Up Automated Backups

```bash
# Make backup script executable
sudo chmod +x /home/holiday-party/app/deploy/backup-database.sh

# Edit crontab for the app user
sudo -u holiday-party crontab -e

# Add this line (runs daily at 2 AM):
0 2 * * * /home/holiday-party/app/deploy/backup-database.sh
```

### 7. Verify Deployment

Visit your domain in a browser:
```
https://yourdomain.com
```

You should see the Holiday Party Planner homepage.

## Subsequent Deployments

After initial setup, deploying updates is simple:

### On Your Local Machine

```bash
# Make your changes
git add .
git commit -m "Description of changes"
git push origin main
```

### On Your Server

```bash
# SSH to your server
ssh your-server

# Navigate to app directory
cd /home/holiday-party/app

# Run deployment script
./deploy/deploy.sh
```

The deployment script will:
1. Backup the database
2. Pull latest code
3. Update dependencies
4. Run database migrations
5. Run tests
6. Restart the service

## Common Commands

### Service Management

```bash
# Check service status
sudo systemctl status holiday-party

# Start service
sudo systemctl start holiday-party

# Stop service
sudo systemctl stop holiday-party

# Restart service
sudo systemctl restart holiday-party

# View service logs
sudo journalctl -u holiday-party -f
```

### Application Management

```bash
# Create admin account
sudo -u holiday-party bash -c 'cd /home/holiday-party/app && source venv/bin/activate && flask create-admin'

# Access Flask shell
sudo -u holiday-party bash -c 'cd /home/holiday-party/app && source venv/bin/activate && flask shell'

# Run database migrations manually
sudo -u holiday-party bash -c 'cd /home/holiday-party/app && source venv/bin/activate && flask db upgrade'

# Backup database manually
sudo -u holiday-party /home/holiday-party/app/deploy/backup-database.sh
```

### Nginx Management

```bash
# Test Nginx configuration
sudo nginx -t

# Reload Nginx
sudo systemctl reload nginx

# Restart Nginx
sudo systemctl restart nginx

# View Nginx error logs
sudo tail -f /var/log/nginx/holiday-party-error.log
```

## Troubleshooting

### Service Won't Start

```bash
# Check detailed logs
sudo journalctl -u holiday-party -n 100 --no-pager

# Check if socket exists
ls -la /run/holiday-party/

# Verify .env file
sudo -u holiday-party cat /home/holiday-party/app/.env
```

### Database Issues

```bash
# Check database connection
sudo -u holiday-party bash -c 'cd /home/holiday-party/app && source venv/bin/activate && flask shell'
>>> from app import db
>>> db.engine.execute('SELECT 1').scalar()
```

### Permission Issues

```bash
# Fix ownership
sudo chown -R holiday-party:holiday-party /home/holiday-party/app

# Fix .env permissions
sudo chmod 600 /home/holiday-party/app/.env
```

## Security Checklist

- [ ] SSL certificate installed and auto-renewal enabled
- [ ] Firewall configured (UFW)
- [ ] Strong SECRET_KEY generated
- [ ] Database password is strong and secure
- [ ] .env file has correct permissions (600)
- [ ] Fail2ban is running
- [ ] Regular backups are scheduled
- [ ] System packages are up to date

## Support

For detailed documentation, see `deploy/README.md` and the main project documentation.

