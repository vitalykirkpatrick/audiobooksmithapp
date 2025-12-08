# AudiobookSmith Disaster Recovery Guide

**Version**: 1.0.0  
**Last Updated**: December 2025  
**Maintainer**: Vitaly Kirkpatrick

---

## Overview

This document provides step-by-step instructions for recovering the AudiobookSmith backend system in case of:

- Server failure or data loss
- Accidental file deletion
- Configuration corruption
- Need to migrate to a new server

All code and configurations are stored in the GitHub repository: **vitalykirkpatrick/audiobooksmithapp**

---

## Quick Recovery (5 Minutes)

If you need to restore the system immediately, run the automated restoration script:

```bash
# SSH into your server
ssh root@audiobooksmith.app

# Download and run the restoration script
curl -fsSL https://raw.githubusercontent.com/vitalykirkpatrick/audiobooksmithapp/main/restore_audiobooksmith.sh | bash
```

This will:
1. ✅ Backup existing files
2. ✅ Install dependencies
3. ✅ Clone latest code from GitHub
4. ✅ Install Python packages
5. ✅ Copy files to `/root/`
6. ✅ Verify installation

---

## Manual Recovery (Step-by-Step)

If you prefer manual control or the automated script fails, follow these steps:

### 1. Backup Existing Files

```bash
# Create backup directory
mkdir -p /root/backup_$(date +%Y%m%d_%H%M%S)

# Backup Python files
cp /root/*.py /root/backup_*/ 2>/dev/null || true

# Backup .env file
cp /root/.env /root/backup_*/ 2>/dev/null || true
```

### 2. Install Dependencies

```bash
# Update system
apt-get update

# Install Git
apt-get install -y git

# Install Python and pip
apt-get install -y python3 python3-pip

# Install GitHub CLI (optional but recommended)
type -p curl >/dev/null || (apt update && apt install curl -y)
curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg
chmod go+r /usr/share/keyrings/githubcli-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | tee /etc/apt/sources.list.d/github-cli.list > /dev/null
apt update && apt install gh -y
```

### 3. Clone Repository

```bash
# Clone to temporary directory
cd /tmp
git clone https://github.com/vitalykirkpatrick/audiobooksmithapp.git

# Or use GitHub CLI
gh repo clone vitalykirkpatrick/audiobooksmithapp
```

### 4. Install Python Dependencies

```bash
pip3 install --upgrade pip
pip3 install openai flask beautifulsoup4 striprtf mobi PyPDF2 ebooklib python-docx
```

### 5. Copy Files

```bash
# Copy all Python files
cp /tmp/audiobooksmithapp/*.py /root/

# Copy documentation
cp /tmp/audiobooksmithapp/*.md /root/

# Set permissions
chmod +x /root/*.py
```

### 6. Restore Environment Variables

```bash
# If .env was backed up
cp /root/backup_*/.env /root/.env

# Or create new .env file
cat > /root/.env << 'EOF'
OPENAI_API_KEY=your_key_here
ELEVENLABS_API_KEY=your_key_here
SLACK_WEBHOOK_URL=your_webhook_here
EOF

# Edit with actual values
nano /root/.env
```

### 7. Start Services

```bash
# Load environment variables
source /root/.env

# Start webhook server
cd /root
nohup python3 audiobook_webhook_server_v7_with_voices.py > webhook.log 2>&1 &

# Verify it's running
ps aux | grep audiobook_webhook
curl http://localhost:5001/webhook/health
```

---

## File Inventory

### Core Backend Files

| File | Purpose | Critical? |
|------|---------|-----------|
| `audiobook_webhook_server_v7_with_voices.py` | Main webhook server | ✅ Yes |
| `audiobook_processor_v8_universal_formats.py` | Book processing engine | ✅ Yes |
| `universal_text_extractor.py` | Multi-format text extraction | ✅ Yes |
| `narration_preparation_processor.py` | Narration prep phase | ✅ Yes |
| `audiobooksmith_integration.py` | Pipeline integration | ✅ Yes |
| `progress_tracker.py` | Progress tracking | ✅ Yes |
| `elevenlabs_voice_recommender.py` | Voice recommendations | ⚠️ Optional |

