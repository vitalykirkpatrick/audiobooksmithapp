# AudiobookSmith Webhook - Deployment to websolutionsserver.net

## 🎯 Overview

This package contains everything needed to deploy the AudiobookSmith webhook integration to your websolutionsserver.net server, which already has N8N running.

## 📦 What's Included

### Deployment Scripts
1. **`audit_server.sh`** - Audits your server to check existing installations
2. **`smart_deploy.sh`** - Intelligently deploys webhook integration
3. **`setup_nginx_ssl.sh`** - Configures Nginx and SSL (run on server)

### Core Components
4. **`audiobook_webhook_server.py`** - Flask webhook server
5. **`audiobook_processor.py`** - Book processing script
6. **`frontend_integration_code.jsx`** - React component for your website

### Documentation
7. **`INTEGRATION_SUMMARY.md`** - Quick overview
8. **`QUICK_START_GUIDE.md`** - Get started quickly
9. **`WEBHOOK_INTEGRATION_DOCUMENTATION.md`** - Complete technical docs
10. **`DEPLOYMENT_GUIDE.md`** - Detailed deployment guide
11. **`DEPLOYMENT_README.md`** - This file

### Configuration
12. **`nginx_config_template.conf`** - Nginx configuration template
13. **`deployment_config.sh`** - Deployment settings

---

## 🚀 Quick Deployment (3 Steps)

### Step 1: Run Smart Deployment Script

From this sandbox or your local machine:

```bash
./smart_deploy.sh websolutionsserver.net ubuntu
```

This will:
- ✅ Check your server configuration
- ✅ Adapt to existing N8N setup
- ✅ Find available port (5001, 5002, etc.)
- ✅ Copy all files
- ✅ Install dependencies (Flask if needed)
- ✅ Configure paths
- ✅ Start webhook server

### Step 2: Configure Nginx

SSH to your server:

```bash
ssh ubuntu@websolutionsserver.net
```

Add webhook routes to your existing Nginx configuration:

```bash
# Edit your Nginx config (likely the same one used for N8N)
sudo nano /etc/nginx/sites-available/default
# or
sudo nano /etc/nginx/sites-available/n8n
```

Add these location blocks inside your existing `server` block:

```nginx
# AudiobookSmith Webhook
location /webhook/audiobook-process {
    proxy_pass http://127.0.0.1:5001/webhook/audiobook-process;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    
    client_max_body_size 100M;
    proxy_connect_timeout 300s;
    proxy_send_timeout 300s;
    proxy_read_timeout 300s;
}

location /webhook/health {
    proxy_pass http://127.0.0.1:5001/health;
    proxy_set_header Host $host;
    access_log off;
}
```

Test and reload Nginx:

```bash
sudo nginx -t
sudo systemctl reload nginx
```

### Step 3: Test the Integration

```bash
# Test health endpoint
curl https://websolutionsserver.net/webhook/health

# Test file upload
curl -X POST "https://websolutionsserver.net/webhook/audiobook-process" \
  -F "email=test@example.com" \
  -F "bookTitle=Test Book" \
  -F "plan=free" \
  -F "bookFile=@test.pdf"
```

---

## 📋 Detailed Deployment Steps

### Option A: Automatic Deployment (Recommended)

1. **Make scripts executable:**
   ```bash
   chmod +x audit_server.sh smart_deploy.sh
   ```

2. **Run audit (optional but recommended):**
   ```bash
   ./audit_server.sh
   ```
   This will show you what's already installed on your server.

3. **Run smart deployment:**
   ```bash
   ./smart_deploy.sh websolutionsserver.net ubuntu
   ```
   
   The script will:
   - Connect via SSH
   - Check existing installations
   - Find available port
   - Copy files
   - Configure everything
   - Start the server

4. **Configure Nginx** (see Step 2 above)

5. **Test** (see Step 3 above)

### Option B: Manual Deployment

If you prefer manual control:

1. **SSH to your server:**
   ```bash
   ssh ubuntu@websolutionsserver.net
   ```

2. **Create directory:**
   ```bash
   mkdir -p ~/audiobook_webhook/{logs,uploads,backups}
   ```

