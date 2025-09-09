#!/usr/bin/env python3
import time, digitalio, board, sys
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
GREEN=(0,180,0); RED=(200,0,0); WHITE=(255,255,255); BLUE=(0,100,200)
def font_big():
    try:
        return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 18)
    except Exception:
        return ImageFont.load_default()
FB = font_big(); FS = ImageFont.load_default()

def draw(title, color):
    img = Image.new("RGB", (IMG_W, IMG_H), color)
    d = ImageDraw.Draw(img)
    try:
        bbox = d.textbbox((0,0), title, font=FB); tw=bbox[2]-bbox[0]; th=bbox[3]-bbox[1]
    except AttributeError:
        tw, th = d.textsize(title, font=FB)
    d.text(((IMG_W - tw)//2, 22), title, font=FB, fill=WHITE)
    disp.image(img)

# --- GPIO (polling) ---
BTN_BLOCK=23  # bottom
BTN_ALLOW=24  # top
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.setup(BTN_BLOCK, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(BTN_ALLOW, GPIO.IN, pull_up_down=GPIO.PUD_UP)

print("[LIVE] ready: bottom=GPIO23 (BLOCK), top=GPIO24 (ALLOW)", flush=True)
draw("BUTTON TEST", BLUE)

last_ms=0
debounce=150  # ms
try:
    while True:
        now_ms = int(time.time()*1000)

        if GPIO.input(BTN_BLOCK) == 0 and now_ms - last_ms > debounce:
            print("[LIVE] BLOCK pressed", flush=True)
            draw("BUTTON 23 PRESSED", RED)
            last_ms = now_ms

        elif GPIO.input(BTN_ALLOW) == 0 and now_ms - last_ms > debounce:
            print("[LIVE] ALLOW pressed", flush=True)
            draw("BUTTON 24 PRESSED", GREEN)
            last_ms = now_ms

        time.sleep(0.02)
except KeyboardInterrupt:
    GPIO.cleanup([BTN_BLOCK, BTN_ALLOW])
    print("\n[LIVE] bye", flush=True)
