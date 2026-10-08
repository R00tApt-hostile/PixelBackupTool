import os
import json
import shutil
import platform
import queue
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from datetime import datetime
import subprocess
import threading
import time
import zipfile

try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

CONFIG_FILE = os.path.expanduser("~/.pixel_backup_toolkit.json")
COMPRESS_LEVELS = {"fast": 1, "balanced": 6, "maximum": 9}


class PixelBackupToolkit:
    def __init__(self, root):
        self.root = root
        self.root.title("Google Pixel Backup Toolkit")
        self.root.geometry("900x650")
        self.root.minsize(720, 520)

        # ---- state must exist BEFORE UI is built ----
        self.backup_history = []
        self.backup_process = None
        self.backup_canceled = False
        self.connected_device = None
        self.adb_path = self.find_adb()

        # thread-safe UI update queue
        self._ui_queue = queue.Queue()
        self._schedule_ui_poll()

        # styles first, then build UI
        self.setup_styles()
        self.setup_ui()
        self.load_settings()

        # defer device check until mainloop is running
        self.root.after(150, self.check_device_connection)

    # ---------------- thread-safe UI helpers ----------------
    def _schedule_ui_poll(self):
        self.root.after(80, self._process_ui_queue)

    def _process_ui_queue(self):
        try:
            while True:
                func, args, kwargs = self._ui_queue.get_nowait()
                try:
                    func(*args, **kwargs)
                except Exception as exc:
                    print(f"[UI callback error] {exc}")
        except queue.Empty:
            pass
        self._schedule_ui_poll()

    def ui(self, func, *args, **kwargs):
        """Run `func` on the Tk main thread (safe from workers)."""
        self._ui_queue.put((func, args, kwargs))

    # ---------------- ADB discovery ----------------
    def find_adb(self):
        candidates = []
        android_home = os.environ.get("ANDROID_HOME") or os.environ.get("ANDROID_SDK_ROOT")
        exe = "adb.exe" if platform.system() == "Windows" else "adb"
        if android_home:
            candidates.append(os.path.join(android_home, "platform-tools", exe))
        if platform.system() == "Windows":
            candidates.append(os.path.expanduser(
                r"~\AppData\Local\Android\Sdk\platform-tools\adb.exe"))
        else:
            candidates.extend([
                "/usr/bin/adb", "/usr/local/bin/adb", "/opt/homebrew/bin/adb"
            ])
        candidates.append(exe)  # fall back to PATH

        for cand in candidates:
            if os.sep in cand or (os.altsep and os.altsep in cand):
                if os.path.isfile(cand):
                    return cand
            else:
                found = shutil.which(cand)
                if found:
                    return found
        return "adb"

    # ---------------- styles ----------------
    def setup_styles(self):
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure('TFrame', background='#f5f5f5')
        style.configure('TLabel', background='#f5f5f5', font=('Segoe UI', 10))
        style.configure('TButton', font=('Segoe UI', 10))
        style.configure('TNotebook', background='#f5f5f5')
        style.configure('TNotebook.Tab', font=('Segoe UI', 10, 'bold'))
        style.configure('TCheckbutton', background='#f5f5f5')
        style.configure('TRadiobutton', background='#f5f5f5')
        style.configure('TLabelframe', background='#f5f5f5')
        style.configure('TLabelframe.Label', background='#f5f5f5')
        style.configure('Header.TLabel', font=('Segoe UI', 16, 'bold'),
                        background='#f5f5f5')

    # ---------------- UI ----------------
    def setup_ui(self):
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill=tk.X, pady=(0, 10))

        if PIL_AVAILABLE and os.path.exists("pixel_logo.png"):
            try:
                logo_img = Image.open("pixel_logo.png").resize((32, 32))
                self.logo = ImageTk.PhotoImage(logo_img)
                ttk.Label(header_frame, image=self.logo).pack(side=tk.LEFT, padx=(0, 10))
            except Exception:
                pass

        ttk.Label(header_frame, text="Google Pixel Backup Toolkit",
                  style='Header.TLabel').pack(side=tk.LEFT)

        self.device_status = ttk.Label(header_frame, text="Checking for device…",
                                       foreground='red')
        self.device_status.pack(side=tk.RIGHT)

        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        self.setup_full_backup_tab()
        self.setup_media_backup_tab()
        self.setup_settings_tab()
        self.setup_history_tab()

        footer = ttk.Frame(main_frame)
        footer.pack(fill=tk.X, pady=(10, 0))
        ttk.Button(footer, text="Connect Phone",
                   command=self.connect_phone).pack(side=tk.LEFT, padx=5)
        ttk.Button(footer, text="Refresh",
                   command=self.check_device_connection).pack(side=tk.LEFT, padx=5)
        ttk.Button(footer, text="About",
                   command=self.show_about).pack(side=tk.LEFT, padx=5)
        ttk.Button(footer, text="Exit",
                   command=self.root.quit).pack(side=tk.RIGHT, padx=5)

    def setup_full_backup_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Full Backup")

        options_frame = ttk.LabelFrame(tab, text="Backup Options")
        options_frame.pack(fill=tk.X, padx=5, pady=5)

        self.system_data_var = tk.BooleanVar(value=True)
        self.apps_var = tk.BooleanVar(value=True)
        self.contacts_var = tk.BooleanVar(value=True)
        self.messages_var = tk.BooleanVar(value=True)
        self.call_logs_var = tk.BooleanVar(value=True)

        for text, var in [("System Data", self.system_data_var),
                          ("Apps", self.apps_var),
                          ("Contacts", self.contacts_var),
                          ("Messages", self.messages_var),
                          ("Call Logs", self.call_logs_var)]:
            ttk.Checkbutton(options_frame, text=text, variable=var).pack(anchor=tk.W)

        media_frame = ttk.LabelFrame(tab, text="Media Options")
        media_frame.pack(fill=tk.X, padx=5, pady=5)

        self.photos_var = tk.BooleanVar(value=True)
        self.videos_var = tk.BooleanVar(value=True)
        self.documents_var = tk.BooleanVar(value=True)
        self.music_var = tk.BooleanVar(value=True)
        self.downloads_var = tk.BooleanVar(value=True)
        self.other_media_var = tk.BooleanVar(value=True)

        for row_vars in [(self.photos_var, "Photos", self.videos_var, "Videos"),
                         (self.documents_var, "Documents", self.music_var, "Music"),
                         (self.downloads_var, "Downloads", self.other_media_var, "Other Media")]:
            row = ttk.Frame(media_frame)
            row.pack(fill=tk.X)
            ttk.Checkbutton(row, text=row_vars[1], variable=row_vars[0]).pack(side=tk.LEFT, padx=5)
            ttk.Checkbutton(row, text=row_vars[3], variable=row_vars[2]).pack(side=tk.LEFT, padx=5)

        location_frame = ttk.LabelFrame(tab, text="Backup Location")
        location_frame.pack(fill=tk.X, padx=5, pady=5)
        self.backup_location = tk.StringVar(value=os.path.expanduser("~/Pixel_Backups"))
        ttk.Entry(location_frame, textvariable=self.backup_location
                  ).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        ttk.Button(location_frame, text="Browse",
                   command=self.browse_backup_location).pack(side=tk.RIGHT)

        ttk.Button(tab, text="Start Full Backup",
                   command=self.start_full_backup).pack(pady=10)

    def setup_media_backup_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Media Backup")

        type_frame = ttk.LabelFrame(tab, text="Media Type Selection")
        type_frame.pack(fill=tk.X, padx=5, pady=5)

        self.media_type = tk.StringVar(value="custom")
        for row_vars in [("photos", "Photos Only", "videos", "Videos Only"),
                         ("documents", "Documents Only", "custom", "Custom Selection")]:
            row = ttk.Frame(type_frame)
            row.pack(fill=tk.X)
            ttk.Radiobutton(row, text=row_vars[1], variable=self.media_type,
                            value=row_vars[0]).pack(side=tk.LEFT, padx=5)
            ttk.Radiobutton(row, text=row_vars[3], variable=self.media_type,
                            value=row_vars[2]).pack(side=tk.LEFT, padx=5)

        date_frame = ttk.LabelFrame(tab, text="Date Range")
        date_frame.pack(fill=tk.X, padx=5, pady=5)
        ttk.Label(date_frame, text="From:").pack(side=tk.LEFT, padx=5)
        self.date_from = ttk.Entry(date_frame, width=12)
        self.date_from.pack(side=tk.LEFT)
        self.date_from.insert(0, "01/01/2023")
        ttk.Label(date_frame, text="To:").pack(side=tk.LEFT, padx=5)
        self.date_to = ttk.Entry(date_frame, width=12)
        self.date_to.pack(side=tk.LEFT)
        self.date_to.insert(0, datetime.now().strftime("%m/%d/%Y"))

        filter_frame = ttk.LabelFrame(tab, text="Advanced Filters")
        filter_frame.pack(fill=tk.X, padx=5, pady=5)
        self.large_files_var = tk.BooleanVar()
        self.screenshots_var = tk.BooleanVar()
        self.raw_images_var = tk.BooleanVar()
        self.uhd_videos_var = tk.BooleanVar()
        for text, var in [("Over 5MB files only", self.large_files_var),
                          ("Screenshots only", self.screenshots_var),
                          ("RAW images only", self.raw_images_var),
                          ("4K videos only", self.uhd_videos_var)]:
            ttk.Checkbutton(filter_frame, text=text, variable=var).pack(anchor=tk.W)

        location_frame = ttk.LabelFrame(tab, text="Backup Location")
        location_frame.pack(fill=tk.X, padx=5, pady=5)
        self.media_backup_location = tk.StringVar(value=os.path.expanduser("~/Pixel_Media"))
        ttk.Entry(location_frame, textvariable=self.media_backup_location
                  ).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        ttk.Button(location_frame, text="Browse",
                   command=self.browse_media_location).pack(side=tk.RIGHT)

        button_frame = ttk.Frame(tab)
        button_frame.pack(fill=tk.X, pady=10)
        ttk.Button(button_frame, text="Preview Selected Files",
                   command=self.preview_files).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Start Media Backup",
                   command=self.start_media_backup).pack(side=tk.RIGHT, padx=5)

    def setup_settings_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Settings")

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
                     values=list(COMPRESS_LEVELS.keys()),
                     state="readonly").pack(side=tk.LEFT)

        notify_frame = ttk.LabelFrame(tab, text="Notifications")
        notify_frame.pack(fill=tk.X, padx=5, pady=5)
        self.sound_var = tk.BooleanVar(value=True)
        self.notification_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(notify_frame, text="Play sound when backup completes",
                        variable=self.sound_var).pack(anchor=tk.W)
        ttk.Checkbutton(notify_frame, text="Show desktop notification",
                        variable=self.notification_var).pack(anchor=tk.W)

        connection_frame = ttk.LabelFrame(tab, text="Connection")
        connection_frame.pack(fill=tk.X, padx=5, pady=5)
        self.default_connection = tk.StringVar(value="usb")
        ttk.Label(connection_frame, text="Default connection:").pack(anchor=tk.W)
        ttk.Combobox(connection_frame, textvariable=self.default_connection,
                     values=["usb", "wifi"], state="readonly").pack(fill=tk.X, pady=(0, 5))
        self.auto_detect_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(connection_frame, text="Auto-detect Pixel devices",
                        variable=self.auto_detect_var).pack(anchor=tk.W)

        button_frame = ttk.Frame(tab)
        button_frame.pack(fill=tk.X, pady=10)
        ttk.Button(button_frame, text="Save Settings",
                   command=self.save_settings).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Restore Defaults",
                   command=self.restore_defaults).pack(side=tk.RIGHT, padx=5)

    def setup_history_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Backup History")

        columns = ("date", "type", "size", "location")
        self.history_tree = ttk.Treeview(tab, columns=columns, show="headings")
        for col, width in [("date", 130), ("type", 100), ("size", 80), ("location", 350)]:
            self.history_tree.heading(col, text=col.capitalize())
            self.history_tree.column(col, width=width)

        scrollbar = ttk.Scrollbar(tab, orient=tk.VERTICAL,
                                  command=self.history_tree.yview)
        self.history_tree.configure(yscroll=scrollbar.set)
        self.history_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        button_frame = ttk.Frame(tab)
        button_frame.pack(fill=tk.X, pady=5)
        ttk.Button(button_frame, text="Refresh",
                   command=self.update_history_view).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Delete Selected",
                   command=self.delete_selected_backup).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Open Location",
                   command=self.open_backup_location).pack(side=tk.RIGHT, padx=5)

    # ---------------- history ----------------
    def update_history_view(self):
        for item in self.history_tree.get_children():
            self.history_tree.delete(item)
        for backup in self.backup_history:
            self.history_tree.insert("", tk.END, values=(
                backup.get("date", ""),
                backup.get("type", ""),
                backup.get("size", ""),
                backup.get("location", ""),
            ))

    def delete_selected_backup(self):
        selected = self.history_tree.selection()
        if not selected:
            return
        item = self.history_tree.item(selected[0])
        location = item['values'][3]
        if not messagebox.askyesno("Confirm Delete", f"Delete backup at {location}?"):
            return
        try:
            if os.path.isdir(location):
                shutil.rmtree(location)
            elif os.path.isfile(location):
                os.remove(location)
            self.backup_history = [b for b in self.backup_history
                                   if b.get("location") != location]
            self.update_history_view()
            messagebox.showinfo("Success", "Backup deleted successfully")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to delete backup: {e}")

    def open_backup_location(self):
        selected = self.history_tree.selection()
        if not selected:
            return
        location = self.history_tree.item(selected[0])['values'][3]
        if not os.path.exists(location):
            messagebox.showerror("Error", "Backup location no longer exists")
            return
        try:
            if platform.system() == "Windows":
                os.startfile(location)  # noqa
            elif platform.system() == "Darwin":
                subprocess.Popen(["open", location])
            else:
                subprocess.Popen(["xdg-open", location])
        except Exception as e:
            messagebox.showerror("Error", f"Cannot open location: {e}")

    # ---------------- browse ----------------
    def browse_backup_location(self):
        folder = filedialog.askdirectory(initialdir=self.backup_location.get())
        if folder:
            self.backup_location.set(folder)

    def browse_media_location(self):
        folder = filedialog.askdirectory(initialdir=self.media_backup_location.get())
        if folder:
            self.media_backup_location.set(folder)

    # ---------------- device ----------------
    def connect_phone(self):
        if self.check_device_connection():
            messagebox.showinfo("Connected", f"Device connected: {self.connected_device}")
        else:
            messagebox.showerror(
                "Error",
                "No Pixel device detected. Connect via USB and enable USB debugging.")

    def check_device_connection(self):
        try:
            result = subprocess.run([self.adb_path, 'devices'],
                                    capture_output=True, text=True, timeout=5)
            devices = [line.split('\t')[0]
                       for line in result.stdout.splitlines()[1:] if line.strip()]
            if devices:
                model_result = subprocess.run(
                    [self.adb_path, 'shell', 'getprop', 'ro.product.model'],
                    capture_output=True, text=True, timeout=5)
                model = model_result.stdout.strip()
                if "Pixel" in model:
                    self.connected_device = model
                    self.device_status.config(text=f"Connected: {model}",
                                              foreground='green')
                    return True
                self.connected_device = None
                self.device_status.config(text=f"Non-Pixel: {model or 'unknown'}",
                                          foreground='orange')
                return False
            self.connected_device = None
            self.device_status.config(text="No device connected", foreground='red')
        except subprocess.TimeoutExpired:
            self.device_status.config(text="ADB timeout", foreground='red')
        except FileNotFoundError:
            self.device_status.config(text="ADB not found", foreground='red')
        except Exception as e:
            self.device_status.config(text=f"Error: {e}", foreground='red')
        return False

    # ---------------- progress window ----------------
    def _create_progress_window(self, title):
        win = tk.Toplevel(self.root)
        win.title(f"{title} - In Progress")
        win.geometry("460x230")
        win.transient(self.root)
        win.grab_set()

        label = ttk.Label(win, text="Starting…")
        label.pack(pady=10)

        var = tk.DoubleVar(value=0)
        ttk.Progressbar(win, variable=var, maximum=100).pack(fill=tk.X, padx=20, pady=5)

        time_label = ttk.Label(win, text="")
        time_label.pack()

        detail_label = ttk.Label(win, text="")
        detail_label.pack(pady=4)

        btn_frame = ttk.Frame(win)
        btn_frame.pack(pady=10)
        cancel_btn = ttk.Button(btn_frame, text="Cancel")
        cancel_btn.pack(side=tk.RIGHT, padx=10)

        win.protocol("WM_DELETE_WINDOW", lambda: None)  # block close while running

        return {
            "window": win, "label": label, "var": var,
            "time_label": time_label, "detail_label": detail_label,
            "cancel_btn": cancel_btn,
        }

    def _progress_update(self, progress, text=None, value=None, detail=None,
                         detail_color=None, done=False):
        def _apply():
            if text is not None:
                progress["label"].config(text=text)
            if value is not None:
                progress["var"].set(value)
            if detail is not None:
                progress["detail_label"].config(text=detail)
            if detail_color is not None:
                progress["detail_label"].config(foreground=detail_color)
            if done:
                progress["cancel_btn"].config(text="Close",
                                              command=progress["window"].destroy)
                progress["window"].protocol("WM_DELETE_WINDOW",
                                            progress["window"].destroy)
                progress["window"].grab_release()
        self.ui(_apply)

    def cancel_backup(self, progress):
        self.backup_canceled = True
        try:
            progress["window"].grab_release()
            progress["window"].destroy()
        except tk.TclError:
            pass
        messagebox.showinfo("Backup Canceled", "The backup process was canceled")

    # ---------------- full backup ----------------
    def start_full_backup(self):
        if not self.check_device_connection():
            messagebox.showerror("Error", "No Pixel device connected")
            return

        backup_folder = os.path.join(
            self.backup_location.get(),
            datetime.now().strftime("%Y%m%d_%H%M%S"))
        try:
            os.makedirs(backup_folder, exist_ok=True)
        except OSError as e:
            messagebox.showerror("Error", f"Cannot create backup folder: {e}")
            return

        progress = self._create_progress_window("Full Backup")
        progress["cancel_btn"].config(command=lambda: self.cancel_backup(progress))

        self.backup_canceled = False
        threading.Thread(target=self._perform_full_backup,
                         args=(backup_folder, progress),
                         daemon=True).start()

    def _perform_full_backup(self, backup_folder, progress):
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
            backup_steps.append(("Media",
                                 lambda bf: self.backup_media(media_backups, bf)))

        total = max(len(backup_steps), 1)
        for idx, (name, func) in enumerate(backup_steps, 1):
            if self.backup_canceled:
                return
            self._progress_update(progress,
                                  text=f"Backing up {name} ({idx}/{total})",
                                  value=(idx - 1) * 100 / total,
                                  detail=f"Starting {name} backup…",
                                  detail_color='black')
            start = time.time()
            try:
                ok = func(backup_folder)
            except Exception as e:
                ok = False
                self._progress_update(progress, detail=f"{name} error: {e}",
                                      detail_color='red')
            if not ok:
                self._progress_update(progress, detail=f"Failed: {name}",
                                      detail_color='red')
                if self.backup_canceled:
                    return
                if not messagebox.askyesno("Error",
                                           f"Failed to backup {name}. Continue?"):
                    return
                continue
            elapsed = time.time() - start
            self._progress_update(progress,
                                  detail=f"{name} completed in {elapsed:.1f}s",
                                  detail_color='green',
                                  value=idx * 100 / total)

        if self.backup_canceled:
            return

        # Optional compression
        if self.compress_backup_var.get():
            self._progress_update(progress, text="Compressing backup…",
                                  detail="Creating ZIP archive…")
            zip_path = f"{backup_folder}.zip"
            level = COMPRESS_LEVELS.get(self.compression_level.get(), 6)
            try:
                with zipfile.ZipFile(zip_path, 'w',
                                     zipfile.ZIP_DEFLATED,
                                     compresslevel=level) as zf:
                    for root_dir, _, files in os.walk(backup_folder):
                        for f in files:
                            full = os.path.join(root_dir, f)
                            zf.write(full, os.path.relpath(full, backup_folder))
                shutil.rmtree(backup_folder)
                backup_folder = zip_path
            except Exception as e:
                self._progress_update(progress, detail=f"Compression failed: {e}",
                                      detail_color='orange')

        size_str = self.format_size(self.get_folder_size(backup_folder))

        self.backup_history.append({
            'date': datetime.now().strftime("%Y-%m-%d %H:%M"),
            'type': 'Full',
            'size': size_str,
            'location': backup_folder,
        })
        self.ui(self.update_history_view)

        self._progress_update(progress, text="Backup completed successfully!",
                              detail=f"Final size: {size_str}", value=100,
                              detail_color='green', done=True)

        if self.notification_var.get():
            self.ui(messagebox.showinfo, "Backup Complete",
                    "Full backup completed successfully!")

    # ---------------- individual backup steps ----------------
    def backup_system_data(self, backup_folder):
        try:
            out = os.path.join(backup_folder, "system_data.ab")
            r = subprocess.run([self.adb_path, 'backup', '-f', out, '-system'],
                               capture_output=True, text=True, timeout=1800)
            return r.returncode == 0
        except Exception as e:
            print(f"System data backup error: {e}")
            return False

    def backup_apps(self, backup_folder):
        """Backup all user apps."""
        try:
            # adb backup does NOT accept package names via stdin; use -all
            out = os.path.join(backup_folder, "user_apps.ab")
            r = subprocess.run(
                [self.adb_path, 'backup', '-f', out,
                 '-apk', '-obb', '-shared', '-all'],
                capture_output=True, text=True, timeout=3600)
            return r.returncode == 0
        except Exception as e:
            print(f"Apps backup error: {e}")
            return False

    def backup_contacts(self, backup_folder):
        try:
            out = os.path.join(backup_folder, "contacts.ab")
            r = subprocess.run(
                [self.adb_path, 'backup', '-f', out, '-nosystem',
                 'com.android.providers.contacts'],
                capture_output=True, text=True, timeout=600)
            return r.returncode == 0
        except Exception as e:
            print(f"Contacts backup error: {e}")
            return False

    def backup_messages(self, backup_folder):
        try:
            out = os.path.join(backup_folder, "messages.ab")
            r = subprocess.run(
                [self.adb_path, 'backup', '-f', out, '-nosystem',
                 'com.android.providers.telephony'],
                capture_output=True, text=True, timeout=600)
            return r.returncode == 0
        except Exception as e:
            print(f"Messages backup error: {e}")
            return False

    def backup_call_logs(self, backup_folder):
        try:
            out = os.path.join(backup_folder, "call_logs.ab")
            r = subprocess.run(
                [self.adb_path, 'backup', '-f', out, '-nosystem',
                 'com.android.providers.contacts'],
                capture_output=True, text=True, timeout=600)
            return r.returncode == 0
        except Exception as e:
            print(f"Call logs backup error: {e}")
            return False

    def backup_media(self, media_paths, backup_folder):
        try:
            media_folder = os.path.join(backup_folder, "Media")
            os.makedirs(media_folder, exist_ok=True)
            ok = True
            for path, name in media_paths:
                if self.backup_canceled:
                    return False
                dest = os.path.join(media_folder, name)
                os.makedirs(dest, exist_ok=True)
                r = subprocess.run(
                    [self.adb_path, 'pull', f'/sdcard/{path}', dest],
                    capture_output=True, text=True, timeout=3600)
                if r.returncode != 0:
                    print(f"Failed to pull {path}: {r.stderr}")
                    ok = False
            return ok
        except Exception as e:
            print(f"Media backup error: {e}")
            return False

    # ---------------- size utils ----------------
    def get_folder_size(self, path):
        if os.path.isfile(path):
            try:
                return os.path.getsize(path)
            except OSError:
                return 0
        total = 0
        try:
            for entry in os.scandir(path):
                try:
                    if entry.is_file(follow_symlinks=False):
                        total += entry.stat().st_size
                    elif entry.is_dir(follow_symlinks=False):
                        total += self.get_folder_size(entry.path)
                except OSError:
                    continue
        except OSError:
            return 0
        return total

    def format_size(self, size):
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"

    # ---------------- media backup ----------------
    def start_media_backup(self):
        if not self.check_device_connection():
            messagebox.showerror("Error", "No Pixel device connected")
            return

        media_type = self.media_type.get()
        backup_folder = os.path.join(
            self.media_backup_location.get(),
            f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{media_type}")
        try:
            os.makedirs(backup_folder, exist_ok=True)
        except OSError as e:
            messagebox.showerror("Error", f"Cannot create backup folder: {e}")
            return

        progress = self._create_progress_window("Media Backup")
        progress["cancel_btn"].config(command=lambda: self.cancel_backup(progress))

        self.backup_canceled = False
        threading.Thread(target=self._perform_media_backup,
                         args=(backup_folder, media_type, progress),
                         daemon=True).start()

    def _perform_media_backup(self, backup_folder, media_type, progress):
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
        else:
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
            self._progress_update(progress, text="Counting files…",
                                  detail="Scanning device…")
            total_files = 0
            for path, _ in media_paths:
                try:
                    r = subprocess.run(
                        [self.adb_path, 'shell', 'find', f'/sdcard/{path}',
                         '-type', 'f'],
                        capture_output=True, text=True, timeout=120)
                    if r.returncode == 0:
                        total_files += len(r.stdout.splitlines())
                except Exception:
                    continue

            if total_files == 0:
                self._progress_update(progress, text="No files found.",
                                      detail_color='orange', done=True)
                return

            copied_total = 0
            for path, name in media_paths:
                if self.backup_canceled:
                    return
                dest = os.path.join(backup_folder, name)
                os.makedirs(dest, exist_ok=True)
                self._progress_update(progress, text=f"Backing up {name}…",
                                      detail=f"Pulling /sdcard/{path}")

                proc = subprocess.Popen(
                    [self.adb_path, 'pull', f'/sdcard/{path}', dest],
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                while proc.poll() is None:
                    if self.backup_canceled:
                        proc.terminate()
                        return
                    try:
                        copied_total = sum(
                            len(files)
                            for _, _, files in os.walk(backup_folder))
                        pct = min(copied_total / total_files * 100, 99)
                        self._progress_update(progress,
                                              value=pct,
                                              detail=f"Copied {copied_total}/{total_files}")
                    except Exception:
                        pass
                    time.sleep(0.8)

            size_str = self.format_size(self.get_folder_size(backup_folder))
            self.backup_history.append({
                'date': datetime.now().strftime("%Y-%m-%d %H:%M"),
                'type': media_type.capitalize(),
                'size': size_str,
                'location': backup_folder,
            })
            self.ui(self.update_history_view)

            self._progress_update(progress, text="Backup completed successfully!",
                                  detail=f"Final size: {size_str}", value=100,
                                  detail_color='green', done=True)

            if self.notification_var.get():
                self.ui(messagebox.showinfo, "Backup Complete",
                        f"{media_type.capitalize()} backup completed successfully!")
        except Exception as e:
            self._progress_update(progress, text=f"Error: {e}",
                                  detail_color='red', done=True)

    # ---------------- preview ----------------
    def preview_files(self):
        if not self.check_device_connection():
            messagebox.showerror("Error", "No Pixel device connected")
            return

        preview_window = tk.Toplevel(self.root)
        preview_window.title(f"Preview {self.media_type.get()} Files")
        preview_window.geometry("640x420")
        preview_window.transient(self.root)

        columns = ("name", "size", "date")
        tree = ttk.Treeview(preview_window, columns=columns, show="headings")
        for col, w in [("name", 300), ("size", 100), ("date", 180)]:
            tree.heading(col, text=col.capitalize())
            tree.column(col, width=w)
        scrollbar = ttk.Scrollbar(preview_window, orient=tk.VERTICAL,
                                  command=tree.yview)
        tree.configure(yscroll=scrollbar.set)
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        status = ttk.Label(preview_window, text="Loading file list…")
        status.pack(fill=tk.X)

        threading.Thread(target=self._load_file_preview,
                         args=(tree, status, self.media_type.get()),
                         daemon=True).start()

    def _load_file_preview(self, tree, status_label, media_type):
        try:
            paths = []
            if media_type == "photos":
                paths.append("/sdcard/DCIM/Camera")
                if not self.screenshots_var.get():
                    paths.append("/sdcard/Pictures/Screenshots")
            elif media_type == "videos":
                paths.extend(["/sdcard/Movies", "/sdcard/DCIM/Camera"])
            elif media_type == "documents":
                paths.extend(["/sdcard/Documents", "/sdcard/Download"])
            else:
                if self.photos_var.get():
                    paths.append("/sdcard/DCIM/Camera")
                if self.videos_var.get():
                    paths.append("/sdcard/Movies")
                if self.documents_var.get():
                    paths.append("/sdcard/Documents")
                if self.music_var.get():
                    paths.append("/sdcard/Music")
                if self.downloads_var.get():
                    paths.append("/sdcard/Download")
                if self.other_media_var.get():
                    paths.append("/sdcard/Pictures")

            try:
                from_date = datetime.strptime(self.date_from.get(), "%m/%d/%Y")
                to_date = datetime.strptime(self.date_to.get(), "%m/%d/%Y")
            except ValueError:
                from_date = to_date = None

            found = 0
            for path in paths:
                self.ui(status_label.config, text=f"Searching {path}…")
                find_cmd = ['find', path, '-type', 'f']
                if self.large_files_var.get():
                    find_cmd.extend(['-size', '+5M'])
                if self.raw_images_var.get() and "DCIM" in path:
                    find_cmd.extend(['-name', '*.dng'])
                if self.uhd_videos_var.get() and ("Movies" in path or "DCIM" in path):
                    find_cmd.extend(['-name', '*4k*'])

                r = subprocess.run([self.adb_path, 'shell'] + find_cmd,
                                   capture_output=True, text=True, timeout=120)
                if r.returncode != 0:
                    continue

                for f in r.stdout.splitlines():
                    stat = subprocess.run(
                        [self.adb_path, 'shell', 'stat', '-c', '%s %y', f],
                        capture_output=True, text=True, timeout=10)
                    if stat.returncode != 0:
                        continue
                    try:
                        size, date = stat.stdout.strip().split(' ', 1)
                        if from_date and to_date:
                            file_date = datetime.strptime(date.split('.')[0],
                                                          "%Y-%m-%d %H:%M:%S")
                            if not (from_date <= file_date <= to_date):
                                continue
                        self.ui(tree.insert, "", tk.END,
                                values=(os.path.basename(f),
                                        self.format_size(int(size)), date))
                        found += 1
                        if found % 10 == 0:
                            self.ui(status_label.config,
                                    text=f"Found {found} files…")
                    except Exception:
                        continue

            self.ui(status_label.config, text=f"Found {found} matching files")
        except Exception as e:
            self.ui(status_label.config, text=f"Error: {e}", foreground='red')

    # ---------------- settings persistence ----------------
    def _collect_settings(self):
        return {
            "verify_backup": self.verify_backup_var.get(),
            "compress_backup": self.compress_backup_var.get(),
            "compression_level": self.compression_level.get(),
            "sound": self.sound_var.get(),
            "notification": self.notification_var.get(),
            "default_connection": self.default_connection.get(),
            "auto_detect": self.auto_detect_var.get(),
            "backup_location": self.backup_location.get(),
            "media_backup_location": self.media_backup_location.get(),
        }

    def load_settings(self):
        if not os.path.isfile(CONFIG_FILE):
            return
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as fh:
                data = json.load(fh)
            self.verify_backup_var.set(data.get("verify_backup", True))
            self.compress_backup_var.set(data.get("compress_backup", True))
            self.compression_level.set(data.get("compression_level", "balanced"))
            self.sound_var.set(data.get("sound", True))
            self.notification_var.set(data.get("notification", True))
            self.default_connection.set(data.get("default_connection", "usb"))
            self.auto_detect_var.set(data.get("auto_detect", True))
            self.backup_location.set(
                data.get("backup_location", self.backup_location.get()))
            self.media_backup_location.set(
                data.get("media_backup_location", self.media_backup_location.get()))
        except Exception as e:
            print(f"Failed to load settings: {e}")

    def save_settings(self):
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as fh:
                json.dump(self._collect_settings(), fh, indent=2)
            messagebox.showinfo("Settings Saved",
                                "Your settings have been saved successfully")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save settings: {e}")

    def restore_defaults(self):
        self.verify_backup_var.set(True)
        self.compress_backup_var.set(True)
        self.compression_level.set("balanced")
        self.sound_var.set(True)
        self.notification_var.set(True)
        self.default_connection.set("usb")
        self.auto_detect_var.set(True)
        messagebox.showinfo("Defaults Restored",
                            "All settings have been restored to defaults")

    # ---------------- about ----------------
    def show_about(self):
        about_text = (
            "Google Pixel Backup Toolkit\nVersion 1.1\n\n"
            "A comprehensive tool to backup your Google Pixel phone data\n"
            "with customizable options for different media types.\n\n"
            "Features:\n"
            "- Full system backups\n"
            "- Selective media backups\n"
            "- Advanced filters and options\n"
            "- Backup history tracking\n\n"
            "© 2025 Pixel Backup Toolkit"
        )
        messagebox.showinfo("About", about_text)


if __name__ == "__main__":
    root = tk.Tk()
    app = PixelBackupToolkit(root)
    root.mainloop()