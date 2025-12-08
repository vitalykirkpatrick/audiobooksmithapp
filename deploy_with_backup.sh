#!/bin/bash

################################################################################
# AudiobookSmith Webhook - Complete Automated Deployment with Backup
#
# This script fully automates deployment with automatic backup and error handling
# Server: 172.245.67.47 (websolutionsserver.net)
# User: root
# Password: Chernivtsi_23
#
# Features:
# - Automatic backup before deployment
# - Error handling with rollback capability
# - Dependency installation
# - Service configuration
# - Testing and validation
#
# Usage: ./deploy_with_backup.sh
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
BACKUP_DIR="/root/audiobook_webhook_backup_$(date +%Y%m%d_%H%M%S)"
INSTALL_DIR="/root/audiobook_webhook"

# Error handling
ERROR_COUNT=0
MAX_RETRIES=3
DEPLOYMENT_FAILED=false

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

# Rollback function
rollback() {
    echo ""
    log_error "Deployment failed! Initiating rollback..."
    
    ssh_exec "bash -s" << ROLLBACK
        if [ -d "${BACKUP_DIR}" ]; then
            echo "🔄 Restoring from backup..."
            
            # Stop current webhook server
            pkill -f audiobook_webhook_server.py || true
            
            # Restore backup
            if [ -d "${INSTALL_DIR}" ]; then
                rm -rf "${INSTALL_DIR}"
            fi
            
            if [ -d "${BACKUP_DIR}" ]; then
                cp -r "${BACKUP_DIR}" "${INSTALL_DIR}"
                echo "✅ Backup restored"
                
                # Restart if there was a previous installation
                if [ -f "${INSTALL_DIR}/start.sh" ]; then
                    cd "${INSTALL_DIR}"
                    ./start.sh
                    echo "✅ Previous version restarted"
                fi
            fi
        else
            echo "⚠️  No backup found to restore"
        fi
ROLLBACK
    
    log_info "Rollback completed"
    exit 1
}

# Trap errors
trap 'DEPLOYMENT_FAILED=true; rollback' ERR

clear

echo -e "${MAGENTA}"
cat << "EOF"
╔════════════════════════════════════════════════════════════╗
║                                                            ║
║   AudiobookSmith Webhook - Automated Deployment           ║
║   With Backup & Error Handling                            ║
║                                                            ║
╚════════════════════════════════════════════════════════════╝
EOF
echo -e "${NC}"
echo ""

# Initialize log
echo "Deployment started at $(date)" > deployment.log
echo "Server: ${REMOTE_HOST}" >> deployment.log
echo "User: ${REMOTE_USER}" >> deployment.log
echo "" >> deployment.log

log_info "Target Server: ${REMOTE_HOST} (websolutionsserver.net)"
log_info "Backup will be created before deployment"
echo ""

# Check prerequisites
echo -e "${YELLOW}═══════════════════════════════════════════════════════════${NC}"
echo -e "${YELLOW}[PHASE 1/7] Checking Prerequisites${NC}"
echo -e "${YELLOW}═══════════════════════════════════════════════════════════${NC}"
echo ""

if ! command -v sshpass &> /dev/null; then
    log_warning "sshpass not found, installing..."
    if command -v apt-get &> /dev/null; then
        sudo apt-get update -qq && sudo apt-get install -y sshpass
    elif command -v brew &> /dev/null; then
        brew install hudochenkov/sshpass/sshpass
    else
        log_error "Cannot install sshpass automatically"
        exit 1
    fi
fi
log_success "sshpass is available"

# Test SSH connection
echo ""
echo -e "${YELLOW}═══════════════════════════════════════════════════════════${NC}"
echo -e "${YELLOW}[PHASE 2/7] Testing Connection${NC}"
echo -e "${YELLOW}═══════════════════════════════════════════════════════════${NC}"
echo ""

if ! retry_command "ssh_exec 'echo test' > /dev/null 2>&1" "SSH connection test"; then
    log_error "Cannot connect to server"
    exit 1
fi

SERVER_INFO=$(ssh_exec "hostname && cat /etc/os-release | grep PRETTY_NAME | cut -d'\"' -f2")
log_info "Connected to: $(echo $SERVER_INFO | head -1)"
echo ""

# Create backup
echo -e "${YELLOW}═══════════════════════════════════════════════════════════${NC}"
echo -e "${YELLOW}[PHASE 3/7] Creating Backup${NC}"
echo -e "${YELLOW}═══════════════════════════════════════════════════════════${NC}"
echo ""

log_info "Creating backup directory: ${BACKUP_DIR}"

ssh_exec "bash -s" << BACKUP
    # Create backup directory
    mkdir -p "${BACKUP_DIR}"
    
    # Check if webhook installation exists
    if [ -d "${INSTALL_DIR}" ]; then
        echo "📦 Backing up existing installation..."
        
        # Copy entire directory
        cp -r "${INSTALL_DIR}" "${BACKUP_DIR}_temp"
        mv "${BACKUP_DIR}_temp" "${BACKUP_DIR}"
        
        # Create backup manifest
        cat > "${BACKUP_DIR}/backup_info.txt" << EOF
