#!/usr/bin/env python3
import time, os, threading
import digitalio, board
import RPi.GPIO as GPIO
from PIL import Image, ImageDraw, ImageFont
from adafruit_rgb_display import st7789
from adafruit_rgb_display.rgb import color565

# Single-instance guard
LOCK_PATH = "/tmp/buttons-min.lock"
_lock_fd = None
try:
    import fcntl  # POSIX only
    _lock_fd = os.open(LOCK_PATH, os.O_CREAT | os.O_RDWR, 0o644)
    fcntl.flock(_lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    os.write(_lock_fd, str(os.getpid()).encode())
except Exception:
    print("[buttons-min] another instance detected; exiting", flush=True)
    raise SystemExit(0)

# Display init (Mini PiTFT 135x240, ST7789)
BAUDRATE = 24_000_000
disp = st7789.ST7789(
    board.SPI(),
    cs=digitalio.DigitalInOut(board.CE0),
    dc=digitalio.DigitalInOut(board.D25),
    rst=None,
    baudrate=BAUDRATE,
    width=135, height=240, x_offset=53, y_offset=40
)
disp.rotation = 270
IMG_W, IMG_H = disp.height, disp.width

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

# Render thread state
_render_lock = threading.Lock()
_render_thread = None
_latest_title = None
_latest_bg = None
_render_version = 0


def log_line(msg: str):
    try:
        with open(LOG_PATH, "a") as f:
            f.write(f"{time.strftime('%H:%M:%S')} {msg}\n")
    except Exception:
        pass


def disp_fill(color_tuple):
    try:
        disp.fill(color565(color_tuple[0], color_tuple[1], color_tuple[2]))
    except Exception:
        img = Image.new("RGB", (IMG_W, IMG_H), color=color_tuple)
        disp.image(img)


def render_and_draw_once(title: str, bg):
    t0 = time.time()
    img = Image.new("RGB", (IMG_W, IMG_H), color=bg)
    t1 = time.time()
    d = ImageDraw.Draw(img)
    try:
        bbox = d.textbbox((0, 0), title, font=FB)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    except AttributeError:
        tw, th = d.textsize(title, font=FB)
    d.text(((IMG_W - tw)//2, 18), title, font=FB, fill=BLACK if bg==YELLOW else WHITE)
    t2 = time.time()
    disp.image(img)
    t3 = time.time()
    log_line(f"render profile: create={(t1-t0)*1000:.1f}ms text={(t2-t1)*1000:.1f}ms image={(t3-t2)*1000:.1f}ms total={(t3-t0)*1000:.1f}ms")


def _render_worker(start_version: int):
    global _render_thread
    while True:
        with _render_lock:
            version = _render_version
            title = _latest_title
            bg = _latest_bg
        if title is None:
            break
        render_and_draw_once(title, bg)
        with _render_lock:
            # If no newer request came in during render, exit
            if version == _render_version:
                _latest_title = None
                _latest_bg = None
                break
    _render_thread = None


def schedule_render(title: str, bg):
    global _render_thread, _render_version, _latest_title, _latest_bg
    with _render_lock:
        _latest_title = title
        _latest_bg = bg
        _render_version += 1
        need_start = _render_thread is None
    if need_start:
        t = threading.Thread(target=_render_worker, args=(_render_version,), daemon=True)
        _render_thread = t
        t.start()


def blink_backlight():
    backlight.value = False
    time.sleep(0.1)
    backlight.value = True


def main():
    schedule_render("Ready", GREEN)
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
                    disp_fill(YELLOW)
                    log_line(f"BLOCK fill issued ({(time.time()-t0)*1000:.1f}ms since detect)")
                    schedule_render("BLOCK pressed", YELLOW)
                last[BTN_BLOCK] = cur_b

            cur_a = GPIO.input(BTN_ALLOW)
            if cur_a != last[BTN_ALLOW]:
                if cur_a == 0 and now - last_ts[BTN_ALLOW] > DEBOUNCE_S:
                    last_ts[BTN_ALLOW] = now
                    t0 = time.time()
                    log_line("ALLOW press detected")
                    blink_backlight()
                    log_line("ALLOW backlight blinked")
                    disp_fill(YELLOW)
                    log_line(f"ALLOW fill issued ({(time.time()-t0)*1000:.1f}ms since detect)")
                    schedule_render("ALLOW pressed", YELLOW)
                last[BTN_ALLOW] = cur_a

            time.sleep(0.01)
    except KeyboardInterrupt:
        pass
    finally:
        GPIO.cleanup()
        log_line("service exit")
        try:
            if _lock_fd is not None:
                fcntl.flock(_lock_fd, fcntl.LOCK_UN)
                os.close(_lock_fd)
                os.remove(LOCK_PATH)
        except Exception:
            pass


if __name__ == "__main__":
    main()
