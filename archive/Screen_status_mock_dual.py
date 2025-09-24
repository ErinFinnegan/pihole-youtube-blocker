# Mock version of dual-button Pi-hole LCD screen for testing

import time, subprocess, sys, signal, threading
from datetime import datetime
import tkinter as tk
from tkinter import ttk
import queue

# ----------------------------
# Mock Hardware Simulation
# ----------------------------

# Simulate display dimensions
W, H = 135, 240

# Colors (same as original)
GREEN = (0,180,0)
RED   = (200,0,0)
WHITE = (255,255,255)
BLACK = (0,0,0)
BLUE  = (0,100,200)
YELLOW = (255,255,0)
ORANGE = (255,165,0)
PURPLE = (128,0,128)

# Global variables for button feedback
button_pressed = None
button_press_time = 0
status_change_confirmed = False
status_change_time = 0

# Mock status - starts as blocked
mock_youtube_blocked = True
mock_roblox_blocked = True
mock_scratch_accessible = True
mock_active_sessions = {'youtube': 0, 'roblox': 0, 'total': 0}
mock_sessions_killed = 0

# ----------------------------
# Mock Functions
# ----------------------------

def mock_youtube_blocked() -> bool:
    """Mock function that simulates checking YouTube block status"""
    return mock_youtube_blocked

def mock_roblox_blocked() -> bool:
    """Mock function that simulates checking Roblox block status"""
    return mock_roblox_blocked

def mock_scratch_accessible() -> bool:
    """Mock function that simulates checking Scratch accessibility"""
    return mock_scratch_accessible

def mock_toggle_youtube_roblox():
    """Mock function that simulates toggling YouTube/Roblox"""
    global mock_youtube_blocked, mock_roblox_blocked, button_pressed, button_press_time
    button_pressed = "toggling"
    button_press_time = time.time()
    print("Mock: Toggling YouTube and Roblox...")
    # Simulate some delay
    time.sleep(1)
    mock_youtube_blocked = not mock_youtube_blocked
    mock_roblox_blocked = not mock_roblox_blocked
    print(f"Mock: YouTube {'blocked' if mock_youtube_blocked else 'allowed'}, Roblox {'blocked' if mock_roblox_blocked else 'allowed'}!")

def mock_kill_sessions():
    """Mock function that simulates killing active sessions"""
    global button_pressed, button_press_time, mock_sessions_killed, mock_active_sessions
    button_pressed = "killing"
    button_press_time = time.time()
    print("Mock: Killing active sessions...")
    # Simulate some delay
    time.sleep(1)
    mock_sessions_killed = mock_active_sessions['total']
    mock_active_sessions = {'youtube': 0, 'roblox': 0, 'total': 0}
    print(f"Mock: Killed {mock_sessions_killed} sessions!")

def mock_add_session():
    """Mock function to add a test session"""
    global mock_active_sessions
    mock_active_sessions['youtube'] += 1
    mock_active_sessions['total'] += 1
    print(f"Mock: Added YouTube session. Total: {mock_active_sessions['total']}")

def mock_add_roblox_session():
    """Mock function to add a Roblox session"""
    global mock_active_sessions
    mock_active_sessions['roblox'] += 1
    mock_active_sessions['total'] += 1
    print(f"Mock: Added Roblox session. Total: {mock_active_sessions['total']}")

# ----------------------------
# GUI Display Simulation
# ----------------------------