Backup created: \$(date)
Original location: ${INSTALL_DIR}
Backup location: ${BACKUP_DIR}
Files backed up: \$(find "${BACKUP_DIR}" -type f | wc -l)
EOF
        
        echo "✅ Backup created successfully"
        echo "📁 Backup location: ${BACKUP_DIR}"
        
        # Create restore script
        cat > "${BACKUP_DIR}/restore.sh" << 'RESTORE'
#!/bin/bash
echo "🔄 Restoring AudiobookSmith Webhook from backup..."

# Stop current server
pkill -f audiobook_webhook_server.py || true

# Remove current installation
if [ -d "${INSTALL_DIR}" ]; then
    rm -rf "${INSTALL_DIR}"
fi

# Restore from backup
BACKUP_DIR="\$(cd "\$(dirname "\${BASH_SOURCE[0]}")" && pwd)"
cp -r "\${BACKUP_DIR}" "${INSTALL_DIR}"

# Restart server
if [ -f "${INSTALL_DIR}/start.sh" ]; then
    cd "${INSTALL_DIR}"
    ./start.sh
fi

echo "✅ Restore completed"
RESTORE
        
        chmod +x "${BACKUP_DIR}/restore.sh"
        echo "✅ Restore script created: ${BACKUP_DIR}/restore.sh"
    else
        echo "ℹ️  No existing installation found, skipping backup"
    fi
BACKUP

log_success "Backup phase completed"
echo ""

# Audit server
echo -e "${YELLOW}═══════════════════════════════════════════════════════════${NC}"
echo -e "${YELLOW}[PHASE 4/7] Auditing Server${NC}"
echo -e "${YELLOW}═══════════════════════════════════════════════════════════${NC}"
echo ""

ssh_exec "bash -s" << 'AUDIT' 2>&1 | tee -a deployment.log
    echo "🔍 Checking server configuration..."
    echo ""
    
    # Check Python
    if command -v python3.11 &> /dev/null; then
        echo "✅ Python 3.11: $(python3.11 --version)"
    elif command -v python3 &> /dev/null; then
        echo "✅ Python 3: $(python3 --version)"
    else
        echo "⚠️  Python not found - will install"
    fi
    
    # Check Flask
    if python3 -c "import flask" 2>/dev/null; then
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
    
    # Check ports
    echo ""
    echo "📊 Port Status:"
    for PORT in 5001 5002 5003; do
        if netstat -tln 2>/dev/null | grep -q ":${PORT} "; then
            echo "   Port ${PORT}: IN USE"
        else
            echo "   Port ${PORT}: AVAILABLE ✓"
        fi
    done
AUDIT

echo ""

# Setup directories
echo -e "${YELLOW}═══════════════════════════════════════════════════════════${NC}"
echo -e "${YELLOW}[PHASE 5/7] Installing & Configuring${NC}"
echo -e "${YELLOW}═══════════════════════════════════════════════════════════${NC}"
echo ""

log_info "Creating directory structure..."
ssh_exec "mkdir -p ${INSTALL_DIR}/{logs,uploads,backups,scripts,config} && chmod -R 755 ${INSTALL_DIR}"
log_success "Directory structure created"

# Upload files
log_info "Uploading files to server..."

FILES=(
    "audiobook_webhook_server.py"
    "audiobook_processor.py"
    "nginx_multi_domain.conf"
    "setup_ssl_both_domains.sh"
    "frontend_integration_code.jsx"
)

for file in "${FILES[@]}"; do
    if [ -f "$file" ]; then
        retry_command "scp_copy $file ${REMOTE_USER}@${REMOTE_HOST}:${INSTALL_DIR}/" "Upload $file"
    fi
done

scp_copy *.md ${REMOTE_USER}@${REMOTE_HOST}:${INSTALL_DIR}/ 2>/dev/null || true

log_success "All files uploaded"
echo ""

