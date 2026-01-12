#!/bin/bash

# Configuration
REMOTE_HOST="pizero2-2"
REMOTE_DIR="~/workspace/auto-chess-backend"
LOCAL_DIR="."

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}🚀 Deploying to $REMOTE_HOST...${NC}"

# Create remote directory if it doesn't exist
ssh "$REMOTE_HOST" "mkdir -p $REMOTE_DIR"

# Rsync files (only changed ones)
rsync -avz --delete \
  --exclude-from='.gitignore' \
  --exclude '.git/' \
  --exclude 'tests/' \
  --exclude 'analysis/' \
  --exclude 'docs/' \
  --exclude 'AGENTS.md' \
  "$LOCAL_DIR/" "$REMOTE_HOST:$REMOTE_DIR/"

echo -e "${GREEN}✅ Files synced successfully!${NC}"

# Optional: Install/update dependencies on remote
echo -e "${YELLOW}⚙️  Setting up environment on device...${NC}"
ssh "$REMOTE_HOST" "cd $REMOTE_DIR && bash setup_env.sh"

echo -e "${GREEN}🎉 Deployment complete!${NC}"
echo ""
echo "💡 To run commands on the device:"
echo "  ssh -t pizero2-2 'cd $REMOTE_DIR && ~/.local/bin/uv run chess home'"
echo "  ssh -t pizero2-2 'cd $REMOTE_DIR && ~/.local/bin/uv run chess status'"
echo ""
echo "🔧 Or create an alias:"
echo "  alias chess='ssh -t pizero2-2 \"cd $REMOTE_DIR && ~/.local/bin/uv run chess\"'"
echo "  Then use: chess home, chess status, etc."
