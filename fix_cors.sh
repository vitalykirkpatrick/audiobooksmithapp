#!/bin/bash

# Fix CORS Issue on AudiobookSmith Webhook Server
# This script installs flask-cors and updates the server

set -e

echo "╔════════════════════════════════════════════════════════════╗"
echo "║  Fixing CORS Issue on AudiobookSmith Webhook Server       ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Step 1: Install flask-cors
echo "[1/4] Installing flask-cors..."
pip3 install flask-cors
echo "✅ flask-cors installed"
echo ""

# Step 2: Backup current server
echo "[2/4] Creating backup..."
cp /root/audiobook_webhook/audiobook_webhook_server.py /root/audiobook_webhook/audiobook_webhook_server.py.backup_$(date +%Y%m%d_%H%M%S)
echo "✅ Backup created"
echo ""

# Step 3: Download updated server with CORS
echo "[3/4] Downloading updated server with CORS support..."
curl -sSL https://raw.githubusercontent.com/vitalykirkpatrick/audiobooksmithapp/main/audiobook_webhook_server_v3.py -o /root/audiobook_webhook/audiobook_webhook_server.py
chmod +x /root/audiobook_webhook/audiobook_webhook_server.py
echo "✅ Server updated"
echo ""

# Step 4: Restart server
echo "[4/4] Restarting webhook server..."
cd /root/audiobook_webhook
./stop.sh
sleep 2
./start.sh
sleep 3
echo "✅ Server restarted"
echo ""

# Test
echo "Testing server..."
curl -s http://localhost:5001/webhook/health | python3 -m json.tool
echo ""

echo "╔════════════════════════════════════════════════════════════╗"
echo "║  ✅ CORS Fix Complete!                                     ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo "The webhook server now accepts requests from:"
echo "  • https://audiobooksmith.com"
echo "  • http://localhost:* (for testing)"
echo ""
echo "Test from audiobooksmith.com now - the 'Failed to fetch' error should be resolved!"
