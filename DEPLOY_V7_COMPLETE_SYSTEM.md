# AudiobookSmith V7 - Complete Deployment Guide

## 🎯 What V7 Fixes

### Current Issues (Old System - V3)
- ❌ Author: "Unknown"
- ❌ Genre: "Unknown"  
- ❌ Chapters: 0 detected (should be 46)
- ❌ Title: Just the filename
- ❌ No voice recommendations
- ❌ Simple flat folder structure
- ❌ Accepts invalid documents (templates, guides)

### After V7 Deployment
- ✅ Author: Detected by AI ("Vitaly Magidov")
- ✅ Genre: Detected by AI ("Memoir")
- ✅ Chapters: All 46 chapters with titles
- ✅ Title: Actual book title detected
- ✅ 5 AI-recommended voices with samples
- ✅ Session-based versioning folder structure
- ✅ Strict validation (rejects templates/guides)

---

## 📦 Files to Deploy

### 1. Core Processing Files
```
elevenlabs_voice_recommender.py          # Voice recommendation engine
audiobook_processor_v7_with_voices.py    # Main processor with AI + voices
audiobook_webhook_server_v7_with_voices.py  # Webhook server
analysis_page_template_v3_with_voices.html  # HTML template
```

### 2. Environment Variables Needed
```bash
ELEVENLABS_API_KEY=<your_elevenlabs_api_key>
SLACK_WEBHOOK_URL=<your_slack_webhook_url>
OPENAI_API_KEY=(already set on server)
```

---

## 🚀 Deployment Steps

### Step 1: SSH to Server
```bash
ssh root@172.245.67.47
# Password: Chernivtsi_23
```

### Step 2: Backup Current System
```bash
cd /root
mkdir -p backups/v3_$(date +%Y%m%d_%H%M%S)
cp audiobook_*.py backups/v3_$(date +%Y%m%d_%H%M%S)/
```

### Step 3: Upload New Files

**Option A: Using SCP (from your local machine)**
```bash
scp /home/ubuntu/elevenlabs_voice_recommender.py root@172.245.67.47:/root/
scp /home/ubuntu/audiobook_processor_v7_with_voices.py root@172.245.67.47:/root/
scp /home/ubuntu/audiobook_webhook_server_v7_with_voices.py root@172.245.67.47:/root/
scp /home/ubuntu/analysis_page_template_v3_with_voices.html root@172.245.67.47:/root/
```

**Option B: Using Git (recommended)**
```bash
# On server
cd /root
git clone https://github.com/vitalykirkpatrick/audiobooksmithapp.git temp_deploy
cp temp_deploy/elevenlabs_voice_recommender.py /root/
cp temp_deploy/audiobook_processor_v7_with_voices.py /root/
cp temp_deploy/audiobook_webhook_server_v7_with_voices.py /root/
cp temp_deploy/analysis_page_template_v3_with_voices.html /root/
rm -rf temp_deploy
```

### Step 4: Install Dependencies
```bash
pip3 install elevenlabs requests PyPDF2 openai --break-system-packages
```

### Step 5: Set Environment Variables
```bash
# Edit the systemd service file
nano /etc/systemd/system/audiobook-webhook.service
```

**Add these environment variables:**
```ini
[Service]
Environment="ELEVENLABS_API_KEY=<your_elevenlabs_api_key>"
Environment="SLACK_WEBHOOK_URL=<your_slack_webhook_url>"
Environment="OPENAI_API_KEY=<your_openai_key>"
```

**Update the ExecStart line:**
```ini
ExecStart=/usr/bin/python3 /root/audiobook_webhook_server_v7_with_voices.py
```

Save and exit (Ctrl+X, Y, Enter)

### Step 6: Reload and Restart Service
```bash
# Reload systemd
systemctl daemon-reload

# Restart the service
systemctl restart audiobook-webhook

# Check status
systemctl status audiobook-webhook

# Check logs
journalctl -u audiobook-webhook -f
```

### Step 7: Test the Deployment

**Test 1: Health Check**
```bash
curl https://audiobooksmith.app/webhook/health
```

Expected output:
```json
{
  "status": "healthy",
  "version": "7.0.0",
  "features": ["validation", "folder_structure", "voice_recommendations"],
  "timestamp": "2025-12-08T..."
}
```

**Test 2: Upload a Book**
- Go to https://audiobooksmith.app
- Upload the Vitaly book
- Check that you see:
  - ✅ Author: "Vitaly Magidov"
  - ✅ Genre: "Memoir"
  - ✅ 45-46 chapters listed
  - ✅ 5 voice recommendations with audio players

