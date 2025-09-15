#!/usr/bin/env python3
import time, digitalio, board, sys, subprocess, signal, os
import RPi.GPIO as GPIO
from PIL import Image, ImageDraw, ImageFont
from adafruit_rgb_display import st7789
from datetime import datetime

# --- Display (your proven params) ---
disp = st7789.ST7789(
    board.SPI(),
    cs=digitalio.DigitalInOut(board.CE0),
    dc=digitalio.DigitalInOut(board.D25),
    rst=None,
    baudrate=64_000_000,
    width=135, height=240,
    x_offset=53, y_offset=40
)
disp.rotation = 270
try: 
    disp.fill(0)
except Exception: 
    pass

# Draw using swapped size found by probe: 240x135
IMG_W, IMG_H = disp.height, disp.width  # 240x135
print(f"[LIVE] driver={disp.width}x{disp.height} image={IMG_W}x{IMG_H} rotation={disp.rotation}", flush=True)

# --- Colors & fonts ---
GREEN=(0,180,0); RED=(200,0,0); WHITE=(255,255,255); BLACK=(0,0,0); BLUE=(0,100,200); YELLOW=(255,255,0)

def font_big():
    try:
        return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 20)
    except:
        return ImageFont.load_default()

def font_small():
    try:
        return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 12)
    except:
        return ImageFont.load_default()

FB = font_big()
FS = font_small()

