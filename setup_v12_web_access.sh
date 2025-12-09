#!/bin/bash
#
# AudiobookSmith V12 - Web Access Setup Script
# This script configures nginx to serve V12 analysis results
# without disrupting your existing webhook server
#

set -e  # Exit on any error

echo "🚀 AudiobookSmith V12 - Web Access Setup"
echo "========================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}❌ Please run as root: sudo bash setup_v12_web_access.sh${NC}"
    exit 1
fi

echo -e "${BLUE}📋 Step 1: Backing up current nginx config...${NC}"
BACKUP_FILE="/etc/nginx/sites-available/audiobooksmith.backup.$(date +%Y%m%d_%H%M%S)"
cp /etc/nginx/sites-available/audiobooksmith "$BACKUP_FILE"
echo -e "${GREEN}✅ Backup saved: $BACKUP_FILE${NC}"
echo ""

echo -e "${BLUE}📋 Step 2: Checking for existing /v12-results/ location...${NC}"
if grep -q "location /v12-results/" /etc/nginx/sites-available/audiobooksmith; then
    echo -e "${YELLOW}⚠️  /v12-results/ location already exists, skipping...${NC}"
else
    echo -e "${BLUE}Adding /v12-results/ location to HTTPS server block...${NC}"
    
    # Create temporary file with the new location block
    cat > /tmp/v12_location_block.txt << 'EOF'

    # AudiobookSmith V12 Analysis Results
    location /v12-results/ {
        alias /var/www/audiobooksmith/;
        autoindex on;
        autoindex_exact_size off;
        autoindex_localtime on;
        
        # Allow access to HTML, CSS, JS, and text files
        location ~ \.(html|css|js|txt)$ {
            add_header Content-Type text/html;
        }
        
        try_files $uri $uri/ =404;
    }
EOF

    # Insert the location block before the "# Root location" comment in HTTPS server
    sed -i '/# Root location (for N8N or other services)/r /tmp/v12_location_block.txt' /etc/nginx/sites-available/audiobooksmith
    
    echo -e "${GREEN}✅ Added /v12-results/ location block${NC}"
    rm /tmp/v12_location_block.txt
fi
echo ""

echo -e "${BLUE}📋 Step 3: Testing nginx configuration...${NC}"
if nginx -t 2>&1 | grep -q "successful"; then
    echo -e "${GREEN}✅ Nginx configuration is valid${NC}"
else
    echo -e "${RED}❌ Nginx configuration test failed!${NC}"
    echo -e "${YELLOW}Restoring backup...${NC}"
    cp "$BACKUP_FILE" /etc/nginx/sites-available/audiobooksmith
    exit 1
fi
echo ""

echo -e "${BLUE}📋 Step 4: Reloading nginx...${NC}"
systemctl reload nginx
if systemctl is-active --quiet nginx; then
    echo -e "${GREEN}✅ Nginx reloaded successfully${NC}"
else
    echo -e "${RED}❌ Nginx failed to reload!${NC}"
    echo -e "${YELLOW}Restoring backup...${NC}"
    cp "$BACKUP_FILE" /etc/nginx/sites-available/audiobooksmith
    systemctl reload nginx
    exit 1
fi
echo ""

echo -e "${BLUE}📋 Step 5: Setting permissions...${NC}"
chmod -R 755 /var/www/audiobooksmith/vitalybook_v12_results_*
echo -e "${GREEN}✅ Permissions set${NC}"
echo ""

echo "========================================"
echo -e "${GREEN}🎉 Setup Complete!${NC}"
echo ""
echo -e "${BLUE}📊 Access your V12 analysis results at:${NC}"
echo ""

# Find all V12 result directories
RESULT_DIRS=$(find /var/www/audiobooksmith -maxdepth 1 -type d -name "*_v12_results_*" 2>/dev/null)

if [ -n "$RESULT_DIRS" ]; then
    while IFS= read -r dir; do
        DIR_NAME=$(basename "$dir")
        echo -e "  ${GREEN}✓${NC} https://audiobooksmith.app/v12-results/${DIR_NAME}/analysis.html"
    done <<< "$RESULT_DIRS"
else
    echo -e "  ${YELLOW}⚠️  No V12 result directories found yet${NC}"
    echo -e "  ${BLUE}Run V12 processor first, then results will appear at:${NC}"
    echo -e "  https://audiobooksmith.app/v12-results/BOOKNAME_v12_results_TIMESTAMP/analysis.html"
fi

echo ""
echo -e "${BLUE}📁 Browse all results:${NC}"
echo -e "  https://audiobooksmith.app/v12-results/"
echo ""

echo -e "${BLUE}ℹ️  Configuration Details:${NC}"
echo -e "  • Results directory: /var/www/audiobooksmith/"
echo -e "  • Nginx config: /etc/nginx/sites-available/audiobooksmith"
echo -e "  • Backup saved: $BACKUP_FILE"
echo -e "  • Auto-index enabled (you can browse directories)"
echo ""

echo -e "${GREEN}✅ V12 web access is now configured!${NC}"
echo ""
