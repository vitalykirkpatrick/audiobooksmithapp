#!/bin/bash

# AudiobookSmith V7 Automated Deployment Script
# Run as root: curl -fsSL https://raw.githubusercontent.com/vitalykirkpatrick/audiobooksmithapp/main/deploy_v7.sh | bash

set -e

echo "╔════════════════════════════════════════════════════════╗"
echo "║   AudiobookSmith V7 Deployment                         ║"
echo "║   AI Detection + Voice Recommendations + Validation    ║"
echo "╚════════════════════════════════════════════════════════╝"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then
  echo "❌ Error: This script must be run as root"
  echo "   Please run: sudo bash deploy_v7.sh"
  exit 1
fi

echo "📦 Step 1/8: Backing up current system..."
cd /root
mkdir -p backups/v3_$(date +%Y%m%d_%H%M%S)
if ls audiobook_*.py 1> /dev/null 2>&1; then
  cp audiobook_*.py backups/v3_$(date +%Y%m%d_%H%M%S)/
  echo "✅ Backup created"
else
  echo "ℹ️  No existing files to backup"
fi

echo ""
echo "📥 Step 2/8: Downloading V7 files from GitHub..."
rm -rf /tmp/audiobooksmith_deploy
git clone --quiet https://github.com/vitalykirkpatrick/audiobooksmithapp.git /tmp/audiobooksmith_deploy
echo "✅ Files downloaded"

echo ""
echo "📋 Step 3/8: Installing V7 files..."
cp /tmp/audiobooksmith_deploy/elevenlabs_voice_recommender.py /root/
cp /tmp/audiobooksmith_deploy/audiobook_processor_v7_with_voices.py /root/
cp /tmp/audiobooksmith_deploy/audiobook_webhook_server_v7_with_voices.py /root/
cp /tmp/audiobooksmith_deploy/analysis_page_template_v3_with_voices.html /root/
echo "✅ Files installed"

echo ""
echo "🔧 Step 4/8: Installing Python dependencies..."
pip3 install elevenlabs requests PyPDF2 openai --break-system-packages --quiet 2>&1 | grep -v "WARNING" || true
echo "✅ Dependencies installed"

echo ""
echo "⚙️  Step 5/8: Configuring systemd service..."
cat > /etc/systemd/system/audiobook-webhook.service << 'SERVICEEOF'
[Unit]
Description=AudiobookSmith Webhook Server V7
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root
Environment="ELEVENLABS_API_KEY=<REPLACE_WITH_YOUR_KEY>"
Environment="SLACK_WEBHOOK_URL=<REPLACE_WITH_YOUR_WEBHOOK>"
Environment="OPENAI_API_KEY=<REPLACE_WITH_YOUR_KEY>"
ExecStart=/usr/bin/python3 /root/audiobook_webhook_server_v7_with_voices.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
SERVICEEOF

# Replace placeholders with actual values (you need to edit these)
echo "⚠️  IMPORTANT: Edit /etc/systemd/system/audiobook-webhook.service"
echo "   Replace <REPLACE_WITH_YOUR_KEY> with your actual API keys"
echo ""
read -p "Press Enter after you've updated the API keys in the service file..."

echo ""
echo "🔄 Step 6/8: Reloading systemd..."
systemctl daemon-reload
echo "✅ Systemd reloaded"

echo ""
echo "🚀 Step 7/8: Restarting service..."
systemctl restart audiobook-webhook
sleep 3
echo "✅ Service restarted"

echo ""
echo "🔍 Step 8/8: Verifying deployment..."

# Check service status
if systemctl is-active --quiet audiobook-webhook; then
  echo "✅ Service is running"
else
  echo "❌ Service failed to start"
  echo "   Check logs: journalctl -u audiobook-webhook -n 50"
  exit 1
fi

# Test health endpoint
echo ""
echo "Testing health endpoint..."
sleep 2
HEALTH_CHECK=$(curl -s https://audiobooksmith.app/webhook/health 2>/dev/null || echo "")

if echo "$HEALTH_CHECK" | grep -q "7.0.0"; then
  echo "✅ Health check passed - V7 is running!"
elif echo "$HEALTH_CHECK" | grep -q "healthy"; then
  echo "⚠️  Service is healthy but version might not be 7.0.0"
  echo "   Response: $HEALTH_CHECK"
else
  echo "⚠️  Health check returned: $HEALTH_CHECK"
  echo "   The service may still be starting up..."
fi

echo ""
echo "╔════════════════════════════════════════════════════════╗"
echo "║   ✅ AudiobookSmith V7 Deployment Complete!            ║"
echo "╚════════════════════════════════════════════════════════╝"
echo ""
echo "📊 What's New in V7:"
echo "  ✅ AI-powered author, title, genre detection"
echo "  ✅ Complete chapter detection (all 46 chapters)"
echo "  ✅ 5 AI-recommended voices with samples"
echo "  ✅ Strict validation (rejects templates/guides)"
echo "  ✅ Session-based folder structure with versioning"
echo ""
echo "🧪 Next Steps:"
echo "  1. Test by uploading a book at https://audiobooksmith.app"
echo "  2. Verify AI detects title, author, genre correctly"
echo "  3. Check that all chapters are listed"
echo "  4. Test voice recommendations"
echo "  5. Try uploading an invalid document (should be rejected)"
echo ""
echo "📝 Logs:"
echo "  View logs: journalctl -u audiobook-webhook -f"
echo "  Service status: systemctl status audiobook-webhook"
echo ""
echo "🔄 Rollback (if needed):"
echo "  cd /root/backups/v3_*"
echo "  cp audiobook_*.py /root/"
echo "  systemctl restart audiobook-webhook"
echo ""
echo "Deployment completed at: $(date)"
