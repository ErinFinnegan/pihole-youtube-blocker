## 2025-09-24 Attempt A30
Goal:
Make cron-based YouTube blocking reliable and ensure immediate screen updates from scheduled actions.

Commands run / PRs:
- Updated `schedule_setup.sh` helpers to avoid Pi-hole CLI (api.sh readonly var issue): use direct sqlite `UPDATE` on `KidsRestricted`, reload/restart FTL, and signal the display service (SIGUSR1).
- Added sqlite `PRAGMA busy_timeout` and a short retry loop to handle transient "database is locked".
- Cleaned crontab to keep only `pitft_cron_allow` (12:00) and `pitft_cron_block` (21:00).

Output digest / errors:
- Manual tests succeeded: DB toggled as expected (1 after block, 0 after allow), TFT updated via service.
- Extra `5000` printed by sqlite before results; benign (busy_timeout echo).

Result: ✅ Success (robust scheduling + immediate display refresh).

Next step:
- Let cron fire at 12:00/21:00 and verify on-device. Optionally, use sqlite `-noheader -batch` if you want cleaner CLI output.

## 2025-09-24 Attempt A29
Goal:
Verify end-to-end responsiveness with async actions and busy lock; confirm that display updates instantly on press and returns to Ready, and enable visible logging to stdout.

Commands run / PRs:
- Edited `buttons_display_minimal.py` to print logs to stdout in addition to `/tmp/buttons-min.log`.
- Deployed to Pi (`~/pi-tft/`), stopped TFT/button services, ran in foreground with `sudo -E python3`.
- Used a second terminal to tail `/tmp/buttons-min.log` (optional once stdout logging added).

Output digest / errors:
- Buttons super-responsive; on press shows “Blocking…/Allowing…”, then “Blocked/Allowed”, then “Ready”.
- No errors after `_render_worker` globals fix.
- Log file present; stdout now mirrors log messages when running in foreground.

Result: ✅ Success (UX is immediate; concurrency guarded; logs visible on-screen).

Next step:
- If desired, create a simple systemd unit to run this minimal script as a test service, or merge the async/busy patterns back into the full display daemon.

## 2025-09-23 Attempt A28
Goal:
Wire minimal buttons script to Pi-hole actions cleanly: run `pitft_block.sh`/`pitft_allow.sh` asynchronously, add a busy lock to avoid overlapping actions, thread-safe render scheduling, and fix a threading bug seen on first run.

Commands run / PRs:
- Edited `buttons_display_minimal.py`: async subprocess calls to helpers, `_action_lock` busy guard, background `_render_worker` with correct `global` declarations, single-instance file lock, logging to `/tmp/buttons-min.log`, auto-return to "Ready".
- Deployed to Pi in `~/pi-tft`; stopped conflicting services; ran in foreground with `sudo -E python3`.

Output digest / errors:
- Initial crash: `UnboundLocalError` in `_render_worker` (missing `global` for `_latest_title/_latest_bg/_render_version`). Fixed and redeployed.
- System Python 3.11 confirmed on Pi; packages installed from piwheels. `.local` SSH host works; IP fallback available.

Result: ✅ Script launches; expect on press: "Blocking.../Allowing..." → "Blocked/Allowed" → auto "Ready". Mid-action presses show "Busy...".

Next step:
- Live test both buttons and tail `/tmp/buttons-min.log` for timing. If draw latency persists, ensure no other service holds SPI and consider lowering ST7789 baudrate.

## 2025-09-20 Attempt A27
Goal:
Make feedback truly instant by using disp.fill(YELLOW) immediately on press, and profile PIL+disp.image timings in background.

Commands run / PRs:
- Edited buttons_display_minimal.py: immediate disp.fill on press; spawn thread to render text + disp.image; log create/text/image timings
- Will restart single instance and test after user keeps changes

Output digest / errors:
- Pending (awaiting run); expectation: overlay appears instantly while background draw completes later

Result: ⏳ Planned

Next step:
- Restart minimal test, press buttons, and review /tmp/buttons-min.log for fill issued vs render profile lines.
## 2025-09-20 Attempt A26
Goal:
Run minimal buttons script as single instance; foreground test confirms backlight flickers instantly but draw still delayed ~5s.

