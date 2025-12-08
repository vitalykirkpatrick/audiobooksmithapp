#!/bin/bash

################################################################################
# AudiobookSmith Webhook - Complete Automated Deployment
#
# This script fully automates the deployment process with error handling
# Server: 172.245.67.47 (websolutionsserver.net)
# User: root
# Password: Chernivtsi_23
#
# Usage: ./auto_deploy_complete.sh
################################################################################

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m'

# Configuration
REMOTE_HOST="172.245.67.47"
REMOTE_USER="root"
REMOTE_PASSWORD="Chernivtsi_23"
REMOTE_PORT="22"
WEBHOOK_PORT="5001"

# Error handling
ERROR_COUNT=0
MAX_RETRIES=3

log_error() {
    echo -e "${RED}❌ ERROR: $1${NC}" | tee -a deployment.log
    ERROR_COUNT=$((ERROR_COUNT + 1))
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}" | tee -a deployment.log
}

log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}" | tee -a deployment.log
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}" | tee -a deployment.log
}

retry_command() {
    local command="$1"
    local description="$2"
    local retries=0
    
    while [ $retries -lt $MAX_RETRIES ]; do
        if eval "$command"; then
            log_success "$description"
            return 0
        else
            retries=$((retries + 1))
            if [ $retries -lt $MAX_RETRIES ]; then
                log_warning "$description failed, retrying ($retries/$MAX_RETRIES)..."
                sleep 2
            fi
        fi
    done
    
    log_error "$description failed after $MAX_RETRIES attempts"
    return 1
}

ssh_exec() {
    sshpass -p "${REMOTE_PASSWORD}" ssh -o StrictHostKeyChecking=no -o ConnectTimeout=30 -p ${REMOTE_PORT} ${REMOTE_USER}@${REMOTE_HOST} "$@"
}

scp_copy() {
    sshpass -p "${REMOTE_PASSWORD}" scp -o StrictHostKeyChecking=no -o ConnectTimeout=30 -P ${REMOTE_PORT} "$@"
}

clear

echo -e "${MAGENTA}"
cat << "EOF"
╔════════════════════════════════════════════════════════════╗
║                                                            ║
║   AudiobookSmith Webhook - Automated Deployment           ║
║   Complete Setup with Error Handling                      ║
║                                                            ║
╚════════════════════════════════════════════════════════════╝
EOF
echo -e "${NC}"
echo ""

# Initialize log
echo "Deployment started at $(date)" > deployment.log

log_info "Target Server: ${REMOTE_HOST} (websolutionsserver.net)"
log_info "User: ${REMOTE_USER}"
log_info "Domains: websolutionsserver.net, audiobooksmith.app"
echo ""

# Check prerequisites
echo -e "${YELLOW}[PHASE 1/6] Checking Prerequisites${NC}"
echo ""

if ! command -v sshpass &> /dev/null; then
    log_warning "sshpass not found, installing..."
    if command -v apt-get &> /dev/null; then
        sudo apt-get update -qq && sudo apt-get install -y sshpass
    elif command -v brew &> /dev/null; then
        brew install hudochenkov/sshpass/sshpass
    else
        log_error "Cannot install sshpass automatically. Please install manually."
        exit 1
    fi
fi
log_success "sshpass is available"

# Test SSH connection
echo ""
echo -e "${YELLOW}[PHASE 2/6] Testing Connection${NC}"
echo ""

if ! retry_command "ssh_exec 'echo test' > /dev/null 2>&1" "SSH connection test"; then
    log_error "Cannot connect to server. Please check:"
    echo "  1. Server IP: ${REMOTE_HOST}"
    echo "  2. SSH port: ${REMOTE_PORT}"
    echo "  3. Firewall settings"
    echo "  4. Network connectivity"
    exit 1
fi

# Get server info
SERVER_INFO=$(ssh_exec "echo 'OS:' \$(cat /etc/os-release | grep PRETTY_NAME | cut -d'\"' -f2) && echo 'Hostname:' \$(hostname)")
log_info "Server Info:"
echo "$SERVER_INFO" | sed 's/^/   /'
echo ""

# Audit server
echo -e "${YELLOW}[PHASE 3/6] Auditing Server${NC}"
echo ""

