#!/usr/bin/env python3
import time, digitalio, board, sys, subprocess
import RPi.GPIO as GPIO
from PIL import Image, ImageDraw, ImageFont
from adafruit_rgb_display import st7789

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
        return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 18)
    except Exception:
        return ImageFont.load_default()
FB = font_big(); FS = ImageFont.load_default()

def draw(title, color, dots=""):
    img = Image.new("RGB", (IMG_W, IMG_H), color)
    d = ImageDraw.Draw(img)
    
    # Choose text color based on background
    text_color = BLACK if color == YELLOW else WHITE
    
    try:
        bbox = d.textbbox((0,0), title, font=FB); tw=bbox[2]-bbox[0]; th=bbox[3]-bbox[1]
    except AttributeError:
        tw, th = d.textsize(title, font=FB)
    d.text(((IMG_W - tw)//2, 22), title, font=FB, fill=text_color)
    
    # Add animated dots if provided
    if dots:
        try:
            bbox = d.textbbox((0,0), dots, font=FS); dw=bbox[2]-bbox[0]; dh=bbox[3]-bbox[1]
        except AttributeError:
            dw, dh = d.textsize(dots, font=FS)
        d.text(((IMG_W - dw)//2, 50), dots, font=FS, fill=text_color)
    
    disp.image(img)

# --- Pi-hole control functions ---
def block_youtube_roblox():
    """Block YouTube and Roblox domains using direct SQLite"""
    print("[LIVE] Blocking YouTube and Roblox...", flush=True)
    
    # Block YouTube domains
    youtube_domains = [
        "youtube.com", "www.youtube.com", "m.youtube.com", "youtu.be",
        "googlevideo.com", "ytimg.com", "youtube.googleapis.com"
    ]
    
    # Block Roblox domains  
    roblox_domains = [
        "roblox.com", "www.roblox.com", "rbxcdn.com", "rbxtrk.com",
        "ecsv2.roblox.com", "ncs.roblox.com", "client-telemetry.roblox.com"
    ]
    
    # Add to blacklist (type 1)
    for domain in youtube_domains + roblox_domains:
        subprocess.run([
            "sudo", "sqlite3", "/etc/pihole/gravity.db",
            f"INSERT OR IGNORE INTO domainlist (type, domain) VALUES (1, '{domain}');"
        ], check=False)
    
    # Ensure Scratch domains are whitelisted (type 0)
    scratch_domains = [
        "scratch.mit.edu", "api.scratch.mit.edu", "projects.scratch.mit.edu",
        "cdn.scratch.mit.edu", "cdn2.scratch.mit.edu"
    ]
    
    for domain in scratch_domains:
        subprocess.run([
            "sudo", "sqlite3", "/etc/pihole/gravity.db", 
            f"INSERT OR IGNORE INTO domainlist (type, domain) VALUES (0, '{domain}');"
        ], check=False)
    
    # Reload Pi-hole
    subprocess.run(["sudo", "pihole", "reloadlists"], check=False)

def allow_youtube_roblox():
    """Allow YouTube and Roblox domains using direct SQLite"""
    print("[LIVE] Allowing YouTube and Roblox...", flush=True)
    
    # Remove from blacklist
    youtube_domains = [
        "youtube.com", "www.youtube.com", "m.youtube.com", "youtu.be",
        "googlevideo.com", "ytimg.com", "youtubei.googleapis.com"
    ]
    
    roblox_domains = [
        "roblox.com", "www.roblox.com", "rbxcdn.com", "rbxtrk.com",
        "ecsv2.roblox.com", "ncs.roblox.com", "client-telemetry.roblox.com"
    ]
    
    for domain in youtube_domains + roblox_domains:
        subprocess.run([
            "sudo", "sqlite3", "/etc/pihole/gravity.db",
            f"DELETE FROM domainlist WHERE domain='{domain}' AND type=1;"
        ], check=False)
    
    # Keep Scratch whitelisted
    scratch_domains = [
        "scratch.mit.edu", "api.scratch.mit.edu", "projects.scratch.mit.edu",
        "cdn.scratch.mit.edu", "cdn2.scratch.mit.edu"
    ]
    
    for domain in scratch_domains:
        subprocess.run([
            "sudo", "sqlite3", "/etc/pihole/gravity.db",
            f"INSERT OR IGNORE INTO domainlist (type, domain) VALUES (0, '{domain}');"
        ], check=False)
    
    # Reload Pi-hole
    subprocess.run(["sudo", "pihole", "reloadlists"], check=False)

def get_status():
    """Get current blocking status"""
    try:
        # Check if YouTube is blocked
        result = subprocess.run([
            "sudo", "sqlite3", "/etc/pihole/gravity.db",
            "SELECT COUNT(*) FROM domainlist WHERE domain='youtube.com' AND type=1;"
        ], capture_output=True, text=True, check=True)
        youtube_blocked = result.stdout.strip() != "0"
        
        # Check if Roblox is blocked
        result = subprocess.run([
            "sudo", "sqlite3", "/etc/pihole/gravity.db", 
            "SELECT COUNT(*) FROM domainlist WHERE domain='roblox.com' AND type=1;"
        ], capture_output=True, text=True, check=True)
        roblox_blocked = result.stdout.strip() != "0"
        
        return youtube_blocked, roblox_blocked
    except Exception:
        return True, True  # fail safe

# --- GPIO (polling) ---
BTN_BLOCK=23  # bottom
BTN_ALLOW=24  # top
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.setup(BTN_BLOCK, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(BTN_ALLOW, GPIO.IN, pull_up_down=GPIO.PUD_UP)

print("[LIVE] ready: bottom=GPIO23 (BLOCK), top=GPIO24 (ALLOW)", flush=True)

# Initial status display
youtube_blocked, roblox_blocked = get_status()
if youtube_blocked and roblox_blocked:
    draw("BLOCKED", RED)
else:
    draw("ALLOWED", GREEN)

last_ms=0
debounce=50  # ms - faster response
feedback_time=0
feedback_shown=False
button_pressed=""
try:
    while True:
        now_ms = int(time.time()*1000)

        if GPIO.input(BTN_BLOCK) == 0 and now_ms - last_ms > debounce:
            print("[LIVE] BLOCK pressed", flush=True)
            # Instant feedback - yellow screen with animated dots
            draw("BLOCKING...", YELLOW, "...")
            feedback_time = now_ms
            feedback_shown = True
            button_pressed = "block"
            last_ms = now_ms

        elif GPIO.input(BTN_ALLOW) == 0 and now_ms - last_ms > debounce:
            print("[LIVE] ALLOW pressed", flush=True)
            # Instant feedback - yellow screen with animated dots
            draw("ALLOWING...", YELLOW, "...")
            feedback_time = now_ms
            feedback_shown = True
            button_pressed = "allow"
            last_ms = now_ms

        # Show animated dots during feedback
        if feedback_shown:
            elapsed = now_ms - feedback_time
            dot_count = min(3, elapsed // 200)  # Add dot every 200ms
            dots = "." * dot_count
            draw("BLOCKING..." if button_pressed == "block" else "ALLOWING...", YELLOW, dots)
            
            # Execute action after 1000ms
            if elapsed > 1000:
                if button_pressed == "block":
                    block_youtube_roblox()
                    draw("BLOCKED", RED)
                elif button_pressed == "allow":
                    allow_youtube_roblox()
                    draw("ALLOWED", GREEN)
                feedback_shown = False

        time.sleep(0.01)  # Faster polling
except KeyboardInterrupt:
    GPIO.cleanup([BTN_BLOCK, BTN_ALLOW])
    print("\n[LIVE] bye", flush=True)
