#!/usr/bin/env python3
import time
from datetime import datetime
import sqlite3
import json, os, threading, signal
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
disp.rotation = 270
W, H = disp.width, disp.height
# For this ST7789, draw at swapped dimensions (240x135)
IMG_W, IMG_H = disp.height, disp.width

# Colors
GREEN = (0,180,0)
RED   = (200,0,0)
WHITE = (255,255,255)
YELLOW = (255,255,0)
BLACK = (0,0,0)

try:
    FB = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 18)
except Exception:
    FB = ImageFont.load_default()
FS = ImageFont.load_default()

DB_PATH = "/etc/pihole/gravity.db"
DB_POLL_INTERVAL_S = 2.0
UI_HINT_PATH = "/tmp/pitft_ui.json"

_state_lock = threading.Lock()
_last_blocked_state = True
_sigusr1_flag = False


def read_ui_hint():
    if not os.path.exists(UI_HINT_PATH):
        return None
    try:
        with open(UI_HINT_PATH) as f:
            data = json.load(f)
            if isinstance(data, dict):
                return data
    except Exception:
        return {"mode": "toggling", "msg": "TOGGLING..."}
    return None


def query_kids_restricted_enabled() -> bool:
    # Very short timeout to avoid blocking UI
    try:
        conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True, timeout=0.05)
        try:
            conn.execute("PRAGMA busy_timeout=50")
            cursor = conn.execute("SELECT enabled FROM 'group' WHERE name='KidsRestricted';")
            row = cursor.fetchone()
            if not row:
                return True
            return int(row[0]) == 1
        finally:
            conn.close()
    except Exception:
        return _last_blocked_state


def db_poll_worker():
    global _last_blocked_state
    while True:
        new_state = query_kids_restricted_enabled()
        with _state_lock:
            _last_blocked_state = new_state
        time.sleep(DB_POLL_INTERVAL_S)


def get_cached_blocked() -> bool:
    with _state_lock:
        return _last_blocked_state


def draw_overlay_toggling(message: str):
    try:
        img = Image.new("RGB", (IMG_W, IMG_H), color=YELLOW)
        d = ImageDraw.Draw(img)
        try:
            bbox = d.textbbox((0, 0), message, font=FB)
            tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        except AttributeError:
            tw, th = d.textsize(message, font=FB)
        d.text(((IMG_W - tw)//2, 18), message, font=FB, fill=BLACK)
        d.text((6, IMG_H-18), datetime.now().strftime("%H:%M:%S"), font=FS, fill=BLACK)
        disp.image(img)
    except Exception:
        pass


def draw(blocked: bool):
    try:
        img = Image.new("RGB", (IMG_W, IMG_H), color=RED if blocked else GREEN)
        d = ImageDraw.Draw(img)
        title = "YouTube BLOCKED" if blocked else "YouTube ALLOWED"
        try:
            bbox = d.textbbox((0, 0), title, font=FB)
            tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        except AttributeError:
            tw, th = d.textsize(title, font=FB)
        d.text(((IMG_W - tw)//2, 18), title, font=FB, fill=WHITE)
        d.text((6, IMG_H-18), datetime.now().strftime("%H:%M:%S"), font=FS, fill=WHITE)
        disp.image(img)
    except Exception:
        pass


def _on_sigusr1(signum, frame):
    # Set a flag so the main loop immediately refreshes overlay/status
    global _sigusr1_flag
    _sigusr1_flag = True


def main():
    # Start DB poller thread
    t = threading.Thread(target=db_poll_worker, daemon=True)
    t.start()

    # Install signal handler for instant refresh
    signal.signal(signal.SIGUSR1, _on_sigusr1)

    last_drawn_state = None
    ui_poll_interval = 0.01  # 100Hz for snappy overlay
    heartbeat_interval = 1.0
    last_heartbeat = 0.0

    while True:
        # If signaled, perform an immediate draw
        if _sigusr1_flag:
            # Clear flag first to avoid loops
            _sigusr1_flag = False
            hint = read_ui_hint()
            if hint is not None:
                draw_overlay_toggling(hint.get("msg") or "TOGGLING...")
            else:
                draw(get_cached_blocked())
            # continue with normal loop

        # Immediate UI hint overlay
        hint = read_ui_hint()
        if hint is not None:
            msg = hint.get("msg") or "TOGGLING..."
            draw_overlay_toggling(msg)
            time.sleep(ui_poll_interval)
            continue

        # Status rendering and heartbeat (uses cached DB state)
        blocked = get_cached_blocked()
        now = time.monotonic()
        if blocked != last_drawn_state or (now - last_heartbeat) >= heartbeat_interval:
            draw(blocked)
            last_drawn_state = blocked
            last_heartbeat = now
        time.sleep(ui_poll_interval)


if __name__ == "__main__":
    main()
