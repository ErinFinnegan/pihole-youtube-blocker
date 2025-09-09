#!/bin/bash

# Session Control Script for Pi-hole
# Provides easy commands to monitor and control active sessions

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SESSION_MONITOR="$SCRIPT_DIR/session_monitor.py"

# Function to show help
show_help() {
    echo "🎮 Pi-hole Session Control"
    echo "========================="
    echo ""
    echo "Commands:"
    echo "  status     - Show current session status"
    echo "  list       - List all active sessions"
    echo "  terminate  - Terminate a specific session"
    echo "  monitor    - Start continuous monitoring"
    echo "  help       - Show this help"
    echo ""
    echo "Examples:"
    echo "  $0 status"
    echo "  $0 list"
    echo "  $0 terminate 192.168.1.100"
    echo "  $0 monitor"
}

# Function to check if session monitor exists
check_monitor() {
    if [ ! -f "$SESSION_MONITOR" ]; then
        echo "❌ Session monitor script not found at: $SESSION_MONITOR"
        echo "Please ensure session_monitor.py is in the same directory."
        exit 1
    fi
}

# Function to show session status
show_status() {
    echo "📊 Checking session status..."
    python3 "$SESSION_MONITOR" status
}

# Function to list active sessions
list_sessions() {
    echo "📱 Active Sessions:"
    python3 "$SESSION_MONITOR" list
}

# Function to terminate a session
terminate_session() {
    if [ -z "$1" ]; then
        echo "❌ Please specify a client IP address"
        echo "Usage: $0 terminate <client_ip>"
        echo ""
        echo "First, list active sessions:"
        list_sessions
        exit 1
    fi
    
    echo "🛑 Terminating session for $1..."
    python3 "$SESSION_MONITOR" terminate "$1"
}

# Function to start monitoring
start_monitoring() {
    echo "🎮 Starting session monitoring..."
    echo "Press Ctrl+C to stop"
    python3 "$SESSION_MONITOR" monitor
}

# Main command handling
case "$1" in
    "status"|"s")
        check_monitor
        show_status
        ;;
    "list"|"l")
        check_monitor
        list_sessions
        ;;
    "terminate"|"t")
        check_monitor
        terminate_session "$2"
        ;;
    "monitor"|"m")
        check_monitor
        start_monitoring
        ;;
    "help"|"h"|"")
        show_help
        ;;
    *)
        echo "❌ Unknown command: $1"
        echo ""
        show_help
        exit 1
        ;;
esac
