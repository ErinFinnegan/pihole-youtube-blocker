# Dual-Button Pi-hole LCD Screen Deployment Guide

## 🎯 Overview
This enhanced system provides dual-button functionality:
- **Button 1 (Left)**: Toggle YouTube/Roblox blocking
- **Button 2 (Right)**: Kill all active sessions

## 🚀 Quick Setup

### Step 1: Test the Mock System
```bash
# Test the dual-button functionality locally
python3 Screen_status_mock_dual.py
```

**Test Features:**
- Click "BTN1: Toggle YouTube & Roblox" to test blocking toggle
- Click "Add YouTube Session" or "Add Roblox Session" to create test sessions
- Click "BTN2: Kill Active Sessions" to test session termination
- Watch the display change colors and show feedback

### Step 2: Deploy to Pi
```bash
# Copy session monitoring files
scp session_monitor.py zerocool@pi-hole.local:~/
scp session_control.sh zerocool@pi-hole.local:~/

# Copy enhanced display script
scp Screen_status_dual_buttons.py zerocool@pi-hole.local:~/tft-youtube-status.py

# Make scripts executable
ssh zerocool@pi-hole.local "chmod +x session_monitor.py session_control.sh"
```

### Step 3: Restart Services
```bash
# Restart the display service
ssh zerocool@pi-hole.local "sudo systemctl restart tft-youtube.service"

# Check service status
ssh zerocool@pi-hole.local "sudo systemctl status tft-youtube.service"
```

## 🎮 Button Functionality

### Button 1 (Left Button - GPIO 23)
- **Function**: Toggle YouTube/Roblox blocking
- **Behavior**: 
  - If blocked → Allow both YouTube and Roblox
  - If allowed → Block both YouTube and Roblox
- **Display**: Blue screen with "TOGGLING..." and animated dots
- **Confirmation**: Yellow screen with "STATUS CHANGED!"

### Button 2 (Right Button - GPIO 24)
- **Function**: Kill all active sessions
- **Behavior**: 
  - Detects all active YouTube/Roblox sessions
  - Terminates each session by blocking their domains
  - Shows count of terminated sessions
- **Display**: Purple screen with "KILLING SESSIONS..." and animated dots
- **Confirmation**: Yellow screen with "KILLED X SESSIONS!"

## 📱 Display States

### Normal Display
- **Background**: Red (blocked) or Green (allowed)
- **Title**: "YouTube BLOCKED" or "YouTube ALLOWED"
- **Status Lines**:
  - Roblox: BLOCKED/ALLOWED
  - Scratch: OK (or BLOCKED! in yellow if issue)
  - Active: YT:X RB:Y (orange if sessions active)
  - BTN1:Toggle BTN2:Kill (button instructions)

### Button Press Feedback
- **Toggle Button**: Blue background, "TOGGLING..." with dots
- **Kill Button**: Purple background, "KILLING SESSIONS..." with dots

### Status Confirmation
- **Yellow background** with black text
- **Toggle**: "STATUS CHANGED!" and "✓ DONE"
- **Kill**: "KILLED X SESSIONS!" and "✓ X SESSIONS TERMINATED"

## 🔧 Session Monitoring

### How It Works
1. **Monitors Pi-hole DNS logs** every 30 seconds
2. **Tracks active sessions** by client IP address
3. **Detects session end** after 5 minutes of inactivity
4. **Updates display** with real-time session counts

### Session Termination Process
1. **Detects active sessions** from DNS logs
2. **Blocks specific domains** used by each session
3. **Preserves other domains** (like Scratch)
4. **Shows confirmation** with count of terminated sessions

## 🧪 Testing

### Test Toggle Functionality
1. **Press Button 1** (left button)
2. **Should see**: Blue "TOGGLING..." screen
3. **Then see**: Yellow "STATUS CHANGED!" screen
4. **Final state**: Background color changes (red↔green)

### Test Session Killing
1. **Start a YouTube video** on a device
2. **Wait 30 seconds** for session detection
3. **Press Button 2** (right button)
4. **Should see**: Purple "KILLING SESSIONS..." screen
5. **Then see**: Yellow "KILLED X SESSIONS!" screen
6. **Video should stop** immediately

### Test Session Detection
1. **Start YouTube/Roblox** on multiple devices
2. **Watch display** - should show "Active: YT:X RB:Y"
3. **Stop all sessions** and wait 5 minutes
4. **Display should show** no active sessions

## 🚨 Troubleshooting

### Buttons Not Working
```bash
# Check GPIO setup
ssh zerocool@pi-hole.local "python3 -c '
import RPi.GPIO as GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setup(23, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(24, GPIO.IN, pull_up_down=GPIO.PUD_UP)
print(\"GPIO 23 (Toggle):\", GPIO.input(23))
print(\"GPIO 24 (Kill):\", GPIO.input(24))
'"
```

### Session Detection Not Working
```bash
# Check session monitor
ssh zerocool@pi-hole.local "./session_control.sh status"

# Check Pi-hole database
ssh zerocool@pi-hole.local "sudo sqlite3 /etc/pihole/pihole-FTL.db 'SELECT COUNT(*) FROM queries;'"
```

### Display Not Updating
```bash
# Check display service
ssh zerocool@pi-hole.local "sudo systemctl status tft-youtube.service"

# Check for errors
ssh zerocool@pi-hole.local "sudo journalctl -u tft-youtube.service -f"
```

## 📊 Advanced Features

### Session Monitoring Commands
```bash
# Check current status
ssh zerocool@pi-hole.local "./session_control.sh status"

# List active sessions
ssh zerocool@pi-hole.local "./session_control.sh list"

# Start continuous monitoring
ssh zerocool@pi-hole.local "./session_control.sh monitor"
```

### Manual Session Termination
```bash
# Terminate specific client
ssh zerocool@pi-hole.local "./session_control.sh terminate 192.168.1.100"
```

## 🎯 Use Cases

### Parental Control
- **Quick toggle** between study time (blocked) and free time (allowed)
- **Immediate session termination** when kids should stop gaming
- **Visual feedback** shows exactly what's happening

### Network Management
- **Emergency session killing** for bandwidth management
- **Quick policy changes** with single button press
- **Real-time monitoring** of network usage

### Educational Environment
- **Preserve educational access** (Scratch always works)
- **Control entertainment** during study hours
- **Provide immediate feedback** to users

## 🔒 Security & Safety

- **Temporary blocking** - domains can be unblocked
- **No permanent data loss** - sessions can resume
- **Audit trail** - all actions are logged
- **Fail-safe design** - errors don't break the system

## 📈 Performance

- **Minimal CPU usage** (checks every 30 seconds)
- **Low memory footprint** (stores session data in RAM)
- **No disk I/O** (reads from Pi-hole database)
- **Network efficient** (only DNS monitoring)

This dual-button system provides powerful, intuitive control over your Pi-hole while maintaining the simplicity and reliability of your existing setup!
