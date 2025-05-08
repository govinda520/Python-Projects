import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import json
from datetime import datetime
import psutil
import threading
import time
import win32gui
import win32process
import win32api
import win32con
import win32com.client
import pythoncom
from PIL import Image, ImageTk
import customtkinter as ctk

class EditTaskDialog:
    def __init__(self, parent, task):
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Edit Task")
        self.dialog.geometry("500x250")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        self.dialog.configure(bg="#f0f0f0")
        
        self.result = None
        self.task = task
        
        # Create main frame
        main_frame = ttk.Frame(self.dialog, padding="20", style="Card.TFrame")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Title
        title_label = ttk.Label(main_frame, text="Edit Task", style="Title.TLabel")
        title_label.pack(pady=(0, 20))
        
        # Task description
        ttk.Label(main_frame, text="Task Description:", style="Subtitle.TLabel").pack(anchor=tk.W, pady=(0, 5))
        self.task_entry = ttk.Entry(main_frame, width=50, style="Custom.TEntry")
        self.task_entry.insert(0, task["description"])
        self.task_entry.pack(fill=tk.X, pady=(0, 15))
        
        # Source folder
        ttk.Label(main_frame, text="Source Folder:", style="Subtitle.TLabel").pack(anchor=tk.W, pady=(0, 5))
        folder_frame = ttk.Frame(main_frame, style="Card.TFrame")
        folder_frame.pack(fill=tk.X, pady=(0, 20))
        
        self.folder_entry = ttk.Entry(folder_frame, width=40, style="Custom.TEntry")
        self.folder_entry.insert(0, task["source_folder"])
        self.folder_entry.pack(side=tk.LEFT, padx=(0, 10), fill=tk.X, expand=True)
        
        browse_button = ttk.Button(folder_frame, text="Browse", command=self.browse_folder, style="Action.TButton")
        browse_button.pack(side=tk.RIGHT)
        
        # Buttons
        button_frame = ttk.Frame(main_frame, style="Card.TFrame")
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        save_button = ttk.Button(button_frame, text="Save Changes", command=self.save, style="Primary.TButton")
        save_button.pack(side=tk.RIGHT, padx=(5, 0))
        
        cancel_button = ttk.Button(button_frame, text="Cancel", command=self.dialog.destroy, style="Secondary.TButton")
        cancel_button.pack(side=tk.RIGHT)
        
        # Center the dialog
        self.dialog.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - self.dialog.winfo_width()) // 2
        y = parent.winfo_y() + (parent.winfo_height() - self.dialog.winfo_height()) // 2
        self.dialog.geometry(f"+{x}+{y}")
        
    def browse_folder(self):
        folder_path = filedialog.askdirectory()
        if folder_path:
            self.folder_entry.delete(0, tk.END)
            self.folder_entry.insert(0, folder_path)
    
    def save(self):
        description = self.task_entry.get().strip()
        source_folder = self.folder_entry.get().strip()
        
        if not description:
            messagebox.showerror("Error", "Please enter a task description", parent=self.dialog)
            return
        
        if not source_folder:
            messagebox.showerror("Error", "Please select a source folder", parent=self.dialog)
            return
        
        if not os.path.exists(source_folder):
            messagebox.showerror("Error", "Selected folder does not exist", parent=self.dialog)
            return
        
        self.result = {
            "description": description,
            "source_folder": source_folder,
            "created_at": self.task["created_at"],
            "completed": self.task.get("completed", False)
        }
        self.dialog.destroy()

