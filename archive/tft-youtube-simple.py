import time, subprocess
from datetime import datetime
import digitalio, board
from PIL import Image, ImageDraw, ImageFont
from adafruit_rgb_display import st7789

# --- Display init (Mini PiTFT 135x240, ST7789) ---
disp = st7789.ST7789(
    board.SPI(),
    cs=digitalio.DigitalInOut(board.CE0),
    dc=digitalio.DigitalInOut(board.D25),
    rst=None,
    baudrate=64_000_000,
    width=135, height=240, x_offset=53, y_offset=40
)
W, H = disp.width, disp.height

# Colors
GREEN = (0,180,0)
RED   = (200,0,0)
WHITE = (255,255,255)
BLACK = (0,0,0)

def font_big():
    try:
        return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 18)
    except Exception:
        return ImageFont.load_default()
FB = font_big()
FS = ImageFont.load_default()

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
    # Center title (supporting both new and old Pillow)
    try:
        bbox = d.textbbox((0, 0), title, font=FB)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    except AttributeError:
        tw, th = d.textsize(title, font=FB)
    d.text(((W - tw)//2, 22), title, font=FB, fill=WHITE)
    # Small clock at bottom
    d.text((6, H-18), datetime.now().strftime("%Y-%m-%d %H:%M:%S"), font=FS, fill=WHITE)
    disp.image(img)

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
