# Cloudflare Tunnel Deployment Guide

## Overview

Using **Cloudflare Tunnel** (formerly Argo Tunnel) is an excellent alternative to traditional SSL/TLS setup. It provides:

- ✅ **Automatic SSL/TLS** - No need for Let's Encrypt
- ✅ **No Port Forwarding** - No need to open ports 80/443
- ✅ **DDoS Protection** - Built-in Cloudflare protection
- ✅ **Simpler Firewall** - Only SSH port needs to be open
- ✅ **Free Tier Available** - No cost for basic usage
- ✅ **No Public IP Required** - Works behind NAT/firewall

## Prerequisites

- [ ] Domain registered and using Cloudflare nameservers
- [ ] Cloudflare account (free tier is fine)
- [ ] Ubuntu server with SSH access
- [ ] Application deployed (follow main deployment guide)

## Architecture Comparison

### Traditional Setup (Let's Encrypt)
```
Internet → Your Server IP:443 (Nginx + SSL) → Application
```

### Cloudflare Tunnel Setup
```
Internet → Cloudflare Edge → Encrypted Tunnel → Your Server (HTTP) → Application
```

**Key Difference:** SSL/TLS terminates at Cloudflare's edge, not your server.

---

## Deployment Changes

### What to SKIP from Main Guide

When using Cloudflare Tunnel, **SKIP these sections** from the main deployment guide:

- ❌ **Step 2.4:** Install Certbot - Not needed
- ❌ **Step 4.3:** Obtain SSL Certificate - Not needed
- ❌ **Step 4.4:** Test Auto-Renewal - Not needed
- ❌ **Firewall ports 80/443** - Not needed (only SSH)

### What to KEEP

Everything else remains the same:
- ✅ Python installation
- ✅ Application setup
- ✅ Nginx installation (but simpler config)
- ✅ Database setup
- ✅ All application configuration

---

## Step-by-Step Setup

### Step 1: Install Cloudflared

```bash
# Add Cloudflare GPG key
sudo mkdir -p --mode=0755 /usr/share/keyrings
curl -fsSL https://pkg.cloudflare.com/cloudflare-main.gpg | sudo tee /usr/share/keyrings/cloudflare-main.gpg >/dev/null

# Add Cloudflare repository
echo "deb [signed-by=/usr/share/keyrings/cloudflare-main.gpg] https://pkg.cloudflare.com/cloudflared $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/cloudflared.list

# Update and install
sudo apt update
sudo apt install -y cloudflared

# Verify installation
cloudflared --version
```

**Expected Output:** `cloudflared version 2024.x.x`

### Step 2: Authenticate with Cloudflare

```bash
# Login to Cloudflare (this will open a browser)
cloudflared tunnel login
```

**What happens:**
1. A browser window opens
2. Log in to your Cloudflare account
3. Select the domain you want to use
4. Authorization certificate is saved to `~/.cloudflared/cert.pem`

**Expected Output:** `You have successfully logged in.`

### Step 3: Create a Tunnel

```bash
# Create a tunnel (replace YOUR_TUNNEL_NAME with something like "holiday-party")
cloudflared tunnel create YOUR_TUNNEL_NAME

# Note the Tunnel ID that's displayed - you'll need it
```

**Expected Output:**
```
Tunnel credentials written to /root/.cloudflared/TUNNEL_ID.json
Created tunnel YOUR_TUNNEL_NAME with id TUNNEL_ID
```

**📝 SAVE THIS:**
- Tunnel ID: `TUNNEL_ID`
- Tunnel Name: `YOUR_TUNNEL_NAME`

### Step 4: Configure the Tunnel

Create the tunnel configuration file:

```bash
sudo mkdir -p /etc/cloudflared
sudo nano /etc/cloudflared/config.yml
```

**Add this configuration:**

```yaml
# Tunnel ID from Step 3
tunnel: TUNNEL_ID

# Credentials file location
credentials-file: /root/.cloudflared/TUNNEL_ID.json

# Ingress rules - route traffic to your application
ingress:
  # Route your domain to the local application
  - hostname: YOUR_DOMAIN_COM
    service: http://localhost:80
  
  # Optional: Route www subdomain
  - hostname: www.YOUR_DOMAIN_COM
    service: http://localhost:80
  
  # Catch-all rule (required)
  - service: http_status:404
```

