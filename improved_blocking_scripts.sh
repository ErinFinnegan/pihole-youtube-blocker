#!/bin/bash

# Improved YouTube blocking scripts that force immediate screen updates
# These scripts should be placed in /usr/local/bin/ on your Pi

# Function to force Pi-hole to reload and restart FTL
force_pihole_reload() {
    echo "Forcing Pi-hole to reload configuration..."
    sudo pihole reloadlists
    sudo systemctl restart pihole-FTL
    sleep 2  # Give FTL time to restart
}

# Function to signal the display service to refresh immediately
signal_display_refresh() {
    echo "Signaling display service to refresh..."
    # Send SIGUSR1 signal to the display service to force immediate refresh
    sudo systemctl kill --signal=SIGUSR1 tft-youtube.service 2>/dev/null || true
}

# YouTube Block Script (yb)
cat > /tmp/yb_improved << 'EOF'
#!/bin/bash
echo "Blocking YouTube..."

# Update the database
sudo sqlite3 /etc/pihole/gravity.db "UPDATE 'group' SET enabled=1 WHERE name='KidsRestricted';"

# Force Pi-hole to reload
sudo pihole reloadlists
sudo systemctl restart pihole-FTL
sleep 2

# Signal display service to refresh immediately
sudo systemctl kill --signal=SIGUSR1 tft-youtube.service 2>/dev/null || true

echo "YouTube blocked and display refreshed!"
EOF

# YouTube Unblock Script (yu)
cat > /tmp/yu_improved << 'EOF'
#!/bin/bash
echo "Unblocking YouTube..."

# Update the database
sudo sqlite3 /etc/pihole/gravity.db "UPDATE 'group' SET enabled=0 WHERE name='KidsRestricted';"

# Force Pi-hole to reload
sudo pihole reloadlists
sudo systemctl restart pihole-FTL
sleep 2

# Signal display service to refresh immediately
sudo systemctl kill --signal=SIGUSR1 tft-youtube.service 2>/dev/null || true

echo "YouTube unblocked and display refreshed!"
EOF

# YouTube Status Script (ys)
cat > /tmp/ys_improved << 'EOF'
#!/bin/bash
status=$(sudo sqlite3 /etc/pihole/gravity.db "SELECT enabled FROM 'group' WHERE name='KidsRestricted';")
if [ "$status" = "1" ]; then
    echo "YouTube is currently BLOCKED"
else
    echo "YouTube is currently ALLOWED"
fi
EOF

echo "Improved blocking scripts created!"
echo ""
echo "To install these on your Pi, run:"
echo "sudo cp /tmp/yb_improved /usr/local/bin/yb"
echo "sudo cp /tmp/yu_improved /usr/local/bin/yu"
echo "sudo cp /tmp/ys_improved /usr/local/bin/ys"
echo "sudo chmod +x /usr/local/bin/y{b,u,s}"
echo ""
echo "These scripts will:"
echo "1. Update the Pi-hole database"
echo "2. Force Pi-hole to reload and restart FTL"
echo "3. Signal the display service to refresh immediately"
