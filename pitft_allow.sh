#!/usr/bin/env bash
set -euo pipefail

# Disable KidsRestricted group (YouTube allowed) with busy-timeout + retries (avoid pihole CLI)
SQLITE=(sudo sqlite3 -cmd "PRAGMA busy_timeout=5000;")
for i in {1..5}; do
  "${SQLITE[@]}" /etc/pihole/gravity.db "UPDATE 'group' SET enabled=0 WHERE name='KidsRestricted';" && break || sleep 1
done

# Reload FTL so changes take effect promptly
sudo systemctl reload pihole-FTL 2>/dev/null || sudo systemctl restart pihole-FTL 2>/dev/null || true
exit 0


