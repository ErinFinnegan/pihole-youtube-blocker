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


def _async_block():
    write_ui_hint("toggling", "BLOCKING...")
    _run_cmd(["/bin/bash", "/usr/local/bin/pitft_block.sh"])  # direct helper (SQLite only)
    _op_done()


def _async_allow():
    write_ui_hint("toggling", "ALLOWING...")
    _run_cmd(["/bin/bash", "/usr/local/bin/pitft_allow.sh"])  # direct helper (SQLite only)
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
    print("[buttons] daemon started; monitoring pins 23 (BLOCK), 24 (ALLOW)", flush=True)
    last = {BTN_BLOCK: 1, BTN_ALLOW: 1}
    last_ts = {BTN_BLOCK: 0.0, BTN_ALLOW: 0.0}
    try:
        while True:
            now = time.time()
            # Poll with debounce
            cur_block = GPIO.input(BTN_BLOCK)
            if cur_block != last[BTN_BLOCK]:
                print(f"[buttons] pin {BTN_BLOCK} changed -> {cur_block}", flush=True)
                if cur_block == 0 and now - last_ts[BTN_BLOCK] > DEBOUNCE_S:
                    last_ts[BTN_BLOCK] = now
                    _start_if_idle(_async_block, "block")
                last[BTN_BLOCK] = cur_block

            cur_allow = GPIO.input(BTN_ALLOW)
            if cur_allow != last[BTN_ALLOW]:
                print(f"[buttons] pin {BTN_ALLOW} changed -> {cur_allow}", flush=True)
                if cur_allow == 0 and now - last_ts[BTN_ALLOW] > DEBOUNCE_S:
                    last_ts[BTN_ALLOW] = now
                    _start_if_idle(_async_allow, "allow")
                last[BTN_ALLOW] = cur_allow

            time.sleep(0.02)
    except KeyboardInterrupt:
        pass
    finally:
        print("[buttons] cleanup", flush=True)
        GPIO.cleanup()


if __name__ == "__main__":
    main()


