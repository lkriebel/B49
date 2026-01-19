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

        # Style
        self.style = ttk.Style()
        # self.style.theme_use('alt')
        self.style.configure('TLabel', foreground='white', background='black')
        self.style.configure('Free.Timer.TLabel', foreground='#00FF00', font=('Arial', 120, 'bold'))
        self.style.configure('Busy.Timer.TLabel', foreground='#FF6600', font=('Arial', 120, 'bold'))
        self.style.configure('Error.Timer.TLabel', foreground='red', font=('Arial', 120, 'bold'))
        self.style.configure('EndTime.TLabel', font=('Arial', 40, 'bold'))
        self.style.map('TButton',
                       foreground=[('active', 'white')],
                       background=[('active', '#CC0000')],
        )
        self.style.configure('TButton', foreground='white', background='#FF3333', padding='30 15 30 15', relief='raised', font=('Arial', 20, 'bold'), borderwidth=5)
        self.style.configure('TFrame', background='black')

        # UI Elements
        self.status_frame = ttk.Frame(self.root)
        self.status_frame.pack(expand=True)

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
            text="SET FREE",
            command=self.manual_free,
        )
        self.free_button.pack(pady=30)
        
        # Initialize Firebase
        self.init_firebase()

        # Initialize Discord environment stuff
        # self.discord_token = os.getenv('DISCORD_BOT_TOKEN')
        # self.channel_id = os.getenv('DISCORD_STATUS_CHANNEL_ID')
        
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
        self.set_discord_channel_status('BUSY')
    
    def set_free(self):
        """Set display to FREE"""
        self.end_time = None
        self.is_free = True
        self.set_discord_channel_status('OPEN')
    
    def manual_free(self):
        """Manual button to set status to FREE"""
        self.set_free()
        self.set_discord_channel_status('OPEN')

    def set_discord_channel_status(self, status: str):
        """Set status for channel in .env to given string"""
        self.discord_token = os.getenv('DISCORD_BOT_TOKEN')
        self.channel_id = os.getenv('DISCORD_STATUS_CHANNEL_ID')
        headers = {
                "Authorization": f"Bot {self.discord_token}",
                # "User-Agent": "DiscordBot",
        }
        url = f'https://discord.com/api/v10/channels/{self.channel_id}'
        resp = requests.patch(url, headers=headers, json={"name": f'B49 Status: {status}'})
        print(resp)
        print(url)
    
    def update_display(self):
        """Update the display every second"""
        now = datetime.now()
        now_time = now.time()
        open_time = time(10,00)
        close_time = time(17,20)

        # Handle weekends where 5 and 6 are Saturday and Sunday
        if now.weekday() > 5:
            self.status_label.config(text="CLOSED UNTIL MONDAY", style='Busy.Timer.TLabel')
            self.end_time_label.config(text=str(open_time))
            if not self.closed_for_day:
                self.closed_for_day = True
                self.set_discord_channel_status('CLOSED')
        if close_time <= now_time or now_time <= open_time:
            # Not Saturday or Sunday
            if now.weekday() < 4:
                self.status_label.config(text="CLOSED UNTIL TOMORROW", style='Busy.Timer.TLabel')
            else:
                self.status_label.config(text="CLOSED UNTIL MONDAY", style='Busy.Timer.TLabel')
            self.end_time_label.config(text=str(open_time))
            if not self.closed_for_day:
                self.closed_for_day = True
                self.set_discord_channel_status('CLOSED')
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
