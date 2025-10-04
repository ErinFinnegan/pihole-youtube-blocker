#!/bin/bash

# Enhanced YouTube and Roblox blocking scripts
# These scripts should replace your existing yb, yu, and ys scripts

echo "Creating enhanced blocking scripts for YouTube and Roblox..."

# Enhanced YouTube Block Script (yb)
cat > /tmp/yb_enhanced << 'EOF'
#!/bin/bash
echo "Blocking YouTube, Roblox, and Playhop..."

# Update the database to block YouTube
sudo sqlite3 /etc/pihole/gravity.db "UPDATE 'group' SET enabled=1 WHERE name='KidsRestricted';"

# Block Roblox domains
pihole deny roblox.com rbxcdn.com rbxtrk.com roblox.plus
pihole deny ecsv2.roblox.com ncs.roblox.com client-telemetry.roblox.com
pihole deny presence.roblox.com gold.roblox.com lms.roblox.com
pihole deny metrics.roblox.com tracing.roblox.com
pihole deny setup.roblox.com version.roblox.com assetdelivery.roblox.com
pihole deny thumbs.roblox.com thumbnails.roblox.com avatar.roblox.com
pihole deny catalog.roblox.com economy.roblox.com friends.roblox.com
pihole deny groups.roblox.com inventory.roblox.com itemconfiguration.roblox.com
pihole deny locale.roblox.com localization.roblox.com notifications.roblox.com
pihole deny publish.roblox.com realtime.roblox.com share.roblox.com
pihole deny textfilter.roblox.com trades.roblox.com translation.roblox.com
pihole deny users.roblox.com voice.roblox.com

# Block Playhop domains
pihole deny playhop.com www.playhop.com api.playhop.com cdn.playhop.com
sudo sqlite3 /etc/pihole/gravity.db "INSERT OR IGNORE INTO domainlist (type, domain) VALUES (3, '(^|\\.)playhop\\.com$');"

# Ensure Scratch domains remain whitelisted
pihole allow scratch.mit.edu api.scratch.mit.edu projects.scratch.mit.edu
pihole allow cdn.scratch.mit.edu cdn2.scratch.mit.edu assets.scratch.mit.edu
pihole allow clouddata.scratch.mit.edu download.scratch.mit.edu
pihole allow downloads.scratch.mit.edu uploads.scratch.mit.edu
pihole allow scratch-edu.mit.edu scratchjr.mit.edu
pihole allow recaptcha.net www.recaptcha.net gstatic.com www.gstatic.com
pihole allow fonts.gstatic.com wistia.com fast.wistia.net wistia.net
pihole allow akamaihd.net embedwistia-a.akamaihd.net

# Force Pi-hole to reload
sudo pihole reloadlists
sudo systemctl restart pihole-FTL
sleep 2

# Signal display service to refresh immediately
sudo systemctl kill --signal=SIGUSR1 tft-youtube.service 2>/dev/null || true

echo "YouTube, Roblox, and Playhop blocked; Scratch whitelisted; display refreshed!"
EOF

# Enhanced YouTube Allow Script (yu)
cat > /tmp/yu_enhanced << 'EOF'
#!/bin/bash
echo "Allowing YouTube, Roblox, and Playhop..."

# Update the database to allow YouTube
sudo sqlite3 /etc/pihole/gravity.db "UPDATE 'group' SET enabled=0 WHERE name='KidsRestricted';"

# Unblock Roblox domains
pihole allow roblox.com rbxcdn.com rbxtrk.com roblox.plus
pihole allow ecsv2.roblox.com ncs.roblox.com client-telemetry.roblox.com
pihole allow presence.roblox.com gold.roblox.com lms.roblox.com
pihole allow metrics.roblox.com tracing.roblox.com
pihole allow setup.roblox.com version.roblox.com assetdelivery.roblox.com
pihole allow thumbs.roblox.com thumbnails.roblox.com avatar.roblox.com
pihole allow catalog.roblox.com economy.roblox.com friends.roblox.com
pihole allow groups.roblox.com inventory.roblox.com itemconfiguration.roblox.com
pihole allow locale.roblox.com localization.roblox.com notifications.roblox.com
pihole allow publish.roblox.com realtime.roblox.com share.roblox.com
pihole allow textfilter.roblox.com trades.roblox.com translation.roblox.com
pihole allow users.roblox.com voice.roblox.com

# Unblock Playhop domains
pihole allow playhop.com www.playhop.com api.playhop.com cdn.playhop.com
sudo sqlite3 /etc/pihole/gravity.db "DELETE FROM domainlist WHERE type=3 AND domain='(^|\\.)playhop\\.com$';"

# Ensure Scratch domains remain whitelisted
pihole allow scratch.mit.edu api.scratch.mit.edu projects.scratch.mit.edu
pihole allow cdn.scratch.mit.edu cdn2.scratch.mit.edu assets.scratch.mit.edu
pihole allow clouddata.scratch.mit.edu download.scratch.mit.edu
pihole allow downloads.scratch.mit.edu uploads.scratch.mit.edu
pihole allow scratch-edu.mit.edu scratchjr.mit.edu
pihole allow recaptcha.net www.recaptcha.net gstatic.com www.gstatic.com
pihole allow fonts.gstatic.com wistia.com fast.wistia.net wistia.net
pihole allow akamaihd.net embedwistia-a.akamaihd.net

