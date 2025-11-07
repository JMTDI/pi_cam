# Pi Zero Instant Camera with Network Share

A fast-booting, portable camera system with Android-style interface, automatic WiFi photo sharing, and Windows file explorer access. Perfect for your 1.44" ST7735S color display!

## ✨ Features

- **Ultra-fast boot** - Camera ready in 15-25 seconds
- **Android-style launcher** - Navigate with D-pad between Camera and Settings
- **Live camera preview** - Full-color real-time viewfinder on 128x128 display
- **Windows network share** - Photos automatically accessible from Windows File Explorer
- **Date-organized photos** - Daily folders (2025-10-25, 2025-10-26, etc.)
- **5-way navigation** - Simple D-pad control (up/down/left/right/center)
- **WiFi management** - Easy network setup and connection
- **Battery powered** - Optimized for portable 500mAh operation
- **Color LCD interface** - Beautiful UI with icons, colors, and animations

## 🛠 Hardware Requirements

### Core Components
- **Raspberry Pi Zero W** - Main computer
- **Pi Camera Module v2** - 8MP camera (or v1 5MP)
- **ST7735S 1.44" TFT LCD** - 128x128 color display with 8 pins:
  - VCC, GND, CS, DC, RES, SDA, SCL, BLK
- **5-way navigation switch** - D-pad style control with 7 pins:
  - VCC, GND, UP, DOWN, LEFT, RIGHT, CENTER
- **500mAh LiPo battery** - With JST connector
- **MicroSD card** - 16GB+ Class 10

### Wiring
See `WIRING.md` for complete connection diagram.

## 🚀 Quick Start

### 1. Prepare SD Card
```bash
# Flash Raspberry Pi OS Lite to SD card
# Enable SSH and WiFi in boot partition (optional)