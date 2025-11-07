#!/bin/bash

# Complete Pi Zero Camera Setup Script with Network Share
# Author: JMTDI
# Date: 2025-10-25

echo "🎯 Pi Zero Camera - Complete Setup with Network Share"
echo "===================================================="
echo "This script will install and configure your Pi Zero instant camera"
echo "with automatic photo sharing to Windows devices on your network."
echo ""

# Check if running as pi user
if [ "$USER" != "pi" ]; then
    echo "❌ This script should be run as the 'pi' user"
    echo "Run as: ./complete_setup.sh"
    exit 1
fi

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &> /dev/null && pwd)"

echo "📍 Setup directory: $SCRIPT_DIR"
echo ""

# Step 1: Install camera system with network share
echo "Step 1/2: Installing camera system with network share..."
"$SCRIPT_DIR/install.sh"
if [ $? -ne 0 ]; then
    echo "❌ Camera installation failed"
    exit 1
fi

# Step 2: Boot optimization
echo ""
echo "Step 2/2: Optimizing boot performance..."
sudo "$SCRIPT_DIR/optimize_boot.sh"
if [ $? -ne 0 ]; then
    echo "❌ Boot optimization failed"
    exit 1
fi

# Get network information for user
echo ""
echo "🌐 Getting network information..."
IP_ADDRESS=$(hostname -I | awk '{print $1}')
HOSTNAME=$(hostname)

# Final configuration
echo ""
echo "🔧 Final configuration complete!"

# Summary
echo ""
echo "🎉 Setup Complete!"
echo "=================="
echo ""
echo "Your Pi Zero camera is ready with network sharing! Here's what was installed:"
echo ""
echo "✅ ST7735S display driver (128x128 color LCD)"
echo "✅ Camera application with live preview"
echo "✅ Settings app with WiFi management"
echo "✅ Network share system (Samba)"
echo "✅ Photo organization by date"
echo "✅ Fast boot optimization (15-25 second boot)"
echo "✅ Auto-start service (starts on boot)"
echo ""
echo "🎮 How to use the camera:"
echo "• Power on → Wait 20 seconds → Camera launcher appears"
echo "• D-pad LEFT/RIGHT: Switch between Camera/Settings"
echo "• CENTER button: Select app or take photo"
echo "• UP button (in apps): Return to launcher"
echo ""
echo "📁 How to access photos from Windows:"
echo "1. Make sure both devices are on the same WiFi network"
echo "2. Open File Explorer on Windows"
echo "3. In the address bar, type: \\\\$IP_ADDRESS\\PiCamera"
echo "4. Press Enter"
echo ""
echo "Alternative access methods:"
echo "• By hostname: \\\\$HOSTNAME\\PiCamera"
echo "• Network discovery: Look for '$HOSTNAME' in Network"
echo ""
echo "📂 Photo organization:"
echo "• by_date/ folder: Photos organized by date (YYYY-MM-DD)"
echo "• all_photos/ folder: All photos in chronological order"
echo "• Photos appear automatically as you take them!"
echo ""
echo "🔧 System information:"
echo "• Camera device: $HOSTNAME"
echo "• IP address: $IP_ADDRESS"
echo "• Share name: PiCamera"
echo "• Access instructions: /home/pi/camera_share/HOW_TO_ACCESS_FROM_WINDOWS.txt"
echo ""
echo "🔄 Next steps:"
echo "1. sudo reboot  (to enable all optimizations)"
echo "2. Wait for camera launcher to appear on screen"
echo "3. Test camera functionality"
echo "4. Configure WiFi in Settings app if needed"
echo "5. Take photos and check Windows access"
echo ""

read -p "Ready to reboot and start using your camera? (Y/n): " do_reboot
if [ "$do_reboot" != "n" ] && [ "$do_reboot" != "N" ]; then
    echo ""
    echo "🔄 Rebooting in 5 seconds..."
    echo ""
    echo "After reboot:"
    echo "• Your camera will start automatically"
    echo "• Photos will be accessible from Windows immediately"
    echo "• Network share: \\\\$IP_ADDRESS\\PiCamera"
    echo ""
    sleep 5
    sudo reboot
else
    echo ""
    echo "✅ Setup complete!"
    echo ""
    echo "Manual reboot: sudo reboot"
    echo "Access photos: \\\\$IP_ADDRESS\\PiCamera"
    echo "Enjoy your Pi Zero instant camera! 📷✨"
fi