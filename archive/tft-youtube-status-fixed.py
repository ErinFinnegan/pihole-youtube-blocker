#!/usr/bin/env python3
# Fixed version of tft-youtube-status.py with direct SQLite queries

import time, subprocess, sys, signal, threading
from datetime import datetime
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
# GPIO Setup
# ----------------------------
BTN_BLOCK = 23  # Bottom button
BTN_ALLOW = 24  # Top button
GPIO.setmode(GPIO.BCM)
GPIO.setup(BTN_BLOCK, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(BTN_ALLOW, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# ----------------------------
# Status Functions (Fixed with direct SQLite queries)
# ----------------------------
def youtube_blocked() -> bool:
    """Check if YouTube is blocked via KidsRestricted group"""
    cmd = [
        "sudo","/usr/bin/sqlite3","/etc/pihole/gravity.db",
        "SELECT enabled FROM 'group' WHERE name='KidsRestricted';"
    ]
    try:
        out = subprocess.check_output(cmd, text=True).strip()
        return out == "1"
    except Exception:
        return True  # fail safe: assume blocked

def roblox_blocked() -> bool:
    """Check if Roblox is blocked using direct SQLite query"""
    try:
        result = subprocess.run(
            ["sudo", "sqlite3", "/etc/pihole/gravity.db", 
             "SELECT COUNT(*) FROM domainlist WHERE domain='roblox.com' AND type=1;"],
            capture_output=True, text=True, timeout=3
        )
        return result.stdout.strip() == "1"
    except Exception:
        return False  # fail safe: assume allowed

def scratch_accessible() -> bool:
    """Check if Scratch is accessible using direct SQLite query"""
    try:
        result = subprocess.run(
            ["sudo", "sqlite3", "/etc/pihole/gravity.db", 
             "SELECT COUNT(*) FROM domainlist WHERE domain='scratch.mit.edu' AND type=0;"],
            capture_output=True, text=True, timeout=3
        )
        return result.stdout.strip() == "1"
    except Exception:
        return True  # fail safe: assume accessible

# ----------------------------
# Button Functions
# ----------------------------
def block_youtube(_ch=None):
    """Block YouTube by enabling KidsRestricted group"""
    print("Blocking YouTube...")
    try:
        subprocess.run([
            "sudo", "sqlite3", "/etc/pihole/gravity.db",
            "UPDATE 'group' SET enabled=1 WHERE name='KidsRestricted';"
        ], timeout=10)
        subprocess.run(["sudo", "pihole", "reloadlists"], timeout=10)
        print("YouTube blocked successfully")
    except Exception as e:
        print(f"Error blocking YouTube: {e}")

def allow_youtube(_ch=None):
    """Allow YouTube by disabling KidsRestricted group"""
    print("Allowing YouTube...")
    try:
        subprocess.run([
            "sudo", "sqlite3", "/etc/pihole/gravity.db",
            "UPDATE 'group' SET enabled=0 WHERE name='KidsRestricted';"
        ], timeout=10)
        subprocess.run(["sudo", "pihole", "reloadlists"], timeout=10)
        print("YouTube allowed successfully")
    except Exception as e:
        print(f"Error allowing YouTube: {e}")

# ----------------------------
# Display Functions
# ----------------------------
def draw(blocked: bool, show_button_feedback=False, show_status_confirmation=False):
    # Get current status of all services
    youtube_status = blocked
    roblox_status = roblox_blocked()
    scratch_status = scratch_accessible()
    
    # Determine background color and title
    if show_button_feedback:
        # Show blue background when button is pressed
        bg_color = BLUE
        if button_pressed == "blocking":
            title = "BLOCKING..."
        else:  # allowing
            title = "ALLOWING..."
    elif show_status_confirmation:
        # Show yellow background for confirmation
        bg_color = YELLOW
        title = "STATUS CHANGED!"
    else:
        # Normal status display
        if youtube_status:
            bg_color = RED
            title = "YouTube BLOCKED"
        else:
            bg_color = GREEN
            title = "YouTube ALLOWED"
    
    # Create image
    img = Image.new("RGB", (IMG_W, IMG_H), color=bg_color)
    d = ImageDraw.Draw(img)
    
    # Text color (black on yellow, white on others)
    text_color = BLACK if bg_color == YELLOW else WHITE
    
    # Main title
    d.text((10, 10), title, font=FB, fill=text_color)
    
    # Status details
    d.text((10, 40), f"YouTube: {'BLOCKED' if youtube_status else 'ALLOWED'}", font=FS, fill=text_color)
    d.text((10, 55), f"Roblox: {'BLOCKED' if roblox_status else 'ALLOWED'}", font=FS, fill=text_color)
    d.text((10, 70), f"Scratch: {'BLOCKED' if not scratch_status else 'ALLOWED'}", font=FS, fill=text_color)
    
    # Clock
    now = datetime.now()
    time_str = now.strftime("%H:%M:%S")
    d.text((10, 90), time_str, font=FS, fill=text_color)
    
    # Button labels
    d.text((10, IMG_H-20), "B23: BLOCK  B24: ALLOW", font=FS, fill=text_color)
    
    disp.image(img)

# ----------------------------
# Button Event Handlers
# ----------------------------
button_pressed = None
button_press_time = 0
status_change_confirmed = False
status_change_time = 0

def button_block_callback(channel):
    global button_pressed, button_press_time, status_change_confirmed, status_change_time
    button_pressed = "blocking"
    button_press_time = time.time()
    status_change_confirmed = False
    draw(True, show_button_feedback=True)
    threading.Thread(target=block_youtube, daemon=True).start()

def button_allow_callback(channel):
    global button_pressed, button_press_time, status_change_confirmed, status_change_time
    button_pressed = "allowing"
    button_press_time = time.time()
    status_change_confirmed = False
    draw(False, show_button_feedback=True)
    threading.Thread(target=allow_youtube, daemon=True).start()

def _force_refresh(*_):
    """Force refresh display"""
    global status_change_confirmed, status_change_time
    status_change_confirmed = True
    status_change_time = time.time()
    print("Display refresh requested via signal")

# ----------------------------
# Signal Handlers
# ----------------------------
signal.signal(signal.SIGUSR1, _force_refresh)

def _clean_exit(signum, frame):
    print(f"\nReceived signal {signum}, cleaning up...")
    try:
        disp.fill(0)  # Clear display
    except:
        pass
    GPIO.cleanup()
    sys.exit(0)

signal.signal(signal.SIGINT, _clean_exit)
signal.signal(signal.SIGTERM, _clean_exit)

# ----------------------------
# Main Loop
# ----------------------------
def main():
    global button_pressed, button_press_time, status_change_confirmed, status_change_time
    
    print("Starting PiTFT YouTube Status Display...")
    print("Button 23 (bottom) = BLOCK, Button 24 (top) = ALLOW")
    
    # Button state tracking for polling
    button_states = {BTN_BLOCK: True, BTN_ALLOW: True}  # True = not pressed (pull-up)
    last_button_time = {BTN_BLOCK: 0, BTN_ALLOW: 0}
    DEBOUNCE_TIME = 0.2  # 200ms debounce
    
    last_state = None
    try:
        while True:
            current_time = time.time()
            blocked = youtube_blocked()
            
            # Check for button presses (polling with debounce)
            for button_pin in [BTN_BLOCK, BTN_ALLOW]:
                current_state = GPIO.input(button_pin)
                if current_state != button_states[button_pin]:  # State changed
                    if current_state == False and current_time - last_button_time[button_pin] > DEBOUNCE_TIME:
                        # Button pressed (False = pressed due to pull-up)
                        last_button_time[button_pin] = current_time
                        
                        if button_pin == BTN_BLOCK:
                            button_pressed = "blocking"
                            button_press_time = current_time
                            status_change_confirmed = False
                            draw(blocked, show_button_feedback=True)
                            threading.Thread(target=block_youtube, daemon=True).start()
                        elif button_pin == BTN_ALLOW:
                            button_pressed = "allowing"
                            button_press_time = current_time
                            status_change_confirmed = False
                            draw(blocked, show_button_feedback=True)
                            threading.Thread(target=allow_youtube, daemon=True).start()
                    
                    button_states[button_pin] = current_state
            
            # Show button feedback for 2 seconds
            if button_pressed and current_time - button_press_time < 2:
                draw(blocked, show_button_feedback=True)
            # Show status confirmation for 3 seconds
            elif status_change_confirmed and current_time - status_change_time < 3:
                draw(blocked, show_status_confirmation=True)
            # Normal display
            else:
                if blocked != last_state:
                    draw(blocked)
                    last_state = blocked
                else:
                    draw(blocked)  # refresh time
            
            time.sleep(0.1)  # Faster polling for better button responsiveness
            
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        GPIO.cleanup()

if __name__ == "__main__":
    main()
