#!/usr/bin/env python3
"""
Simple button test script for PiTFT
Tests button responsiveness without any Pi-hole integration
"""

import time
import sys
import signal
import digitalio, board
import RPi.GPIO as GPIO
from PIL import Image, ImageDraw, ImageFont
from adafruit_rgb_display import st7789

# ----------------------------
# Display init (Mini PiTFT 135x240, ST7789)
# ----------------------------
disp = st7789.ST7789(
    board.SPI(),
    cs=digitalio.DigitalInOut(board.CE0),
    dc=digitalio.DigitalInOut(board.D25),
    rst=None,
    baudrate=64_000_000,
    width=135, height=240, x_offset=53, y_offset=40
)

# Set rotation so text is upright
disp.rotation = 270
W, H = disp.width, disp.height
# For ST7789, we need to draw at swapped dimensions
IMG_W, IMG_H = disp.height, disp.width  # 240x135

# ----------------------------
# Colors & Fonts
# ----------------------------
GREEN = (0,180,0)
RED   = (200,0,0)
WHITE = (255,255,255)
BLACK = (0,0,0)
BLUE  = (0,100,200)
YELLOW = (255,255,0)

def font_big():
    try:
        return ImageFont.truetype(
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 18
        )
    except Exception:
        return ImageFont.load_default()

FB = font_big()
FS = ImageFont.load_default()

# ----------------------------
# GPIO Buttons (Mini PiTFT has 2)
# ----------------------------
BTN_BLOCK = 23   # left/front button
BTN_ALLOW = 24   # right/front button

GPIO.setmode(GPIO.BCM)
GPIO.setup(BTN_BLOCK, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(BTN_ALLOW, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# Button state tracking for polling
button_states = {BTN_BLOCK: True, BTN_ALLOW: True}  # True = not pressed (pulled up)
last_button_time = {BTN_BLOCK: 0, BTN_ALLOW: 0}
DEBOUNCE_TIME = 0.2  # 200ms debounce

# ----------------------------
# Clean exit on Ctrl+C or service stop
# ----------------------------
def _clean_exit(*_):
    try:
        GPIO.cleanup()
    except Exception:
        pass
    sys.exit(0)

signal.signal(signal.SIGINT, _clean_exit)
signal.signal(signal.SIGTERM, _clean_exit)

# ----------------------------
# Simple display function
# ----------------------------
def draw_screen(title, bg_color, message=""):
    img = Image.new("RGB", (IMG_W, IMG_H), color=bg_color)
    d = ImageDraw.Draw(img)
    
    # Centered title
    try:
        bbox = d.textbbox((0, 0), title, font=FB)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    except AttributeError:
        tw, th = d.textsize(title, font=FB)
    d.text(((IMG_W - tw)//2, 22), title, font=FB, fill=WHITE)
    
    # Message if provided
    if message:
        try:
            bbox = d.textbbox((0, 0), message, font=FS)
            mw, mh = bbox[2] - bbox[0], bbox[3] - bbox[1]
        except AttributeError:
            mw, mh = d.textsize(message, font=FS)
        d.text(((IMG_W - mw)//2, 50), message, font=FS, fill=WHITE)
    
    # Clock at bottom
    d.text((6, IMG_H-18), time.strftime("%H:%M:%S"), font=FS, fill=WHITE)
    disp.image(img)

# ----------------------------
# Main loop
# ----------------------------
def main():
    print("Button Test Starting...")
    print("Button 23 (Left): Should show RED screen")
    print("Button 24 (Right): Should show GREEN screen")
    print("Press Ctrl+C to exit")
    
    # Initial display
    draw_screen("BUTTON TEST", BLUE, "Press buttons!")
    
    while True:
        current_time = time.time()
        
        # Poll buttons for presses
        for button_pin in [BTN_BLOCK, BTN_ALLOW]:
            current_state = GPIO.input(button_pin)
            if current_state != button_states[button_pin]:  # State changed
                if current_state == False and current_time - last_button_time[button_pin] > DEBOUNCE_TIME:
                    # Button pressed (False = pressed due to pull-up)
                    last_button_time[button_pin] = current_time
                    print(f"Button {button_pin} pressed!")
                    
                    if button_pin == BTN_BLOCK:
                        draw_screen("BUTTON 23", RED, "LEFT BUTTON!")
                    elif button_pin == BTN_ALLOW:
                        draw_screen("BUTTON 24", GREEN, "RIGHT BUTTON!")
                
                button_states[button_pin] = current_state
        
        time.sleep(0.02)  # 50Hz polling

if __name__ == "__main__":
    main()
