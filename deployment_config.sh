#!/bin/bash

################################################################################
# AudiobookSmith Webhook Deployment Configuration
#
# Edit these settings before running deploy_to_websolutionsserver.sh
################################################################################

# SSH Connection Settings
export REMOTE_HOST="websolutionsserver.net"
export REMOTE_USER="ubuntu"        # Change to your actual SSH username
export REMOTE_PORT="22"            # Change if using non-standard SSH port

# Installation Paths
export REMOTE_DIR="/home/\${REMOTE_USER}/audiobook_webhook"
export UPLOAD_DIR="\${REMOTE_DIR}/uploads"
export LOG_DIR="\${REMOTE_DIR}/logs"

# Server Settings
export WEBHOOK_PORT="5001"         # Port for webhook server
export MAX_FILE_SIZE="100"         # Maximum file size in MB

# Domain Settings (for Nginx configuration)
export WEBHOOK_DOMAIN="webhook.audiobooksmith.com"  # Your webhook domain

# Python Settings
export PYTHON_CMD="python3.11"     # Python command (python3.11 or python3)

# Optional: Email for notifications
export ADMIN_EMAIL="admin@audiobooksmith.com"

################################################################################
# Advanced Settings (usually don't need to change)
################################################################################

# Backup Settings
export BACKUP_DIR="\${REMOTE_DIR}/backups"
export KEEP_BACKUPS="7"            # Number of days to keep backups

# Log Rotation
export LOG_ROTATE_DAYS="30"        # Days to keep logs
export LOG_MAX_SIZE="100M"         # Maximum log file size

# Security
export API_KEY_ENABLED="false"     # Set to "true" to enable API key auth
export API_KEY=""                  # Set your API key if enabled

################################################################################
# Do not edit below this line
################################################################################

echo "Configuration loaded:"
echo "  Remote Host: ${REMOTE_HOST}"
echo "  Remote User: ${REMOTE_USER}"
echo "  Remote Port: ${REMOTE_PORT}"
echo "  Install Dir: ${REMOTE_DIR}"
echo "  Webhook Port: ${WEBHOOK_PORT}"
