#!/usr/bin/env python3
"""
Pi Zero Instant Camera - Fast Boot Launcher
Android-style interface for ST7735S display
Author: JMTDI
Date: 2025-10-25
"""

import os
import sys
import time
import signal
import threading
from datetime import datetime

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from camera_app import CameraApp
    from settings_app import SettingsApp
    from display_driver import ST7735Display
    from navigation import NavigationController
    from config import Config
    from wifi_manager import WiFiManager
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure all files are in the same directory")
    sys.exit(1)

class PiCameraLauncher:
    def __init__(self):
        print("🚀 Pi Zero Camera Launcher starting...")
        start_time = time.time()
        
        self.config = Config()
        self.running = True
        
        # Initialize display first for immediate feedback
        print("📺 Initializing ST7735S display...")
        self.display = ST7735Display()
        self.display.init_display()
        self.show_boot_splash()
        
        # Initialize navigation
        print("🎮 Initializing navigation...")
        self.navigation = NavigationController()
        
        # Initialize WiFi manager
        print("📶 Initializing WiFi...")
        self.wifi_manager = WiFiManager()
        
        # Initialize applications
        print("📷 Initializing camera app...")
        self.camera_app = CameraApp(self.display, self.navigation, self.wifi_manager)
        
        print("⚙️ Initializing settings app...")
        self.settings_app = SettingsApp(self.display, self.navigation, self.wifi_manager)
        
        # Launcher state
        self.current_screen = "launcher"
        self.selected_app = 0
        self.last_activity = time.time()
        
        # App configuration
        self.apps = [
            {
                "name": "Camera", 
                "icon": "📷", 
                "app": self.camera_app,
                "color": (100, 200, 255)
            },
            {
                "name": "Settings", 
                "icon": "⚙️", 
                "app": self.settings_app,
                "color": (255, 150, 50)
            }
        ]
        
        boot_time = time.time() - start_time
        print(f"✅ Boot complete in {boot_time:.1f} seconds")
        
        # Setup signal handlers for clean shutdown
        signal.signal(signal.SIGTERM, self.signal_handler)
        signal.signal(signal.SIGINT, self.signal_handler)
        
        # Start background tasks
        self.start_background_tasks()
    
    def show_boot_splash(self):
        """Show immediate boot feedback on display"""
        self.display.clear((0, 0, 50))  # Dark blue background
        
        # Logo area
        self.display.draw_rectangle(20, 30, 88, 60, color=(30, 30, 80), outline=(100, 150, 255))
        
        # Title
        self.display.draw_text("PiCamera", 28, 45, color=(255, 255, 255), size=16)
        self.display.draw_text("v1.0", 50, 65, color=(150, 150, 255), size=10)
        
        # Loading animation
        for i in range(4):
            loading_text = "Starting" + "." * (i % 4)
            self.display.draw_text(f"{loading_text}    ", 30, 100, color=(255, 255, 0), size=10)
            self.display.update()
            time.sleep(0.3)
    
    def start_background_tasks(self):
        """Start background threads for system tasks"""
        # Background thread for system monitoring
        monitor_thread = threading.Thread(target=self.system_monitor, daemon=True)
        monitor_thread.start()
    
    def system_monitor(self):
        """Background system monitoring"""
        while self.running:
            try:
                # Check for auto-sleep
                if time.time() - self.last_activity > self.config.AUTO_SLEEP_TIME:
                    if self.current_screen == "launcher":
                        self.show_sleep_screen()
                
                time.sleep(10)  # Check every 10 seconds
            except Exception as e:
                print(f"System monitor error: {e}")
                time.sleep(30)
    
    def run(self):
        """Main application loop"""
        print("🎯 Launcher ready - showing main screen")
        frame_count = 0
        
        while self.running:
            try:
                frame_start = time.time()
                
                # Handle navigation input
                nav_input = self.navigation.get_input()
                if nav_input:
                    self.last_activity = time.time()
                    self.handle_navigation(nav_input)
                
                # Update current screen
                if self.current_screen == "launcher":
                    self.show_launcher()
                elif self.current_screen == "camera":
                    if not self.camera_app.run_frame():
                        self.current_screen = "launcher"
                elif self.current_screen == "settings":
                    if not self.settings_app.run_frame():
                        self.current_screen = "launcher"
                elif self.current_screen == "sleep":
                    self.handle_sleep_mode()
                
                # Frame rate control (20 FPS)
                frame_time = time.time() - frame_start
                sleep_time = max(0, 0.05 - frame_time)
                time.sleep(sleep_time)
                
                frame_count += 1
                if frame_count % 200 == 0:  # Debug every 10 seconds
                    fps = 1/(frame_time + sleep_time) if (frame_time + sleep_time) > 0 else 0
                    print(f"FPS: {fps:.1f}")
                
            except Exception as e:
                print(f"❌ Error in main loop: {e}")
                time.sleep(1)
    
    def handle_navigation(self, nav_input):
        """Handle D-pad navigation input"""
        if self.current_screen == "launcher":
            self.handle_launcher_navigation(nav_input)
        elif self.current_screen == "camera":
            self.camera_app.handle_input(nav_input)
        elif self.current_screen == "settings":
            self.settings_app.handle_input(nav_input)
        elif self.current_screen == "sleep":
            if nav_input:  # Any button wakes up
                self.current_screen = "launcher"
    
    def handle_launcher_navigation(self, nav_input):
        """Handle launcher D-pad navigation"""
        if nav_input == "LEFT":
            self.selected_app = max(0, self.selected_app - 1)
        elif nav_input == "RIGHT":
            self.selected_app = min(len(self.apps) - 1, self.selected_app + 1)
        elif nav_input == "CENTER":
            self.launch_selected_app()
        elif nav_input == "UP":
            # Quick actions menu
            self.show_quick_actions()
        elif nav_input == "DOWN":
            # System info
            self.show_system_info()
    
    def launch_selected_app(self):
        """Launch the currently selected app"""
        selected = self.apps[self.selected_app]
        print(f"🚀 Launching {selected['name']} app")
        
        # App transition effect
        self.show_app_transition(selected)
        
        if selected['name'] == "Camera":
            self.current_screen = "camera"
            self.camera_app.on_launch()
        elif selected['name'] == "Settings":
            self.current_screen = "settings"
            self.settings_app.on_launch()
    
    def show_app_transition(self, app):
        """Show app launch transition"""
        self.display.clear()
        
        # Expanding circle effect
        for radius in range(5, 65, 8):
            self.display.clear()
            self.display.draw_circle(64, 64, radius, color=app['color'])
            self.display.draw_text(app['icon'], 55, 55, color=(255, 255, 255), size=16)
            self.display.update()
            time.sleep(0.02)
    
    def show_launcher(self):
        """Display Android-style launcher home screen"""
        self.display.clear((20, 20, 40))  # Dark background
        
        # Status bar
        self.draw_status_bar()
        
        # App title
        self.display.draw_text("PiCamera", 25, 25, color=(255, 255, 255), size=16)
        
        # Current time larger
        current_time = datetime.now().strftime("%H:%M")
        self.display.draw_text(current_time, 35, 45, color=(200, 200, 255), size=12)
        
        # App icons in a grid
        self.draw_app_icons()
        
        # Navigation hints
        self.display.draw_text("◄ ► Select", 5, 108, color=(120, 120, 120), size=8)
        self.display.draw_text("● Open", 75, 108, color=(120, 120, 120), size=8)
        
        self.display.update()
    
    def draw_status_bar(self):
        """Draw status bar with system info"""
        # Status bar background
        self.display.draw_rectangle(0, 0, 128, 18, color=(10, 10, 30))
        
        # Time (left)
        current_time = datetime.now().strftime("%H:%M")
        self.display.draw_text(current_time, 3, 4, color=(255, 255, 255), size=10)
        
        # WiFi status
        if self.wifi_manager.is_connected():
            self.display.draw_text("📶", 85, 3, color=(0, 255, 0), size=8)
        else:
            self.display.draw_text("📶", 85, 3, color=(100, 100, 100), size=8)
        
        # Battery indicator (right)
        battery_level = self.get_battery_level()
        battery_color = (0, 255, 0) if battery_level > 30 else (255, 100, 0) if battery_level > 15 else (255, 0, 0)
        self.display.draw_text(f"🔋{battery_level}%", 95, 3, color=battery_color, size=8)
    
    def draw_app_icons(self):
        """Draw app icons with selection highlighting"""
        icon_size = 45
        icon_spacing = 64
        start_x = 16
        icon_y = 65
        
        for i, app in enumerate(self.apps):
            x = start_x + (i * icon_spacing)
            
            # Selection highlight with glow effect
            if i == self.selected_app:
                # Outer glow
                self.display.draw_rectangle(x-8, icon_y-8, icon_size+16, icon_size+8, 
                                          color=(50, 100, 200))
                # Inner highlight
                self.display.draw_rectangle(x-5, icon_y-5, icon_size+10, icon_size+2, 
                                          color=app['color'], outline=(255, 255, 255))
            else:
                # Normal border
                self.display.draw_rectangle(x-2, icon_y-2, icon_size+4, icon_size-2, 
                                          color=(60, 60, 80), outline=(100, 100, 120))
            
            # App icon
            self.display.draw_text(app["icon"], x+8, icon_y+5, color=(255, 255, 255), size=24)
            
            # App name
            name_color = (255, 255, 255) if i == self.selected_app else (180, 180, 180)
            self.display.draw_text(app["name"], x-2, icon_y+35, color=name_color, size=9)
    
    def show_quick_actions(self):
        """Show quick actions overlay"""
        # Semi-transparent overlay
        self.display.draw_rectangle(10, 30, 108, 70, color=(0, 0, 0), outline=(100, 150, 255))
        
        self.display.draw_text("Quick Actions", 25, 40, color=(255, 255, 255), size=12)
        self.display.draw_text("📷 Take Photo", 15, 55, color=(200, 200, 200), size=10)
        self.display.draw_text("📶 WiFi Toggle", 15, 70, color=(200, 200, 200), size=10)
        self.display.draw_text("🔄 Restart", 15, 85, color=(200, 200, 200), size=10)
        
        self.display.update()
        time.sleep(2)
    
    def show_system_info(self):
        """Show system information overlay"""
        # Get system stats
        uptime = self.get_system_uptime()
        memory = self.get_memory_usage()
        
        # Semi-transparent overlay
        self.display.draw_rectangle(10, 25, 108, 80, color=(0, 0, 0), outline=(100, 150, 255))
        
        self.display.draw_text("System Info", 30, 35, color=(255, 255, 255), size=12)
        self.display.draw_text(f"Uptime: {uptime}", 15, 50, color=(200, 200, 200), size=8)
        self.display.draw_text(f"Memory: {memory}%", 15, 62, color=(200, 200, 200), size=8)
        self.display.draw_text(f"Photos: {self.camera_app.get_photo_count()}", 15, 74, color=(200, 200, 200), size=8)
        
        network = self.wifi_manager.get_current_network() or 'None'
        self.display.draw_text(f"WiFi: {network[:8]}", 15, 86, color=(200, 200, 200), size=8)
        
        self.display.update()
        time.sleep(3)
    
    def show_sleep_screen(self):
        """Show sleep/screensaver mode"""
        self.current_screen = "sleep"
    
    def handle_sleep_mode(self):
        """Handle sleep mode display"""
        self.display.clear((0, 0, 0))
        
        # Dim clock display
        current_time = datetime.now().strftime("%H:%M:%S")
        self.display.draw_text(current_time, 25, 55, color=(50, 50, 100), size=16)
        
        # Low power indicator
        self.display.draw_text("Press any button", 15, 85, color=(30, 30, 60), size=8)
        
        self.display.update()
    
    def get_battery_level(self):
        """Get battery level (placeholder - implement with actual hardware)"""
        # TODO: Implement actual battery monitoring
        return 85
    
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
    
    def get_memory_usage(self):
        """Get memory usage percentage"""
        try:
            with open('/proc/meminfo', 'r') as f:
                lines = f.readlines()
                total = int([line for line in lines if 'MemTotal' in line][0].split()[1])
                available = int([line for line in lines if 'MemAvailable' in line][0].split()[1])
                used_percent = int((total - available) / total * 100)
                return used_percent
        except:
            return 0
    
    def signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        print(f"\n📴 Received signal {signum}, shutting down...")
        self.shutdown()
    
    def shutdown(self):
        """Clean shutdown sequence"""
        print("🛑 Shutting down Pi Camera Launcher...")
        
        # Show shutdown screen
        self.display.clear((50, 0, 0))
        self.display.draw_text("Shutting down...", 20, 55, color=(255, 200, 200), size=12)
        self.display.update()
        time.sleep(1)
        
        # Clean up resources
        try:
            self.camera_app.cleanup()
            self.settings_app.cleanup()
            self.display.cleanup()
            self.navigation.cleanup()
        except Exception as e:
            print(f"Cleanup error: {e}")
        
        self.running = False
        print("✅ Shutdown complete")

def main():
    """Main entry point with comprehensive error handling"""
    try:
        # Ensure we're in the right directory
        script_dir = os.path.dirname(os.path.abspath(__file__))
        os.chdir(script_dir)
        print(f"📂 Working directory: {script_dir}")
        
        # Create and run launcher
        launcher = PiCameraLauncher()
        launcher.run()
        
    except KeyboardInterrupt:
        print("\n⌨️ Keyboard interrupt received")
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("🏁 Pi Camera Launcher stopped")

if __name__ == "__main__":
    main()