#!/usr/bin/env python3
import time, subprocess, threading
import RPi.GPIO as GPIO

# Pins
BTN_BLOCK = 23
BTN_ALLOW = 24

GPIO.setmode(GPIO.BCM)
GPIO.setup(BTN_BLOCK, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(BTN_ALLOW, GPIO.IN, pull_up_down=GPIO.PUD_UP)

DEBOUNCE_S = 0.2


def block_action():
    # Run helper script to block
    subprocess.call(["/bin/bash", "/usr/local/bin/pitft_block.sh"])
    # Ping display service to refresh (optional)
    subprocess.call(["/bin/systemctl", "kill", "--signal=SIGUSR1", "tft-display.service"])  # ignore errors


def allow_action():
    # Run helper script to allow
    subprocess.call(["/bin/bash", "/usr/local/bin/pitft_allow.sh"])
    subprocess.call(["/bin/systemctl", "kill", "--signal=SIGUSR1", "tft-display.service"])  # ignore errors


def main():
    print("[buttons] daemon started; monitoring pins 23 (block), 24 (allow)", flush=True)
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


