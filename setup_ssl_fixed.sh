#!/bin/bash

################################################################################
# AudiobookSmith Webhook - SSL Setup Script (Fixed)
#
# This script properly configures Nginx and SSL in the correct order:
# 1. Configure Nginx with HTTP only
# 2. Obtain SSL certificates via certbot
# 3. Update Nginx to use HTTPS
#
# Usage: ./setup_ssl_fixed.sh
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
║   AudiobookSmith Webhook - SSL Configuration              ║
║   Multi-Domain Setup with Let's Encrypt                   ║
║                                                            ║
╚════════════════════════════════════════════════════════════╝
EOF
echo -e "${NC}"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}❌ This script must be run as root${NC}"
    exit 1
fi

# Configuration
DOMAIN1="websolutionsserver.net"
DOMAIN2="audiobooksmith.app"
WEBHOOK_PORT="5001"
NGINX_CONF="/etc/nginx/sites-available/audiobooksmith"
NGINX_ENABLED="/etc/nginx/sites-enabled/audiobooksmith"

echo -e "${YELLOW}📋 Configuration:${NC}"
echo -e "   Domain 1: ${DOMAIN1}"
echo -e "   Domain 2: ${DOMAIN2}"
echo -e "   Webhook Port: ${WEBHOOK_PORT}"
echo ""

# Install certbot if needed
echo -e "${YELLOW}[1/6] Checking prerequisites...${NC}"
if ! command -v certbot &> /dev/null; then
    echo -e "${YELLOW}⚠️  Certbot not found, installing...${NC}"
    apt-get update -qq
    apt-get install -y certbot python3-certbot-nginx
    echo -e "${GREEN}✅ Certbot installed${NC}"
else
    echo -e "${GREEN}✅ Certbot is installed${NC}"
fi
echo ""

# Create temporary HTTP-only Nginx configuration
echo -e "${YELLOW}[2/6] Creating temporary HTTP configuration...${NC}"

cat > "$NGINX_CONF" << 'NGINX_HTTP'
# AudiobookSmith Webhook - Temporary HTTP Configuration
# This will be updated to HTTPS after obtaining SSL certificates

server {
    listen 80;
    server_name websolutionsserver.net audiobooksmith.app;

    # Allow certbot to verify domain ownership
    location /.well-known/acme-challenge/ {
        root /var/www/html;
        allow all;
    }

    # Webhook endpoints
    location /webhook/ {
        proxy_pass http://localhost:5001/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # File upload settings
        client_max_body_size 100M;
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
    }

    # Health check
    location /webhook/health {
        proxy_pass http://localhost:5001/health;
        proxy_set_header Host $host;
    }
}
NGINX_HTTP

echo -e "${GREEN}✅ HTTP configuration created${NC}"
echo ""

# Enable the configuration
echo -e "${YELLOW}[3/6] Enabling Nginx configuration...${NC}"
ln -sf "$NGINX_CONF" "$NGINX_ENABLED"

# Test and reload Nginx
nginx -t
systemctl reload nginx
echo -e "${GREEN}✅ Nginx configured and reloaded${NC}"
echo ""

# Check DNS before obtaining certificates
echo -e "${YELLOW}[4/6] Checking DNS configuration...${NC}"
for DOMAIN in "$DOMAIN1" "$DOMAIN2"; do
    IP=$(dig +short "$DOMAIN" | tail -1)
    if [ -n "$IP" ]; then
        echo -e "${GREEN}✅ $DOMAIN → $IP${NC}"
    else
        echo -e "${YELLOW}⚠️  $DOMAIN - DNS not found or not propagated${NC}"
    fi
done
echo ""

# Obtain SSL certificates
echo -e "${YELLOW}[5/6] Obtaining SSL certificates...${NC}"
echo -e "${CYAN}This may take a minute...${NC}"
echo ""

# Try to obtain certificates
if certbot --nginx -d "$DOMAIN1" -d "$DOMAIN2" --non-interactive --agree-tos --register-unsafely-without-email --redirect; then
    echo ""
    echo -e "${GREEN}✅ SSL certificates obtained successfully${NC}"
else
    echo ""
    echo -e "${YELLOW}⚠️  Certificate generation had issues${NC}"
    echo -e "${YELLOW}This is usually due to:${NC}"
    echo -e "   1. DNS not pointing to this server"
    echo -e "   2. Firewall blocking port 80/443"
    echo -e "   3. Domain verification failed"
    echo ""
    echo -e "${CYAN}You can try manual certificate generation:${NC}"
    echo -e "   certbot --nginx -d $DOMAIN1 -d $DOMAIN2"
    echo ""
    echo -e "${YELLOW}Continuing with HTTP configuration...${NC}"
fi
echo ""

# Test final configuration
echo -e "${YELLOW}[6/6] Testing final configuration...${NC}"
if nginx -t; then
    systemctl reload nginx
    echo -e "${GREEN}✅ Nginx reloaded with final configuration${NC}"
else
    echo -e "${RED}❌ Nginx configuration has errors${NC}"
    exit 1
fi
echo ""

# Final status
echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  🎉 SSL Configuration Complete!                            ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

echo -e "${BLUE}🌐 Your Services:${NC}"
echo ""

# Check if SSL was successful
if [ -f "/etc/letsencrypt/live/$DOMAIN1/fullchain.pem" ]; then
    echo -e "${GREEN}✅ SSL Certificates Installed${NC}"
    echo ""
    echo -e "${BLUE}N8N Workflow Automation:${NC}"
    echo -e "   https://$DOMAIN1"
    echo -e "   https://$DOMAIN2"
    echo ""
    echo -e "${BLUE}AudiobookSmith Webhook:${NC}"
    echo -e "   https://$DOMAIN2/webhook/audiobook-process ${CYAN}(Use this in frontend)${NC}"
    echo -e "   https://$DOMAIN1/webhook/audiobook-process"
    echo ""
    echo -e "${BLUE}Health Check:${NC}"
    echo -e "   https://$DOMAIN2/webhook/health"
    echo -e "   https://$DOMAIN1/webhook/health"
    echo ""
    echo -e "${BLUE}🧪 Test Commands:${NC}"
    echo -e "   ${CYAN}curl https://$DOMAIN2/webhook/health${NC}"
    echo -e "   ${CYAN}curl https://$DOMAIN1/webhook/health${NC}"
else
    echo -e "${YELLOW}⚠️  SSL Certificates Not Installed (HTTP Only)${NC}"
    echo ""
    echo -e "${BLUE}N8N Workflow Automation:${NC}"
    echo -e "   http://$DOMAIN1"
    echo -e "   http://$DOMAIN2"
    echo ""
    echo -e "${BLUE}AudiobookSmith Webhook:${NC}"
    echo -e "   http://$DOMAIN2/webhook/audiobook-process"
    echo -e "   http://$DOMAIN1/webhook/audiobook-process"
    echo ""
    echo -e "${BLUE}Health Check:${NC}"
    echo -e "   http://$DOMAIN2/webhook/health"
    echo -e "   http://$DOMAIN1/webhook/health"
    echo ""
    echo -e "${YELLOW}To obtain SSL certificates manually:${NC}"
    echo -e "   ${CYAN}certbot --nginx -d $DOMAIN1 -d $DOMAIN2${NC}"
fi

echo ""
echo -e "${BLUE}📋 Certificate Auto-Renewal:${NC}"
echo -e "   Certbot will automatically renew certificates before expiry"
echo -e "   Test renewal: ${CYAN}certbot renew --dry-run${NC}"
echo ""

echo -e "${GREEN}✅ Setup complete!${NC}"
echo ""
