#!/bin/bash

################################################################################
# AudiobookSmith Webhook - Server Audit Script
#
# This script checks your websolutionsserver.net for:
# - Existing installations (Python, Flask, Nginx, SSL, N8N)
# - Current configurations
# - Available ports
# - Disk space
# - Required dependencies
#
# Run this FIRST before deployment to understand your server setup
#
# Usage: ./audit_server.sh
################################################################################

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  AudiobookSmith Webhook - Server Audit                    ║${NC}"
echo -e "${BLUE}║  Target: websolutionsserver.net                           ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Output file
AUDIT_REPORT="/tmp/server_audit_$(date +%Y%m%d_%H%M%S).txt"
echo "Audit Report - $(date)" > ${AUDIT_REPORT}
echo "Server: websolutionsserver.net" >> ${AUDIT_REPORT}
echo "========================================" >> ${AUDIT_REPORT}
echo "" >> ${AUDIT_REPORT}

# Function to check and report
check_item() {
    local item=$1
    local status=$2
    local details=$3
    
    if [ "$status" = "OK" ]; then
        echo -e "${GREEN}✅ ${item}${NC}"
        echo "✅ ${item}" >> ${AUDIT_REPORT}
    elif [ "$status" = "WARN" ]; then
        echo -e "${YELLOW}⚠️  ${item}${NC}"
        echo "⚠️  ${item}" >> ${AUDIT_REPORT}
    else
        echo -e "${RED}❌ ${item}${NC}"
        echo "❌ ${item}" >> ${AUDIT_REPORT}
    fi
    
    if [ ! -z "$details" ]; then
        echo -e "${CYAN}   ${details}${NC}"
        echo "   ${details}" >> ${AUDIT_REPORT}
    fi
}

echo -e "${YELLOW}[1/10] System Information${NC}"
echo "========================================" >> ${AUDIT_REPORT}
echo "SYSTEM INFORMATION" >> ${AUDIT_REPORT}
echo "========================================" >> ${AUDIT_REPORT}

# OS Info
OS_INFO=$(cat /etc/os-release | grep PRETTY_NAME | cut -d'"' -f2)
check_item "Operating System" "OK" "${OS_INFO}"

# Hostname
HOSTNAME=$(hostname)
check_item "Hostname" "OK" "${HOSTNAME}"

# Uptime
UPTIME=$(uptime -p)
check_item "Uptime" "OK" "${UPTIME}"

# Current User
CURRENT_USER=$(whoami)
check_item "Current User" "OK" "${CURRENT_USER}"
echo "" >> ${AUDIT_REPORT}
echo ""

echo -e "${YELLOW}[2/10] Python Environment${NC}"
echo "========================================" >> ${AUDIT_REPORT}
echo "PYTHON ENVIRONMENT" >> ${AUDIT_REPORT}
echo "========================================" >> ${AUDIT_REPORT}

# Python 3.11
if command -v python3.11 &> /dev/null; then
    PY311_VERSION=$(python3.11 --version)
    check_item "Python 3.11" "OK" "${PY311_VERSION}"
else
    check_item "Python 3.11" "WARN" "Not installed (will use python3)"
fi

# Python 3
if command -v python3 &> /dev/null; then
    PY3_VERSION=$(python3 --version)
    check_item "Python 3" "OK" "${PY3_VERSION}"
else
    check_item "Python 3" "ERROR" "Not installed - REQUIRED"
fi

# pip3
if command -v pip3 &> /dev/null; then
    PIP_VERSION=$(pip3 --version | cut -d' ' -f1-2)
    check_item "pip3" "OK" "${PIP_VERSION}"
else
    check_item "pip3" "ERROR" "Not installed - REQUIRED"
fi

# Flask
if python3 -c "import flask" 2>/dev/null; then
    FLASK_VERSION=$(python3 -c "import flask; print(flask.__version__)")
    check_item "Flask" "OK" "Version ${FLASK_VERSION}"
else
    check_item "Flask" "WARN" "Not installed (will be installed)"
fi
echo "" >> ${AUDIT_REPORT}
echo ""

echo -e "${YELLOW}[3/10] Web Server (Nginx)${NC}"
echo "========================================" >> ${AUDIT_REPORT}
echo "WEB SERVER (NGINX)" >> ${AUDIT_REPORT}
echo "========================================" >> ${AUDIT_REPORT}

# Nginx
if command -v nginx &> /dev/null; then
    NGINX_VERSION=$(nginx -v 2>&1 | cut -d'/' -f2)
    check_item "Nginx" "OK" "Version ${NGINX_VERSION}"
    
    # Nginx status
    if systemctl is-active --quiet nginx; then
        check_item "Nginx Status" "OK" "Running"
    else
        check_item "Nginx Status" "WARN" "Not running"
    fi
    
    # Nginx config test
    if nginx -t 2>/dev/null; then
        check_item "Nginx Config" "OK" "Valid configuration"
    else
        check_item "Nginx Config" "WARN" "Configuration has warnings"
    fi
    
    # Check existing sites
    if [ -d /etc/nginx/sites-enabled ]; then
        ENABLED_SITES=$(ls -1 /etc/nginx/sites-enabled | wc -l)
        check_item "Nginx Sites" "OK" "${ENABLED_SITES} site(s) enabled"
        echo "   Enabled sites:" >> ${AUDIT_REPORT}
        ls -1 /etc/nginx/sites-enabled >> ${AUDIT_REPORT}
    fi
