#!/usr/bin/env bash
set -euo pipefail

# Install cron jobs on the Pi to allow at 12:00 and block at 21:00 daily
# Requires: existing /usr/local/bin/yb and /usr/local/bin/yu or equivalent actions

ALLOW_CMD="/usr/local/bin/yu"
BLOCK_CMD="/usr/local/bin/yb"

if ! command -v sudo >/dev/null 2>&1; then
  echo "This script should be run on your Mac to push to the Pi, or directly on the Pi." >&2
fi

PI_HOST="${PI_HOST:-zerocool@pi-hole.local}"

echo "Installing cron schedule on $PI_HOST ..."

ssh "$PI_HOST" bash -s <<'REMOTE'
set -euo pipefail
ALLOW_CMD="/usr/local/bin/yu"
BLOCK_CMD="/usr/local/bin/yb"

echo "Creating helper scripts in /usr/local/sbin (direct sqlite + FTL reload) ..."
sudo tee /usr/local/sbin/pitft_cron_allow >/dev/null <<EOF
#!/usr/bin/env bash
set -e
date '+%F %T cron allow' >> /var/log/pihole-cron.log
# Disable KidsRestricted group (allow YouTube)
sqlite3 /etc/pihole/gravity.db "UPDATE 'group' SET enabled=0 WHERE name='KidsRestricted';" || true
# Reload FTL to apply without invoking api.sh
systemctl reload pihole-FTL 2>/dev/null || systemctl restart pihole-FTL 2>/dev/null || true
# Nudge display to refresh immediately if service is running
systemctl kill --signal=SIGUSR1 tft-youtube.service 2>/dev/null || true
systemctl kill --signal=SIGUSR1 tft-display.service 2>/dev/null || true
EOF

sudo tee /usr/local/sbin/pitft_cron_block >/dev/null <<EOF
#!/usr/bin/env bash
set -e
date '+%F %T cron block' >> /var/log/pihole-cron.log
# Enable KidsRestricted group (block YouTube)
sqlite3 /etc/pihole/gravity.db "UPDATE 'group' SET enabled=1 WHERE name='KidsRestricted';" || true
# Reload FTL to apply without invoking api.sh
systemctl reload pihole-FTL 2>/dev/null || systemctl restart pihole-FTL 2>/dev/null || true
# Nudge display to refresh immediately if service is running
systemctl kill --signal=SIGUSR1 tft-youtube.service 2>/dev/null || true
systemctl kill --signal=SIGUSR1 tft-display.service 2>/dev/null || true
EOF

sudo chmod +x /usr/local/sbin/pitft_cron_{allow,block}

echo "Installing root crontab entries..."
tmpfile=$(mktemp)
sudo crontab -l 2>/dev/null >"$tmpfile" || true
grep -q 'pitft_cron_allow' "$tmpfile" || echo "0 12 * * * /usr/local/sbin/pitft_cron_allow" >>"$tmpfile"
grep -q 'pitft_cron_block' "$tmpfile" || echo "0 21 * * * /usr/local/sbin/pitft_cron_block" >>"$tmpfile"
sudo crontab "$tmpfile"
rm -f "$tmpfile"

echo "Done. Current root crontab:" >&2
sudo crontab -l >&2
REMOTE

echo "Schedule installed."


