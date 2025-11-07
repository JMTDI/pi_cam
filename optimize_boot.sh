#!/bin/bash

# Pi Zero Fast Boot Optimization Script
# Author: JMTDI
# Date: 2025-10-25

set -e

echo "⚡ Optimizing Pi Zero for fast boot..."
echo "===================================="

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   echo "❌ This script must be run as root"
   echo "Run as: sudo ./optimize_boot.sh"
   exit 1
fi

# Backup original files
echo "💾 Creating backups..."
cp /boot/config.txt /boot/config.txt.backup.$(date +%Y%m%d_%H%M%S)
cp /boot/cmdline.txt /boot/cmdline.txt.backup.$(date +%Y%m%d_%H%M%S)
cp /etc/fstab /etc/fstab.backup.$(date +%Y%m%d_%H%M%S)

# Disable unnecessary services
echo "🛑 Disabling unnecessary services..."
SERVICES_TO_DISABLE=(
    "bluetooth.service"
    "hciuart.service" 
    "avahi-daemon.service"
    "triggerhappy.service"
    "keyboard-setup.service"
    "dphys-swapfile.service"
    "rsync.service"
    "nfs-common.service"
    "rpcbind.service"
    "apt-daily.service"
    "apt-daily-upgrade.service"
    "man-db.service"
)

for service in "${SERVICES_TO_DISABLE[@]}"; do
    if systemctl is-enabled $service >/dev/null 2>&1; then
        echo "  Disabling $service"
        systemctl disable $service
    fi
done

# Configure boot settings in config.txt
echo "🔧 Configuring boot settings..."
cat >> /boot/config.txt << EOF

# Pi Zero Camera Fast Boot Configuration
# Added on $(date)

# Boot optimization
boot_delay=0
disable_splash=1
avoid_warnings=1

# GPU memory allocation (minimal for camera)
gpu_mem=64

# Enable camera
start_x=1

# Enable SPI for display
dtparam=spi=on

# Disable unused hardware (keep WiFi for network share)
dtoverlay=disable-bt

# Speed up boot
initial_turbo=30

EOF

# Optimize cmdline.txt for faster boot
echo "🚀 Optimizing kernel command line..."
CURRENT_CMDLINE=$(cat /boot/cmdline.txt)
# Remove console output and add quiet boot options
NEW_CMDLINE="$CURRENT_CMDLINE quiet splash loglevel=1 logo.nologo vt.global_cursor_default=0"
echo "$NEW_CMDLINE" > /boot/cmdline.txt

# Create systemd optimizations
echo "⚙️ Optimizing systemd..."
mkdir -p /etc/systemd/system.conf.d
cat > /etc/systemd/system.conf.d/boot-optimization.conf << EOF
[Manager]
DefaultTimeoutStartSec=15s
DefaultTimeoutStopSec=5s
DefaultRestartSec=1s
EOF

# Configure faster filesystem mounts
echo "💾 Configuring filesystem optimizations..."
cat >> /etc/fstab << EOF

# Temporary filesystems for better performance and less SD wear
tmpfs /tmp tmpfs defaults,noatime,nosuid,size=100m 0 0
tmpfs /var/log tmpfs defaults,noatime,nosuid,mode=0755,size=50m 0 0
tmpfs /var/tmp tmpfs defaults,noatime,nosuid,size=50m 0 0
EOF

# Preload modules for camera and SPI
echo "📦 Configuring module preloading..."
cat >> /etc/modules << EOF

# Preload camera and display modules for faster startup
bcm2835-v4l2
spi-bcm2835
EOF

echo ""
echo "✅ Boot optimization complete!"
echo ""
echo "Expected improvements:"
echo "• Boot time: 15-25 seconds (from 45+ seconds)"
echo "• Camera ready: Within 20 seconds of power on"
echo "• Network share available immediately after boot"
echo "• Reduced SD card wear"
echo "• Lower memory usage"
echo ""
echo "⚠️  Note: Some optimizations disable features like Bluetooth"
echo "   WiFi is kept enabled for network share functionality"
echo "   Edit /boot/config.txt to re-enable if needed"
echo ""
echo "🔄 Reboot to apply changes: sudo reboot"