else
    check_item "Nginx" "ERROR" "Not installed - REQUIRED"
fi
echo "" >> ${AUDIT_REPORT}
echo ""

echo -e "${YELLOW}[4/10] SSL Certificates${NC}"
echo "========================================" >> ${AUDIT_REPORT}
echo "SSL CERTIFICATES" >> ${AUDIT_REPORT}
echo "========================================" >> ${AUDIT_REPORT}

# Certbot
if command -v certbot &> /dev/null; then
    CERTBOT_VERSION=$(certbot --version 2>&1 | cut -d' ' -f2)
    check_item "Certbot" "OK" "Version ${CERTBOT_VERSION}"
    
    # List certificates
    if [ -d /etc/letsencrypt/live ]; then
        CERT_COUNT=$(ls -1 /etc/letsencrypt/live | wc -l)
        check_item "SSL Certificates" "OK" "${CERT_COUNT} certificate(s) installed"
        echo "   Installed certificates:" >> ${AUDIT_REPORT}
        ls -1 /etc/letsencrypt/live >> ${AUDIT_REPORT}
    fi
else
    check_item "Certbot" "WARN" "Not installed (SSL available via other method)"
fi
echo "" >> ${AUDIT_REPORT}
echo ""

echo -e "${YELLOW}[5/10] N8N Installation${NC}"
echo "========================================" >> ${AUDIT_REPORT}
echo "N8N INSTALLATION" >> ${AUDIT_REPORT}
echo "========================================" >> ${AUDIT_REPORT}

# Check for N8N
if command -v n8n &> /dev/null; then
    N8N_VERSION=$(n8n --version 2>&1 || echo "unknown")
    check_item "N8N" "OK" "Version ${N8N_VERSION}"
else
    check_item "N8N" "WARN" "Command not found (may be running via npm/docker)"
fi

# Check if N8N is running
if pgrep -f "n8n" > /dev/null; then
    N8N_PID=$(pgrep -f "n8n" | head -1)
    check_item "N8N Process" "OK" "Running (PID: ${N8N_PID})"
    
    # Check N8N port
    N8N_PORT=$(netstat -tlnp 2>/dev/null | grep ${N8N_PID} | awk '{print $4}' | cut -d':' -f2 | head -1)
    if [ ! -z "$N8N_PORT" ]; then
        check_item "N8N Port" "OK" "Listening on port ${N8N_PORT}"
    fi
else
    check_item "N8N Process" "WARN" "Not running"
fi

# Check N8N Nginx config
if [ -f /etc/nginx/sites-enabled/n8n ] || [ -f /etc/nginx/sites-available/n8n ]; then
    check_item "N8N Nginx Config" "OK" "Configuration file exists"
else
    check_item "N8N Nginx Config" "WARN" "No dedicated Nginx config found"
fi
echo "" >> ${AUDIT_REPORT}
echo ""

echo -e "${YELLOW}[6/10] Port Availability${NC}"
echo "========================================" >> ${AUDIT_REPORT}
echo "PORT AVAILABILITY" >> ${AUDIT_REPORT}
echo "========================================" >> ${AUDIT_REPORT}

# Check common ports
PORTS_TO_CHECK="5000 5001 5002 5003 8000 8001 8080"
for PORT in $PORTS_TO_CHECK; do
    if netstat -tln 2>/dev/null | grep -q ":${PORT} "; then
        PROCESS=$(netstat -tlnp 2>/dev/null | grep ":${PORT} " | awk '{print $7}' | cut -d'/' -f2 | head -1)
        check_item "Port ${PORT}" "WARN" "In use by ${PROCESS}"
    else
        check_item "Port ${PORT}" "OK" "Available"
    fi
done
echo "" >> ${AUDIT_REPORT}
echo ""

echo -e "${YELLOW}[7/10] Disk Space${NC}"
echo "========================================" >> ${AUDIT_REPORT}
echo "DISK SPACE" >> ${AUDIT_REPORT}
echo "========================================" >> ${AUDIT_REPORT}

# Check disk space
DISK_USAGE=$(df -h / | tail -1 | awk '{print $5}' | sed 's/%//')
DISK_AVAIL=$(df -h / | tail -1 | awk '{print $4}')

if [ $DISK_USAGE -lt 80 ]; then
    check_item "Disk Space" "OK" "${DISK_AVAIL} available (${DISK_USAGE}% used)"
else
    check_item "Disk Space" "WARN" "${DISK_AVAIL} available (${DISK_USAGE}% used)"
fi

# Check home directory
HOME_AVAIL=$(df -h $HOME | tail -1 | awk '{print $4}')
check_item "Home Directory" "OK" "${HOME_AVAIL} available"
echo "" >> ${AUDIT_REPORT}
echo ""

