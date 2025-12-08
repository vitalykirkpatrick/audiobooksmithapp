#!/bin/bash
#
# Update AudiobookSmith Webhook Server to v3
# This script updates the production server with the new analysis-enabled version
#

set -e

echo "╔════════════════════════════════════════════════════════════╗"
echo "║  Updating to AudiobookSmith Webhook Server v3             ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Configuration
WEBHOOK_DIR="/root/audiobook_webhook"
BACKUP_DIR="/root/audiobook_webhook_backup_$(date +%Y%m%d_%H%M%S)"

# Step 1: Backup existing installation
if [ -d "$WEBHOOK_DIR" ]; then
    echo "[1/6] Creating backup..."
    cp -r "$WEBHOOK_DIR" "$BACKUP_DIR"
    echo "✅ Backup created at $BACKUP_DIR"
else
    echo "[1/6] No existing installation found, skipping backup..."
fi

# Step 2: Stop existing server
echo ""
echo "[2/6] Stopping existing server..."
if [ -f "$WEBHOOK_DIR/stop.sh" ]; then
    cd "$WEBHOOK_DIR" && ./stop.sh || true
else
    pkill -f "audiobook_webhook_server" || true
fi
sleep 2
echo "✅ Server stopped"

# Step 3: Install dependencies
echo ""
echo "[3/6] Checking dependencies..."

# Check for pdftotext (poppler-utils)
if ! command -v pdftotext &> /dev/null; then
    echo "Installing poppler-utils for PDF processing..."
    apt-get update && apt-get install -y poppler-utils
fi

# Check for python-docx
if ! python3 -c "import docx" 2>/dev/null; then
    echo "Installing python-docx for DOCX processing..."
    pip3 install python-docx
fi

# Check for ebooklib
if ! python3 -c "import ebooklib" 2>/dev/null; then
    echo "Installing ebooklib for EPUB processing..."
    pip3 install ebooklib beautifulsoup4
fi

echo "✅ Dependencies checked"

# Step 4: Update server file
echo ""
echo "[4/6] Updating webhook server..."
cp audiobook_webhook_server_v3.py "$WEBHOOK_DIR/audiobook_webhook_server.py"
chmod +x "$WEBHOOK_DIR/audiobook_webhook_server.py"
echo "✅ Server updated to v3"

# Step 5: Update management scripts
echo ""
echo "[5/6] Updating management scripts..."

# Update start script
cat > "$WEBHOOK_DIR/start.sh" << 'EOF'
#!/bin/bash
cd "$(dirname "$0")"
nohup python3 audiobook_webhook_server.py > logs/webhook_server.log 2>&1 &
echo $! > webhook_server.pid
echo "✅ Webhook server started (PID: $(cat webhook_server.pid))"
EOF
chmod +x "$WEBHOOK_DIR/start.sh"

# Update status script
cat > "$WEBHOOK_DIR/status.sh" << 'EOF'
#!/bin/bash
cd "$(dirname "$0")"
if [ -f webhook_server.pid ]; then
    PID=$(cat webhook_server.pid)
    if ps -p $PID > /dev/null 2>&1; then
        echo "✅ Webhook server is running (PID: $PID)"
        echo ""
        echo "Testing health endpoint..."
        curl -s http://localhost:5001/webhook/health | python3 -m json.tool || echo "❌ Health check failed"
    else
        echo "❌ Webhook server is not running (stale PID file)"
    fi
else
    echo "❌ Webhook server is not running (no PID file)"
fi
EOF
chmod +x "$WEBHOOK_DIR/status.sh"

echo "✅ Management scripts updated"

# Step 6: Start server
echo ""
echo "[6/6] Starting webhook server v3..."
cd "$WEBHOOK_DIR" && ./start.sh
sleep 3

# Test the server
echo ""
echo "Testing server..."
if curl -s http://localhost:5001/webhook/health | grep -q "healthy"; then
    echo "✅ Server is running and healthy!"
else
    echo "❌ Server health check failed"
    exit 1
fi

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║  ✅ Update Complete!                                       ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo "📍 Server Details:"
echo "   Version: 3.0.0"
echo "   Location: $WEBHOOK_DIR"
echo "   Backup: $BACKUP_DIR"
echo ""
echo "🎯 New Features in v3:"
echo "   • Comprehensive book analysis"
echo "   • Chapter and section detection"
echo "   • Production recommendations"
echo "   • Beautiful results display page"
echo "   • Multiple file format support"
echo ""
echo "🧪 Test the server:"
echo "   curl https://audiobooksmith.app/webhook/health"
echo ""
echo "📊 View logs:"
echo "   tail -f $WEBHOOK_DIR/logs/webhook_server.log"
echo ""
