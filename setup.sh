#!/bin/bash
# Setup script for Research Pivot Advisor System
# Installs required dependencies for macOS

set -e  # Exit on error

echo "🚀 Setting up Research Pivot Advisor System..."
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if running on macOS
if [[ "$OSTYPE" != "darwin"* ]]; then
    echo -e "${RED}❌ This script is for macOS only${NC}"
    exit 1
fi

echo "📋 Checking current environment..."
echo ""

# Check current Python version
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
    echo "Current Python version: $PYTHON_VERSION"
else
    echo -e "${RED}Python 3 not found${NC}"
    PYTHON_VERSION="0.0.0"
fi

# Check if Homebrew is installed
if ! command -v brew &> /dev/null; then
    echo -e "${YELLOW}⚠️  Homebrew not found. Installing...${NC}"
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

    # Add Homebrew to PATH
    echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
    eval "$(/opt/homebrew/bin/brew shellenv)"

    echo -e "${GREEN}✅ Homebrew installed${NC}"
else
    echo -e "${GREEN}✅ Homebrew already installed${NC}"
fi

echo ""
echo "📦 Installing required packages..."
echo ""

# Install Python 3.11
if ! command -v python3.11 &> /dev/null; then
    echo "Installing Python 3.11..."
    brew install python@3.11
    echo -e "${GREEN}✅ Python 3.11 installed${NC}"
else
    echo -e "${GREEN}✅ Python 3.11 already installed${NC}"
fi

# Verify Python 3.11
PYTHON311_VERSION=$(python3.11 --version)
echo "Python 3.11 version: $PYTHON311_VERSION"

# Install Poetry
if ! command -v poetry &> /dev/null; then
    echo "Installing Poetry..."
    curl -sSL https://install.python-poetry.org | python3.11 -

    # Add Poetry to PATH
    export PATH="$HOME/.local/bin:$PATH"
    echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc

    echo -e "${GREEN}✅ Poetry installed${NC}"
else
    echo -e "${GREEN}✅ Poetry already installed${NC}"
fi

poetry --version

# Install Docker Desktop (just check, manual install required)
if ! command -v docker &> /dev/null; then
    echo -e "${YELLOW}⚠️  Docker not found${NC}"
    echo "Installing Docker Desktop..."
    brew install --cask docker
    echo -e "${YELLOW}⚠️  Please start Docker Desktop app manually${NC}"
    echo "Open Spotlight (Cmd+Space), type 'Docker', press Enter"
    echo "Wait for Docker to start, then run this script again."
else
    echo -e "${GREEN}✅ Docker already installed${NC}"

    # Check if Docker daemon is running
    if docker ps &> /dev/null; then
        echo -e "${GREEN}✅ Docker daemon is running${NC}"
    else
        echo -e "${YELLOW}⚠️  Docker daemon not running. Please start Docker Desktop.${NC}"
    fi
fi

# Install Node.js 18
if ! command -v node &> /dev/null; then
    echo "Installing Node.js 18..."
    brew install node@18
    echo -e "${GREEN}✅ Node.js installed${NC}"
else
    NODE_VERSION=$(node --version)
    echo -e "${GREEN}✅ Node.js already installed: $NODE_VERSION${NC}"
fi

echo ""
echo "🐳 Starting Docker services..."
echo ""

# Start Docker Compose services
if docker ps &> /dev/null; then
    docker-compose up -d
    echo -e "${GREEN}✅ PostgreSQL and Redis containers started${NC}"

    # Wait for services to be ready
    echo "Waiting for databases to be ready..."
    sleep 5

    docker ps
else
    echo -e "${YELLOW}⚠️  Skipping Docker Compose (Docker not running)${NC}"
fi

echo ""
echo "🎯 Setup Summary"
echo "================================"

# Python
if command -v python3.11 &> /dev/null; then
    echo -e "${GREEN}✅ Python 3.11: $(python3.11 --version)${NC}"
else
    echo -e "${RED}❌ Python 3.11: Not installed${NC}"
fi

# Poetry
if command -v poetry &> /dev/null; then
    echo -e "${GREEN}✅ Poetry: $(poetry --version)${NC}"
else
    echo -e "${RED}❌ Poetry: Not installed${NC}"
fi

# Docker
if command -v docker &> /dev/null; then
    echo -e "${GREEN}✅ Docker: $(docker --version)${NC}"
    if docker ps &> /dev/null; then
        echo -e "${GREEN}✅ Docker daemon: Running${NC}"
    else
        echo -e "${YELLOW}⚠️  Docker daemon: Not running${NC}"
    fi
else
    echo -e "${RED}❌ Docker: Not installed${NC}"
fi

# Node.js
if command -v node &> /dev/null; then
    echo -e "${GREEN}✅ Node.js: $(node --version)${NC}"
else
    echo -e "${RED}❌ Node.js: Not installed${NC}"
fi

# Docker services
if docker ps | grep -q postgres; then
    echo -e "${GREEN}✅ PostgreSQL: Running on port 5432${NC}"
else
    echo -e "${YELLOW}⚠️  PostgreSQL: Not running${NC}"
fi

if docker ps | grep -q redis; then
    echo -e "${GREEN}✅ Redis: Running on port 6379${NC}"
else
    echo -e "${YELLOW}⚠️  Redis: Not running${NC}"
fi

echo ""
echo "🎉 Setup complete!"
echo ""
echo "Next steps:"
echo "1. Review docs/CURSOR_IDE_SETUP.md for build instructions"
echo "2. Start Cursor IDE"
echo "3. Open Composer (Cmd+I) and begin Phase 1"
echo ""
echo "Quick start commands:"
echo "  cd research-advisor-backend && poetry install    # Install backend deps"
echo "  cd research-advisor-frontend && npm install      # Install frontend deps"
echo ""
