#!/usr/bin/env python3
import time, subprocess, threading, json, os
import RPi.GPIO as GPIO

# Pins
BTN_BLOCK = 23
BTN_ALLOW = 24

GPIO.setmode(GPIO.BCM)
GPIO.setup(BTN_BLOCK, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(BTN_ALLOW, GPIO.IN, pull_up_down=GPIO.PUD_UP)

DEBOUNCE_S = 0.2
UI_HINT_PATH = "/tmp/pitft_ui.json"


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
    except Exception as e:
        print(f"[buttons] ui hint clear error: {e}", flush=True)


def block_action():
    subprocess.call(["/bin/bash", "/usr/local/bin/pitft_block.sh"])  # blocking
    clear_ui_hint()


def allow_action():
    subprocess.call(["/bin/bash", "/usr/local/bin/pitft_allow.sh"])  # blocking
    clear_ui_hint()


def main():
    print("[buttons] daemon started; monitoring pins 23 (BLOCK), 24 (ALLOW)", flush=True)
    last = {BTN_BLOCK: 1, BTN_ALLOW: 1}
    last_ts = {BTN_BLOCK: 0.0, BTN_ALLOW: 0.0}
    try:
        while True:
            now = time.time()
            for pin, fn in (
                (BTN_BLOCK, block_action),
                (BTN_ALLOW, allow_action),
            ):
                cur = GPIO.input(pin)
                if cur != last[pin]:
                    print(f"[buttons] pin {pin} changed -> {cur}", flush=True)
                    if cur == 0 and now - last_ts[pin] > DEBOUNCE_S:
                        last_ts[pin] = now
                        action = "block" if pin == BTN_BLOCK else "allow"
                        print(f"[buttons] {action} triggered", flush=True)
                        # Immediate yellow overlay hint (atomic write)
                        write_ui_hint("toggling", "BLOCKING..." if action == "block" else "ALLOWING...")
                        threading.Thread(target=fn, daemon=True).start()
                    last[pin] = cur
            time.sleep(0.02)
    except KeyboardInterrupt:
        pass
    finally:
        print("[buttons] cleanup", flush=True)
        GPIO.cleanup()


if __name__ == "__main__":
    main()