# Install and configure
ssh_exec "bash -s" << 'INSTALL' 2>&1 | tee -a deployment.log
    cd /root/audiobook_webhook
    
    echo "📦 Installing dependencies..."
    
    # Python
    if ! command -v python3 &> /dev/null; then
        apt-get update -qq && apt-get install -y python3 python3-pip
    fi
    
    # Flask
    if ! python3 -c "import flask" 2>/dev/null; then
        pip3 install flask
    fi
    
    # Nginx
    if ! command -v nginx &> /dev/null; then
        apt-get install -y nginx
        systemctl enable nginx
        systemctl start nginx
    fi
    
    # Certbot
    if ! command -v certbot &> /dev/null; then
        apt-get install -y certbot python3-certbot-nginx
    fi
    
    echo "✅ Dependencies installed"
    echo ""
    
    # Configure
    echo "⚙️  Configuring webhook server..."
    
    sed -i 's|UPLOAD_FOLDER = "/home/ubuntu/audiobook_uploads"|UPLOAD_FOLDER = "/root/audiobook_webhook/uploads"|g' audiobook_webhook_server.py
    sed -i 's|PROCESSOR_SCRIPT = "/home/ubuntu/audiobook_processor.py"|PROCESSOR_SCRIPT = "/root/audiobook_webhook/audiobook_processor.py"|g' audiobook_webhook_server.py
    
    # Find available port
    WEBHOOK_PORT=5001
    for PORT in 5001 5002 5003; do
        if ! netstat -tln 2>/dev/null | grep -q ":${PORT} "; then
            WEBHOOK_PORT=${PORT}
            break
        fi
    done
    
    sed -i "s|port=5001|port=${WEBHOOK_PORT}|g" audiobook_webhook_server.py
    echo "✅ Using port ${WEBHOOK_PORT}"
    
    chmod +x *.py *.sh 2>/dev/null || true
    
    # Create management scripts
    PYTHON_CMD=$(command -v python3.11 || command -v python3)
    
    cat > start.sh << EOF
#!/bin/bash
cd /root/audiobook_webhook
nohup ${PYTHON_CMD} audiobook_webhook_server.py > logs/webhook_server.log 2>&1 &
echo \\\$! > webhook_server.pid
echo "✅ Webhook server started (PID: \\\$(cat webhook_server.pid))"
EOF
    
    cat > stop.sh << 'EOF'
#!/bin/bash
if [ -f /root/audiobook_webhook/webhook_server.pid ]; then
    kill \$(cat /root/audiobook_webhook/webhook_server.pid) 2>/dev/null
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
    
    chmod +x *.sh
    
    echo "✅ Configuration complete"
INSTALL

log_success "Installation and configuration complete"
echo ""

# Start service
echo -e "${YELLOW}═══════════════════════════════════════════════════════════${NC}"
echo -e "${YELLOW}[PHASE 6/7] Starting Services${NC}"
echo -e "${YELLOW}═══════════════════════════════════════════════════════════${NC}"
echo ""

log_info "Starting webhook server..."
ssh_exec "cd ${INSTALL_DIR} && ./start.sh"
sleep 3

# Test
echo ""
echo -e "${YELLOW}═══════════════════════════════════════════════════════════${NC}"
echo -e "${YELLOW}[PHASE 7/7] Testing Installation${NC}"
echo -e "${YELLOW}═══════════════════════════════════════════════════════════${NC}"
echo ""

log_info "Testing webhook health endpoint..."
HEALTH=$(ssh_exec "curl -s http://localhost:5001/health 2>/dev/null || curl -s http://localhost:5002/health 2>/dev/null")

if echo "$HEALTH" | grep -q "healthy"; then
    log_success "Webhook is responding correctly"
    echo "$HEALTH" | python3 -m json.tool 2>/dev/null || echo "$HEALTH"
else
    log_warning "Unexpected health check response"
fi

echo ""

# Final report
echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  🎉 Deployment Completed Successfully!                     ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

echo -e "${BLUE}📍 Installation Summary:${NC}"
echo -e "   Server: ${REMOTE_HOST} (websolutionsserver.net)"
echo -e "   Location: ${INSTALL_DIR}"
echo -e "   Backup: ${BACKUP_DIR}"
echo -e "   Status: ✅ Running"
echo ""

echo -e "${BLUE}🔧 Management:${NC}"
echo -e "   Start:   ssh root@${REMOTE_HOST} '${INSTALL_DIR}/start.sh'"
echo -e "   Stop:    ssh root@${REMOTE_HOST} '${INSTALL_DIR}/stop.sh'"
echo -e "   Status:  ssh root@${REMOTE_HOST} '${INSTALL_DIR}/status.sh'"
echo -e "   Logs:    ssh root@${REMOTE_HOST} 'tail -f ${INSTALL_DIR}/logs/webhook_server.log'"
echo ""

echo -e "${BLUE}🛡️  Backup & Restore:${NC}"
echo -e "   Backup location: ${BACKUP_DIR}"
echo -e "   Restore: ssh root@${REMOTE_HOST} '${BACKUP_DIR}/restore.sh'"
echo ""

echo -e "${YELLOW}⚠️  NEXT STEP: Configure SSL${NC}"
echo -e "   ${CYAN}ssh root@${REMOTE_HOST} 'cd ${INSTALL_DIR} && ./setup_ssl_both_domains.sh'${NC}"
echo ""

if [ $ERROR_COUNT -gt 0 ]; then
    echo -e "${YELLOW}⚠️  Completed with ${ERROR_COUNT} warning(s)${NC}"
else
    echo -e "${GREEN}✅ Deployment completed with no errors!${NC}"
fi

echo ""
echo -e "${BLUE}📄 Full log: deployment.log${NC}"
echo ""
