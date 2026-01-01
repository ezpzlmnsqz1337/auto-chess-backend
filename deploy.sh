#!/bin/bash

# Configuration
REMOTE_HOST="pizero2-2"
REMOTE_DIR="/home/mazel/workspace/auto-chess-backend"
LOCAL_DIR="."

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Deploying to $REMOTE_HOST...${NC}"

# Create remote directory if it doesn't exist
ssh "$REMOTE_HOST" "mkdir -p $REMOTE_DIR"

# Rsync files (only changed ones)
rsync -avz --delete \
  --exclude '.git/' \
  --exclude '.venv/' \
  --exclude '__pycache__/' \
  --exclude '*.pyc' \
  --exclude '.pytest_cache/' \
  --exclude '.mypy_cache/' \
  --exclude '.ruff_cache/' \
  --exclude 'tests/output/' \
  --exclude 'analysis/' \
  --exclude 'docs/' \
  --exclude '.DS_Store' \
  "$LOCAL_DIR/" "$REMOTE_HOST:$REMOTE_DIR/"

echo -e "${GREEN}Files synced successfully!${NC}"

# Optional: Install/update dependencies on remote
echo -e "${YELLOW}Setting up environment on device...${NC}"
ssh "$REMOTE_HOST" << 'ENDSSH'
cd /home/mazel/workspace/auto-chess-backend

# Install system dependencies for GPIO access
echo "Installing system dependencies..."
sudo apt-get update -qq
sudo apt-get install -y python3-lgpio swig liblgpio-dev

# Install uv if not present
if ! command -v uv &> /dev/null; then
    echo "Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"
fi
# Create or update virtual environment
echo "Creating/updating virtual environment..."
uv venv --python 3.13.5 --clear

# Sync dependencies
echo "Syncing Python dependencies..."
uv sync

# Install lgpio into the venv
echo "Installing GPIO libraries into venv..."
export PATH="$HOME/.local/bin:$PATH"
uv pip install rpi-lgpio
ENDSSH

echo -e "${GREEN}Deployment complete!${NC}"
echo ""
echo "To run commands on the device:"
echo "  ssh pizero2-2 'cd $REMOTE_DIR && ~/.local/bin/uv run python src/main.py home'"
echo "  ssh pizero2-2 'cd $REMOTE_DIR && ~/.local/bin/uv run python src/main.py status'"
echo ""
echo "Or create an alias:"
echo "  alias chess='ssh pizero2-2 \"cd $REMOTE_DIR && ~/.local/bin/uv run python src/main.py\"'"
echo "  Then use: chess home, chess status, etc."
