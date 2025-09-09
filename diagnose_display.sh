#!/bin/bash

# Quick diagnostic script to check what happened to your desktop
# Run this on your Pi to see the current state

echo "🔍 Pi-hole Display Diagnostic"
echo "============================="
echo ""

echo "📋 System Information:"
echo "---------------------"
echo "OS: $(cat /etc/os-release | grep PRETTY_NAME | cut -d'"' -f2)"
echo "Kernel: $(uname -r)"
echo "Architecture: $(uname -m)"
echo ""

echo "🖥️  Desktop Environment Status:"
echo "------------------------------"
if dpkg -l | grep -q "raspberrypi-ui-mods"; then
    echo "✅ Raspberry Pi UI is installed"
else
    echo "❌ Raspberry Pi UI is NOT installed"
fi

if dpkg -l | grep -q "lxde"; then
    echo "✅ LXDE is installed"
else
    echo "❌ LXDE is NOT installed"
fi

if systemctl is-enabled lightdm >/dev/null 2>&1; then
    echo "✅ LightDM (display manager) is enabled"
else
    echo "❌ LightDM is NOT enabled"
fi

if systemctl is-active lightdm >/dev/null 2>&1; then
    echo "✅ LightDM is running"
else
    echo "❌ LightDM is NOT running"
fi

echo ""
echo "📺 Display Configuration:"
echo "------------------------"
echo "Boot config (/boot/config.txt):"
if [ -f /boot/config.txt ]; then
    echo "PiTFT settings:"
    grep -i "pitft\|st7789" /boot/config.txt || echo "  No PiTFT settings found"
    echo ""
    echo "HDMI settings:"
    grep -i "hdmi" /boot/config.txt || echo "  No HDMI settings found"
    echo ""
    echo "Display settings:"
    grep -i "display\|fb" /boot/config.txt || echo "  No display settings found"
else
    echo "❌ /boot/config.txt not found"
fi

echo ""
echo "🖼️  Framebuffer Devices:"
echo "----------------------"
ls -la /dev/fb* 2>/dev/null || echo "No framebuffer devices found"

echo ""
echo "🎮 PiTFT Service Status:"
echo "----------------------"
if systemctl list-units --type=service | grep -q "tft-youtube"; then
    echo "✅ tft-youtube service found"
    systemctl status tft-youtube --no-pager -l
else
    echo "❌ tft-youtube service not found"
fi

echo ""
echo "🖥️  X11 Status:"
echo "-------------"
if pgrep -x "Xorg" > /dev/null; then
    echo "✅ X server is running"
    echo "Display: $DISPLAY"
else
    echo "❌ X server is NOT running"
fi

echo ""
echo "📱 PiTFT Display Test:"
echo "--------------------"
if [ -e /dev/fb1 ]; then
    echo "✅ PiTFT framebuffer (/dev/fb1) exists"
    echo "Testing PiTFT display..."
    # Simple test - clear the screen
    sudo dd if=/dev/zero of=/dev/fb1 bs=1024 count=1024 2>/dev/null && echo "✅ PiTFT display test successful" || echo "❌ PiTFT display test failed"
else
    echo "❌ PiTFT framebuffer not found"
fi

echo ""
echo "🔧 Quick Fixes to Try:"
echo "--------------------"
echo "1. Enable desktop: sudo systemctl enable lightdm && sudo systemctl start lightdm"
echo "2. Install desktop: sudo apt update && sudo apt install -y raspberrypi-ui-mods"
echo "3. Check boot config: sudo nano /boot/config.txt"
echo "4. Reboot: sudo reboot"
echo ""
echo "For detailed restoration, run: ./restore_desktop_gui.sh"
