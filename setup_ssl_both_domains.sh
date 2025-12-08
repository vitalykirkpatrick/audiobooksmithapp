#!/bin/bash

################################################################################
# AudiobookSmith - SSL Setup for Both Domains
#
# This script sets up SSL certificates for:
# - websolutionsserver.net
# - audiobooksmith.app
#
# Run this ON YOUR SERVER after deploying the webhook
#
# Usage: sudo ./setup_ssl_both_domains.sh
################################################################################

set -e

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "❌ Please run as root: sudo ./setup_ssl_both_domains.sh"
    exit 1
fi

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  AudiobookSmith - Multi-Domain SSL Setup                  ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Configuration
DOMAIN1="websolutionsserver.net"
DOMAIN2="audiobooksmith.app"
ADMIN_EMAIL="admin@audiobooksmith.com"

echo -e "${YELLOW}This script will set up SSL certificates for:${NC}"
echo -e "  1. ${DOMAIN1}"
echo -e "  2. ${DOMAIN2}"
echo -e "  3. www.${DOMAIN2}"
echo ""

# Prompt for email
echo -e "${YELLOW}Enter your email for SSL certificate notifications:${NC}"
read -p "Email (default: ${ADMIN_EMAIL}): " input_email
if [ ! -z "$input_email" ]; then
    ADMIN_EMAIL="$input_email"
fi
echo ""

# Check if certbot is installed
echo -e "${YELLOW}[1/5] Checking certbot installation...${NC}"
if ! command -v certbot &> /dev/null; then
    echo -e "${YELLOW}⚠️  Certbot not found. Installing...${NC}"
    apt-get update
    apt-get install -y certbot python3-certbot-nginx
    echo -e "${GREEN}✅ Certbot installed${NC}"
else
    echo -e "${GREEN}✅ Certbot is already installed${NC}"
fi
echo ""

# Check DNS
echo -e "${YELLOW}[2/5] Checking DNS configuration...${NC}"
echo -e "${CYAN}Verifying that domains point to this server...${NC}"

SERVER_IP=$(curl -s ifconfig.me)
echo -e "Server IP: ${SERVER_IP}"

for DOMAIN in ${DOMAIN1} ${DOMAIN2} www.${DOMAIN2}; do
    DOMAIN_IP=$(dig +short ${DOMAIN} | tail -1)
    if [ "$DOMAIN_IP" = "$SERVER_IP" ]; then
        echo -e "${GREEN}✅ ${DOMAIN} → ${DOMAIN_IP}${NC}"
    else
        echo -e "${YELLOW}⚠️  ${DOMAIN} → ${DOMAIN_IP} (expected: ${SERVER_IP})${NC}"
        echo -e "${YELLOW}   DNS may not be configured correctly${NC}"
    fi
done
echo ""

# Backup existing Nginx config
echo -e "${YELLOW}[3/5] Backing up Nginx configuration...${NC}"
if [ -f /etc/nginx/sites-enabled/audiobooksmith ]; then
    cp /etc/nginx/sites-enabled/audiobooksmith /etc/nginx/sites-enabled/audiobooksmith.backup.$(date +%Y%m%d_%H%M%S)
    echo -e "${GREEN}✅ Backup created${NC}"
else
    echo -e "${YELLOW}⚠️  No existing config found (this is okay for first-time setup)${NC}"
fi
echo ""

# Install multi-domain Nginx config
echo -e "${YELLOW}[4/5] Installing Nginx configuration...${NC}"

# Check if we have the multi-domain config
if [ -f ~/audiobook_webhook/nginx_multi_domain.conf ]; then
    NGINX_CONFIG=~/audiobook_webhook/nginx_multi_domain.conf
elif [ -f ./nginx_multi_domain.conf ]; then
    NGINX_CONFIG=./nginx_multi_domain.conf
else
    echo -e "${RED}❌ nginx_multi_domain.conf not found${NC}"
    exit 1
fi

# Copy to sites-available
cp ${NGINX_CONFIG} /etc/nginx/sites-available/audiobooksmith

# Disable default site if it exists
if [ -f /etc/nginx/sites-enabled/default ]; then
    echo -e "${YELLOW}⚠️  Disabling default Nginx site...${NC}"
    rm -f /etc/nginx/sites-enabled/default
fi

# Enable our site
ln -sf /etc/nginx/sites-available/audiobooksmith /etc/nginx/sites-enabled/audiobooksmith

echo -e "${GREEN}✅ Nginx configuration installed${NC}"
echo ""

# Test Nginx configuration (before SSL)
echo -e "${YELLOW}Testing Nginx configuration...${NC}"
if nginx -t; then
    echo -e "${GREEN}✅ Nginx configuration is valid${NC}"
else
    echo -e "${RED}❌ Nginx configuration has errors${NC}"
    exit 1
fi

