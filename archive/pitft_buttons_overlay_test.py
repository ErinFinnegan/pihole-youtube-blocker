#!/usr/bin/env python3
import time, json, os, sys
import RPi.GPIO as GPIO

BTN_BLOCK = 23
BTN_ALLOW = 24
UI_HINT_PATH = "/tmp/pitft_ui.json"


def write_ui_hint(message: str):
    tmp_path = UI_HINT_PATH + ".tmp"
    try:
        payload = {"mode": "toggling", "msg": message, "ts": time.time()}
        with open(tmp_path, "w") as f:
            json.dump(payload, f)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_path, UI_HINT_PATH)
        print(f"[overlay-test] hint -> {payload}", flush=True)
    except Exception as e:
        print(f"[overlay-test] hint write error: {e}", flush=True)


def clear_ui_hint():
    try:
        if os.path.exists(UI_HINT_PATH):
            os.remove(UI_HINT_PATH)
            print("[overlay-test] hint cleared", flush=True)
    except Exception as e:
        print(f"[overlay-test] hint clear error: {e}", flush=True)


def main():
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(BTN_BLOCK, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(BTN_ALLOW, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    last = {BTN_BLOCK: 1, BTN_ALLOW: 1}
    last_ts = {BTN_BLOCK: 0.0, BTN_ALLOW: 0.0}
    DEBOUNCE_S = 0.2

    print("[overlay-test] running: 23=BLOCK, 24=ALLOW (overlay only)", flush=True)
    try:
        while True:
            now = time.time()
            cur_b = GPIO.input(BTN_BLOCK)
            if cur_b != last[BTN_BLOCK]:
                if cur_b == 0 and now - last_ts[BTN_BLOCK] > DEBOUNCE_S:
                    last_ts[BTN_BLOCK] = now
                    write_ui_hint("BLOCKING (TEST)...")
                last[BTN_BLOCK] = cur_b

            cur_a = GPIO.input(BTN_ALLOW)
            if cur_a != last[BTN_ALLOW]:
                if cur_a == 0 and now - last_ts[BTN_ALLOW] > DEBOUNCE_S:
                    last_ts[BTN_ALLOW] = now
                    write_ui_hint("ALLOWING (TEST)...")
                last[BTN_ALLOW] = cur_a

            time.sleep(0.02)
    except KeyboardInterrupt:
        pass
    finally:
        clear_ui_hint()
        GPIO.cleanup()
        print("[overlay-test] exit", flush=True)


if __name__ == "__main__":
    main()
