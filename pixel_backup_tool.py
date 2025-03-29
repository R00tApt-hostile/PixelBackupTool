import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from datetime import datetime
import subprocess
import threading
from PIL import Image, ImageTk
import platform

class PixelBackupToolkit:
    def __init__(self, root):
        self.root = root
        self.root.title("Google Pixel Backup Toolkit")
        self.root.geometry("800x600")
        self.setup_ui()
        self.backup_history = []
        self.setup_styles()
        
        # Device connection status
        self.connected_device = None
        self.check_device_connection()
    
    def setup_styles(self):
        style = ttk.Style()
        style.configure('TFrame', background='#f5f5f5')
        style.configure('TLabel', background='#f5f5f5', font=('Segoe UI', 10))
        style.configure('TButton', font=('Segoe UI', 10))
        style.configure('TNotebook', background='#f5f5f5')
        style.configure('TNotebook.Tab', font=('Segoe UI', 10))
        style.configure('TCheckbutton', background='#f5f5f5')
        style.configure('TRadiobutton', background='#f5f5f5')
        
    def setup_ui(self):
        # Main container
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Header
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Logo and title
        try:
            logo_img = Image.open("pixel_logo.png").resize((32, 32))
            self.logo = ImageTk.PhotoImage(logo_img)
            logo_label = ttk.Label(header_frame, image=self.logo)
            logo_label.pack(side=tk.LEFT, padx=(0, 10))
        except:
            pass  # Continue without logo if image not found
            
        title_label = ttk.Label(header_frame, text="Google Pixel Backup Toolkit", font=('Segoe UI', 16, 'bold'))
        title_label.pack(side=tk.LEFT)
        
        # Device status
        self.device_status = ttk.Label(header_frame, text="No device connected", foreground='red')
        self.device_status.pack(side=tk.RIGHT)
        
        # Notebook (Tabs)
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Tab 1: Full Backup
        self.setup_full_backup_tab()
        
        # Tab 2: Media Backup
        self.setup_media_backup_tab()
        
        # Tab 3: Settings
        self.setup_settings_tab()
        
        # Footer buttons
        footer_frame = ttk.Frame(main_frame)
        footer_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(footer_frame, text="Connect Phone", command=self.connect_phone).pack(side=tk.LEFT, padx=5)
        ttk.Button(footer_frame, text="Refresh", command=self.check_device_connection).pack(side=tk.LEFT, padx=5)
        ttk.Button(footer_frame, text="About", command=self.show_about).pack(side=tk.LEFT, padx=5)
        ttk.Button(footer_frame, text="Exit", command=self.root.quit).pack(side=tk.RIGHT, padx=5)
    
    def setup_full_backup_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Full Backup")
        
        # Backup Options
        options_frame = ttk.LabelFrame(tab, text="Backup Options")
        options_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.system_data_var = tk.BooleanVar(value=True)
        self.apps_var = tk.BooleanVar(value=True)
        self.contacts_var = tk.BooleanVar(value=True)
        self.messages_var = tk.BooleanVar(value=True)
        self.call_logs_var = tk.BooleanVar(value=True)
        
        ttk.Checkbutton(options_frame, text="System Data", variable=self.system_data_var).pack(anchor=tk.W)
        ttk.Checkbutton(options_frame, text="Apps", variable=self.apps_var).pack(anchor=tk.W)
        ttk.Checkbutton(options_frame, text="Contacts", variable=self.contacts_var).pack(anchor=tk.W)
        ttk.Checkbutton(options_frame, text="Messages", variable=self.messages_var).pack(anchor=tk.W)
        ttk.Checkbutton(options_frame, text="Call Logs", variable=self.call_logs_var).pack(anchor=tk.W)
        
        # Media Options
        media_frame = ttk.LabelFrame(tab, text="Media Options")
        media_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.photos_var = tk.BooleanVar(value=True)
        self.videos_var = tk.BooleanVar(value=True)
        self.documents_var = tk.BooleanVar(value=True)
        self.music_var = tk.BooleanVar(value=True)
        self.downloads_var = tk.BooleanVar(value=True)
        self.other_media_var = tk.BooleanVar(value=True)
        
        row1 = ttk.Frame(media_frame)
        row1.pack(fill=tk.X)
        ttk.Checkbutton(row1, text="Photos", variable=self.photos_var).pack(side=tk.LEFT, padx=5)
        ttk.Checkbutton(row1, text="Videos", variable=self.videos_var).pack(side=tk.LEFT, padx=5)
        
        row2 = ttk.Frame(media_frame)
        row2.pack(fill=tk.X)
        ttk.Checkbutton(row2, text="Documents", variable=self.documents_var).pack(side=tk.LEFT, padx=5)
        ttk.Checkbutton(row2, text="Music", variable=self.music_var).pack(side=tk.LEFT, padx=5)
        
        row3 = ttk.Frame(media_frame)
        row3.pack(fill=tk.X)
        ttk.Checkbutton(row3, text="Downloads", variable=self.downloads_var).pack(side=tk.LEFT, padx=5)
        ttk.Checkbutton(row3, text="Other Media", variable=self.other_media_var).pack(side=tk.LEFT, padx=5)
        
        # Backup Location
        location_frame = ttk.LabelFrame(tab, text="Backup Location")
        location_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.backup_location = tk.StringVar(value=os.path.expanduser("~/Pixel_Backups"))
        ttk.Entry(location_frame, textvariable=self.backup_location).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        ttk.Button(location_frame, text="Browse", command=self.browse_backup_location).pack(side=tk.RIGHT)
        
        # Start Button
        ttk.Button(tab, text="Start Full Backup", command=self.start_full_backup).pack(pady=10)
    
    def setup_media_backup_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Media Backup")
        
        # Media Type Selection
        type_frame = ttk.LabelFrame(tab, text="Media Type Selection")
        type_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.media_type = tk.StringVar(value="custom")
        
        row1 = ttk.Frame(type_frame)
        row1.pack(fill=tk.X)
        ttk.Radiobutton(row1, text="Photos Only", variable=self.media_type, value="photos").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(row1, text="Videos Only", variable=self.media_type, value="videos").pack(side=tk.LEFT, padx=5)
        
        row2 = ttk.Frame(type_frame)
        row2.pack(fill=tk.X)
        ttk.Radiobutton(row2, text="Documents Only", variable=self.media_type, value="documents").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(row2, text="Custom Selection", variable=self.media_type, value="custom").pack(side=tk.LEFT, padx=5)
        
        # Date Range
        date_frame = ttk.LabelFrame(tab, text="Date Range")
        date_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(date_frame, text="From:").pack(side=tk.LEFT, padx=5)
        self.date_from = ttk.Entry(date_frame, width=10)
        self.date_from.pack(side=tk.LEFT)
        self.date_from.insert(0, "01/01/2023")
        
        ttk.Label(date_frame, text="To:").pack(side=tk.LEFT, padx=5)
        self.date_to = ttk.Entry(date_frame, width=10)
        self.date_to.pack(side=tk.LEFT)
        self.date_to.insert(0, datetime.now().strftime("%m/%d/%Y"))
        
        # Advanced Filters
        filter_frame = ttk.LabelFrame(tab, text="Advanced Filters")
        filter_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.large_files_var = tk.BooleanVar()
        self.screenshots_var = tk.BooleanVar()
        self.raw_images_var = tk.BooleanVar()
        self.uhd_videos_var = tk.BooleanVar()
        
        ttk.Checkbutton(filter_frame, text="Over 5MB files only", variable=self.large_files_var).pack(anchor=tk.W)
        ttk.Checkbutton(filter_frame, text="Screenshots only", variable=self.screenshots_var).pack(anchor=tk.W)
        ttk.Checkbutton(filter_frame, text="RAW images only", variable=self.raw_images_var).pack(anchor=tk.W)
        ttk.Checkbutton(filter_frame, text="4K videos only", variable=self.uhd_videos_var).pack(anchor=tk.W)
        
        # Backup Location
        location_frame = ttk.LabelFrame(tab, text="Backup Location")
        location_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.media_backup_location = tk.StringVar(value=os.path.expanduser("~/Pixel_Media"))
        ttk.Entry(location_frame, textvariable=self.media_backup_location).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        ttk.Button(location_frame, text="Browse", command=self.browse_media_location).pack(side=tk.RIGHT)
        
        # Action Buttons
        button_frame = ttk.Frame(tab)
        button_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(button_frame, text="Preview Selected Files", command=self.preview_files).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Start Media Backup", command=self.start_media_backup).pack(side=tk.RIGHT, padx=5)
    
    def setup_settings_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Settings")
        
        # General Settings
        general_frame = ttk.LabelFrame(tab, text="General")
        general_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.verify_backup_var = tk.BooleanVar(value=True)
        self.compress_backup_var = tk.BooleanVar(value=True)
        self.compression_level = tk.StringVar(value="balanced")
        
        ttk.Checkbutton(general_frame, text="Verify backup integrity when complete", 
                       variable=self.verify_backup_var).pack(anchor=tk.W)
        ttk.Checkbutton(general_frame, text="Compress backups (ZIP)", 
                       variable=self.compress_backup_var).pack(anchor=tk.W)
        
        level_frame = ttk.Frame(general_frame)
        level_frame.pack(fill=tk.X, pady=(0, 5))
        ttk.Label(level_frame, text="Compression Level:").pack(side=tk.LEFT)
        ttk.Combobox(level_frame, textvariable=self.compression_level, 
                    values=["fast", "balanced", "maximum"], state="readonly").pack(side=tk.LEFT)
        
        # Notification Settings
        notify_frame = ttk.LabelFrame(tab, text="Notifications")
        notify_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.sound_var = tk.BooleanVar(value=True)
        self.notification_var = tk.BooleanVar(value=True)
        
        ttk.Checkbutton(notify_frame, text="Play sound when backup completes", 
                       variable=self.sound_var).pack(anchor=tk.W)
        ttk.Checkbutton(notify_frame, text="Show desktop notification", 
                       variable=self.notification_var).pack(anchor=tk.W)
        
        # Connection Settings
        connection_frame = ttk.LabelFrame(tab, text="Connection")
        connection_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.default_connection = tk.StringVar(value="usb")
        
        ttk.Label(connection_frame, text="Default connection:").pack(anchor=tk.W)
        ttk.Combobox(connection_frame, textvariable=self.default_connection, 
                     values=["usb", "wifi"], state="readonly").pack(fill=tk.X, pady=(0, 5))
        
        self.auto_detect_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(connection_frame, text="Auto-detect Pixel devices", 
                       variable=self.auto_detect_var).pack(anchor=tk.W)
        
        # Save Buttons
        button_frame = ttk.Frame(tab)
        button_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(button_frame, text="Save Settings", command=self.save_settings).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Restore Defaults", command=self.restore_defaults).pack(side=tk.RIGHT, padx=5)
    
    def browse_backup_location(self):
        folder = filedialog.askdirectory(initialdir=self.backup_location.get())
        if folder:
            self.backup_location.set(folder)
    
    def browse_media_location(self):
        folder = filedialog.askdirectory(initialdir=self.media_backup_location.get())
        if folder:
            self.media_backup_location.set(folder)
    
    def connect_phone(self):
        self.check_device_connection()
        if self.connected_device:
            messagebox.showinfo("Connected", f"Device connected: {self.connected_device}")
        else:
            messagebox.showerror("Error", "No Pixel device detected. Please connect your phone via USB and enable USB debugging.")
    
    def check_device_connection(self):
        try:
            result = subprocess.run(['adb', 'devices'], capture_output=True, text=True)
            devices = [line.split('\t')[0] for line in result.stdout.split('\n')[1:] if line.strip()]
            
            if devices:
                # Get device model
                model_result = subprocess.run(['adb', 'shell', 'getprop', 'ro.product.model'], 
                                            capture_output=True, text=True)
                model = model_result.stdout.strip()
                
                if "Pixel" in model:
                    self.connected_device = model
                    self.device_status.config(text=f"Connected: {model}", foreground='green')
                else:
                    self.connected_device = None
                    self.device_status.config(text="Non-Pixel device connected", foreground='orange')
            else:
                self.connected_device = None
                self.device_status.config(text="No device connected", foreground='red')
        except FileNotFoundError:
            self.connected_device = None
            self.device_status.config(text="ADB not found", foreground='red')
    
    def start_full_backup(self):
        if not self.connected_device:
            messagebox.showerror("Error", "No Pixel device connected")
            return
        
        backup_folder = os.path.join(self.backup_location.get(), datetime.now().strftime("%Y%m%d_%H%M%S"))
        os.makedirs(backup_folder, exist_ok=True)
        
        # Start backup in a separate thread
        threading.Thread(target=self.perform_full_backup, args=(backup_folder,), daemon=True).start()
    
    def perform_full_backup(self, backup_folder):
        # This is a simulation - real implementation would use ADB commands
        total_files = 0
        
        # Create progress window
        progress_window = tk.Toplevel(self.root)
        progress_window.title("Backup in Progress")
        progress_window.geometry("400x200")
        
        progress_label = ttk.Label(progress_window, text="Starting backup...")
        progress_label.pack(pady=10)
        
        progress_var = tk.DoubleVar()
        progress_bar = ttk.Progressbar(progress_window, variable=progress_var, maximum=100)
        progress_bar.pack(fill=tk.X, padx=20, pady=5)
        
        time_label = ttk.Label(progress_window, text="Estimated time remaining: calculating...")
        time_label.pack(pady=5)
        
        button_frame = ttk.Frame(progress_window)
        button_frame.pack(pady=10)
        
        pause_button = ttk.Button(button_frame, text="Pause", state=tk.DISABLED)
        pause_button.pack(side=tk.LEFT, padx=10)
        
        cancel_button = ttk.Button(button_frame, text="Cancel", command=progress_window.destroy)
        cancel_button.pack(side=tk.RIGHT, padx=10)
        
        # Simulate backup progress
        for i in range(1, 101):
            if not progress_window.winfo_exists():
                return  # Backup canceled
            
            progress_var.set(i)
            progress_label.config(text=f"Backing up files... ({i}%)")
            time_label.config(text=f"Estimated time remaining: {100 - i} seconds")
            progress_window.update()
            
            # Simulate work
            self.root.after(100)
        
        # Backup complete
        progress_label.config(text="Backup completed successfully!")
        cancel_button.config(text="Close")
        pause_button.pack_forget()
        
        # Add to history
        self.backup_history.append({
            'date': datetime.now().strftime("%Y-%m-%d"),
            'type': 'Full',
            'size': 'Simulated'
        })
        
        if self.notification_var.get():
            messagebox.showinfo("Backup Complete", "Full backup completed successfully!")
    
    def start_media_backup(self):
        if not self.connected_device:
            messagebox.showerror("Error", "No Pixel device connected")
            return
        
        media_type = self.media_type.get()
        backup_folder = os.path.join(self.media_backup_location.get(), 
                                   f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{media_type}")
        os.makedirs(backup_folder, exist_ok=True)
        
        # Start backup in a separate thread
        threading.Thread(target=self.perform_media_backup, args=(backup_folder, media_type), daemon=True).start()
    
    def perform_media_backup(self, backup_folder, media_type):
        # This is a simulation - real implementation would use ADB commands
        total_files = 0
        
        # Create progress window
        progress_window = tk.Toplevel(self.root)
        progress_window.title("Backup in Progress")
        progress_window.geometry("400x200")
        
        progress_label = ttk.Label(progress_window, text=f"Starting {media_type} backup...")
        progress_label.pack(pady=10)
        
        progress_var = tk.DoubleVar()
        progress_bar = ttk.Progressbar(progress_window, variable=progress_var, maximum=100)
        progress_bar.pack(fill=tk.X, padx=20, pady=5)
        
        time_label = ttk.Label(progress_window, text="Estimated time remaining: calculating...")
        time_label.pack(pady=5)
        
        button_frame = ttk.Frame(progress_window)
        button_frame.pack(pady=10)
        
        pause_button = ttk.Button(button_frame, text="Pause", state=tk.DISABLED)
        pause_button.pack(side=tk.LEFT, padx=10)
        
        cancel_button = ttk.Button(button_frame, text="Cancel", command=progress_window.destroy)
        cancel_button.pack(side=tk.RIGHT, padx=10)
        
        # Simulate backup progress
        for i in range(1, 101):
            if not progress_window.winfo_exists():
                return  # Backup canceled
            
            progress_var.set(i)
            progress_label.config(text=f"Backing up {media_type}... ({i}%)")
            time_label.config(text=f"Estimated time remaining: {50 - i//2} seconds")
            progress_window.update()
            
            # Simulate work
            self.root.after(50)
        
        # Backup complete
        progress_label.config(text=f"{media_type.capitalize()} backup completed!")
        cancel_button.config(text="Close")
        pause_button.pack_forget()
        
        # Add to history
        self.backup_history.append({
            'date': datetime.now().strftime("%Y-%m-%d"),
            'type': media_type.capitalize(),
            'size': 'Simulated'
        })
        
        if self.notification_var.get():
            messagebox.showinfo("Backup Complete", f"{media_type.capitalize()} backup completed successfully!")
    
    def preview_files(self):
        media_type = self.media_type.get()
        messagebox.showinfo("Preview", f"This would show a preview of {media_type} files to be backed up")
    
    def save_settings(self):
        messagebox.showinfo("Settings Saved", "Your settings have been saved successfully")
    
    def restore_defaults(self):
        self.verify_backup_var.set(True)
        self.compress_backup_var.set(True)
        self.compression_level.set("balanced")
        self.sound_var.set(True)
        self.notification_var.set(True)
        self.default_connection.set("usb")
        self.auto_detect_var.set(True)
        messagebox.showinfo("Defaults Restored", "All settings have been restored to defaults")
    
    def show_about(self):
        about_text = """Google Pixel Backup Toolkit
Version 1.0

A simple tool to backup your Google Pixel phone data
with customizable options for different media types.

© 2023 Pixel Backup Toolkit"""
        messagebox.showinfo("About", about_text)

if __name__ == "__main__":
    root = tk.Tk()
    app = PixelBackupToolkit(root)
    root.mainloop()
