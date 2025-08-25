ok starting a new thread for memory reasons. Here's a summary of what we've done so far:

here’s a compact but detailed summary of everything we set up, so you can paste it into a new thread and we’ll pick up smoothly:

📋 Pi-hole + Mini PiTFT Project Summary
Hardware / OS

Raspberry Pi Zero WH running Raspberry Pi OS (Bookworm Lite).

Adafruit Mini PiTFT 135×240 ST7789 (with 2 buttons).

Using pitft-venv virtual environment for Python libs.

Pi-hole Setup

Pi-hole installed and working on 192.168.1.167.

DNS configured manually on AppleTV, iPad, etc.

Created custom group KidsRestricted with regex rules to block YouTube domains (youtube.com, googlevideo.com, etc.).

Devices (AppleTV + iPad) assigned to KidsRestricted group.

Scheduling

Added cron jobs for group toggling:

12:00 PM daily → unblock YouTube

9:00 PM daily → block YouTube

Verified working with sqlite3 + pihole reloadlists + systemctl restart pihole-FTL.

Quick Commands (aliases)

Created shortcuts in /usr/local/bin (with sudoers NOPASSWD rules) so user zerocool can run without password:

yb → Block YouTube

yu → Unblock YouTube

ys → Status (YouTube currently BLOCKED/ALLOWED)

Mini PiTFT Status Screen

Python script: ~/tft-youtube-status.py

Shows YouTube BLOCKED (red) or ALLOWED (green).

Displays live clock at bottom.

Polls Pi-hole gravity.db every 5s via sqlite3.

Rotation settable via disp.rotation = 90 or 270.

Service: tft-youtube.service runs it at boot using venv’s Python.

Buttons (GPIO 23 & 24)

Left button → run yb (block).

Right button → run yu (unblock).

Added RPi.GPIO event handlers in script.

_clean_exit handles Ctrl+C cleanly and calls GPIO.cleanup().

Verified mapping with test script (prints when pressed).

Outstanding / Next Goals

Confirm correct rotation value so text fits screen (90 vs 270).

Ensure buttons correctly mapped to GPIO 23/24 (double-check with tester).

Add PIN-unlock feature later (temporary unblock for 15 mins).

Optionally: Mac desktop shortcuts (ssh zerocool@pi-hole.local yb/yu/ys) for quick toggling.

👉 With this summary, we can start the next thread right where we left off: fine-tuning the TFT rotation and button handling.

Would you like me to also include the latest full script version (with status, clock, rotation, GPIO buttons, clean exit) so you have a single “master copy” to paste into the new thread?

You said:
yes please do that - I was losing track and wanted a new copy of the latest script anyway
ChatGPT said:

Perfect 👍 — here’s the latest master copy of your tft-youtube-status.py.
This version includes:

Rotation setting (adjustable: try 270 first, or switch to 90 if text is sideways).

Red/green screen with big centered YouTube BLOCKED/ALLOWED text.

Clock at the bottom.

Polling Pi-hole’s gravity.db every 5s.

Button support:

GPIO 23 = Block (yb)

GPIO 24 = Unblock (yu)

Clean exit handler (Ctrl+C or service stop = no traceback, cleans GPIO).

~/tft-youtube-status.py
import time, subprocess, sys, signal
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

# ----------------------------
# Colors & Fonts
# ----------------------------
GREEN = (0,180,0)
RED   = (200,0,0)
WHITE = (255,255,255)
BLACK = (0,0,0)

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

def block_youtube(_ch=None):
    subprocess.call(["/usr/local/bin/yb"])

def allow_youtube(_ch=None):
    subprocess.call(["/usr/local/bin/yu"])

GPIO.add_event_detect(BTN_BLOCK, GPIO.FALLING, callback=block_youtube, bouncetime=300)
GPIO.add_event_detect(BTN_ALLOW, GPIO.FALLING, callback=allow_youtube, bouncetime=300)

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

def draw(blocked: bool):
    img = Image.new("RGB", (W, H), color=RED if blocked else GREEN)
    d = ImageDraw.Draw(img)
    title = "YouTube BLOCKED" if blocked else "YouTube ALLOWED"
    # Centered title (new Pillow uses textbbox, fallback textsize)
    try:
        bbox = d.textbbox((0, 0), title, font=FB)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    except AttributeError:
        tw, th = d.textsize(title, font=FB)
    d.text(((W - tw)//2, 22), title, font=FB, fill=WHITE)
    # Clock at bottom
    d.text((6, H-18), datetime.now().strftime("%Y-%m-%d %H:%M:%S"), font=FS, fill=WHITE)
    disp.image(img)

# ----------------------------
# Main loop
# ----------------------------
def main():
    last_state = None
    while True:
        blocked = youtube_blocked()
        if blocked != last_state:
            draw(blocked)
            last_state = blocked
        else:
            draw(blocked)  # refresh time
        time.sleep(5)

if __name__ == "__main__":
    main()


✅ With this in place, you can:

Use your cron jobs (12 PM unblock / 9 PM block).

Use your quick commands (yb, yu, ys).

Press the TFT buttons to toggle block/unblock instantly.

Watch the status update every ~5 seconds on the display.

Run as a service so it auto-starts on boot.

Would you like me to also include the systemd service file (final version) in your summary, so you have one complete package to paste into your new thread?

You said:
yes
ChatGPT said:

Awesome — here’s the final systemd service you can paste into your new thread. It runs your TFT script at boot using your venv’s Python, restarts if it crashes, and doesn’t require you to activate the venv manually.

tft-youtube.service (copy/paste exactly)
sudo tee /etc/systemd/system/tft-youtube.service >/dev/null <<'EOF'
[Unit]
Description=PiTFT YouTube Status (red=BLOCKED, green=ALLOWED)
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
# Use the Python inside your venv so Pillow/Blinka/etc are available
ExecStart=/home/zerocool/pitft-venv/bin/python3 /home/zerocool/tft-youtube-status.py
WorkingDirectory=/home/zerocool
User=zerocool
Group=zerocool
Restart=always
RestartSec=3

# Optional: slightly nicer environment (no need to edit these)
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
EOF

Enable + start it now
sudo systemctl daemon-reload
sudo systemctl enable --now tft-youtube.service

Useful commands
# Check status (q to exit if it pages)
systemctl status tft-youtube.service --no-pager -l

# Follow logs live
journalctl -u tft-youtube.service -f

# Stop / start / restart
sudo systemctl stop tft-youtube.service
sudo systemctl start tft-youtube.service
sudo systemctl restart tft-youtube.service

Notes / tweaks

If your text is sideways or clipped, open ~/tft-youtube-status.py and switch:

disp.rotation = 270  # try 90 if needed


Then:

sudo systemctl restart tft-youtube.service


Your quick toggles still work from anywhere:

ys   # prints “YouTube currently BLOCKED/ALLOWED”
yb   # blocks (screen turns red within ~5s)
yu   # unblocks (screen turns green within ~5s)


Buttons on the Mini PiTFT:

GPIO 23 → yb (block)

GPIO 24 → yu (unblock)

That’s the whole package. Paste this + the script into your new thread and we can keep iterating (PIN unlock window next, if you want).