# Force Pi-hole to reload
sudo pihole reloadlists
sudo systemctl restart pihole-FTL
sleep 2

# Signal display service to refresh immediately
sudo systemctl kill --signal=SIGUSR1 tft-youtube.service 2>/dev/null || true

echo "YouTube and Roblox allowed, Scratch whitelisted, and display refreshed!"
EOF

# Enhanced Status Script (ys)
cat > /tmp/ys_enhanced << 'EOF'
#!/bin/bash
echo "=== Pi-hole Status Report ==="
echo ""

# Check YouTube status
youtube_status=$(sudo sqlite3 /etc/pihole/gravity.db "SELECT enabled FROM 'group' WHERE name='KidsRestricted';")
if [ "$youtube_status" = "1" ]; then
    echo "🎮 YouTube: BLOCKED"
else
    echo "🎮 YouTube: ALLOWED"
fi

# Check Roblox status
if sudo pihole -q roblox.com | grep -q "BLOCKED"; then
    echo "🎮 Roblox: BLOCKED"
else
    echo "🎮 Roblox: ALLOWED"
fi

# Check Scratch status
if sudo pihole -q scratch.mit.edu | grep -q "OK"; then
    echo "✅ Scratch: ACCESSIBLE"
else
    echo "❌ Scratch: BLOCKED (This is bad!)"
fi

echo ""
echo "=== Domain Test Results ==="
echo "Testing roblox.com:"
sudo pihole -q roblox.com

echo ""
echo "Testing playhop.com:"
sudo pihole -q playhop.com

echo ""
echo "Testing scratch.mit.edu:"
sudo pihole -q scratch.mit.edu

echo ""
echo "Testing youtube.com:"
sudo pihole -q youtube.com
EOF

# Roblox-only block script (rb)
cat > /tmp/rb_enhanced << 'EOF'
#!/bin/bash
echo "Blocking Roblox and Playhop only (YouTube status unchanged)..."

# Block Roblox domains
pihole deny roblox.com rbxcdn.com rbxtrk.com roblox.plus
pihole deny ecsv2.roblox.com ncs.roblox.com client-telemetry.roblox.com
pihole deny presence.roblox.com gold.roblox.com lms.roblox.com
pihole deny metrics.roblox.com tracing.roblox.com
pihole deny setup.roblox.com version.roblox.com assetdelivery.roblox.com
pihole deny thumbs.roblox.com thumbnails.roblox.com avatar.roblox.com
pihole deny catalog.roblox.com economy.roblox.com friends.roblox.com
pihole deny groups.roblox.com inventory.roblox.com itemconfiguration.roblox.com
pihole deny locale.roblox.com localization.roblox.com notifications.roblox.com
pihole deny publish.roblox.com realtime.roblox.com share.roblox.com
pihole deny textfilter.roblox.com trades.roblox.com translation.roblox.com
pihole deny users.roblox.com voice.roblox.com

# Block Playhop domains
pihole deny playhop.com www.playhop.com api.playhop.com cdn.playhop.com

# Ensure Scratch domains remain whitelisted
pihole allow scratch.mit.edu api.scratch.mit.edu projects.scratch.mit.edu
pihole allow cdn.scratch.mit.edu cdn2.scratch.mit.edu assets.scratch.mit.edu
pihole allow clouddata.scratch.mit.edu download.scratch.mit.edu
pihole allow downloads.scratch.mit.edu uploads.scratch.mit.edu
pihole allow scratch-edu.mit.edu scratchjr.mit.edu
pihole allow recaptcha.net www.recaptcha.net gstatic.com www.gstatic.com
pihole allow fonts.gstatic.com wistia.com fast.wistia.net wistia.net
pihole allow akamaihd.net embedwistia-a.akamaihd.net

# Force Pi-hole to reload
sudo pihole reloadlists
sudo systemctl restart pihole-FTL
sleep 2

# Signal display service to refresh immediately
sudo systemctl kill --signal=SIGUSR1 tft-youtube.service 2>/dev/null || true

echo "Roblox blocked, Scratch whitelisted, and display refreshed!"
EOF

# Roblox-only allow script (ru)
cat > /tmp/ru_enhanced << 'EOF'
#!/bin/bash
echo "Allowing Roblox and Playhop only (YouTube status unchanged)..."

