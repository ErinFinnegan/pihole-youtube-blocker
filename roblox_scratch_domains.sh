#!/bin/bash

# Pi-hole Domain Configuration Script
# Blocks Roblox domains and ensures Scratch domains are whitelisted
# Run this script on your Pi to configure the domains

echo "🎮 Configuring Pi-hole domains for Roblox blocking and Scratch whitelisting..."
echo ""

# Function to add domains to blacklist
block_domains() {
    echo "🚫 Blocking Roblox domains..."
    
    # Core Roblox domains
    pihole -b roblox.com
    pihole -b rbxcdn.com
    pihole -b rbxtrk.com
    pihole -b roblox.plus
    
    # Roblox API and services
    pihole -b ecsv2.roblox.com
    pihole -b ncs.roblox.com
    pihole -b client-telemetry.roblox.com
    pihole -b presence.roblox.com
    pihole -b gold.roblox.com
    pihole -b lms.roblox.com
    pihole -b metrics.roblox.com
    pihole -b tracing.roblox.com
    
    # Regional Roblox servers
    pihole -b dfw2-128-116-95-3.roblox.com
    pihole -b ams2-128-116-21-3.roblox.com
    pihole -b atl1-128-116-99-3.roblox.com
    pihole -b lax2-128-116-116-3.roblox.com
    pihole -b nrt1-128-116-120-3.roblox.com
    pihole -b ord2-128-116-101-3.roblox.com
    
    # Additional Roblox tracking domains
    pihole -b setup.roblox.com
    pihole -b version.roblox.com
    pihole -b assetdelivery.roblox.com
    pihole -b thumbs.roblox.com
    pihole -b thumbnails.roblox.com
    pihole -b avatar.roblox.com
    pihole -b avatar.roblox.com
    pihole -b catalog.roblox.com
    pihole -b economy.roblox.com
    pihole -b friends.roblox.com
    pihole -b groups.roblox.com
    pihole -b inventory.roblox.com
    pihole -b itemconfiguration.roblox.com
    pihole -b locale.roblox.com
    pihole -b localization.roblox.com
    pihole -b notifications.roblox.com
    pihole -b publish.roblox.com
    pihole -b realtime.roblox.com
    pihole -b share.roblox.com
    pihole -b textfilter.roblox.com
    pihole -b thumbnails.roblox.com
    pihole -b trades.roblox.com
    pihole -b translation.roblox.com
    pihole -b users.roblox.com
    pihole -b voice.roblox.com
    
    echo "✅ Roblox domains blocked successfully!"
}

# Function to whitelist Scratch domains
whitelist_scratch() {
    echo "✅ Whitelisting Scratch domains..."
    
    # Core Scratch domains
    pihole -w scratch.mit.edu
    pihole -w api.scratch.mit.edu
    pihole -w projects.scratch.mit.edu
    pihole -w cdn.scratch.mit.edu
    pihole -w cdn2.scratch.mit.edu
    pihole -w assets.scratch.mit.edu
    pihole -w clouddata.scratch.mit.edu
    pihole -w download.scratch.mit.edu
    pihole -w downloads.scratch.mit.edu
    pihole -w uploads.scratch.mit.edu
    pihole -w scratch-edu.mit.edu
    pihole -w scratchjr.mit.edu
    
    # Scratch dependencies
    pihole -w recaptcha.net
    pihole -w www.recaptcha.net
    pihole -w gstatic.com
    pihole -w www.gstatic.com
    pihole -w fonts.gstatic.com
    pihole -w wistia.com
    pihole -w fast.wistia.net
    pihole -w wistia.net
    pihole -w akamaihd.net
    pihole -w embedwistia-a.akamaihd.net
    
    # Additional Scratch-related domains
    pihole -w mit.edu
    pihole -w web.mit.edu
    pihole -w media.mit.edu
    
    echo "✅ Scratch domains whitelisted successfully!"
}

# Function to verify configuration
verify_config() {
    echo "🔍 Verifying domain configuration..."
    echo ""
    
    echo "Checking if Roblox is blocked:"
    if pihole -q roblox.com | grep -q "BLOCKED"; then
        echo "✅ roblox.com is blocked"
    else
        echo "❌ roblox.com is NOT blocked"
    fi
    
    echo ""
    echo "Checking if Scratch is accessible:"
    if pihole -q scratch.mit.edu | grep -q "OK"; then
        echo "✅ scratch.mit.edu is accessible"
    else
        echo "❌ scratch.mit.edu is blocked (this is bad!)"
    fi
    
    echo ""
    echo "Domain configuration verification complete!"
}

# Main execution
main() {
    echo "Starting Pi-hole domain configuration..."
    echo ""
    
    # Check if running as root or with sudo
    if [[ $EUID -ne 0 ]]; then
        echo "❌ This script must be run as root or with sudo"
        echo "Usage: sudo $0"
        exit 1
    fi
    
    # Check if pihole command is available
    if ! command -v pihole &> /dev/null; then
        echo "❌ Pi-hole is not installed or not in PATH"
        exit 1
    fi
    
    # Execute domain configuration
    block_domains
    echo ""
    whitelist_scratch
    echo ""
    
    # Reload Pi-hole configuration
    echo "🔄 Reloading Pi-hole configuration..."
    pihole restartdns
    echo ""
    
    # Verify the configuration
    verify_config
    
    echo ""
    echo "🎉 Domain configuration complete!"
    echo ""
    echo "Summary:"
    echo "- Roblox domains have been blocked"
    echo "- Scratch domains have been whitelisted"
    echo "- Pi-hole configuration has been reloaded"
    echo ""
    echo "You can now test by:"
    echo "1. Trying to access roblox.com (should be blocked)"
    echo "2. Trying to access scratch.mit.edu (should work)"
}

# Run the main function
main "$@"
