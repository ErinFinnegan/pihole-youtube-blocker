#!/usr/bin/env bash
set -euo pipefail

# Disable KidsRestricted group (YouTube allowed)
sudo sqlite3 /etc/pihole/gravity.db "UPDATE 'group' SET enabled=0 WHERE name='KidsRestricted';"

# Optionally unblock Roblox
# sudo sqlite3 /etc/pihole/gravity.db "DELETE FROM domainlist WHERE domain='roblox.com' AND type=1;"

sudo pihole reloadlists || true
exit 0


