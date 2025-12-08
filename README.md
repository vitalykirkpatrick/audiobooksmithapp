# AudiobookSmith Webhook Integration - Complete Deployment Package

## 🎯 What This Package Does

This package deploys a complete webhook integration system to your **websolutionsserver.net** server, making it accessible through both:
- **websolutionsserver.net** (your existing domain)
- **audiobooksmith.app** (your branded domain)

Both domains will have full access to:
- ✅ **N8N Workflow Automation**
- ✅ **AudiobookSmith Webhook** for file uploads
- ✅ **Full HTTPS/SSL encryption**
- ✅ **Automatic SSL certificate renewal**

---

## 📦 Package Contents

### 🚀 Quick Start
- **`DEPLOY_NOW.sh`** - One-click deployment script
- **`MULTI_DOMAIN_SETUP.md`** - Complete multi-domain setup guide

### 🔧 Deployment Scripts
- **`smart_deploy.sh`** - Intelligent deployment that adapts to your server
- **`audit_server.sh`** - Audits your server configuration
- **`setup_ssl_both_domains.sh`** - Sets up SSL for both domains

### 💻 Core Components
- **`audiobook_webhook_server.py`** - Flask webhook server
- **`audiobook_processor.py`** - Book processing script
- **`frontend_integration_code.jsx`** - React component for your website

### ⚙️ Configuration Files
- **`nginx_multi_domain.conf`** - Nginx config for both domains
- **`nginx_config_template.conf`** - Alternative Nginx config
- **`deployment_config.sh`** - Deployment settings

### 📚 Documentation
- **`INTEGRATION_SUMMARY.md`** - Quick overview
- **`QUICK_START_GUIDE.md`** - Get started quickly
- **`WEBHOOK_INTEGRATION_DOCUMENTATION.md`** - Complete technical docs
- **`DEPLOYMENT_GUIDE.md`** - Detailed deployment guide
- **`DEPLOYMENT_README.md`** - Deployment instructions
- **`README.md`** - This file

---

## ⚡ Quick Deployment (5 Minutes)

### Prerequisites

1. **DNS Configuration** - Make sure these domains point to your server:
   ```bash
   audiobooksmith.app → Your Server IP
   www.audiobooksmith.app → Your Server IP
   websolutionsserver.net → Your Server IP
   ```

2. **SSH Access** - You can connect to your server:
   ```bash
   ssh ubuntu@websolutionsserver.net
   ```

### Step 1: Deploy Everything

From this directory, run:

```bash
./DEPLOY_NOW.sh
```

This will:
- Connect to your server via SSH
- Check existing installations (N8N, Nginx, Python, etc.)
- Install dependencies (Flask if needed)
- Copy all files to your server
- Configure the webhook server
- Start the webhook service

### Step 2: Configure Nginx for Both Domains

SSH to your server:

```bash
ssh ubuntu@websolutionsserver.net
```

Run the SSL setup script:

```bash
cd ~/audiobook_webhook
chmod +x setup_ssl_both_domains.sh
sudo ./setup_ssl_both_domains.sh
```

This will:
- Install/configure Nginx for both domains
- Obtain SSL certificates from Let's Encrypt
- Configure automatic SSL renewal
- Set up all routes (N8N and webhook)

### Step 3: Test

```bash
# Test webhook health
curl https://audiobooksmith.app/webhook/health
curl https://websolutionsserver.net/webhook/health

# Test N8N access
curl -I https://audiobooksmith.app
curl -I https://websolutionsserver.net
```

---

## 🌐 What You'll Get

After deployment, your services will be accessible at:

### N8N Workflow Automation
- https://audiobooksmith.app
- https://websolutionsserver.net

### AudiobookSmith Webhook
- **File Upload**: 
  - https://audiobooksmith.app/webhook/audiobook-process
  - https://websolutionsserver.net/webhook/audiobook-process