Commands run / PRs:
- Killed background instances; relaunched with nohup (no output); ran in foreground with -u for live output

Output digest / errors:
- buttons-min.log shows ALLOW/BLOCK detected instantly, blink immediate, draw issued ~5.1–5.6s later
- Foreground run restores responsiveness but still with ~4–5s draw delay

Result: ❌ (delay persists; SPI draw path blockage unrelated to Pi-hole)

Next step:
- Ensure absolutely only one process holds SPI; add single-instance guard to minimal script and verify no other services are touching display; consider lowering ST7789 baudrate or disabling vsync/temp fixes if library blocks.

## 2025-09-20 Attempt A25
Goal:
Eliminate 5s SPI draw delay by removing concurrent display writers (duplicate test processes).

Commands run / PRs:
- Observed two running instances of buttons_display_minimal.py (SPI contention)
- Plan: kill all instances and relaunch a single instance; add single-instance guard next

Output digest / errors:
- Log shows backlight blink instant, draw delayed ~5.5s → points to SPI contention

Result: ⏳ Pending after restart of a single instance

Next step:
- Kill duplicates, run one instance, re-test; if fixed, add PID/lock to prevent recurrence.

## 2025-09-20 Attempt A23
Goal:
Re-test with accepted code deployed; recover from stuck yellow overlay and unresponsive buttons.

Commands run / PRs:
- Planned: Redeploy latest pitft_display.py and pitft_buttons.py, clear /tmp/pitft_ui.json, stop overlay-test, restart services
- SSH hiccup occurred; user manually rebooted and retried

Output digest / errors:
- After reboot: PiTFT stuck on yellow "Blocking (test)", periodic black flicker, buttons unresponsive

Result: ❌

Next step:
- Create a new, minimal project focused solely on responsive buttons and direct drawing (no Pi-hole calls, no IPC), run it standalone with all services stopped to isolate hardware responsiveness.

## 2025-09-20 Attempt A24
Goal:
Instrument minimal test to isolate latency: blink backlight (GPIO22) immediately on press and log timestamps around detect/blink/draw.

Commands run / PRs:
- Edited buttons_display_minimal.py: added backlight blink and timestamp logging; no Pi-hole/IPC
- Will redeploy and run standalone (services stopped) after user keeps changes

Output digest / errors:
- Pending (awaiting deploy)

Result: ⏳ Planned

Next step:
- Deploy, then press buttons and share /tmp/buttons-min.log lines to see if blink is instant and where draw latency occurs.

## 2025-09-20 Attempt A22
Goal:
Make overlay fully event-driven: buttons write hint file then signal display (SIGUSR1) to draw immediately (no polling delay).

Commands run / PRs:
- Plan: Update pitft_display.py to install SIGUSR1 handler that immediately draws overlay if hint exists
- Plan: Update pitft_buttons.py to send SIGUSR1 to tft-display.service right after writing the hint and again after clearing
- Hold deployment until user approves

Output digest / errors:
- Pending (awaiting code acceptance and deploy)

Result: ⏳ Planned

Next step:
- After acceptance, deploy to Pi and test immediate yellow overlay.

## 2025-09-20 Attempt A21
Goal:
Prove instant overlay path end-to-end with a minimal overlay-only buttons test.

Commands run / PRs:
- Created pitft_buttons_overlay_test.py to write UI hint on button presses (no Pi-hole)
- Stopped pitft-buttons.service and launched the test in background

Output digest / errors:
- Test started; awaiting user confirmation of immediate yellow overlay on press

Result: ⏳ Pending user verification

Next step:
- If overlay is instant, re-enable buttons daemon; otherwise, lower display hint poll further

## 2025-09-20 Attempt A20
Goal:
Fix missing yellow overlay by making IPC writes atomic and drawing overlay continuously while hint exists.

Commands run / PRs:
- Updated pitft_buttons.py: atomic write to /tmp/pitft_ui.json (os.replace), added logs for write/clear
- Updated pitft_display.py: poll hint at 20Hz, render overlay every poll while present, robust JSON fallback
- Deployed both scripts and restarted tft-display.service and pitft-buttons.service
- Verified unit ExecStart paths and remote script contents
- Manually created /tmp/pitft_ui.json to test overlay trigger