**Test 3: Upload Invalid Document**
- Upload a technical guide or template
- Should be rejected with clear error message

**Test 4: Check Slack Notifications**
- You should receive notifications for:
  - Server startup
  - Upload started
  - Processing complete (with book details)
  - Voice selection

---

## 🔍 Troubleshooting

### Issue: Service won't start
```bash
# Check logs
journalctl -u audiobook-webhook -n 50

# Check if port 5001 is in use
netstat -tulpn | grep 5001

# Kill old process if needed
pkill -f audiobook_webhook
```

### Issue: Import errors
```bash
# Verify Python packages
python3 -c "import elevenlabs; print('elevenlabs OK')"
python3 -c "import PyPDF2; print('PyPDF2 OK')"
python3 -c "from openai import OpenAI; print('openai OK')"
```

### Issue: No voice recommendations
```bash
# Check ElevenLabs API key
echo $ELEVENLABS_API_KEY

# Test ElevenLabs connection
curl -H "xi-api-key: sk_b006ebce7fa44b04bdc0037b5858fbdaa62e85688177a5b4" \
  https://api.elevenlabs.io/v1/voices
```

### Issue: Chapters not detected
- This means AI analysis failed
- Check OpenAI API key is set
- Check logs for AI errors
- Verify book has readable text (not scanned)

---

## 📊 Verification Checklist

After deployment, verify these features work:

### ✅ Content Validation
- [ ] Valid book is accepted
- [ ] Template/guide is rejected with clear message
- [ ] Short story (1000+ words) is accepted
- [ ] Document under 1000 words is rejected

### ✅ AI Detection
- [ ] Book title is detected (not just filename)
- [ ] Author is detected
- [ ] Genre is detected (Memoir, Fiction, etc.)
- [ ] Chapters are detected with titles

### ✅ Voice Recommendations
- [ ] 5 voices are recommended
- [ ] Each voice has audio player
- [ ] Audio samples use actual book text
- [ ] Voice selection works and saves

### ✅ Folder Structure
- [ ] Session-based folders created
- [ ] 11 numbered processing folders (01-10, 99)
- [ ] ElevenLabs subfolders exist
- [ ] Voice samples saved to 09_elevenlabs_integration/voice_samples/

### ✅ Slack Notifications
- [ ] Server startup notification
- [ ] Upload started notification
- [ ] Processing complete notification (with details)
- [ ] Validation failed notification (for invalid docs)
- [ ] Voice selection notification

---

## 🔄 Rollback Instructions

If something goes wrong, rollback to v3:

```bash
# Stop service
systemctl stop audiobook-webhook

# Restore old files
cd /root
cp backups/v3_*/audiobook_*.py /root/

# Edit service file to use old server
nano /etc/systemd/system/audiobook-webhook.service
# Change ExecStart back to old server file

# Reload and restart
systemctl daemon-reload
systemctl restart audiobook-webhook
```

---

## 📈 Expected Results

### Before (V3)
```json
{
  "bookInfo": {
    "title": "Copy_of_VITALY_BOOK_-_FINAP_PUBLISHED_COPY_ON_AMZN",
    "author": "Unknown",
    "genre": "Unknown"
  },
  "structure": {
    "totalChapters": 0
  }
}
```

### After (V7)
```json
{
  "bookInfo": {
    "title": "VITALY The MisAdventures of a Ukrainian Orphan",
    "author": "Vitaly Magidov",
    "genre": "Memoir"
  },
  "structure": {
    "totalChapters": 46,
    "chapters": [
      {"number": 1, "title": "The Beginning"},
      {"number": 2, "title": "Early Memories"},
      ...
    ]
  },
  "voiceRecommendations": {
    "recommended_voices": [
      {
        "name": "Adam",
        "match_score": 95,
        "sample_path": "..."
      },
      ...
    ]
  }
}
```

---

## 🎉 Success Indicators

You'll know the deployment is successful when:

1. ✅ Health check returns version "7.0.0"
2. ✅ Slack notification shows "AudiobookSmith Server Started - Version 7.0.0"
3. ✅ Upload test shows actual book title, author, genre
4. ✅ All 46 chapters are listed
5. ✅ 5 voice recommendations appear with audio players
6. ✅ Invalid document is rejected with helpful error message

---

## 📞 Support

If you encounter issues:

1. Check logs: `journalctl -u audiobook-webhook -f`
2. Verify environment variables are set
3. Test API keys individually
4. Check file permissions
5. Verify Python packages are installed

---

**Estimated Deployment Time:** 15-20 minutes

**Recommended Time:** During low-traffic period (to avoid disrupting active users)
