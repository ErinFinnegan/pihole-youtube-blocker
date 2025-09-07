# Mock version of tft-youtube-status.py for testing without Pi hardware

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

# Global variables for button feedback (same as original)
button_pressed = None
button_press_time = 0
status_change_confirmed = False
status_change_time = 0

# Mock YouTube status - starts as blocked
mock_youtube_blocked = True

# ----------------------------
# Mock Functions
# ----------------------------

def mock_youtube_blocked() -> bool:
    """Mock function that simulates checking YouTube block status"""
    return mock_youtube_blocked

def mock_block_youtube():
    """Mock function that simulates blocking YouTube"""
    global mock_youtube_blocked, button_pressed, button_press_time
    button_pressed = "blocking"
    button_press_time = time.time()
    print("Mock: Blocking YouTube...")
    # Simulate some delay
    time.sleep(1)
    mock_youtube_blocked = True
    print("Mock: YouTube blocked!")

def mock_allow_youtube():
    """Mock function that simulates allowing YouTube"""
    global mock_youtube_blocked, button_pressed, button_press_time
    button_pressed = "allowing"
    button_press_time = time.time()
    print("Mock: Allowing YouTube...")
    # Simulate some delay
    time.sleep(1)
    mock_youtube_blocked = False
    print("Mock: YouTube allowed!")

# ----------------------------
# GUI Display Simulation
# ----------------------------

class MockDisplay:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Pi-hole LCD Screen Mock")
        self.root.geometry("300x500")
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
        
        self.block_btn = tk.Button(
            self.button_frame,
            text="BLOCK YouTube",
            command=self.on_block_pressed,
            bg="red",
            fg="white",
            font=("Arial", 12, "bold"),
            width=15
        )
        self.block_btn.pack(side="left", padx=10)
        
        self.allow_btn = tk.Button(
            self.button_frame,
            text="ALLOW YouTube", 
            command=self.on_allow_pressed,
            bg="green",
            fg="white",
            font=("Arial", 12, "bold"),
            width=15
        )
        self.allow_btn.pack(side="left", padx=10)
        
        # Status info
        self.info_label = tk.Label(
            self.root,
            text="Mock Pi-hole LCD Screen\nPress buttons to test feedback",
            font=("Arial", 10),
            fg="gray"
        )
        self.info_label.pack(pady=10)
        
        # Start the display update loop
        self.update_display()
        
    def on_block_pressed(self):
        """Handle block button press"""
        threading.Thread(target=mock_block_youtube, daemon=True).start()
        
    def on_allow_pressed(self):
        """Handle allow button press"""
        threading.Thread(target=mock_allow_youtube, daemon=True).start()
    
    def update_display(self):
        """Update the display - called every 500ms"""
        global button_pressed, button_press_time, status_change_confirmed, status_change_time, mock_youtube_blocked
        
        current_time = time.time()
        blocked = mock_youtube_blocked
        
        # Check if we should show button feedback (for 2 seconds after button press)
        show_button_feedback = (button_pressed is not None and 
                              current_time - button_press_time < 2.0)
        
        # Check if we should show status confirmation (for 3 seconds after status change)
        show_status_confirmation = (status_change_confirmed and 
                                  current_time - status_change_time < 3.0)
        
        # Determine background color and title
        if show_button_feedback:
            bg_color = "#0064C8"  # Blue
            if button_pressed == "blocking":
                title = "BLOCKING..."
            else:  # allowing
                title = "ALLOWING..."
            status_text = "..." + ("." * int((current_time - button_press_time) * 2))[:3]
        elif show_status_confirmation:
            bg_color = "#FFFF00"  # Yellow
            title = "STATUS CHANGED!"
            status_text = "✓ DONE"
        else:
            # Normal status display
            bg_color = "#C80000" if blocked else "#00B400"  # Red or Green
            title = "YouTube BLOCKED" if blocked else "YouTube ALLOWED"
            status_text = ""
        
        # Update the display
        self.title_label.config(text=title, bg=bg_color)
        self.status_label.config(text=status_text, bg=bg_color)
        self.clock_label.config(
            text=datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 
            bg=bg_color
        )
        self.display_frame.config(bg=bg_color)
        
        # Update clock
        self.clock_label.config(text=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        
        # Schedule next update
        self.root.after(500, self.update_display)
    
    def run(self):
        """Start the GUI"""
        self.root.mainloop()

# ----------------------------
# Main Logic (same as original)
# ----------------------------

def main():
    global button_pressed, button_press_time, status_change_confirmed, status_change_time, mock_youtube_blocked
    
    last_state = None
    
    def check_status_changes():
        """Background thread to check for status changes"""
        nonlocal last_state
        while True:
            current_time = time.time()
            blocked = mock_youtube_blocked
            
            # Handle status changes
            if blocked != last_state:
                if last_state is not None:  # Don't show confirmation on first run
                    status_change_confirmed = True
                    status_change_time = current_time
                last_state = blocked
                # Clear button feedback when status actually changes
                button_pressed = None
            
            # Clear button feedback after timeout
            if button_pressed is not None and current_time - button_press_time >= 2.0:
                button_pressed = None
            
            # Clear status confirmation after timeout
            if status_change_confirmed and current_time - status_change_time >= 3.0:
                status_change_confirmed = False
            
            time.sleep(0.1)  # Check more frequently
    
    # Start background status checking
    status_thread = threading.Thread(target=check_status_changes, daemon=True)
    status_thread.start()
    
    # Start the GUI
    display = MockDisplay()
    display.run()

if __name__ == "__main__":
    print("Starting Pi-hole LCD Screen Mock...")
    print("This simulates your Pi-hole screen without needing the actual hardware.")
    print("Press the buttons to test the feedback system!")
    main()