Output digest / errors:
- Services active; no crashes; hint file manual creation succeeded (file present)
- Buttons logs show triggers; awaiting confirmation that overlay appears on press

Result: ⏳ Pending user verification

Next step:
- User presses both buttons; confirm immediate yellow overlay. If good, reduce DB polling delay to 2s to shorten status lag.

## 2025-09-20 Attempt A19
Goal:
Adopt event-driven UX: instant feedback on press, run yb/yu in background, ignore presses while busy.

Commands run / PRs:
- Updated pitft_buttons.py: added busy lock, background threads for yb/yu, atomic UI hint writes, and debounce handling
- Kept display IPC overlay polling; no changes needed in display
- Deployed buttons daemon and restarted service; tailed logs for presses

Output digest / errors:
- Buttons log shows hint writes and clears around each operation
- Pending confirmation: overlay is instant on press; DB truth still polled in background

Result: ⏳ Pending user verification

Next step:
- If overlay is instant, drop DB polling in display to 2s to reduce status lag.

## 2025-09-19 Attempt A18
Goal:
Fix missing yellow overlay by making IPC writes atomic and drawing overlay continuously while hint exists.

Commands run / PRs:
- Updated pitft_buttons.py: atomic write to /tmp/pitft_ui.json (os.replace), added logs for write/clear
- Updated pitft_display.py: poll hint at 20Hz, render overlay every poll while present, robust JSON fallback
- Deployed both scripts and restarted tft-display.service and pitft-buttons.service
- Verified unit ExecStart paths and remote script contents
- Manually created /tmp/pitft_ui.json to test overlay trigger

Output digest / errors:
- Services active; no crashes; hint file manual creation succeeded (file present)
- Buttons logs show triggers; awaiting confirmation that overlay appears on press

Result: ⏳ Pending user verification

Next step:
- User presses both buttons; confirm immediate yellow overlay. If good, reduce DB polling delay to 2s to shorten status lag.

## 2025-09-20 Attempt A20
Goal:
Eliminate 4–5s delay caused by `pihole reloadlists` hitting api.sh readonly var bug.

Commands run / PRs:
- On Pi, removed `sudo pihole reloadlists` from /usr/local/bin/pitft_block.sh and pitft_allow.sh
- Verified scripts now only update SQLite and exit

Output digest / errors:
- Before/after grep confirmed removal; scripts shown without reloadlists
- Expect immediate overlay and quicker return from helpers (no api.sh delay)

Result: ✅ (change applied)

Next step:
- Press buttons; confirm overlay appears instantly and stays up only during the (now shorter) DB update. If status lag remains, lower display DB poll to 2s.

## 2025-09-19 Attempt A17
Goal:
Restore instant yellow "TOGGLING…" feedback with split services via lightweight IPC.

Commands run / PRs:
- Edited pitft_buttons.py to write /tmp/pitft_ui.json with {mode:"toggling", msg}
- Edited pitft_display.py to poll /tmp/pitft_ui.json at 10Hz and render yellow overlay
- Removed SIGUSR1 signaling (was killing the display process); rely on polling
- Deployed both scripts and restarted services

Output digest / errors:
- Services active after restart
- Prior attempt with SIGUSR1 caused systemd to restart the display; removed
- Buttons logs show daemon start; awaiting live press to verify overlay

Result: ⏳ Pending verification (expected immediate yellow on press)

Next step:
- Press a button and confirm immediate yellow overlay; verify that it clears automatically after the helper completes and status reconciles within a few seconds.

## 2025-09-19 Attempt A16
Goal:
Reduce display tight-loop CPU usage and remove sudo-subprocess DB queries; ensure clock heartbeat and stable rendering.

Commands run / PRs:
- Edited pitft_display.py to:
  - Use Python sqlite3 (read-only URI) to query KidsRestricted
  - Cache status and poll DB every 5s
  - Refresh screen every 1s with a clock heartbeat
  - Wrap draw/display in try/except
- scp pitft_display.py zerocool@pi-hole.local:/home/zerocool/
- ssh … "sudo systemctl restart tft-display.service"
- Checked service status, PID, CPU, and logs