**⚠️ REPLACE:**
- `TUNNEL_ID` - Your actual tunnel ID from Step 3
- `YOUR_DOMAIN_COM` - Your actual domain (e.g., party.example.com)

**Save and exit:** `Ctrl+X`, `Y`, `Enter`

### Step 5: Configure DNS in Cloudflare

```bash
# Route your domain through the tunnel
cloudflared tunnel route dns YOUR_TUNNEL_NAME YOUR_DOMAIN_COM

# If you want www subdomain:
cloudflared tunnel route dns YOUR_TUNNEL_NAME www.YOUR_DOMAIN_COM
```

**Expected Output:** `Created CNAME record for YOUR_DOMAIN_COM`

**Verification:**
- Go to Cloudflare Dashboard → DNS
- You should see a CNAME record pointing to `TUNNEL_ID.cfargotunnel.com`

### Step 6: Configure Nginx for HTTP Only

Since Cloudflare handles SSL, Nginx only needs to serve HTTP:

```bash
sudo nano /etc/nginx/sites-available/holiday-party
```

**Replace the entire file with this simpler configuration:**

```nginx
# Cloudflare Tunnel - HTTP Only Configuration
# SSL/TLS is handled by Cloudflare

server {
    listen 80;
    listen [::]:80;
    server_name YOUR_DOMAIN_COM www.YOUR_DOMAIN_COM;
    
    # Logging
    access_log /var/log/nginx/holiday-party-access.log;
    error_log /var/log/nginx/holiday-party-error.log;
    
    # Max upload size
    client_max_body_size 10M;
    client_body_buffer_size 128k;
    
    # Timeouts
    client_body_timeout 12;
    client_header_timeout 12;
    keepalive_timeout 15;
    send_timeout 10;
    
    # Root directory
    root /home/holiday-party/app;
    
    # Static files
    location /static {
        alias /home/holiday-party/app/app/static;
        expires 30d;
        add_header Cache-Control "public, immutable";
        access_log off;
    }
    
    # Favicon
    location = /favicon.ico {
        alias /home/holiday-party/app/app/static/favicon.ico;
        access_log off;
        log_not_found off;
    }
    
    # Health check endpoint
    location = /api/health {
        proxy_pass http://unix:/run/holiday-party/holiday-party.sock;
        access_log off;
    }
    
    # All application requests
    location / {
        proxy_pass http://unix:/run/holiday-party/holiday-party.sock;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto https;  # Tell app it's HTTPS
        proxy_redirect off;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}
```

**⚠️ REPLACE:** `YOUR_DOMAIN_COM` with your actual domain

**Save and test:**
```bash
sudo nginx -t
sudo systemctl reload nginx
```

### Step 7: Install Tunnel as a Service

```bash
# Install the tunnel as a system service
sudo cloudflared service install

# Start the tunnel
sudo systemctl start cloudflared

# Enable on boot
sudo systemctl enable cloudflared

# Check status
sudo systemctl status cloudflared
```

**Expected Output:** Should show "active (running)" in green

### Step 8: Update Application Configuration

```bash
# Edit .env file
sudo -u holiday-party nano /home/holiday-party/app/.env
```

**Update APP_URL to use https:**
```bash
APP_URL=https://YOUR_DOMAIN_COM
```

**Save and restart application:**
```bash
sudo systemctl restart holiday-party
```

### Step 9: Configure Firewall (Simplified)

With Cloudflare Tunnel, you only need SSH open:

```bash
# Allow SSH only
sudo ufw allow OpenSSH

# Enable firewall
sudo ufw --force enable

# Check status
sudo ufw status
```

**Expected Output:**
```
Status: active

To                         Action      From
--                         ------      ----
OpenSSH                    ALLOW       Anywhere
```

**Note:** Ports 80 and 443 do NOT need to be open to the internet!

---

## Verification

### Test Your Deployment

1. **Visit your domain:**
   ```
   https://YOUR_DOMAIN_COM
   ```
   Should load with HTTPS (green padlock)

2. **Check SSL certificate:**
   - Click the padlock in browser
   - Should show "Cloudflare Inc ECC CA-3" or similar
   - Valid and trusted automatically

3. **Test from different locations:**
   - Use your phone (not on same network)
   - Use https://www.whatsmyip.org/ to check from different locations

4. **Check tunnel status:**
   ```bash
   sudo systemctl status cloudflared
   cloudflared tunnel info YOUR_TUNNEL_NAME
   ```

