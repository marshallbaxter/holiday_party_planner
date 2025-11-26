# Deployment Checklist

Use this checklist to ensure a smooth deployment of the Holiday Party Planner application.

## Pre-Deployment Checklist

### Local Development

- [ ] All features tested locally
- [ ] All tests passing (`pytest`)
- [ ] Database migrations created and tested
- [ ] Code reviewed and approved
- [ ] Dependencies updated in `requirements.txt`
- [ ] `.env.example` updated with any new variables
- [ ] Documentation updated
- [ ] Committed all changes to Git
- [ ] Pushed to GitHub repository

### Server Preparation

- [ ] Server meets minimum requirements (Ubuntu 20.04+, 2GB RAM, 20GB disk)
- [ ] Domain name configured and DNS pointing to server
- [ ] SSH access configured
- [ ] Sudo/root access available
- [ ] Brevo account created and API key obtained
- [ ] Sender email verified in Brevo

## Initial Deployment Checklist

### 1. Server Setup

- [ ] Run `setup-server.sh` script
- [ ] Verify all dependencies installed
- [ ] PostgreSQL database created
- [ ] Application user created
- [ ] Repository cloned
- [ ] Virtual environment created
- [ ] `.env` file created with secure values

### 2. Configuration

- [ ] Update `.env` with Brevo API credentials
- [ ] Verify `SECRET_KEY` is strong and unique
- [ ] Set correct `APP_URL` (domain name)
- [ ] Configure `SUPPORT_EMAIL`
- [ ] Review and adjust feature flags
- [ ] Set appropriate `LOG_LEVEL`

### 3. Database

- [ ] Database migrations applied (`flask db upgrade`)
- [ ] Database connection tested
- [ ] Admin account created (`flask create-admin`)
- [ ] Test login with admin account

### 4. Web Server

- [ ] Nginx configuration installed
- [ ] Nginx configuration tested (`nginx -t`)
- [ ] SSL certificate obtained (Let's Encrypt)
- [ ] HTTPS working correctly
- [ ] HTTP redirects to HTTPS
- [ ] Static files serving correctly

### 5. Application Service

- [ ] Systemd service installed
- [ ] Service enabled (`systemctl enable holiday-party`)
- [ ] Service started (`systemctl start holiday-party`)
- [ ] Service status is active
- [ ] Application accessible via domain
- [ ] No errors in service logs

### 6. Security

- [ ] Firewall configured (UFW)
- [ ] Only necessary ports open (80, 443, 22)
- [ ] Fail2ban installed and running
- [ ] `.env` file permissions set to 600
- [ ] Application runs as non-root user
- [ ] SSL certificate auto-renewal configured
- [ ] Security headers configured in Nginx

### 7. Monitoring & Backups

- [ ] Automated database backups configured (cron)
- [ ] Backup script tested
- [ ] Log rotation configured
- [ ] Health check endpoint accessible (`/api/health`)
- [ ] Error logging working
- [ ] Access logs being written

### 8. Testing

- [ ] Homepage loads correctly
- [ ] Admin login works
- [ ] Can create an event
- [ ] Email sending works (test invitation)
- [ ] RSVP flow works
- [ ] All major features functional
- [ ] Mobile responsive design works
- [ ] No console errors in browser

## Subsequent Deployment Checklist

### Before Deployment

- [ ] All changes committed and pushed to GitHub
- [ ] Tests passing locally
- [ ] Database migrations created if needed
- [ ] Breaking changes documented
- [ ] Deployment window scheduled (if needed)
- [ ] Stakeholders notified (if needed)

### During Deployment

- [ ] SSH to server
- [ ] Navigate to app directory
- [ ] Run `./deploy/deploy.sh`
- [ ] Monitor deployment output
- [ ] Verify no errors during deployment
- [ ] Check service restarted successfully

### After Deployment

- [ ] Application accessible
- [ ] No errors in logs
- [ ] New features working as expected
- [ ] Database migrations applied successfully
- [ ] Email functionality still working
- [ ] Performance acceptable
- [ ] No broken links or 404 errors

## Rollback Checklist

If deployment fails and you need to rollback:

- [ ] Stop the service: `sudo systemctl stop holiday-party`
- [ ] Checkout previous Git commit: `git checkout <previous-commit>`
- [ ] Rollback database if needed: `flask db downgrade`
- [ ] Restore database from backup if needed
- [ ] Restart service: `sudo systemctl start holiday-party`
- [ ] Verify application working
- [ ] Document what went wrong
- [ ] Fix issues before next deployment

## Post-Deployment Monitoring

### First Hour

- [ ] Monitor error logs: `sudo journalctl -u holiday-party -f`
- [ ] Check application logs: `tail -f logs/app.log`
- [ ] Monitor Nginx logs: `tail -f /var/log/nginx/holiday-party-error.log`
- [ ] Test critical user flows
- [ ] Monitor server resources (CPU, memory, disk)

### First Day

- [ ] Review error logs for any issues
- [ ] Check email delivery success rate
- [ ] Monitor user activity
- [ ] Verify scheduled tasks running
- [ ] Check backup completion

### First Week

- [ ] Review performance metrics
- [ ] Check for any user-reported issues
- [ ] Verify SSL certificate status
- [ ] Review security logs
- [ ] Confirm backups are working

## Emergency Contacts

Document your emergency contacts and procedures:

- **Server Provider:** ___________________________
- **Domain Registrar:** ___________________________
- **Email Service (Brevo):** ___________________________
- **On-Call Developer:** ___________________________
- **Backup Developer:** ___________________________

## Useful Commands Reference

```bash
# Service management
sudo systemctl status holiday-party
sudo systemctl restart holiday-party
sudo journalctl -u holiday-party -f

# Application management
cd /home/holiday-party/app
source venv/bin/activate
flask shell
flask create-admin

# Database
flask db current
flask db upgrade
flask db downgrade

# Logs
tail -f logs/app.log
tail -f logs/error.log
sudo tail -f /var/log/nginx/holiday-party-error.log

# Backups
./deploy/backup-database.sh
ls -lh backups/

# Deployment
./deploy/deploy.sh
```

## Notes

- Keep this checklist updated as your deployment process evolves
- Document any custom procedures specific to your setup
- Review and improve the checklist after each deployment
- Share lessons learned with your team

