#!/usr/bin/env python3
"""
Navigation Controller for Powered 5-Way Switch
Updated for your VCC/GND switch configuration
Author: JMTDI
Date: 2025-10-25
"""

import RPi.GPIO as GPIO
import time
import threading

class NavigationController:
    def __init__(self):
        # GPIO pin assignments for your powered 5-way switch
        self.pins = {
            'UP': 17,       # GPIO 17 (Pin 11)
            'DOWN': 27,     # GPIO 27 (Pin 13)  
            'LEFT': 22,     # GPIO 22 (Pin 15)
            'RIGHT': 23,    # GPIO 23 (Pin 16)
            'CENTER': 18    # GPIO 18 (Pin 12)
        }
        
        # Timing configuration
        self.debounce_time = 0.2    # 200ms debounce
        self.repeat_delay = 0.5     # 500ms before repeat starts
        self.repeat_rate = 0.1      # 100ms between repeats
        
        # State tracking
        self.last_press = {}
        self.press_count = {}
        self.button_states = {}
        self.repeat_active = {}
        
        # Initialize GPIO
        self.setup_gpio()
        
        # Background thread for repeat functionality
        self.running = True
        self.repeat_thread = threading.Thread(target=self._repeat_handler, daemon=True)
        self.repeat_thread.start()
        
        print("🎮 Navigation controller initialized (powered switch)")
    
    def setup_gpio(self):
        """Setup GPIO pins for powered navigation switch"""
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        
        # Initialize state tracking
        for direction in self.pins:
            self.last_press[direction] = 0
            self.press_count[direction] = 0
            self.button_states[direction] = False
            self.repeat_active[direction] = False
        
        # Setup pins - NO internal pull-ups needed (switch has VCC)
        for direction, pin in self.pins.items():
            GPIO.setup(pin, GPIO.IN)  # No pull-up needed for powered switch
            print(f"📌 {direction}: GPIO {pin}")
        
        print("✅ GPIO setup complete (powered switch mode)")
    
    def get_input(self):
        """Get current navigation input with debouncing"""
        current_time = time.time()
        
        for direction, pin in self.pins.items():
            try:
                # For powered switch: HIGH = pressed, LOW = not pressed
                button_pressed = GPIO.input(pin) == GPIO.HIGH
                
                # Check for button press
                if button_pressed and not self.button_states[direction]:
                    # Button just pressed
                    if current_time - self.last_press[direction] >= self.debounce_time:
                        self.last_press[direction] = current_time
                        self.button_states[direction] = True
                        self.press_count[direction] = 1
                        print(f"🎮 Navigation: {direction}")
                        return direction
                
                elif not button_pressed and self.button_states[direction]:
                    # Button just released
                    self.button_states[direction] = False
                    self.repeat_active[direction] = False
                
                elif button_pressed and self.button_states[direction]:
                    # Button held down - check for repeat
                    hold_time = current_time - self.last_press[direction]
                    
                    if hold_time >= self.repeat_delay and not self.repeat_active[direction]:
                        # Start repeating
                        self.repeat_active[direction] = True
                        print(f"🔁 Navigation repeat started: {direction}")
                        
            except Exception as e:
                print(f"⚠️ GPIO error for {direction}: {e}")
                continue
        
        return None
    
    def _repeat_handler(self):
        """Background thread to handle button repeat functionality"""
        while self.running:
            current_time = time.time()
            
            for direction in self.pins:
                if (self.repeat_active[direction] and 
                    self.button_states[direction] and
                    current_time - self.last_press[direction] >= self.repeat_rate):
                    
                    # Generate repeat event
                    self.last_press[direction] = current_time
                    self.press_count[direction] += 1
                    
                    # Don't flood with repeat events
                    if self.press_count[direction] % 3 == 0:  # Every 3rd repeat
                        print(f"🔁 Navigation repeat: {direction}")
            
            time.sleep(0.05)  # Check every 50ms
    
    def wait_for_input(self, timeout=None):
        """Wait for navigation input with optional timeout"""
        start_time = time.time()
        
        while True:
            input_val = self.get_input()
            if input_val:
                return input_val
            
            if timeout and (time.time() - start_time) > timeout:
                return None
            
            time.sleep(0.05)
    
    def cleanup(self):
        """Clean up GPIO resources"""
        print("🧹 Cleaning up navigation controller...")
        self.running = False
        
        # Wait for repeat thread to finish
        if self.repeat_thread.is_alive():
            self.repeat_thread.join(timeout=1)
        
        # Reset all pins to input
        for pin in self.pins.values():
            try:
                GPIO.setup(pin, GPIO.IN)
            except Exception as e:
                print(f"⚠️ GPIO cleanup error on pin {pin}: {e}")
        
        print("✅ Navigation cleanup complete")