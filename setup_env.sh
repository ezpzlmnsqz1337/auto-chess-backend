#!/bin/bash
# Setup Python environment for auto-chess-backend on Raspberry Pi

set -e  # Exit on error

cd "$(dirname "$0")"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${CYAN}⚙️  Setting up environment...${NC}"

# Install system dependencies for GPIO access (only if needed)
if ! dpkg -l | grep -q python3-lgpio; then
    echo -e "${YELLOW}📦 Installing system dependencies...${NC}"
    sudo apt-get update -qq
    sudo apt-get install -y python3-lgpio swig liblgpio-dev
else
    echo -e "${GREEN}✓ System dependencies already installed, skipping...${NC}"
fi

# Install uv if not present
export PATH="$HOME/.local/bin:$PATH"
if ! command -v uv &> /dev/null; then
    echo -e "${YELLOW}📥 Installing uv...${NC}"
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"
fi

# Create or update virtual environment
echo -e "${YELLOW}🔨 Creating/updating virtual environment...${NC}"
uv venv --python 3.13.5 --clear

# Sync dependencies
echo -e "${YELLOW}📚 Syncing Python dependencies...${NC}"
uv sync

# Install lgpio into the venv
echo -e "${YELLOW}🔌 Installing GPIO libraries into venv...${NC}"
export PATH="$HOME/.local/bin:$PATH"
uv pip install rpi-lgpio

echo -e "${GREEN}✅ Environment setup complete!${NC}"
