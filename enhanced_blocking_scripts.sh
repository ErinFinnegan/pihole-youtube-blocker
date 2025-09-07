#!/bin/bash

# Enhanced YouTube and Roblox blocking scripts
# These scripts should replace your existing yb, yu, and ys scripts

echo "Creating enhanced blocking scripts for YouTube and Roblox..."

# Enhanced YouTube Block Script (yb)
cat > /tmp/yb_enhanced << 'EOF'
#!/bin/bash
echo "Blocking YouTube and Roblox..."

# Update the database to block YouTube
sudo sqlite3 /etc/pihole/gravity.db "UPDATE 'group' SET enabled=1 WHERE name='KidsRestricted';"

# Block Roblox domains
pihole -b roblox.com rbxcdn.com rbxtrk.com roblox.plus
pihole -b ecsv2.roblox.com ncs.roblox.com client-telemetry.roblox.com
pihole -b presence.roblox.com gold.roblox.com lms.roblox.com
pihole -b metrics.roblox.com tracing.roblox.com
pihole -b setup.roblox.com version.roblox.com assetdelivery.roblox.com
pihole -b thumbs.roblox.com thumbnails.roblox.com avatar.roblox.com
pihole -b catalog.roblox.com economy.roblox.com friends.roblox.com
pihole -b groups.roblox.com inventory.roblox.com itemconfiguration.roblox.com
pihole -b locale.roblox.com localization.roblox.com notifications.roblox.com
pihole -b publish.roblox.com realtime.roblox.com share.roblox.com
pihole -b textfilter.roblox.com trades.roblox.com translation.roblox.com
pihole -b users.roblox.com voice.roblox.com

# Ensure Scratch domains remain whitelisted
pihole -w scratch.mit.edu api.scratch.mit.edu projects.scratch.mit.edu
pihole -w cdn.scratch.mit.edu cdn2.scratch.mit.edu assets.scratch.mit.edu
pihole -w clouddata.scratch.mit.edu download.scratch.mit.edu
pihole -w downloads.scratch.mit.edu uploads.scratch.mit.edu
pihole -w scratch-edu.mit.edu scratchjr.mit.edu
pihole -w recaptcha.net www.recaptcha.net gstatic.com www.gstatic.com
pihole -w fonts.gstatic.com wistia.com fast.wistia.net wistia.net
pihole -w akamaihd.net embedwistia-a.akamaihd.net

# Force Pi-hole to reload
sudo pihole reloadlists
sudo systemctl restart pihole-FTL
sleep 2

# Signal display service to refresh immediately
sudo systemctl kill --signal=SIGUSR1 tft-youtube.service 2>/dev/null || true

echo "YouTube and Roblox blocked, Scratch whitelisted, and display refreshed!"
EOF

# Enhanced YouTube Allow Script (yu)
cat > /tmp/yu_enhanced << 'EOF'
#!/bin/bash
echo "Allowing YouTube and Roblox..."

# Update the database to allow YouTube
sudo sqlite3 /etc/pihole/gravity.db "UPDATE 'group' SET enabled=0 WHERE name='KidsRestricted';"

# Unblock Roblox domains
pihole -b -d roblox.com rbxcdn.com rbxtrk.com roblox.plus
pihole -b -d ecsv2.roblox.com ncs.roblox.com client-telemetry.roblox.com
pihole -b -d presence.roblox.com gold.roblox.com lms.roblox.com
pihole -b -d metrics.roblox.com tracing.roblox.com
pihole -b -d setup.roblox.com version.roblox.com assetdelivery.roblox.com
pihole -b -d thumbs.roblox.com thumbnails.roblox.com avatar.roblox.com
pihole -b -d catalog.roblox.com economy.roblox.com friends.roblox.com
pihole -b -d groups.roblox.com inventory.roblox.com itemconfiguration.roblox.com
pihole -b -d locale.roblox.com localization.roblox.com notifications.roblox.com
pihole -b -d publish.roblox.com realtime.roblox.com share.roblox.com
pihole -b -d textfilter.roblox.com trades.roblox.com translation.roblox.com
pihole -b -d users.roblox.com voice.roblox.com

# Ensure Scratch domains remain whitelisted
pihole -w scratch.mit.edu api.scratch.mit.edu projects.scratch.mit.edu
pihole -w cdn.scratch.mit.edu cdn2.scratch.mit.edu assets.scratch.mit.edu
pihole -w clouddata.scratch.mit.edu download.scratch.mit.edu
pihole -w downloads.scratch.mit.edu uploads.scratch.mit.edu
pihole -w scratch-edu.mit.edu scratchjr.mit.edu
pihole -w recaptcha.net www.recaptcha.net gstatic.com www.gstatic.com
pihole -w fonts.gstatic.com wistia.com fast.wistia.net wistia.net
pihole -w akamaihd.net embedwistia-a.akamaihd.net

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
if pihole -q roblox.com | grep -q "BLOCKED"; then
    echo "🎮 Roblox: BLOCKED"
