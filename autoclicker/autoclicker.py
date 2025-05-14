import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import pyautogui
import keyboard
import time
import threading
import json
from typing import List, Dict

class AutoClicker:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Advanced Auto Clicker")
        self.root.geometry("800x600")
        
        # Configure dark theme
        self.root.configure(bg='#2b2b2b')
        style = ttk.Style()
        style.theme_use('clam')  # Use clam theme as base
        
        # Configure colors
        style.configure('.',
            background='#2b2b2b',
            foreground='#ffffff',
            fieldbackground='#3c3f41',
            troughcolor='#3c3f41',
            selectbackground='#4b6eaf',
            selectforeground='#ffffff'
        )
        
        # Configure specific widget styles
        style.configure('TLabel', background='#2b2b2b', foreground='#ffffff')
        style.configure('TButton', background='#3c3f41', foreground='#ffffff')
        style.configure('TFrame', background='#2b2b2b')
        style.configure('TLabelframe', background='#2b2b2b', foreground='#ffffff')
        style.configure('TLabelframe.Label', background='#2b2b2b', foreground='#ffffff')
        style.configure('TEntry', fieldbackground='#3c3f41', foreground='#ffffff')
        style.configure('TCombobox', fieldbackground='#3c3f41', foreground='#ffffff', background='#3c3f41')
        style.configure('TSpinbox', fieldbackground='#3c3f41', foreground='#ffffff', background='#3c3f41')
        
        # Configure hover effects
        style.map('TButton',
            background=[('active', '#4b6eaf')],
            foreground=[('active', '#ffffff')]
        )
        
        self.locations: List[Dict] = []
        self.is_running = False
        self.current_thread = None
        self.current_position = None
        self.position_update_running = False
        self.current_tracking_index = None
        self.save_button = None
        
        self.setup_ui()
        
    def setup_ui(self):
        # Number of locations frame
        locations_frame = ttk.LabelFrame(self.root, text="Setup", padding=10)
        locations_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(locations_frame, text="Number of Locations:").pack(side="left")
        self.num_locations = ttk.Spinbox(locations_frame, from_=1, to=100, width=5)
        self.num_locations.pack(side="left", padx=5)
        ttk.Button(locations_frame, text="Set Locations", command=self.setup_locations).pack(side="left", padx=5)
        
        # Add save/load buttons
        ttk.Button(locations_frame, text="Save Locations", command=self.save_locations).pack(side="left", padx=5)
        ttk.Button(locations_frame, text="Load Locations", command=self.load_locations).pack(side="left", padx=5)
        
        # Locations list frame
        self.locations_frame = ttk.LabelFrame(self.root, text="Locations", padding=10)
        self.locations_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Control frame
        control_frame = ttk.Frame(self.root, padding=10)
        control_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(control_frame, text="Repeat Count (0 for infinite):").pack(side="left")
        self.repeat_count = ttk.Spinbox(control_frame, from_=0, to=999999, width=10)
        self.repeat_count.pack(side="left", padx=5)
        
        self.start_button = ttk.Button(control_frame, text="Start", command=self.start_clicking)
        self.start_button.pack(side="left", padx=5)
        
        self.stop_button = ttk.Button(control_frame, text="Stop", command=self.stop_clicking, state="disabled")
        self.stop_button.pack(side="left", padx=5)
        
        # Counter frame
        counter_frame = ttk.LabelFrame(self.root, text="Statistics", padding=10)
        counter_frame.pack(fill="x", padx=10, pady=5)
        
        self.iteration_label = ttk.Label(counter_frame, text="Current Iteration: 0")
        self.iteration_label.pack(side="left", padx=5)
        
        self.total_clicks_label = ttk.Label(counter_frame, text="Total Clicks: 0")
        self.total_clicks_label.pack(side="left", padx=5)
        
        # Status label
        self.status_label = ttk.Label(self.root, text="Ready")
        self.status_label.pack(pady=5)
        
    def setup_locations(self):
        try:
            num = int(self.num_locations.get())
            if num < 1:
                raise ValueError("Number of locations must be at least 1")
                
            # Clear existing locations
            for widget in self.locations_frame.winfo_children():
                widget.destroy()
            self.locations.clear()
            
            # Create location entries
            for i in range(num):
                location_frame = ttk.Frame(self.locations_frame)
                location_frame.pack(fill="x", pady=2)
                
                ttk.Label(location_frame, text=f"Location {i+1}:").pack(side="left")
                
                # Action selection
                action_var = tk.StringVar(value="left_click")
                action_combo = ttk.Combobox(location_frame, textvariable=action_var, 
                                          values=["left_click", "right_click", "up_arrow", "down_arrow", "enter"],
                                          width=15)
                action_combo.pack(side="left", padx=5)
                
                # Delay entry
                ttk.Label(location_frame, text="Delay (seconds):").pack(side="left")
                delay_var = tk.StringVar(value="1")
                delay_entry = ttk.Entry(location_frame, textvariable=delay_var, width=5)
                delay_entry.pack(side="left", padx=5)
                
                # Position display
                position_label = ttk.Label(location_frame, text="Position: Not set", width=20)
                position_label.pack(side="left", padx=5)
                
                # Get Position button
                get_pos_btn = ttk.Button(location_frame, text="Get Position", 
                                       command=lambda idx=i, label=position_label: 
                                       self.start_position_tracking(idx, label))
                get_pos_btn.pack(side="left", padx=5)
                
                self.locations.append({
                    "frame": location_frame,
                    "action": action_var,
                    "delay": delay_var,
                    "position_label": position_label,
                    "position": None
                })
                
        except ValueError as e:
            messagebox.showerror("Error", str(e))
            
    def start_position_tracking(self, index, label):
        if self.position_update_running:
            self.stop_position_tracking()
            
        self.current_position = None
        self.position_update_running = True
        self.current_tracking_index = index
        
        # Create save button if it doesn't exist
        if self.save_button is None:
            self.save_button = ttk.Button(self.root, text="Save Current Position", 
                                        command=self.save_current_position)
        self.save_button.pack(pady=5)
        # Bind Enter key
        self.root.bind('<Return>', self.save_current_position_event)
        
        def update_position():
            while self.position_update_running:
                x, y = pyautogui.position()
                label.config(text=f"Position: ({x}, {y})")
                self.current_position = (x, y)
                self.root.update()
                time.sleep(0.1)
                
        self.position_thread = threading.Thread(target=update_position)
        self.position_thread.daemon = True
        self.position_thread.start()
        
    def save_current_position(self):
        if self.current_position is not None and self.current_tracking_index is not None:
            index = self.current_tracking_index
            self.locations[index]["position"] = self.current_position
            self.locations[index]["position_label"].config(
                text=f"Position: {self.current_position}")
            self.stop_position_tracking()
            self.status_label.config(
                text=f"Location {index + 1} saved at {self.current_position}")
        
    def save_current_position_event(self, event):
        self.save_current_position()
        
    def stop_position_tracking(self):
        self.position_update_running = False
        if hasattr(self, 'position_thread'):
            self.position_thread.join(timeout=1)
        if self.save_button:
            self.save_button.pack_forget()
        # Unbind Enter key
        self.root.unbind('<Return>')
        
    def perform_action(self, action, position):
        if position:
            # Add a small delay before moving to ensure stability
            time.sleep(0.1)
            
            # Move to position
            pyautogui.moveTo(position[0], position[1])
            
            # Verify position before clicking
            current_x, current_y = pyautogui.position()
            if abs(current_x - position[0]) > 5 or abs(current_y - position[1]) > 5:
                # If position is off, try to correct it
                pyautogui.moveTo(position[0], position[1])
                time.sleep(0.1)  # Wait for movement to complete
            
            if action == "left_click":
                pyautogui.click()
            elif action == "right_click":
                pyautogui.rightClick()
            elif action == "up_arrow":
                keyboard.press_and_release('up')
            elif action == "down_arrow":
                keyboard.press_and_release('down')
            elif action == "enter":
                keyboard.press_and_release('enter')
                
    def clicking_thread(self):
        repeat_count = int(self.repeat_count.get())
        count = 0
        total_clicks = 0
        
        while self.is_running and (repeat_count == 0 or count < repeat_count):
            for location in self.locations:
                if not self.is_running:
                    break
                    
                action = location["action"].get()
                delay = float(location["delay"].get())
                position = location["position"]
                
                if position:
                    self.perform_action(action, position)
                    total_clicks += 1
                    self.total_clicks_label.config(text=f"Total Clicks: {total_clicks}")
                    time.sleep(delay)
                    
            count += 1
            self.iteration_label.config(text=f"Current Iteration: {count}")
            self.status_label.config(text=f"Completed iteration {count}")
            
        self.is_running = False
        self.start_button.config(state="normal")
        self.stop_button.config(state="disabled")
        self.status_label.config(text="Ready")
        
    def start_clicking(self):
        if not any(loc["position"] for loc in self.locations):
            messagebox.showerror("Error", "Please set at least one location first")
            return
            
        self.is_running = True
        self.start_button.config(state="disabled")
        self.stop_button.config(state="normal")
        
        self.current_thread = threading.Thread(target=self.clicking_thread)
        self.current_thread.daemon = True
        self.current_thread.start()
        
    def stop_clicking(self):
        self.is_running = False
        self.start_button.config(state="normal")
        self.stop_button.config(state="disabled")
        
    def save_locations(self):
        if not self.locations:
            messagebox.showerror("Error", "No locations to save")
            return
            
        file_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            title="Save Locations"
        )
        
        if file_path:
            try:
                locations_data = []
                for loc in self.locations:
                    if loc["position"]:  # Only save locations that have positions set
                        locations_data.append({
                            "action": loc["action"].get(),
                            "delay": loc["delay"].get(),
                            "position": loc["position"]
                        })
                
                with open(file_path, 'w') as f:
                    json.dump(locations_data, f)
                messagebox.showinfo("Success", "Locations saved successfully!")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save locations: {str(e)}")
                
    def load_locations(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            title="Load Locations"
        )
        
        if file_path:
            try:
                with open(file_path, 'r') as f:
                    locations_data = json.load(f)
                
                # Clear existing locations
                for widget in self.locations_frame.winfo_children():
                    widget.destroy()
                self.locations.clear()
                
                # Set number of locations
                self.num_locations.delete(0, tk.END)
                self.num_locations.insert(0, str(len(locations_data)))
                
                # Create new locations
                for i, loc_data in enumerate(locations_data):
                    location_frame = ttk.Frame(self.locations_frame)
                    location_frame.pack(fill="x", pady=2)
                    
                    ttk.Label(location_frame, text=f"Location {i+1}:").pack(side="left")
                    
                    # Action selection
                    action_var = tk.StringVar(value=loc_data["action"])
                    action_combo = ttk.Combobox(location_frame, textvariable=action_var, 
                                              values=["left_click", "right_click", "up_arrow", "down_arrow", "enter"],
                                              width=15)
                    action_combo.pack(side="left", padx=5)
                    
                    # Delay entry
                    ttk.Label(location_frame, text="Delay (seconds):").pack(side="left")
                    delay_var = tk.StringVar(value=loc_data["delay"])
                    delay_entry = ttk.Entry(location_frame, textvariable=delay_var, width=5)
                    delay_entry.pack(side="left", padx=5)
                    
                    # Position display
                    position_label = ttk.Label(location_frame, text=f"Position: {loc_data['position']}", width=20)
                    position_label.pack(side="left", padx=5)
                    
                    # Get Position button
                    get_pos_btn = ttk.Button(location_frame, text="Get Position", 
                                           command=lambda idx=i, label=position_label: 
                                           self.start_position_tracking(idx, label))
                    get_pos_btn.pack(side="left", padx=5)
                    
                    self.locations.append({
                        "frame": location_frame,
                        "action": action_var,
                        "delay": delay_var,
                        "position_label": position_label,
                        "position": loc_data["position"]
                    })
                
                messagebox.showinfo("Success", "Locations loaded successfully!")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load locations: {str(e)}")
        
    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = AutoClicker()
    app.run() 