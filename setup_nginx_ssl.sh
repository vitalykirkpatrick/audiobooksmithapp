#!/bin/bash

################################################################################
# AudiobookSmith Webhook - Nginx & SSL Setup Script
#
# Run this script ON YOUR SERVER (websolutionsserver.net) after deployment
# to configure Nginx reverse proxy and SSL certificate
#
# Usage: sudo ./setup_nginx_ssl.sh
################################################################################

set -e

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "❌ Please run as root: sudo ./setup_nginx_ssl.sh"
    exit 1
fi

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  AudiobookSmith Webhook - Nginx & SSL Setup               ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Configuration
WEBHOOK_DOMAIN="webhook.audiobooksmith.com"
ADMIN_EMAIL="admin@audiobooksmith.com"
NGINX_CONF="/etc/nginx/sites-available/audiobook-webhook"
WEBHOOK_DIR="$HOME/audiobook_webhook"

# Prompt for domain
echo -e "${YELLOW}Enter your webhook domain (default: webhook.audiobooksmith.com):${NC}"
read -p "> " input_domain
if [ ! -z "$input_domain" ]; then
    WEBHOOK_DOMAIN="$input_domain"
fi

# Prompt for email
echo -e "${YELLOW}Enter your email for SSL certificate (default: admin@audiobooksmith.com):${NC}"
read -p "> " input_email
if [ ! -z "$input_email" ]; then
    ADMIN_EMAIL="$input_email"
fi

echo ""
echo -e "${GREEN}Configuration:${NC}"
echo -e "  Domain: ${WEBHOOK_DOMAIN}"
echo -e "  Email:  ${ADMIN_EMAIL}"
echo ""

# Install Nginx if not installed
echo -e "${YELLOW}[1/6] Checking Nginx installation...${NC}"
if ! command -v nginx &> /dev/null; then
    echo -e "${YELLOW}⚠️  Nginx not found. Installing...${NC}"
    apt-get update
    apt-get install -y nginx
    echo -e "${GREEN}✅ Nginx installed${NC}"
else
    echo -e "${GREEN}✅ Nginx is already installed${NC}"
fi
echo ""

# Create Nginx configuration
echo -e "${YELLOW}[2/6] Creating Nginx configuration...${NC}"
cat > ${NGINX_CONF} << EOF
# AudiobookSmith Webhook - Nginx Configuration
# Generated on $(date)

# HTTP - Redirect to HTTPS
server {
    listen 80;
    listen [::]:80;
    server_name ${WEBHOOK_DOMAIN};
    
    # Allow Let's Encrypt verification
    location /.well-known/acme-challenge/ {
        root /var/www/html;
    }
    
    # Redirect all other HTTP requests to HTTPS
    location / {
        return 301 https://\$server_name\$request_uri;
    }
}

# HTTPS - Main webhook server
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name ${WEBHOOK_DOMAIN};
    
    # SSL Configuration (will be updated by certbot)
    ssl_certificate /etc/ssl/certs/ssl-cert-snakeoil.pem;
    ssl_certificate_key /etc/ssl/private/ssl-cert-snakeoil.key;
    
    # SSL Security Settings
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    
    # Security Headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    
    # File Upload Settings
    client_max_body_size 100M;
    client_body_timeout 300s;
    
    # Logging
    access_log /var/log/nginx/audiobook-webhook-access.log;
    error_log /var/log/nginx/audiobook-webhook-error.log;
    
    # Proxy to Flask application
    location / {
        proxy_pass http://127.0.0.1:5001;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        # Timeouts
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
    }
    
    # Health check endpoint
    location /health {
        proxy_pass http://127.0.0.1:5001/health;
        proxy_set_header Host \$host;
        access_log off;
    }
}
EOF

echo -e "${GREEN}✅ Nginx configuration created${NC}"
echo ""

