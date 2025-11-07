#!/usr/bin/env python3
"""
Network Share Server for Pi Zero Camera
Creates SMB/CIFS share accessible from Windows
Author: JMTDI
Date: 2025-10-25
"""

import os
import subprocess
import time
from datetime import datetime

class NetworkShareServer:
    def __init__(self):
        self.share_name = "PiCamera"
        self.share_path = "/home/pi/camera_share"
        self.config_file = "/etc/samba/smb.conf"
        self.username = "pi"
        
        print("🌐 Network Share Server initializing...")
    
    def setup_samba_share(self):
        """Set up Samba network share"""
        try:
            print("📂 Setting up Samba network share...")
            
            # Install Samba if not already installed
            subprocess.run(['sudo', 'apt', 'update'], check=True, capture_output=True)
            subprocess.run(['sudo', 'apt', 'install', '-y', 'samba', 'samba-common-bin'], 
                         check=True, capture_output=True)
            
            # Create share directory
            os.makedirs(self.share_path, exist_ok=True)
            os.makedirs(f"{self.share_path}/by_date", exist_ok=True)
            os.makedirs(f"{self.share_path}/all_photos", exist_ok=True)
            
            # Set proper permissions
            subprocess.run(['sudo', 'chown', '-R', 'pi:pi', self.share_path], check=True)
            subprocess.run(['sudo', 'chmod', '-R', '755', self.share_path], check=True)
            
            # Backup original Samba config
            subprocess.run(['sudo', 'cp', self.config_file, f"{self.config_file}.backup"], 
                         check=True)
            
            # Add share configuration to Samba
            share_config = f"""

# Pi Zero Camera Share - Added {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
[{self.share_name}]
    comment = Pi Zero Camera Photos
    path = {self.share_path}
    browseable = yes
    writeable = no
    only guest = no
    create mask = 0644
    directory mask = 0755
    public = yes
    guest ok = yes
    read only = yes
    force user = pi
    force group = pi
"""
            
            # Append share config to smb.conf
            with open('/tmp/share_config.txt', 'w') as f:
                f.write(share_config)
            
            subprocess.run(['sudo', 'bash', '-c', f'cat /tmp/share_config.txt >> {self.config_file}'], 
                         check=True)
            
            # Test Samba configuration
            result = subprocess.run(['sudo', 'testparm', '-s'], 
                                  capture_output=True, text=True, check=True)
            print("✅ Samba configuration validated")
            
            # Restart Samba services
            subprocess.run(['sudo', 'systemctl', 'restart', 'smbd'], check=True)
            subprocess.run(['sudo', 'systemctl', 'restart', 'nmbd'], check=True)
            
            # Enable Samba services to start on boot
            subprocess.run(['sudo', 'systemctl', 'enable', 'smbd'], check=True)
            subprocess.run(['sudo', 'systemctl', 'enable', 'nmbd'], check=True)
            
            print(f"✅ Samba share '{self.share_name}' created successfully")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Error setting up Samba share: {e}")
            return False
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            return False
    
    def get_share_info(self):
        """Get network share information"""
        try:
            # Get Pi's IP address
            ip_result = subprocess.run(['hostname', '-I'], 
                                     capture_output=True, text=True, check=True)
            ip_address = ip_result.stdout.strip().split()[0]
            
            # Get hostname
            hostname_result = subprocess.run(['hostname'], 
                                           capture_output=True, text=True, check=True)
            hostname = hostname_result.stdout.strip()
            
            share_info = {
                'share_name': self.share_name,
                'ip_address': ip_address,
                'hostname': hostname,
                'share_path': self.share_path,
                'windows_path': f"\\\\{ip_address}\\{self.share_name}",
                'windows_path_hostname': f"\\\\{hostname}\\{self.share_name}"
            }
            
            return share_info
            
        except Exception as e:
            print(f"Error getting share info: {e}")
            return None
    
    def create_access_instructions(self):
        """Create instructions file for accessing the share"""
        try:
            share_info = self.get_share_info()
            if not share_info:
                return False
            
            instructions = f"""Pi Zero Camera Network Share
==========================

Access your camera photos from Windows:

Method 1 - Using IP Address:
1. Open File Explorer (Windows + E)
2. In the address bar, type: {share_info['windows_path']}
3. Press Enter

Method 2 - Using Computer Name:
1. Open File Explorer (Windows + E)  
2. In the address bar, type: {share_info['windows_path_hostname']}
3. Press Enter

Method 3 - Network Discovery:
1. Open File Explorer
2. Click "Network" in the left sidebar
3. Look for "{share_info['hostname']}" 
4. Double-click it and then double-click "{self.share_name}"

Folder Structure:
- by_date/          Photos organized by date (YYYY-MM-DD folders)
  - 2025-10-25/     Today's photos
  - 2025-10-24/     Yesterday's photos
  - etc...
- all_photos/       All photos in chronological order

Camera Device: {share_info['hostname']}
Share Name: {self.share_name}
IP Address: {share_info['ip_address']}

Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Troubleshooting:
- Make sure both devices are on the same WiFi network
- If access fails, try using the IP address method
- Photos appear automatically as you take them
- No login required - read-only access
"""
            
            # Save instructions to share folder
            instructions_file = f"{self.share_path}/HOW_TO_ACCESS_FROM_WINDOWS.txt"
            with open(instructions_file, 'w') as f:
                f.write(instructions)
            
            os.chmod(instructions_file, 0o644)
            
            print(f"📋 Access instructions created: {instructions_file}")
            print(f"🌐 Share accessible at: {share_info['windows_path']}")
            
            return True
            
        except Exception as e:
            print(f"Error creating access instructions: {e}")
            return False
    
    def test_share_access(self):
        """Test if share is accessible"""
        try:
            # Test if Samba is running
            smbd_status = subprocess.run(['sudo', 'systemctl', 'is-active', 'smbd'], 
                                       capture_output=True, text=True)
            nmbd_status = subprocess.run(['sudo', 'systemctl', 'is-active', 'nmbd'], 
                                       capture_output=True, text=True)
            
            if smbd_status.stdout.strip() == 'active' and nmbd_status.stdout.strip() == 'active':
                print("✅ Samba services are running")
                
                # Test share listing
                shares_result = subprocess.run(['smbclient', '-L', 'localhost', '-N'], 
                                             capture_output=True, text=True)
                
                if self.share_name in shares_result.stdout:
                    print(f"✅ Share '{self.share_name}' is listed and accessible")
                    return True
                else:
                    print(f"❌ Share '{self.share_name}' not found in share listing")
                    return False
            else:
                print("❌ Samba services are not running")
                return False
                
        except Exception as e:
            print(f"Error testing share access: {e}")
            return False

