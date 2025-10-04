# tft-youtube-status.py

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
# Try 270 first; if sideways, change to 90
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
BTN_YOUTUBE = 23   # left/front button: toggle YouTube
BTN_ROBLOX  = 24   # right/front button: toggle Roblox/Playhop

GPIO.setmode(GPIO.BCM)
GPIO.setup(BTN_YOUTUBE, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(BTN_ROBLOX, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# Global variables for button feedback
button_pressed = None
button_press_time = 0
status_change_confirmed = False
status_change_time = 0

def block_youtube(_ch=None):
    global button_pressed, button_press_time
    button_pressed = "blocking"
    button_press_time = time.time()
    # Run the actual command in a separate thread to avoid blocking
    threading.Thread(target=lambda: subprocess.call(["/bin/bash", "/usr/local/bin/pitft_block.sh"]), daemon=True).start()

def allow_youtube(_ch=None):
    global button_pressed, button_press_time
    button_pressed = "allowing"
    button_press_time = time.time()
    # Run the actual command in a separate thread to avoid blocking
    threading.Thread(target=lambda: subprocess.call(["/bin/bash", "/usr/local/bin/pitft_allow.sh"]), daemon=True).start()


def toggle_roblox(_ch=None):
    global button_pressed, button_press_time
    button_pressed = "toggling"
    button_press_time = time.time()
    # Decide helper based on KidsRoblox group
    try:
        out = subprocess.check_output([
            "sudo", "/usr/bin/sqlite3", "/etc/pihole/gravity.db",
            "SELECT enabled FROM 'group' WHERE name='KidsRoblox';"
        ], text=True).strip()
        is_blocked = (out == "1")
    except Exception:
        is_blocked = False
    helper = "/usr/local/bin/pitft_roblox_allow.sh" if is_blocked else "/usr/local/bin/pitft_roblox_block.sh"
    threading.Thread(target=lambda: subprocess.call(["/bin/bash", helper]), daemon=True).start()

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

def _force_refresh(*_):
    """Force immediate display refresh when signaled"""
    global last_state
    last_state = None  # Force a refresh on next loop iteration
    print("Display refresh requested via signal")

signal.signal(signal.SIGINT, _clean_exit)
signal.signal(signal.SIGTERM, _clean_exit)
signal.signal(signal.SIGUSR1, _force_refresh)  # Handle refresh signal

# ----------------------------
# Helpers
# ----------------------------
def youtube_blocked() -> bool:
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
    try:
        out = subprocess.check_output([
            "sudo","/usr/bin/sqlite3","/etc/pihole/gravity.db",
            "SELECT enabled FROM 'group' WHERE name='KidsRoblox';"
        ], text=True).strip()
        return out == "1"
    except Exception:
        return False

# Scratch is always allowed by policy; avoid any runtime DNS checks

def draw(blocked: bool, show_button_feedback=False, show_status_confirmation=False):
    global button_pressed, button_press_time, status_change_confirmed, status_change_time
    
    # Get current status of all services
    youtube_status = blocked
    roblox_status = roblox_blocked()
    
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
        # Normal status display - show primary service status
        bg_color = RED if youtube_status else GREEN
        title = "YouTube BLOCKED" if youtube_status else "YouTube ALLOWED"
    
    img = Image.new("RGB", (IMG_W, IMG_H), color=bg_color)
    d = ImageDraw.Draw(img)

    # Improve contrast: black text on yellow, white otherwise
    text_color = BLACK if bg_color == YELLOW else WHITE
    
    # Centered title (new Pillow uses textbbox, fallback textsize)
    try:
        bbox = d.textbbox((0, 0), title, font=FB)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    except AttributeError:
        tw, th = d.textsize(title, font=FB)
    d.text(((IMG_W - tw)//2, 22), title, font=FB, fill=text_color)
    
    # Add dots for button feedback
    if show_button_feedback:
        dots = "..." + ("." * int((time.time() - button_press_time) * 2))[:3]
        try:
            bbox = d.textbbox((0, 0), dots, font=FS)
            dw, dh = bbox[2] - bbox[0], bbox[3] - bbox[1]
        except AttributeError:
            dw, dh = d.textsize(dots, font=FS)
        d.text(((IMG_W - dw)//2, 50), dots, font=FS, fill=text_color)
    
    # Add confirmation message
    if show_status_confirmation:
        confirm_msg = "✓ DONE"
        try:
            bbox = d.textbbox((0, 0), confirm_msg, font=FS)
            cw, ch = bbox[2] - bbox[0], bbox[3] - bbox[1]
        except AttributeError:
            cw, ch = d.textsize(confirm_msg, font=FS)
        d.text(((IMG_W - cw)//2, 50), confirm_msg, font=FS, fill=text_color)
    
    # Add status indicators for other services (only in normal display mode)
    if not show_button_feedback and not show_status_confirmation:
        # Show Roblox status (independent KidsRoblox group)
        roblox_text = "Roblox: " + ("BLOCKED" if roblox_status else "ALLOWED")
        try:
            bbox = d.textbbox((0, 0), roblox_text, font=FB)
            rw, rh = bbox[2] - bbox[0], bbox[3] - bbox[1]
        except AttributeError:
            rw, rh = d.textsize(roblox_text, font=FB)
        d.text(((IMG_W - rw)//2, 50), roblox_text, font=FB, fill=WHITE)
        
        # (Scratch line removed; Scratch is allowed by policy)
    
    # Clock at bottom
    d.text((6, IMG_H-18), datetime.now().strftime("%Y-%m-%d %H:%M:%S"), font=FS, fill=WHITE)
    disp.image(img)

# ----------------------------
# Main loop
# ----------------------------
def main():
    global button_pressed, button_press_time, status_change_confirmed, status_change_time
    
    last_state = None
    while True:
        current_time = time.time()
        
        # Poll buttons for presses (replaces edge detection)
        for button_pin in [BTN_YOUTUBE, BTN_ROBLOX]:
            current_state = GPIO.input(button_pin)
            if current_state != button_states[button_pin]:  # State changed
                if current_state == False and current_time - last_button_time[button_pin] > DEBOUNCE_TIME:
                    # Button pressed (False = pressed due to pull-up)
                    last_button_time[button_pin] = current_time
                    if button_pin == BTN_YOUTUBE:
                        block_youtube()
                    elif button_pin == BTN_ROBLOX:
                        toggle_roblox()
                button_states[button_pin] = current_state
        
        blocked = youtube_blocked()
        
        # Check if we should show button feedback (for 2 seconds after button press)
        show_button_feedback = (button_pressed is not None and 
                              current_time - button_press_time < 2.0)
        
        # Check if we should show status confirmation (for 3 seconds after status change)
        show_status_confirmation = (status_change_confirmed and 
                                  current_time - status_change_time < 3.0)
        
        # Handle status changes
        if blocked != last_state:
            if last_state is not None:  # Don't show confirmation on first run
                status_change_confirmed = True
                status_change_time = current_time
            last_state = blocked
            # Clear button feedback when status actually changes
            button_pressed = None
        
        # Clear button feedback after timeout
        if button_pressed is not None and current_time - button_press_time >= 2.0:
            button_pressed = None
        
        # Clear status confirmation after timeout
        if status_change_confirmed and current_time - status_change_time >= 3.0:
            status_change_confirmed = False
        
        # Draw the appropriate display
        if show_button_feedback:
            draw(blocked, show_button_feedback=True)
        elif show_status_confirmation:
            draw(blocked, show_status_confirmation=True)
        else:
            draw(blocked)  # normal display
        
        time.sleep(0.2)  # Snappier refresh for button feedback without heavy CPU

if __name__ == "__main__":
    main()