Output digest / errors:
- Service active; new PID running
- CPU around ~65% (improved loop but still significant due to PIL draws each second)
- Display logs clear (no more sudo sqlite calls after restart window)
- Buttons service has no recent entries in the last minute

Result: ❌ (partial ✅: display loop hardened; no sudo sqlite; heartbeat enabled)

Next step:
- Verify on-device that the clock is visibly ticking; if not, investigate rotation/canvas mismatch.
- Lower redraw rate to 2s or use double-buffer/dirty-region to reduce CPU.
- Inspect pitft-buttons service live: add temporary per-iteration debug or confirm edge polling rate; ensure no other process owns /dev/gpiomem.
- Consider briefly stopping display service and testing buttons-only responsiveness.

## 2025-09-19 Attempt A15
Goal:
Diagnose frozen display clock and unresponsive buttons post-deployment; verify conflicts and live status.

Commands run / PRs:
- ssh zerocool@pi-hole.local "systemctl is-active tft-display.service pitft-buttons.service"
- ssh zerocool@pi-hole.local "systemctl list-unit-files | grep -E 'tft|pitft'"
- ssh zerocool@pi-hole.local "ps aux | grep -E 'tft-|pitft-|youtube|Screen_status|working_pihole|button_test' | grep -v grep"
- ssh zerocool@pi-hole.local "sudo sqlite3 /etc/pihole/gravity.db \"SELECT enabled FROM 'group' WHERE name='KidsRestricted';\""
- ssh zerocool@pi-hole.local "sudo journalctl -u tft-display.service -n 30 --no-pager"
- ssh zerocool@pi-hole.local "sudo journalctl -u pitft-buttons.service -n 30 --no-pager"

Output digest / errors:
- Both services active; display PID and buttons PID running.
- KidsRestricted=0 (Allowed) in DB.
- Display logs: steady 3–5s sqlite reads, no errors; clock appears frozen on-screen.
- Buttons logs: no recent entries post-reboot (no presses recorded).
- Old units listed but disabled (tft-youtube.service, tft-pihole-buttons.service).

Result: ❌
Buttons not registering events in logs; display showing Allowed and clock not visibly updating.

Next step:
Add explicit heartbeat timer in display loop; raise button daemon logging level on every poll edge; run a minimal GPIO probe to confirm pins live; check /dev/gpiomem contention and permissions; consider restarting only buttons service.

## 2025-09-19 Attempt A14
Goal:
Clear potential stale SPI/GPIO/display state by rebooting the Pi.

Commands run / PRs:
- ssh zerocool@pi-hole.local "sudo reboot now"

Output digest / errors:
- Reboot succeeded. After boot, both services showed active, but on-screen clock still appeared stuck; buttons still unresponsive.

Result: ❌

Next step:
Re-check unit status, logs, DB flag, and search for conflicting services/processes (performed in A15).

## 2025-09-16 Attempt A13
Goal:
Inspect live services and logs to confirm whether button presses are detected and whether display loop is running.

Commands run / PRs:
- ssh zerocool@pi-hole.local "systemctl is-active tft-display.service pitft-buttons.service"
- ssh zerocool@pi-hole.local "ps aux | grep -E 'pitft_(display|buttons)\\.py' | grep -v grep"
- ssh zerocool@pi-hole.local "sudo journalctl -u tft-display.service -n 25 --no-pager"
- ssh zerocool@pi-hole.local "sudo journalctl -u pitft-buttons.service -n 25 --no-pager"
- ssh zerocool@pi-hole.local "sudo sqlite3 /etc/pihole/gravity.db \"SELECT enabled FROM 'group' WHERE name='KidsRestricted';\""

Output digest / errors:
- Services active; display querying DB periodically.
- Buttons logs showed pin 23 and 24 transitions, block/allow handlers executed, sqlite UPDATE on group and pihole reloadlists ran without error.
- Despite successful button handler actions, user-reported display appeared stuck on Allowed and flickered earlier.

Result: ❌ (partial ✅ on button detection prior to reboot)

Next step:
Reboot to clear state (done in A14) and then verify fresh logs; consider reducing display loop sudo usage and ensure non-blocking rendering.


