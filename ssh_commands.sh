#!/bin/bash

# SSH commands for controlling Pi-hole YouTube blocking from your Mac
# Replace 'zerocool@pi-hole.local' with your actual Pi SSH address

PI_USER="zerocool"
PI_HOST="pi-hole.local"  # or use IP like 192.168.1.167

echo "Pi-hole YouTube Control via SSH"
echo "================================"
echo ""

# Function to run command on Pi
run_on_pi() {
    ssh "$PI_USER@$PI_HOST" "$1"
}

# Block YouTube
block_youtube() {
    echo "Blocking YouTube on Pi-hole..."
    run_on_pi "yb"
    echo "Done! Check your Pi-hole screen."
}

# Allow YouTube  
allow_youtube() {
    echo "Allowing YouTube on Pi-hole..."
    run_on_pi "yu"
    echo "Done! Check your Pi-hole screen."
}

# Check status
check_status() {
    echo "Checking YouTube status on Pi-hole..."
    run_on_pi "ys"
}

# Force display refresh
refresh_display() {
    echo "Forcing display refresh..."
    run_on_pi "sudo systemctl kill --signal=SIGUSR1 tft-youtube.service"
    echo "Display refresh signal sent!"
}

# Main menu
case "$1" in
    "block"|"b")
        block_youtube
        ;;
    "allow"|"a")
        allow_youtube
        ;;
    "status"|"s")
        check_status
        ;;
    "refresh"|"r")
        refresh_display
        ;;
    *)
        echo "Usage: $0 {block|allow|status|refresh}"
        echo ""
        echo "Commands:"
        echo "  block, b    - Block YouTube"
        echo "  allow, a    - Allow YouTube"
        echo "  status, s   - Check current status"
        echo "  refresh, r  - Force display refresh"
        echo ""
        echo "Examples:"
        echo "  $0 block"
        echo "  $0 allow"
        echo "  $0 status"
        ;;
esac
