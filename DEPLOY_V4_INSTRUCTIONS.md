# AudiobookSmith v4 Manual Deployment Guide

## 🎯 What's New in V4

- ✅ **AI-Powered Chapter Detection** - Automatically detects all chapters with titles
- ✅ **Automatic Genre Classification** - AI determines book type, genre, themes, author
- ✅ **Slack Notifications** - Get alerts when books are uploaded and processed
- ✅ **Simplified Form** - Only requires: name, email, file, comments (optional)
- ✅ **Enhanced Analysis Page** - Shows all chapters organized by parts

---

## 📦 Files to Deploy

Download from GitHub repository: `vitalykirkpatrick/audiobooksmithapp`

1. **audiobook_webhook_server_v4.py** - Enhanced webhook server with AI + Slack
2. **audiobook_processor_v4_ai.py** - AI-powered book processor

---

## 🚀 Deployment Steps

### Step 1: SSH to Server

```bash
ssh root@172.245.67.47
```

### Step 2: Backup Current Version

```bash
cd /root/audiobook_webhook
cp audiobook_webhook_server.py audiobook_webhook_server_v3_backup.py
cp audiobook_processor.py audiobook_processor_v3_backup.py
```

### Step 3: Download New Files from GitHub

```bash
cd /root/audiobook_webhook

# Download v4 files
curl -O https://raw.githubusercontent.com/vitalykirkpatrick/audiobooksmithapp/main/audiobook_webhook_server_v4.py
curl -O https://raw.githubusercontent.com/vitalykirkpatrick/audiobooksmithapp/main/audiobook_processor_v4_ai.py

# Rename to active files
mv audiobook_webhook_server_v4.py audiobook_webhook_server.py
```

### Step 4: Install Dependencies

```bash
cd /root/audiobook_webhook
pip3 install PyPDF2 openai requests flask flask-cors
```

### Step 5: Set Environment Variables

Create a `.env` file or set environment variables in the systemd service file.

**Required Environment Variables:**
- `SLACK_WEBHOOK_URL` - Your Slack webhook URL
- `SLACK_CHANNEL` - Your Slack channel ID
- `OPENAI_API_KEY` - Your OpenAI API key

```bash
# Option 1: Create .env file (I'll provide the values separately)
nano /root/audiobook_webhook/.env

# Option 2: Set in systemd service (see Step 6)
```

### Step 6: Update Systemd Service

```bash
nano /etc/systemd/system/audiobook-webhook.service
```

Update the service file to include environment variables:

```ini
[Unit]
Description=AudiobookSmith Webhook Server v4 (AI + Slack)
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/audiobook_webhook
Environment="SLACK_WEBHOOK_URL=<YOUR_SLACK_WEBHOOK_URL>"
Environment="SLACK_CHANNEL=<YOUR_SLACK_CHANNEL>"
Environment="OPENAI_API_KEY=<YOUR_OPENAI_API_KEY>"
ExecStart=/usr/bin/python3 /root/audiobook_webhook/audiobook_webhook_server.py
Restart=always
RestartSec=10
StandardOutput=append:/root/audiobook_webhook/logs/webhook_server.log
StandardError=append:/root/audiobook_webhook/logs/webhook_server.log

[Install]
WantedBy=multi-user.target
```

Then reload systemd:

```bash
systemctl daemon-reload
```

### Step 7: Restart Service

```bash
# Stop current service
systemctl stop audiobook-webhook

# Start new version
systemctl start audiobook-webhook

# Check status
systemctl status audiobook-webhook

# View logs
tail -f /root/audiobook_webhook/logs/webhook_server.log
```

---

## 🧪 Testing

### Test 1: Health Check

```bash
curl https://audiobooksmith.app/webhook/health
```

**Expected Response:**
```json
{
  "service": "AudiobookSmith Webhook Server v4 (AI-Powered + Slack)",
  "status": "healthy",
  "timestamp": "2025-12-08T...",
  "version": "4.0.0",
  "features": ["AI Chapter Detection", "Auto Genre Classification", "Simplified Form", "Slack Notifications"]
}
```

### Test 2: Check Slack

You should see a startup notification in your Slack channel.

### Test 3: Upload a Book

Use the form on audiobooksmith.com to upload a test PDF. You should:
1. See upload notification in Slack
2. See processing completion in Slack with book details
3. Get redirected to analysis page with all chapters displayed

---

## 📊 What You'll See in Slack

**Upload Started:**
- User name and email
- Status: Processing...

**Processing Complete:**
- Book title (detected by AI)
- Author (detected by AI)
- Genre and type
- Chapter count
- Word count and pages
- Link to view results

**Errors (if any):**
- Error message
- File name

---

## 🔧 Troubleshooting

### Issue: Service won't start

```bash
# Check logs
journalctl -u audiobook-webhook -n 50

# Check Python syntax
python3 /root/audiobook_webhook/audiobook_webhook_server.py
```

### Issue: No Slack notifications

```bash
# Test Slack webhook manually
curl -X POST $SLACK_WEBHOOK_URL \
  -H 'Content-Type: application/json' \
  -d '{"text":"Test notification from AudiobookSmith"}'
```

### Issue: AI processing fails

```bash
# Check OpenAI API key
echo $OPENAI_API_KEY

# Test OpenAI connection
python3 << 'EOF'
from openai import OpenAI
client = OpenAI()
response = client.chat.completions.create(
    model="gpt-4.1-mini",
    messages=[{"role": "user", "content": "Hello"}],
    max_tokens=10
)
print("✅ OpenAI working:", response.choices[0].message.content)
EOF
```

---

## 📝 Frontend Changes Needed

The form on audiobooksmith.com needs to be updated to only send:

**Remove These Fields:**
- ❌ `bookTitle` - AI will detect this
- ❌ `genre` - AI will detect this  
- ❌ `plan` - Not needed

**Keep/Add These Fields:**
- ✅ `name` - User's name
- ✅ `email` - User's email
- ✅ `bookFile` - PDF file
- ✅ `comments` - Optional comments (new field)

**Example Form Submission:**
```javascript
const formData = new FormData();
formData.append('name', userName);
formData.append('email', userEmail);
formData.append('bookFile', pdfFile);
formData.append('comments', userComments || '');

const response = await fetch('https://audiobooksmith.app/webhook/audiobook-process', {
  method: 'POST',
  body: formData
});

const result = await response.json();
if (result.success) {
  window.location.href = result.folderUrl;
}
```

---

## 🎯 Success Criteria

After deployment:

- ✅ Webhook server running with v4
- ✅ AI chapter detection working
- ✅ Slack notifications arriving
- ✅ Analysis pages showing all chapters
- ✅ Simplified form working

---

**Note:** API keys and secrets will be provided separately for security.
