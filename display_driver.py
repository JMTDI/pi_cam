#!/usr/bin/env python3
"""
ST7735S Display Driver for 1.44" 128x128 TFT LCD
Optimized for Pi Zero with fast SPI communication
Author: JMTDI
Date: 2025-10-25
"""

import spidev
import RPi.GPIO as GPIO
import time
import math
from PIL import Image, ImageDraw, ImageFont

class ST7735Display:
    def __init__(self):
        # ST7735S GPIO pins (matching your 8-pin display)
        self.DC_PIN = 24   # Data/Command
        self.RST_PIN = 25  # Reset
        self.CS_PIN = 8    # Chip Select (CE0)
        
        # Display specifications
        self.WIDTH = 128
        self.HEIGHT = 128
        self.ROTATION = 0  # 0, 90, 180, or 270 degrees
        
        # Initialize SPI
        self.spi = spidev.SpiDev()
        self.spi.open(0, 0)  # Bus 0, Device 0 (CE0)
        self.spi.max_speed_hz = 8000000  # 8MHz for fast updates
        self.spi.mode = 0
        
        # Initialize GPIO
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        GPIO.setup(self.DC_PIN, GPIO.OUT)
        GPIO.setup(self.RST_PIN, GPIO.OUT)
        
        # Create image buffer
        self.image = Image.new('RGB', (self.WIDTH, self.HEIGHT), (0, 0, 0))
        self.draw = ImageDraw.Draw(self.image)
        
        # Font cache
        self.fonts = {}
        self.load_fonts()
        
        print("📺 ST7735S Display driver initialized")
    
    def load_fonts(self):
        """Load and cache fonts of different sizes"""
        font_paths = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
            "/usr/share/fonts/truetype/droid/DroidSans.ttf"
        ]
        
        # Try to load TrueType fonts
        font_loaded = False
        for font_path in font_paths:
            try:
                self.fonts = {
                    8: ImageFont.truetype(font_path, 8),
                    9: ImageFont.truetype(font_path, 9),
                    10: ImageFont.truetype(font_path, 10),
                    12: ImageFont.truetype(font_path, 12),
                    14: ImageFont.truetype(font_path, 14),
                    16: ImageFont.truetype(font_path, 16),
                    20: ImageFont.truetype(font_path, 20),
                    24: ImageFont.truetype(font_path, 24)
                }
                print(f"✅ Loaded fonts from {font_path}")
                font_loaded = True
                break
            except OSError:
                continue
        
        # Fallback to default font
        if not font_loaded:
            default_font = ImageFont.load_default()
            self.fonts = {size: default_font for size in [8, 9, 10, 12, 14, 16, 20, 24]}
            print("⚠️ Using default font (install ttf fonts for better display)")
    
    def init_display(self):
        """Initialize ST7735S display with proper command sequence"""
        print("🔧 Initializing ST7735S display...")
        
        # Hardware reset sequence
        GPIO.output(self.RST_PIN, GPIO.HIGH)
        time.sleep(0.01)
        GPIO.output(self.RST_PIN, GPIO.LOW)
        time.sleep(0.01)
        GPIO.output(self.RST_PIN, GPIO.HIGH)
        time.sleep(0.12)
        
        # Software reset
        self._send_command(0x01)  # SWRESET
        time.sleep(0.15)
        
        # Sleep out
        self._send_command(0x11)  # SLPOUT
        time.sleep(0.5)
        
        # Frame rate control (normal mode/full colors)
        self._send_command(0xB1, [0x01, 0x2C, 0x2D])  # FRMCTR1
        self._send_command(0xB2, [0x01, 0x2C, 0x2D])  # FRMCTR2
        self._send_command(0xB3, [0x01, 0x2C, 0x2D, 0x01, 0x2C, 0x2D])  # FRMCTR3
        
        # Display inversion control
        self._send_command(0xB4, [0x07])  # INVCTR
        
        # Power control
        self._send_command(0xC0, [0xA2, 0x02, 0x84])  # PWCTR1
        self._send_command(0xC1, [0xC5])              # PWCTR2
        self._send_command(0xC2, [0x0A, 0x00])        # PWCTR3
        self._send_command(0xC3, [0x8A, 0x2A])        # PWCTR4
        self._send_command(0xC4, [0x8A, 0xEE])        # PWCTR5
        
        # VCOM control
        self._send_command(0xC5, [0x0E])  # VMCTR1
        
        # Display inversion off
        self._send_command(0x20)  # INVOFF
        
        # Memory access control (rotation and RGB/BGR)
        self._send_command(0x36, [0x00])  # MADCTL
        
        # Pixel format (16-bit color)
        self._send_command(0x3A, [0x05])  # COLMOD
        
        # Column address set (0 to 127)
        self._send_command(0x2A, [0x00, 0x00, 0x00, 0x7F])  # CASET
        
        # Row address set (0 to 127)
        self._send_command(0x2B, [0x00, 0x00, 0x00, 0x7F])  # RASET
        
        # Gamma correction
        self._send_command(0xE0, [  # GMCTRP1 (positive gamma)
            0x02, 0x1c, 0x07, 0x12, 0x37, 0x32, 0x29, 0x2d,
            0x29, 0x25, 0x2B, 0x39, 0x00, 0x01, 0x03, 0x10
        ])
        self._send_command(0xE1, [  # GMCTRN1 (negative gamma)
            0x03, 0x1d, 0x07, 0x06, 0x2E, 0x2C, 0x29, 0x2D,
            0x2E, 0x2E, 0x37, 0x3F, 0x00, 0x00, 0x02, 0x10
        ])
        
        # Normal display mode on
        self._send_command(0x13)  # NORON
        time.sleep(0.01)
        
        # Display on
        self._send_command(0x29)  # DISPON
        time.sleep(0.12)
        
        # Clear display
        self.clear()
        self.update()
        
        print("✅ ST7735S display ready (128x128 @ 16-bit color)")
    
    def _send_command(self, cmd, data=None):
        """Send command to ST7735S"""
        GPIO.output(self.DC_PIN, GPIO.LOW)  # Command mode
        self.spi.xfer2([cmd])
        
        if data:
            GPIO.output(self.DC_PIN, GPIO.HIGH)  # Data mode
            self.spi.xfer2(data)
    
    def _send_data(self, data):
        """Send data to ST7735S"""
        GPIO.output(self.DC_PIN, GPIO.HIGH)  # Data mode
        
        # Send data in chunks for better performance
        chunk_size = 4096
        for i in range(0, len(data), chunk_size):
            chunk = data[i:i + chunk_size]
            self.spi.xfer2(chunk)
    
    def clear(self, color=(0, 0, 0)):
        """Clear display buffer with specified color"""
        if isinstance(color, tuple) and len(color) >= 3:
            fill_color = color[:3]
        else:
            fill_color = (0, 0, 0)
        
        self.draw.rectangle([(0, 0), (self.WIDTH, self.HEIGHT)], fill=fill_color)
    
    def draw_text(self, text, x, y, color=(255, 255, 255), size=10, font=None):
        """Draw text with specified font size and color"""
        if font is None:
            font = self.fonts.get(size, self.fonts.get(10))
        
        # Handle color formats
        if isinstance(color, tuple) and len(color) >= 3:
            text_color = color[:3]  # Use RGB, ignore alpha if present
        else:
            text_color = (255, 255, 255)  # Default white
        
        self.draw.text((int(x), int(y)), str(text), font=font, fill=text_color)
    
    def draw_rectangle(self, x, y, width, height, color=(255, 255, 255), outline=None):
        """Draw filled rectangle"""
        coords = [(int(x), int(y)), (int(x + width), int(y + height))]
        
        # Handle color formats
        if isinstance(color, tuple) and len(color) >= 3:
            fill_color = color[:3]
        else:
            fill_color = (255, 255, 255)
        
        if outline and isinstance(outline, tuple) and len(outline) >= 3:
            outline_color = outline[:3]
        else:
            outline_color = outline
        
        self.draw.rectangle(coords, fill=fill_color, outline=outline_color)
    
    def draw_circle(self, x, y, radius, color=(255, 255, 255), outline=None):
        """Draw filled circle"""
        coords = [(int(x - radius), int(y - radius)), (int(x + radius), int(y + radius))]
        
        if isinstance(color, tuple) and len(color) >= 3:
            fill_color = color[:3]
        else:
            fill_color = (255, 255, 255)
        
        self.draw.ellipse(coords, fill=fill_color, outline=outline)
    
    def draw_line(self, x1, y1, x2, y2, color=(255, 255, 255), width=1):
        """Draw line"""
        if isinstance(color, tuple) and len(color) >= 3:
            line_color = color[:3]
        else:
            line_color = (255, 255, 255)
        
        self.draw.line([(int(x1), int(y1)), (int(x2), int(y2))], fill=line_color, width=int(width))
    
    def display_image(self, img, x=0, y=0):
        """Display PIL image on screen at specified position"""
        if isinstance(img, Image.Image):
            self.image.paste(img, (int(x), int(y)))
        else:
            print("⚠️ Invalid image format")
    
    def update(self):
        """Update display with current buffer content"""
        # Convert image to RGB565 format for ST7735S
        rgb_image = self.image.convert('RGB')
        pixels = list(rgb_image.getdata())
        
        # Convert RGB888 to RGB565
        rgb565_data = []
        for pixel in pixels:
            r, g, b = pixel
            # Convert to 5-6-5 bit format
            r565 = (r >> 3) << 11
            g565 = (g >> 2) << 5
            b565 = b >> 3
            rgb565 = r565 | g565 | b565
            
            # Split into high and low bytes (big endian)
            rgb565_data.append((rgb565 >> 8) & 0xFF)
            rgb565_data.append(rgb565 & 0xFF)
        
        # Set memory write command
        self._send_command(0x2C)  # RAMWR
        
        # Send pixel data
        self._send_data(rgb565_data)
    
    def flash_screen(self, color=(255, 255, 255), duration=0.2):
        """Flash screen with specified color for camera feedback"""
        # Save current image
        original_image = self.image.copy()
        
        # Flash with specified color
        self.clear(color)
        self.update()
        time.sleep(duration)
        
        # Restore original image
        self.image = original_image
        self.update()
    
    def cleanup(self):
        """Clean up GPIO and SPI resources"""
        try:
            # Clear display
            self.clear()
            self.update()
            
            # Close SPI
            self.spi.close()
            
            # Reset GPIO pins
            GPIO.output(self.RST_PIN, GPIO.LOW)
            
            print("🧹 Display cleanup complete")
        except Exception as e:
            print(f"⚠️ Display cleanup error: {e}")