- **Health Check**:
  - https://audiobooksmith.app/webhook/health
  - https://websolutionsserver.net/webhook/health

---

## 📖 Detailed Guides

Choose the guide that fits your needs:

### For Quick Setup
1. **`MULTI_DOMAIN_SETUP.md`** - Complete multi-domain setup guide (RECOMMENDED)
2. **`QUICK_START_GUIDE.md`** - Get started in 5 minutes

### For Technical Details
3. **`WEBHOOK_INTEGRATION_DOCUMENTATION.md`** - Complete API and technical docs
4. **`DEPLOYMENT_GUIDE.md`** - Detailed deployment instructions

### For Overview
5. **`INTEGRATION_SUMMARY.md`** - Quick overview and status

---

## 🔧 Manual Deployment (Alternative)

If you prefer step-by-step control:

### 1. Audit Your Server (Optional)

```bash
./audit_server.sh
```

This shows what's already installed on your server.

### 2. Deploy Webhook

```bash
./smart_deploy.sh websolutionsserver.net ubuntu
```

### 3. Configure Nginx

```bash
ssh ubuntu@websolutionsserver.net
sudo cp ~/audiobook_webhook/nginx_multi_domain.conf /etc/nginx/sites-available/audiobooksmith
sudo ln -sf /etc/nginx/sites-available/audiobooksmith /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 4. Set Up SSL

```bash
cd ~/audiobook_webhook
sudo ./setup_ssl_both_domains.sh
```

---

## 🎨 Frontend Integration

Update your frontend code to use the webhook:

```javascript
// Use the branded domain (recommended)
const WEBHOOK_URL = "https://audiobooksmith.app/webhook/audiobook-process";

// Or use the server domain
// const WEBHOOK_URL = "https://websolutionsserver.net/webhook/audiobook-process";
```

See `frontend_integration_code.jsx` for the complete React component.

---

## 🧪 Testing Your Deployment

### Test Health Endpoint

```bash
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
curl -X POST "https://audiobooksmith.app/webhook/audiobook-process" \
  -F "email=test@example.com" \
  -F "bookTitle=Test Book" \
  -F "plan=free" \
  -F "bookFile=@test.pdf"
```

Expected response:
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

### Common Issues

**Problem**: DNS not pointing to server  
**Solution**: Wait for DNS propagation (up to 48 hours), then run SSL setup again

**Problem**: SSL certificate fails  
**Solution**: Check DNS with `dig audiobooksmith.app`, ensure it returns your server IP

**Problem**: Webhook returns 502 Bad Gateway  
**Solution**: Check if webhook server is running: `ssh ubuntu@websolutionsserver.net '~/audiobook_webhook/status.sh'`

**Problem**: N8N not accessible  
**Solution**: Check if N8N is running: `ssh ubuntu@websolutionsserver.net 'ps aux | grep n8n'`

### Get Help

1. Check the relevant documentation file
2. Review server logs: `tail -f ~/audiobook_webhook/logs/webhook_server.log`
3. Check Nginx logs: `sudo tail -f /var/log/nginx/error.log`
4. Test each component individually

---

## 📊 Server Management

### Start/Stop Webhook

```bash
# Start
ssh ubuntu@websolutionsserver.net '~/audiobook_webhook/start.sh'

# Stop
ssh ubuntu@websolutionsserver.net '~/audiobook_webhook/stop.sh'

# Status
ssh ubuntu@websolutionsserver.net '~/audiobook_webhook/status.sh'

# Restart
ssh ubuntu@websolutionsserver.net '~/audiobook_webhook/restart.sh'
```

### View Logs

```bash
# Webhook logs
ssh ubuntu@websolutionsserver.net 'tail -f ~/audiobook_webhook/logs/webhook_server.log'

