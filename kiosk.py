#!/usr/bin/env python3
"""
Kiosk Timer Application for Raspberry Pi
Monitors Firebase for sign-in/sign-out events and displays countdown timer
Semi Vibe-coded with Claude & Gemini (sorry)
"""

import tkinter as tk
from tkinter import ttk
from datetime import datetime, timedelta, time
import firebase_admin
from firebase_admin import credentials, db
import threading
import dotenv
import os
import requests

dotenv.load_dotenv()

class KioskTimerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Kiosk Timer")

        # Fullscreen setup
        self.root.attributes('-fullscreen', True)
        self.root.configure(bg='black')
        self.root.bind('<Escape>', lambda e: self.root.destroy())  # Exit with ESC key

        # Timer state
        self.end_time = None
        self.is_free = True
        self.closed_for_day = False
        self.manually_closed = False

        # Style
        self.style = ttk.Style()
        # self.style.theme_use('alt')
        self.style.configure('TLabel', foreground='white', background='black')
        self.style.configure('Free.Timer.TLabel', foreground='#00FF00', font=('Arial', 180, 'bold'), justify=tk.CENTER)
        self.style.configure('Header.TLabel', foreground='#FFFFFF', font=('Arial', 80, 'bold'), justify=tk.CENTER)
        self.style.configure('Busy.Timer.TLabel', foreground='#FF6600', font=('Arial', 180, 'bold'), justify=tk.CENTER)
        self.style.configure('Error.Timer.TLabel', foreground='red', font=('Arial', 180, 'bold'), justify=tk.CENTER)
        self.style.configure('Closed.Timer.TLabel', foreground='red', font=('Arial', 180, 'bold'), justify=tk.CENTER)
        self.style.configure('EndTime.TLabel', font=('Arial', 100, 'bold'), justify=tk.CENTER)
        self.style.map('Free.TButton',
                       foreground=[('active', 'white')],
                       background=[('active', '#00CC00')],
        )
        self.style.map('Busy.TButton',
                       foreground=[('active', 'white')],
                       background=[('active', '#CC0000')],
        )
        self.style.map('Close.TButton',
                       foreground=[('active', 'white')],
                       background=[('active', '#CC0000')],
        )
        self.style.map('Open.TButton',
                       foreground=[('active', 'white')],
                       background=[('active', '#00CC00')],
        )
        self.style.configure('Free.TButton', foreground='white', background='#66FF33', padding='10 10 10 10', relief='raised', font=('Arial', 30, 'bold'), borderwidth=5)
        self.style.configure('Busy.TButton', foreground='white', background='#FFCC33', padding='10 10 10 10', relief='raised', font=('Arial', 30, 'bold'), borderwidth=5)
        self.style.configure('Close.TButton', foreground='white', background='#FF3333', padding='10 10 10 10', relief='raised', font=('Arial', 30, 'bold'), borderwidth=5)
        self.style.configure('Open.TButton', foreground='white', background='#66FF33', padding='10 10 10 10', relief='raised', font=('Arial', 30, 'bold'), borderwidth=5)
        self.style.configure('TFrame', background='black')

        # UI Elements
        self.status_frame = ttk.Frame(self.root)
        self.status_frame.pack(expand=True)

        self.header_label = ttk.Label(
                self.status_frame,
                text="B49 is",
                style="Header.TLabel",
        )
        self.header_label.pack()
        self.status_label = ttk.Label(
            self.status_frame, 
            text="FREE", 
            style='Free.Timer.TLabel',
        )
        self.status_label.pack()
        
        self.end_time_label = ttk.Label(
            self.status_frame, 
            text="",
            style='EndTime.TLabel',
        )
        self.end_time_label.pack(pady=20)
        
        # Manual Free button
        self.free_button = ttk.Button(
            root,
            text="FREE",
            command=self.manual_free,
            style='Busy.TButton',
        )
        self.free_button.pack(padx=10, pady=50, side=tk.LEFT, expand=True)
        # self.free_button.grid(column=0, row=0)
        
        self.busy_button = ttk.Button(
            root,
            text="BUSY",
            command=self.manual_busy,
            style='Busy.TButton',
        )
        self.busy_button.pack(padx=10, pady=50, side=tk.LEFT, expand=True)
        # self.busy_button.grid(column=0, row=1)

        self.closed_toggle_button = ttk.Button(
            root,
            text="CLOSE",
            command=self.toggle_closed,
            style='Close.TButton',
        )
        self.closed_toggle_button.place(relx=1, rely=1, anchor=tk.SE)


        # Initialize Firebase
        # self.init_firebase()

        # Start update loop
        self.update_display()
    
    def init_firebase(self):
        """Initialize Firebase connection"""
        try:
            # Initialize Firebase with service account
            cred = credentials.Certificate('firebase-credentials.json')
            url = os.getenv('FIREBASE_URL')
            firebase_admin.initialize_app(cred, {
                'databaseURL': url
            })
            
            # Reference to the kiosk status
            self.status_ref = db.reference('kiosk/status')
            
            # Listen for changes
            self.status_ref.listen(self.on_status_change)
            
            print("Firebase initialized successfully")
        except Exception as e:
            print(f"Error initializing Firebase: {e}")
            self.status_label.config(text="ERROR", style='Error.Timer.TLabel')
    
    def on_status_change(self, event):
        """Callback when Firebase data changes"""
        data = event.data
        
        if data is None:
            return
        
        event_type = data.get('event')
        timestamp = data.get('timestamp')
        
        if event_type == 'sign_in':
            # Start 1-hour timer
            self.start_timer(timestamp)
        elif event_type == 'sign_out':
            # Set to FREE
            self.set_free()
    
    def start_timer(self, timestamp):
        """Start 1-hour countdown timer"""
        self.end_time = datetime.fromtimestamp(timestamp) + timedelta(hours=1)
        self.is_free = False
        self.set_discord_channel_status('🟧 BUSY')
    
    def set_free(self):
        """Set display to FREE"""
        self.end_time = None
        self.is_free = True
        self.set_discord_channel_status('🟩 OPEN')
    
    def manual_free(self):
        """Manual button to set status to FREE"""
        self.set_free()

    def manual_busy(self):
        self.start_timer(datetime.now().timestamp())

    def toggle_closed(self):
        if self.manually_closed:
            self.closed_toggle_button.config(text='CLOSE', style='Close.TButton')
        else:
            self.closed_toggle_button.config(text='OPEN', style='Open.TButton')
        self.manually_closed = not self.manually_closed


    def set_discord_channel_status(self, status: str):
        """Set status for channel in .env to given string"""
        token = os.getenv('DISCORD_BOT_TOKEN')
        channel_id = os.getenv('DISCORD_STATUS_CHANNEL_ID')
        headers = {
                "Authorization": f"Bot {token}",
        }
        url = f'https://discord.com/api/v10/channels/{channel_id}'
        channel_resp = requests.get(url, headers=headers)
        if channel_resp.status_code != 200:
            print("GET on channel failed")
            print(channel_resp.json())
            return
        try:
            channel_resp_json = channel_resp.json()
            # manual override for channel name
            if 'FOR' in channel_resp_json['name'].upper():
                return
        except requests.exceptions.JSONDecodeError:
            print("Channel lookup did not return valid JSON")
            return
        patch_resp = requests.patch(url, headers=headers, json={"name": f'B49 Status: {status}'})
        if patch_resp.status_code != 200:
            print("Updating channel failed")
            print(patch_resp.json())

    def update_display(self):
        """Update the display every second"""
        now = datetime.now()
        now_time = now.time()
        open_time = time(10,00)
        close_time = time(17,20)


        if self.manually_closed:
            self.status_label.config(text="CLOSED", style='Closed.Timer.TLabel')
            if not self.closed_for_day:
                self.closed_for_day = True
                self.set_discord_channel_status('🔴 CLOSED')
        # Handle weekends where 5 and 6 are Saturday and Sunday
        elif now.weekday() > 5:
            self.status_label.config(text="CLOSED UNTIL MONDAY", style='Closed.Timer.TLabel')
            self.end_time_label.config(text=str(open_time))
            if not self.closed_for_day:
                self.closed_for_day = True
                self.set_discord_channel_status('🔴 CLOSED')
        elif close_time <= now_time or now_time <= open_time:
            # Not Saturday or Sunday
            if now.weekday() < 4:
                self.status_label.config(text="CLOSED UNTIL TOMORROW", style='Closed.Timer.TLabel')
            else:
                self.status_label.config(text="CLOSED UNTIL MONDAY", style='Closed.Timer.TLabel')
            self.end_time_label.config(text=str(open_time))
            if not self.closed_for_day:
                self.closed_for_day = True
                self.set_discord_channel_status('🔴 CLOSED')
        elif self.is_free or self.end_time is None:
            self.status_label.config(text="FREE", style='Free.Timer.TLabel')
            self.end_time_label.config(text="")
            if self.closed_for_day:
                self.closed_for_day = False
        else:
            # Calculate remaining time
            now = datetime.now()
            
            if now >= self.end_time:
                # Timer expired
                self.set_free()
            else:
                # Display countdown
                remaining = self.end_time - now
                hours, remainder = divmod(int(remaining.total_seconds()), 3600)
                minutes, seconds = divmod(remainder, 60)
                
                time_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
                self.status_label.config(
                    text=time_str, 
                    style='Busy.Timer.TLabel'
                )
                
                self.end_time_label.config(
                    text=f"Available at {self.end_time.strftime('%I:%M %p')}"
                )
            if self.closed_for_day:
                self.closed_for_day = False
        
        # Schedule next update
        self.root.after(1000, self.update_display)

def main():
    root = tk.Tk()
    app = KioskTimerApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
