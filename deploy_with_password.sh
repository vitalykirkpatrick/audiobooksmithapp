#!/bin/bash

################################################################################
# AudiobookSmith Webhook - Deployment with Password Authentication
#
# This script deploys to your server using password authentication
# Server: 172.245.67.47 (websolutionsserver.net)
# User: root
# Password: Chernivtsi_23
#
# Usage: ./deploy_with_password.sh
################################################################################

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# Configuration
REMOTE_HOST="172.245.67.47"
REMOTE_USER="root"
REMOTE_PASSWORD="Chernivtsi_23"
REMOTE_PORT="22"

clear

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  AudiobookSmith Webhook - Automated Deployment            ║${NC}"
echo -e "${BLUE}║  Target: ${REMOTE_HOST} (websolutionsserver.net)${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Check if sshpass is installed
if ! command -v sshpass &> /dev/null; then
    echo -e "${YELLOW}⚠️  sshpass not found. Installing...${NC}"
    if command -v apt-get &> /dev/null; then
        sudo apt-get update && sudo apt-get install -y sshpass
    elif command -v yum &> /dev/null; then
        sudo yum install -y sshpass
    else
        echo -e "${RED}❌ Cannot install sshpass automatically${NC}"
        echo -e "${YELLOW}   Please install sshpass manually or use SSH key authentication${NC}"
        exit 1
    fi
fi

echo -e "${YELLOW}📋 Deployment Configuration:${NC}"
echo -e "   Server: ${REMOTE_HOST}"
echo -e "   User: ${REMOTE_USER}"
echo ""

# Confirm
echo -e "${YELLOW}This will deploy the webhook integration to your server.${NC}"
echo -e "${YELLOW}The deployment is safe and will not affect your existing N8N setup.${NC}"
echo ""
read -p "Continue with deployment? (y/n): " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${RED}Deployment cancelled.${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}Starting deployment...${NC}"
echo ""

# Test SSH connection
echo -e "${YELLOW}[1/12] Testing SSH connection...${NC}"
if sshpass -p "${REMOTE_PASSWORD}" ssh -o StrictHostKeyChecking=no -p ${REMOTE_PORT} ${REMOTE_USER}@${REMOTE_HOST} exit 2>/dev/null; then
    echo -e "${GREEN}✅ SSH connection successful${NC}"
else
    echo -e "${RED}❌ SSH connection failed${NC}"
    exit 1
fi
echo ""

# Run audit on remote server
echo -e "${YELLOW}[2/12] Auditing remote server...${NC}"
sshpass -p "${REMOTE_PASSWORD}" ssh -o StrictHostKeyChecking=no -p ${REMOTE_PORT} ${REMOTE_USER}@${REMOTE_HOST} "bash -s" << 'AUDIT_SCRIPT'
    echo "🔍 Checking server configuration..."
    
    # Check Python
    if command -v python3.11 &> /dev/null; then
        echo "✅ Python 3.11: $(python3.11 --version)"
        PYTHON_CMD="python3.11"
    elif command -v python3 &> /dev/null; then
        echo "✅ Python 3: $(python3 --version)"
        PYTHON_CMD="python3"
    else
        echo "❌ Python not found"
        exit 1
    fi
    
    # Check Flask
    if $PYTHON_CMD -c "import flask" 2>/dev/null; then
        echo "✅ Flask installed"
    else
        echo "⚠️  Flask not installed - will install"
    fi
    
    # Check Nginx
    if command -v nginx &> /dev/null; then
        echo "✅ Nginx: $(nginx -v 2>&1 | cut -d'/' -f2)"
    else
        echo "⚠️  Nginx not found - will install"
    fi
    
    # Check N8N
    if pgrep -f "n8n" > /dev/null; then
        echo "✅ N8N is running"
    fi
    
    # Find available port
    for PORT in 5001 5002 5003 5004 5005; do
        if ! netstat -tln 2>/dev/null | grep -q ":${PORT} "; then
            echo "✅ Port ${PORT} is available"
            echo "WEBHOOK_PORT=${PORT}" > /tmp/webhook_config.env
            break
        fi
    done
