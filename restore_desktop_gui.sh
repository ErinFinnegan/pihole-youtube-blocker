#!/bin/bash

# Script to restore desktop GUI while preserving PiTFT functionality
# Run this on your Pi to diagnose and fix the display issues

echo "🖥️  Pi-hole Desktop GUI Restore Script"
echo "======================================"
echo ""

# Function to check current status
check_status() {
    echo "📋 Current System Status:"
    echo "------------------------"
    
    # Check if desktop environment is installed
    if dpkg -l | grep -q "raspberrypi-ui-mods\|lxde\|xfce4"; then
        echo "✅ Desktop environment is installed"
    else
        echo "❌ Desktop environment is NOT installed"
    fi
    
    # Check if desktop is enabled
    if systemctl is-enabled lightdm >/dev/null 2>&1; then
        echo "✅ Display manager (lightdm) is enabled"
    else
        echo "❌ Display manager (lightdm) is NOT enabled"
    fi
    
    # Check if desktop is running
    if systemctl is-active lightdm >/dev/null 2>&1; then
        echo "✅ Display manager is running"
    else
        echo "❌ Display manager is NOT running"
    fi
    
    # Check boot configuration
    echo ""
    echo "🔧 Boot Configuration (/boot/config.txt):"
    echo "----------------------------------------"
    if grep -q "dtoverlay=pitft" /boot/config.txt; then
        echo "✅ PiTFT overlay is configured"
        grep "dtoverlay=pitft" /boot/config.txt
    else
        echo "❌ PiTFT overlay not found"
    fi
    
    if grep -q "hdmi_force_hotplug=1" /boot/config.txt; then
        echo "✅ HDMI hotplug is enabled"
    else
        echo "❌ HDMI hotplug is disabled"
    fi
    
    if grep -q "hdmi_drive=2" /boot/config.txt; then
        echo "✅ HDMI drive mode is set"
    else
        echo "❌ HDMI drive mode not set"
    fi
    
    echo ""
    echo "📺 Display Information:"
    echo "----------------------"
    if command -v xrandr >/dev/null 2>&1; then
        echo "Available displays:"
        xrandr --query 2>/dev/null || echo "Cannot query displays (X11 not running)"
    else
        echo "xrandr not available"
    fi
}

# Function to install desktop environment
install_desktop() {
    echo ""
    echo "🛠️  Installing Desktop Environment..."
    echo "===================================="
    
    # Update package list
    sudo apt update
    
    # Install desktop environment
    sudo apt install -y raspberrypi-ui-mods
    
    # Install additional useful packages
    sudo apt install -y xserver-xorg-video-fbdev
    
    echo "✅ Desktop environment installed"
}

# Function to enable desktop
enable_desktop() {
    echo ""
    echo "🚀 Enabling Desktop Environment..."
    echo "================================="
    
    # Enable display manager
    sudo systemctl enable lightdm
    
    # Start display manager
    sudo systemctl start lightdm
    
    echo "✅ Desktop environment enabled and started"
}

# Function to configure dual display
configure_dual_display() {
    echo ""
    echo "🖥️  Configuring Dual Display Setup..."
    echo "===================================="
    
    # Backup original config
    sudo cp /boot/config.txt /boot/config.txt.backup.$(date +%Y%m%d_%H%M%S)
    
    # Create optimized config for dual display
    cat > /tmp/config_dual_display.txt << 'EOF'
# PiTFT Configuration (keep existing)
dtoverlay=pitft35-resistive,rotate=270,speed=32000000,fps=20
dtoverlay=pitft35-resistive,rotate=270,speed=32000000,fps=20

# HDMI Configuration (restore desktop)
hdmi_force_hotplug=1
hdmi_drive=2
hdmi_group=2
hdmi_mode=82
hdmi_cvt=1024 768 60 6 0 0 0

# Display priority (HDMI first, then PiTFT)
display_default_lcd=0
display_default_hdmi=1

# GPU memory split (increase for desktop)
gpu_mem=128

# Enable composite video (optional)
enable_uart=1
EOF
    
    echo "📝 New configuration created. Review it:"
    cat /tmp/config_dual_display.txt
    
    echo ""
    read -p "Apply this configuration? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        # Apply the configuration
        sudo cp /tmp/config_dual_display.txt /boot/config.txt
        echo "✅ Configuration applied. Reboot required."
    else
        echo "❌ Configuration not applied."
    fi
}

