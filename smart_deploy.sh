#!/bin/bash

################################################################################
# AudiobookSmith Webhook - Smart Deployment Script
#
# This script intelligently deploys the webhook integration to your server
# It adapts to your existing setup (N8N, Nginx, SSL, etc.)
#
# Usage: ./smart_deploy.sh [remote_host] [remote_user]
# Example: ./smart_deploy.sh 172.245.67.47 root
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
REMOTE_HOST="${1:-172.245.67.47}"
REMOTE_USER="${2:-root}"
REMOTE_PORT="22"
WEBHOOK_PORT="5001"  # Will be adjusted if port is in use

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  AudiobookSmith Webhook - Smart Deployment                ║${NC}"
echo -e "${BLUE}║  Target: ${REMOTE_HOST} (websolutionsserver.net)${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Test SSH connection
echo -e "${YELLOW}[1/12] Testing SSH connection...${NC}"
if ! ssh -p ${REMOTE_PORT} -o ConnectTimeout=10 ${REMOTE_USER}@${REMOTE_HOST} exit 2>/dev/null; then
    echo -e "${RED}❌ Cannot connect to ${REMOTE_HOST}${NC}"
    echo -e "${YELLOW}   Trying with password authentication...${NC}"
    if ! ssh -p ${REMOTE_PORT} -o ConnectTimeout=10 ${REMOTE_USER}@${REMOTE_HOST} exit; then
        echo -e "${RED}❌ SSH connection failed${NC}"
        exit 1
    fi
fi
echo -e "${GREEN}✅ SSH connection successful${NC}"
echo ""

# Run audit on remote server
echo -e "${YELLOW}[2/12] Auditing remote server...${NC}"
ssh -p ${REMOTE_PORT} ${REMOTE_USER}@${REMOTE_HOST} "bash -s" << 'AUDIT_SCRIPT'
    # Quick audit
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
        echo "❌ Nginx not found"
        exit 1
    fi
    
    # Check N8N
    if pgrep -f "n8n" > /dev/null; then
        N8N_PORT=$(netstat -tlnp 2>/dev/null | grep $(pgrep -f "n8n" | head -1) | awk '{print $4}' | cut -d':' -f2 | head -1)
        echo "✅ N8N running on port ${N8N_PORT}"
    fi
    
    # Find available port
    for PORT in 5001 5002 5003 5004 5005; do
        if ! netstat -tln 2>/dev/null | grep -q ":${PORT} "; then
            echo "✅ Port ${PORT} is available"
            echo "WEBHOOK_PORT=${PORT}" > /tmp/webhook_config.env
            break
        fi
    done
    
    # Check SSL
    if [ -d /etc/letsencrypt/live ]; then
        CERT_COUNT=$(sudo ls -1 /etc/letsencrypt/live 2>/dev/null | wc -l)
        echo "✅ SSL certificates: ${CERT_COUNT} found"
    fi
AUDIT_SCRIPT

echo -e "${GREEN}✅ Server audit complete${NC}"
echo ""

# Get configuration from remote
echo -e "${YELLOW}[3/12] Getting server configuration...${NC}"
scp -P ${REMOTE_PORT} ${REMOTE_USER}@${REMOTE_HOST}:/tmp/webhook_config.env /tmp/webhook_config.env 2>/dev/null || true
if [ -f /tmp/webhook_config.env ]; then
    source /tmp/webhook_config.env
    echo -e "${GREEN}✅ Will use port ${WEBHOOK_PORT}${NC}"
fi
echo ""

# Create remote directory structure
echo -e "${YELLOW}[4/12] Creating directory structure...${NC}"
ssh -p ${REMOTE_PORT} ${REMOTE_USER}@${REMOTE_HOST} "bash -s" << 'ENDSSH'
    mkdir -p ~/audiobook_webhook/{logs,uploads,backups,scripts,config}
    chmod 755 ~/audiobook_webhook
    chmod 755 ~/audiobook_webhook/uploads
    chmod 755 ~/audiobook_webhook/logs
    echo "✅ Directories created"
ENDSSH
echo -e "${GREEN}✅ Directory structure created${NC}"
echo ""

# Copy files
echo -e "${YELLOW}[5/12] Copying webhook server...${NC}"
scp -P ${REMOTE_PORT} /home/ubuntu/audiobook_webhook_server.py \
    ${REMOTE_USER}@${REMOTE_HOST}:~/audiobook_webhook/
