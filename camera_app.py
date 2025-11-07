#!/usr/bin/env python3
"""
Camera Application for Pi Zero
Full-screen camera with live preview and photo capture
Author: JMTDI
Date: 2025-10-25
"""

import os
import time
import threading
from datetime import datetime
from PIL import Image
try:
    from picamera import PiCamera
    CAMERA_AVAILABLE = True
except ImportError:
    print("⚠️ PiCamera not available - using mock camera for testing")
    CAMERA_AVAILABLE = False

from photo_uploader import PhotoUploader
from config import Config

class MockCamera:
    """Mock camera for testing without hardware"""
    def __init__(self):
        self.resolution = (640, 480)
        self.framerate = 24
        self.closed = False
        self.exposure_mode = 'auto'
        self.awb_mode = 'auto'
        self.meter_mode = 'average'
        self.image_effect = 'none'
    
    def capture(self, filepath, **kwargs):
        """Create a test image"""
        if 'resize' in kwargs:
            size = kwargs['resize']
        else:
            size = (640, 480)
        
        img = Image.new('RGB', size, color=(100, 150, 200))
        
        # Add some test pattern
        from PIL import ImageDraw
        draw = ImageDraw.Draw(img)
        draw.rectangle([10, 10, size[0]-10, size[1]-10], outline=(255, 255, 255))
        draw.text((20, 20), "TEST CAMERA", fill=(255, 255, 255))
        draw.text((20, 40), datetime.now().strftime("%H:%M:%S"), fill=(255, 255, 0))
        
        img.save(filepath)
        print(f"📷 Mock photo saved: {filepath}")
    
    def close(self):
        self.closed = True