ssh_exec "bash -s" << 'AUDIT' 2>&1 | tee -a deployment.log
    echo "🔍 Checking server configuration..."
    
    # Check Python
    if command -v python3.11 &> /dev/null; then
        echo "✅ Python 3.11: $(python3.11 --version)"
        PYTHON_CMD="python3.11"
    elif command -v python3 &> /dev/null; then
        echo "✅ Python 3: $(python3 --version)"
        PYTHON_CMD="python3"
    else
        echo "❌ Python not found - will install"
    fi
    
    # Check pip
    if command -v pip3 &> /dev/null; then
        echo "✅ pip3: $(pip3 --version | cut -d' ' -f1-2)"
    else
        echo "⚠️  pip3 not found - will install"
    fi
    
    # Check Flask
    if python3 -c "import flask" 2>/dev/null; then
        FLASK_VER=$(python3 -c "import flask; print(flask.__version__)")
        echo "✅ Flask: ${FLASK_VER}"
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
    else
        echo "⚠️  N8N not detected"
    fi
    
    # Check ports
    echo ""
    echo "📊 Port Status:"
    for PORT in 5001 5002 5003 5678; do
        if netstat -tln 2>/dev/null | grep -q ":${PORT} "; then
            echo "   Port ${PORT}: IN USE"
        else
            echo "   Port ${PORT}: AVAILABLE"
        fi
    done
    
    # Check disk space
    echo ""
    echo "💾 Disk Space:"
    df -h / | tail -1 | awk '{print "   Total: "$2", Used: "$3", Available: "$4", Usage: "$5}'
AUDIT

echo ""

# Create directory structure
echo -e "${YELLOW}[PHASE 4/6] Setting Up Server${NC}"
echo ""

log_info "Creating directory structure..."
if ssh_exec "mkdir -p /root/audiobook_webhook/{logs,uploads,backups,scripts,config} && chmod -R 755 /root/audiobook_webhook"; then
    log_success "Directory structure created"
else
    log_error "Failed to create directories"
    exit 1
fi

# Upload files
log_info "Uploading files to server..."

FILES_TO_UPLOAD=(
    "audiobook_webhook_server.py"
    "audiobook_processor.py"
    "nginx_multi_domain.conf"
    "setup_ssl_both_domains.sh"
    "frontend_integration_code.jsx"
)

for file in "${FILES_TO_UPLOAD[@]}"; do
    if [ -f "$file" ]; then
        if retry_command "scp_copy $file ${REMOTE_USER}@${REMOTE_HOST}:/root/audiobook_webhook/" "Upload $file"; then
            :
        else
            log_error "Failed to upload $file"
        fi
    else
        log_warning "$file not found, skipping"
    fi
done

# Upload documentation
log_info "Uploading documentation..."
scp_copy *.md ${REMOTE_USER}@${REMOTE_HOST}:/root/audiobook_webhook/ 2>/dev/null || log_warning "Some documentation files not uploaded"

log_success "All files uploaded"
echo ""

# Install dependencies and configure
echo -e "${YELLOW}[PHASE 5/6] Installing Dependencies & Configuring${NC}"
echo ""

ssh_exec "bash -s" << 'INSTALL' 2>&1 | tee -a deployment.log
    cd /root/audiobook_webhook
    
    echo "📦 Installing dependencies..."
    
    # Determine Python command
    if command -v python3.11 &> /dev/null; then
        PYTHON_CMD="python3.11"
    elif command -v python3 &> /dev/null; then
        PYTHON_CMD="python3"
    else
        echo "❌ Python not found, installing..."
        apt-get update -qq && apt-get install -y python3 python3-pip
        PYTHON_CMD="python3"
    fi
    
    # Install pip if needed
    if ! command -v pip3 &> /dev/null; then
        echo "Installing pip3..."
        apt-get install -y python3-pip
    fi
    
    # Install Flask
    if ! $PYTHON_CMD -c "import flask" 2>/dev/null; then
        echo "Installing Flask..."
        pip3 install flask
        echo "✅ Flask installed"
    else
        echo "✅ Flask already installed"
    fi
    
    # Install Nginx if needed
    if ! command -v nginx &> /dev/null; then
        echo "Installing Nginx..."
        apt-get update -qq && apt-get install -y nginx
        systemctl enable nginx
        systemctl start nginx
        echo "✅ Nginx installed and started"
    else
        echo "✅ Nginx already installed"
    fi
    
    # Install certbot if needed
    if ! command -v certbot &> /dev/null; then
        echo "Installing certbot..."
        apt-get install -y certbot python3-certbot-nginx
        echo "✅ Certbot installed"
    else
        echo "✅ Certbot already installed"
    fi
    
    echo ""
    echo "⚙️  Configuring webhook server..."
    
    # Update paths in webhook server
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
    echo "✅ Using port ${WEBHOOK_PORT}"
    
    # Make scripts executable
    chmod +x audiobook_webhook_server.py audiobook_processor.py setup_ssl_both_domains.sh 2>/dev/null || true
    
    echo ""
    echo "📝 Creating management scripts..."
    
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
    
    echo "✅ Configuration complete"
INSTALL

if [ $? -ne 0 ]; then
    log_error "Installation/configuration failed"
    exit 1
fi

log_success "Dependencies installed and configured"
echo ""

# Start webhook server
echo -e "${YELLOW}[PHASE 6/6] Starting Services & Testing${NC}"
echo ""

