#!/usr/bin/env python3
import time, subprocess, threading, json, os
import RPi.GPIO as GPIO

# Pins
# BTN23 → Toggle YouTube
# BTN24 → Toggle Roblox/Playhop
BTN_YOUTUBE = 23
BTN_ROBLOX = 24

GPIO.setmode(GPIO.BCM)
GPIO.setup(BTN_YOUTUBE, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(BTN_ROBLOX, GPIO.IN, pull_up_down=GPIO.PUD_UP)

DEBOUNCE_S = 0.2
UI_HINT_PATH = "/tmp/pitft_ui.json"

_op_lock = threading.Lock()
_op_in_progress = False


def _signal_display():
    try:
        subprocess.call(["/bin/systemctl", "kill", "--signal=SIGUSR1", "tft-display.service"])  # best-effort
    except Exception:
        pass


def write_ui_hint(mode: str, msg: str = ""):
    tmp_path = UI_HINT_PATH + ".tmp"
    try:
        payload = {"mode": mode, "msg": msg, "ts": time.time()}
        with open(tmp_path, "w") as f:
            json.dump(payload, f)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_path, UI_HINT_PATH)
        print(f"[buttons] ui hint write: {payload}", flush=True)
        _signal_display()
    except Exception as e:
        print(f"[buttons] ui hint write error: {e}", flush=True)
        try:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
        except Exception:
            pass


def clear_ui_hint():
    try:
        if os.path.exists(UI_HINT_PATH):
            os.remove(UI_HINT_PATH)
            print("[buttons] ui hint cleared", flush=True)
        _signal_display()
    except Exception as e:
        print(f"[buttons] ui hint clear error: {e}", flush=True)


def _run_cmd(cmd):
    try:
        return subprocess.call(cmd) == 0
    except Exception:
        return False


def _op_done():
    global _op_in_progress
    clear_ui_hint()
    with _op_lock:
        _op_in_progress = False


def _youtube_blocked() -> bool:
    try:
        out = subprocess.check_output([
            "sudo", "/usr/bin/sqlite3", "/etc/pihole/gravity.db",
            "SELECT enabled FROM 'group' WHERE name='KidsRestricted';"
        ], text=True).strip()
        return out == "1"
    except Exception:
        return True


def _roblox_blocked() -> bool:
    try:
        out = subprocess.check_output([
            "sudo", "/usr/bin/sqlite3", "/etc/pihole/gravity.db",
            "SELECT enabled FROM 'group' WHERE name='KidsRoblox';"
        ], text=True).strip()
        return out == "1"
    except Exception:
        # If group missing or query fails, assume not blocked (safer default)
        return False


def _async_toggle_youtube():
    if _youtube_blocked():
        write_ui_hint("toggling", "YOUTUBE: ALLOWING...")
        _run_cmd(["/bin/bash", "/usr/local/bin/pitft_allow.sh"])  # set enabled=0
    else:
        write_ui_hint("toggling", "YOUTUBE: BLOCKING...")
        _run_cmd(["/bin/bash", "/usr/local/bin/pitft_block.sh"])  # set enabled=1
    _op_done()


def _async_toggle_roblox():
    if _roblox_blocked():
        write_ui_hint("toggling", "ROBLOX: ALLOWING...")
        _run_cmd(["/bin/bash", "/usr/local/bin/pitft_roblox_allow.sh"])  # set KidsRoblox enabled=0
    else:
        write_ui_hint("toggling", "ROBLOX: BLOCKING...")
        _run_cmd(["/bin/bash", "/usr/local/bin/pitft_roblox_block.sh"])  # set KidsRoblox enabled=1
    _op_done()


def _start_if_idle(target_fn, label: str):
    global _op_in_progress
    with _op_lock:
        if _op_in_progress:
            print("[buttons] press ignored (busy)", flush=True)
            return
        _op_in_progress = True
    print(f"[buttons] {label} triggered", flush=True)
    threading.Thread(target=target_fn, daemon=True).start()


def main():
    print("[buttons] daemon started; BTN23=YouTube toggle, BTN24=Roblox/Playhop toggle", flush=True)
    last = {BTN_YOUTUBE: 1, BTN_ROBLOX: 1}
    last_ts = {BTN_YOUTUBE: 0.0, BTN_ROBLOX: 0.0}
    try:
        while True:
            now = time.time()
            # Poll with debounce
            cur_yt = GPIO.input(BTN_YOUTUBE)
            if cur_yt != last[BTN_YOUTUBE]:
                print(f"[buttons] pin {BTN_YOUTUBE} changed -> {cur_yt}", flush=True)
                if cur_yt == 0 and now - last_ts[BTN_YOUTUBE] > DEBOUNCE_S:
                    last_ts[BTN_YOUTUBE] = now
                    _start_if_idle(_async_toggle_youtube, "toggle_youtube")
                last[BTN_YOUTUBE] = cur_yt

            cur_rb = GPIO.input(BTN_ROBLOX)
            if cur_rb != last[BTN_ROBLOX]:
                print(f"[buttons] pin {BTN_ROBLOX} changed -> {cur_rb}", flush=True)
                if cur_rb == 0 and now - last_ts[BTN_ROBLOX] > DEBOUNCE_S:
                    last_ts[BTN_ROBLOX] = now
                    _start_if_idle(_async_toggle_roblox, "toggle_roblox")
                last[BTN_ROBLOX] = cur_rb

            time.sleep(0.02)
    except KeyboardInterrupt:
        pass
    finally:
        print("[buttons] cleanup", flush=True)
        GPIO.cleanup()


if __name__ == "__main__":
    main()


