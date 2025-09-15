#!/bin/bash

# Enhanced cron jobs that update both Pi-hole and the display
# These should be installed as root cron jobs

echo "Creating enhanced cron jobs..."

# Create the blocking script
cat > /tmp/cron_block.sh << 'EOF'
#!/bin/bash
echo "$(date): Cron job - Blocking YouTube and Roblox" >> /var/log/pihole-cron.log

# Block domains
sqlite3 /etc/pihole/gravity.db "INSERT OR IGNORE INTO domainlist (type, domain) VALUES (1, 'youtube.com'), (1, 'roblox.com');"

# Reload Pi-hole
pihole reloadlists

# Signal the display service to refresh
systemctl kill --signal=SIGUSR1 tft-pihole-buttons.service 2>/dev/null || true

echo "$(date): Cron job - Blocking completed" >> /var/log/pihole-cron.log
EOF

# Create the unblocking script  
cat > /tmp/cron_unblock.sh << 'EOF'
#!/bin/bash
echo "$(date): Cron job - Unblocking YouTube and Roblox" >> /var/log/pihole-cron.log

# Unblock domains
sqlite3 /etc/pihole/gravity.db "DELETE FROM domainlist WHERE domain IN ('youtube.com', 'roblox.com') AND type=1;"

# Reload Pi-hole
pihole reloadlists

# Signal the display service to refresh
systemctl kill --signal=SIGUSR1 tft-pihole-buttons.service 2>/dev/null || true

echo "$(date): Cron job - Unblocking completed" >> /var/log/pihole-cron.log
EOF

# Make scripts executable
chmod +x /tmp/cron_block.sh /tmp/cron_unblock.sh

# Install as root cron jobs
echo "Installing cron jobs..."
(crontab -l 2>/dev/null; echo "# 12:00 PM daily - Unblock YouTube and Roblox") | crontab -
(crontab -l 2>/dev/null; echo "0 12 * * * /tmp/cron_unblock.sh") | crontab -
(crontab -l 2>/dev/null; echo "# 9:00 PM daily - Block YouTube and Roblox") | crontab -
(crontab -l 2>/dev/null; echo "0 21 * * * /tmp/cron_block.sh") | crontab -

echo "Enhanced cron jobs installed!"
echo "Cron jobs will now:"
echo "  - Block YouTube/Roblox at 9:00 PM daily"
echo "  - Unblock YouTube/Roblox at 12:00 PM daily"  
echo "  - Update the display when they run"
echo "  - Log all actions to /var/log/pihole-cron.log"
