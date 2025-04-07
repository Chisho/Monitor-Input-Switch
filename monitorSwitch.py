# --- Imports and MyMonitor Class (Same as before) ---
import tkinter as tk
from PIL import Image, ImageTk
import time
from monitorcontrol import get_monitors
import traceback
import os
import sys

class MyMonitor:
    # ... (MyMonitor class code remains unchanged from the previous version) ...
    def __init__(self, index, monitor_obj):
        self.index = index
        self.monitor = monitor_obj
        self.vcp = {}
        self.model = "N/A"
        self.current_source = "Unknown"
        self.error = None
        try:
            with self.monitor:
                self.vcp = self.monitor.get_vcp_capabilities()
                self.model = self.vcp.get('model', 'N/A')
                source_obj = self.monitor.get_input_source()
                self.current_source = source_obj.name if hasattr(source_obj, 'name') else str(source_obj)
        except Exception as e:
            self.error = e

    def get_model(self):
        return self.model

    def get_current_source_str(self):
        if self.error: return "Error"
        try:
             with self.monitor:
                 source_obj = self.monitor.get_input_source()
                 self.current_source = source_obj.name if hasattr(source_obj, 'name') else str(source_obj)
                 return self.current_source
        except Exception:
             return "Unknown (Error checking)"

    def set_input_source(self, desired_source_str):
        if self.error:
            print(f"Monitor Index {self.index} ({self.model}) had an initialization error. Cannot set source.")
            return False
        try:
            with self.monitor:
                print(f"Setting Monitor Index {self.index} ({self.model}) to source '{desired_source_str}'...")
                self.monitor.set_input_source(desired_source_str)
                self.current_source = desired_source_str
                print(f"Monitor Index {self.index} set successfully.")
                return True
        except ValueError:
             print(f"ERROR: Monitor Index {self.index} ({self.model}) does not support source name '{desired_source_str}'. Check available sources.")
             return False
        except Exception as e:
            print(f"ERROR setting source for Monitor Index {self.index} ({self.model}): {e}")
            traceback.print_exc()
            return False

# --- Monitor Identification (Same as before) ---
print("--- Detecting Monitors ---")
identified_monitors = []
monitor_handles = get_monitors()
# ... (Loop to identify monitors and print details - unchanged) ...
if not monitor_handles:
    print("!!! No monitors detected by monitorcontrol library.")
else:
    for i, monitor_obj in enumerate(monitor_handles):
        # ... (rest of identification loop - unchanged) ...
        print(f"\nProcessing Monitor Index: {i}")
        mon = MyMonitor(i, monitor_obj)
        identified_monitors.append(mon)
        print(f"  Index: {mon.index}")
        if mon.error:
            print(f"  Error: Could not fully query this monitor.")
            print(f"         Details: {type(mon.error).__name__}: {mon.error}")
        else:
            print(f"  Model: {mon.get_model()}")
            print(f"  Current Source: {mon.current_source}")

print("\n--- Monitor Detection Complete ---")
print(f"Found {len(identified_monitors)} monitor(s).")
print("Targeting Monitor Index 0 ('Left') and Monitor Index 3 ('Main/Right').")
print("-" * 30 + "\n")


# --- Define Monitor Indices to Control (Same as before) ---
LEFT_MONITOR_INDEX = 0
RIGHT_MONITOR_INDEX = 3

# --- Specific Action Functions (Same as before) ---
def set_both_work():
    # ... (Function unchanged) ...
    print("Action: BothWork")
    success_left = False
    success_right = False
    if LEFT_MONITOR_INDEX < len(identified_monitors):
        success_left = identified_monitors[LEFT_MONITOR_INDEX].set_input_source("DP1")
    else: print(f"Error: Monitor Index {LEFT_MONITOR_INDEX} not found.")
    if RIGHT_MONITOR_INDEX < len(identified_monitors):
        success_right = identified_monitors[RIGHT_MONITOR_INDEX].set_input_source("HDMI1")
    else: print(f"Error: Monitor Index {RIGHT_MONITOR_INDEX} not found.")
    if not (success_left and success_right):
        if (LEFT_MONITOR_INDEX < len(identified_monitors) and not success_left) or \
           (RIGHT_MONITOR_INDEX < len(identified_monitors) and not success_right):
            raise RuntimeError("One or both monitors failed to switch for BothWork.")