echo -e "${GREEN}✅ Webhook server copied${NC}"
echo ""

echo -e "${YELLOW}[6/12] Copying audiobook processor...${NC}"
scp -P ${REMOTE_PORT} /home/ubuntu/audiobook_processor.py \
    ${REMOTE_USER}@${REMOTE_HOST}:~/audiobook_webhook/
echo -e "${GREEN}✅ Audiobook processor copied${NC}"
echo ""

echo -e "${YELLOW}[7/12] Copying documentation...${NC}"
scp -P ${REMOTE_PORT} \
    /home/ubuntu/INTEGRATION_SUMMARY.md \
    /home/ubuntu/QUICK_START_GUIDE.md \
    /home/ubuntu/WEBHOOK_INTEGRATION_DOCUMENTATION.md \
    /home/ubuntu/DEPLOYMENT_GUIDE.md \
    /home/ubuntu/frontend_integration_code.jsx \
    ${REMOTE_USER}@${REMOTE_HOST}:~/audiobook_webhook/
echo -e "${GREEN}✅ Documentation copied${NC}"
echo ""

# Configure and install
echo -e "${YELLOW}[8/12] Configuring webhook server...${NC}"
ssh -p ${REMOTE_PORT} ${REMOTE_USER}@${REMOTE_HOST} "bash -s" << ENDSSH
    cd ~/audiobook_webhook
    
    # Update paths in webhook server
    sed -i 's|UPLOAD_FOLDER = "/home/ubuntu/audiobook_uploads"|UPLOAD_FOLDER = "'$HOME'/audiobook_webhook/uploads"|g' audiobook_webhook_server.py
    sed -i 's|PROCESSOR_SCRIPT = "/home/ubuntu/audiobook_processor.py"|PROCESSOR_SCRIPT = "'$HOME'/audiobook_webhook/audiobook_processor.py"|g' audiobook_webhook_server.py
    sed -i 's|port=5001|port=${WEBHOOK_PORT}|g' audiobook_webhook_server.py
    
    # Make executable
    chmod +x audiobook_webhook_server.py audiobook_processor.py
    
    echo "✅ Configuration updated"
ENDSSH
echo -e "${GREEN}✅ Webhook server configured${NC}"
echo ""

# Install dependencies
echo -e "${YELLOW}[9/12] Installing dependencies...${NC}"
ssh -p ${REMOTE_PORT} ${REMOTE_USER}@${REMOTE_HOST} "bash -s" << 'ENDSSH'
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
ENDSSH
echo -e "${GREEN}✅ Dependencies installed${NC}"
echo ""

# Create management scripts
echo -e "${YELLOW}[10/12] Creating management scripts...${NC}"
ssh -p ${REMOTE_PORT} ${REMOTE_USER}@${REMOTE_HOST} "bash -s" << 'ENDSSH'
    cd ~/audiobook_webhook
    
    # Determine Python command
    if command -v python3.11 &> /dev/null; then
        PYTHON_CMD="python3.11"
    else
        PYTHON_CMD="python3"
    fi
    
    # Start script
    cat > start.sh << EOF
#!/bin/bash
cd ~/audiobook_webhook
nohup ${PYTHON_CMD} audiobook_webhook_server.py > logs/webhook_server.log 2>&1 &
echo \$! > webhook_server.pid
echo "✅ Webhook server started (PID: \$(cat webhook_server.pid))"
echo "📊 View logs: tail -f ~/audiobook_webhook/logs/webhook_server.log"
EOF
    
    # Stop script
    cat > stop.sh << 'EOF'
#!/bin/bash
if [ -f ~/audiobook_webhook/webhook_server.pid ]; then
    PID=$(cat ~/audiobook_webhook/webhook_server.pid)
    if kill -0 $PID 2>/dev/null; then
        kill $PID
        rm ~/audiobook_webhook/webhook_server.pid
        echo "✅ Webhook server stopped"
    else
        echo "⚠️  Process not running"
        rm ~/audiobook_webhook/webhook_server.pid
    fi
else
    pkill -f audiobook_webhook_server.py && echo "✅ Stopped" || echo "⚠️  Not running"
fi
EOF
    
    # Status script
    cat > status.sh << 'EOF'
