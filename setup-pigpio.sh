#!/bin/bash
# Setup script for pigpio daemon on Raspberry Pi

set -e

echo "🔧 Installing pigpio daemon..."

# Install pigpio if not already installed
if ! dpkg -l | grep -q pigpio; then
    echo "Installing pigpio package..."
    sudo apt-get update
    sudo apt-get install -y pigpio python3-pigpio
else
    echo "✅ pigpio already installed"
fi

# Enable and start pigpiod service
echo "Enabling pigpiod service..."
sudo systemctl enable pigpiod
sudo systemctl start pigpiod

# Check if service is running
if systemctl is-active --quiet pigpiod; then
    echo "✅ pigpiod service is running"
else
    echo "❌ Failed to start pigpiod service"
    exit 1
fi

echo ""
echo "✅ pigpio setup complete!"
echo ""
echo "The pigpiod daemon will now start automatically on boot."
echo "To manually control it:"
echo "  sudo systemctl start pigpiod    # Start daemon"
echo "  sudo systemctl stop pigpiod     # Stop daemon"
echo "  sudo systemctl status pigpiod   # Check status"
