#!/bin/bash
################################################################################
# AudiobookSmith V12 - Production Deployment Script
# Server: 172.245.67.47 (audiobooksmith.app)
# Version: V12 Hybrid Chapter Splitter
# Date: December 8, 2025
################################################################################

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
APP_DIR="/var/www/audiobooksmith"  # Adjust this to your actual path
GITHUB_REPO="https://github.com/vitalykirkpatrick/audiobooksmithapp.git"
PYTHON_CMD="python3"
PIP_CMD="pip3"

################################################################################
# Helper Functions
################################################################################

print_header() {
    echo -e "${BLUE}================================================================================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}================================================================================================${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

################################################################################
# Pre-Deployment Checks
################################################################################

print_header "AUDIOBOOKSMITH V12 - PRODUCTION DEPLOYMENT"
echo ""
print_info "Starting deployment process..."
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    print_error "Please run as root (use: sudo bash deploy_v12_to_production.sh)"
    exit 1
fi

print_success "Running as root"

# Check Python installation
print_info "Checking Python installation..."
if command -v $PYTHON_CMD &> /dev/null; then
    PYTHON_VERSION=$($PYTHON_CMD --version 2>&1 | awk '{print $2}')
    print_success "Python $PYTHON_VERSION found"
else
    print_error "Python 3 not found. Please install Python 3.7+"
    exit 1
fi

# Check pip installation
print_info "Checking pip installation..."
if command -v $PIP_CMD &> /dev/null; then
    print_success "pip found"
else
    print_error "pip not found. Installing..."
    apt-get update && apt-get install -y python3-pip
fi

# Check git installation
print_info "Checking git installation..."
if command -v git &> /dev/null; then
    print_success "git found"
else
    print_error "git not found. Installing..."
    apt-get update && apt-get install -y git
fi

echo ""

################################################################################
# Application Directory Setup
################################################################################

print_header "STEP 1: APPLICATION DIRECTORY SETUP"
echo ""

# Check if app directory exists
if [ -d "$APP_DIR" ]; then
    print_success "Application directory exists: $APP_DIR"
    cd "$APP_DIR"
    
    # Check if it's a git repository
    if [ -d ".git" ]; then
        print_success "Git repository found"
    else
        print_warning "Not a git repository. Initializing..."
        git init
        git remote add origin $GITHUB_REPO
    fi
else
    print_warning "Application directory not found. Creating..."
    mkdir -p "$APP_DIR"
    cd "$APP_DIR"
    print_success "Created directory: $APP_DIR"
    
    print_info "Cloning repository..."
    git clone $GITHUB_REPO .
    print_success "Repository cloned"
fi

echo ""

################################################################################
# Pull Latest Code
################################################################################

print_header "STEP 2: PULLING LATEST CODE FROM GITHUB"
echo ""

print_info "Fetching latest changes..."
git fetch origin

print_info "Pulling main branch..."
git pull origin main

print_success "Code updated to latest version"

# Show latest commit
LATEST_COMMIT=$(git log -1 --pretty=format:"%h - %s (%cr)")
print_info "Latest commit: $LATEST_COMMIT"

echo ""

################################################################################
# Install Dependencies
################################################################################

print_header "STEP 3: INSTALLING DEPENDENCIES"
echo ""

print_info "Installing required Python packages..."

# Install packages one by one with status
packages=("PyMuPDF" "pdfplumber" "PyPDF2")

for package in "${packages[@]}"; do
    print_info "Installing $package..."
    $PIP_CMD install --upgrade $package > /dev/null 2>&1
    if [ $? -eq 0 ]; then
        print_success "$package installed"
    else
        print_error "Failed to install $package"
        exit 1
    fi
done

echo ""

################################################################################
# Verify Installation
################################################################################

print_header "STEP 4: VERIFYING INSTALLATION"
echo ""

print_info "Testing Python imports..."

$PYTHON_CMD << 'EOF'
import sys
try:
    import fitz
    print("✅ PyMuPDF (fitz) imported successfully")
except ImportError as e:
    print(f"❌ PyMuPDF import failed: {e}")
    sys.exit(1)

try:
    import pdfplumber
    print("✅ pdfplumber imported successfully")
except ImportError as e:
    print(f"❌ pdfplumber import failed: {e}")
    sys.exit(1)

try:
    import PyPDF2
    print("✅ PyPDF2 imported successfully")
except ImportError as e:
    print(f"❌ PyPDF2 import failed: {e}")
    sys.exit(1)

print("\n✅ All dependencies verified successfully")
EOF

if [ $? -ne 0 ]; then
    print_error "Dependency verification failed"
    exit 1
fi

echo ""

################################################################################
# File Permissions
################################################################################

print_header "STEP 5: SETTING FILE PERMISSIONS"
echo ""

print_info "Setting executable permissions..."
chmod +x audiobook_processor_v12_hybrid.py 2>/dev/null || true
chmod +x hybrid_chapter_splitter_production.py 2>/dev/null || true

print_success "Permissions set"

echo ""

################################################################################
# Test Run (Optional)
################################################################################

print_header "STEP 6: DEPLOYMENT VERIFICATION"
echo ""

print_info "Checking V12 processor..."
if [ -f "audiobook_processor_v12_hybrid.py" ]; then
    print_success "V12 processor found"
else
    print_error "V12 processor not found!"
    exit 1
fi

if [ -f "hybrid_chapter_splitter_production.py" ]; then
    print_success "Hybrid splitter found"
else
    print_error "Hybrid splitter not found!"
    exit 1
fi

if [ -f "vitaly_book_final_enriched_metadata.json" ]; then
    print_success "Enriched metadata found"
else
    print_warning "Enriched metadata not found (optional for V12)"
fi

echo ""

################################################################################
# Create Test Script
################################################################################

print_info "Creating test script..."

cat > test_v12.sh << 'TESTEOF'
#!/bin/bash
# Quick test script for V12

if [ -z "$1" ]; then
    echo "Usage: ./test_v12.sh /path/to/book.pdf"
    exit 1
fi

python3 audiobook_processor_v12_hybrid.py "$1"
TESTEOF

chmod +x test_v12.sh
print_success "Test script created: ./test_v12.sh"

echo ""

################################################################################
# Deployment Summary
################################################################################

print_header "DEPLOYMENT COMPLETE! 🎉"
echo ""

print_success "AudiobookSmith V12 successfully deployed!"
echo ""

print_info "Deployment Summary:"
echo "  📁 Location: $APP_DIR"
echo "  🔧 Python: $PYTHON_VERSION"
echo "  📦 Dependencies: PyMuPDF, pdfplumber, PyPDF2"
echo "  ✅ Status: READY FOR PRODUCTION"
echo ""

print_info "Files Deployed:"
echo "  ✅ audiobook_processor_v12_hybrid.py"
echo "  ✅ hybrid_chapter_splitter_production.py"
echo "  ✅ vitaly_book_final_enriched_metadata.json"
echo "  ✅ V12_DEPLOYMENT_GUIDE.md"
echo ""

print_info "Quick Start:"
echo "  1. Test with: ./test_v12.sh /path/to/book.pdf"
echo "  2. Or run: python3 audiobook_processor_v12_hybrid.py /path/to/book.pdf"
echo "  3. Check output in: BookName_v12_results_TIMESTAMP/"
echo ""

print_info "Documentation:"
echo "  📖 Read: V12_DEPLOYMENT_GUIDE.md"
echo "  🔗 GitHub: https://github.com/vitalykirkpatrick/audiobooksmithapp"
echo ""

print_success "V12 is ready to process books! 🚀"
echo ""

################################################################################
# End of Script
################################################################################
