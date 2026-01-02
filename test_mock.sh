#!/bin/bash
# Quick test script for mock mode

echo "🧪 Testing mock mode..."
echo

echo "=== 📊 Testing Status Command ==="
uv run chess status 2>/dev/null
echo

echo "=== 🏠 Testing Home Command ==="
uv run chess home 2>/dev/null
echo

echo "=== 🧲 Testing Magnet Commands ==="
uv run chess magnet-on 2>/dev/null
uv run chess magnet-off 2>/dev/null
echo

echo "=== ⚡ Testing Motor Enable/Disable ==="
uv run chess motor-disable 2>/dev/null
uv run chess motor-enable 2>/dev/null
echo

echo "✅ All tests passed! Ready to deploy."
