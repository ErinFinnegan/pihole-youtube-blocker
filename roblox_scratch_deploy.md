# Roblox Blocking & Scratch Whitelisting Deployment Guide

## 🎮 Overview
This guide helps you add Roblox blocking to your Pi-hole setup while ensuring all Scratch domains remain accessible for educational programming.

## 🚀 Quick Setup

### Step 1: Install Domain Configuration Script
```bash
# Copy the domain configuration script to your Pi
scp roblox_scratch_domains.sh zerocool@pi-hole.local:~/

# SSH into your Pi and run the configuration
ssh zerocool@pi-hole.local
sudo chmod +x roblox_scratch_domains.sh
sudo ./roblox_scratch_domains.sh
```

### Step 2: Install Enhanced Blocking Scripts
```bash
# On your Pi, install the enhanced scripts
sudo cp /tmp/yb_enhanced /usr/local/bin/yb
sudo cp /tmp/yu_enhanced /usr/local/bin/yu
sudo cp /tmp/ys_enhanced /usr/local/bin/ys
sudo cp /tmp/rb_enhanced /usr/local/bin/rb
sudo cp /tmp/ru_enhanced /usr/local/bin/ru
sudo chmod +x /usr/local/bin/y{b,u,s} /usr/local/bin/r{b,u}
```

### Step 3: Update Display Service
Replace your current `~/tft-youtube-status.py` with the enhanced version that shows:
- YouTube status (primary display)
- Roblox status (secondary line)
- Scratch status (with warning if blocked)

### Step 4: Restart Services
```bash
# Restart the display service
sudo systemctl restart tft-youtube.service

# Restart Pi-hole FTL
sudo systemctl restart pihole-FTL
```

## 🎯 Available Commands

### On Your Pi:
- `yb` - Block YouTube and Roblox
- `yu` - Allow YouTube and Roblox  
- `ys` - Check status of all services
- `rb` - Block Roblox only (YouTube unchanged)
- `ru` - Allow Roblox only (YouTube unchanged)

### From Your Mac:
```bash
./ssh_commands.sh block           # Block both YouTube and Roblox
./ssh_commands.sh allow           # Allow both YouTube and Roblox
./ssh_commands.sh block-roblox    # Block only Roblox
./ssh_commands.sh allow-roblox    # Allow only Roblox
./ssh_commands.sh status          # Check all statuses
```

## 🚫 Roblox Domains Blocked

The following Roblox domains will be blocked:
- `roblox.com` - Main Roblox website
- `rbxcdn.com` - Content delivery network
- `rbxtrk.com` - Tracking services
- `roblox.plus` - Third-party Roblox services
- `ecsv2.roblox.com` - API services
- `client-telemetry.roblox.com` - Telemetry data
- `metrics.roblox.com` - Analytics
- `tracing.roblox.com` - Performance tracking
- Plus 20+ additional Roblox service domains

## ✅ Scratch Domains Whitelisted

The following Scratch domains will remain accessible:
- `scratch.mit.edu` - Main Scratch website
- `api.scratch.mit.edu` - Scratch API
- `projects.scratch.mit.edu` - Project hosting
- `cdn.scratch.mit.edu` - Content delivery
- `assets.scratch.mit.edu` - Asset storage
- `clouddata.scratch.mit.edu` - Cloud storage
- `download.scratch.mit.edu` - Downloads
- `scratch-edu.mit.edu` - Educational resources
- `scratchjr.mit.edu` - Scratch Jr
- Plus all required dependencies (recaptcha, gstatic, wistia, etc.)

## 📱 Display Screen Information

Your Pi-hole LCD screen will now show:
- **Primary Status**: YouTube BLOCKED/ALLOWED (red/green background)
- **Secondary Line**: Roblox: BLOCKED/ALLOWED
- **Third Line**: Scratch: OK (or BLOCKED! in yellow if there's an issue)
- **Clock**: Current date and time

## 🔧 Troubleshooting

### If Roblox Still Works:
```bash
# Check if domains are actually blocked
pihole -q roblox.com
pihole -q rbxcdn.com

# If not blocked, manually add them
sudo pihole -b roblox.com rbxcdn.com rbxtrk.com
```

### If Scratch Doesn't Work:
```bash
# Check if Scratch is blocked
pihole -q scratch.mit.edu

# If blocked, whitelist it
sudo pihole -w scratch.mit.edu
sudo pihole -w api.scratch.mit.edu
sudo pihole -w projects.scratch.mit.edu
```

### If Display Doesn't Update:
```bash
# Check display service status
sudo systemctl status tft-youtube.service

# Force refresh
sudo systemctl kill --signal=SIGUSR1 tft-youtube.service

# Check logs
sudo journalctl -u tft-youtube.service -f
```

## 🧪 Testing

### Test Roblox Blocking:
1. Try to access `roblox.com` - should be blocked
2. Try to access `rbxcdn.com` - should be blocked
3. Check your Pi-hole screen - should show "Roblox: BLOCKED"

### Test Scratch Access:
1. Try to access `scratch.mit.edu` - should work
2. Try to access `projects.scratch.mit.edu` - should work
3. Check your Pi-hole screen - should show "Scratch: OK"

### Test Commands:
```bash
# Test individual commands
ys  # Should show all statuses
rb  # Should block only Roblox
ru  # Should allow only Roblox
yb  # Should block both YouTube and Roblox
yu  # Should allow both YouTube and Roblox
```

## 📋 Verification Checklist

- [ ] Roblox domains are blocked
- [ ] Scratch domains are accessible
- [ ] Display shows correct statuses
- [ ] Physical buttons work correctly
- [ ] SSH commands work from Mac
- [ ] Status script shows all services
- [ ] Pi-hole FTL service is running
- [ ] Display service is running

## 🎉 Success!

Once everything is working:
- Roblox will be blocked when you press the block button
- Scratch will always remain accessible for educational use
- Your display will show comprehensive status information
- You can control everything from your Mac via SSH

The system now provides granular control over gaming content while preserving educational programming access!