# Reload Nginx
systemctl reload nginx
echo -e "${GREEN}✅ Nginx reloaded${NC}"
echo ""

# Obtain SSL certificates
echo -e "${YELLOW}[5/5] Obtaining SSL certificates...${NC}"
echo ""

# Check if certificates already exist
CERT1_EXISTS=false
CERT2_EXISTS=false

if [ -d /etc/letsencrypt/live/${DOMAIN1} ]; then
    echo -e "${GREEN}✅ Certificate for ${DOMAIN1} already exists${NC}"
    CERT1_EXISTS=true
fi

if [ -d /etc/letsencrypt/live/${DOMAIN2} ]; then
    echo -e "${GREEN}✅ Certificate for ${DOMAIN2} already exists${NC}"
    CERT2_EXISTS=true
fi

# Obtain certificate for websolutionsserver.net
if [ "$CERT1_EXISTS" = false ]; then
    echo -e "${YELLOW}Obtaining certificate for ${DOMAIN1}...${NC}"
    certbot --nginx -d ${DOMAIN1} \
        --non-interactive \
        --agree-tos \
        --email ${ADMIN_EMAIL} \
        --redirect
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Certificate for ${DOMAIN1} obtained${NC}"
    else
        echo -e "${RED}❌ Failed to obtain certificate for ${DOMAIN1}${NC}"
        echo -e "${YELLOW}   This may be due to DNS not being configured correctly${NC}"
    fi
else
    echo -e "${YELLOW}Renewing certificate for ${DOMAIN1} (if needed)...${NC}"
    certbot renew --cert-name ${DOMAIN1}
fi
echo ""

# Obtain certificate for audiobooksmith.app
if [ "$CERT2_EXISTS" = false ]; then
    echo -e "${YELLOW}Obtaining certificate for ${DOMAIN2} and www.${DOMAIN2}...${NC}"
    certbot --nginx -d ${DOMAIN2} -d www.${DOMAIN2} \
        --non-interactive \
        --agree-tos \
        --email ${ADMIN_EMAIL} \
        --redirect
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Certificate for ${DOMAIN2} obtained${NC}"
    else
        echo -e "${RED}❌ Failed to obtain certificate for ${DOMAIN2}${NC}"
        echo -e "${YELLOW}   Make sure DNS is pointing to this server${NC}"
        echo -e "${YELLOW}   You can run this script again after DNS propagates${NC}"
    fi
else
    echo -e "${YELLOW}Renewing certificate for ${DOMAIN2} (if needed)...${NC}"
    certbot renew --cert-name ${DOMAIN2}
fi
echo ""

# Test Nginx configuration (after SSL)
echo -e "${YELLOW}Testing final Nginx configuration...${NC}"
if nginx -t; then
    echo -e "${GREEN}✅ Nginx configuration is valid${NC}"
    systemctl reload nginx
    echo -e "${GREEN}✅ Nginx reloaded${NC}"
else
    echo -e "${RED}❌ Nginx configuration has errors${NC}"
    exit 1
fi
echo ""

# Set up automatic renewal
echo -e "${YELLOW}Setting up automatic certificate renewal...${NC}"
if ! crontab -l 2>/dev/null | grep -q "certbot renew"; then
    (crontab -l 2>/dev/null; echo "0 3 * * * certbot renew --quiet --post-hook 'systemctl reload nginx'") | crontab -
    echo -e "${GREEN}✅ Automatic renewal configured (runs daily at 3 AM)${NC}"
else
    echo -e "${GREEN}✅ Automatic renewal already configured${NC}"
fi
echo ""

# Final status
echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  🎉 SSL Setup Complete!                                    ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}📍 Your services are now accessible via HTTPS:${NC}"
echo ""
echo -e "${GREEN}N8N:${NC}"
echo -e "  https://websolutionsserver.net"
echo -e "  https://audiobooksmith.app"
echo ""
echo -e "${GREEN}Webhook:${NC}"
echo -e "  https://websolutionsserver.net/webhook/audiobook-process"
echo -e "  https://audiobooksmith.app/webhook/audiobook-process"
echo ""
echo -e "${GREEN}Health Check:${NC}"
echo -e "  https://websolutionsserver.net/webhook/health"
echo -e "  https://audiobooksmith.app/webhook/health"
echo ""
echo -e "${BLUE}🧪 Test your setup:${NC}"
echo -e "  curl https://audiobooksmith.app/webhook/health"
echo -e "  curl https://websolutionsserver.net/webhook/health"
echo ""
echo -e "${BLUE}📋 SSL Certificate Info:${NC}"
certbot certificates
echo ""
echo -e "${YELLOW}⚠️  Update your frontend webhook URL to:${NC}"
echo -e "  ${CYAN}https://audiobooksmith.app/webhook/audiobook-process${NC}"
echo ""
echo -e "${GREEN}✅ All done! Your webhook and N8N are accessible via both domains.${NC}"
echo ""
