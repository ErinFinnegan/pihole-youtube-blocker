#!/usr/bin/env python3
import time
from datetime import datetime
import sqlite3
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

try:
    FB = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 18)
except Exception:
    FB = ImageFont.load_default()
FS = ImageFont.load_default()

DB_PATH = "/etc/pihole/gravity.db"
DB_CHECK_INTERVAL_S = 5.0


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
    # Re-query only every DB_CHECK_INTERVAL_S seconds
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
            # Drop connection and keep previous cached value or safe default
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
        # Ignore transient draw/display errors to keep loop alive
        pass


def main():
    state_cache = {}
    last_drawn_state = None
    while True:
        blocked = youtube_blocked_cached(state_cache)
        # Always refresh to update the clock, but keep cadence light
        if blocked != last_drawn_state:
            draw(blocked)
            last_drawn_state = blocked
        else:
            draw(blocked)
        time.sleep(1.0)


if __name__ == "__main__":
    main()
