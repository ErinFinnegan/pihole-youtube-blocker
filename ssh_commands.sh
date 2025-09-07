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

# Block YouTube and Roblox
block_youtube() {
    echo "Blocking YouTube and Roblox on Pi-hole..."
    run_on_pi "yb"
    echo "Done! Check your Pi-hole screen."
}

# Allow YouTube and Roblox
allow_youtube() {
    echo "Allowing YouTube and Roblox on Pi-hole..."
    run_on_pi "yu"
    echo "Done! Check your Pi-hole screen."
}

# Block Roblox only
block_roblox() {
    echo "Blocking Roblox only on Pi-hole..."
    run_on_pi "rb"
    echo "Done! Check your Pi-hole screen."
}

# Allow Roblox only
allow_roblox() {
    echo "Allowing Roblox only on Pi-hole..."
    run_on_pi "ru"
    echo "Done! Check your Pi-hole screen."
}

# Check status
check_status() {
    echo "Checking YouTube, Roblox, and Scratch status on Pi-hole..."
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
    "block-roblox"|"br")
        block_roblox
        ;;
    "allow-roblox"|"ar")
        allow_roblox
        ;;
    "status"|"s")
        check_status
        ;;
    "refresh"|"r")
        refresh_display
        ;;
    *)
        echo "Usage: $0 {block|allow|block-roblox|allow-roblox|status|refresh}"
        echo ""
        echo "Commands:"
        echo "  block, b           - Block YouTube and Roblox"
        echo "  allow, a           - Allow YouTube and Roblox"
        echo "  block-roblox, br   - Block Roblox only (YouTube unchanged)"
        echo "  allow-roblox, ar   - Allow Roblox only (YouTube unchanged)"
        echo "  status, s          - Check current status of all services"
        echo "  refresh, r         - Force display refresh"
        echo ""
        echo "Examples:"
        echo "  $0 block           # Block both YouTube and Roblox"
        echo "  $0 allow           # Allow both YouTube and Roblox"
        echo "  $0 block-roblox    # Block only Roblox"
        echo "  $0 allow-roblox    # Allow only Roblox"
        echo "  $0 status          # Check all statuses"
        echo ""
        echo "Note: All commands ensure Scratch domains remain whitelisted!"
        ;;
esac
