# Pi-hole LCD Screen Deployment Instructions

## 🚀 How to Deploy the Enhanced Dual-Button System with Session Monitoring

### Prerequisites
- Raspberry Pi Zero WH with Pi-hole installed
- Mini PiTFT 135×240 ST7789 display
- SSH access to your Pi
- Current display service running as `tft-youtube.service`

### Step 1: Test the System Locally (Recommended)

Before deploying to your Pi, test the dual-button functionality:

```bash
# Test the mock system
python3 Screen_status_mock_dual.py
```

**Test Features:**
- Click "BTN1: Toggle YouTube & Roblox" to test blocking toggle
- Click "BTN2: Kill Active Sessions" to test session termination
- Watch the display change colors and show feedback

### Step 2: Deploy Session Monitoring System

Copy the session monitoring files to your Pi:

```bash
# Copy session monitoring files
scp session_monitor.py zerocool@pi-hole.local:~/
scp session_control.sh zerocool@pi-hole.local:~/

# Make scripts executable
ssh zerocool@pi-hole.local "chmod +x session_monitor.py session_control.sh"
```

### Step 3: Deploy Enhanced Display Script

Copy the dual-button display script to your Pi:

```bash
# Copy enhanced display script
scp Screen_status_dual_buttons.py zerocool@pi-hole.local:~/tft-youtube-status.py
```

### Step 4: Install Enhanced Blocking Scripts (Optional)

If you want the enhanced blocking scripts with Roblox support:

```bash
# First, run the setup script to create all the individual command files
bash /usr/local/bin/yb_enhanced

# The setup script will create and install all the commands automatically
# Now make them executable (they should exist after running the setup script)
sudo chmod +x /usr/local/bin/y{b,u,s} /usr/local/bin/r{b,u}
```

### Step 5: Restart Display Service

```bash
# Restart the display service to load the new code
sudo systemctl restart tft-youtube.service

# Check that it's running properly
sudo systemctl status tft-youtube.service
```

### Step 6: Test the Dual-Button System

#### Test Physical Buttons
- **Press Button 1 (Left - GPIO 23)**: Should show blue "TOGGLING..." screen
- **Press Button 2 (Right - GPIO 24)**: Should show purple "KILLING SESSIONS..." screen
- **Watch for confirmations**: Yellow "STATUS CHANGED!" or "KILLED X SESSIONS!"
- **Verify final status**: Background color changes (red=blocked, green=allowed)

#### Test Session Monitoring
```bash
# Check session status
ssh zerocool@pi-hole.local "./session_control.sh status"

# List active sessions
ssh zerocool@pi-hole.local "./session_control.sh list"

# Start continuous monitoring
ssh zerocool@pi-hole.local "./session_control.sh monitor"
```

#### Test SSH Commands (Enhanced)
From your Mac, use the enhanced SSH control script:

```bash
# Make the script executable (if not already)
chmod +x ssh_commands.sh

# Test blocking YouTube and Roblox
./ssh_commands.sh block

# Test allowing YouTube and Roblox
./ssh_commands.sh allow

# Test blocking only Roblox
./ssh_commands.sh block-roblox

# Test allowing only Roblox
./ssh_commands.sh allow-roblox

# Check current status
./ssh_commands.sh status

# Force display refresh if needed
./ssh_commands.sh refresh
```

### Step 7: Verify Everything Works

1. **Dual Button Feedback**: 
   - Button 1: Blue "TOGGLING..." screen
   - Button 2: Purple "KILLING SESSIONS..." screen
2. **Status Confirmation**: Watch for yellow confirmation screens
3. **Session Monitoring**: Check that active sessions are detected and displayed
4. **SSH Updates**: Run commands via SSH and verify screen updates immediately
5. **Final States**: Confirm red screen = blocked, green screen = allowed

### Troubleshooting

#### If Screen Doesn't Update After SSH Commands:
```bash
# Check if the display service is running
sudo systemctl status tft-youtube.service

# Check service logs for errors
sudo journalctl -u tft-youtube.service -f

# Force a manual refresh
sudo systemctl kill --signal=SIGUSR1 tft-youtube.service
```

#### If Buttons Don't Respond:
```bash
# Check GPIO permissions
ls -la /dev/gpiomem

# Verify button mapping with test script
python3 -c "
import RPi.GPIO as GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setup(23, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(24, GPIO.IN, pull_up_down=GPIO.PUD_UP)
print('GPIO 23 (Toggle):', GPIO.input(23))
print('GPIO 24 (Kill):', GPIO.input(24))
"
```

#### If Session Monitoring Doesn't Work:
```bash
# Check session monitor
./session_control.sh status

# Check Pi-hole database access
sudo sqlite3 /etc/pihole/pihole-FTL.db "SELECT COUNT(*) FROM queries;"

# Check recent queries
sudo sqlite3 /etc/pihole/pihole-FTL.db "SELECT domain, client, timestamp FROM queries ORDER BY timestamp DESC LIMIT 10;"
```

#### If Pi-hole Commands Fail:
```bash
# Test the blocking scripts directly
sudo /usr/local/bin/yb
sudo /usr/local/bin/yu
sudo /usr/local/bin/ys

# Check Pi-hole FTL service
sudo systemctl status pihole-FTL
```

### Features Added

✅ **Dual Button Functionality**: 
- Button 1: Toggle YouTube/Roblox blocking
- Button 2: Kill all active sessions
✅ **Session Monitoring**: Real-time detection of active YouTube/Roblox sessions  
✅ **Session Termination**: Kill active sessions by blocking their domains  
✅ **Enhanced Display**: Shows active session counts and button instructions  
✅ **Immediate Button Feedback**: Color-coded screens for different actions  
✅ **Status Change Confirmation**: Yellow screen with detailed confirmations  
✅ **SSH-Triggered Updates**: Screen updates immediately when commands run via SSH  
✅ **Threading Support**: Non-blocking button operations  
✅ **Signal Handling**: Display service responds to refresh signals  
✅ **Enhanced Error Handling**: Better reliability and debugging  

### Files Modified/Created

- `Screen_status_dual_buttons.py` - Enhanced display service with dual buttons
- `Screen_status_mock_dual.py` - Mock version for testing dual-button functionality
- `session_monitor.py` - Core session detection and termination system
- `session_control.sh` - Command-line interface for session management
- `enhanced_blocking_scripts.sh` - Enhanced blocking/unblocking scripts with Roblox support
- `ssh_commands.sh` - Enhanced SSH control script with Roblox commands
- `dual_button_deployment.md` - Comprehensive dual-button setup guide
- `session_monitoring_setup.md` - Session monitoring setup guide
- `deploy.md` - This updated deployment guide

The system now provides powerful dual-button control with real-time session monitoring, ensuring you have complete control over YouTube/Roblox access while preserving educational content like Scratch!
