# Enhanced tft-youtube-status.py with dual button functionality
# Button 1: Toggle YouTube/Roblox blocking
# Button 2: Kill active sessions

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

# ----------------------------
# Colors & Fonts
# ----------------------------
GREEN = (0,180,0)
RED   = (200,0,0)
WHITE = (255,255,255)
BLACK = (0,0,0)
BLUE  = (0,100,200)
YELLOW = (255,255,0)
ORANGE = (255,165,0)
PURPLE = (128,0,128)

def font_big():
    try:
        return ImageFont.truetype(
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 18
        )
    except Exception:
        return ImageFont.load_default()

def font_small():
    try:
        return ImageFont.truetype(
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 12
        )
    except Exception:
        return ImageFont.load_default()

FB = font_big()
FS = font_small()

# ----------------------------
# GPIO Buttons (Mini PiTFT has 2)
# ----------------------------
BTN_TOGGLE = 23   # left/front button - Toggle YouTube/Roblox
BTN_KILL = 24     # right/front button - Kill active sessions

GPIO.setmode(GPIO.BCM)
GPIO.setup(BTN_TOGGLE, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(BTN_KILL, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# Global variables for button feedback
button_pressed = None
button_press_time = 0
status_change_confirmed = False
status_change_time = 0
active_sessions = {'youtube': 0, 'roblox': 0, 'total': 0}
sessions_killed = 0

def toggle_youtube_roblox(_ch=None):
    """Button 1: Toggle YouTube/Roblox blocking"""
    global button_pressed, button_press_time
    button_pressed = "toggling"
    button_press_time = time.time()
    # Run the actual command in a separate thread to avoid blocking
    threading.Thread(target=lambda: subprocess.call(["/usr/local/bin/yb" if youtube_blocked() else "/usr/local/bin/yu"]), daemon=True).start()

def kill_active_sessions(_ch=None):
    """Button 2: Kill all active sessions"""
    global button_pressed, button_press_time, sessions_killed
    button_pressed = "killing"
    button_press_time = time.time()
    sessions_killed = 0
    
    def kill_sessions():
        global sessions_killed
        try:
            # Get active sessions
            result = subprocess.run(
                ["python3", "/home/zerocool/session_monitor.py", "list"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                output = result.stdout.strip()
                if "Active sessions:" in output:
                    lines = output.split('\n')[1:]  # Skip header
                    for line in lines:
                        if line.strip().startswith('- '):
                            # Extract client IP from line like "- 192.168.1.100: YouTube"
                            parts = line.strip().split(':')
                            if len(parts) >= 2:
                                client_ip = parts[0].replace('- ', '').strip()
                                # Terminate the session
                                kill_result = subprocess.run(
                                    ["python3", "/home/zerocool/session_monitor.py", "terminate", client_ip],
                                    capture_output=True,
                                    text=True,
                                    timeout=10
                                )
                                if kill_result.returncode == 0:
                                    sessions_killed += 1
                                    print(f"Killed session for {client_ip}")
        except Exception as e:
            print(f"Error killing sessions: {e}")
    
    # Run session killing in a separate thread
    threading.Thread(target=kill_sessions, daemon=True).start()

GPIO.add_event_detect(BTN_TOGGLE, GPIO.FALLING, callback=toggle_youtube_roblox, bouncetime=300)
GPIO.add_event_detect(BTN_KILL, GPIO.FALLING, callback=kill_active_sessions, bouncetime=300)

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
    """Check if Roblox is blocked by testing a Roblox domain"""
    try:
        result = subprocess.run(
            ["pihole", "-q", "roblox.com"], 
            capture_output=True, 
            text=True, 
            timeout=5
        )
        return "BLOCKED" in result.stdout
    except Exception:
        return True  # fail safe: assume blocked

def scratch_accessible() -> bool:
    """Check if Scratch is accessible by testing a Scratch domain"""
    try:
        result = subprocess.run(
            ["pihole", "-q", "scratch.mit.edu"], 
            capture_output=True, 
            text=True, 
            timeout=5
        )
        return "OK" in result.stdout
    except Exception:
        return False  # fail safe: assume blocked

def get_active_sessions():
    """Get active session counts from session monitor"""
    global active_sessions
    try:
        # Run session monitor to get current status
        result = subprocess.run(
            ["python3", "/home/zerocool/session_monitor.py", "status"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            output = result.stdout.strip()
            # Parse the output to extract session counts
            if "YouTube:" in output:
                youtube_part = output.split("YouTube:")[1].split()[0]
                active_sessions['youtube'] = int(youtube_part) if youtube_part.isdigit() else 0
            if "Roblox:" in output:
                roblox_part = output.split("Roblox:")[1].split()[0]
                active_sessions['roblox'] = int(roblox_part) if roblox_part.isdigit() else 0
            if "Active sessions:" in output:
                total_part = output.split("Active sessions:")[1].split()[0]
                active_sessions['total'] = int(total_part) if total_part.isdigit() else 0
                
    except Exception as e:
        print(f"Error getting session status: {e}")
        # Keep existing values on error

def draw(blocked: bool, show_button_feedback=False, show_status_confirmation=False):
    global button_pressed, button_press_time, status_change_confirmed, status_change_time, active_sessions, sessions_killed
    
    # Get current status of all services
    youtube_status = blocked
    roblox_status = roblox_blocked()
    scratch_status = scratch_accessible()
    
    # Determine background color and title
    if show_button_feedback:
        if button_pressed == "toggling":
            # Show blue background when toggling
            bg_color = BLUE
            text_color = WHITE
            title = "TOGGLING..."
        elif button_pressed == "killing":
            # Show purple background when killing sessions
            bg_color = PURPLE
            text_color = WHITE
            title = "KILLING SESSIONS..."
    elif show_status_confirmation:
        # Show yellow background for confirmation
        bg_color = YELLOW
        text_color = BLACK  # Black text on yellow background
        if sessions_killed > 0:
            title = f"KILLED {sessions_killed} SESSIONS!"
        else:
            title = "STATUS CHANGED!"
    else:
        # Normal status display - show primary service status
        bg_color = RED if youtube_status else GREEN
        text_color = WHITE
        title = "YouTube BLOCKED" if youtube_status else "YouTube ALLOWED"
    
    img = Image.new("RGB", (W, H), color=bg_color)
    d = ImageDraw.Draw(img)
    
    # Centered title (new Pillow uses textbbox, fallback textsize)
    try:
        bbox = d.textbbox((0, 0), title, font=FB)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    except AttributeError:
        tw, th = d.textsize(title, font=FB)
    d.text(((W - tw)//2, 22), title, font=FB, fill=text_color)
    
    # Add dots for button feedback
    if show_button_feedback:
        dots = "..." + ("." * int((time.time() - button_press_time) * 2))[:3]
        try:
            bbox = d.textbbox((0, 0), dots, font=FS)
            dw, dh = bbox[2] - bbox[0], bbox[3] - bbox[1]
        except AttributeError:
            dw, dh = d.textsize(dots, font=FS)
        d.text(((W - dw)//2, 50), dots, font=FS, fill=text_color)
    
    # Add confirmation message
    if show_status_confirmation:
        if sessions_killed > 0:
            confirm_msg = f"✓ {sessions_killed} SESSIONS TERMINATED"
        else:
            confirm_msg = "✓ DONE"
        try:
            bbox = d.textbbox((0, 0), confirm_msg, font=FS)
            cw, ch = bbox[2] - bbox[0], bbox[3] - bbox[1]
        except AttributeError:
            cw, ch = d.textsize(confirm_msg, font=FS)
        d.text(((W - cw)//2, 50), confirm_msg, font=FS, fill=text_color)
    
    # Add status indicators for other services (only in normal display mode)
    if not show_button_feedback and not show_status_confirmation:
        y_pos = 50
        
        # Show Roblox status
        roblox_text = "Roblox: " + ("BLOCKED" if roblox_status else "ALLOWED")
        try:
            bbox = d.textbbox((0, 0), roblox_text, font=FS)
            rw, rh = bbox[2] - bbox[0], bbox[3] - bbox[1]
        except AttributeError:
            rw, rh = d.textsize(roblox_text, font=FS)
        d.text(((W - rw)//2, y_pos), roblox_text, font=FS, fill=text_color)
        y_pos += 20
        
        # Show Scratch status
        scratch_text = "Scratch: " + ("OK" if scratch_status else "BLOCKED!")
        scratch_color = text_color if scratch_status else YELLOW
        try:
            bbox = d.textbbox((0, 0), scratch_text, font=FS)
            sw, sh = bbox[2] - bbox[0], bbox[3] - bbox[1]
        except AttributeError:
            sw, sh = d.textsize(scratch_text, font=FS)
        d.text(((W - sw)//2, y_pos), scratch_text, font=FS, fill=scratch_color)
        y_pos += 20
        
        # Show active sessions if any
        if active_sessions['total'] > 0:
            session_text = f"Active: YT:{active_sessions['youtube']} RB:{active_sessions['roblox']}"
            session_color = ORANGE if active_sessions['total'] > 0 else text_color
            try:
                bbox = d.textbbox((0, 0), session_text, font=FS)
                sw, sh = bbox[2] - bbox[0], bbox[3] - bbox[1]
            except AttributeError:
                sw, sh = d.textsize(session_text, font=FS)
            d.text(((W - sw)//2, y_pos), session_text, font=FS, fill=session_color)
            y_pos += 20
        
        # Show button instructions
        button_text = "BTN1:Toggle BTN2:Kill"
        try:
            bbox = d.textbbox((0, 0), button_text, font=FS)
            bw, bh = bbox[2] - bbox[0], bbox[3] - bbox[1]
        except AttributeError:
            bw, bh = d.textsize(button_text, font=FS)
        d.text(((W - bw)//2, y_pos), button_text, font=FS, fill=text_color)
    
    # Clock at bottom
    d.text((6, H-18), datetime.now().strftime("%Y-%m-%d %H:%M:%S"), font=FS, fill=text_color)
    disp.image(img)

# ----------------------------
# Main loop
# ----------------------------
def main():
    global button_pressed, button_press_time, status_change_confirmed, status_change_time, active_sessions, sessions_killed
    
    last_state = None
    last_session_check = 0
    
    while True:
        current_time = time.time()
        blocked = youtube_blocked()
        
        # Check for active sessions every 30 seconds
        if current_time - last_session_check > 30:
            get_active_sessions()
            last_session_check = current_time
        
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
            sessions_killed = 0  # Reset session kill count
        
        # Draw the appropriate display
        if show_button_feedback:
            draw(blocked, show_button_feedback=True)
        elif show_status_confirmation:
            draw(blocked, show_status_confirmation=True)
        else:
            draw(blocked)  # normal display
        
        time.sleep(0.5)  # Faster refresh for better responsiveness

if __name__ == "__main__":
    main()
