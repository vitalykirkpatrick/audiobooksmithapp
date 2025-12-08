# AudiobookSmith Webhook - Deployment Instructions

## 🎯 Quick Deploy (Choose One Method)

### Method 1: Deploy with Automatic Backup (RECOMMENDED) ⭐

This method creates a backup before deployment and can automatically rollback if anything fails.

```bash
chmod +x deploy_with_backup.sh
./deploy_with_backup.sh
```

**Features:**
- ✅ Automatic backup before deployment
- ✅ Automatic rollback on failure
- ✅ Error handling with retries
- ✅ Complete installation and testing
- ✅ Creates restore script

### Method 2: Simple Deploy with Password

Basic deployment without backup (faster but no rollback).

```bash
chmod +x deploy_with_password.sh
./deploy_with_password.sh
```

### Method 3: One-Click Deploy

Simplified deployment with prompts.

```bash
chmod +x DEPLOY_NOW.sh
./DEPLOY_NOW.sh
```

---

## 📋 What Each Script Does

### deploy_with_backup.sh (RECOMMENDED)

**7 Phases:**
1. ✅ Check prerequisites (install sshpass if needed)
2. ✅ Test SSH connection
3. ✅ **Create backup of existing installation**
4. ✅ Audit server (check Python, Flask, Nginx, ports)
5. ✅ Install dependencies and configure
6. ✅ Start webhook server
7. ✅ Test installation

**Backup Features:**
- Creates timestamped backup: `/root/audiobook_webhook_backup_YYYYMMDD_HHMMSS/`
- Includes restore script for easy rollback
- Automatic rollback if deployment fails
- Preserves all existing configurations

**Error Handling:**
- Retries failed operations (up to 3 times)
- Logs all operations to `deployment.log`
- Automatic rollback on critical errors
- Detailed error messages

### deploy_with_password.sh

**12 Steps:**
- Basic deployment without backup
- Faster execution
- Good for first-time installation
- No rollback capability

### DEPLOY_NOW.sh

**Simple wrapper:**
- Calls smart_deploy.sh
- Interactive prompts
- Good for manual control

---

## 🚀 Recommended Deployment Process

### Step 1: Deploy with Backup

```bash
./deploy_with_backup.sh
```

**What happens:**
- Connects to 172.245.67.47
- Creates backup if installation exists
- Installs all dependencies
- Configures webhook server
- Starts the service
- Tests the installation

**Time:** 3-5 minutes

### Step 2: Configure SSL (Run on Server)

After deployment, SSH to your server and run:

```bash
ssh root@172.245.67.47
cd /root/audiobook_webhook
./setup_ssl_both_domains.sh
```

**What happens:**
- Configures Nginx for both domains
- Obtains SSL certificates from Let's Encrypt
- Sets up automatic renewal
- Makes webhook accessible via HTTPS

**Time:** 2-3 minutes

### Step 3: Test

```bash
curl https://audiobooksmith.app/webhook/health
curl https://websolutionsserver.net/webhook/health
```

**Expected response:**
```json
{
  "status": "healthy",
  "service": "AudiobookSmith Webhook Server",
  "timestamp": "2025-12-07T21:00:00.000000"
}
```

---

## 🛡️ Backup & Restore

### Backup Location

Backups are stored at:
```
/root/audiobook_webhook_backup_YYYYMMDD_HHMMSS/
```

### Restore from Backup

If something goes wrong, restore the previous version:

```bash
ssh root@172.245.67.47
/root/audiobook_webhook_backup_*/restore.sh
```

This will:
- Stop current webhook server
- Remove current installation
- Restore from backup
- Restart previous version

### Manual Backup

Create a manual backup anytime:

```bash
ssh root@172.245.67.47
BACKUP_DIR="/root/audiobook_webhook_backup_manual_$(date +%Y%m%d_%H%M%S)"
cp -r /root/audiobook_webhook "$BACKUP_DIR"
echo "Backup created: $BACKUP_DIR"
```