class FolderMonitor:
    def __init__(self, task_manager):
        self.task_manager = task_manager
        self.running = False
        self.monitor_thread = None
        self.last_window = None
        self.last_alert_time = 0
        self.alert_cooldown = 30  # seconds between alerts
        self.last_path = None
        self.shell = None
        self.last_drive_check = 0
        self.drive_check_interval = 0.1  # Check drives every 0.1 seconds
        self.current_alert_window = None
        self.is_drive_alert_shown = False
        self.restricted_drives = ["C:", "D:", "E:"]  # List of restricted drives
        self.last_alert_path = None
        self.last_alert_time = 0
        self.alert_debounce = 5  # seconds between alerts for the same path
        self.debug_print_interval = 5  # seconds between debug prints
        self.last_debug_print = 0
        self._monitoring = False  # Flag to prevent multiple monitoring threads
        self._alert_showing = False  # Flag to track if alert is currently showing
        
        # List of allowed applications (process names)
        self.allowed_apps = [
            "code.exe",           # VS Code
            "WINWORD.EXE",        # Microsoft Word
            "EXCEL.EXE",          # Microsoft Excel
            "POWERPNT.EXE",       # Microsoft PowerPoint
            "msedge.exe",         # Microsoft Edge
            "chrome.exe",         # Google Chrome
            "firefox.exe",        # Firefox
            "notepad.exe",        # Notepad
            "notepad++.exe"       # Notepad++
        ]

    def start(self):
        if not self._monitoring:
            print("[FolderMonitor] Starting folder monitoring thread...")
            self.running = True
            self._monitoring = True
            self.monitor_thread = threading.Thread(target=self._monitor_folders)
            self.monitor_thread.daemon = True
            self.monitor_thread.start()

    def stop(self):
        print("[FolderMonitor] Stopping folder monitoring thread...")
        self.running = False
        self._monitoring = False
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=1.0)
            self.monitor_thread = None

    def _get_current_folder(self):
        try:
            # Initialize COM for this thread
            pythoncom.CoInitialize()
            
            # Get the active window
            current_window = win32gui.GetForegroundWindow()
            window_title = win32gui.GetWindowText(current_window)
            
            # Fast check for drive access in window title
            for drive in self.restricted_drives:
                if drive in window_title or drive.lower() in window_title:
                    return window_title
            
            # Try to get the current folder from Explorer
            if "File Explorer" in window_title or "This PC" in window_title:
                try:
                    if not self.shell:
                        self.shell = win32com.client.Dispatch("Shell.Application")
                    
                    # Get the active window
                    windows = self.shell.Windows()
                    for window in windows:
                        if window.HWND == current_window:
                            try:
                                path = window.Document.Folder.Self.Path
                                return path
                            except:
                                pass
                except:
                    pass
            
            # Fallback to process-based detection
            _, process_id = win32process.GetWindowThreadProcessId(current_window)
            try:
                process = psutil.Process(process_id)
                path = process.cwd()
                return path
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                return None
        except Exception as e:
            print(f"Error getting current folder: {e}")
            return None
        finally:
            pythoncom.CoUninitialize()

    def _is_path_allowed(self, current_path):
        # Get all active tasks' source folders
        active_tasks = [t for t in self.task_manager.tasks if not t.get("completed", False)]
        allowed_folders = [t["source_folder"] for t in active_tasks]
        
        # If no active tasks, all folders are allowed
        if not allowed_folders:
            return True
        
        # Normalize current_path
        try:
            current_path_norm = os.path.abspath(os.path.normcase(current_path))
        except Exception:
            current_path_norm = current_path
        
        # Check if current path is inside any allowed folder (including subfolders)
        for folder in allowed_folders:
            try:
                folder_norm = os.path.abspath(os.path.normcase(folder))
                if os.path.commonpath([current_path_norm, folder_norm]) == folder_norm:
                    return True
            except Exception:
                continue
        
        # Check if path is in any restricted drive
        if current_path:
            for drive in self.restricted_drives:
                if (current_path.startswith(drive) or 
                    current_path.startswith(drive.lower()) or 
                    drive in current_path or 
                    drive.lower() in current_path):
                    return False
        return True

    def _get_current_process(self):
        try:
            # Get the active window
            current_window = win32gui.GetForegroundWindow()
            _, process_id = win32process.GetWindowThreadProcessId(current_window)
            process = psutil.Process(process_id)
            return process.name().lower()
        except:
            return None

    def _is_allowed_application(self):
        current_process = self._get_current_process()
        if current_process:
            return current_process in [app.lower() for app in self.allowed_apps]
        return False

    def _monitor_folders(self):
        print("[FolderMonitor] Monitor thread running.")
        while self.running:
            try:
                # If an alert is showing, pause monitoring
                if self._alert_showing:
                    time.sleep(0.5)  # Sleep longer when alert is showing
                    continue

                current_time = time.time()
                if current_time - self.last_drive_check >= self.drive_check_interval:
                    self.last_drive_check = current_time
                    current_path = self._get_current_folder()
                    
                    if current_time - self.last_debug_print >= self.debug_print_interval:
                        print(f"[FolderMonitor] Current path: {current_path}")
                        self.last_debug_print = current_time
                    
                    if current_path and current_path != self.last_path:
                        self.last_path = current_path
                        # Check if current application is allowed
                        if not self._is_allowed_application():
                            if not self._is_path_allowed(current_path):
                                is_restricted_drive = any(
                                    drive in current_path or drive.lower() in current_path 
                                    for drive in self.restricted_drives
                                )
                                if is_restricted_drive:
                                    if (self.last_alert_path != current_path or
                                        current_time - self.last_alert_time > self.alert_debounce):
                                        if not self._alert_showing:
                                            self._show_alert(current_path)
                                            self.last_alert_path = current_path
                                            self.last_alert_time = current_time
                                else:
                                    if current_time - self.last_alert_time > self.alert_cooldown:
                                        self.last_alert_time = current_time
                                        if not self._alert_showing:
                                            self._show_alert(current_path)
            except Exception as e:
                print(f"[FolderMonitor] Monitoring error: {e}")
            time.sleep(0.05)

    def _show_alert(self, current_path):
        if self._alert_showing:
            return

        self._alert_showing = True
        alert_window = tk.Toplevel(self.task_manager.root)
        self.current_alert_window = alert_window
        alert_window.title("Task Alert")
        alert_window.geometry("540x400")
        alert_window.resizable(False, False)
        alert_window.attributes('-topmost', True)
        alert_window.configure(bg="#23272e")
        
        # Remove default window decorations
        alert_window.overrideredirect(True)
        
        # Create outer frame for rounded corners
        outer_frame = ctk.CTkFrame(alert_window, corner_radius=15, fg_color="#1a1d21")
        outer_frame.pack(fill="both", expand=True, padx=2, pady=2)
        
        # Create custom title bar
        title_bar = ctk.CTkFrame(outer_frame, height=30, corner_radius=0, fg_color="#1a1d21")
        title_bar.pack(fill="x", side="top")
        
        # Title label
        title_label = ctk.CTkLabel(title_bar, text="Task Alert", font=("Segoe UI", 12, "bold"), text_color="#ffffff")
        title_label.pack(side="left", padx=10)
        
        # Window control buttons
        close_btn = ctk.CTkButton(title_bar, text="×", width=30, height=30, corner_radius=0,
                                 fg_color="transparent", hover_color="#e81123",
                                 command=lambda: self._close_alert(alert_window))
        close_btn.pack(side="right", padx=0)
        
        # Main content frame with rounded corners
        frame = ctk.CTkFrame(outer_frame, corner_radius=10, fg_color="#23272e")
        frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        # Check if it's restricted drive access
        is_restricted_drive = any(
            drive in current_path or drive.lower() in current_path 
            for drive in self.restricted_drives
        )

        if is_restricted_drive:
            drive_letter = next(
                (drive for drive in self.restricted_drives 
                 if drive in current_path or drive.lower() in current_path),
                "restricted drive"
            )
            ctk.CTkLabel(frame, text="⚠️", font=("Segoe UI", 32), text_color="#fff").pack(pady=(0, 2))
            ctk.CTkLabel(frame, text="Task Pending", font=("Segoe UI", 16, "bold"), text_color="#0d47a1").pack(pady=(0, 6))
            ctk.CTkLabel(frame, text=f"Complete your tasks before accessing {drive_letter} drive.", 
                        font=("Segoe UI", 12), wraplength=280, text_color="#fff").pack(pady=(0, 10))
            active_tasks = [t for t in self.task_manager.tasks if not t.get("completed", False)]
            if active_tasks:
                ctk.CTkLabel(frame, text="Pending tasks:", font=("Segoe UI", 11, "bold"), 
                            text_color="#0d47a1").pack(pady=(0, 2))
                for task in active_tasks:
                    task_text = f"• {task['description']}"
                    ctk.CTkLabel(frame, text=task_text, font=("Segoe UI", 11), wraplength=260, 
                                text_color="#fff").pack(anchor="w", padx=8)
        else:
            ctk.CTkLabel(frame, text="⚠️", font=("Segoe UI", 32), text_color="#fff").pack(pady=(0, 2))
            ctk.CTkLabel(frame, text="Task Alert", font=("Segoe UI", 16, "bold"), 
                        text_color="#b71c1c").pack(pady=(0, 6))
            ctk.CTkLabel(frame, text="Unauthorized folder:", font=("Segoe UI", 12), 
                        text_color="#fff").pack(pady=(0, 2))
            ctk.CTkLabel(frame, text=current_path, font=("Segoe UI", 11), wraplength=260, 
                        text_color="#fff").pack(pady=(0, 10))

        # Button frame
        button_frame = ctk.CTkFrame(frame, fg_color="transparent")
        button_frame.pack(fill="x", pady=(30, 0))

        # Center the buttons
        inner_button_frame = ctk.CTkFrame(button_frame, fg_color="transparent")
        inner_button_frame.pack(anchor="center")

        # Go to Source Folder button
        goto_button = ctk.CTkButton(
            inner_button_frame, 
            text="Go to Source Folder", 
            command=lambda: self._goto_source_and_close(alert_window), 
            fg_color="#388e3c",
            hover_color="#1b5e20", 
            text_color="#fff", 
            width=120,
            height=32,
            corner_radius=8,
            font=("Segoe UI", 11, "bold")
        )
        goto_button.pack(side="left", padx=(0, 10), pady=(0, 6))

        # Cancel button
        cancel_button = ctk.CTkButton(
            inner_button_frame, 
            text="Cancel", 
            command=lambda: self._close_alert(alert_window), 
            fg_color="#b71c1c",
            hover_color="#7f0000", 
            text_color="#fff", 
            width=100,
            height=32,
            corner_radius=8,
            font=("Segoe UI", 11, "bold")
        )
        cancel_button.pack(side="left", pady=(0, 6))

        # Make the window draggable
        def start_move(event):
            alert_window.x = event.x
            alert_window.y = event.y

        def do_move(event):
            deltax = event.x - alert_window.x
            deltay = event.y - alert_window.y
            x = alert_window.winfo_x() + deltax
            y = alert_window.winfo_y() + deltay
            alert_window.geometry(f"+{x}+{y}")

        # Bind mouse events to the title bar for dragging
        title_bar.bind("<Button-1>", start_move)
        title_bar.bind("<B1-Motion>", do_move)
        title_label.bind("<Button-1>", start_move)
        title_label.bind("<B1-Motion>", do_move)

        # Center the window
        x = self.task_manager.root.winfo_x() + (self.task_manager.root.winfo_width() - 540) // 2
        y = self.task_manager.root.winfo_y() + (self.task_manager.root.winfo_height() - 400) // 2
        alert_window.geometry(f"+{x}+{y}")

    def _close_alert(self, alert_window):
        self.current_alert_window = None
        self._alert_showing = False
        alert_window.destroy()
        self.last_alert_time = time.time()

    def _goto_source_and_close(self, alert_window):
        active_tasks = [t for t in self.task_manager.tasks if not t.get("completed", False)]
        if active_tasks:
            folder = active_tasks[0]["source_folder"]
            try:
                os.startfile(folder)
            except Exception as e:
                messagebox.showerror("Error", f"Could not open folder: {e}")
        else:
            messagebox.showinfo("Info", "No active task source folder found.")
        self._close_alert(alert_window)

