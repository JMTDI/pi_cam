#!/usr/bin/env python3
"""
Settings Application for Pi Zero Camera
Android-style settings with network share information
Author: JMTDI
Date: 2025-10-25
"""

import time
import os
import subprocess
from datetime import datetime

class SettingsApp:
    def __init__(self, display, navigation, wifi_manager):
        self.display = display
        self.navigation = navigation
        self.wifi_manager = wifi_manager
        
        # App state
        self.running = False
        self.current_menu = "main"
        self.selected_item = 0
        self.scroll_offset = 0
        self.should_exit_flag = False
        
        # Menu structure
        self.menu_structure = {
            "main": {
                "title": "Settings",
                "items": [
                    {"name": "WiFi", "icon": "📶", "action": "submenu", "submenu": "wifi"},
                    {"name": "Network Share", "icon": "📁", "action": "submenu", "submenu": "share"},
                    {"name": "Camera", "icon": "📷", "action": "submenu", "submenu": "camera"},
                    {"name": "Display", "icon": "🖥️", "action": "submenu", "submenu": "display"},
                    {"name": "System", "icon": "⚙️", "action": "submenu", "submenu": "system"},
                    {"name": "About", "icon": "ℹ️", "action": "submenu", "submenu": "about"},
                    {"name": "Exit", "icon": "🚪", "action": "exit"}
                ]
            },
            "wifi": {
                "title": "WiFi Settings",
                "items": [
                    {"name": "Scan Networks", "icon": "🔍", "action": "scan_wifi"},
                    {"name": "Current Network", "icon": "📡", "action": "show_current"},
                    {"name": "Back", "icon": "◄", "action": "back"}
                ]
            },
            "share": {
                "title": "Network Share",
                "items": [
                    {"name": "Share Status", "icon": "📊", "action": "show_share_status"},
                    {"name": "Access Info", "icon": "ℹ️", "action": "show_share_info"},
                    {"name": "Today's Photos", "icon": "📅", "action": "show_today_photos"},
                    {"name": "Total Photos", "icon": "📷", "action": "show_total_photos"},
                    {"name": "Back", "icon": "◄", "action": "back"}
                ]
            },
            "camera": {
                "title": "Camera Settings",
                "items": [
                    {"name": "Resolution", "icon": "📐", "action": "info", "value": "1640x1232"},
                    {"name": "Quality", "icon": "✨", "action": "info", "value": "85%"},
                    {"name": "Auto Upload", "icon": "⬆️", "action": "info", "value": "Enabled"},
                    {"name": "Back", "icon": "◄", "action": "back"}
                ]
            },
            "display": {
                "title": "Display Settings",
                "items": [
                    {"name": "Size", "icon": "📐", "action": "info", "value": "128x128"},
                    {"name": "UI Timeout", "icon": "⏰", "action": "info", "value": "5 sec"},
                    {"name": "Back", "icon": "◄", "action": "back"}
                ]
            },
            "system": {
                "title": "System Settings",
                "items": [
                    {"name": "Device Name", "icon": "📛", "action": "info", "value": "PiCamera"},
                    {"name": "Restart", "icon": "🔄", "action": "restart"},
                    {"name": "Shutdown", "icon": "⏻", "action": "shutdown"},
                    {"name": "Back", "icon": "◄", "action": "back"}
                ]
            },
            "about": {
                "title": "About",
                "items": [
                    {"name": "Version", "icon": "📋", "action": "show_info", "key": "version"},
                    {"name": "Device ID", "icon": "🆔", "action": "show_info", "key": "device_id"},
                    {"name": "Uptime", "icon": "⏱️", "action": "show_info", "key": "uptime"},
                    {"name": "Back", "icon": "◄", "action": "back"}
                ]
            }
        }
        
        # WiFi networks
        self.wifi_networks = []
        self.wifi_selected = 0
        
        print("⚙️ Settings app initialized")
    
    def on_launch(self):
        """Called when settings app is launched"""
        print("⚙️ Settings app launched")
        self.running = True
        self.current_menu = "main"
        self.selected_item = 0
        self.should_exit_flag = False
    
    def run_frame(self):
        """Update settings app (called every frame)"""
        if not self.running:
            return False
        
        # Show current menu
        if self.current_menu in self.menu_structure:
            self.show_menu(self.current_menu)
        elif self.current_menu == "wifi_scan":
            self.show_wifi_scan()
        elif self.current_menu == "wifi_networks":
            self.show_wifi_networks()
        
        self.display.update()
        return not self.should_exit_flag
    
    def handle_input(self, nav_input):
        """Handle settings app input"""
        if self.current_menu in self.menu_structure:
            self.handle_menu_input(nav_input)
        elif self.current_menu == "wifi_scan":
            self.handle_wifi_scan_input(nav_input)
        elif self.current_menu == "wifi_networks":
            self.handle_wifi_networks_input(nav_input)
    
    def handle_menu_input(self, nav_input):
        """Handle menu navigation input"""
        menu = self.menu_structure[self.current_menu]
        
        if nav_input == "UP":
            self.selected_item = max(0, self.selected_item - 1)
        elif nav_input == "DOWN":
            self.selected_item = min(len(menu["items"]) - 1, self.selected_item + 1)
        elif nav_input == "CENTER":
            self.execute_menu_action()
        elif nav_input == "LEFT":
            if self.current_menu != "main":
                self.go_back()
    
    def execute_menu_action(self):
        """Execute the action for the selected menu item"""
        menu = self.menu_structure[self.current_menu]
        item = menu["items"][self.selected_item]
        action = item["action"]
        
        if action == "submenu":
            self.current_menu = item["submenu"]
            self.selected_item = 0
        elif action == "back":
            self.go_back()
        elif action == "exit":
            self.should_exit_flag = True
        elif action == "scan_wifi":
            self.scan_wifi_networks()
        elif action == "show_current":
            self.show_current_network()
        elif action == "show_share_status":
            self.show_share_status()
        elif action == "show_share_info":
            self.show_share_info()
        elif action == "show_today_photos":
            self.show_today_photos()
        elif action == "show_total_photos":
            self.show_total_photos()
        elif action == "restart":
            self.restart_system()
        elif action == "shutdown":
            self.shutdown_system()
        elif action == "show_info":
            self.show_system_info(item["key"])
    
    def show_menu(self, menu_name):
        """Display menu interface"""
        menu = self.menu_structure[menu_name]
        self.display.clear((20, 20, 40))
        
        # Title bar
        self.display.draw_rectangle(0, 0, 128, 25, color=(25, 118, 210))
        title = menu["title"]
        if menu_name != "main":
            title = "◄ " + title
        self.display.draw_text(title, 5, 7, color=(255, 255, 255), size=12)
        
        # Menu items
        visible_items = 4
        start_item = max(0, min(self.selected_item - visible_items + 1, 
                               len(menu["items"]) - visible_items))
        
        y = 30
        for i in range(start_item, min(len(menu["items"]), start_item + visible_items)):
            item = menu["items"][i]
            
            # Highlight selected item
            if i == self.selected_item:
                self.display.draw_rectangle(2, y-2, 124, 20, color=(50, 150, 255))
            
            # Icon and text
            self.display.draw_text(item["icon"], 8, y, color=(255, 255, 255), size=12)
            self.display.draw_text(item["name"], 28, y, color=(255, 255, 255), size=10)
            
            # Show value if present
            if "value" in item:
                value = str(item["value"])
                self.display.draw_text(value, 80, y, color=(200, 200, 200), size=8)
            
            # Arrow for submenus
            if item["action"] in ["submenu", "info"]:
                self.display.draw_text("►", 115, y, color=(150, 150, 150), size=10)
            
            y += 22
        
        # Navigation hint
        self.display.draw_text("▲▼ Navigate  ● Select", 5, 115, color=(100, 100, 100), size=8)
    
    def scan_wifi_networks(self):
        """Scan for WiFi networks"""
        self.current_menu = "wifi_scan"
        self.wifi_networks = []
        
        # Start scan in background
        import threading
        scan_thread = threading.Thread(target=self._perform_wifi_scan, daemon=True)
        scan_thread.start()
    
    def _perform_wifi_scan(self):
        """Perform WiFi scan in background"""
        try:
            self.wifi_networks = self.wifi_manager.scan_networks()
            if self.wifi_networks:
                self.current_menu = "wifi_networks"
                self.wifi_selected = 0
            else:
                time.sleep(2)  # Show "No networks" message
                self.current_menu = "wifi"
        except Exception as e:
            print(f"WiFi scan error: {e}")
            time.sleep(2)
            self.current_menu = "wifi"
    
    def show_wifi_scan(self):
        """Show WiFi scanning screen"""
        self.display.clear((20, 20, 40))
        
        self.display.draw_rectangle(0, 0, 128, 25, color=(25, 118, 210))
        self.display.draw_text("◄ Scanning WiFi", 5, 7, color=(255, 255, 255), size=12)
        
        # Scanning animation
        dots = "." * ((int(time.time() * 3) % 4))
        self.display.draw_text(f"Scanning{dots}    ", 30, 60, color=(255, 255, 255), size=12)
        
        # Cancel hint
        self.display.draw_text("◄ Cancel", 5, 115, color=(100, 100, 100), size=8)
    
    def show_wifi_networks(self):
        """Show available WiFi networks"""
        self.display.clear((20, 20, 40))
        
        self.display.draw_rectangle(0, 0, 128, 25, color=(25, 118, 210))
        self.display.draw_text("◄ WiFi Networks", 5, 7, color=(255, 255, 255), size=12)
        
        if not self.wifi_networks:
            self.display.draw_text("No networks found", 15, 60, color=(255, 100, 100), size=10)
            return
        
        # Show networks
        y = 35
        visible_networks = 3
        start_net = max(0, min(self.wifi_selected - visible_networks + 1,
                              len(self.wifi_networks) - visible_networks))
        
        for i in range(start_net, min(len(self.wifi_networks), start_net + visible_networks)):
            network = self.wifi_networks[i]
            
            if i == self.wifi_selected:
                self.display.draw_rectangle(2, y-2, 124, 18, color=(50, 150, 255))
            
            # Signal strength
            self.display.draw_text("📶", 8, y, color=(255, 255, 255), size=10)
            
            # Network name
            ssid = network.get('ssid', 'Unknown')[:15]
            self.display.draw_text(ssid, 25, y, color=(255, 255, 255), size=9)
            
            # Security indicator
            if network.get('encrypted', True):
                self.display.draw_text("🔒", 110, y, color=(255, 255, 0), size=8)
            
            y += 20
        
        self.display.draw_text("◄ Back  ● Connect", 5, 115, color=(100, 100, 100), size=8)
    
    def handle_wifi_scan_input(self, nav_input):
        """Handle WiFi scan input"""
        if nav_input == "LEFT":
            self.current_menu = "wifi"
    
    def handle_wifi_networks_input(self, nav_input):
        """Handle WiFi networks input"""
        if nav_input == "UP":
            self.wifi_selected = max(0, self.wifi_selected - 1)
        elif nav_input == "DOWN":
            self.wifi_selected = min(len(self.wifi_networks) - 1, self.wifi_selected + 1)
        elif nav_input == "LEFT":
            self.current_menu = "wifi"
        elif nav_input == "CENTER":
            self.connect_to_wifi()
    
    def connect_to_wifi(self):
        """Connect to selected WiFi network"""
        if self.wifi_networks and self.wifi_selected < len(self.wifi_networks):
            network = self.wifi_networks[self.wifi_selected]
            ssid = network.get('ssid')
            
            # Show connecting message
            self.display.clear()
            self.display.draw_text("Connecting...", 25, 55, color=(255, 255, 0), size=12)
            self.display.draw_text(ssid[:15], 15, 75, color=(200, 200, 200), size=10)
            self.display.update()
            
            # Attempt connection (simplified - would need password input for secured networks)
            success = self.wifi_manager.connect_to_network(ssid, "")
            
            # Show result
            if success:
                self.display.clear()
                self.display.draw_text("Connected!", 30, 55, color=(0, 255, 0), size=12)
                self.display.update()
                time.sleep(2)
            else:
                self.display.clear()
                self.display.draw_text("Failed to connect", 15, 55, color=(255, 0, 0), size=10)
                self.display.update()
                time.sleep(2)
            
            self.current_menu = "wifi"
    
    def show_current_network(self):
        """Show current WiFi network info"""
        current = self.wifi_manager.get_current_network()
        ip = self.wifi_manager.get_ip_address()
        
        self.display.clear()
        self.display.draw_text("Current Network", 15, 35, color=(255, 255, 255), size=12)
        
        if current:
            self.display.draw_text(current[:15], 15, 55, color=(0, 255, 0), size=10)
            if ip:
                self.display.draw_text(ip, 15, 70, color=(200, 200, 200), size=8)
        else:
            self.display.draw_text("Not connected", 15, 55, color=(255, 100, 100), size=10)
        
        self.display.draw_text("Press any key", 15, 100, color=(100, 100, 100), size=8)
        self.display.update()
        
        # Wait for input
        self.navigation.wait_for_input(timeout=5)
    
    def show_share_status(self):
        """Show network share status"""
        self.display.clear()
        self.display.draw_text("Network Share", 20, 30, color=(255, 255, 255), size=12)
        
        # Check if share is accessible
        share_path = "/home/pi/camera_share"
        if os.path.exists(share_path):
            self.display.draw_text("Status: Active", 15, 50, color=(0, 255, 0), size=10)
            
            # Get today's photos count
            today = datetime.now().strftime('%Y-%m-%d')
            today_folder = f"{share_path}/by_date/{today}"
            today_count = 0
            if os.path.exists(today_folder):
                photos = [f for f in os.listdir(today_folder) 
                         if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
                today_count = len(photos)
            
            self.display.draw_text(f"Today: {today_count}", 15, 65, color=(255, 255, 255), size=10)
        else:
            self.display.draw_text("Status: Error", 15, 50, color=(255, 0, 0), size=10)
        
        # Show IP for access
        ip = self.wifi_manager.get_ip_address()
        if ip:
            self.display.draw_text(f"Access: \\\\{ip}", 15, 80, color=(200, 200, 200), size=8)
        
        self.display.draw_text("Press any key", 15, 105, color=(100, 100, 100), size=8)
        self.display.update()
        
        self.navigation.wait_for_input(timeout=5)
    
    def show_share_info(self):
        """Show network share access information"""
        self.display.clear()
        self.display.draw_text("Access Info", 30, 25, color=(255, 255, 255), size=12)
        
        ip = self.wifi_manager.get_ip_address()
        if ip:
            self.display.draw_text("From Windows:", 15, 45, color=(255, 255, 255), size=10)
            self.display.draw_text("File Explorer →", 15, 60, color=(200, 200, 200), size=9)
            self.display.draw_text(f"\\\\{ip}\\PiCamera", 15, 75, color=(0, 255, 255), size=8)
        else:
            self.display.draw_text("Connect to WiFi", 15, 50, color=(255, 100, 100), size=10)
            self.display.draw_text("to access share", 15, 65, color=(255, 100, 100), size=10)
        
        self.display.draw_text("Press any key", 15, 105, color=(100, 100, 100), size=8)
        self.display.update()
        
        self.navigation.wait_for_input(timeout=8)
    
    def show_today_photos(self):
        """Show today's photo count"""
        today = datetime.now().strftime('%Y-%m-%d')
        share_path = "/home/pi/camera_share"
        today_folder = f"{share_path}/by_date/{today}"
        
        self.display.clear()
        self.display.draw_text("Today's Photos", 20, 35, color=(255, 255, 255), size=12)
        
        if os.path.exists(today_folder):
            photos = [f for f in os.listdir(today_folder) 
                     if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
            count = len(photos)
            self.display.draw_text(f"Count: {count}", 15, 55, color=(0, 255, 0), size=12)
            self.display.draw_text(f"Date: {today}", 15, 75, color=(200, 200, 200), size=9)
        else:
            self.display.draw_text("No photos today", 15, 55, color=(255, 100, 100), size=10)
        
        self.display.draw_text("Press any key", 15, 100, color=(100, 100, 100), size=8)
        self.display.update()
        
        self.navigation.wait_for_input(timeout=5)
    
    def show_total_photos(self):
        """Show total photo count in share"""
        share_path = "/home/pi/camera_share"
        all_folder = f"{share_path}/all_photos"
        
        self.display.clear()
        self.display.draw_text("Total Photos", 25, 35, color=(255, 255, 255), size=12)
        
        if os.path.exists(all_folder):
            photos = [f for f in os.listdir(all_folder) 
                     if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
            count = len(photos)
            self.display.draw_text(f"Total: {count}", 15, 55, color=(0, 255, 0), size=12)
            
            # Show space used (approximate)
            try:
                total_size = sum(os.path.getsize(f"{all_folder}/{f}") for f in photos)
                size_mb = total_size / (1024 * 1024)
                self.display.draw_text(f"Size: {size_mb:.1f}MB", 15, 75, color=(200, 200, 200), size=9)
            except:
                pass
        else:
            self.display.draw_text("No photos yet", 20, 55, color=(255, 100, 100), size=10)
        
        self.display.draw_text("Press any key", 15, 100, color=(100, 100, 100), size=8)
        self.display.update()
        
        self.navigation.wait_for_input(timeout=5)
    
    def show_system_info(self, info_type):
        """Show system information"""
        self.display.clear()
        
        if info_type == "version":
            self.display.draw_text("PiCamera v1.0", 15, 45, color=(255, 255, 255), size=12)
            self.display.draw_text("Built: 2025-10-25", 15, 65, color=(200, 200, 200), size=9)
        elif info_type == "device_id":
            self.display.draw_text("Device ID:", 15, 45, color=(255, 255, 255), size=10)
            self.display.draw_text("picamera-001", 15, 60, color=(200, 200, 200), size=9)
        elif info_type == "uptime":
            uptime = self.get_system_uptime()
            self.display.draw_text("Uptime:", 15, 45, color=(255, 255, 255), size=10)
            self.display.draw_text(uptime, 15, 60, color=(200, 200, 200), size=9)
        
        self.display.draw_text("Press any key", 15, 100, color=(100, 100, 100), size=8)
        self.display.update()
        
        # Wait for input
        self.navigation.wait_for_input(timeout=5)
    
    def restart_system(self):
        """Restart the system"""
        self.display.clear()
        self.display.draw_text("Restarting...", 25, 60, color=(255, 255, 0), size=12)
        self.display.update()
        time.sleep(2)
        
        try:
            subprocess.run(['sudo', 'reboot'], check=True)
        except Exception as e:
            print(f"Restart failed: {e}")
    
    def shutdown_system(self):
        """Shutdown the system"""
        self.display.clear()
        self.display.draw_text("Shutting down...", 15, 60, color=(255, 100, 100), size=12)
        self.display.update()
        time.sleep(2)
        
        try:
            subprocess.run(['sudo', 'shutdown', '-h', 'now'], check=True)
        except Exception as e:
            print(f"Shutdown failed: {e}")
    
    def go_back(self):
        """Go back to previous menu"""
        if self.current_menu == "main":
            self.should_exit_flag = True
        else:
            self.current_menu = "main"
            self.selected_item = 0
    
    def should_exit(self):
        """Check if app should exit"""
        return self.should_exit_flag
    
    def get_system_uptime(self):
        """Get system uptime"""
        try:
            with open('/proc/uptime', 'r') as f:
                uptime_seconds = float(f.readline().split()[0])
                hours = int(uptime_seconds // 3600)
                minutes = int((uptime_seconds % 3600) // 60)
                return f"{hours}h {minutes}m"
        except:
            return "Unknown"
    
    def cleanup(self):
        """Clean up settings app"""
        print("🧹 Cleaning up settings app...")
        self.running = False