class CameraApp:
    def __init__(self, display, navigation, wifi_manager):
        self.display = display
        self.navigation = navigation
        self.wifi_manager = wifi_manager
        self.config = Config()
        
        # Initialize photo uploader
        self.uploader = PhotoUploader(wifi_manager)
        
        # Camera setup
        self.camera = None
        self.camera_ready = False
        self.preview_active = False
        
        # App state
        self.running = False
        self.show_ui = True
        self.last_photo_time = 0
        self.photo_count = 0
        self.capture_mode = "photo"  # photo, video, burst
        
        # UI state
        self.ui_timeout = 0
        self.show_focus_indicator = False
        self.focus_x, self.focus_y = 64, 64
        
        # Create photos directory
        os.makedirs(self.config.PHOTOS_DIR, exist_ok=True)
        
        # Initialize camera
        self.init_camera()
        
        print("📷 Camera app initialized")
    
    def init_camera(self):
        """Initialize camera hardware"""
        try:
            if CAMERA_AVAILABLE:
                self.camera = PiCamera()
                self.camera.resolution = self.config.CAMERA_RESOLUTION
                self.camera.framerate = 24
                
                # Camera settings for better quality
                self.camera.exposure_mode = 'auto'
                self.camera.awb_mode = 'auto'
                self.camera.meter_mode = 'average'
                self.camera.image_effect = 'none'
                
                # Allow camera to warm up
                time.sleep(2)
                self.camera_ready = True
                print("✅ Pi Camera initialized")
            else:
                self.camera = MockCamera()
                self.camera_ready = True
                print("⚠️ Using mock camera for testing")
                
        except Exception as e:
            print(f"❌ Camera initialization failed: {e}")
            self.camera = MockCamera()
            self.camera_ready = True
    
    def on_launch(self):
        """Called when camera app is launched"""
        print("📷 Camera app launched")
        self.running = True
        self.preview_active = True
        self.show_ui = True
        self.ui_timeout = time.time() + 5  # Hide UI after 5 seconds
        
        # Update photo count
        self.update_photo_count()
    
    def on_exit(self):
        """Called when exiting camera app"""
        print("📷 Camera app exiting")
        self.running = False
        self.preview_active = False
    
    def run_frame(self):
        """Update camera app (called every frame)"""
        if not self.running:
            return False
        
        # Update camera preview
        if self.preview_active and self.camera_ready:
            self.update_preview()
        
        # Draw UI overlay
        if self.show_ui or time.time() < self.ui_timeout:
            self.draw_camera_ui()
        
        # Auto-hide UI
        if time.time() > self.ui_timeout:
            self.show_ui = False
        
        self.display.update()
        return True
    
    def handle_input(self, nav_input):
        """Handle camera app input"""
        if nav_input == "CENTER":
            self.take_photo()
        elif nav_input == "UP":
            # Exit to launcher
            self.on_exit()
            return False
        elif nav_input == "DOWN":
            # Toggle UI overlay
            self.toggle_ui()
        elif nav_input == "LEFT":
            # Previous capture mode
            self.cycle_capture_mode(-1)
        elif nav_input == "RIGHT":
            # Next capture mode
            self.cycle_capture_mode(1)
        
        # Reset UI timeout on any input
        self.ui_timeout = time.time() + 5
        self.show_ui = True
        
        return True
    
    def update_preview(self):
        """Update camera preview on display"""
        try:
            # Capture small preview image
            preview_path = "/tmp/camera_preview.jpg"
            
            if CAMERA_AVAILABLE and self.camera and not getattr(self.camera, 'closed', False):
                self.camera.capture(preview_path, resize=(128, 128), use_video_port=True)
            else:
                # Create mock preview
                self.camera.capture(preview_path, resize=(128, 128))
            
            # Load and display preview
            preview_img = Image.open(preview_path)
            self.display.display_image(preview_img, x=0, y=0)
            
        except Exception as e:
            # Show error instead of preview
            self.display.clear((50, 50, 50))
            self.display.draw_text("Camera Error", 25, 55, color=(255, 100, 100), size=12)
            error_msg = str(e)[:20] + "..." if len(str(e)) > 20 else str(e)
            self.display.draw_text(error_msg, 10, 75, color=(255, 150, 150), size=8)
    
    def take_photo(self):
        """Capture and save photo"""
        current_time = time.time()
        
        # Prevent rapid-fire photos
        if current_time - self.last_photo_time < 1.0:
            return
        
        self.last_photo_time = current_time
        
        if not self.camera_ready:
            self.show_error_message("Camera not ready")
            return
        
        try:
            # Generate filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"photo_{timestamp}.jpg"
            filepath = os.path.join(self.config.PHOTOS_DIR, filename)
            
            # Show capture feedback
            self.show_capture_feedback()
            
            # Capture photo at full resolution
            if CAMERA_AVAILABLE and self.camera and not getattr(self.camera, 'closed', False):
                self.camera.capture(filepath, quality=self.config.PHOTO_QUALITY)
            else:
                # Mock capture
                self.camera.capture(filepath)
            
            print(f"📸 Photo captured: {filename}")
            
            # Update photo count
            self.photo_count += 1
            
            # Queue for upload to network share
            self.uploader.queue_photo(filepath)
            
            # Show success confirmation
            self.show_capture_confirmation(filename)
            
        except Exception as e:
            print(f"❌ Photo capture failed: {e}")
            error_msg = str(e)[:20] + "..." if len(str(e)) > 20 else str(e)
            self.show_error_message(f"Capture failed: {error_msg}")
    
    def show_capture_feedback(self):
        """Show immediate capture feedback"""
        # Flash effect
        self.display.flash_screen(color=(255, 255, 255), duration=0.1)
        
        # Show capture indicator
        self.display.draw_circle(64, 64, 20, color=(255, 255, 255))
        self.display.draw_text("📸", 55, 55, color=(0, 0, 0), size=16)
        self.display.update()
        time.sleep(0.2)
    
    def show_capture_confirmation(self, filename):
        """Show photo saved confirmation"""
        # Semi-transparent overlay
        self.display.draw_rectangle(10, 50, 108, 30, color=(0, 0, 0), outline=(0, 255, 0))
        self.display.draw_text("Saved to Share!", 20, 58, color=(0, 255, 0), size=12)
        display_name = filename[:15] + "..." if len(filename) > 15 else filename
        self.display.draw_text(display_name, 15, 70, color=(200, 255, 200), size=8)
        self.display.update()
        time.sleep(1.5)
    
    def show_error_message(self, message):
        """Show error message overlay"""
        self.display.draw_rectangle(10, 50, 108, 30, color=(0, 0, 0), outline=(255, 0, 0))
        self.display.draw_text("Error", 50, 58, color=(255, 0, 0), size=12)
        self.display.draw_text(message, 15, 70, color=(255, 200, 200), size=8)
        self.display.update()
        time.sleep(2)
    
    def toggle_ui(self):
        """Toggle UI overlay visibility"""
        self.show_ui = not self.show_ui
        if self.show_ui:
            self.ui_timeout = time.time() + 10  # Show for 10 seconds
        print(f"📱 Camera UI {'shown' if self.show_ui else 'hidden'}")
    
    def cycle_capture_mode(self, direction):
        """Cycle through capture modes"""
        modes = ["photo", "video", "burst"]
        current_index = modes.index(self.capture_mode)
        new_index = (current_index + direction) % len(modes)
        self.capture_mode = modes[new_index]
        
        # Show mode change
        self.display.draw_rectangle(20, 45, 88, 20, color=(0, 0, 0), outline=(100, 150, 255))
        self.display.draw_text(f"Mode: {self.capture_mode.title()}", 30, 52, color=(255, 255, 255), size=12)
        self.display.update()
        time.sleep(1)
        
        print(f"📷 Capture mode: {self.capture_mode}")
    
    def draw_camera_ui(self):
        """Draw camera UI overlay"""
        if not self.show_ui:
            return
        
        # Semi-transparent top bar
        self.display.draw_rectangle(0, 0, 128, 22, color=(0, 0, 0))
        
        # Time and mode
        current_time = datetime.now().strftime("%H:%M:%S")
        self.display.draw_text(current_time, 5, 5, color=(255, 255, 255), size=10)
        self.display.draw_text(self.capture_mode.upper(), 70, 5, color=(255, 255, 0), size=10)
        
        # Photo count
        self.display.draw_text(f"📷{self.photo_count}", 5, 12, color=(200, 200, 200), size=8)
        
        # Upload status - show share status instead of WiFi
        upload_status = self.uploader.get_upload_status()
        if upload_status['pending'] > 0:
            self.display.draw_text(f"⬆{upload_status['pending']}", 90, 12, color=(255, 255, 0), size=8)
        else:
            self.display.draw_text("📁", 100, 12, color=(0, 255, 0), size=8)  # Share icon
        
        # Semi-transparent bottom bar
        self.display.draw_rectangle(0, 106, 128, 22, color=(0, 0, 0))
        
        # Control hints
        self.display.draw_text("● Photo", 5, 110, color=(255, 255, 255), size=8)
        self.display.draw_text("▲ Exit", 50, 110, color=(200, 200, 200), size=8)
        self.display.draw_text("▼ UI", 85, 110, color=(200, 200, 200), size=8)
        
        # Mode switching hints
        self.display.draw_text("◄ ► Mode", 30, 118, color=(150, 150, 150), size=7)
    
    def update_photo_count(self):
        """Update photo count from filesystem"""
        try:
            photos = [f for f in os.listdir(self.config.PHOTOS_DIR) 
                     if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
            self.photo_count = len(photos)
        except Exception as e:
            print(f"⚠️ Error counting photos: {e}")
            self.photo_count = 0
    
    def get_photo_count(self):
        """Get current photo count"""
        return self.photo_count
    
    def cleanup(self):
        """Clean up camera resources"""
        print("🧹 Cleaning up camera app...")
        self.running = False
        self.preview_active = False
        
        if self.camera and hasattr(self.camera, 'close') and not getattr(self.camera, 'closed', False):
            try:
                self.camera.close()
                print("✅ Camera closed")
            except Exception as e:
                print(f"⚠️ Camera cleanup error: {e}")
        
        if hasattr(self, 'uploader'):
            self.uploader.cleanup()