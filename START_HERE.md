# AudiobookSmith Webhook Deployment - START HERE

## 🎯 Quick Info

**Your Server:**
- **IP Address:** 172.245.67.47
- **Domain:** websolutionsserver.net
- **Username:** root
- **Password:** Chernivtsi_23

**Additional Domain:** audiobooksmith.app (will be configured)

---

## ⚡ Super Quick Deployment (2 Commands)

### Step 1: Deploy Everything

```bash
chmod +x deploy_with_password.sh
./deploy_with_password.sh
```

This will automatically:
- ✅ Connect to your server (172.245.67.47)
- ✅ Check existing installations
- ✅ Install dependencies (Flask, Nginx if needed)
- ✅ Copy all files
- ✅ Configure the webhook server
- ✅ Start the webhook service

### Step 2: Configure SSL for Both Domains

After deployment completes, SSH to your server and run:

```bash
ssh root@172.245.67.47
cd /root/audiobook_webhook
./setup_ssl_both_domains.sh
```

This will:
- ✅ Configure Nginx for both domains
- ✅ Obtain SSL certificates (Let's Encrypt)
- ✅ Set up automatic renewal
- ✅ Make webhook accessible via HTTPS

---

## 🌐 What You'll Get

After deployment, your services will be accessible at:

### N8N Workflow Automation
- https://websolutionsserver.net
- https://audiobooksmith.app

### AudiobookSmith Webhook
- https://websolutionsserver.net/webhook/audiobook-process
- https://audiobooksmith.app/webhook/audiobook-process

### Health Check
- https://websolutionsserver.net/webhook/health
- https://audiobooksmith.app/webhook/health

---

## 📋 Prerequisites

Before running the deployment:

1. **DNS Configuration** - Make sure these domains point to 172.245.67.47:
   - audiobooksmith.app → 172.245.67.47
   - www.audiobooksmith.app → 172.245.67.47
   - websolutionsserver.net → 172.245.67.47

2. **Check DNS** (optional but recommended):
   ```bash
   dig +short audiobooksmith.app
   dig +short websolutionsserver.net
   # Both should return: 172.245.67.47
   ```

3. **Install sshpass** (if not already installed):
   ```bash
   # On Ubuntu/Debian
   sudo apt-get install sshpass
   
   # On macOS
   brew install hudochenkov/sshpass/sshpass
   ```

---

## 🚀 Deployment Options

### Option 1: Automated Deployment with Password (Recommended)

```bash
./deploy_with_password.sh
```

This script uses the saved password and deploys everything automatically.

### Option 2: Manual SSH Deployment

```bash
./smart_deploy.sh 172.245.67.47 root
```

You'll be prompted for the password during deployment.

### Option 3: One-Click Deployment

```bash
./DEPLOY_NOW.sh
```

Simplified version that prompts for confirmation.

---

## 🧪 Testing After Deployment

### Test Webhook Health

```bash
# Internal test (from server)
ssh root@172.245.67.47 'curl http://localhost:5001/health'

# External test (after SSL setup)
curl https://audiobooksmith.app/webhook/health
curl https://websolutionsserver.net/webhook/health
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
curl -X POST "https://audiobooksmith.app/webhook/audiobook-process" \
  -F "email=test@example.com" \
  -F "bookTitle=Test Book" \
  -F "plan=free" \
  -F "bookFile=@test.pdf"
```

---

## 🔧 Server Management

Once deployed, manage the webhook server with these commands:

### Check Status
```bash
ssh root@172.245.67.47 '/root/audiobook_webhook/status.sh'
```

### Start Server
```bash
ssh root@172.245.67.47 '/root/audiobook_webhook/start.sh'
```

### Stop Server
```bash
ssh root@172.245.67.47 '/root/audiobook_webhook/stop.sh'
```

### Restart Server
```bash
ssh root@172.245.67.47 '/root/audiobook_webhook/restart.sh'
```

### View Logs
```bash
ssh root@172.245.67.47 'tail -f /root/audiobook_webhook/logs/webhook_server.log'
```

---

## 📚 Documentation Files

- **`START_HERE.md`** - This file (quick start guide)
- **`MULTI_DOMAIN_SETUP.md`** - Complete multi-domain setup guide
- **`README.md`** - Full package documentation
- **`WEBHOOK_INTEGRATION_DOCUMENTATION.md`** - Technical API docs
- **`DEPLOYMENT_GUIDE.md`** - Detailed deployment instructions

---

## 🎨 Frontend Integration

After deployment, update your frontend code:

```javascript
// Use the branded domain (recommended)
const WEBHOOK_URL = "https://audiobooksmith.app/webhook/audiobook-process";

// Or use the server domain
// const WEBHOOK_URL = "https://websolutionsserver.net/webhook/audiobook-process";
```

See `frontend_integration_code.jsx` for the complete React component.

---

## 🔍 Troubleshooting

### Problem: sshpass not found

**Solution:**
```bash
sudo apt-get install sshpass
```

### Problem: SSH connection fails

**Solution:**
```bash
# Test SSH manually
ssh root@172.245.67.47
# Enter password: Chernivtsi_23
```

### Problem: DNS not pointing to server

**Solution:**
```bash
# Check DNS
dig +short audiobooksmith.app
# Should return: 172.245.67.47

# If not, update DNS and wait for propagation (up to 48 hours)
```

### Problem: SSL certificate fails

**Solution:**
- Ensure DNS is pointing to your server
- Wait for DNS propagation
- Run SSL setup again: `./setup_ssl_both_domains.sh`

---

## ✅ Deployment Checklist

- [ ] DNS for audiobooksmith.app points to 172.245.67.47
- [ ] DNS for www.audiobooksmith.app points to 172.245.67.47
- [ ] sshpass installed (for automated deployment)
- [ ] Run `./deploy_with_password.sh`
- [ ] SSH to server and run `./setup_ssl_both_domains.sh`
- [ ] Test health endpoint
- [ ] Test file upload
- [ ] Update frontend webhook URL

---

## 🎉 Success Criteria

You'll know everything is working when:

✅ `curl https://audiobooksmith.app/webhook/health` returns "healthy"  
✅ `curl https://websolutionsserver.net/webhook/health` returns "healthy"  
✅ You can access N8N at https://audiobooksmith.app  
✅ File upload test succeeds  
✅ SSL certificates are valid (green padlock in browser)  

---

## 📞 Quick Commands Reference

```bash
# Deploy everything
./deploy_with_password.sh

# SSH to server
ssh root@172.245.67.47

# Configure SSL (run on server)
cd /root/audiobook_webhook && ./setup_ssl_both_domains.sh

# Check webhook status
ssh root@172.245.67.47 '/root/audiobook_webhook/status.sh'

# View logs
ssh root@172.245.67.47 'tail -f /root/audiobook_webhook/logs/webhook_server.log'

# Test webhook
curl https://audiobooksmith.app/webhook/health
```

---

## 🚀 Ready to Deploy!

Just run:

```bash
./deploy_with_password.sh
```

Then follow the on-screen instructions!

**Estimated time:** 5-10 minutes  
**Difficulty:** Easy (fully automated)  
**Status:** Production Ready ✅

---

**Package Version:** 2.1.0 (Customized for 172.245.67.47)  
**Date:** December 7, 2025  
**Server:** 172.245.67.47 (websolutionsserver.net)  
**Domains:** websolutionsserver.net + audiobooksmith.app