# Enable the site
echo -e "${YELLOW}[3/6] Enabling Nginx site...${NC}"
ln -sf ${NGINX_CONF} /etc/nginx/sites-enabled/audiobook-webhook
echo -e "${GREEN}✅ Site enabled${NC}"
echo ""

# Test Nginx configuration
echo -e "${YELLOW}[4/6] Testing Nginx configuration...${NC}"
if nginx -t; then
    echo -e "${GREEN}✅ Nginx configuration is valid${NC}"
else
    echo -e "${RED}❌ Nginx configuration has errors${NC}"
    exit 1
fi
echo ""

# Reload Nginx
echo -e "${YELLOW}[5/6] Reloading Nginx...${NC}"
systemctl reload nginx
echo -e "${GREEN}✅ Nginx reloaded${NC}"
echo ""

# Install and configure SSL with Let's Encrypt
echo -e "${YELLOW}[6/6] Setting up SSL certificate...${NC}"
echo ""
echo -e "${BLUE}Do you want to install Let's Encrypt SSL certificate now?${NC}"
echo -e "${YELLOW}Note: Your domain ${WEBHOOK_DOMAIN} must be pointing to this server${NC}"
read -p "Install SSL certificate? (y/n): " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    # Install certbot if not installed
    if ! command -v certbot &> /dev/null; then
        echo -e "${YELLOW}Installing certbot...${NC}"
        apt-get install -y certbot python3-certbot-nginx
    fi
    
    # Get certificate
    echo -e "${YELLOW}Obtaining SSL certificate...${NC}"
    certbot --nginx -d ${WEBHOOK_DOMAIN} --non-interactive --agree-tos --email ${ADMIN_EMAIL} --redirect
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ SSL certificate installed successfully${NC}"
    else
        echo -e "${RED}❌ Failed to install SSL certificate${NC}"
        echo -e "${YELLOW}   You can run this manually later:${NC}"
        echo -e "${YELLOW}   sudo certbot --nginx -d ${WEBHOOK_DOMAIN}${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  Skipping SSL installation${NC}"
    echo -e "${YELLOW}   To install SSL later, run:${NC}"
    echo -e "${YELLOW}   sudo certbot --nginx -d ${WEBHOOK_DOMAIN}${NC}"
fi
echo ""

# Final status
echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  🎉 Nginx & SSL Setup Complete!                            ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}📍 Configuration:${NC}"
echo -e "   Domain:     ${WEBHOOK_DOMAIN}"
echo -e "   Nginx conf: ${NGINX_CONF}"
echo -e "   Access log: /var/log/nginx/audiobook-webhook-access.log"
echo -e "   Error log:  /var/log/nginx/audiobook-webhook-error.log"
echo ""
echo -e "${BLUE}🧪 Test your webhook:${NC}"
echo -e "   Health check: curl https://${WEBHOOK_DOMAIN}/health"
echo -e "   File upload:  curl -X POST https://${WEBHOOK_DOMAIN}/webhook/audiobook-process \\"
echo -e "                   -F 'email=test@example.com' \\"
echo -e "                   -F 'bookTitle=Test' \\"
echo -e "                   -F 'plan=free' \\"
echo -e "                   -F 'bookFile=@test.pdf'"
echo ""
echo -e "${BLUE}🔧 Nginx commands:${NC}"
echo -e "   Test config:  sudo nginx -t"
echo -e "   Reload:       sudo systemctl reload nginx"
echo -e "   Restart:      sudo systemctl restart nginx"
echo -e "   Status:       sudo systemctl status nginx"
echo ""
echo -e "${YELLOW}⚠️  Don't forget to:${NC}"
echo -e "   1. Update DNS: Point ${WEBHOOK_DOMAIN} to this server's IP"
echo -e "   2. Update frontend: Change webhook URL to https://${WEBHOOK_DOMAIN}/webhook/audiobook-process"
echo -e "   3. Test thoroughly with real file uploads"
echo ""
