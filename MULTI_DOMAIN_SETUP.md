# AudiobookSmith Multi-Domain Setup Guide

## 🌐 Overview

This guide will help you configure your server to make both **N8N** and **AudiobookSmith Webhook** accessible through two domains:

1. **websolutionsserver.net** (your existing domain)
2. **audiobooksmith.app** (your branded domain)

Both domains will have:
- ✅ Full HTTPS/SSL encryption
- ✅ Access to N8N workflow automation
- ✅ Access to AudiobookSmith webhook for file uploads
- ✅ Automatic SSL certificate renewal

---

## 📋 Prerequisites

Before starting, ensure:

- [x] DNS for **audiobooksmith.app** points to your server IP
- [x] DNS for **www.audiobooksmith.app** points to your server IP (optional)
- [x] DNS for **websolutionsserver.net** already points to your server
- [x] You have SSH access to your server
- [x] Ports 80 and 443 are open on your firewall

### Check DNS Configuration

From your local machine:

```bash
# Get your server IP
ssh ubuntu@websolutionsserver.net 'curl -s ifconfig.me'

# Check DNS for audiobooksmith.app
dig +short audiobooksmith.app
dig +short www.audiobooksmith.app

# They should all return the same IP address
```

---

## 🚀 Quick Deployment (3 Steps)

### Step 1: Deploy Webhook Server

From this directory, run:

```bash
chmod +x smart_deploy.sh
./smart_deploy.sh websolutionsserver.net ubuntu
```

This will:
- Copy all files to your server
- Install dependencies
- Configure the webhook server
- Start the webhook service

### Step 2: Configure Nginx for Both Domains

SSH to your server:

```bash
ssh ubuntu@websolutionsserver.net
```

Copy the multi-domain Nginx configuration:

```bash
# Copy the configuration file
sudo cp ~/audiobook_webhook/nginx_multi_domain.conf /etc/nginx/sites-available/audiobooksmith

# Disable old configs (if any)
sudo rm -f /etc/nginx/sites-enabled/default
sudo rm -f /etc/nginx/sites-enabled/n8n  # if exists

# Enable the new config
sudo ln -sf /etc/nginx/sites-available/audiobooksmith /etc/nginx/sites-enabled/audiobooksmith

# Test configuration
sudo nginx -t

# Reload Nginx
sudo systemctl reload nginx
```

### Step 3: Set Up SSL for Both Domains

Still on your server, run:

```bash
cd ~/audiobook_webhook
chmod +x setup_ssl_both_domains.sh
sudo ./setup_ssl_both_domains.sh
```

This will:
- Install certbot (if needed)
- Verify DNS configuration
- Obtain SSL certificates for both domains
- Configure automatic renewal
- Update Nginx with SSL settings

---

## 🧪 Testing

After deployment, test all endpoints:

### Test N8N Access

```bash
# Via websolutionsserver.net
curl -I https://websolutionsserver.net

# Via audiobooksmith.app
curl -I https://audiobooksmith.app
```

Both should return HTTP 200 and redirect to N8N interface.

### Test Webhook Health

```bash
# Via websolutionsserver.net
curl https://websolutionsserver.net/webhook/health

# Via audiobooksmith.app
curl https://audiobooksmith.app/webhook/health
```

Expected response:
```json
{
  "status": "healthy",
  "service": "AudiobookSmith Webhook Server",
  "timestamp": "2025-12-07T20:00:00.000000"
}
```

### Test File Upload

```bash
# Via audiobooksmith.app (recommended for frontend)
curl -X POST "https://audiobooksmith.app/webhook/audiobook-process" \
  -F "email=test@example.com" \
  -F "bookTitle=Test Book" \
  -F "plan=free" \
  -F "bookFile=@test.pdf"
```

---

## 🌐 Service URLs

After setup, your services will be accessible at:

### N8N Workflow Automation

| Domain | URL |
|--------|-----|
| websolutionsserver.net | https://websolutionsserver.net |
| audiobooksmith.app | https://audiobooksmith.app |

### AudiobookSmith Webhook