# Unblock Roblox domains
pihole allow roblox.com rbxcdn.com rbxtrk.com roblox.plus
pihole allow ecsv2.roblox.com ncs.roblox.com client-telemetry.roblox.com
pihole allow presence.roblox.com gold.roblox.com lms.roblox.com
pihole allow metrics.roblox.com tracing.roblox.com
pihole allow setup.roblox.com version.roblox.com assetdelivery.roblox.com
pihole allow thumbs.roblox.com thumbnails.roblox.com avatar.roblox.com
pihole allow catalog.roblox.com economy.roblox.com friends.roblox.com
pihole allow groups.roblox.com inventory.roblox.com itemconfiguration.roblox.com
pihole allow locale.roblox.com localization.roblox.com notifications.roblox.com
pihole allow publish.roblox.com realtime.roblox.com share.roblox.com
pihole allow textfilter.roblox.com trades.roblox.com translation.roblox.com
pihole allow users.roblox.com voice.roblox.com

# Unblock Playhop domains
pihole allow playhop.com www.playhop.com api.playhop.com cdn.playhop.com

# Ensure Scratch domains remain whitelisted
pihole allow scratch.mit.edu api.scratch.mit.edu projects.scratch.mit.edu
pihole allow cdn.scratch.mit.edu cdn2.scratch.mit.edu assets.scratch.mit.edu
pihole allow clouddata.scratch.mit.edu download.scratch.mit.edu
pihole allow downloads.scratch.mit.edu uploads.scratch.mit.edu
pihole allow scratch-edu.mit.edu scratchjr.mit.edu
pihole allow recaptcha.net www.recaptcha.net gstatic.com www.gstatic.com
pihole allow fonts.gstatic.com wistia.com fast.wistia.net wistia.net
pihole allow akamaihd.net embedwistia-a.akamaihd.net

# Force Pi-hole to reload
sudo pihole reloadlists
sudo systemctl restart pihole-FTL
sleep 2

# Signal display service to refresh immediately
sudo systemctl kill --signal=SIGUSR1 tft-youtube.service 2>/dev/null || true

echo "Roblox allowed, Scratch whitelisted, and display refreshed!"
EOF

# Roblox/Playhop group-based toggle helpers (use group 'KidsRoblox')
cat > /tmp/roblox_block << 'EOF'
#!/usr/bin/env bash
set -euo pipefail
SQL=(sqlite3 -cmd "PRAGMA busy_timeout=5000;")
${SQL[@]} /etc/pihole/gravity.db "INSERT OR IGNORE INTO 'group'(name,enabled) VALUES('KidsRoblox',0);"
${SQL[@]} /etc/pihole/gravity.db "UPDATE 'group' SET enabled=1 WHERE name='KidsRoblox';"
systemctl reload pihole-FTL 2>/dev/null || systemctl restart pihole-FTL 2>/dev/null || true
systemctl kill --signal=SIGUSR1 tft-display.service 2>/dev/null || true
EOF

cat > /tmp/roblox_allow << 'EOF'
#!/usr/bin/env bash
set -euo pipefail
SQL=(sqlite3 -cmd "PRAGMA busy_timeout=5000;")
${SQL[@]} /etc/pihole/gravity.db "INSERT OR IGNORE INTO 'group'(name,enabled) VALUES('KidsRoblox',0);"
${SQL[@]} /etc/pihole/gravity.db "UPDATE 'group' SET enabled=0 WHERE name='KidsRoblox';"
systemctl reload pihole-FTL 2>/dev/null || systemctl restart pihole-FTL 2>/dev/null || true
systemctl kill --signal=SIGUSR1 tft-display.service 2>/dev/null || true
EOF

cat > /tmp/roblox_status << 'EOF'
#!/usr/bin/env bash
set -euo pipefail
status=$(sqlite3 /etc/pihole/gravity.db "SELECT enabled FROM 'group' WHERE name='KidsRoblox';" || echo "")
if [ "$status" = "1" ]; then
  echo "Roblox/Playhop: BLOCKED"
else
  echo "Roblox/Playhop: ALLOWED"
fi
EOF

echo "Installing Roblox helpers to /usr/local/bin ..."
sudo install -m 0755 /tmp/roblox_block /usr/local/bin/pitft_roblox_block.sh
sudo install -m 0755 /tmp/roblox_allow /usr/local/bin/pitft_roblox_allow.sh
sudo install -m 0755 /tmp/roblox_status /usr/local/bin/rs

echo "Enhanced blocking scripts created!"
echo ""
echo "To install these on your Pi, run:"
echo "sudo cp /tmp/yb_enhanced /usr/local/bin/yb"
echo "sudo cp /tmp/yu_enhanced /usr/local/bin/yu"
echo "sudo cp /tmp/ys_enhanced /usr/local/bin/ys"
echo "sudo cp /tmp/rb_enhanced /usr/local/bin/rb"
echo "sudo cp /tmp/ru_enhanced /usr/local/bin/ru"
echo "sudo chmod +x /usr/local/bin/y{b,u,s} /usr/local/bin/r{b,u}"
echo ""
echo "New commands available:"
echo "yb - Block YouTube and Roblox"
echo "yu - Allow YouTube and Roblox"
echo "ys - Check status of YouTube, Roblox, and Scratch"
echo "rb - Block Roblox only (YouTube unchanged)"
echo "ru - Allow Roblox only (YouTube unchanged)"
echo ""
echo "All scripts ensure Scratch domains remain whitelisted!"
