#!/bin/bash
################################################################################
# AudiobookSmith Webhook - One-Line Installer
# 
# This script downloads and executes the deployment automatically
# Run on your server: curl -sSL https://raw.githubusercontent.com/vitalykirkpatrick/audiobooksmithapp/main/install.sh | bash
################################################################################

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

clear

echo -e "${BLUE}"
cat << "EOF"
╔════════════════════════════════════════════════════════════╗
║                                                            ║
║   AudiobookSmith Webhook - One-Line Installer             ║
║   Automated Deployment with Backup                        ║
║                                                            ║
╚════════════════════════════════════════════════════════════╝
EOF
echo -e "${NC}"
echo ""

echo -e "${YELLOW}📦 Installing AudiobookSmith Webhook...${NC}"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}❌ This script must be run as root${NC}"
    echo -e "${YELLOW}Please run: sudo bash install.sh${NC}"
    exit 1
fi

# Create deployment directory
DEPLOY_DIR="/root/audiobooksmith_deployment"
INSTALL_DIR="/root/audiobook_webhook"

echo -e "${YELLOW}[1/6] Creating directories...${NC}"
mkdir -p "$DEPLOY_DIR"
cd "$DEPLOY_DIR"
echo -e "${GREEN}✅ Directories created${NC}"
echo ""

# Download deployment files
echo -e "${YELLOW}[2/6] Downloading deployment files from GitHub...${NC}"

REPO_URL="https://raw.githubusercontent.com/vitalykirkpatrick/audiobooksmithapp/main"

# Download main deployment script
curl -sSL "${REPO_URL}/deploy_with_backup.sh" -o deploy_with_backup.sh
chmod +x deploy_with_backup.sh

# Download core files
curl -sSL "${REPO_URL}/audiobook_webhook_server.py" -o audiobook_webhook_server.py
curl -sSL "${REPO_URL}/audiobook_processor.py" -o audiobook_processor.py
curl -sSL "${REPO_URL}/nginx_multi_domain.conf" -o nginx_multi_domain.conf
curl -sSL "${REPO_URL}/setup_ssl_both_domains.sh" -o setup_ssl_both_domains.sh

chmod +x *.py *.sh

echo -e "${GREEN}✅ Files downloaded${NC}"
echo ""

# Check prerequisites
echo -e "${YELLOW}[3/6] Checking prerequisites...${NC}"

# Check Python
if command -v python3.11 &> /dev/null; then
    PYTHON_CMD="python3.11"
    echo -e "${GREEN}✅ Python 3.11 found${NC}"
elif command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
    echo -e "${GREEN}✅ Python 3 found${NC}"
else
    echo -e "${YELLOW}⚠️  Python not found, installing...${NC}"
    apt-get update -qq && apt-get install -y python3 python3-pip
    PYTHON_CMD="python3"
fi

# Check Flask
if ! $PYTHON_CMD -c "import flask" 2>/dev/null; then
    echo -e "${YELLOW}⚠️  Flask not found, installing...${NC}"
    pip3 install flask --ignore-installed blinker || pip3 install flask --break-system-packages
fi

echo -e "${GREEN}✅ Prerequisites checked${NC}"
echo ""

# Create backup if installation exists
echo -e "${YELLOW}[4/6] Checking for existing installation...${NC}"
if [ -d "$INSTALL_DIR" ]; then
    BACKUP_DIR="/root/audiobook_webhook_backup_$(date +%Y%m%d_%H%M%S)"
    echo -e "${YELLOW}⚠️  Existing installation found, creating backup...${NC}"
    cp -r "$INSTALL_DIR" "$BACKUP_DIR"
    echo -e "${GREEN}✅ Backup created: $BACKUP_DIR${NC}"
else
    echo -e "${GREEN}✅ No existing installation found${NC}"
fi
echo ""

# Install
echo -e "${YELLOW}[5/6] Installing webhook server...${NC}"

# Create installation directory
mkdir -p "$INSTALL_DIR"/{logs,uploads,backups}

# Copy files
cp audiobook_webhook_server.py "$INSTALL_DIR/"
cp audiobook_processor.py "$INSTALL_DIR/"
cp nginx_multi_domain.conf "$INSTALL_DIR/"
cp setup_ssl_both_domains.sh "$INSTALL_DIR/"

cd "$INSTALL_DIR"