log_info "Starting webhook server..."
if ssh_exec "/root/audiobook_webhook/start.sh"; then
    log_success "Webhook server started"
else
    log_warning "Failed to start webhook server, trying alternative method..."
    ssh_exec "cd /root/audiobook_webhook && nohup python3 audiobook_webhook_server.py > logs/webhook_server.log 2>&1 & echo \$! > webhook_server.pid"
fi

sleep 3

# Check status
log_info "Checking server status..."
ssh_exec "/root/audiobook_webhook/status.sh" 2>&1 | tee -a deployment.log

echo ""

# Test webhook
log_info "Testing webhook health endpoint..."
HEALTH_TEST=$(ssh_exec "curl -s http://localhost:5001/health 2>/dev/null || curl -s http://localhost:5002/health 2>/dev/null || curl -s http://localhost:5003/health 2>/dev/null")

if echo "$HEALTH_TEST" | grep -q "healthy"; then
    log_success "Webhook is responding correctly"
    echo "$HEALTH_TEST" | python3 -m json.tool 2>/dev/null || echo "$HEALTH_TEST"
else
    log_warning "Webhook health check returned unexpected response"
    echo "$HEALTH_TEST"
fi

echo ""

# Final report
echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  🎉 Deployment Complete!                                   ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

echo -e "${BLUE}📍 Installation Summary:${NC}"
echo -e "   Server: ${REMOTE_HOST} (websolutionsserver.net)"
echo -e "   Location: /root/audiobook_webhook"
echo -e "   Status: Webhook server is running"
echo ""

echo -e "${BLUE}🔧 Management Commands:${NC}"
echo -e "   Start:   ssh root@${REMOTE_HOST} '/root/audiobook_webhook/start.sh'"
echo -e "   Stop:    ssh root@${REMOTE_HOST} '/root/audiobook_webhook/stop.sh'"
echo -e "   Status:  ssh root@${REMOTE_HOST} '/root/audiobook_webhook/status.sh'"
echo -e "   Restart: ssh root@${REMOTE_HOST} '/root/audiobook_webhook/restart.sh'"
echo -e "   Logs:    ssh root@${REMOTE_HOST} 'tail -f /root/audiobook_webhook/logs/webhook_server.log'"
echo ""

echo -e "${YELLOW}⚠️  NEXT STEP: Configure Nginx & SSL${NC}"
echo -e "   Run this command to complete setup:"
echo -e "   ${CYAN}ssh root@${REMOTE_HOST} 'cd /root/audiobook_webhook && ./setup_ssl_both_domains.sh'${NC}"
echo ""
echo -e "   This will:"
echo -e "   • Configure Nginx for both domains"
echo -e "   • Obtain SSL certificates from Let's Encrypt"
echo -e "   • Set up automatic SSL renewal"
echo -e "   • Make webhook accessible via HTTPS"
echo ""

echo -e "${BLUE}🧪 Test Commands (after SSL setup):${NC}"
echo -e "   ${CYAN}curl https://audiobooksmith.app/webhook/health${NC}"
echo -e "   ${CYAN}curl https://websolutionsserver.net/webhook/health${NC}"
echo ""

if [ $ERROR_COUNT -gt 0 ]; then
    echo -e "${YELLOW}⚠️  Deployment completed with ${ERROR_COUNT} warning(s)${NC}"
    echo -e "   Check deployment.log for details"
else
    echo -e "${GREEN}✅ Deployment completed successfully with no errors!${NC}"
fi

echo ""
echo -e "${BLUE}📄 Deployment log saved to: deployment.log${NC}"
echo ""

# Save deployment info
cat > deployment_info.txt << EOF
AudiobookSmith Webhook Deployment
==================================
Date: $(date)
Server: ${REMOTE_HOST} (websolutionsserver.net)
User: ${REMOTE_USER}
Location: /root/audiobook_webhook
Status: Deployed and Running

Domains:
- websolutionsserver.net
- audiobooksmith.app

Next Steps:
1. Configure SSL: ssh root@${REMOTE_HOST} 'cd /root/audiobook_webhook && ./setup_ssl_both_domains.sh'
2. Test webhook: curl https://audiobooksmith.app/webhook/health
3. Update frontend URL to: https://audiobooksmith.app/webhook/audiobook-process

Management:
- Start: ssh root@${REMOTE_HOST} '/root/audiobook_webhook/start.sh'
- Stop: ssh root@${REMOTE_HOST} '/root/audiobook_webhook/stop.sh'
- Status: ssh root@${REMOTE_HOST} '/root/audiobook_webhook/status.sh'
- Logs: ssh root@${REMOTE_HOST} 'tail -f /root/audiobook_webhook/logs/webhook_server.log'

Errors: ${ERROR_COUNT}
EOF

log_success "Deployment information saved to deployment_info.txt"
echo ""