3. **Copy files from this sandbox:**
   ```bash
   # From your local machine or this sandbox
   scp audiobook_webhook_server.py ubuntu@websolutionsserver.net:~/audiobook_webhook/
   scp audiobook_processor.py ubuntu@websolutionsserver.net:~/audiobook_webhook/
   scp *.md ubuntu@websolutionsserver.net:~/audiobook_webhook/
   ```

4. **On the server, configure:**
   ```bash
   cd ~/audiobook_webhook
   
   # Update paths
   sed -i 's|/home/ubuntu/audiobook_uploads|'$HOME'/audiobook_webhook/uploads|g' audiobook_webhook_server.py
   sed -i 's|/home/ubuntu/audiobook_processor.py|'$HOME'/audiobook_webhook/audiobook_processor.py|g' audiobook_webhook_server.py
   
   # Make executable
   chmod +x audiobook_webhook_server.py audiobook_processor.py
   
   # Install Flask if needed
   pip3 install flask
   ```

5. **Start the server:**
   ```bash
   cd ~/audiobook_webhook
   nohup python3 audiobook_webhook_server.py > logs/webhook_server.log 2>&1 &
   echo $! > webhook_server.pid
   ```

6. **Configure Nginx** (see Step 2 in Quick Deployment)

---

## 🔧 Server Management

Once deployed, you can manage the webhook server with these commands:

### Start Server
```bash
ssh ubuntu@websolutionsserver.net '~/audiobook_webhook/start.sh'
```

### Stop Server
```bash
ssh ubuntu@websolutionsserver.net '~/audiobook_webhook/stop.sh'
```

### Check Status
```bash
ssh ubuntu@websolutionsserver.net '~/audiobook_webhook/status.sh'
```

### Restart Server
```bash
ssh ubuntu@websolutionsserver.net '~/audiobook_webhook/restart.sh'
```

### View Logs
```bash
ssh ubuntu@websolutionsserver.net 'tail -f ~/audiobook_webhook/logs/webhook_server.log'
```

---

## 🌐 Nginx Integration

Since your server already has N8N running with Nginx and SSL, you just need to add the webhook routes to your existing configuration.

### Find Your Nginx Config

Your N8N config is likely in one of these locations:
```bash
/etc/nginx/sites-available/default
/etc/nginx/sites-available/n8n
/etc/nginx/conf.d/n8n.conf
```

### Add Webhook Routes

Add the location blocks from `nginx_config_template.conf` to your existing server block.

**Example:** If your N8N config looks like this:

```nginx
server {
    listen 443 ssl http2;
    server_name websolutionsserver.net;
    
    # SSL certificates
    ssl_certificate /etc/letsencrypt/live/websolutionsserver.net/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/websolutionsserver.net/privkey.pem;
    
    # N8N location
    location / {
        proxy_pass http://127.0.0.1:5678;
        # ... proxy settings
    }
}
```

**Add webhook locations:**

```nginx
server {
    listen 443 ssl http2;
    server_name websolutionsserver.net;
    
    # SSL certificates
    ssl_certificate /etc/letsencrypt/live/websolutionsserver.net/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/websolutionsserver.net/privkey.pem;
    
    # N8N location
    location / {
        proxy_pass http://127.0.0.1:5678;
        # ... proxy settings
    }
    
    # AudiobookSmith Webhook (ADD THIS)
    location /webhook/audiobook-process {
        proxy_pass http://127.0.0.1:5001/webhook/audiobook-process;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        client_max_body_size 100M;
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
    }
    
    location /webhook/health {
        proxy_pass http://127.0.0.1:5001/health;
        proxy_set_header Host $host;
        access_log off;
    }
}
```

---

## 🧪 Testing

### 1. Test Health Endpoint

```bash
# Internal (from server)
curl http://localhost:5001/health

# External (through Nginx)
curl https://websolutionsserver.net/webhook/health
```

**Expected response:**
```json
{
  "status": "healthy",
  "service": "AudiobookSmith Webhook Server",
  "timestamp": "2025-12-07T20:00:00.000000"
}
```

### 2. Test File Upload

```bash
curl -X POST "https://websolutionsserver.net/webhook/audiobook-process" \
  -F "email=test@example.com" \
  -F "bookTitle=Test Book" \
  -F "plan=free" \
  -F "bookFile=@/path/to/test.pdf"
```