#!/bin/bash
echo "=== Webhook Server Status ==="
if [ -f ~/audiobook_webhook/webhook_server.pid ]; then
    PID=$(cat ~/audiobook_webhook/webhook_server.pid)
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
echo "📁 Uploads: \$(ls -1 ~/audiobook_webhook/uploads/ 2>/dev/null | wc -l) files"
echo "📋 Recent logs:"
tail -5 ~/audiobook_webhook/logs/webhook_server.log 2>/dev/null || echo "No logs yet"
EOF
    
    # Restart script
    cat > restart.sh << 'EOF'
#!/bin/bash
~/audiobook_webhook/stop.sh
sleep 2
~/audiobook_webhook/start.sh
EOF
    
    chmod +x *.sh
    echo "✅ Management scripts created"
ENDSSH
echo -e "${GREEN}✅ Management scripts created${NC}"
echo ""

# Create Nginx configuration
echo -e "${YELLOW}[11/12] Creating Nginx configuration...${NC}"
ssh -p ${REMOTE_PORT} ${REMOTE_USER}@${REMOTE_HOST} "bash -s" << ENDSSH
    # Create Nginx config template
    cat > ~/audiobook_webhook/nginx_config_template.conf << 'EOF'
# AudiobookSmith Webhook - Nginx Location Block
# Add this to your existing Nginx server block

location /webhook/audiobook-process {
    proxy_pass http://127.0.0.1:${WEBHOOK_PORT}/webhook/audiobook-process;
    proxy_set_header Host \$host;
    proxy_set_header X-Real-IP \$remote_addr;
    proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto \$scheme;
    
    client_max_body_size 100M;
    proxy_connect_timeout 300s;
    proxy_send_timeout 300s;
    proxy_read_timeout 300s;
}

location /webhook/health {
    proxy_pass http://127.0.0.1:${WEBHOOK_PORT}/health;
    proxy_set_header Host \$host;
    access_log off;
}
EOF
    
    echo "✅ Nginx config template created at ~/audiobook_webhook/nginx_config_template.conf"
ENDSSH
echo -e "${GREEN}✅ Nginx configuration template created${NC}"
echo ""

# Start the webhook server
echo -e "${YELLOW}[12/12] Starting webhook server...${NC}"
ssh -p ${REMOTE_PORT} ${REMOTE_USER}@${REMOTE_HOST} "~/audiobook_webhook/start.sh"
sleep 3
ssh -p ${REMOTE_PORT} ${REMOTE_USER}@${REMOTE_HOST} "~/audiobook_webhook/status.sh"
echo ""

# Final instructions
echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  🎉 Deployment Complete!                                   ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}📍 Installation:${NC}"
echo -e "   Location: ${REMOTE_HOST}:~/audiobook_webhook"
echo -e "   Port: ${WEBHOOK_PORT}"
echo ""
echo -e "${BLUE}🔧 Management:${NC}"
echo -e "   Start:   ssh ${REMOTE_USER}@${REMOTE_HOST} '~/audiobook_webhook/start.sh'"
echo -e "   Stop:    ssh ${REMOTE_USER}@${REMOTE_HOST} '~/audiobook_webhook/stop.sh'"
echo -e "   Status:  ssh ${REMOTE_USER}@${REMOTE_HOST} '~/audiobook_webhook/status.sh'"
echo -e "   Restart: ssh ${REMOTE_USER}@${REMOTE_HOST} '~/audiobook_webhook/restart.sh'"
echo ""
echo -e "${YELLOW}⚠️  IMPORTANT: Configure Nginx${NC}"
echo -e "   1. SSH to your server: ssh ${REMOTE_USER}@${REMOTE_HOST}"
echo -e "   2. Edit your existing Nginx config (likely /etc/nginx/sites-available/default or n8n)"
echo -e "   3. Add the location blocks from: ~/audiobook_webhook/nginx_config_template.conf"
echo -e "   4. Test: sudo nginx -t"
echo -e "   5. Reload: sudo systemctl reload nginx"
echo ""
echo -e "${BLUE}🧪 Test:${NC}"
echo -e "   Internal: curl http://localhost:${WEBHOOK_PORT}/health"
echo -e "   External: curl https://websolutionsserver.net/webhook/health"
echo ""
echo -e "${GREEN}✅ Webhook server is running!${NC}"
echo ""