class InfoDialog:
    def __init__(self, parent):
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("About StayFocused")
        self.dialog.geometry("400x500")
        self.dialog.resizable(False, False)
        self.dialog.configure(bg="#23272e")
        
        # Remove default window decorations
        self.dialog.overrideredirect(True)
        
        # Create outer frame for rounded corners
        outer_frame = ctk.CTkFrame(self.dialog, corner_radius=15, fg_color="#1a1d21")
        outer_frame.pack(fill="both", expand=True, padx=2, pady=2)
        
        # Create custom title bar
        title_bar = ctk.CTkFrame(outer_frame, height=30, corner_radius=0, fg_color="#1a1d21")
        title_bar.pack(fill="x", side="top")
        
        # Title label
        title_label = ctk.CTkLabel(title_bar, text="About StayFocused", font=("Segoe UI", 12, "bold"), text_color="#ffffff")
        title_label.pack(side="left", padx=10)
        
        # Close button
        close_btn = ctk.CTkButton(title_bar, text="×", width=30, height=30, corner_radius=0,
                                 fg_color="transparent", hover_color="#e81123",
                                 command=self.dialog.destroy)
        close_btn.pack(side="right", padx=0)
        
        # Main content frame
        content_frame = ctk.CTkFrame(outer_frame, corner_radius=10, fg_color="#23272e")
        content_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        # App logo/icon
        ctk.CTkLabel(content_frame, text="📋", font=("Segoe UI", 48), text_color="#fff").pack(pady=(20, 0))
        
        # App name
        ctk.CTkLabel(content_frame, text="StayFocused", font=("Segoe UI", 24, "bold"), 
                    text_color="#0d47a1").pack(pady=(10, 0))
        
        # Version
        ctk.CTkLabel(content_frame, text="Version 1.0.0", font=("Segoe UI", 12), 
                    text_color="#fff").pack(pady=(5, 20))
        
        # Developer info
        dev_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        dev_frame.pack(fill="x", padx=20, pady=(0, 20))
        
        ctk.CTkLabel(dev_frame, text="Developed by:", font=("Segoe UI", 14, "bold"), 
                    text_color="#0d47a1").pack(anchor="w")
        ctk.CTkLabel(dev_frame, text="Govinda Tudu", font=("Segoe UI", 12), 
                    text_color="#fff").pack(anchor="w", padx=(10, 0))
        
        # GitHub info
        github_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        github_frame.pack(fill="x", padx=20, pady=(0, 20))
        
        ctk.CTkLabel(github_frame, text="GitHub:", font=("Segoe UI", 14, "bold"), 
                    text_color="#0d47a1").pack(anchor="w")
        ctk.CTkLabel(github_frame, text="github.com/govinda520", font=("Segoe UI", 12), 
                    text_color="#fff").pack(anchor="w", padx=(10, 0))
        
        # Technology stack
        tech_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        tech_frame.pack(fill="x", padx=20, pady=(0, 20))
        
        ctk.CTkLabel(tech_frame, text="Built with:", font=("Segoe UI", 14, "bold"), 
                    text_color="#0d47a1").pack(anchor="w")
        
        tech_list = [
            "• Python 3.x",
            "• Tkinter",
            "• CustomTkinter",
            "• PyWin32",
            "• Psutil"
        ]
        
        for tech in tech_list:
            ctk.CTkLabel(tech_frame, text=tech, font=("Segoe UI", 12), 
                        text_color="#fff").pack(anchor="w", padx=(10, 0))
        
        # Description
        desc_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        desc_frame.pack(fill="x", padx=20, pady=(0, 20))
        
        ctk.CTkLabel(desc_frame, text="Description:", font=("Segoe UI", 14, "bold"), 
                    text_color="#0d47a1").pack(anchor="w")
        ctk.CTkLabel(desc_frame, 
                    text="StayFocused is a task management application that helps you stay focused on your work by monitoring and restricting access to unauthorized folders.",
                    font=("Segoe UI", 12), text_color="#fff", wraplength=340).pack(anchor="w", padx=(10, 0))
        
        # Make window draggable
        def start_move(event):
            self.dialog.x = event.x
            self.dialog.y = event.y

        def do_move(event):
            deltax = event.x - self.dialog.x
            deltay = event.y - self.dialog.y
            x = self.dialog.winfo_x() + deltax
            y = self.dialog.winfo_y() + deltay
            self.dialog.geometry(f"+{x}+{y}")

        # Bind mouse events to the title bar for dragging
        title_bar.bind("<Button-1>", start_move)
        title_bar.bind("<B1-Motion>", do_move)
        title_label.bind("<Button-1>", start_move)
        title_label.bind("<B1-Motion>", do_move)
        
        # Center the window
        self.dialog.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - self.dialog.winfo_width()) // 2
        y = parent.winfo_y() + (parent.winfo_height() - self.dialog.winfo_height()) // 2
        self.dialog.geometry(f"+{x}+{y}")

