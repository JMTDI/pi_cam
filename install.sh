#!/bin/bash

# Pi Zero Camera Installation Script with Network Share
# Author: JMTDI
# Date: 2025-10-25

set -e  # Exit on any error

echo "🚀 Installing Pi Zero Camera System with Network Share..."
echo "======================================================="

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   echo "❌ This script should not be run as root"
   echo "Run as: ./install.sh"
   exit 1
fi

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
INSTALL_DIR="/home/pi/camera"

echo "📂 Installation directory: $INSTALL_DIR"

# Create installation directory
sudo mkdir -p "$INSTALL_DIR"
sudo chown pi:pi "$INSTALL_DIR"

# Copy all Python files
echo "📁 Copying application files..."
cp "$SCRIPT_DIR"/*.py "$INSTALL_DIR/"
chmod +x "$INSTALL_DIR/main.py"

# Update system
echo "📦 Updating system packages..."
sudo apt update

# Install required system packages including Samba
echo "📦 Installing system dependencies..."
sudo apt install -y \
    python3-pip \
    python3-dev \
    python3-picamera \
    python3-rpi.gpio \
    python3-spidev \
    python3-pil \
    python3-numpy \
    samba \
    samba-common-bin \
    git \
    vim \
    wireless-tools \
    wpasupplicant

# Install Python packages
echo "🐍 Installing Python dependencies..."
pip3 install --user requests Pillow

# Add user to hardware groups
echo "👥 Adding user to hardware groups..."
sudo usermod -a -G gpio pi
sudo usermod -a -G spi pi
sudo usermod -a -G video pi

# Enable hardware interfaces
echo "🔧 Enabling hardware interfaces..."
sudo raspi-config nonint do_camera 0
sudo raspi-config nonint do_spi 0

# Create directories with proper permissions
echo "📁 Creating camera directories..."
mkdir -p "$INSTALL_DIR/photos"
mkdir -p "$INSTALL_DIR/data"
mkdir -p "$INSTALL_DIR/logs"
chmod 755 "$INSTALL_DIR"/{photos,data,logs}

# Set up network share
echo "🌐 Setting up network share..."
python3 "$INSTALL_DIR/share_server.py"

# Create systemd service
echo "⚙️ Creating systemd service..."
sudo tee /etc/systemd/system/picamera.service > /dev/null <<EOF
[Unit]
Description=Pi Zero Camera Launcher
After=multi-user.target network.target
Wants=network.target

[Service]
Type=simple
User=pi
Group=pi
WorkingDirectory=$INSTALL_DIR
Environment=HOME=/home/pi
Environment=PYTHONPATH=$INSTALL_DIR
Environment=DISPLAY=:0
ExecStartPre=/bin/sleep 10
ExecStart=/usr/bin/python3 $INSTALL_DIR/main.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
KillMode=mixed
TimeoutStopSec=30

[Install]
WantedBy=multi-user.target
EOF

# Enable service
sudo systemctl daemon-reload
sudo systemctl enable picamera.service

# Create hardware test script
echo "🧪 Creating hardware test script..."
cat > "$INSTALL_DIR/test_hardware.py" << 'EOF'
#!/usr/bin/env python3
"""Hardware test script for Pi Zero Camera"""

def test_gpio():
    try:
        import RPi.GPIO as GPIO
        GPIO.setmode(GPIO.BCM)
        print("✅ GPIO: OK")
        GPIO.cleanup()
        return True
    except Exception as e:
        print(f"❌ GPIO: {e}")
        return False

def test_spi():
    try:
        import spidev
        spi = spidev.SpiDev()
        spi.open(0, 0)
        print("✅ SPI: OK")
        spi.close()
        return True
    except Exception as e:
        print(f"❌ SPI: {e}")
        return False

def test_camera():
    try:
        from picamera import PiCamera
        camera = PiCamera()
        camera.close()
        print("✅ Camera: OK")
        return True
    except Exception as e:
        print(f"❌ Camera: {e}")
        return False

def test_pil():
    try:
        from PIL import Image, ImageDraw, ImageFont
        print("✅ PIL: OK")
        return True
    except Exception as e:
        print(f"❌ PIL: {e}")
        return False

def test_samba():
    try:
        import subprocess
        result = subprocess.run(['sudo', 'systemctl', 'is-active', 'smbd'], 
                              capture_output=True, text=True)
        if result.stdout.strip() == 'active':
            print("✅ Samba: OK")
            return True
        else:
            print("❌ Samba: Not running")
            return False
    except Exception as e:
        print(f"❌ Samba: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing hardware and services...")
    all_ok = True
    all_ok &= test_gpio()
    all_ok &= test_spi()
    all_ok &= test_camera()
    all_ok &= test_pil()
    all_ok &= test_samba()
    
    if all_ok:
        print("✅ All tests passed!")
        print("📁 Network share will be accessible at:")
        try:
            import subprocess
            ip_result = subprocess.run(['hostname', '-I'], capture_output=True, text=True)
            ip = ip_result.stdout.strip().split()[0]
            print(f"   \\\\{ip}\\PiCamera")
        except:
            print("   \\\\[Pi_IP_Address]\\PiCamera")
    else:
        print("❌ Some tests failed - check hardware connections")
EOF

chmod +x "$INSTALL_DIR/test_hardware.py"

echo ""
echo "✅ Installation complete!"
echo ""
echo "🧪 Test hardware: python3 $INSTALL_DIR/test_hardware.py"
echo "🔧 Next steps:"
echo "  1. sudo ./optimize_boot.sh"
echo "  2. sudo reboot"
echo "  3. Camera will start automatically"
echo "  4. Photos accessible from Windows file explorer"
echo ""
echo "📊 Service commands:"
echo "  Status: sudo systemctl status picamera"
echo "  Logs:   sudo journalctl -u picamera -f"
echo "  Start:  sudo systemctl start picamera"
echo "  Stop:   sudo systemctl stop picamera"
echo ""
echo "🌐 Network Share:"
echo "  Share name: PiCamera"
echo "  Access from Windows: \\\\[Pi_IP]\\PiCamera"
echo "  Photos organized by date automatically"