# Update paths
sed -i 's|UPLOAD_FOLDER = "/home/ubuntu/audiobook_uploads"|UPLOAD_FOLDER = "/root/audiobook_webhook/uploads"|g' audiobook_webhook_server.py
sed -i 's|PROCESSOR_SCRIPT = "/home/ubuntu/audiobook_processor.py"|PROCESSOR_SCRIPT = "/root/audiobook_webhook/audiobook_processor.py"|g' audiobook_webhook_server.py

# Find available port
WEBHOOK_PORT=5001
for PORT in 5001 5002 5003 5004 5005; do
    if ! netstat -tln 2>/dev/null | grep -q ":${PORT} "; then
        WEBHOOK_PORT=${PORT}
        break
    fi
done

sed -i "s|port=5001|port=${WEBHOOK_PORT}|g" audiobook_webhook_server.py

chmod +x *.py *.sh

# Create management scripts
cat > start.sh << EOF
#!/bin/bash
cd /root/audiobook_webhook
nohup ${PYTHON_CMD} audiobook_webhook_server.py > logs/webhook_server.log 2>&1 &
echo \\\$! > webhook_server.pid
echo "✅ Webhook server started (PID: \\\$(cat webhook_server.pid))"
echo "📊 Logs: tail -f /root/audiobook_webhook/logs/webhook_server.log"
EOF

cat > stop.sh << 'EOF'
#!/bin/bash
if [ -f /root/audiobook_webhook/webhook_server.pid ]; then
    kill $(cat /root/audiobook_webhook/webhook_server.pid) 2>/dev/null
    rm /root/audiobook_webhook/webhook_server.pid
fi
pkill -f audiobook_webhook_server.py
echo "✅ Webhook server stopped"
EOF

cat > status.sh << 'EOF'
#!/bin/bash
if pgrep -f audiobook_webhook_server.py > /dev/null; then
    echo "✅ Webhook server is running"
    ps aux | grep audiobook_webhook_server.py | grep -v grep
else
    echo "❌ Webhook server is not running"
fi
EOF

cat > restart.sh << 'EOF'
#!/bin/bash
/root/audiobook_webhook/stop.sh
sleep 2
/root/audiobook_webhook/start.sh
EOF

chmod +x *.sh

echo -e "${GREEN}✅ Webhook server installed${NC}"
echo ""

# Start service
echo -e "${YELLOW}[6/6] Starting webhook server...${NC}"
./start.sh
sleep 3

# Test
HEALTH=$(curl -s http://localhost:${WEBHOOK_PORT}/health 2>/dev/null)
if echo "$HEALTH" | grep -q "healthy"; then
    echo -e "${GREEN}✅ Webhook server is running and healthy${NC}"
else
    echo -e "${YELLOW}⚠️  Webhook server started but health check unclear${NC}"
fi

echo ""
echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  🎉 Installation Complete!                                 ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

echo -e "${BLUE}📍 Installation Details:${NC}"
echo -e "   Location: /root/audiobook_webhook"
echo -e "   Port: ${WEBHOOK_PORT}"
echo -e "   Status: Running"
echo ""

echo -e "${BLUE}🔧 Management Commands:${NC}"
echo -e "   Start:   /root/audiobook_webhook/start.sh"
echo -e "   Stop:    /root/audiobook_webhook/stop.sh"
echo -e "   Status:  /root/audiobook_webhook/status.sh"
echo -e "   Restart: /root/audiobook_webhook/restart.sh"
echo -e "   Logs:    tail -f /root/audiobook_webhook/logs/webhook_server.log"
echo ""

echo -e "${YELLOW}⚠️  IMPORTANT: Configure Nginx & SSL${NC}"
echo -e "   Run this command to complete setup:"
echo -e "   ${CYAN}cd /root/audiobook_webhook && ./setup_ssl_both_domains.sh${NC}"
echo ""
echo -e "   This will:"
echo -e "   • Configure Nginx for websolutionsserver.net and audiobooksmith.app"
echo -e "   • Obtain SSL certificates from Let's Encrypt"
echo -e "   • Set up automatic SSL renewal"
echo -e "   • Make webhook accessible via HTTPS"
echo ""

echo -e "${BLUE}🧪 Test (after SSL setup):${NC}"
echo -e "   ${CYAN}curl https://audiobooksmith.app/webhook/health${NC}"
echo -e "   ${CYAN}curl https://websolutionsserver.net/webhook/health${NC}"
echo ""

echo -e "${GREEN}✅ AudiobookSmith Webhook is ready!${NC}"
echo ""