class MockDisplay:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Pi-hole LCD Screen Mock - Dual Buttons")
        self.root.geometry("400x600")
        self.root.configure(bg='black')
        
        # Create main display area
        self.display_frame = tk.Frame(self.root, width=240, height=135, bg='black')
        self.display_frame.pack(pady=20)
        self.display_frame.pack_propagate(False)
        
        # Title label
        self.title_label = tk.Label(
            self.display_frame, 
            text="YouTube BLOCKED", 
            font=("Arial", 16, "bold"),
            fg="white",
            bg="red"
        )
        self.title_label.pack(expand=True)
        
        # Status message label
        self.status_label = tk.Label(
            self.display_frame,
            text="",
            font=("Arial", 12),
            fg="white",
            bg="red"
        )
        self.status_label.pack()
        
        # Roblox status label
        self.roblox_label = tk.Label(
            self.display_frame,
            text="Roblox: BLOCKED",
            font=("Arial", 10),
            fg="white",
            bg="red"
        )
        self.roblox_label.pack()
        
        # Scratch status label
        self.scratch_label = tk.Label(
            self.display_frame,
            text="Scratch: OK",
            font=("Arial", 10),
            fg="white",
            bg="red"
        )
        self.scratch_label.pack()
        
        # Active sessions label
        self.sessions_label = tk.Label(
            self.display_frame,
            text="",
            font=("Arial", 10),
            fg="white",
            bg="red"
        )
        self.sessions_label.pack()
        
        # Button instructions label
        self.button_instructions_label = tk.Label(
            self.display_frame,
            text="BTN1:Toggle BTN2:Kill",
            font=("Arial", 8),
            fg="white",
            bg="red"
        )
        self.button_instructions_label.pack()
        
        # Clock label
        self.clock_label = tk.Label(
            self.display_frame,
            text="",
            font=("Arial", 8),
            fg="white",
            bg="red"
        )
        self.clock_label.pack(side="bottom", pady=5)
        
        # Button controls
        self.button_frame = tk.Frame(self.root)
        self.button_frame.pack(pady=20)
        
        self.toggle_btn = tk.Button(
            self.button_frame,
            text="BTN1: Toggle YouTube & Roblox",
            command=self.on_toggle_pressed,
            bg="blue",
            fg="white",
            font=("Arial", 12, "bold"),
            width=25
        )
        self.toggle_btn.pack(side="left", padx=10)
        
        self.kill_btn = tk.Button(
            self.button_frame,
            text="BTN2: Kill Active Sessions", 
            command=self.on_kill_pressed,
            bg="purple",
            fg="white",
            font=("Arial", 12, "bold"),
            width=25
        )
        self.kill_btn.pack(side="left", padx=10)
        
        # Test session controls (hidden by default, can be enabled for testing)
        self.test_frame = tk.Frame(self.root)
        # self.test_frame.pack(pady=10)  # Commented out to hide test buttons
        
        self.add_yt_btn = tk.Button(
            self.test_frame,
            text="Add YouTube Session",
            command=self.add_youtube_session,
            bg="red",
            fg="white",
            font=("Arial", 10),
            width=15
        )
        # self.add_yt_btn.pack(side="left", padx=5)  # Commented out
        
        self.add_rb_btn = tk.Button(
            self.test_frame,
            text="Add Roblox Session",
            command=self.add_roblox_session,
            bg="orange",
            fg="white",
            font=("Arial", 10),
            width=15
        )
        # self.add_rb_btn.pack(side="left", padx=5)  # Commented out
        
        # Status info
        self.info_label = tk.Label(
            self.root,
            text="Mock Pi-hole LCD Screen - Dual Button Mode\nBTN1: Toggle blocking | BTN2: Kill sessions\n(Only 2 buttons - matches actual PiTFT hardware)",
            font=("Arial", 10),
            fg="gray"
        )
        self.info_label.pack(pady=10)
        
        # Start the display update loop
        self.update_display()
        
    def on_toggle_pressed(self):
        """Handle toggle button press"""
        threading.Thread(target=mock_toggle_youtube_roblox, daemon=True).start()
        
    def on_kill_pressed(self):
        """Handle kill sessions button press"""
        threading.Thread(target=mock_kill_sessions, daemon=True).start()
    
    def add_youtube_session(self):
        """Add a test YouTube session"""
        mock_add_session()
    
    def add_roblox_session(self):
        """Add a test Roblox session"""
        mock_add_roblox_session()
    
    def update_display(self):
        """Update the display - called every 500ms"""
        global button_pressed, button_press_time, status_change_confirmed, status_change_time, mock_youtube_blocked, mock_roblox_blocked, mock_scratch_accessible, mock_active_sessions, mock_sessions_killed
        
        current_time = time.time()
        youtube_blocked = mock_youtube_blocked
        roblox_blocked = mock_roblox_blocked
        scratch_accessible = mock_scratch_accessible
        
        # Check if we should show button feedback (for 2 seconds after button press)
        show_button_feedback = (button_pressed is not None and 
                              current_time - button_press_time < 2.0)
        
        # Check if we should show status confirmation (for 3 seconds after status change)
        show_status_confirmation = (status_change_confirmed and 
                                  current_time - status_change_time < 3.0)
        
        # Determine background color and title
        if show_button_feedback:
            if button_pressed == "toggling":
                bg_color = "#0064C8"  # Blue
                text_color = "white"
                title = "TOGGLING..."
            elif button_pressed == "killing":
                bg_color = "#800080"  # Purple
                text_color = "white"
                title = "KILLING SESSIONS..."
        elif show_status_confirmation:
            bg_color = "#FFFF00"  # Yellow
            text_color = "black"  # Black text on yellow background
            if mock_sessions_killed > 0:
                title = f"KILLED {mock_sessions_killed} SESSIONS!"
            else:
                title = "STATUS CHANGED!"
        else:
            # Normal status display - show primary service status
            bg_color = "#C80000" if youtube_blocked else "#00B400"  # Red or Green
            text_color = "white"
            title = "YouTube BLOCKED" if youtube_blocked else "YouTube ALLOWED"
        
        # Update the display
        self.title_label.config(text=title, bg=bg_color, fg=text_color)
        self.status_label.config(text="", bg=bg_color, fg=text_color)
        self.clock_label.config(
            text=datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 
            bg=bg_color,
            fg=text_color
        )
        self.display_frame.config(bg=bg_color)
        
        # Update status indicators (only in normal display mode)
        if not show_button_feedback and not show_status_confirmation:
            roblox_text = "Roblox: " + ("BLOCKED" if roblox_blocked else "ALLOWED")
            self.roblox_label.config(text=roblox_text, bg=bg_color, fg=text_color)
            
            scratch_text = "Scratch: " + ("OK" if scratch_accessible else "BLOCKED!")
            scratch_color = text_color if scratch_accessible else "yellow"
            self.scratch_label.config(text=scratch_text, bg=bg_color, fg=scratch_color)
            
            # Show active sessions
            if mock_active_sessions['total'] > 0:
                session_text = f"Active: YT:{mock_active_sessions['youtube']} RB:{mock_active_sessions['roblox']}"
                session_color = "orange" if mock_active_sessions['total'] > 0 else text_color
                self.sessions_label.config(text=session_text, bg=bg_color, fg=session_color)
            else:
                self.sessions_label.config(text="", bg=bg_color, fg=text_color)
            
            # Show button instructions
            self.button_instructions_label.config(text="BTN1:Toggle BTN2:Kill", bg=bg_color, fg=text_color)
        else:
            # Clear status lines during feedback/confirmation
            self.roblox_label.config(text="", bg=bg_color, fg=text_color)
            self.scratch_label.config(text="", bg=bg_color, fg=text_color)
            self.sessions_label.config(text="", bg=bg_color, fg=text_color)
            self.button_instructions_label.config(text="", bg=bg_color, fg=text_color)
        
        # Add dots for button feedback
        if show_button_feedback:
            dots = "..." + ("." * int((current_time - button_press_time) * 2))[:3]
            self.status_label.config(text=dots, bg=bg_color, fg=text_color)
        
        # Add confirmation message
        if show_status_confirmation:
            if mock_sessions_killed > 0:
                confirm_msg = f"✓ {mock_sessions_killed} SESSIONS TERMINATED"
            else:
                confirm_msg = "✓ DONE"
            self.status_label.config(text=confirm_msg, bg=bg_color, fg=text_color)
        
        # Schedule next update
        self.root.after(500, self.update_display)
    
    def run(self):
        """Start the GUI"""
        self.root.mainloop()

