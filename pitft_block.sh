#!/usr/bin/env bash
set -euo pipefail

# Enable KidsRestricted group (YouTube blocked)
sudo sqlite3 /etc/pihole/gravity.db "UPDATE 'group' SET enabled=1 WHERE name='KidsRestricted';"

# Optionally block Roblox via domainlist
# sudo sqlite3 /etc/pihole/gravity.db "INSERT OR IGNORE INTO domainlist (type, domain) VALUES (1, 'roblox.com');"

sudo pihole reloadlists || true
exit 0


