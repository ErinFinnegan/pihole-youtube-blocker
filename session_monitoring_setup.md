# Pi-hole Session Monitoring & Termination Setup

## 🎯 Overview
This system detects active YouTube/Roblox sessions through Pi-hole DNS logs and can terminate them by blocking domains mid-session.

## 🚀 Quick Setup

### Step 1: Install Session Monitor
```bash
# Copy files to your Pi
scp session_monitor.py zerocool@pi-hole.local:~/
scp session_control.sh zerocool@pi-hole.local:~/

# Make scripts executable
ssh zerocool@pi-hole.local "chmod +x session_monitor.py session_control.sh"
```

### Step 2: Test Session Detection
```bash
# Check current session status
ssh zerocool@pi-hole.local "./session_control.sh status"

# List active sessions
ssh zerocool@pi-hole.local "./session_control.sh list"
```

### Step 3: Integrate with Display (Optional)
```bash
# Copy enhanced display script
scp Screen_status_with_sessions.py zerocool@pi-hole.local:~/tft-youtube-status.py

# Restart display service
ssh zerocool@pi-hole.local "sudo systemctl restart tft-youtube.service"
```

## 🎮 How It Works

### Session Detection
- **Monitors Pi-hole DNS logs** for YouTube/Roblox domain requests
- **Tracks active sessions** by client IP address
- **Detects session end** after 5 minutes of inactivity
- **Updates every 30 seconds** for real-time monitoring

### Session Termination
- **Blocks specific domains** used by active sessions
- **Preserves other domains** (like Scratch)
- **Temporary blocking** - domains can be unblocked later
- **Immediate effect** - sessions lose connectivity instantly

## 📱 Available Commands

### Basic Commands
```bash
# Check session status
./session_control.sh status

# List all active sessions
./session_control.sh list

# Start continuous monitoring
./session_control.sh monitor
```

### Session Termination
```bash
# Terminate session for specific client
./session_control.sh terminate 192.168.1.100

# Example: Terminate YouTube session on iPad
./session_control.sh terminate 192.168.1.150
```

### Direct Python Commands
```bash
# Get session status
python3 session_monitor.py status

# List active sessions
python3 session_monitor.py list

# Terminate specific session
python3 session_monitor.py terminate 192.168.1.100

# Start monitoring
python3 session_monitor.py monitor
```

## 🖥️ Display Integration

### Enhanced Display Features
- **Shows active session counts** (YT:2 RB:1)
- **Orange indicator** when sessions are active
- **Real-time updates** every 30 seconds
- **Maintains all existing features** (button feedback, status confirmation)

### Display States
- **Normal**: Shows YouTube/Roblox/Scratch status + active sessions
- **Button Press**: Blue screen with "BLOCKING..." or "ALLOWING..."
- **Status Change**: Yellow screen with "STATUS CHANGED!" confirmation
- **Active Sessions**: Orange text showing session counts

## 🔧 Advanced Configuration

### Customize Session Timeout
Edit `session_monitor.py` and change:
```python
self.session_timeout = 300  # 5 minutes (change to desired seconds)
```

### Add More Domains
Edit the domain lists in `session_monitor.py`:
```python
self.youtube_domains = {
    'youtube.com', 'www.youtube.com', 'm.youtube.com',
    # Add more YouTube domains here
}

self.roblox_domains = {
    'roblox.com', 'www.roblox.com', 'rbxcdn.com',
    # Add more Roblox domains here
}
```

### Customize Display Refresh
Edit the refresh interval in `Screen_status_with_sessions.py`:
```python
# Check for active sessions every 30 seconds
if current_time - last_session_check > 30:  # Change 30 to desired seconds
```

## 🧪 Testing

### Test Session Detection
1. **Start a YouTube video** on a device
2. **Run session monitor**: `./session_control.sh status`
3. **Should show**: "YouTube: 1" or similar
4. **Stop the video** and wait 5 minutes
5. **Check again**: Should show "No active sessions"

### Test Session Termination
1. **Start a YouTube video** on a device
2. **Get the device IP**: `./session_control.sh list`
3. **Terminate session**: `./session_control.sh terminate <IP>`
4. **Video should stop** immediately
5. **Check status**: Should show "No active sessions"

## 🚨 Troubleshooting

### No Sessions Detected
```bash
# Check Pi-hole database access
sudo sqlite3 /etc/pihole/pihole-FTL.db "SELECT COUNT(*) FROM queries;"

# Check recent queries
sudo sqlite3 /etc/pihole/pihole-FTL.db "SELECT domain, client, timestamp FROM queries ORDER BY timestamp DESC LIMIT 10;"
```

### Session Termination Not Working
```bash
# Check if domains are being blocked
pihole -q youtube.com
pihole -q roblox.com

# Check Pi-hole blacklist
pihole -b -l
```

### Display Not Showing Sessions
```bash
# Check if enhanced display script is running
sudo systemctl status tft-youtube.service

# Check for errors
sudo journalctl -u tft-youtube.service -f
```

## 🎯 Use Cases

### Parental Control
- **Detect when kids start gaming** (YouTube/Roblox)
- **Terminate sessions remotely** via SSH
- **Monitor usage patterns** through session logs

### Network Management
- **Identify bandwidth-heavy sessions**
- **Temporarily block specific users**
- **Monitor network activity** in real-time

### Educational Environment
- **Allow educational content** (Scratch)
- **Block entertainment during study time**
- **Provide immediate feedback** on display

## 🔒 Security Notes

- **Requires sudo access** to read Pi-hole database
- **Temporary domain blocking** - can be reversed
- **No permanent data loss** - sessions can resume
- **Audit trail** - all actions are logged

## 📊 Monitoring & Logs

### Session Logs
```bash
# View session monitor logs
journalctl -u session-monitor.service -f

# Check Pi-hole logs
tail -f /var/log/pihole.log
```

### Performance Impact
- **Minimal CPU usage** (checks every 30 seconds)
- **Low memory footprint** (stores session data in RAM)
- **No disk I/O** (reads from Pi-hole database)
- **Network efficient** (only DNS monitoring)

This system provides powerful session control while maintaining the simplicity and reliability of your existing Pi-hole setup!
