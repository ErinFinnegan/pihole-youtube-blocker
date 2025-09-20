#!/usr/bin/env python3
import time
from datetime import datetime
import sqlite3
import json, os, sys
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
DB_CHECK_INTERVAL_S = 5.0
UI_HINT_PATH = "/tmp/pitft_ui.json"


def read_ui_hint():
    if not os.path.exists(UI_HINT_PATH):
        return None
    try:
        with open(UI_HINT_PATH) as f:
            data = json.load(f)
            if isinstance(data, dict):
                return data
    except Exception:
        # Fall through to a default if file exists but JSON invalid
        return {"mode": "toggling", "msg": "TOGGLING..."}
    return None


def query_kids_restricted_enabled(sqlite_connection: sqlite3.Connection) -> bool:
    cursor = sqlite_connection.execute("SELECT enabled FROM 'group' WHERE name='KidsRestricted';")
    row = cursor.fetchone()
    if not row:
        return True
    try:
        return int(row[0]) == 1
    except Exception:
        return True


def youtube_blocked_cached(state_cache: dict) -> bool:
    now_monotonic = time.monotonic()
    last_check = state_cache.get("last_check_ts", 0.0)
    if now_monotonic - last_check >= DB_CHECK_INTERVAL_S or ("blocked" not in state_cache):
        try:
            conn = state_cache.get("conn")
            if conn is None:
                conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True, timeout=1.0)
                state_cache["conn"] = conn
            blocked = query_kids_restricted_enabled(conn)
            state_cache["blocked"] = blocked
            state_cache["last_check_ts"] = now_monotonic
        except Exception:
            try:
                if state_cache.get("conn") is not None:
                    state_cache["conn"].close()
            except Exception:
                pass
            state_cache["conn"] = None
            if "blocked" not in state_cache:
                state_cache["blocked"] = True
            state_cache["last_check_ts"] = now_monotonic
    return state_cache.get("blocked", True)


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


def main():
    state_cache = {}
    last_drawn_state = None
    ui_poll_interval = 0.05  # 20Hz for snappy overlay
    heartbeat_interval = 1.0
    last_heartbeat = 0.0
    last_hint_present = False
    while True:
        # Immediate UI hint overlay (polled frequently)
        hint = read_ui_hint()
        if hint is not None:
            msg = hint.get("msg") or "TOGGLING..."
            if not last_hint_present:
                print(f"[display] overlay start: {msg}", file=sys.stderr, flush=True)
            draw_overlay_toggling(msg)
            last_hint_present = True
            time.sleep(ui_poll_interval)
            continue
        else:
            if last_hint_present:
                print("[display] overlay cleared", file=sys.stderr, flush=True)
            last_hint_present = False

        # Status rendering and heartbeat
        blocked = youtube_blocked_cached(state_cache)
        now = time.monotonic()
        if blocked != last_drawn_state or (now - last_heartbeat) >= heartbeat_interval:
            draw(blocked)
            last_drawn_state = blocked
            last_heartbeat = now
        time.sleep(ui_poll_interval)


if __name__ == "__main__":
    main()