**Expected response:**
```json
{
  "success": true,
  "message": "Audiobook processed successfully",
  "data": {
    "output": {
      "audiobook_id": "ab_20251207200000",
      "status": "ready_for_processing"
    }
  }
}
```

---

## 🔍 Troubleshooting

### Webhook Server Not Starting

**Check logs:**
```bash
tail -50 ~/audiobook_webhook/logs/webhook_server.log
```

**Common issues:**
- Port already in use: Change port in `audiobook_webhook_server.py`
- Flask not installed: `pip3 install flask`
- Permission denied: `chmod +x audiobook_webhook_server.py`

### Nginx 502 Bad Gateway

**Check if webhook server is running:**
```bash
~/audiobook_webhook/status.sh
```

**Check Nginx error log:**
```bash
sudo tail -50 /var/log/nginx/error.log
```

**Verify proxy_pass port matches webhook server port**

### File Upload Fails

**Check file size limit:**
- Nginx: `client_max_body_size 100M;`
- Webhook server: `MAX_FILE_SIZE = 100 * 1024 * 1024`

**Check disk space:**
```bash
df -h ~/audiobook_webhook/uploads
```

### SSL Certificate Issues

Your SSL is already configured for N8N, so webhook will use the same certificate. No additional SSL setup needed!

---

## 📊 Monitoring

### Check Server Status
```bash
ssh ubuntu@websolutionsserver.net '~/audiobook_webhook/status.sh'
```

### View Recent Logs
```bash
ssh ubuntu@websolutionsserver.net 'tail -50 ~/audiobook_webhook/logs/webhook_server.log'
```

### Check Uploaded Files
```bash
ssh ubuntu@websolutionsserver.net 'ls -lh ~/audiobook_webhook/uploads/'
```

### Monitor in Real-Time
```bash
ssh ubuntu@websolutionsserver.net 'tail -f ~/audiobook_webhook/logs/webhook_server.log'
```

---

## 🔄 Updates

To update the webhook server:

1. **Stop the server:**
   ```bash
   ssh ubuntu@websolutionsserver.net '~/audiobook_webhook/stop.sh'
   ```

2. **Backup current version:**
   ```bash
   ssh ubuntu@websolutionsserver.net 'cp ~/audiobook_webhook/audiobook_webhook_server.py ~/audiobook_webhook/backups/audiobook_webhook_server_$(date +%Y%m%d).py'
   ```

3. **Copy new version:**
   ```bash
   scp audiobook_webhook_server.py ubuntu@websolutionsserver.net:~/audiobook_webhook/
   ```

4. **Start the server:**
   ```bash
   ssh ubuntu@websolutionsserver.net '~/audiobook_webhook/start.sh'
   ```

---

## 🎯 Frontend Integration

Once the webhook is deployed and tested, update your frontend code:

```javascript
// Update webhook URL in frontend_integration_code.jsx
const WEBHOOK_URL = "https://websolutionsserver.net/webhook/audiobook-process";
```

Then integrate the React component into your audiobooksmith.com website.

---

## ✅ Deployment Checklist

- [ ] Run `smart_deploy.sh` to deploy to server
- [ ] Verify webhook server is running (`status.sh`)
- [ ] Add Nginx location blocks to existing config
- [ ] Test Nginx configuration (`sudo nginx -t`)
- [ ] Reload Nginx (`sudo systemctl reload nginx`)
- [ ] Test health endpoint
- [ ] Test file upload with small PDF
- [ ] Update frontend webhook URL
- [ ] Test from website
- [ ] Monitor logs for first few uploads
- [ ] Set up automated cleanup of old files (optional)

---

## 📞 Support

If you encounter issues:

1. **Check logs:** `tail -f ~/audiobook_webhook/logs/webhook_server.log`
2. **Check status:** `~/audiobook_webhook/status.sh`
3. **Check Nginx:** `sudo nginx -t` and `sudo systemctl status nginx`
4. **Review documentation:** See other .md files in this package

---

## 🎉 Success!

Once deployed, your webhook will be accessible at:
- **Health Check:** `https://websolutionsserver.net/webhook/health`
- **File Upload:** `https://websolutionsserver.net/webhook/audiobook-process`

The webhook server runs alongside your existing N8N installation without conflicts!

---

**Deployment Package Version:** 1.0.0  
**Date:** December 7, 2025  
**Status:** Production Ready