AUDIT_SCRIPT

echo -e "${GREEN}✅ Server audit complete${NC}"
echo ""

# Get configuration from remote
echo -e "${YELLOW}[3/12] Getting server configuration...${NC}"
sshpass -p "${REMOTE_PASSWORD}" scp -o StrictHostKeyChecking=no -P ${REMOTE_PORT} ${REMOTE_USER}@${REMOTE_HOST}:/tmp/webhook_config.env /tmp/webhook_config.env 2>/dev/null || true
if [ -f /tmp/webhook_config.env ]; then
    source /tmp/webhook_config.env
    echo -e "${GREEN}✅ Will use port ${WEBHOOK_PORT:-5001}${NC}"
fi
WEBHOOK_PORT=${WEBHOOK_PORT:-5001}
echo ""

# Create remote directory structure
echo -e "${YELLOW}[4/12] Creating directory structure...${NC}"
sshpass -p "${REMOTE_PASSWORD}" ssh -o StrictHostKeyChecking=no -p ${REMOTE_PORT} ${REMOTE_USER}@${REMOTE_HOST} "bash -s" << 'ENDSSH'
    mkdir -p /root/audiobook_webhook/{logs,uploads,backups,scripts,config}
    chmod 755 /root/audiobook_webhook
    chmod 755 /root/audiobook_webhook/uploads
    chmod 755 /root/audiobook_webhook/logs
    echo "✅ Directories created"
ENDSSH
echo -e "${GREEN}✅ Directory structure created${NC}"
echo ""

# Copy files
echo -e "${YELLOW}[5/12] Copying webhook server...${NC}"
sshpass -p "${REMOTE_PASSWORD}" scp -o StrictHostKeyChecking=no -P ${REMOTE_PORT} \
    ./audiobook_webhook_server.py \
    ${REMOTE_USER}@${REMOTE_HOST}:/root/audiobook_webhook/
echo -e "${GREEN}✅ Webhook server copied${NC}"
echo ""

echo -e "${YELLOW}[6/12] Copying audiobook processor...${NC}"
sshpass -p "${REMOTE_PASSWORD}" scp -o StrictHostKeyChecking=no -P ${REMOTE_PORT} \
    ./audiobook_processor.py \
    ${REMOTE_USER}@${REMOTE_HOST}:/root/audiobook_webhook/
echo -e "${GREEN}✅ Audiobook processor copied${NC}"
echo ""

echo -e "${YELLOW}[7/12] Copying configuration files...${NC}"
sshpass -p "${REMOTE_PASSWORD}" scp -o StrictHostKeyChecking=no -P ${REMOTE_PORT} \
    ./nginx_multi_domain.conf \
    ./setup_ssl_both_domains.sh \
    ${REMOTE_USER}@${REMOTE_HOST}:/root/audiobook_webhook/
echo -e "${GREEN}✅ Configuration files copied${NC}"
echo ""