# Nginx logs
ssh ubuntu@websolutionsserver.net 'sudo tail -f /var/log/nginx/audiobooksmith-access.log'
```

---

## 🔐 Security Features

✅ **HTTPS/SSL encryption** on all endpoints  
✅ **Automatic SSL certificate renewal**  
✅ **File size limits** (100MB max)  
✅ **Input validation** and sanitization  
✅ **Security headers** (X-Frame-Options, X-XSS-Protection, etc.)  
✅ **Separate logging** for monitoring  

---

## 🎯 Recommended Workflow

1. **Deploy** using `DEPLOY_NOW.sh`
2. **Configure** Nginx and SSL with `setup_ssl_both_domains.sh`
3. **Test** health endpoint and file upload
4. **Update** frontend with new webhook URL
5. **Monitor** logs for first few uploads
6. **Document** any custom changes

---

## 📞 Support Resources

### Documentation Files
- **Quick Start**: `MULTI_DOMAIN_SETUP.md`
- **Technical Details**: `WEBHOOK_INTEGRATION_DOCUMENTATION.md`
- **Deployment**: `DEPLOYMENT_GUIDE.md`

### Server Logs
- Webhook: `~/audiobook_webhook/logs/webhook_server.log`
- Nginx Access: `/var/log/nginx/audiobooksmith-access.log`
- Nginx Error: `/var/log/nginx/audiobooksmith-error.log`

### Useful Commands
```bash
# Check webhook status
ssh ubuntu@websolutionsserver.net '~/audiobook_webhook/status.sh'

# Check SSL certificates
ssh ubuntu@websolutionsserver.net 'sudo certbot certificates'

# Test Nginx config
ssh ubuntu@websolutionsserver.net 'sudo nginx -t'
```

---

## ✅ Deployment Checklist

Before deployment:
- [ ] DNS for audiobooksmith.app points to server
- [ ] DNS for www.audiobooksmith.app points to server
- [ ] SSH access to server works
- [ ] Have admin/sudo access

After deployment:
- [ ] Webhook server running
- [ ] Nginx configured for both domains
- [ ] SSL certificates obtained
- [ ] Health endpoint returns 200
- [ ] Test file upload successful
- [ ] N8N accessible via both domains
- [ ] Frontend updated with new URL

---

## 🎉 Success Criteria

You'll know everything is working when:

✅ `curl https://audiobooksmith.app/webhook/health` returns "healthy"  
✅ `curl https://websolutionsserver.net/webhook/health` returns "healthy"  
✅ You can access N8N at https://audiobooksmith.app  
✅ File upload test succeeds  
✅ SSL certificates are valid (green padlock in browser)  

---

## 🚀 Next Steps

After successful deployment:

1. **Test thoroughly** with real book files
2. **Update frontend** to use audiobooksmith.app webhook URL
3. **Monitor logs** for the first few days
4. **Set up monitoring** for uptime and errors
5. **Document** any custom configurations
6. **Consider** adding API key authentication for production

---

## 📈 What's Included

This package provides:

- ✅ **Complete webhook server** for file uploads
- ✅ **Multi-domain support** (websolutionsserver.net + audiobooksmith.app)
- ✅ **Full SSL/HTTPS** encryption
- ✅ **Nginx configuration** for both domains
- ✅ **Automatic deployment** scripts
- ✅ **Server management** scripts (start/stop/status)
- ✅ **Frontend integration** code (React)
- ✅ **Comprehensive documentation**
- ✅ **Troubleshooting guides**

---

## 🎊 Ready to Deploy!

Everything is configured and ready. Just run:

```bash
./DEPLOY_NOW.sh
```

Then follow the on-screen instructions to complete the setup.

**Estimated deployment time**: 5-10 minutes  
**Difficulty**: Easy (automated scripts handle everything)  
**Status**: Production Ready ✅

---

**Package Version**: 2.0.0  
**Date**: December 7, 2025  
**Compatibility**: Ubuntu 20.04+, Nginx, Python 3.x  
**Status**: Production Ready with Multi-Domain Support