### Configuration Files

| File | Purpose | Critical? |
|------|---------|-----------|
| `.env` | API keys and secrets | ✅ Yes |
| `webhook.log` | Server logs | ℹ️ Info |

### Documentation Files

| File | Purpose |
|------|---------|
| `NARRATION_PREPARATION_README.md` | Narration prep guide |
| `DISASTER_RECOVERY.md` | This file |
| `restore_audiobooksmith.sh` | Automated restoration script |

---

## Environment Variables Required

```bash
# Required
OPENAI_API_KEY=sk-proj-...        # For AI processing
ELEVENLABS_API_KEY=sk_...         # For voice recommendations

# Optional
SLACK_WEBHOOK_URL=https://...     # For notifications
ANTHROPIC_API_KEY=sk-ant-...      # Alternative AI provider
PERPLEXITY_API_KEY=pplx-...       # For research features
```

---

## Verification Checklist

After restoration, verify the following:

- [ ] All Python files present in `/root/`
- [ ] `.env` file configured with API keys
- [ ] Python dependencies installed (`pip3 list | grep openai`)
- [ ] Webhook server starts without errors
- [ ] Health endpoint responds: `curl http://localhost:5001/webhook/health`
- [ ] Test upload works: Upload a PDF through the frontend
- [ ] Logs are being written: `tail -f /root/webhook.log`

---

## Common Issues & Solutions

### Issue: "ModuleNotFoundError: No module named 'openai'"

**Solution:**
```bash
pip3 install openai
```

### Issue: "Permission denied" when running scripts

**Solution:**
```bash
chmod +x /root/*.py
```

### Issue: Webhook server won't start

**Solution:**
```bash
# Check if port 5001 is already in use
lsof -i :5001

# Kill existing process
kill -9 $(lsof -t -i:5001)

# Restart server
cd /root && source .env && python3 audiobook_webhook_server_v7_with_voices.py
```

### Issue: "OPENAI_API_KEY not set"

**Solution:**
```bash
# Ensure .env file exists and is sourced
cat /root/.env
source /root/.env
echo $OPENAI_API_KEY  # Should print your key
```

---

## Migration to New Server

To migrate to a completely new server:

1. **On new server:**
   ```bash
   curl -fsSL https://raw.githubusercontent.com/vitalykirkpatrick/audiobooksmithapp/main/restore_audiobooksmith.sh | bash
   ```

2. **Copy .env file from old server:**
   ```bash
   scp root@old-server:/root/.env /root/.env
   ```

3. **Update DNS:**
   - Point `audiobooksmith.app` to new server IP
   - Wait for DNS propagation (up to 48 hours)

4. **Verify:**
   - Test webhook endpoint
   - Upload a sample book
   - Check logs for errors

---

## Backup Strategy

### Automated Backups

Set up a daily backup cron job:

```bash
# Add to crontab
crontab -e

# Add this line (runs daily at 2 AM)
0 2 * * * /root/backup_script.sh
```

**backup_script.sh:**
```bash
#!/bin/bash
BACKUP_DIR="/root/backups/$(date +%Y%m%d)"
mkdir -p "$BACKUP_DIR"
cp /root/*.py "$BACKUP_DIR/"
cp /root/.env "$BACKUP_DIR/"
tar -czf "$BACKUP_DIR.tar.gz" "$BACKUP_DIR"
rm -rf "$BACKUP_DIR"
# Keep only last 7 days
find /root/backups/ -name "*.tar.gz" -mtime +7 -delete
```

### Manual Backup

```bash
# Create backup
tar -czf /root/audiobooksmith_backup_$(date +%Y%m%d).tar.gz /root/*.py /root/.env

# Download to local machine
scp root@audiobooksmith.app:/root/audiobooksmith_backup_*.tar.gz ./
```

---

## Emergency Contacts

- **GitHub Repository**: https://github.com/vitalykirkpatrick/audiobooksmithapp
- **Server**: audiobooksmith.app
- **Frontend**: https://audiobooksmith.com

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | Dec 2025 | Initial disaster recovery documentation |

---

**Remember**: Always keep your `.env` file backed up securely and never commit it to GitHub!
