# Remote Deployment to Your Server

## 🎯 Problem Solved

I cannot connect directly to your server from this sandbox due to network/authentication restrictions. However, I've created a solution that will work from your local machine.

## 🚀 Quick Deploy (2 Steps)

### Step 1: Download and Extract

Download the deployment package and extract it:

```bash
tar -xzf audiobooksmith_deployment_final.tar.gz
cd audiobooksmith_deployment_final
```

### Step 2: Run Remote Deployment

```bash
./deploy_to_server.sh
```

This script will:
1. ✅ Test SSH connection to your server
2. ✅ Upload all deployment files to `/root/audiobooksmith_deployment`
3. ✅ Make scripts executable
4. ✅ Execute `deploy_with_backup.sh` on your server
5. ✅ Complete the full deployment automatically

## 🔐 Authentication Options

### Option 1: Password Authentication (Default)

The script uses the password you provided:
```bash
./deploy_to_server.sh
```

### Option 2: SSH Key Authentication

If you have SSH key access configured:
```bash
./deploy_to_server.sh --use-key
```

## 📋 What Gets Deployed

The script uploads to `/root/audiobooksmith_deployment/`:
- All deployment scripts (*.sh)
- Python files (*.py)
- Configuration files (*.conf)
- Frontend code (*.jsx)
- Documentation (*.md, *.txt)

Then executes `deploy_with_backup.sh` which:
- Creates backup of existing installation
- Installs dependencies
- Configures webhook server
- Starts services
- Tests installation

## 🛠️ Troubleshooting

### Problem: SSH connection fails

**Try manual SSH first:**
```bash
ssh root@172.245.67.47
```

If this works, the script should work too.

### Problem: sshpass not found

**Install sshpass:**
```bash
# Ubuntu/Debian
sudo apt-get install sshpass

# macOS
brew install hudochenkov/sshpass/sshpass
```

### Problem: Password authentication disabled

**Use SSH key instead:**
```bash
./deploy_to_server.sh --use-key
```

### Problem: Permission denied

**Check if root login is allowed:**
```bash
ssh root@172.245.67.47 "cat /etc/ssh/sshd_config | grep PermitRootLogin"
```

If it shows "no", you may need to:
1. Use a different user account
2. Enable root login temporarily
3. Use SSH key authentication

## 📊 Deployment Process

```
Your Local Machine
       ↓
  [deploy_to_server.sh]
       ↓
   Upload files via SCP
       ↓
172.245.67.47:/root/audiobooksmith_deployment/
       ↓
  Execute deploy_with_backup.sh
       ↓
   [7 Phase Deployment]
       ↓
  /root/audiobook_webhook/ (installed)
```

## ✅ After Deployment

Once the script completes, configure SSL:

```bash
ssh root@172.245.67.47
cd /root/audiobook_webhook
./setup_ssl_both_domains.sh
```

Then test:
```bash
curl https://audiobooksmith.app/webhook/health
```

## 🔧 Manual Deployment (Alternative)

If the automated script doesn't work, you can deploy manually:

### 1. Upload files manually
```bash
scp -r audiobooksmith_deployment_final root@172.245.67.47:/root/audiobooksmith_deployment
```

### 2. SSH to server
```bash
ssh root@172.245.67.47
```

### 3. Run deployment
```bash
cd /root/audiobooksmith_deployment
chmod +x *.sh
./deploy_with_backup.sh
```

## 📞 Quick Reference

```bash
# Deploy from local machine
./deploy_to_server.sh

# Or with SSH key
./deploy_to_server.sh --use-key

# Check deployment status (after deployment)
ssh root@172.245.67.47 '/root/audiobook_webhook/status.sh'

# View logs
ssh root@172.245.67.47 'tail -f /root/audiobook_webhook/logs/webhook_server.log'
```

## 🎉 Success Indicators

You'll know it worked when:
- ✅ Script shows "Remote Deployment Complete!"
- ✅ Files are in `/root/audiobooksmith_deployment/`
- ✅ Webhook is in `/root/audiobook_webhook/`
- ✅ Backup created in `/root/audiobook_webhook_backup_*/`
- ✅ Server status shows "Running"

---

**Ready to deploy?** Run: `./deploy_to_server.sh`
