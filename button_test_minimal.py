#!/usr/bin/env python3
# Minimal button test - just polling and display feedback

import time
import RPi.GPIO as GPIO
from PIL import Image, ImageDraw, ImageFont
from adafruit_rgb_display import st7789
import digitalio, board

# Display setup
disp = st7789.ST7789(
    board.SPI(),
    cs=digitalio.DigitalInOut(board.CE0),
    dc=digitalio.DigitalInOut(board.D25),
    rst=None,
    baudrate=64_000_000,
    width=135, height=240, x_offset=53, y_offset=40
)
disp.rotation = 270
IMG_W, IMG_H = disp.height, disp.width  # 240x135

# Colors
GREEN = (0,180,0)
RED = (200,0,0)
WHITE = (255,255,255)
BLACK = (0,0,0)
BLUE = (0,100,200)
YELLOW = (255,255,0)

# Fonts
try:
    FB = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 18)
except:
    FB = ImageFont.load_default()
FS = ImageFont.load_default()

# GPIO setup
BTN_BLOCK = 23
BTN_ALLOW = 24
GPIO.setmode(GPIO.BCM)
GPIO.setup(BTN_BLOCK, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(BTN_ALLOW, GPIO.IN, pull_up_down=GPIO.PUD_UP)

def draw_screen(message, color, show_time=True):
    img = Image.new("RGB", (IMG_W, IMG_H), color)
    d = ImageDraw.Draw(img)
    text_color = BLACK if color == YELLOW else WHITE
    
    d.text((10, 10), message, font=FB, fill=text_color)
    
    if show_time:
        now = time.strftime("%H:%M:%S")
        d.text((10, 40), now, font=FS, fill=text_color)
    
    d.text((10, IMG_H-20), "B23:BLOCK B24:ALLOW", font=FS, fill=text_color)
    disp.image(img)

def main():
    print("Starting minimal button test...")
    print("Button 23 (bottom) = BLOCK, Button 24 (top) = ALLOW")
    
    # Button state tracking
    button_states = {BTN_BLOCK: True, BTN_ALLOW: True}
    last_button_time = {BTN_BLOCK: 0, BTN_ALLOW: 0}
    DEBOUNCE_TIME = 0.2
    
    # Initial display
    draw_screen("BUTTON TEST", BLUE)
    
    try:
        while True:
            current_time = time.time()
            
            # Check for button presses
            for button_pin in [BTN_BLOCK, BTN_ALLOW]:
                current_state = GPIO.input(button_pin)
                if current_state != button_states[button_pin]:
                    if current_state == False and current_time - last_button_time[button_pin] > DEBOUNCE_TIME:
                        # Button pressed
                        last_button_time[button_pin] = current_time
                        
                        if button_pin == BTN_BLOCK:
                            print("Button 23 (BLOCK) pressed!")
                            draw_screen("BLOCK PRESSED!", RED)
                        elif button_pin == BTN_ALLOW:
                            print("Button 24 (ALLOW) pressed!")
                            draw_screen("ALLOW PRESSED!", GREEN)
                    
                    button_states[button_pin] = current_state
            
            # Update display every second
            if int(current_time) % 2 == 0:  # Every 2 seconds
                draw_screen("WAITING...", BLUE)
            
            time.sleep(0.1)
            
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        GPIO.cleanup()

if __name__ == "__main__":
    main()