# --- GPIO Setup ---
BTN_BLOCK = 23  # Bottom button
BTN_ALLOW = 24  # Top button
GPIO.setmode(GPIO.BCM)
GPIO.setup(BTN_BLOCK, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(BTN_ALLOW, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# --- Button state tracking ---
button_states = {BTN_BLOCK: True, BTN_ALLOW: True}  # True = not pressed (pull-up)
last_button_time = {BTN_BLOCK: 0, BTN_ALLOW: 0}
DEBOUNCE_TIME = 200  # ms

# --- Animation state ---
animation_frame = 0
last_animation_time = 0
last_status_check = 0
STATUS_CHECK_INTERVAL = 2  # Check status every 2 seconds

# --- Signal handling for graceful shutdown ---
def signal_handler(signum, frame):
    print(f"\n[LIVE] Received signal {signum}, shutting down gracefully...", flush=True)
    try:
        disp.fill(0)  # Clear display
    except:
        pass
    GPIO.cleanup()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

def get_blocking_status():
    """Check if YouTube and Roblox are currently blocked"""
    try:
        # Check YouTube directly in database
        result = subprocess.run(['sudo', 'sqlite3', '/etc/pihole/gravity.db', 
                               "SELECT COUNT(*) FROM domainlist WHERE domain='youtube.com' AND type=1;"],
                              capture_output=True, text=True, timeout=3)
        youtube_blocked = result.stdout.strip() == '1'
        
        # Check Roblox directly in database
        result = subprocess.run(['sudo', 'sqlite3', '/etc/pihole/gravity.db', 
                               "SELECT COUNT(*) FROM domainlist WHERE domain='roblox.com' AND type=1;"],
                              capture_output=True, text=True, timeout=3)
        roblox_blocked = result.stdout.strip() == '1'
        
        return youtube_blocked, roblox_blocked
    except Exception as e:
        print(f"[LIVE] Error checking status: {e}", flush=True)
        return True, True  # Assume blocked on error

def block_domains():
    """Block YouTube and Roblox domains"""
    print("[LIVE] Blocking YouTube and Roblox...", flush=True)
    try:
        # Block YouTube and Roblox
        subprocess.run(['sudo', 'sqlite3', '/etc/pihole/gravity.db', 
                       "INSERT OR IGNORE INTO domainlist (type, domain) VALUES (1, 'youtube.com'), (1, 'roblox.com');"],
                      timeout=10)
        # Reload Pi-hole
        subprocess.run(['sudo', 'pihole', 'reloadlists'], timeout=10)
        print("[LIVE] Domains blocked successfully", flush=True)
    except Exception as e:
        print(f"[LIVE] Error blocking domains: {e}", flush=True)

def unblock_domains():
    """Unblock YouTube and Roblox domains"""
    print("[LIVE] Allowing YouTube and Roblox...", flush=True)
    try:
        # Unblock YouTube and Roblox
        subprocess.run(['sudo', 'sqlite3', '/etc/pihole/gravity.db', 
                       "DELETE FROM domainlist WHERE domain IN ('youtube.com', 'roblox.com') AND type=1;"],
                      timeout=10)
        # Reload Pi-hole
        subprocess.run(['sudo', 'pihole', 'reloadlists'], timeout=10)
        print("[LIVE] Domains unblocked successfully", flush=True)
    except Exception as e:
        print(f"[LIVE] Error unblocking domains: {e}", flush=True)

def draw_status(youtube_blocked, roblox_blocked, show_animation=False):
    """Draw the current status on the display"""
    global animation_frame
    
    # Determine background color
    if youtube_blocked and roblox_blocked:
        bg_color = RED
        status_text = "BLOCKED"
    else:
        bg_color = GREEN  
        status_text = "ALLOWED"
    
    # Create image
    img = Image.new("RGB", (IMG_W, IMG_H), color=bg_color)
    d = ImageDraw.Draw(img)
    
    # Text color (black on yellow, white on others)
    text_color = BLACK if bg_color == YELLOW else WHITE
    
    # Main status (compact layout for small screen)
    d.text((5, 5), "YouTube & Roblox", font=FB, fill=text_color)
    d.text((5, 30), status_text, font=FB, fill=text_color)
    
    # Individual status (smaller font)
    d.text((5, 55), f"YT: {'BLOCKED' if youtube_blocked else 'ALLOWED'}", font=FS, fill=text_color)
    d.text((5, 70), f"RB: {'BLOCKED' if roblox_blocked else 'ALLOWED'}", font=FS, fill=text_color)
    
    # Animated clock/dots to show system is alive
    now = datetime.now()
    time_str = now.strftime("%H:%M:%S")
    d.text((5, 90), time_str, font=FS, fill=text_color)
    
    # Animated dots
    if show_animation:
        dots = "." * ((animation_frame % 4) + 1)
        d.text((5, 105), f"ALIVE{dots}", font=FS, fill=text_color)
    else:
        d.text((5, 105), "ALIVE", font=FS, fill=text_color)
    
    # Button labels (at very bottom)
    d.text((5, IMG_H-15), "B23:BLOCK B24:ALLOW", font=FS, fill=text_color)
    
    disp.image(img)

def draw_toggling_feedback(message):
    """Draw yellow toggling feedback screen"""
    global animation_frame
    
    # Create yellow background
    img = Image.new("RGB", (IMG_W, IMG_H), color=YELLOW)
    d = ImageDraw.Draw(img)
    
    # Black text on yellow background
    text_color = BLACK
    
    # Main message
    d.text((5, 20), message, font=FB, fill=text_color)
    
    # Animated dots
    dots = "." * ((animation_frame % 4) + 1)
    d.text((5, 50), f"Please wait{dots}", font=FS, fill=text_color)
    
    # Clock
    now = datetime.now()
    time_str = now.strftime("%H:%M:%S")
    d.text((5, 80), time_str, font=FS, fill=text_color)
    
    disp.image(img)

def main():
    global animation_frame, last_animation_time, last_status_check
    
    print("[LIVE] ready: bottom=GPIO23 (BLOCK), top=GPIO24 (ALLOW)", flush=True)
    
    # Initial status check
    youtube_blocked, roblox_blocked = get_blocking_status()
    draw_status(youtube_blocked, roblox_blocked)
    
    try:
        while True:
            current_time = int(time.time() * 1000)
            
            # Check for button presses (polling with debounce)
            for button_pin in [BTN_BLOCK, BTN_ALLOW]:
                current_state = GPIO.input(button_pin)
                if current_state != button_states[button_pin]:  # State changed
                    if current_state == False and current_time - last_button_time[button_pin] > DEBOUNCE_TIME:
                        # Button pressed (False = pressed due to pull-up)
                        last_button_time[button_pin] = current_time
                        
                        if button_pin == BTN_BLOCK:
                            print("[LIVE] BLOCK pressed", flush=True)
                            # Show immediate yellow feedback
                            draw_toggling_feedback("BLOCKING...")
                            block_domains()
                        elif button_pin == BTN_ALLOW:
                            print("[LIVE] ALLOW pressed", flush=True)
                            # Show immediate yellow feedback
                            draw_toggling_feedback("ALLOWING...")
                            unblock_domains()
                        
                        # Update status after action
                        youtube_blocked, roblox_blocked = get_blocking_status()
                        draw_status(youtube_blocked, roblox_blocked)
                    
                    button_states[button_pin] = current_state
            
            # Periodic status check (every 2 seconds)
            if current_time - last_status_check > STATUS_CHECK_INTERVAL * 1000:
                youtube_blocked, roblox_blocked = get_blocking_status()
                draw_status(youtube_blocked, roblox_blocked, show_animation=True)
                last_status_check = current_time
            
            # Animation update (every 500ms)
            if current_time - last_animation_time > 500:
                animation_frame += 1
                youtube_blocked, roblox_blocked = get_blocking_status()
                draw_status(youtube_blocked, roblox_blocked, show_animation=True)
                last_animation_time = current_time
            
            time.sleep(0.01)  # Small delay to prevent excessive CPU usage
            
    except KeyboardInterrupt:
        print("\n[LIVE] Interrupted by user", flush=True)
    except Exception as e:
        print(f"[LIVE] Unexpected error: {e}", flush=True)
    finally:
        try:
            disp.fill(0)  # Clear display
        except:
            pass
        GPIO.cleanup()

if __name__ == "__main__":
    main()
