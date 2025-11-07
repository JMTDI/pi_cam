#!/usr/bin/env python3
"""
WiFi Manager for Pi Zero Camera
Handle WiFi connections, scanning, and network management
Author: JMTDI  
Date: 2025-10-25
"""

import subprocess
import time
import json
import os
import re
import threading
from datetime import datetime

class WiFiManager:
    def __init__(self):
        self.config_file = "/etc/wpa_supplicant/wpa_supplicant.conf"
        self.known_networks = []
        self.current_networks = []
        self.connection_status = False
        self.current_network = None
        self.ip_address = None
        
        # Background monitoring
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._connection_monitor, daemon=True)
        self.monitor_thread.start()
        
        print("📶 WiFi Manager initialized")
    
    def is_connected(self):
        """Check if WiFi is connected"""
        return self.connection_status
    
    def get_current_network(self):
        """Get currently connected network name"""
        return self.current_network
    
    def get_ip_address(self):
        """Get current IP address"""
        return self.ip_address
    
    def _connection_monitor(self):
        """Background thread to monitor WiFi connection"""
        while self.monitoring:
            try:
                # Check connection status
                result = subprocess.run(['iwgetid'], capture_output=True, text=True, timeout=5)
                
                if result.returncode == 0 and result.stdout.strip():
                    # Connected
                    self.connection_status = True
                    
                    # Get network name
                    network_result = subprocess.run(['iwgetid', '-r'], capture_output=True, text=True, timeout=5)
                    if network_result.returncode == 0:
                        self.current_network = network_result.stdout.strip()
                    
                    # Get IP address
                    ip_result = subprocess.run(['hostname', '-I'], capture_output=True, text=True, timeout=5)
                    if ip_result.returncode == 0:
                        ips = ip_result.stdout.strip().split()
                        self.ip_address = ips[0] if ips else None
                else:
                    # Not connected
                    self.connection_status = False
                    self.current_network = None
                    self.ip_address = None
                
                time.sleep(10)  # Check every 10 seconds
                
            except Exception as e:
                print(f"WiFi monitor error: {e}")
                time.sleep(30)  # Wait longer on error
    
    def scan_networks(self):
        """Scan for available WiFi networks"""
        try:
            print("📡 Scanning for WiFi networks...")
            
            # Trigger scan
            subprocess.run(['sudo', 'iwlist', 'wlan0', 'scan', 'essid'], 
                         capture_output=True, text=True, timeout=30)
            time.sleep(2)
            
            # Get scan results
            result = subprocess.run(['sudo', 'iwlist', 'wlan0', 'scan'], 
                                  capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                networks = self._parse_scan_results(result.stdout)
                self.current_networks = networks
                print(f"📶 Found {len(networks)} networks")
                return networks
            else:
                print(f"WiFi scan failed: {result.stderr}")
                
        except subprocess.TimeoutExpired:
            print("WiFi scan timeout")
        except Exception as e:
            print(f"WiFi scan error: {e}")
        
        return []
    
    def _parse_scan_results(self, scan_output):
        """Parse iwlist scan output into network list"""
        networks = []
        current_network = {}
        
        for line in scan_output.split('\n'):
            line = line.strip()
            
            # New cell (network)
            if 'Cell' in line and 'Address:' in line:
                if current_network and 'ssid' in current_network:
                    networks.append(current_network)
                current_network = {}
                
                # Extract MAC address
                mac_match = re.search(r'Address: ([a-fA-F0-9:]{17})', line)
                if mac_match:
                    current_network['mac'] = mac_match.group(1)
            
            # ESSID (network name)
            elif 'ESSID:' in line:
                essid_match = re.search(r'ESSID:"([^"]*)"', line)
                if essid_match:
                    essid = essid_match.group(1)
                    if essid:  # Skip hidden networks
                        current_network['ssid'] = essid
            
            # Signal quality
            elif 'Quality=' in line:
                quality_match = re.search(r'Quality=(\d+)/(\d+)', line)
                if quality_match:
                    quality = int(quality_match.group(1))
                    max_quality = int(quality_match.group(2))
                    current_network['quality'] = int((quality / max_quality) * 100)
                
                # Signal level
                signal_match = re.search(r'Signal level=(-?\d+)', line)
                if signal_match:
                    current_network['signal_level'] = int(signal_match.group(1))
            
            # Encryption
            elif 'Encryption key:' in line:
                if 'on' in line.lower():
                    current_network['encrypted'] = True
                else:
                    current_network['encrypted'] = False
        
        # Add last network
        if current_network and 'ssid' in current_network:
            networks.append(current_network)
        
        # Sort by signal strength
        networks.sort(key=lambda x: x.get('quality', 0), reverse=True)
        
        return networks
    
    def connect_to_network(self, ssid, password=None, save=True):
        """Connect to a WiFi network"""
        try:
            print(f"📶 Connecting to {ssid}...")
            
            # Add network using wpa_cli
            commands = [
                ['sudo', 'wpa_cli', '-i', 'wlan0', 'remove_network', 'all'],
                ['sudo', 'wpa_cli', '-i', 'wlan0', 'add_network'],
                ['sudo', 'wpa_cli', '-i', 'wlan0', 'set_network', '0', 'ssid', f'"{ssid}"']
            ]
            
            if password:
                commands.append(['sudo', 'wpa_cli', '-i', 'wlan0', 'set_network', '0', 'psk', f'"{password}"'])
            else:
                commands.append(['sudo', 'wpa_cli', '-i', 'wlan0', 'set_network', '0', 'key_mgmt', 'NONE'])
            
            commands.extend([
                ['sudo', 'wpa_cli', '-i', 'wlan0', 'enable_network', '0'],
                ['sudo', 'wpa_cli', '-i', 'wlan0', 'select_network', '0']
            ])
            
            # Execute commands
            for cmd in commands:
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
                if result.returncode != 0:
                    print(f"Command failed: {' '.join(cmd)}")
                    print(f"Error: {result.stderr}")
            
            # Wait for connection
            print("⏳ Waiting for connection...")
            for attempt in range(30):  # Wait up to 30 seconds
                time.sleep(1)
                if self.is_connected() and self.get_current_network() == ssid:
                    print(f"✅ Connected to {ssid}")
                    
                    # Save configuration if requested
                    if save:
                        subprocess.run(['sudo', 'wpa_cli', '-i', 'wlan0', 'save_config'], 
                                     capture_output=True, timeout=10)
                        print("💾 Network configuration saved")
                    
                    return True
            
            print(f"❌ Failed to connect to {ssid}")
            return False
            
        except Exception as e:
            print(f"❌ Connection error: {e}")
            return False
    
    def cleanup(self):
        """Clean up WiFi manager"""
        print("🧹 Cleaning up WiFi manager...")
        self.monitoring = False
        
        if self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=2)
        
        print("✅ WiFi manager cleanup complete")