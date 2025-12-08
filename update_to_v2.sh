#!/bin/bash

################################################################################
# Update AudiobookSmith Webhook Server to v2 (Testing Version)
#
# This script updates the webhook server to version 2 with file browser
################################################################################

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

clear

echo -e "${BLUE}"
cat << "EOF"
╔════════════════════════════════════════════════════════════╗
║                                                            ║
║   AudiobookSmith Webhook Server - Update to v2            ║
║                                                            ║
╚════════════════════════════════════════════════════════════╝
EOF
echo -e "${NC}"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}❌ This script must be run as root${NC}"
    exit 1
fi

echo -e "${YELLOW}[1/5] Stopping current webhook server...${NC}"
if pgrep -f audiobook_webhook_server.py > /dev/null; then
    pkill -f audiobook_webhook_server.py
    sleep 2
    echo -e "${GREEN}✅ Server stopped${NC}"
else
    echo -e "${YELLOW}⚠️  Server not running${NC}"
fi
echo ""

echo -e "${YELLOW}[2/5] Backing up current version...${NC}"
cd /root/audiobook_webhook
if [ -f "audiobook_webhook_server.py" ]; then
    cp audiobook_webhook_server.py audiobook_webhook_server.py.backup.$(date +%Y%m%d_%H%M%S)
    echo -e "${GREEN}✅ Backup created${NC}"
else
    echo -e "${YELLOW}⚠️  No existing server found${NC}"
fi
echo ""

echo -e "${YELLOW}[3/5] Downloading v2 from GitHub...${NC}"
curl -sSL https://raw.githubusercontent.com/vitalykirkpatrick/audiobooksmithapp/main/audiobook_webhook_server_v2.py -o audiobook_webhook_server_v2.py
chmod +x audiobook_webhook_server_v2.py
echo -e "${GREEN}✅ v2 downloaded${NC}"
echo ""

echo -e "${YELLOW}[4/5] Creating processed directory...${NC}"
mkdir -p /root/audiobook_webhook/processed
chown -R root:root /root/audiobook_webhook/processed
echo -e "${GREEN}✅ Directory created${NC}"
echo ""

echo -e "${YELLOW}[5/5] Starting v2 server...${NC}"
nohup python3 /root/audiobook_webhook/audiobook_webhook_server_v2.py > /root/audiobook_webhook/logs/webhook_server.log 2>&1 &
sleep 3

# Check if server started
if pgrep -f audiobook_webhook_server_v2.py > /dev/null; then
    PID=$(pgrep -f audiobook_webhook_server_v2.py)
    echo -e "${GREEN}✅ Server started (PID: $PID)${NC}"
else
    echo -e "${RED}❌ Failed to start server${NC}"
    echo -e "${YELLOW}Check logs: tail -f /root/audiobook_webhook/logs/webhook_server.log${NC}"
    exit 1
fi
echo ""

# Test server
echo -e "${YELLOW}Testing server...${NC}"
sleep 2
HEALTH_CHECK=$(curl -s http://localhost:5001/health 2>/dev/null || echo "failed")
if echo "$HEALTH_CHECK" | grep -q "healthy"; then
    echo -e "${GREEN}✅ Server is healthy${NC}"
else
    echo -e "${RED}❌ Health check failed${NC}"
    echo -e "${YELLOW}Response: $HEALTH_CHECK${NC}"
fi
echo ""

echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  🎉 Update Complete!                                       ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

echo -e "${BLUE}📊 Server Information:${NC}"
echo -e "   Version: v2 (Testing with File Browser)"
echo -e "   PID: $(pgrep -f audiobook_webhook_server_v2.py)"
echo -e "   Port: 5001"
echo -e "   Status: Running"
echo ""

echo -e "${BLUE}🧪 Test Endpoints:${NC}"
echo -e "   Health: https://audiobooksmith.app/health"
echo -e "   Upload: https://audiobooksmith.app/webhook/audiobook-process"
echo ""

echo -e "${BLUE}🔧 Management:${NC}"
echo -e "   Logs: tail -f /root/audiobook_webhook/logs/webhook_server.log"
echo -e "   Stop: pkill -f audiobook_webhook_server_v2.py"
echo -e "   Start: nohup python3 /root/audiobook_webhook/audiobook_webhook_server_v2.py > /root/audiobook_webhook/logs/webhook_server.log 2>&1 &"
echo ""

echo -e "${BLUE}📁 New Features:${NC}"
echo -e "   ✓ File browser at /files/view/{projectId}"
echo -e "   ✓ Download functionality"
echo -e "   ✓ Beautiful UI"
echo -e "   ✓ Metadata display"
echo -e "   ✓ Folder navigation"
echo ""

echo -e "${GREEN}✅ Ready for testing!${NC}"
echo ""
