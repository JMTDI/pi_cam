#!/usr/bin/env python3
"""
Configuration settings for Pi Zero Camera
Centralized configuration management
Author: JMTDI
Date: 2025-10-25
"""

import os
import json
from datetime import datetime

class Config:
    def __init__(self):
        # Base directories
        self.BASE_DIR = os.path.expanduser("~/camera")
        self.PHOTOS_DIR = os.path.join(self.BASE_DIR, "photos")
        self.DATA_DIR = os.path.join(self.BASE_DIR, "data")
        self.CONFIG_FILE = os.path.join(self.DATA_DIR, "config.json")
        
        # Create directories
        self.ensure_directories()
        
        # Default configuration
        self.default_config = {
            # Camera settings
            "CAMERA_RESOLUTION": [1640, 1232],  # Pi Camera v2 max resolution
            "PREVIEW_RESOLUTION": [128, 128],   # Preview size for display
            "PHOTO_QUALITY": 85,                # JPEG quality (1-100)
            "CAMERA_ROTATION": 0,               # Camera rotation (0, 90, 180, 270)
            
            # Display settings
            "DISPLAY_WIDTH": 128,
            "DISPLAY_HEIGHT": 128,
            "DISPLAY_ROTATION": 0,              # Display rotation
            "DISPLAY_BRIGHTNESS": 80,           # 0-100 (if supported)
            "UI_TIMEOUT": 5,                    # Seconds before UI hides
            
            # Navigation settings
            "BUTTON_DEBOUNCE": 0.2,             # Button debounce time (seconds)
            "REPEAT_DELAY": 0.5,                # Time before repeat starts
            "REPEAT_RATE": 0.1,                 # Time between repeats
            
            # Power management
            "AUTO_SLEEP_TIME": 300,             # Auto sleep after 5 minutes
            "LOW_BATTERY_THRESHOLD": 15,        # Low battery warning %
            "SHUTDOWN_BATTERY_LEVEL": 5,        # Auto shutdown battery %
            
            # WiFi settings
            "WIFI_SCAN_INTERVAL": 60,           # WiFi scan interval (seconds)
            "WIFI_CONNECT_TIMEOUT": 30,         # WiFi connection timeout
            "WIFI_RETRY_ATTEMPTS": 3,           # Number of connection retries
            
            # Network Share settings (instead of upload URL)
            "SHARE_NAME": "PiCamera",           # Network share name
            "SHARE_PATH": "/home/pi/camera_share",  # Local share directory
            "DEVICE_ID": "picamera-001",        # Unique device identifier
            "AUTO_ORGANIZE_BY_DATE": True,      # Organize photos by date
            "AUTO_DELETE_UPLOADED": False,      # Keep local copies
            
            # File management
            "MAX_PHOTOS": 1000,                 # Maximum photos to store
            "PHOTO_FORMAT": "JPEG",             # Photo format
            "FILENAME_FORMAT": "photo_%Y%m%d_%H%M%S",  # Filename format
            
            # System settings
            "DEBUG_MODE": False,                # Enable debug logging
            "LOG_LEVEL": "INFO",                # Logging level
            "STARTUP_SOUND": True,              # Play startup sound
            "SHUTDOWN_SOUND": True              # Play shutdown sound
        }
        
        # Load configuration
        self.config = self.load_config()
        
        # Set attributes for easy access
        self.set_attributes()
        
        print(f"⚙️ Configuration loaded from {self.CONFIG_FILE}")
    
    def ensure_directories(self):
        """Create necessary directories"""
        for directory in [self.BASE_DIR, self.PHOTOS_DIR, self.DATA_DIR]:
            os.makedirs(directory, exist_ok=True)
    
    def load_config(self):
        """Load configuration from file or create default"""
        try:
            if os.path.exists(self.CONFIG_FILE):
                with open(self.CONFIG_FILE, 'r') as f:
                    config = json.load(f)
                # Merge with defaults (add any missing keys)
                for key, value in self.default_config.items():
                    if key not in config:
                        config[key] = value
                return config
            else:
                # Create default config file
                self.save_config(self.default_config)
                return self.default_config.copy()
        except Exception as e:
            print(f"⚠️ Error loading config: {e}")
            return self.default_config.copy()
    
    def save_config(self, config=None):
        """Save configuration to file"""
        try:
            config_to_save = config or self.config
            with open(self.CONFIG_FILE, 'w') as f:
                json.dump(config_to_save, f, indent=4)
            print(f"💾 Configuration saved to {self.CONFIG_FILE}")
        except Exception as e:
            print(f"❌ Error saving config: {e}")
    
    def set_attributes(self):
        """Set configuration values as object attributes"""
        for key, value in self.config.items():
            setattr(self, key, value)
    
    def get(self, key, default=None):
        """Get configuration value"""
        return self.config.get(key, default)
    
    def set(self, key, value, save=True):
        """Set configuration value"""
        self.config[key] = value
        setattr(self, key, value)
        if save:
            self.save_config()