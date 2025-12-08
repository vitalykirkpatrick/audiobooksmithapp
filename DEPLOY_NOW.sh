#!/bin/bash

################################################################################
# AudiobookSmith Webhook - One-Click Deployment
#
# This script deploys everything to websolutionsserver.net in one command
#
# Usage: ./DEPLOY_NOW.sh
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
║        AudiobookSmith Webhook Deployment                  ║
║        One-Click Setup for websolutionsserver.net         ║
║                                                            ║
╚════════════════════════════════════════════════════════════╝
EOF
echo -e "${NC}"
echo ""

# Configuration
REMOTE_HOST="172.245.67.47"
REMOTE_USER="root"

echo -e "${YELLOW}📋 Deployment Configuration:${NC}"
echo -e "   Target Server: ${REMOTE_HOST}"
echo -e "   SSH User: ${REMOTE_USER}"
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

# Run smart deployment
if [ -f "./smart_deploy.sh" ]; then
    ./smart_deploy.sh ${REMOTE_HOST} ${REMOTE_USER}
else
    echo -e "${RED}❌ smart_deploy.sh not found${NC}"
    echo -e "${YELLOW}   Please run this script from the audiobook_webhook_deployment directory${NC}"
    exit 1
fi

echo ""
echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  🎉 Deployment Complete!                                   ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${YELLOW}📋 Next Steps:${NC}"
echo ""
echo -e "${GREEN}1. Configure Nginx (REQUIRED):${NC}"
echo -e "   SSH to your server:"
echo -e "   ${CYAN}ssh ${REMOTE_USER}@${REMOTE_HOST}${NC}"
echo ""
echo -e "   Edit your Nginx config (likely the same one used for N8N):"
echo -e "   ${CYAN}sudo nano /etc/nginx/sites-available/default${NC}"
echo -e "   or"
echo -e "   ${CYAN}sudo nano /etc/nginx/sites-available/n8n${NC}"
echo ""
echo -e "   Add the location blocks from:"
echo -e "   ${CYAN}~/audiobook_webhook/nginx_config_template.conf${NC}"
echo ""
echo -e "   Test and reload:"
echo -e "   ${CYAN}sudo nginx -t${NC}"
echo -e "   ${CYAN}sudo systemctl reload nginx${NC}"
echo ""
echo -e "${GREEN}2. Test the webhook:${NC}"
echo -e "   ${CYAN}curl https://websolutionsserver.net/webhook/health${NC}"
echo ""
echo -e "${GREEN}3. Update your frontend:${NC}"
echo -e "   Change webhook URL to:"
echo -e "   ${CYAN}https://websolutionsserver.net/webhook/audiobook-process${NC}"
echo ""
echo -e "${BLUE}📚 Documentation:${NC}"
echo -e "   See DEPLOYMENT_README.md for detailed instructions"
echo ""
echo -e "${GREEN}✅ Your webhook server is now running on websolutionsserver.net!${NC}"
echo ""