echo -e "${YELLOW}[8/10] Memory${NC}"
echo "========================================" >> ${AUDIT_REPORT}
echo "MEMORY" >> ${AUDIT_REPORT}
echo "========================================" >> ${AUDIT_REPORT}

# Memory info
TOTAL_MEM=$(free -h | grep Mem | awk '{print $2}')
USED_MEM=$(free -h | grep Mem | awk '{print $3}')
AVAIL_MEM=$(free -h | grep Mem | awk '{print $7}')

check_item "Total Memory" "OK" "${TOTAL_MEM}"
check_item "Available Memory" "OK" "${AVAIL_MEM} (Used: ${USED_MEM})"
echo "" >> ${AUDIT_REPORT}
echo ""

echo -e "${YELLOW}[9/10] Network Configuration${NC}"
echo "========================================" >> ${AUDIT_REPORT}
echo "NETWORK CONFIGURATION" >> ${AUDIT_REPORT}
echo "========================================" >> ${AUDIT_REPORT}

# Public IP
if command -v curl &> /dev/null; then
    PUBLIC_IP=$(curl -s ifconfig.me || echo "Unable to detect")
    check_item "Public IP" "OK" "${PUBLIC_IP}"
fi

# Listening services
LISTENING=$(netstat -tln 2>/dev/null | grep LISTEN | wc -l)
check_item "Listening Services" "OK" "${LISTENING} service(s)"
echo "" >> ${AUDIT_REPORT}
echo ""

echo -e "${YELLOW}[10/10] Existing Webhook Setup${NC}"
echo "========================================" >> ${AUDIT_REPORT}
echo "EXISTING WEBHOOK SETUP" >> ${AUDIT_REPORT}
echo "========================================" >> ${AUDIT_REPORT}

# Check if webhook already exists
if [ -d "$HOME/audiobook_webhook" ]; then
    check_item "Webhook Directory" "WARN" "Already exists at $HOME/audiobook_webhook"
else
    check_item "Webhook Directory" "OK" "Not found (will be created)"
fi

# Check for webhook process
if pgrep -f "audiobook_webhook_server" > /dev/null; then
    check_item "Webhook Process" "WARN" "Already running"
else
    check_item "Webhook Process" "OK" "Not running"
fi
echo "" >> ${AUDIT_REPORT}
echo ""

# Summary
echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  Audit Complete!                                          ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo "========================================" >> ${AUDIT_REPORT}
echo "RECOMMENDATIONS" >> ${AUDIT_REPORT}
echo "========================================" >> ${AUDIT_REPORT}

echo -e "${YELLOW}📋 Recommendations:${NC}"
echo ""

# Generate recommendations
RECOMMENDATIONS=""

if ! command -v python3 &> /dev/null; then
    RECOMMENDATIONS="${RECOMMENDATIONS}\n❌ Install Python 3"
fi

if ! python3 -c "import flask" 2>/dev/null; then
    RECOMMENDATIONS="${RECOMMENDATIONS}\n⚠️  Install Flask: pip3 install flask"
fi

if ! command -v nginx &> /dev/null; then
    RECOMMENDATIONS="${RECOMMENDATIONS}\n❌ Install Nginx"
fi

# Check for available port
PORT_FOUND=0
for PORT in 5001 5002 5003; do
    if ! netstat -tln 2>/dev/null | grep -q ":${PORT} "; then
        RECOMMENDATIONS="${RECOMMENDATIONS}\n✅ Use port ${PORT} for webhook server"
        PORT_FOUND=1
        break
    fi
done

if [ $PORT_FOUND -eq 0 ]; then
    RECOMMENDATIONS="${RECOMMENDATIONS}\n⚠️  All common ports are in use - choose a custom port"
fi

if [ -z "$RECOMMENDATIONS" ]; then
    echo -e "${GREEN}✅ Server is ready for webhook deployment!${NC}"
    echo "✅ Server is ready for webhook deployment!" >> ${AUDIT_REPORT}
else
    echo -e "${RECOMMENDATIONS}"
    echo -e "${RECOMMENDATIONS}" >> ${AUDIT_REPORT}
fi

echo ""
echo -e "${BLUE}📄 Full report saved to: ${AUDIT_REPORT}${NC}"
echo ""
echo -e "${YELLOW}🔍 Detailed Information:${NC}"
echo ""
echo -e "${CYAN}Nginx Configuration:${NC}"
if [ -d /etc/nginx/sites-enabled ]; then
    echo "Enabled sites:"
    ls -la /etc/nginx/sites-enabled
fi
echo ""

echo -e "${CYAN}SSL Certificates:${NC}"
if [ -d /etc/letsencrypt/live ]; then
    echo "Installed certificates:"
    sudo ls -la /etc/letsencrypt/live 2>/dev/null || echo "  (requires sudo to view)"
fi
echo ""

echo -e "${CYAN}Running Services on Port 80/443:${NC}"
sudo netstat -tlnp 2>/dev/null | grep -E ':(80|443) ' || echo "  (requires sudo to view)"
echo ""

echo -e "${GREEN}✅ Audit complete! Review the report and run the deployment script.${NC}"
echo ""
