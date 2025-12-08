#!/bin/bash

################################################################################
# AudiobookSmith Webhook - One-File Deployment Script
#
# This script uploads and executes the deployment on your server
# Server: 172.245.67.47 (websolutionsserver.net)
# User: root
#
# Usage: 
#   1. Download this script and the deployment package
#   2. Extract: tar -xzf audiobooksmith_deployment_final.tar.gz
#   3. Run: ./deploy_to_server.sh
#
# Or if you have SSH key access:
#   ./deploy_to_server.sh --use-key
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
USE_SSH_KEY=false

# Parse arguments
if [ "$1" == "--use-key" ]; then
    USE_SSH_KEY=true
fi

clear

echo -e "${BLUE}"
cat << "EOF"
╔════════════════════════════════════════════════════════════╗
║                                                            ║
║   AudiobookSmith Webhook - Remote Deployment              ║
║   Upload & Execute on Server                              ║
║                                                            ║
╚════════════════════════════════════════════════════════════╝
EOF
echo -e "${NC}"
echo ""

echo -e "${YELLOW}Target Server: ${REMOTE_HOST}${NC}"
echo -e "${YELLOW}User: ${REMOTE_USER}${NC}"
echo ""

# Check if deployment directory exists
if [ ! -d "audiobooksmith_deployment_final" ]; then
    echo -e "${RED}❌ Error: audiobooksmith_deployment_final directory not found${NC}"
    echo -e "${YELLOW}Please extract the deployment package first:${NC}"
    echo -e "${CYAN}tar -xzf audiobooksmith_deployment_final.tar.gz${NC}"
    exit 1
fi

# Check for sshpass if using password
if [ "$USE_SSH_KEY" = false ]; then
    if ! command -v sshpass &> /dev/null; then
        echo -e "${YELLOW}⚠️  sshpass not found. Installing...${NC}"
        if command -v apt-get &> /dev/null; then
            sudo apt-get update -qq && sudo apt-get install -y sshpass
        elif command -v brew &> /dev/null; then
            brew install hudochenkov/sshpass/sshpass
        else
            echo -e "${RED}❌ Cannot install sshpass automatically${NC}"
            echo -e "${YELLOW}Please install sshpass or use SSH key: ./deploy_to_server.sh --use-key${NC}"
            exit 1
        fi
    fi
fi

# SSH command wrapper
ssh_cmd() {
    if [ "$USE_SSH_KEY" = true ]; then
        ssh -o StrictHostKeyChecking=no "${REMOTE_USER}@${REMOTE_HOST}" "$@"
    else
        sshpass -p "${REMOTE_PASSWORD}" ssh -o StrictHostKeyChecking=no "${REMOTE_USER}@${REMOTE_HOST}" "$@"
    fi
}

scp_cmd() {
    if [ "$USE_SSH_KEY" = true ]; then
        scp -o StrictHostKeyChecking=no "$@"
    else
        sshpass -p "${REMOTE_PASSWORD}" scp -o StrictHostKeyChecking=no "$@"
    fi
}

# Test connection
echo -e "${YELLOW}[1/5] Testing SSH connection...${NC}"
if ssh_cmd "echo 'Connection successful'" > /dev/null 2>&1; then
    echo -e "${GREEN}✅ SSH connection successful${NC}"
else
    echo -e "${RED}❌ SSH connection failed${NC}"
    echo ""
    echo -e "${YELLOW}Troubleshooting:${NC}"
    echo "1. Check if server is reachable: ping ${REMOTE_HOST}"
    echo "2. Try manual SSH: ssh ${REMOTE_USER}@${REMOTE_HOST}"
    echo "3. If using SSH key, make sure it's added: ssh-add ~/.ssh/id_rsa"
    echo "4. If password auth is disabled, use: ./deploy_to_server.sh --use-key"
    exit 1
fi
echo ""

# Create remote directory
echo -e "${YELLOW}[2/5] Creating deployment directory on server...${NC}"
ssh_cmd "mkdir -p /root/audiobooksmith_deployment && rm -rf /root/audiobooksmith_deployment/*"
echo -e "${GREEN}✅ Directory created${NC}"
echo ""