| Domain | Endpoint | Purpose |
|--------|----------|---------|
| websolutionsserver.net | https://websolutionsserver.net/webhook/audiobook-process | File upload |
| websolutionsserver.net | https://websolutionsserver.net/webhook/health | Health check |
| audiobooksmith.app | https://audiobooksmith.app/webhook/audiobook-process | File upload |
| audiobooksmith.app | https://audiobooksmith.app/webhook/health | Health check |

---

## 🎨 Frontend Integration

Update your frontend code to use the branded domain:

### React Component

```javascript
// frontend_integration_code.jsx

// Use the branded domain for production
const WEBHOOK_URL = "https://audiobooksmith.app/webhook/audiobook-process";

// Or use the server domain
// const WEBHOOK_URL = "https://websolutionsserver.net/webhook/audiobook-process";
```

### HTML Form

```html
<form action="https://audiobooksmith.app/webhook/audiobook-process" 
      method="POST" 
      enctype="multipart/form-data">
  <input type="email" name="email" required>
  <input type="text" name="bookTitle" required>
  <select name="plan">
    <option value="free">Free</option>
    <option value="premium">Premium</option>
  </select>
  <input type="file" name="bookFile" accept=".pdf,.txt" required>
  <button type="submit">Upload Book</button>
</form>
```

---

## 🔧 Configuration Details

### Nginx Configuration

The multi-domain configuration (`nginx_multi_domain.conf`) includes:

1. **HTTP to HTTPS redirect** for both domains
2. **SSL/TLS configuration** with modern security settings
3. **Webhook routes** (`/webhook/*`) proxied to port 5001
4. **N8N routes** (`/`) proxied to port 5678
5. **WebSocket support** for N8N real-time features
6. **Large file upload support** (100MB max)
7. **Security headers** for enhanced protection

### SSL Certificates

Certificates are managed by Let's Encrypt:

- **websolutionsserver.net**: `/etc/letsencrypt/live/websolutionsserver.net/`
- **audiobooksmith.app**: `/etc/letsencrypt/live/audiobooksmith.app/`

Auto-renewal is configured via cron job (runs daily at 3 AM).

### Port Configuration

| Service | Port | Access |
|---------|------|--------|
| N8N | 5678 | Internal only (proxied via Nginx) |
| Webhook | 5001 | Internal only (proxied via Nginx) |
| Nginx HTTP | 80 | Public (redirects to HTTPS) |
| Nginx HTTPS | 443 | Public |

---

## 🔍 Troubleshooting

### DNS Issues

**Problem**: SSL certificate fails with "DNS not pointing to server"

**Solution**:
```bash
# Check DNS propagation
dig +short audiobooksmith.app
nslookup audiobooksmith.app

# Wait for DNS to propagate (can take up to 48 hours)
# Then run SSL setup again
sudo ~/audiobook_webhook/setup_ssl_both_domains.sh
```

### Nginx Configuration Errors

**Problem**: `nginx -t` shows errors

**Solution**:
```bash
# Check syntax
sudo nginx -t

# View detailed error
sudo nginx -T

# Check logs
sudo tail -50 /var/log/nginx/error.log
```

### SSL Certificate Issues

**Problem**: Certificate not working

**Solution**:
```bash
# Check certificate status
sudo certbot certificates

# Renew certificates manually
sudo certbot renew --force-renewal

# Reload Nginx
sudo systemctl reload nginx
```

### Webhook Not Accessible

**Problem**: 502 Bad Gateway or connection refused

**Solution**:
```bash
# Check if webhook server is running
~/audiobook_webhook/status.sh

# Start if not running
~/audiobook_webhook/start.sh

# Check logs
tail -50 ~/audiobook_webhook/logs/webhook_server.log
```

### N8N Not Accessible

**Problem**: N8N not loading

**Solution**:
```bash
# Check if N8N is running
ps aux | grep n8n

# Check N8N port
netstat -tlnp | grep 5678

# Restart N8N (depends on your setup)
# If using systemd:
sudo systemctl restart n8n

# If using PM2:
pm2 restart n8n
```

---

## 🔄 Updating Configuration

### Add Another Domain

To add more domains:

1. Update DNS to point to your server
2. Edit `/etc/nginx/sites-available/audiobooksmith`
3. Add new `server` block for the domain
4. Test: `sudo nginx -t`
5. Reload: `sudo systemctl reload nginx`
6. Get SSL: `sudo certbot --nginx -d newdomain.com`

### Change Webhook Port

If you need to change the webhook port:

1. Edit `~/audiobook_webhook/audiobook_webhook_server.py`
2. Change `port=5001` to your desired port
3. Update Nginx config to proxy to new port
4. Restart webhook: `~/audiobook_webhook/restart.sh`
5. Reload Nginx: `sudo systemctl reload nginx`

---

## 📊 Monitoring

### Check Service Status

```bash
# Webhook server
ssh ubuntu@websolutionsserver.net '~/audiobook_webhook/status.sh'

# N8N
ssh ubuntu@websolutionsserver.net 'ps aux | grep n8n'

# Nginx
ssh ubuntu@websolutionsserver.net 'sudo systemctl status nginx'
```

### View Logs

```bash
# Webhook logs
ssh ubuntu@websolutionsserver.net 'tail -f ~/audiobook_webhook/logs/webhook_server.log'

# Nginx access logs
ssh ubuntu@websolutionsserver.net 'sudo tail -f /var/log/nginx/audiobooksmith-access.log'

# Nginx error logs
ssh ubuntu@websolutionsserver.net 'sudo tail -f /var/log/nginx/audiobooksmith-error.log'
```

### SSL Certificate Expiry

```bash
# Check certificate expiry dates
ssh ubuntu@websolutionsserver.net 'sudo certbot certificates'
```

---

## 🎯 Recommended Setup

For production use, we recommend:

1. **Use audiobooksmith.app for frontend**
   - Cleaner, branded URL
   - Better for user experience
   - Easier to remember

2. **Use websolutionsserver.net for admin**
   - Keep N8N admin access on this domain
   - Easier to separate concerns

3. **Set up monitoring**
   - Monitor SSL certificate expiry
   - Monitor webhook uptime
   - Monitor disk space for uploads

---

## ✅ Post-Deployment Checklist

- [ ] Both domains resolve to server IP
- [ ] SSL certificates obtained for both domains
- [ ] Nginx configured and running
- [ ] Webhook server running
- [ ] N8N accessible via both domains
- [ ] Webhook health check returns 200
- [ ] Test file upload successful
- [ ] Frontend updated with new webhook URL
- [ ] Automatic SSL renewal configured
- [ ] Monitoring set up

---

## 🔐 Security Recommendations

1. **Add API Key Authentication**
   - Protect webhook endpoint with API keys
   - See `WEBHOOK_INTEGRATION_DOCUMENTATION.md` for details

2. **Rate Limiting**
   - Limit requests per IP to prevent abuse
   - Configure in Nginx or webhook server

3. **Firewall Rules**
   - Only allow ports 80, 443, and SSH (22)
   - Block all other incoming ports

4. **Regular Updates**
   - Keep Nginx updated
   - Keep certbot updated
   - Update webhook server code regularly

5. **Backup Configuration**
   - Backup Nginx configs regularly
   - Backup webhook code and data
   - Document any custom changes

---

## 📞 Support

If you encounter issues:

1. Check this guide's troubleshooting section
2. Review logs (webhook, Nginx, system)
3. Test each component individually
4. Verify DNS and SSL configuration

---

## 🎉 Success!

Once setup is complete, you'll have:

✅ **Two domains** accessing the same services  
✅ **Full SSL encryption** on both domains  
✅ **N8N workflow automation** accessible via both domains  
✅ **AudiobookSmith webhook** for file uploads  
✅ **Automatic SSL renewal** configured  
✅ **Production-ready** configuration  

Your users can now upload books via:
- https://audiobooksmith.app/webhook/audiobook-process
- https://websolutionsserver.net/webhook/audiobook-process

And access N8N workflows via:
- https://audiobooksmith.app
- https://websolutionsserver.net

---

**Setup Version:** 2.0.0  
**Date:** December 7, 2025  
**Status:** Multi-Domain Production Ready
