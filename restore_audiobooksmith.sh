#!/bin/bash
###############################################################################
# AudiobookSmith Backend Restoration Script
# 
# This script restores the complete AudiobookSmith backend environment from
# GitHub in case of server failure or data loss.
#
# Version: 1.0.0
# Author: Manus AI
# Date: December 2025
###############################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
GITHUB_REPO="vitalykirkpatrick/audiobooksmithapp"
INSTALL_DIR="/root"
BACKUP_DIR="/root/backup_$(date +%Y%m%d_%H%M%S)"

echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║   AudiobookSmith Backend Restoration Script v1.0.0        ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

###############################################################################
# Step 1: Backup existing files
###############################################################################
echo -e "${YELLOW}[1/7] Creating backup of existing files...${NC}"
mkdir -p "$BACKUP_DIR"

if [ -f "$INSTALL_DIR/audiobook_webhook_server_v7_with_voices.py" ]; then
    cp "$INSTALL_DIR"/*.py "$BACKUP_DIR/" 2>/dev/null || true
    echo -e "${GREEN}✓ Backed up existing Python files to $BACKUP_DIR${NC}"
else
    echo -e "${YELLOW}⚠ No existing files found, skipping backup${NC}"
fi

###############################################################################
# Step 2: Install dependencies
###############################################################################
echo -e "${YELLOW}[2/7] Installing system dependencies...${NC}"

# Check if git is installed
if ! command -v git &> /dev/null; then
    echo "Installing git..."
    apt-get update && apt-get install -y git
fi

# Check if gh CLI is installed
if ! command -v gh &> /dev/null; then
    echo "Installing GitHub CLI..."
    type -p curl >/dev/null || (apt update && apt install curl -y)
    curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg
    chmod go+r /usr/share/keyrings/githubcli-archive-keyring.gpg
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | tee /etc/apt/sources.list.d/github-cli.list > /dev/null
    apt update && apt install gh -y
fi

echo -e "${GREEN}✓ System dependencies installed${NC}"

###############################################################################
# Step 3: Clone/Pull from GitHub
###############################################################################
echo -e "${YELLOW}[3/7] Fetching latest code from GitHub...${NC}"

TEMP_DIR="/tmp/audiobooksmith_restore"
rm -rf "$TEMP_DIR"

# Clone repository
git clone "https://github.com/$GITHUB_REPO.git" "$TEMP_DIR"

echo -e "${GREEN}✓ Code fetched from GitHub${NC}"

###############################################################################
# Step 4: Install Python dependencies
###############################################################################
echo -e "${YELLOW}[4/7] Installing Python dependencies...${NC}"

# Ensure pip is installed
if ! command -v pip3 &> /dev/null; then
    apt-get install -y python3-pip
fi

# Install required packages
pip3 install --upgrade pip
pip3 install openai flask beautifulsoup4 striprtf mobi PyPDF2 ebooklib python-docx

echo -e "${GREEN}✓ Python dependencies installed${NC}"

###############################################################################
# Step 5: Copy files to installation directory
###############################################################################
echo -e "${YELLOW}[5/7] Copying files to $INSTALL_DIR...${NC}"

# Copy all Python files
cp "$TEMP_DIR"/*.py "$INSTALL_DIR/" 2>/dev/null || true

# Copy documentation
cp "$TEMP_DIR"/*.md "$INSTALL_DIR/" 2>/dev/null || true

# Set permissions
chmod +x "$INSTALL_DIR"/*.py

echo -e "${GREEN}✓ Files copied to installation directory${NC}"

###############################################################################
# Step 6: Restore environment variables
###############################################################################
echo -e "${YELLOW}[6/7] Checking environment variables...${NC}"

if [ ! -f "$INSTALL_DIR/.env" ]; then
    echo -e "${RED}⚠ WARNING: .env file not found!${NC}"
    echo "Creating template .env file..."
    cat > "$INSTALL_DIR/.env" << 'EOF'
# AudiobookSmith Environment Variables
# IMPORTANT: Fill in your actual API keys below

OPENAI_API_KEY=your_openai_api_key_here
ELEVENLABS_API_KEY=your_elevenlabs_api_key_here
SLACK_WEBHOOK_URL=your_slack_webhook_url_here

# Optional: Uncomment and configure if needed
# ANTHROPIC_API_KEY=your_anthropic_key_here
# PERPLEXITY_API_KEY=your_perplexity_key_here
EOF
    echo -e "${YELLOW}⚠ Please edit $INSTALL_DIR/.env with your actual API keys${NC}"
else
    echo -e "${GREEN}✓ .env file exists${NC}"
fi

###############################################################################
# Step 7: Verify installation
###############################################################################
echo -e "${YELLOW}[7/7] Verifying installation...${NC}"

REQUIRED_FILES=(
    "audiobook_webhook_server_v7_with_voices.py"
    "audiobook_processor_v8_universal_formats.py"
    "universal_text_extractor.py"
    "narration_preparation_processor.py"
    "audiobooksmith_integration.py"
    "progress_tracker.py"
)

MISSING_FILES=()

for file in "${REQUIRED_FILES[@]}"; do
    if [ -f "$INSTALL_DIR/$file" ]; then
        echo -e "${GREEN}✓ $file${NC}"
    else
        echo -e "${RED}✗ $file (MISSING)${NC}"
        MISSING_FILES+=("$file")
    fi
done

# Cleanup
rm -rf "$TEMP_DIR"

###############################################################################
# Summary
###############################################################################
echo ""
echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║              Restoration Complete!                        ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

if [ ${#MISSING_FILES[@]} -eq 0 ]; then
    echo -e "${GREEN}✓ All required files are present${NC}"
    echo ""
    echo -e "${YELLOW}Next steps:${NC}"
    echo "1. Edit $INSTALL_DIR/.env with your API keys"
    echo "2. Start the webhook server:"
    echo "   cd $INSTALL_DIR"
    echo "   source .env"
    echo "   nohup python3 audiobook_webhook_server_v7_with_voices.py > webhook.log 2>&1 &"
    echo ""
    echo -e "${GREEN}Backup location: $BACKUP_DIR${NC}"
else
    echo -e "${RED}⚠ WARNING: ${#MISSING_FILES[@]} required files are missing:${NC}"
    for file in "${MISSING_FILES[@]}"; do
        echo -e "${RED}  - $file${NC}"
    done
    echo ""
    echo "Please check the GitHub repository and ensure all files are present."
    exit 1
fi

echo ""
echo -e "${GREEN}Restoration completed successfully!${NC}"