echo -e "${YELLOW}[8/12] Copying documentation...${NC}"
sshpass -p "${REMOTE_PASSWORD}" scp -o StrictHostKeyChecking=no -P ${REMOTE_PORT} \
    ./*.md \
    ./frontend_integration_code.jsx \
    ${REMOTE_USER}@${REMOTE_HOST}:/root/audiobook_webhook/ 2>/dev/null || true
echo -e "${GREEN}✅ Documentation copied${NC}"
echo ""

# Configure and install
echo -e "${YELLOW}[9/12] Configuring webhook server...${NC}"
sshpass -p "${REMOTE_PASSWORD}" ssh -o StrictHostKeyChecking=no -p ${REMOTE_PORT} ${REMOTE_USER}@${REMOTE_HOST} "bash -s" << ENDSSH
    cd /root/audiobook_webhook
    
    # Update paths in webhook server
    sed -i 's|UPLOAD_FOLDER = "/home/ubuntu/audiobook_uploads"|UPLOAD_FOLDER = "/root/audiobook_webhook/uploads"|g' audiobook_webhook_server.py
    sed -i 's|PROCESSOR_SCRIPT = "/home/ubuntu/audiobook_processor.py"|PROCESSOR_SCRIPT = "/root/audiobook_webhook/audiobook_processor.py"|g' audiobook_webhook_server.py
    sed -i 's|port=5001|port=${WEBHOOK_PORT}|g' audiobook_webhook_server.py
    
    # Make executable
    chmod +x audiobook_webhook_server.py audiobook_processor.py setup_ssl_both_domains.sh
    
    echo "✅ Configuration updated"
ENDSSH
echo -e "${GREEN}✅ Webhook server configured${NC}"
echo ""

# Install dependencies
echo -e "${YELLOW}[10/12] Installing dependencies...${NC}"
sshpass -p "${REMOTE_PASSWORD}" ssh -o StrictHostKeyChecking=no -p ${REMOTE_PORT} ${REMOTE_USER}@${REMOTE_HOST} "bash -s" << 'ENDSSH'
    # Determine Python command
    if command -v python3.11 &> /dev/null; then
        PYTHON_CMD="python3.11"
    else
        PYTHON_CMD="python3"
    fi
    
    # Install Flask if needed
    if ! $PYTHON_CMD -c "import flask" 2>/dev/null; then
        echo "📦 Installing Flask..."
        pip3 install flask
        echo "✅ Flask installed"
    else
        echo "✅ Flask already installed"
    fi
    
    # Install Nginx if needed
    if ! command -v nginx &> /dev/null; then
        echo "📦 Installing Nginx..."
        apt-get update && apt-get install -y nginx
        echo "✅ Nginx installed"
    fi
ENDSSH
echo -e "${GREEN}✅ Dependencies installed${NC}"
echo ""

# Create management scripts
echo -e "${YELLOW}[11/12] Creating management scripts...${NC}"
sshpass -p "${REMOTE_PASSWORD}" ssh -o StrictHostKeyChecking=no -p ${REMOTE_PORT} ${REMOTE_USER}@${REMOTE_HOST} "bash -s" << 'ENDSSH'
    cd /root/audiobook_webhook
    
    # Determine Python command
    if command -v python3.11 &> /dev/null; then
        PYTHON_CMD="python3.11"
    else
        PYTHON_CMD="python3"
    fi
    
    # Start script
    cat > start.sh << EOF
#!/bin/bash
cd /root/audiobook_webhook
nohup ${PYTHON_CMD} audiobook_webhook_server.py > logs/webhook_server.log 2>&1 &
echo \$! > webhook_server.pid
echo "✅ Webhook server started (PID: \$(cat webhook_server.pid))"
echo "📊 View logs: tail -f /root/audiobook_webhook/logs/webhook_server.log"
EOF
    
    # Stop script
    cat > stop.sh << 'EOF'
#!/bin/bash
if [ -f /root/audiobook_webhook/webhook_server.pid ]; then
    PID=$(cat /root/audiobook_webhook/webhook_server.pid)
    if kill -0 $PID 2>/dev/null; then
        kill $PID
        rm /root/audiobook_webhook/webhook_server.pid
        echo "✅ Webhook server stopped"
    else
        echo "⚠️  Process not running"
        rm /root/audiobook_webhook/webhook_server.pid
    fi
else
    pkill -f audiobook_webhook_server.py && echo "✅ Stopped" || echo "⚠️  Not running"
fi
EOF
    
    # Status script
    cat > status.sh << 'EOF'
#!/bin/bash
echo "=== Webhook Server Status ==="
if [ -f /root/audiobook_webhook/webhook_server.pid ]; then
    PID=$(cat /root/audiobook_webhook/webhook_server.pid)
    if kill -0 $PID 2>/dev/null; then
        echo "✅ Running (PID: $PID)"
        ps aux | grep $PID | grep -v grep
    else
        echo "❌ Not running"
    fi
else
    if pgrep -f audiobook_webhook_server.py > /dev/null; then
        echo "⚠️  Running (no PID file)"
        ps aux | grep audiobook_webhook_server.py | grep -v grep
    else
        echo "❌ Not running"
    fi
fi
echo ""
echo "📁 Uploads: \$(ls -1 /root/audiobook_webhook/uploads/ 2>/dev/null | wc -l) files"
echo "📋 Recent logs:"
tail -5 /root/audiobook_webhook/logs/webhook_server.log 2>/dev/null || echo "No logs yet"
EOF
    
    # Restart script
    cat > restart.sh << 'EOF'
#!/bin/bash
/root/audiobook_webhook/stop.sh
sleep 2
/root/audiobook_webhook/start.sh
EOF
    
    chmod +x *.sh
    echo "✅ Management scripts created"
ENDSSH
echo -e "${GREEN}✅ Management scripts created${NC}"
echo ""

# Start the webhook server
echo -e "${YELLOW}[12/12] Starting webhook server...${NC}"
sshpass -p "${REMOTE_PASSWORD}" ssh -o StrictHostKeyChecking=no -p ${REMOTE_PORT} ${REMOTE_USER}@${REMOTE_HOST} "/root/audiobook_webhook/start.sh"
sleep 3
sshpass -p "${REMOTE_PASSWORD}" ssh -o StrictHostKeyChecking=no -p ${REMOTE_PORT} ${REMOTE_USER}@${REMOTE_HOST} "/root/audiobook_webhook/status.sh"
echo ""

# Final instructions
echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  🎉 Deployment Complete!                                   ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}📍 Installation:${NC}"
echo -e "   Server: ${REMOTE_HOST} (websolutionsserver.net)"
echo -e "   Location: /root/audiobook_webhook"
echo -e "   Port: ${WEBHOOK_PORT}"
echo ""
echo -e "${BLUE}🔧 Management Commands:${NC}"
echo -e "   Start:   ssh root@${REMOTE_HOST} '/root/audiobook_webhook/start.sh'"
echo -e "   Stop:    ssh root@${REMOTE_HOST} '/root/audiobook_webhook/stop.sh'"
echo -e "   Status:  ssh root@${REMOTE_HOST} '/root/audiobook_webhook/status.sh'"
echo -e "   Restart: ssh root@${REMOTE_HOST} '/root/audiobook_webhook/restart.sh'"
echo ""
echo -e "${YELLOW}⚠️  IMPORTANT: Configure Nginx & SSL${NC}"
echo -e "   SSH to your server:"
echo -e "   ${CYAN}ssh root@${REMOTE_HOST}${NC}"
echo ""
echo -e "   Then run the SSL setup script:"
echo -e "   ${CYAN}cd /root/audiobook_webhook${NC}"
echo -e "   ${CYAN}./setup_ssl_both_domains.sh${NC}"
echo ""
echo -e "   This will:"
echo -e "   • Configure Nginx for both domains (websolutionsserver.net and audiobooksmith.app)"
echo -e "   • Obtain SSL certificates from Let's Encrypt"
echo -e "   • Set up automatic SSL renewal"
echo -e "   • Configure webhook routes"
echo ""
echo -e "${BLUE}🧪 Test (after SSL setup):${NC}"
echo -e "   ${CYAN}curl https://audiobooksmith.app/webhook/health${NC}"
echo -e "   ${CYAN}curl https://websolutionsserver.net/webhook/health${NC}"
echo ""
echo -e "${GREEN}✅ Webhook server is running!${NC}"
echo ""
