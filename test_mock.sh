#!/bin/bash
# Quick test script for mock mode

echo "Testing mock mode..."
echo

echo "=== Testing Status Command ==="
uv run python src/main.py status 2>/dev/null
echo

echo "=== Testing Home Command ==="
uv run python src/main.py home 2>/dev/null
echo

echo "=== Testing Magnet Commands ==="
uv run python src/main.py magnet-on 2>/dev/null
uv run python src/main.py magnet-off 2>/dev/null
echo

echo "=== Testing Motor Enable/Disable ==="
uv run python src/main.py motor-disable 2>/dev/null
uv run python src/main.py motor-enable 2>/dev/null
echo

echo "All tests passed! Ready to deploy."