---

## Monitoring & Management

### Check Tunnel Status

```bash
# Service status
sudo systemctl status cloudflared

# View logs
sudo journalctl -u cloudflared -f

# List tunnels
cloudflared tunnel list

# Tunnel info
cloudflared tunnel info YOUR_TUNNEL_NAME
```

### Cloudflare Dashboard

Visit: https://one.dash.cloudflare.com/

Navigate to: **Zero Trust → Networks → Tunnels**

You'll see:
- Tunnel status (active/inactive)
- Traffic metrics
- Connection health
- Configuration

---

## Troubleshooting

### Tunnel Not Connecting

```bash
# Check cloudflared logs
sudo journalctl -u cloudflared -n 50

# Common issues:
# 1. Wrong tunnel ID in config.yml
# 2. Credentials file not found
# 3. DNS not configured in Cloudflare
```

### Site Not Loading

```bash
# Check if tunnel is running
sudo systemctl status cloudflared

# Check if application is running
sudo systemctl status holiday-party

# Check Nginx
sudo systemctl status nginx

# Check Nginx logs
sudo tail -50 /var/log/nginx/holiday-party-error.log
```

### DNS Not Resolving

```bash
# Check DNS from your machine
nslookup YOUR_DOMAIN_COM

# Should show Cloudflare IPs (104.x.x.x or 172.x.x.x)
# NOT your server's IP
```

---

## Advantages of Cloudflare Tunnel

### Security
- ✅ No ports exposed to internet (except SSH)
- ✅ DDoS protection included
- ✅ Web Application Firewall (WAF) available
- ✅ Automatic SSL/TLS management
- ✅ Protection against common attacks

### Simplicity
- ✅ No Let's Encrypt setup
- ✅ No certificate renewal
- ✅ No port forwarding
- ✅ Works behind NAT/firewall
- ✅ No public IP required

### Performance
- ✅ Cloudflare's global CDN
- ✅ Automatic caching
- ✅ HTTP/2 and HTTP/3 support
- ✅ Brotli compression

### Cost
- ✅ Free tier available
- ✅ No bandwidth charges
- ✅ No certificate costs

---

## Cloudflare Dashboard Features

### Available Features (Free Tier)

1. **Analytics**
   - Traffic metrics
   - Bandwidth usage
   - Request counts

2. **Security**
   - Firewall rules
   - Rate limiting
   - Bot protection

3. **Performance**
   - Caching rules
   - Page rules
   - Auto minification

4. **Access Control**
   - IP allowlist/blocklist
   - Geographic restrictions
   - User agent filtering

---

## Maintenance

### Daily
- Automatic - tunnel reconnects if needed

### Weekly
```bash
# Check tunnel status
sudo systemctl status cloudflared
```

### Monthly
```bash
# Update cloudflared
sudo apt update
sudo apt upgrade cloudflared

# Restart tunnel
sudo systemctl restart cloudflared
```

---

## Comparison: Let's Encrypt vs Cloudflare Tunnel

| Feature | Let's Encrypt | Cloudflare Tunnel |
|---------|---------------|-------------------|
| SSL/TLS | ✅ Yes | ✅ Yes (automatic) |
| Cost | Free | Free |
| Setup Time | 15 minutes | 10 minutes |
| Renewal | Auto (90 days) | N/A (managed) |
| Ports Required | 80, 443 | None |
| DDoS Protection | ❌ No | ✅ Yes |
| CDN | ❌ No | ✅ Yes |
| WAF | ❌ No | ✅ Yes (paid) |
| Works Behind NAT | ❌ No | ✅ Yes |

---

## Summary

✅ **Simpler Setup** - No SSL certificates to manage
✅ **Better Security** - No exposed ports, DDoS protection
✅ **Better Performance** - Cloudflare's global CDN
✅ **Zero Cost** - Free tier is sufficient
✅ **Less Maintenance** - No certificate renewals

**Cloudflare Tunnel is the recommended approach for most deployments!**

---

## Next Steps

1. ✅ Complete main deployment guide (skip SSL sections)
2. ✅ Follow this guide to set up Cloudflare Tunnel
3. ✅ Test your deployment
4. ✅ Configure Cloudflare security features (optional)
5. ✅ Set up monitoring and alerts

**Your Holiday Party Planner is now securely accessible via Cloudflare Tunnel!** 🎉

