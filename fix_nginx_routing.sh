#!/bin/bash

################################################################################
# AudiobookSmith Webhook - Fix Nginx Routing
#
# This script diagnoses and fixes 404 errors by:
# 1. Checking webhook server status
# 2. Verifying Nginx configuration
# 3. Fixing routing issues
# 4. Testing endpoints
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
║   AudiobookSmith Webhook - Nginx Routing Fix              ║
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

echo -e "${YELLOW}[1/5] Checking webhook server status...${NC}"

# Check if webhook server is running
if pgrep -f audiobook_webhook_server.py > /dev/null; then
    WEBHOOK_PID=$(pgrep -f audiobook_webhook_server.py)
    echo -e "${GREEN}✅ Webhook server is running (PID: $WEBHOOK_PID)${NC}"
    
    # Check which port it's using
    WEBHOOK_PORT=$(netstat -tlnp 2>/dev/null | grep "$WEBHOOK_PID" | grep -oP ':\K[0-9]+' | head -1)
    if [ -n "$WEBHOOK_PORT" ]; then
        echo -e "${GREEN}✅ Listening on port: $WEBHOOK_PORT${NC}"
    else
        echo -e "${YELLOW}⚠️  Could not determine port${NC}"
        WEBHOOK_PORT="5001"
    fi
else
    echo -e "${RED}❌ Webhook server is not running${NC}"
    echo -e "${YELLOW}Starting webhook server...${NC}"
    cd /root/audiobook_webhook
    ./start.sh
    sleep 3
    WEBHOOK_PORT="5001"
fi

# Test local webhook
echo -e "${YELLOW}Testing local webhook on port $WEBHOOK_PORT...${NC}"
LOCAL_TEST=$(curl -s http://localhost:$WEBHOOK_PORT/health 2>/dev/null || echo "failed")
if echo "$LOCAL_TEST" | grep -q "healthy"; then
    echo -e "${GREEN}✅ Local webhook responds correctly${NC}"
else
    echo -e "${RED}❌ Local webhook not responding${NC}"
    echo -e "${YELLOW}Response: $LOCAL_TEST${NC}"
fi
echo ""

echo -e "${YELLOW}[2/5] Checking Nginx configuration...${NC}"

# Find all Nginx configs that might be interfering
echo -e "${CYAN}Checking for existing configurations...${NC}"
CONFIGS=$(ls -1 /etc/nginx/sites-enabled/ 2>/dev/null)
echo "$CONFIGS"
echo ""

# Check if our config exists
if [ -f "/etc/nginx/sites-available/audiobooksmith" ]; then
    echo -e "${GREEN}✅ AudiobookSmith config exists${NC}"
else
    echo -e "${YELLOW}⚠️  AudiobookSmith config not found${NC}"
fi
echo ""

echo -e "${YELLOW}[3/5] Creating correct Nginx configuration...${NC}"

# Backup existing config
if [ -f "/etc/nginx/sites-available/audiobooksmith" ]; then
    cp /etc/nginx/sites-available/audiobooksmith /etc/nginx/sites-available/audiobooksmith.backup.$(date +%Y%m%d_%H%M%S)
fi

# Create new configuration
cat > /etc/nginx/sites-available/audiobooksmith << NGINX_CONFIG
# AudiobookSmith Webhook Configuration
# Generated: $(date)

# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name websolutionsserver.net audiobooksmith.app;

    # Allow certbot
    location /.well-known/acme-challenge/ {
        root /var/www/html;
        allow all;
    }

    # Redirect all other HTTP traffic to HTTPS
    location / {
        return 301 https://\$host\$request_uri;
    }
}

