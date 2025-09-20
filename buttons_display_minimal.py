#!/usr/bin/env python3
import time
import digitalio, board
import RPi.GPIO as GPIO
from PIL import Image, ImageDraw, ImageFont
from adafruit_rgb_display import st7789

# Display init (Mini PiTFT 135x240, ST7789)
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

# Backlight control (GPIO22)
backlight = digitalio.DigitalInOut(board.D22)
backlight.switch_to_output()
backlight.value = True

# Colors
GREEN = (0,180,0)
RED   = (200,0,0)
YELLOW= (255,255,0)
BLACK = (0,0,0)
WHITE = (255,255,255)

try:
    FB = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 18)
except Exception:
    FB = ImageFont.load_default()
FS = ImageFont.load_default()

# Buttons
BTN_BLOCK = 23
BTN_ALLOW = 24
GPIO.setmode(GPIO.BCM)
GPIO.setup(BTN_BLOCK, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(BTN_ALLOW, GPIO.IN, pull_up_down=GPIO.PUD_UP)

last = {BTN_BLOCK: 1, BTN_ALLOW: 1}
last_ts = {BTN_BLOCK: 0.0, BTN_ALLOW: 0.0}
DEBOUNCE_S = 0.15

LOG_PATH = "/tmp/buttons-min.log"

def log_line(msg: str):
    try:
        with open(LOG_PATH, "a") as f:
            f.write(f"{time.strftime('%H:%M:%S')} {msg}\n")
    except Exception:
        pass


def draw(bg, title):
    img = Image.new("RGB", (IMG_W, IMG_H), color=bg)
    d = ImageDraw.Draw(img)
    try:
        bbox = d.textbbox((0, 0), title, font=FB)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    except AttributeError:
        tw, th = d.textsize(title, font=FB)
    d.text(((IMG_W - tw)//2, 18), title, font=FB, fill=BLACK if bg==YELLOW else WHITE)
    disp.image(img)


def blink_backlight():
    # Quick, SPI-independent visual cue
    backlight.value = False
    time.sleep(0.1)
    backlight.value = True


def main():
    # Start with neutral green screen
    draw(GREEN, "Ready")
    log_line("service started")
    try:
        while True:
            now = time.time()
            cur_b = GPIO.input(BTN_BLOCK)
            if cur_b != last[BTN_BLOCK]:
                if cur_b == 0 and now - last_ts[BTN_BLOCK] > DEBOUNCE_S:
                    last_ts[BTN_BLOCK] = now
                    t0 = time.time()
                    log_line("BLOCK press detected")
                    blink_backlight()
                    log_line("BLOCK backlight blinked")
                    draw(YELLOW, "BLOCK pressed")
                    log_line(f"BLOCK draw issued ({(time.time()-t0)*1000:.1f}ms since detect)")
                last[BTN_BLOCK] = cur_b

            cur_a = GPIO.input(BTN_ALLOW)
            if cur_a != last[BTN_ALLOW]:
                if cur_a == 0 and now - last_ts[BTN_ALLOW] > DEBOUNCE_S:
                    last_ts[BTN_ALLOW] = now
                    t0 = time.time()
                    log_line("ALLOW press detected")
                    blink_backlight()
                    log_line("ALLOW backlight blinked")
                    draw(YELLOW, "ALLOW pressed")
                    log_line(f"ALLOW draw issued ({(time.time()-t0)*1000:.1f}ms since detect)")
                last[BTN_ALLOW] = cur_a

            time.sleep(0.01)
    except KeyboardInterrupt:
        pass
    finally:
        GPIO.cleanup()
        log_line("service exit")


if __name__ == "__main__":
    main()