# ----------------------------
# Main Logic
# ----------------------------

def main():
    global button_pressed, button_press_time, status_change_confirmed, status_change_time, mock_youtube_blocked, mock_roblox_blocked, mock_scratch_accessible, mock_active_sessions, mock_sessions_killed
    
    last_state = None
    
    def check_status_changes():
        """Background thread to check for status changes"""
        nonlocal last_state
        global button_pressed, button_press_time, status_change_confirmed, status_change_time, mock_youtube_blocked, mock_roblox_blocked, mock_scratch_accessible, mock_active_sessions, mock_sessions_killed
        while True:
            current_time = time.time()
            youtube_blocked = mock_youtube_blocked
            
            # Handle status changes (check YouTube as primary status)
            if youtube_blocked != last_state:
                if last_state is not None:  # Don't show confirmation on first run
                    status_change_confirmed = True
                    status_change_time = current_time
                last_state = youtube_blocked
                # Clear button feedback when status actually changes
                button_pressed = None
            
            # Clear button feedback after timeout
            if button_pressed is not None and current_time - button_press_time >= 2.0:
                button_pressed = None
            
            # Clear status confirmation after timeout
            if status_change_confirmed and current_time - status_change_time >= 3.0:
                status_change_confirmed = False
                mock_sessions_killed = 0  # Reset session kill count
            
            time.sleep(0.1)  # Check more frequently
    
    # Start background status checking
    status_thread = threading.Thread(target=check_status_changes, daemon=True)
    status_thread.start()
    
    # Start the GUI
    display = MockDisplay()
    display.run()

if __name__ == "__main__":
    print("Starting Pi-hole LCD Screen Mock - Dual Button Mode...")
    print("This simulates your Pi-hole screen with dual button functionality.")
    print("BTN1: Toggle YouTube/Roblox blocking")
    print("BTN2: Kill active sessions")
    print("Use the test buttons to add sessions, then test the kill functionality!")
    main()
