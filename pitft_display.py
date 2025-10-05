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
GREEN  = (0,180,0)
RED    = (200,0,0)
WHITE  = (255,255,255)
YELLOW = (255,255,0)
BLACK  = (0,0,0)
BLUE   = (0,100,200)
ORANGE = (255,140,0)

try:
    FB = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 18)
except Exception:
    FB = ImageFont.load_default()
FS = ImageFont.load_default()

DB_PATH = "/etc/pihole/gravity.db"
DB_POLL_INTERVAL_S = 2.0
UI_HINT_PATH = "/tmp/pitft_ui.json"

_state_lock = threading.Lock()
_last_blocked_state = True  # YouTube
_last_roblox_state = False  # Roblox
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
def query_kids_roblox_enabled() -> bool:
    try:
        conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True, timeout=0.05)
        try:
            conn.execute("PRAGMA busy_timeout=50")
            cursor = conn.execute("SELECT enabled FROM 'group' WHERE name='KidsRoblox';")
            row = cursor.fetchone()
            if not row:
                return False
            return int(row[0]) == 1
        finally:
            conn.close()
    except Exception:
        return _last_roblox_state



def db_poll_worker():
    global _last_blocked_state, _last_roblox_state
    while True:
        new_state = query_kids_restricted_enabled()
        new_rb = query_kids_roblox_enabled()
        with _state_lock:
            _last_blocked_state = new_state
            _last_roblox_state = new_rb
        time.sleep(DB_POLL_INTERVAL_S)


def get_cached_blocked() -> bool:
    with _state_lock:
        return _last_blocked_state

def get_cached_roblox() -> bool:
    with _state_lock:
        return _last_roblox_state


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
        # Fill hardware buffer to avoid any ghosting, then blit
        try:
            disp.fill(YELLOW)
        except Exception:
            pass
        disp.image(img)
    except Exception:
        pass


def draw(blocked: bool, rb_blocked: bool):
    try:
        if blocked and rb_blocked:
            bg = RED
        elif blocked and not rb_blocked:
            bg = ORANGE
        elif (not blocked) and rb_blocked:
            bg = BLUE
        else:
            bg = GREEN

        # Clear to black first to ensure no ghosted/double text, then paint bg rect
        img = Image.new("RGB", (IMG_W, IMG_H), color=BLACK)
        d = ImageDraw.Draw(img)
        d.rectangle([(0, 0), (IMG_W, IMG_H)], fill=bg)

        # No combined title to avoid clipping; show only per-service lines

        yt_text = "YouTube: " + ("BLOCKED" if blocked else "ALLOWED")
        rb_text = "Roblox: " + ("BLOCKED" if rb_blocked else "ALLOWED")
        try:
            bbox1 = d.textbbox((0, 0), yt_text, font=FB)
            yt_w, yt_h = bbox1[2] - bbox1[0], bbox1[3] - bbox1[1]
        except AttributeError:
            yt_w, yt_h = d.textsize(yt_text, font=FB)
        try:
            bbox2 = d.textbbox((0, 0), rb_text, font=FB)
            rb_w, rb_h = bbox2[2] - bbox2[0], bbox2[3] - bbox2[1]
        except AttributeError:
            rb_w, rb_h = d.textsize(rb_text, font=FB)
        x_yt = max(0, min(IMG_W - yt_w, (IMG_W - yt_w)//2))
        x_rb = max(0, min(IMG_W - rb_w, (IMG_W - rb_w)//2))
        # Position lines with extra spacing (approx two line breaks)
        y_yt = 28
        y_rb = y_yt + (yt_h * 2) + 12
        d.text((x_yt, y_yt), yt_text, font=FB, fill=WHITE)
        d.text((x_rb, y_rb), rb_text, font=FB, fill=WHITE)

        d.text((6, IMG_H-18), datetime.now().strftime("%H:%M:%S"), font=FS, fill=WHITE)
        # Fill hardware buffer first to eliminate ghosting, then draw image
        try:
            disp.fill(bg)
        except Exception:
            pass
        disp.image(img)
    except Exception:
        pass


def _on_sigusr1(signum, frame):
    # Set a flag so the main loop immediately refreshes overlay/status
    global _sigusr1_flag
    _sigusr1_flag = True


def main():
    global _sigusr1_flag
    # Start DB poller thread
    t = threading.Thread(target=db_poll_worker, daemon=True)
    t.start()

    # Install signal handler for instant refresh
    signal.signal(signal.SIGUSR1, _on_sigusr1)

    last_drawn_state = None
    ui_poll_interval = 0.02  # 50Hz is enough and reduces CPU
    heartbeat_interval = 0.0  # disable periodic redraw to avoid flicker
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
                ytb = get_cached_blocked(); rbb = get_cached_roblox()
                print(f"[display] refresh on signal: yt={ytb} rb={rbb}")
                draw(ytb, rbb)
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
        rb_blocked = get_cached_roblox()
        now = time.monotonic()
        if (blocked, rb_blocked) != last_drawn_state or (heartbeat_interval and (now - last_heartbeat) >= heartbeat_interval):
            print(f"[display] state draw: yt={blocked} rb={rb_blocked}")
            draw(blocked, rb_blocked)
            last_drawn_state = (blocked, rb_blocked)
            last_heartbeat = now
        time.sleep(ui_poll_interval)


if __name__ == "__main__":
    main()