# Function to create X11 configuration
create_x11_config() {
    echo ""
    echo "🎨 Creating X11 Configuration..."
    echo "==============================="
    
    # Create X11 configuration directory if it doesn't exist
    sudo mkdir -p /etc/X11/xorg.conf.d
    
    # Create configuration for dual display
    sudo tee /etc/X11/xorg.conf.d/99-pitft-hdmi.conf > /dev/null << 'EOF'
Section "Device"
    Identifier "HDMI"
    Driver "fbdev"
    Option "fbdev" "/dev/fb0"
EndSection

Section "Device"
    Identifier "PiTFT"
    Driver "fbdev"
    Option "fbdev" "/dev/fb1"
EndSection

Section "Monitor"
    Identifier "HDMI"
    Option "Primary" "true"
EndSection

Section "Monitor"
    Identifier "PiTFT"
    Option "RightOf" "HDMI"
EndSection

Section "Screen"
    Identifier "Screen0"
    Device "HDMI"
    Monitor "HDMI"
    DefaultDepth 24
    SubSection "Display"
        Depth 24
        Modes "1024x768"
    EndSubSection
EndSection
EOF
    
    echo "✅ X11 configuration created"
}

# Function to test displays
test_displays() {
    echo ""
    echo "🧪 Testing Display Configuration..."
    echo "================================="
    
    echo "Checking PiTFT:"
    if [ -e /dev/fb1 ]; then
        echo "✅ PiTFT framebuffer (/dev/fb1) exists"
    else
        echo "❌ PiTFT framebuffer not found"
    fi
    
    echo ""
    echo "Checking HDMI:"
    if [ -e /dev/fb0 ]; then
        echo "✅ HDMI framebuffer (/dev/fb0) exists"
    else
        echo "❌ HDMI framebuffer not found"
    fi
    
    echo ""
    echo "Checking display services:"
    systemctl status lightdm --no-pager -l
}

# Main menu
main() {
    echo "Choose an option:"
    echo "1. Check current status"
    echo "2. Install desktop environment"
    echo "3. Enable desktop environment"
    echo "4. Configure dual display"
    echo "5. Create X11 configuration"
    echo "6. Test displays"
    echo "7. Do everything (full restore)"
    echo "8. Exit"
    echo ""
    read -p "Enter your choice (1-8): " choice
    
    case $choice in
        1)
            check_status
            ;;
        2)
            install_desktop
            ;;
        3)
            enable_desktop
            ;;
        4)
            configure_dual_display
            ;;
        5)
            create_x11_config
            ;;
        6)
            test_displays
            ;;
        7)
            echo "🚀 Performing full restore..."
            check_status
            install_desktop
            enable_desktop
            configure_dual_display
            create_x11_config
            test_displays
            echo ""
            echo "🎉 Full restore complete!"
            echo "You may need to reboot for all changes to take effect."
            ;;
        8)
            echo "Goodbye!"
            exit 0
            ;;
        *)
            echo "Invalid choice. Please try again."
            main
            ;;
    esac
    
    echo ""
    read -p "Press Enter to continue..."
    main
}

# Check if running as root
if [[ $EUID -eq 0 ]]; then
    echo "⚠️  Warning: Running as root. Some operations may not work correctly."
    echo "It's recommended to run this script as a regular user with sudo access."
    echo ""
fi

# Start the main menu
main