def setup_network_share():
    """Main function to set up network share"""
    server = NetworkShareServer()
    
    print("🚀 Setting up Pi Zero Camera Network Share...")
    
    # Set up Samba share
    if server.setup_samba_share():
        print("✅ Samba share setup completed")
        
        # Create access instructions
        if server.create_access_instructions():
            print("✅ Access instructions created")
        
        # Test share access
        if server.test_share_access():
            print("✅ Share is working and accessible")
            
            share_info = server.get_share_info()
            if share_info:
                print("\n🎉 Setup Complete!")
                print("=" * 50)
                print(f"📂 Share Name: {share_info['share_name']}")
                print(f"🌐 IP Address: {share_info['ip_address']}")
                print(f"💻 Windows Path: {share_info['windows_path']}")
                print(f"📍 Local Path: {share_info['share_path']}")
                print("\n📋 To access from Windows:")
                print(f"   1. Open File Explorer")
                print(f"   2. Type in address bar: {share_info['windows_path']}")
                print(f"   3. Press Enter")
                print("\n📷 Photos will be organized by date automatically!")
                
        else:
            print("❌ Share setup completed but testing failed")
            print("   You may need to check firewall settings or restart the Pi")
    else:
        print("❌ Failed to set up Samba share")
        return False
    
    return True

if __name__ == "__main__":
    setup_network_share()