# Upload files
echo -e "${YELLOW}[3/5] Uploading deployment files...${NC}"
cd audiobooksmith_deployment_final

echo "  Uploading scripts..."
scp_cmd *.sh "${REMOTE_USER}@${REMOTE_HOST}:/root/audiobooksmith_deployment/" 2>/dev/null || true

echo "  Uploading Python files..."
scp_cmd *.py "${REMOTE_USER}@${REMOTE_HOST}:/root/audiobooksmith_deployment/" 2>/dev/null || true

echo "  Uploading configuration..."
scp_cmd *.conf "${REMOTE_USER}@${REMOTE_HOST}:/root/audiobooksmith_deployment/" 2>/dev/null || true

echo "  Uploading frontend code..."
scp_cmd *.jsx "${REMOTE_USER}@${REMOTE_HOST}:/root/audiobooksmith_deployment/" 2>/dev/null || true

echo "  Uploading documentation..."
scp_cmd *.md *.txt "${REMOTE_USER}@${REMOTE_HOST}:/root/audiobooksmith_deployment/" 2>/dev/null || true

cd ..

echo -e "${GREEN}✅ All files uploaded${NC}"
echo ""

# Make scripts executable
echo -e "${YELLOW}[4/5] Making scripts executable...${NC}"
ssh_cmd "cd /root/audiobooksmith_deployment && chmod +x *.sh *.py"
echo -e "${GREEN}✅ Scripts are executable${NC}"
echo ""

# Execute deployment
echo -e "${YELLOW}[5/5] Executing deployment on server...${NC}"
echo ""
echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
echo ""

ssh_cmd "cd /root/audiobooksmith_deployment && bash deploy_with_backup.sh" || {
    echo ""
    echo -e "${RED}❌ Deployment script encountered an error${NC}"
    echo -e "${YELLOW}The files are on your server at: /root/audiobooksmith_deployment${NC}"
    echo -e "${YELLOW}You can run the deployment manually:${NC}"
    echo -e "${CYAN}ssh ${REMOTE_USER}@${REMOTE_HOST}${NC}"
    echo -e "${CYAN}cd /root/audiobooksmith_deployment${NC}"
    echo -e "${CYAN}./deploy_with_backup.sh${NC}"
    exit 1
}

echo ""
echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
echo ""

# Final message
echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  🎉 Remote Deployment Complete!                            ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

echo -e "${BLUE}📍 Files Location:${NC}"
echo -e "   Server: ${REMOTE_HOST}"
echo -e "   Deployment files: /root/audiobooksmith_deployment"
echo -e "   Webhook installation: /root/audiobook_webhook"
echo ""

echo -e "${BLUE}🔧 Next Steps:${NC}"
echo ""
echo -e "${GREEN}1. Configure SSL (REQUIRED):${NC}"
echo -e "   ${CYAN}ssh ${REMOTE_USER}@${REMOTE_HOST}${NC}"
echo -e "   ${CYAN}cd /root/audiobook_webhook${NC}"
echo -e "   ${CYAN}./setup_ssl_both_domains.sh${NC}"
echo ""

echo -e "${GREEN}2. Test the webhook:${NC}"
echo -e "   ${CYAN}curl https://audiobooksmith.app/webhook/health${NC}"
echo ""

echo -e "${GREEN}3. Update your frontend:${NC}"
echo -e "   Use webhook URL: ${CYAN}https://audiobooksmith.app/webhook/audiobook-process${NC}"
echo ""

echo -e "${BLUE}🔧 Management Commands:${NC}"
echo -e "   Status:  ${CYAN}ssh ${REMOTE_USER}@${REMOTE_HOST} '/root/audiobook_webhook/status.sh'${NC}"
echo -e "   Logs:    ${CYAN}ssh ${REMOTE_USER}@${REMOTE_HOST} 'tail -f /root/audiobook_webhook/logs/webhook_server.log'${NC}"
echo -e "   Restart: ${CYAN}ssh ${REMOTE_USER}@${REMOTE_HOST} '/root/audiobook_webhook/restart.sh'${NC}"
echo ""

echo -e "${GREEN}✅ Deployment successful!${NC}"
echo ""
