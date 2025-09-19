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