# HTTPS Server
server {
    listen 443 ssl http2;
    server_name websolutionsserver.net audiobooksmith.app;

    # SSL Configuration (certbot will manage these)
    ssl_certificate /etc/letsencrypt/live/websolutionsserver.net/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/websolutionsserver.net/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Webhook endpoints - IMPORTANT: trailing slash handling
    location /webhook {
        # Remove trailing slash if present and redirect
        rewrite ^/webhook/$ /webhook permanent;
        
        # Proxy to webhook server
        proxy_pass http://localhost:${WEBHOOK_PORT};
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        # File upload settings
        client_max_body_size 100M;
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
        proxy_buffering off;
    }

    # Root location (for N8N or other services)
    location / {
        # If you have N8N or another service on a different port, configure here
        # For now, return a simple message
        return 200 'AudiobookSmith Server - Use /webhook endpoints';
        add_header Content-Type text/plain;
    }
}
NGINX_CONFIG

echo -e "${GREEN}✅ Nginx configuration created${NC}"
echo ""

echo -e "${YELLOW}[4/5] Enabling and testing configuration...${NC}"

# Enable the site
ln -sf /etc/nginx/sites-available/audiobooksmith /etc/nginx/sites-enabled/audiobooksmith

# Test configuration
if nginx -t 2>&1; then
    echo -e "${GREEN}✅ Nginx configuration is valid${NC}"
    systemctl reload nginx
    echo -e "${GREEN}✅ Nginx reloaded${NC}"
else
    echo -e "${RED}❌ Nginx configuration has errors${NC}"
    echo -e "${YELLOW}Restoring backup...${NC}"
    if [ -f "/etc/nginx/sites-available/audiobooksmith.backup."* ]; then
        cp /etc/nginx/sites-available/audiobooksmith.backup.* /etc/nginx/sites-available/audiobooksmith
        nginx -t && systemctl reload nginx
    fi
    exit 1
fi
echo ""

echo -e "${YELLOW}[5/5] Testing endpoints...${NC}"
sleep 2

# Test health endpoint
echo -e "${CYAN}Testing: http://localhost/webhook/health${NC}"
HTTP_TEST=$(curl -s http://localhost/webhook/health 2>/dev/null || echo "failed")
if echo "$HTTP_TEST" | grep -q "healthy"; then
    echo -e "${GREEN}✅ HTTP health check works${NC}"
else
    echo -e "${YELLOW}⚠️  HTTP health check: $HTTP_TEST${NC}"
fi

echo -e "${CYAN}Testing: https://localhost/webhook/health${NC}"
HTTPS_TEST=$(curl -sk https://localhost/webhook/health 2>/dev/null || echo "failed")
if echo "$HTTPS_TEST" | grep -q "healthy"; then
    echo -e "${GREEN}✅ HTTPS health check works${NC}"
else
    echo -e "${YELLOW}⚠️  HTTPS health check: $HTTPS_TEST${NC}"
fi

echo ""
echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  🎉 Nginx Routing Fixed!                                   ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

echo -e "${BLUE}🧪 Test Your Endpoints:${NC}"
echo ""
echo -e "${CYAN}Health Check:${NC}"
echo -e "   curl https://audiobooksmith.app/webhook/health"
echo -e "   curl https://websolutionsserver.net/webhook/health"
echo ""
echo -e "${CYAN}Process Audiobook:${NC}"
echo -e "   curl -X POST https://audiobooksmith.app/webhook/audiobook-process \\"
echo -e "     -F \"email=test@example.com\" \\"
echo -e "     -F \"bookTitle=Test Book\" \\"
echo -e "     -F \"plan=free\" \\"
echo -e "     -F \"bookFile=@/path/to/book.pdf\""
echo ""

echo -e "${BLUE}📋 Configuration Details:${NC}"
echo -e "   Webhook Port: ${WEBHOOK_PORT}"
echo -e "   Nginx Config: /etc/nginx/sites-available/audiobooksmith"
echo -e "   Webhook Server: /root/audiobook_webhook/"
echo ""

echo -e "${BLUE}🔧 Management Commands:${NC}"
echo -e "   Status:  /root/audiobook_webhook/status.sh"
echo -e "   Logs:    tail -f /root/audiobook_webhook/logs/webhook_server.log"
echo -e "   Restart: /root/audiobook_webhook/restart.sh"
echo ""

echo -e "${GREEN}✅ All done!${NC}"
echo ""
