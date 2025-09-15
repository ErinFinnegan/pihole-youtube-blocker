#!/usr/bin/env python3
import time
import RPi.GPIO as GPIO

# Setup GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setup(23, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(24, GPIO.IN, pull_up_down=GPIO.PUD_UP)

print("=== BUTTON TEST - Press buttons now! ===")
print("Button 23 (bottom) = BLOCK, Button 24 (top) = ALLOW")
print("Press buttons and watch for changes from 1 to 0...")
print("Press Ctrl+C to stop")
print()

try:
    for i in range(200):  # Run for about 40 seconds
        current_time = time.strftime("%H:%M:%S")
        btn23 = GPIO.input(23)
        btn24 = GPIO.input(24)
        
        # Highlight when buttons are pressed (0 = pressed)
        status23 = "PRESSED!" if btn23 == 0 else "not pressed"
        status24 = "PRESSED!" if btn24 == 0 else "not pressed"
        
        print(f"Time: {current_time} - Button 23: {btn23} ({status23}), Button 24: {btn24} ({status24})")
        time.sleep(0.2)
        
except KeyboardInterrupt:
    print("\nTest stopped by user")
finally:
    GPIO.cleanup()
    print("GPIO cleaned up")