else
    echo "🎮 Roblox: ALLOWED"
fi

# Check Scratch status
if pihole -q scratch.mit.edu | grep -q "OK"; then
    echo "✅ Scratch: ACCESSIBLE"
else
    echo "❌ Scratch: BLOCKED (This is bad!)"
fi

echo ""
echo "=== Domain Test Results ==="
echo "Testing roblox.com:"
pihole -q roblox.com

echo ""
echo "Testing scratch.mit.edu:"
pihole -q scratch.mit.edu

echo ""
echo "Testing youtube.com:"
pihole -q youtube.com
EOF

# Roblox-only block script (rb)
cat > /tmp/rb_enhanced << 'EOF'
#!/bin/bash
echo "Blocking Roblox only (YouTube status unchanged)..."

# Block Roblox domains
pihole -b roblox.com rbxcdn.com rbxtrk.com roblox.plus
pihole -b ecsv2.roblox.com ncs.roblox.com client-telemetry.roblox.com
pihole -b presence.roblox.com gold.roblox.com lms.roblox.com
pihole -b metrics.roblox.com tracing.roblox.com
pihole -b setup.roblox.com version.roblox.com assetdelivery.roblox.com
pihole -b thumbs.roblox.com thumbnails.roblox.com avatar.roblox.com
pihole -b catalog.roblox.com economy.roblox.com friends.roblox.com
pihole -b groups.roblox.com inventory.roblox.com itemconfiguration.roblox.com
pihole -b locale.roblox.com localization.roblox.com notifications.roblox.com
pihole -b publish.roblox.com realtime.roblox.com share.roblox.com
pihole -b textfilter.roblox.com trades.roblox.com translation.roblox.com
pihole -b users.roblox.com voice.roblox.com

# Ensure Scratch domains remain whitelisted
pihole -w scratch.mit.edu api.scratch.mit.edu projects.scratch.mit.edu
pihole -w cdn.scratch.mit.edu cdn2.scratch.mit.edu assets.scratch.mit.edu
pihole -w clouddata.scratch.mit.edu download.scratch.mit.edu
pihole -w downloads.scratch.mit.edu uploads.scratch.mit.edu
pihole -w scratch-edu.mit.edu scratchjr.mit.edu
pihole -w recaptcha.net www.recaptcha.net gstatic.com www.gstatic.com
pihole -w fonts.gstatic.com wistia.com fast.wistia.net wistia.net
pihole -w akamaihd.net embedwistia-a.akamaihd.net

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
echo "Allowing Roblox only (YouTube status unchanged)..."

# Unblock Roblox domains
pihole -b -d roblox.com rbxcdn.com rbxtrk.com roblox.plus
pihole -b -d ecsv2.roblox.com ncs.roblox.com client-telemetry.roblox.com
pihole -b -d presence.roblox.com gold.roblox.com lms.roblox.com
pihole -b -d metrics.roblox.com tracing.roblox.com
pihole -b -d setup.roblox.com version.roblox.com assetdelivery.roblox.com
pihole -b -d thumbs.roblox.com thumbnails.roblox.com avatar.roblox.com
pihole -b -d catalog.roblox.com economy.roblox.com friends.roblox.com
pihole -b -d groups.roblox.com inventory.roblox.com itemconfiguration.roblox.com
pihole -b -d locale.roblox.com localization.roblox.com notifications.roblox.com
pihole -b -d publish.roblox.com realtime.roblox.com share.roblox.com
pihole -b -d textfilter.roblox.com trades.roblox.com translation.roblox.com
pihole -b -d users.roblox.com voice.roblox.com

# Ensure Scratch domains remain whitelisted
pihole -w scratch.mit.edu api.scratch.mit.edu projects.scratch.mit.edu
pihole -w cdn.scratch.mit.edu cdn2.scratch.mit.edu assets.scratch.mit.edu
pihole -w clouddata.scratch.mit.edu download.scratch.mit.edu
pihole -w downloads.scratch.mit.edu uploads.scratch.mit.edu
pihole -w scratch-edu.mit.edu scratchjr.mit.edu
pihole -w recaptcha.net www.recaptcha.net gstatic.com www.gstatic.com
pihole -w fonts.gstatic.com wistia.com fast.wistia.net wistia.net
pihole -w akamaihd.net embedwistia-a.akamaihd.net

# Force Pi-hole to reload
sudo pihole reloadlists
sudo systemctl restart pihole-FTL
sleep 2

# Signal display service to refresh immediately
sudo systemctl kill --signal=SIGUSR1 tft-youtube.service 2>/dev/null || true

echo "Roblox allowed, Scratch whitelisted, and display refreshed!"
EOF

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