def set_both_no_work():
    # ... (Function unchanged) ...
    print("Action: BothNoWork")
    success_left = False
    success_right = False
    if LEFT_MONITOR_INDEX < len(identified_monitors):
        success_left = identified_monitors[LEFT_MONITOR_INDEX].set_input_source("HDMI1")
    else: print(f"Error: Monitor Index {LEFT_MONITOR_INDEX} not found.")
    if RIGHT_MONITOR_INDEX < len(identified_monitors):
        success_right = identified_monitors[RIGHT_MONITOR_INDEX].set_input_source("DP1")
    else: print(f"Error: Monitor Index {RIGHT_MONITOR_INDEX} not found.")
    if not (success_left and success_right):
         if (LEFT_MONITOR_INDEX < len(identified_monitors) and not success_left) or \
           (RIGHT_MONITOR_INDEX < len(identified_monitors) and not success_right):
            raise RuntimeError("One or both monitors failed to switch for BothNoWork.")

def set_left_work():
    # ... (Function unchanged) ...
    print("Action: LeftWork")
    success_left = False
    if LEFT_MONITOR_INDEX < len(identified_monitors):
        success_left = identified_monitors[LEFT_MONITOR_INDEX].set_input_source("DP1")
    else:
        print(f"Error: Monitor Index {LEFT_MONITOR_INDEX} not found.")
        raise IndexError(f"Monitor Index {LEFT_MONITOR_INDEX} not found.")
    if not success_left: raise RuntimeError("Monitor failed to switch for LeftWork.")

def set_right_no_work():
    # ... (Function unchanged) ...
    print("Action: RightNoWork")
    success_right = False
    if RIGHT_MONITOR_INDEX < len(identified_monitors):
        success_right = identified_monitors[RIGHT_MONITOR_INDEX].set_input_source("DP1")
    else:
        print(f"Error: Monitor Index {RIGHT_MONITOR_INDEX} not found.")
        raise IndexError(f"Monitor Index {RIGHT_MONITOR_INDEX} not found.")
    if not success_right: raise RuntimeError("Monitor failed to switch for RightNoWork.")

# --- GUI Code ---

# Function that runs the script and handles button color changes (Same as before)
def run_script(button, script_function):
    # ... (Function unchanged) ...
    original_bg = button.cget("bg")
    button.config(bg="red")
    root.update()
    try:
        script_function()
        button.config(bg="green")
    except Exception as e:
        print(f"Error during script execution: {e}")
        button.config(bg="orange")
    finally:
        root.update()
        time.sleep(1.5)
        button.config(bg=original_bg)
        root.update()

# Function to get resource path (Same as before)
def resource_path(relative_path):
    # ... (Function unchanged) ...
    try: base_path = sys._MEIPASS
    except AttributeError: base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# --- Initialize Tkinter Window (Same as before) ---
root = tk.Tk()
# ... (Title, geometry, overrideredirect - unchanged) ...
root.title("Monitor Input Switcher")
root.geometry("900x506")
root.overrideredirect(True)

# --- Background Image (Same as before) ---
try:
    # ... (Background loading unchanged) ...
    bg_image_path = resource_path("background.jpg")
    if os.path.exists(bg_image_path):
        background_image = Image.open(bg_image_path)
        background_image = background_image.resize((900, 506), Image.LANCZOS)
        bg_image = ImageTk.PhotoImage(background_image)
        bg_label = tk.Label(root, image=bg_image)
        bg_label.place(relwidth=1, relheight=1)
    else:
        print(f"Warning: Background image not found at {bg_image_path}. Using gray background.")
        bg_label = tk.Label(root, bg="gray50")
        bg_label.place(relwidth=1, relheight=1)
except Exception as e:
    print(f"Error loading background image: {e}")
    bg_label = tk.Label(root, bg="gray50")
    bg_label.place(relwidth=1, relheight=1)


# --- Window Dragging Functionality (Same as before) ---
dragging = False
x_offset = y_offset = 0
def start_move(event): global x_offset, y_offset, dragging; dragging=True; x_offset=event.x; y_offset=event.y
def on_motion(event):
    if dragging: root.geometry(f"+{root.winfo_pointerx()-x_offset}+{root.winfo_pointery()-y_offset}")