class TaskManager:
    def __init__(self, root):
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")
        self.root = root
        self.root.title("Task Manager")
        self.root.geometry("400x500")
        self.root.configure(bg="#23272e")
        
        # Store initial window position and size
        self.initial_geometry = "400x500"
        self.initial_position = None
        
        # Remove default window decorations
        self.root.overrideredirect(True)
        
        # Create outer frame for rounded corners
        self.outer_frame = ctk.CTkFrame(self.root, corner_radius=15, fg_color="#1a1d21")
        self.outer_frame.pack(fill="both", expand=True, padx=2, pady=2)
        
        # Create custom title bar
        self.title_bar = ctk.CTkFrame(self.outer_frame, height=30, corner_radius=0, fg_color="#1a1d21")
        self.title_bar.pack(fill="x", side="top")
        
        # Title label
        self.title_label = ctk.CTkLabel(self.title_bar, text="Task Manager", font=("Segoe UI", 12, "bold"), text_color="#ffffff")
        self.title_label.pack(side="left", padx=10)
        
        # Info button
        self.info_btn = ctk.CTkButton(self.title_bar, text="ⓘ", width=30, height=30, corner_radius=0,
                                     fg_color="transparent", hover_color="#2d3136",
                                     command=self.show_info)
        self.info_btn.pack(side="right", padx=0)
        
        # Window control button (close only)
        self.close_btn = ctk.CTkButton(self.title_bar, text="×", width=30, height=30, corner_radius=0,
                                      fg_color="transparent", hover_color="#e81123",
                                      command=self.on_closing)
        self.close_btn.pack(side="right", padx=0)
        
        # Make window draggable
        self.title_bar.bind("<Button-1>", self.start_move)
        self.title_bar.bind("<B1-Motion>", self.do_move)
        self.title_label.bind("<Button-1>", self.start_move)
        self.title_label.bind("<B1-Motion>", self.do_move)
        
        # Initialize folder monitor
        self.folder_monitor = FolderMonitor(self)
        self.monitor_started = False
        
        # Main frame with rounded corners
        self.main_frame = ctk.CTkFrame(self.outer_frame, corner_radius=10, fg_color="#23272e")
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        # Create tabview
        self.tabview = ctk.CTkTabview(self.main_frame, fg_color="#23272e")
        self.tabview.pack(fill="both", expand=True)
        
        # Add tabs
        self.tabview.add("Tasks")
        self.tabview.add("Overview")
        
        # Tasks Tab Content
        tasks_frame = self.tabview.tab("Tasks")
        
        # Title
        title_frame = ctk.CTkFrame(tasks_frame, fg_color="#23272e")
        title_frame.pack(fill="x", pady=(0, 8))
        ctk.CTkLabel(title_frame, text="📋 Task Manager", font=("Segoe UI", 20, "bold"), text_color="#fff").pack(side="left")
        
        # Input Card
        input_card = ctk.CTkFrame(tasks_frame, corner_radius=8, fg_color="#23272e")
        input_card.pack(fill="x", pady=(0, 8))
        ctk.CTkLabel(input_card, text="✏️ Task:", font=("Segoe UI", 13, "bold"), text_color="#fff").pack(anchor="w", pady=(4, 0))
        self.task_entry = ctk.CTkEntry(input_card, width=220, fg_color="#23272e", text_color="#fff")
        self.task_entry.pack(fill="x", pady=(0, 6))
        ctk.CTkLabel(input_card, text="📁 Folder:", font=("Segoe UI", 13, "bold"), text_color="#fff").pack(anchor="w", pady=(4, 0))
        folder_frame = ctk.CTkFrame(input_card, fg_color="#23272e")
        folder_frame.pack(fill="x", pady=(0, 6))
        self.folder_entry = ctk.CTkEntry(folder_frame, width=160, fg_color="#23272e", text_color="#fff")
        self.folder_entry.pack(side="left", fill="x", expand=True, padx=(0, 6))
        self.browse_button = ctk.CTkButton(folder_frame, text="Browse", command=self.browse_folder, width=60)
        self.browse_button.pack(side="right")
        self.create_button = ctk.CTkButton(input_card, text="➕ Create", command=self.create_task)
        self.create_button.pack(pady=(4, 0))
        
        # Active Tasks Card
        active_card = ctk.CTkFrame(tasks_frame, corner_radius=8, fg_color="#23272e")
        active_card.pack(fill="both", expand=True, pady=(0, 8))
        header_frame = ctk.CTkFrame(active_card, fg_color="#23272e")
        header_frame.pack(fill="x", pady=(0, 4))
        ctk.CTkLabel(header_frame, text="📌 Active", font=("Segoe UI", 13, "bold"), text_color="#fff").pack(side="left")
        self.edit_button = ctk.CTkButton(header_frame, text="✏️ Edit", command=self.edit_task, width=60)
        self.edit_button.pack(side="right")
        self.task_listbox = tk.Listbox(active_card, width=40, height=4, font=("Segoe UI", 11),
                                       bg="#23272e", fg="#fff", selectbackground="#0d47a1", selectforeground="#fff",
                                       borderwidth=0, highlightthickness=0, relief="flat")
        self.task_listbox.pack(fill="both", expand=True, pady=(0, 4))
        self.task_listbox.bind('<Double-Button-1>', self.toggle_task_completion)
        
        # Completed Tasks Card
        completed_card = ctk.CTkFrame(tasks_frame, corner_radius=8, fg_color="#23272e")
        completed_card.pack(fill="both", expand=True)
        completed_header = ctk.CTkFrame(completed_card, fg_color="#23272e")
        completed_header.pack(fill="x", pady=(0, 4))
        ctk.CTkLabel(completed_header, text="✅ Completed", font=("Segoe UI", 13, "bold"), text_color="#fff").pack(side="left")
        self.delete_completed_button = ctk.CTkButton(completed_header, text="🗑️ Delete", command=self.delete_completed_task, width=60)
        self.delete_completed_button.pack(side="right")
        self.completed_listbox = tk.Listbox(completed_card, width=40, height=4, font=("Segoe UI", 11),
                                            bg="#23272e", fg="#fff", selectbackground="#0d47a1", selectforeground="#fff",
                                            borderwidth=0, highlightthickness=0, relief="flat")
        self.completed_listbox.pack(fill="both", expand=True, pady=(0, 4))
        
        # Overview Tab Content
        overview_frame = self.tabview.tab("Overview")
        
        # Title
        ctk.CTkLabel(overview_frame, text="📋 StayFocused Overview", font=("Segoe UI", 20, "bold"), 
                    text_color="#fff").pack(pady=(0, 20))
        
        # Features
        features = [
            ("🎯 Task Management", "Create and manage tasks with specific source folders"),
            ("🔒 Folder Monitoring", "StayFocused monitors your file system access"),
            ("⚠️ Smart Alerts", "Get notified when accessing unauthorized folders"),
            ("✅ Task Completion", "Mark tasks as complete when finished"),
            ("📊 Progress Tracking", "Keep track of active and completed tasks"),
            ("⚡ Performance", "Lightweight and efficient background monitoring"),
            ("🔐 Security", "Restrict access to unauthorized folders"),
            ("🎨 Modern UI", "Clean and intuitive user interface")
        ]
        
        for title, desc in features:
            feature_frame = ctk.CTkFrame(overview_frame, fg_color="#23272e")
            feature_frame.pack(fill="x", pady=(0, 10))
            
            ctk.CTkLabel(feature_frame, text=title, font=("Segoe UI", 14, "bold"), 
                        text_color="#0d47a1").pack(anchor="w")
            ctk.CTkLabel(feature_frame, text=desc, font=("Segoe UI", 12), 
                        text_color="#fff", wraplength=340).pack(anchor="w", padx=(10, 0))
        
        # Load existing tasks
        self.tasks = []
        self.load_tasks()
        
        # Handle window close
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def on_closing(self):
        self.folder_monitor.stop()
        self.root.destroy()

    def browse_folder(self):
        folder_path = filedialog.askdirectory()
        if folder_path:
            self.folder_entry.delete(0, tk.END)
            self.folder_entry.insert(0, folder_path)
    
    def create_task(self):
        task_description = self.task_entry.get().strip()
        source_folder = self.folder_entry.get().strip()
        
        if not task_description:
            messagebox.showerror("Error", "Please enter a task description")
            return
        
        if not source_folder:
            messagebox.showerror("Error", "Please select a source folder")
            return
        
        if not os.path.exists(source_folder):
            messagebox.showerror("Error", "Selected folder does not exist")
            return
        
        task = {
            "description": task_description,
            "source_folder": source_folder,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "completed": False
        }
        
        self.tasks.append(task)
        self.save_tasks()
        self.update_task_lists()
        
        # Clear inputs
        self.task_entry.delete(0, tk.END)
        self.folder_entry.delete(0, tk.END)
        
        messagebox.showinfo("Success", "Task created successfully!")
        # Start folder monitoring after first task is created
        if not self.monitor_started:
            self.folder_monitor.start()
            self.monitor_started = True
    
    def edit_task(self):
        selection = self.task_listbox.curselection()
        if not selection:
            messagebox.showerror("Error", "Please select a task to edit")
            return
        
        index = selection[0]
        task = [t for t in self.tasks if not t.get("completed", False)][index]
        
        dialog = EditTaskDialog(self.root, task)
        self.root.wait_window(dialog.dialog)
        
        if dialog.result:
            self.tasks[self.tasks.index(task)] = dialog.result
            self.save_tasks()
            self.update_task_lists()
            messagebox.showinfo("Success", "Task updated successfully!")
    
    def delete_completed_task(self):
        selection = self.completed_listbox.curselection()
        if not selection:
            messagebox.showerror("Error", "Please select a task to delete")
            return
        
        if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this task?"):
            index = selection[0]
            completed_tasks = [t for t in self.tasks if t.get("completed", False)]
            task_to_delete = completed_tasks[index]
            self.tasks.remove(task_to_delete)
            self.save_tasks()
            self.update_task_lists()
            messagebox.showinfo("Success", "Task deleted successfully!")
    
    def toggle_task_completion(self, event):
        selection = self.task_listbox.curselection()
        if not selection:
            return
        
        index = selection[0]
        active_tasks = [t for t in self.tasks if not t.get("completed", False)]
        task = active_tasks[index]
        task["completed"] = True
        self.save_tasks()
        self.update_task_lists()
    
    def save_tasks(self):
        with open("tasks.json", "w") as f:
            json.dump(self.tasks, f, indent=4)
    
    def load_tasks(self):
        try:
            with open("tasks.json", "r") as f:
                self.tasks = json.load(f)
                self.update_task_lists()
        except FileNotFoundError:
            self.tasks = []
    
    def update_task_lists(self):
        # Update active tasks list
        self.task_listbox.delete(0, tk.END)
        active_tasks = [t for t in self.tasks if not t.get("completed", False)]
        for task in active_tasks:
            display_text = f"{task['description']} - {task['source_folder']} ({task['created_at']})"
            self.task_listbox.insert(tk.END, display_text)
        
        # Update completed tasks list
        self.completed_listbox.delete(0, tk.END)
        completed_tasks = [t for t in self.tasks if t.get("completed", False)]
        for task in completed_tasks:
            display_text = f"{task['description']} - {task['source_folder']} ({task['created_at']})"
            self.completed_listbox.insert(tk.END, display_text)

    def start_move(self, event):
        self.root.x = event.x
        self.root.y = event.y

    def do_move(self, event):
        deltax = event.x - self.root.x
        deltay = event.y - self.root.y
        x = self.root.winfo_x() + deltax
        y = self.root.winfo_y() + deltay
        self.root.geometry(f"+{x}+{y}")

    def show_info(self):
        InfoDialog(self.root)

if __name__ == "__main__":
    root = tk.Tk()
    app = TaskManager(root)
    root.mainloop() 