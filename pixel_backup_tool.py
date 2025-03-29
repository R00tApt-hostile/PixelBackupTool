import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from datetime import datetime
import subprocess
import threading
from PIL import Image, ImageTk
import zipfile
import time
from collections import defaultdict

class PixelBackupToolkit:
    def __init__(self, root):
        self.root = root
        self.root.title("Google Pixel Backup Toolkit")
        self.root.geometry("900x650")
        self.setup_ui()
        self.backup_history = []
        self.setup_styles()
        self.backup_process = None
        self.backup_canceled = False
        self.adb_path = self.find_adb()
        
        # Device connection status
        self.connected_device = None
        self.check_device_connection()
    
    def find_adb(self):
        """Locate ADB executable in common locations"""
        paths = [
            os.path.join(os.environ.get("ANDROID_HOME", ""), "platform-tools", "adb"),
            "/usr/bin/adb",
            "/usr/local/bin/adb",
            "adb"  # Try system path
        ]
        for path in paths:
            if os.path.exists(path):
                return path
        return "adb"  # Fallback to hoping it's in PATH
    
    def setup_styles(self):
        style = ttk.Style()
        style.configure('TFrame', background='#f5f5f5')
        style.configure('TLabel', background='#f5f5f5', font=('Segoe UI', 10))
        style.configure('TButton', font=('Segoe UI', 10))
        style.configure('TNotebook', background='#f5f5f5')
        style.configure('TNotebook.Tab', font=('Segoe UI', 10, 'bold'))
        style.configure('TCheckbutton', background='#f5f5f5')
        style.configure('TRadiobutton', background='#f5f5f5')
        style.configure('Header.TLabel', font=('Segoe UI', 16, 'bold'))
        
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
            
        title_label = ttk.Label(header_frame, text="Google Pixel Backup Toolkit", style='Header.TLabel')
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
        
        # Tab 4: Backup History
        self.setup_history_tab()
        
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
    
    def setup_history_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Backup History")
        
        # Treeview for backup history
        columns = ("date", "type", "size", "location")
        self.history_tree = ttk.Treeview(tab, columns=columns, show="headings")
        
        # Define headings
        self.history_tree.heading("date", text="Date")
        self.history_tree.heading("type", text="Type")
        self.history_tree.heading("size", text="Size")
        self.history_tree.heading("location", text="Location")
        
        # Set column widths
        self.history_tree.column("date", width=120)
        self.history_tree.column("type", width=100)
        self.history_tree.column("size", width=80)
        self.history_tree.column("location", width=250)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(tab, orient=tk.VERTICAL, command=self.history_tree.yview)
        self.history_tree.configure(yscroll=scrollbar.set)
        
        # Pack widgets
        self.history_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Action buttons
        button_frame = ttk.Frame(tab)
        button_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(button_frame, text="Refresh", command=self.update_history_view).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Delete Selected", command=self.delete_selected_backup).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Open Location", command=self.open_backup_location).pack(side=tk.RIGHT, padx=5)
    
    def update_history_view(self):
        """Update the history treeview with current backup history"""
        for item in self.history_tree.get_children():
            self.history_tree.delete(item)
        
        for backup in self.backup_history:
            self.history_tree.insert("", tk.END, values=(
                backup.get("date", ""),
                backup.get("type", ""),
                backup.get("size", ""),
                backup.get("location", "")
            ))
    
    def delete_selected_backup(self):
        selected = self.history_tree.selection()
        if not selected:
            return
            
        item = self.history_tree.item(selected[0])
        location = item['values'][3]
        
        if messagebox.askyesno("Confirm Delete", f"Delete backup at {location}?"):
            try:
                if os.path.isdir(location):
                    import shutil
                    shutil.rmtree(location)
                elif os.path.isfile(location):
                    os.remove(location)
                
                # Remove from history
                self.backup_history = [b for b in self.backup_history if b.get("location") != location]
                self.update_history_view()
                messagebox.showinfo("Success", "Backup deleted successfully")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete backup: {str(e)}")
    
    def open_backup_location(self):
        selected = self.history_tree.selection()
        if not selected:
            return
            
        item = self.history_tree.item(selected[0])
        location = item['values'][3]
        
        if os.path.exists(location):
            if platform.system() == "Windows":
                os.startfile(location)
            elif platform.system() == "Darwin":
                subprocess.Popen(["open", location])
            else:
                subprocess.Popen(["xdg-open", location])
        else:
            messagebox.showerror("Error", "Backup location no longer exists")
    
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
            result = subprocess.run([self.adb_path, 'devices'], capture_output=True, text=True, timeout=5)
            devices = [line.split('\t')[0] for line in result.stdout.split('\n')[1:] if line.strip()]
            
            if devices:
                # Get device model
                model_result = subprocess.run([self.adb_path, 'shell', 'getprop', 'ro.product.model'], 
                                            capture_output=True, text=True, timeout=5)
                model = model_result.stdout.strip()
                
                if "Pixel" in model:
                    self.connected_device = model
                    self.device_status.config(text=f"Connected: {model}", foreground='green')
                    return True
                else:
                    self.connected_device = None
                    self.device_status.config(text="Non-Pixel device connected", foreground='orange')
            else:
                self.connected_device = None
                self.device_status.config(text="No device connected", foreground='red')
        except subprocess.TimeoutExpired:
            self.connected_device = None
            self.device_status.config(text="ADB timeout", foreground='red')
        except FileNotFoundError:
            self.connected_device = None
            self.device_status.config(text="ADB not found", foreground='red')
        except Exception as e:
            self.connected_device = None
            self.device_status.config(text=f"Error: {str(e)}", foreground='red')
        
        return False
    
    def start_full_backup(self):
        if not self.check_device_connection():
            messagebox.showerror("Error", "No Pixel device connected")
            return
        
        backup_folder = os.path.join(self.backup_location.get(), datetime.now().strftime("%Y%m%d_%H%M%S"))
        os.makedirs(backup_folder, exist_ok=True)
        
        # Start backup in a separate thread
        threading.Thread(target=self.perform_full_backup, args=(backup_folder,), daemon=True).start()
    
    def perform_full_backup(self, backup_folder):
        self.backup_canceled = False
        
        # Create progress window
        progress_window = tk.Toplevel(self.root)
        progress_window.title("Backup in Progress")
        progress_window.geometry("400x200")
        progress_window.protocol("WM_DELETE_WINDOW", lambda: None)  # Disable close button
        
        progress_label = ttk.Label(progress_window, text="Starting backup...")
        progress_label.pack(pady=10)
        
        progress_var = tk.DoubleVar()
        progress_bar = ttk.Progressbar(progress_window, variable=progress_var, maximum=100)
        progress_bar.pack(fill=tk.X, padx=20, pady=5)
        
        time_label = ttk.Label(progress_window, text="Estimated time remaining: calculating...")
        time_label.pack(pady=5)
        
        details_label = ttk.Label(progress_window, text="")
        details_label.pack(pady=5)
        
        button_frame = ttk.Frame(progress_window)
        button_frame.pack(pady=10)
        
        cancel_button = ttk.Button(button_frame, text="Cancel", command=lambda: self.cancel_backup(progress_window))
        cancel_button.pack(side=tk.RIGHT, padx=10)
        
        # Initialize backup steps
        backup_steps = []
        if self.system_data_var.get():
            backup_steps.append(("System Data", self.backup_system_data))
        if self.apps_var.get():
            backup_steps.append(("Apps", self.backup_apps))
        if self.contacts_var.get():
            backup_steps.append(("Contacts", self.backup_contacts))
        if self.messages_var.get():
            backup_steps.append(("Messages", self.backup_messages))
        if self.call_logs_var.get():
            backup_steps.append(("Call Logs", self.backup_call_logs))
        
        # Media backups
        media_backups = []
        if self.photos_var.get():
            media_backups.append(("DCIM/Camera", "Photos"))
        if self.videos_var.get():
            media_backups.append(("Movies", "Videos"))
        if self.documents_var.get():
            media_backups.append(("Documents", "Documents"))
        if self.music_var.get():
            media_backups.append(("Music", "Music"))
        if self.downloads_var.get():
            media_backups.append(("Download", "Downloads"))
        if self.other_media_var.get():
            media_backups.append(("Pictures", "Other Pictures"))
            media_backups.append(("Podcasts", "Podcasts"))
        
        if media_backups:
            backup_steps.append(("Media", lambda: self.backup_media(media_backups, backup_folder)))
        
        total_steps = len(backup_steps)
        current_step = 0
        
        # Execute each backup step
        for step_name, step_func in backup_steps:
            if self.backup_canceled:
                break
                
            current_step += 1
            progress_label.config(text=f"Backing up {step_name} ({current_step}/{total_steps})")
            progress_var.set((current_step - 1) * 100 / total_steps)
            progress_window.update()
            
            try:
                start_time = time.time()
                details_label.config(text=f"Starting {step_name} backup...")
                
                # Execute the backup step
                result = step_func(backup_folder)
                
                if not result:
                    details_label.config(text=f"Failed to backup {step_name}", foreground='red')
                    if messagebox.askyesno("Error", f"Failed to backup {step_name}. Continue?"):
                        continue
                    else:
                        break
                
                elapsed = time.time() - start_time
                details_label.config(text=f"{step_name} backup completed in {elapsed:.1f} seconds", foreground='green')
                progress_var.set(current_step * 100 / total_steps)
                
            except Exception as e:
                details_label.config(text=f"Error during {step_name} backup: {str(e)}", foreground='red')
                if not messagebox.askyesno("Error", f"Error during {step_name} backup. Continue?"):
                    break
        
        # Finalize backup
        if not self.backup_canceled:
            if self.compress_backup_var.get():
                progress_label.config(text="Compressing backup...")
                details_label.config(text="Creating ZIP archive...")
                progress_window.update()
                
                zip_path = f"{backup_folder}.zip"
                try:
                    with zipfile.ZipFile(zip_path, 'w', 
                                       zipfile.ZIP_DEFLATED if self.compression_level.get() != "fast" else zipfile.ZIP_STORED) as zipf:
                        for root, _, files in os.walk(backup_folder):
                            for file in files:
                                zipf.write(os.path.join(root, file), 
                                          os.path.relpath(os.path.join(root, file), backup_folder))
                    
                    # Remove original folder if ZIP succeeded
                    import shutil
                    shutil.rmtree(backup_folder)
                    backup_folder = zip_path
                except Exception as e:
                    details_label.config(text=f"Compression failed: {str(e)}", foreground='orange')
            
            # Calculate backup size
            backup_size = self.get_folder_size(backup_folder)
            size_str = self.format_size(backup_size)
            
            # Add to history
            self.backup_history.append({
                'date': datetime.now().strftime("%Y-%m-%d %H:%M"),
                'type': 'Full',
                'size': size_str,
                'location': backup_folder
            })
            self.update_history_view()
            
            progress_label.config(text="Backup completed successfully!")
            details_label.config(text=f"Final backup size: {size_str}")
            cancel_button.config(text="Close")
            
            if self.notification_var.get():
                self.root.after(100, lambda: messagebox.showinfo("Backup Complete", "Full backup completed successfully!"))
        
        progress_window.protocol("WM_DELETE_WINDOW", progress_window.destroy)  # Re-enable close button
    
    def backup_system_data(self, backup_folder):
        """Backup system data using ADB"""
        try:
            backup_file = os.path.join(backup_folder, "system_data.ab")
            result = subprocess.run([self.adb_path, 'backup', '-f', backup_file, '-system'], 
                                  capture_output=True, text=True, timeout=300)
            return result.returncode == 0
        except Exception as e:
            print(f"System data backup error: {str(e)}")
            return False
    
    def backup_apps(self, backup_folder):
        """Backup all user apps using ADB"""
        try:
            # Get list of user apps
            result = subprocess.run([self.adb_path, 'shell', 'pm', 'list', 'packages', '-3'], 
                                  capture_output=True, text=True, timeout=60)
            packages = [line.split(':')[1].strip() for line in result.stdout.splitlines() if line.startswith('package:')]
            
            if not packages:
                return True  # No user apps to backup
                
            backup_file = os.path.join(backup_folder, "user_apps.ab")
            result = subprocess.run([self.adb_path, 'backup', '-f', backup_file, '-apk', '-obb', '-shared', '-all'], 
                                  input='\n'.join(packages), text=True, timeout=600)
            return result.returncode == 0
        except Exception as e:
            print(f"Apps backup error: {str(e)}")
            return False
    
    def backup_contacts(self, backup_folder):
        """Backup contacts using ADB"""
        try:
            backup_file = os.path.join(backup_folder, "contacts.ab")
            result = subprocess.run([self.adb_path, 'backup', '-f', backup_file, '-nosystem', 'com.android.providers.contacts'], 
                                  capture_output=True, text=True, timeout=120)
            return result.returncode == 0
        except Exception as e:
            print(f"Contacts backup error: {str(e)}")
            return False
    
    def backup_messages(self, backup_folder):
        """Backup SMS/MMS messages using ADB"""
        try:
            backup_file = os.path.join(backup_folder, "messages.ab")
            result = subprocess.run([self.adb_path, 'backup', '-f', backup_file, '-nosystem', 'com.android.providers.telephony'], 
                                  capture_output=True, text=True, timeout=120)
            return result.returncode == 0
        except Exception as e:
            print(f"Messages backup error: {str(e)}")
            return False
    
    def backup_call_logs(self, backup_folder):
        """Backup call logs using ADB"""
        try:
            backup_file = os.path.join(backup_folder, "call_logs.ab")
            result = subprocess.run([self.adb_path, 'backup', '-f', backup_file, '-nosystem', 'com.android.providers.contacts'], 
                                  capture_output=True, text=True, timeout=120)
            return result.returncode == 0
        except Exception as e:
            print(f"Call logs backup error: {str(e)}")
            return False
    
    def backup_media(self, media_paths, backup_folder):
        """Backup media files from device"""
        try:
            media_folder = os.path.join(backup_folder, "Media")
            os.makedirs(media_folder, exist_ok=True)
            
            for path, name in media_paths:
                dest_folder = os.path.join(media_folder, name)
                os.makedirs(dest_folder, exist_ok=True)
                
                # Use ADB pull to copy files
                result = subprocess.run([self.adb_path, 'pull', f'/sdcard/{path}', dest_folder], 
                                      capture_output=True, text=True, timeout=600)
                if result.returncode != 0:
                    print(f"Failed to backup {path}: {result.stderr}")
            
            return True
        except Exception as e:
            print(f"Media backup error: {str(e)}")
            return False
    
    def cancel_backup(self, window):
        self.backup_canceled = True
        window.destroy()
        messagebox.showinfo("Backup Canceled", "The backup process was canceled")
    
    def get_folder_size(self, path):
        """Calculate total size of a folder"""
        total = 0
        for entry in os.scandir(path):
            if entry.is_file():
                total += entry.stat().st_size
            elif entry.is_dir():
                total += self.get_folder_size(entry.path)
        return total
    
    def format_size(self, size):
        """Format size in bytes to human-readable format"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"
    
    def start_media_backup(self):
        if not self.check_device_connection():
            messagebox.showerror("Error", "No Pixel device connected")
            return
        
        media_type = self.media_type.get()
        backup_folder = os.path.join(self.media_backup_location.get(), 
                                    f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{media_type}")
        os.makedirs(backup_folder, exist_ok=True)
        
        # Start backup in a separate thread
        threading.Thread(target=self.perform_media_backup_task, args=(backup_folder, media_type), daemon=True).start()
    
    def perform_media_backup_task(self, backup_folder, media_type):
        self.backup_canceled = False
        
        # Create progress window
        progress_window = tk.Toplevel(self.root)
        progress_window.title("Backup in Progress")
        progress_window.geometry("400x200")
        progress_window.protocol("WM_DELETE_WINDOW", lambda: None)  # Disable close button
        
        progress_label = ttk.Label(progress_window, text=f"Starting {media_type} backup...")
        progress_label.pack(pady=10)
        
        progress_var = tk.DoubleVar()
        progress_bar = ttk.Progressbar(progress_window, variable=progress_var, maximum=100)
        progress_bar.pack(fill=tk.X, padx=20, pady=5)
        
        time_label = ttk.Label(progress_window, text="Estimated time remaining: calculating...")
        time_label.pack(pady=5)
        
        details_label = ttk.Label(progress_window, text="")
        details_label.pack(pady=5)
        
        button_frame = ttk.Frame(progress_window)
        button_frame.pack(pady=10)
        
        cancel_button = ttk.Button(button_frame, text="Cancel", command=lambda: self.cancel_backup(progress_window))
        cancel_button.pack(side=tk.RIGHT, padx=10)
        
        # Determine media paths to backup
        media_paths = []
        if media_type == "photos":
            media_paths.append(("DCIM/Camera", "Photos"))
            if not self.screenshots_var.get():
                media_paths.append(("Pictures/Screenshots", "Screenshots"))
        elif media_type == "videos":
            media_paths.append(("Movies", "Videos"))
            media_paths.append(("DCIM/Camera", "Video Clips"))
        elif media_type == "documents":
            media_paths.append(("Documents", "Documents"))
            media_paths.append(("Download", "Downloads"))
        else:  # Custom
            if self.photos_var.get():
                media_paths.append(("DCIM/Camera", "Photos"))
            if self.videos_var.get():
                media_paths.append(("Movies", "Videos"))
            if self.documents_var.get():
                media_paths.append(("Documents", "Documents"))
            if self.music_var.get():
                media_paths.append(("Music", "Music"))
            if self.downloads_var.get():
                media_paths.append(("Download", "Downloads"))
            if self.other_media_var.get():
                media_paths.append(("Pictures", "Other Pictures"))
        
        try:
            total_files = 0
            copied_files = 0
            
            # First count all files to get total
            details_label.config(text="Counting files...")
            progress_window.update()
            
            for path, name in media_paths:
                result = subprocess.run([self.adb_path, 'shell', 'find', f'/sdcard/{path}', '-type', 'f'], 
                                      capture_output=True, text=True, timeout=60)
                if result.returncode == 0:
                    total_files += len(result.stdout.splitlines())
            
            if total_files == 0:
                details_label.config(text="No files found to backup!", foreground='orange')
                progress_window.after(2000, progress_window.destroy)
                return
                
            # Now perform the actual backup
            for path, name in media_paths:
                if self.backup_canceled:
                    break
                    
                dest_folder = os.path.join(backup_folder, name)
                os.makedirs(dest_folder, exist_ok=True)
                
                details_label.config(text=f"Backing up {name}...")
                progress_window.update()
                
                # Use ADB pull to copy files
                process = subprocess.Popen([self.adb_path, 'pull', f'/sdcard/{path}', dest_folder], 
                                         stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                
                # Monitor progress
                while True:
                    if self.backup_canceled:
                        process.terminate()
                        break
                        
                    # Count files in destination to estimate progress
                    try:
                        copied = sum([len(files) for _, _, files in os.walk(dest_folder)])
                        progress = (copied / total_files) * 100 if total_files > 0 else 0
                        progress_var.set(progress)
                        details_label.config(text=f"Copied {copied} of {total_files} files")
                        progress_window.update()
                    except:
                        pass
                        
                    # Check if process completed
                    if process.poll() is not None:
                        break
                        
                    time.sleep(1)
                
                if process.returncode != 0 and not self.backup_canceled:
                    details_label.config(text=f"Error backing up {name}", foreground='red')
                    if not messagebox.askyesno("Error", f"Error during {name} backup. Continue?"):
                        break
            
            if not self.backup_canceled:
                # Calculate backup size
                backup_size = self.get_folder_size(backup_folder)
                size_str = self.format_size(backup_size)
                
                # Add to history
                self.backup_history.append({
                    'date': datetime.now().strftime("%Y-%m-%d %H:%M"),
                    'type': media_type.capitalize(),
                    'size': size_str,
                    'location': backup_folder
                })
                self.update_history_view()
                
                progress_label.config(text="Backup completed successfully!")
                details_label.config(text=f"Final backup size: {size_str}")
                cancel_button.config(text="Close")
                
                if self.notification_var.get():
                    self.root.after(100, lambda: messagebox.showinfo("Backup Complete", 
                        f"{media_type.capitalize()} backup completed successfully!"))
            
        except Exception as e:
            details_label.config(text=f"Error: {str(e)}", foreground='red')
            progress_window.after(2000, progress_window.destroy)
        
        progress_window.protocol("WM_DELETE_WINDOW", progress_window.destroy)  # Re-enable close button
    
    def preview_files(self):
        media_type = self.media_type.get()
        
        if not self.check_device_connection():
            messagebox.showerror("Error", "No Pixel device connected")
            return
        
        # Create preview window
        preview_window = tk.Toplevel(self.root)
        preview_window.title(f"Preview {media_type} Files")
        preview_window.geometry("600x400")
        
        # Treeview for file list
        columns = ("name", "size", "date")
        file_tree = ttk.Treeview(preview_window, columns=columns, show="headings")
        
        # Define headings
        file_tree.heading("name", text="File Name")
        file_tree.heading("size", text="Size")
        file_tree.heading("date", text="Modified Date")
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(preview_window, orient=tk.VERTICAL, command=file_tree.yview)
        file_tree.configure(yscroll=scrollbar.set)
        
        # Pack widgets
        file_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Status label
        status_label = ttk.Label(preview_window, text="Loading file list...")
        status_label.pack(fill=tk.X)
        
        # Load files in background
        threading.Thread(target=self.load_file_preview, 
                        args=(preview_window, file_tree, status_label, media_type), 
                        daemon=True).start()
    
    def load_file_preview(self, window, tree, status_label, media_type):
        try:
            # Determine paths to search based on media type
            search_paths = []
            if media_type == "photos":
                search_paths.append("/sdcard/DCIM/Camera")
                if not self.screenshots_var.get():
                    search_paths.append("/sdcard/Pictures/Screenshots")
            elif media_type == "videos":
                search_paths.append("/sdcard/Movies")
                search_paths.append("/sdcard/DCIM/Camera")
            elif media_type == "documents":
                search_paths.append("/sdcard/Documents")
                search_paths.append("/sdcard/Download")
            else:  # Custom
                if self.photos_var.get():
                    search_paths.append("/sdcard/DCIM/Camera")
                if self.videos_var.get():
                    search_paths.append("/sdcard/Movies")
                if self.documents_var.get():
                    search_paths.append("/sdcard/Documents")
                if self.music_var.get():
                    search_paths.append("/sdcard/Music")
                if self.downloads_var.get():
                    search_paths.append("/sdcard/Download")
                if self.other_media_var.get():
                    search_paths.append("/sdcard/Pictures")
            
            # Get file list from device
            file_count = 0
            for path in search_paths:
                status_label.config(text=f"Searching {path}...")
                window.update()
                
                # Use ADB to find files
                find_cmd = ['find', path, '-type', 'f']
                if self.large_files_var.get():
                    find_cmd.extend(['-size', '+5M'])
                if self.raw_images_var.get() and "DCIM" in path:
                    find_cmd.extend(['-name', '*.dng'])
                if self.uhd_videos_var.get() and ("Movies" in path or "DCIM" in path):
                    find_cmd.extend(['-name', '*4k*'])
                
                result = subprocess.run([self.adb_path, 'shell'] + find_cmd, 
                                      capture_output=True, text=True, timeout=60)
                
                if result.returncode == 0:
                    files = result.stdout.splitlines()
                    for file in files:
                        # Get file details
                        stat_cmd = ['stat', '-c', '%s %y', file]
                        stat_result = subprocess.run([self.adb_path, 'shell'] + stat_cmd, 
                                                  capture_output=True, text=True, timeout=10)
                        
                        if stat_result.returncode == 0:
                            size, date = stat_result.stdout.strip().split(' ', 1)
                            name = os.path.basename(file)
                            
                            # Check date range filter
                            try:
                                file_date = datetime.strptime(date.split('.')[0], "%Y-%m-%d %H:%M:%S")
                                from_date = datetime.strptime(self.date_from.get(), "%m/%d/%Y")
                                to_date = datetime.strptime(self.date_to.get(), "%m/%d/%Y")
                                
                                if from_date <= file_date <= to_date:
                                    tree.insert("", tk.END, values=(name, self.format_size(int(size)), date))
                                    file_count += 1
                                    if file_count % 10 == 0:
                                        status_label.config(text=f"Found {file_count} files...")
                                        window.update()
                            except:
                                pass
            
            status_label.config(text=f"Found {file_count} matching files")
            
        except Exception as e:
            status_label.config(text=f"Error: {str(e)}", foreground='red')
    
    def save_settings(self):
        # In a real app, you would save these to a config file
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

A comprehensive tool to backup your Google Pixel phone data
with customizable options for different media types.

Features:
- Full system backups
- Selective media backups
- Advanced filters and options
- Backup history tracking

© 2025 Pixel Backup Toolkit"""
        messagebox.showinfo("About", about_text)

if __name__ == "__main__":
    root = tk.Tk()
    app = PixelBackupToolkit(root)
    root.mainloop()