def stop_move(event): global dragging; dragging=False
bg_label.bind("<ButtonPress-1>", start_move)
bg_label.bind("<B1-Motion>", on_motion)
bg_label.bind("<ButtonRelease-1>", stop_move)


# --- Monitor Icon for Buttons (*** UPDATED ***) ---
monitor_image = None # Default to no image
try:
    # Prefer PNG for potential transparency, fallback to JPG
    icon_filename = "monitor_icon.png"
    icon_path = resource_path(icon_filename)
    if not os.path.exists(icon_path):
        print(f"Info: '{icon_filename}' not found, trying '.jpg'...")
        icon_filename = "monitor_icon.jpg"
        icon_path = resource_path(icon_filename)

    if os.path.exists(icon_path):
        print(f"Loading icon: {icon_filename}") # Confirm which icon is loaded
        monitor_icon_original = Image.open(icon_path)
        # Ensure image has an alpha channel for proper transparency handling if PNG
        if monitor_icon_original.mode != 'RGBA':
             monitor_icon_original = monitor_icon_original.convert('RGBA')

        # Resize (Consider Lanczos for better quality downscaling)
        icon_size = (90, 90) # Keep the size consistent
        monitor_icon_resized = monitor_icon_original.resize(icon_size, Image.LANCZOS)
        monitor_image = ImageTk.PhotoImage(monitor_icon_resized)
    else:
        print(f"Warning: Monitor icon not found as '{icon_filename}' or '.jpg'. Buttons will lack icon.")

except Exception as e:
    print(f"Error loading monitor icon: {e}")
    traceback.print_exc()
    monitor_image = None # Ensure it's None on error


# --- Create Buttons (Same as before, uses updated monitor_image) ---
def create_button(frame, text, command, x, y):
    # ... (Function unchanged, will use whatever monitor_image loaded) ...
    btn_config = {
        "compound": "center", "command": lambda: run_script(btn, command),
        "fg": "white", "bg": "gray20", "font": ('Arial', 12, 'bold'),
        "width": 100, "height": 100, "bd": 0, "highlightthickness": 0
    }
    if monitor_image: btn_config["image"] = monitor_image
    btn = tk.Button(frame, **btn_config)
    btn.place(x=x, y=y)
    label = tk.Label(frame, text=text, fg="white", bg="gray20", font=('Arial', 10, 'bold'))
    label.place(x=x, y=y + 105, width=100)
    return btn

button1 = create_button(root, "BothWork", set_both_work, x=50, y=50)
button2 = create_button(root, "BothNoWork", set_both_no_work, x=750, y=50)
button3 = create_button(root, "LeftWork", set_left_work, x=50, y=356)
button4 = create_button(root, "RightNoWork", set_right_no_work, x=750, y=356)


# --- Exit Button (Same as before) ---
def exit_app(): print("Exiting application."); root.destroy()
# ... (Button creation unchanged) ...
exit_button = tk.Button(root, text="Exit", command=exit_app, fg="white", bg="red", font=('Arial', 12, 'bold'), width=10, height=2, bd=0, highlightthickness=0)
exit_button.place(relx=0.5, y=478, anchor='s')


# --- Footer Label (*** UPDATED ***) ---
footer_text = "Property of MCDIX incorporated, 04.2025 - Gemini 2.5"
footer_font = ('Arial', 8)
footer_fg = "gray"
# Set a background color that blends better with dark backgrounds
# Try 'gray10', 'gray5', or another dark shade found in your background.jpg
footer_bg = "gray10" # Changed from 'black'

footer_label = tk.Label(
    root,
    text=footer_text,
    font=footer_font,
    fg=footer_fg,
    bg=footer_bg # Use the chosen dark gray color
)
# Anchor to bottom-left
footer_label.place(x=10, rely=1.0, y=-2, anchor='sw')


# --- Run Main Loop (Same as before) ---
root.lift()
# ... (Rest of main loop unchanged) ...
root.attributes("-topmost", True)
root.after_idle(root.attributes, '-topmost', False)
root.mainloop()