---

## 🔍 Troubleshooting

### Problem: sshpass not found

**Solution:**
```bash
# Ubuntu/Debian
sudo apt-get install sshpass

# macOS
brew install hudochenkov/sshpass/sshpass
```

### Problem: SSH connection fails

**Solution:**
```bash
# Test SSH manually
ssh root@172.245.67.47
# Password: Chernivtsi_23

# Check if server is reachable
ping 172.245.67.47
```

### Problem: Deployment fails

**Solution:**
The script will automatically rollback to the previous version. Check `deployment.log` for details:

```bash
cat deployment.log
```

### Problem: Port already in use

**Solution:**
The script automatically finds an available port (5001, 5002, or 5003). If all are in use, manually stop other services:

```bash
ssh root@172.245.67.47
netstat -tlnp | grep 500
# Kill the process using the port
kill <PID>
```

### Problem: Flask not installing

**Solution:**
```bash
ssh root@172.245.67.47
pip3 install --upgrade pip
pip3 install flask
```

---

## 📊 Deployment Logs

### View Deployment Log

```bash
cat deployment.log
```

### View Webhook Server Logs

```bash
ssh root@172.245.67.47 'tail -f /root/audiobook_webhook/logs/webhook_server.log'
```

### View Nginx Logs

```bash
ssh root@172.245.67.47 'tail -f /var/log/nginx/error.log'
```

---

## 🔧 Server Management

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
ssh root@172.245.67.47 'cd /root/audiobook_webhook && ./stop.sh && sleep 2 && ./start.sh'
```

---

## ✅ Deployment Checklist

Before deployment:
- [ ] DNS for audiobooksmith.app points to 172.245.67.47
- [ ] DNS for websolutionsserver.net points to 172.245.67.47
- [ ] sshpass installed on local machine
- [ ] Can SSH to server: `ssh root@172.245.67.47`

After deployment:
- [ ] Webhook server running
- [ ] Health endpoint responds: `curl http://172.245.67.47:5001/health`
- [ ] SSL configured: `./setup_ssl_both_domains.sh`
- [ ] HTTPS working: `curl https://audiobooksmith.app/webhook/health`
- [ ] Frontend updated with new URL

---

## 🎉 Success Criteria

You'll know deployment succeeded when:

✅ Deployment script shows "Deployment Completed Successfully"  
✅ `deployment.log` shows no critical errors  
✅ Webhook health check returns "healthy"  
✅ Backup created in `/root/audiobook_webhook_backup_*/`  
✅ Server status shows "Running"  

---

## 📞 Quick Reference

```bash
# Deploy with backup (recommended)
./deploy_with_backup.sh

# Configure SSL (run on server)
ssh root@172.245.67.47 'cd /root/audiobook_webhook && ./setup_ssl_both_domains.sh'

# Test webhook
curl https://audiobooksmith.app/webhook/health

# Check status
ssh root@172.245.67.47 '/root/audiobook_webhook/status.sh'

# View logs
ssh root@172.245.67.47 'tail -f /root/audiobook_webhook/logs/webhook_server.log'

# Restore from backup
ssh root@172.245.67.47 '/root/audiobook_webhook_backup_*/restore.sh'
```

---

## 🌐 Final URLs

After SSL configuration, your services will be at:

**N8N:**
- https://websolutionsserver.net
- https://audiobooksmith.app

**Webhook:**
- https://websolutionsserver.net/webhook/audiobook-process
- https://audiobooksmith.app/webhook/audiobook-process

**Health Check:**
- https://websolutionsserver.net/webhook/health
- https://audiobooksmith.app/webhook/health

---

**Ready to deploy?** Run: `./deploy_with_backup.sh`

**Package Version:** 2.2.0 (With Backup Integration)  
**Date:** December 7, 2025  
**Server:** 172.245.67.47 (websolutionsserver.net)
