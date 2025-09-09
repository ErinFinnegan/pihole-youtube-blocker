#!/usr/bin/env python3

# Pi-hole Session Monitor
# Detects and terminates active YouTube/Roblox sessions

import time
import subprocess
import sqlite3
import json
from datetime import datetime, timedelta
from collections import defaultdict
import threading
import signal
import sys

class SessionMonitor:
    def __init__(self):
        self.pihole_db = "/etc/pihole/pihole-FTL.db"
        self.gravity_db = "/etc/pihole/gravity.db"
        self.session_timeout = 300  # 5 minutes of inactivity = session ended
        self.active_sessions = defaultdict(lambda: {'last_seen': 0, 'domains': set()})
        self.blocked_domains = set()
        self.running = True
        
        # YouTube and Roblox domains to monitor
        self.youtube_domains = {
            'youtube.com', 'www.youtube.com', 'm.youtube.com',
            'googlevideo.com', 'ytimg.com', 'youtube-nocookie.com',
            'youtubei.googleapis.com', 'youtube.googleapis.com'
        }
        
        self.roblox_domains = {
            'roblox.com', 'www.roblox.com', 'rbxcdn.com', 'rbxtrk.com',
            'ecsv2.roblox.com', 'client-telemetry.roblox.com',
            'presence.roblox.com', 'metrics.roblox.com'
        }
        
        # Signal handlers for clean shutdown
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
    
    def signal_handler(self, signum, frame):
        print(f"\nReceived signal {signum}, shutting down gracefully...")
        self.running = False
    
    def get_recent_queries(self, minutes=5):
        """Get recent DNS queries from Pi-hole database"""
        try:
            # Query the Pi-hole FTL database for recent queries
            cmd = [
                "sudo", "sqlite3", self.pihole_db,
                f"""
                SELECT domain, client, timestamp 
                FROM queries 
                WHERE timestamp > {int(time.time()) - (minutes * 60)}
                AND type = 1
                ORDER BY timestamp DESC
                """
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            if result.returncode != 0:
                print(f"Error querying Pi-hole database: {result.stderr}")
                return []
            
            queries = []
            for line in result.stdout.strip().split('\n'):
                if line:
                    parts = line.split('|')
                    if len(parts) >= 3:
                        queries.append({
                            'domain': parts[0],
                            'client': parts[1],
                            'timestamp': int(parts[2])
                        })
            
            return queries
            
        except Exception as e:
            print(f"Error getting recent queries: {e}")
            return []
    
    def detect_active_sessions(self):
        """Detect active YouTube/Roblox sessions"""
        current_time = time.time()
        recent_queries = self.get_recent_queries(5)  # Last 5 minutes
        
        # Clear old sessions
        for client in list(self.active_sessions.keys()):
            if current_time - self.active_sessions[client]['last_seen'] > self.session_timeout:
                del self.active_sessions[client]
        
        # Process recent queries
        for query in recent_queries:
            domain = query['domain'].lower()
            client = query['client']
            timestamp = query['timestamp']
            
            # Check if it's a YouTube or Roblox domain
            is_youtube = any(yt_domain in domain for yt_domain in self.youtube_domains)
            is_roblox = any(rb_domain in domain for rb_domain in self.roblox_domains)
            
            if is_youtube or is_roblox:
                if client not in self.active_sessions:
                    self.active_sessions[client] = {'last_seen': 0, 'domains': set()}
                
                self.active_sessions[client]['last_seen'] = max(
                    self.active_sessions[client]['last_seen'], 
                    timestamp
                )
                self.active_sessions[client]['domains'].add(domain)
    
    def get_active_sessions(self):
        """Get list of currently active sessions"""
        current_time = time.time()
        active = []
        
        for client, session in self.active_sessions.items():
            if current_time - session['last_seen'] <= self.session_timeout:
                # Determine session type
                session_type = []
                if any(yt_domain in ' '.join(session['domains']) for yt_domain in self.youtube_domains):
                    session_type.append('YouTube')
                if any(rb_domain in ' '.join(session['domains']) for rb_domain in self.roblox_domains):
                    session_type.append('Roblox')
                
                if session_type:
                    active.append({
                        'client': client,
                        'type': ' + '.join(session_type),
                        'last_seen': session['last_seen'],
                        'domains': list(session['domains'])
                    })
        
        return active
    
    def terminate_session(self, client):
        """Terminate a session by blocking all related domains"""
        if client not in self.active_sessions:
            return False
        
        session = self.active_sessions[client]
        blocked_count = 0
        
        for domain in session['domains']:
            if domain not in self.blocked_domains:
                try:
                    # Add domain to Pi-hole blacklist
                    cmd = ["sudo", "pihole", "-b", domain]
                    result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
                    
                    if result.returncode == 0:
                        self.blocked_domains.add(domain)
                        blocked_count += 1
                        print(f"Blocked domain: {domain}")
                    
                except Exception as e:
                    print(f"Error blocking domain {domain}: {e}")
        
        # Remove the session
        del self.active_sessions[client]
        
        print(f"Terminated session for {client}, blocked {blocked_count} domains")
        return blocked_count > 0
    
    def unblock_domains(self, domains):
        """Unblock previously blocked domains"""
        unblocked_count = 0
        
        for domain in domains:
            if domain in self.blocked_domains:
                try:
                    cmd = ["sudo", "pihole", "-b", "-d", domain]
                    result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
                    
                    if result.returncode == 0:
                        self.blocked_domains.remove(domain)
                        unblocked_count += 1
                        print(f"Unblocked domain: {domain}")
                    
                except Exception as e:
                    print(f"Error unblocking domain {domain}: {e}")
        
        return unblocked_count
    
    def get_session_status(self):
        """Get current session status for display"""
        active_sessions = self.get_active_sessions()
        
        if not active_sessions:
            return {
                'status': 'No active sessions',
                'count': 0,
                'sessions': []
            }
        
        # Group by type
        youtube_sessions = [s for s in active_sessions if 'YouTube' in s['type']]
        roblox_sessions = [s for s in active_sessions if 'Roblox' in s['type']]
        
        status_parts = []
        if youtube_sessions:
            status_parts.append(f"YouTube: {len(youtube_sessions)}")
        if roblox_sessions:
            status_parts.append(f"Roblox: {len(roblox_sessions)}")
        
        return {
            'status': ' | '.join(status_parts) if status_parts else 'Active sessions',
            'count': len(active_sessions),
            'sessions': active_sessions,
            'youtube_count': len(youtube_sessions),
            'roblox_count': len(roblox_sessions)
        }
    
    def monitor_loop(self):
        """Main monitoring loop"""
        print("🎮 Starting Pi-hole Session Monitor...")
        print("Monitoring for YouTube and Roblox sessions...")
        
        while self.running:
            try:
                # Detect active sessions
                self.detect_active_sessions()
                
                # Get current status
                status = self.get_session_status()
                
                if status['count'] > 0:
                    print(f"📱 Active sessions: {status['status']}")
                    for session in status['sessions']:
                        last_seen = datetime.fromtimestamp(session['last_seen'])
                        print(f"  - {session['client']}: {session['type']} (last seen: {last_seen.strftime('%H:%M:%S')})")
                
                # Sleep for 30 seconds before next check
                time.sleep(30)
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"Error in monitoring loop: {e}")
                time.sleep(10)
        
        print("🛑 Session monitor stopped")

def main():
    monitor = SessionMonitor()
    
    # Check if running as script with arguments
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "status":
            monitor.detect_active_sessions()
            status = monitor.get_session_status()
            print(f"Session Status: {status['status']}")
            print(f"Active sessions: {status['count']}")
            
        elif command == "terminate" and len(sys.argv) > 2:
            client = sys.argv[2]
            monitor.detect_active_sessions()
            if monitor.terminate_session(client):
                print(f"✅ Terminated session for {client}")
            else:
                print(f"❌ No active session found for {client}")
                
        elif command == "list":
            monitor.detect_active_sessions()
            sessions = monitor.get_active_sessions()
            if sessions:
                print("Active sessions:")
                for session in sessions:
                    print(f"  - {session['client']}: {session['type']}")
            else:
                print("No active sessions")
                
        else:
            print("Usage:")
            print("  python3 session_monitor.py status     - Show current session status")
            print("  python3 session_monitor.py list       - List active sessions")
            print("  python3 session_monitor.py terminate <client> - Terminate session for client")
            print("  python3 session_monitor.py monitor    - Start continuous monitoring")
    else:
        # Start continuous monitoring
        monitor.monitor_loop()

if __name__ == "__main__":
    main()
