import tkinter as tk
from PIL import Image, ImageTk
import time
import os
import sys
import traceback
import threading

from monitor_manager import initialize_monitors
import control_logic

identified_monitors_global = []
root_window = None

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def show_loading_screen(root_window):
    for widget in root_window.winfo_children():
        widget.destroy()
    # Show background image if available
    try:
        bg_image_path = resource_path("background.jpg")
        if os.path.exists(bg_image_path):
            background_image_pil = Image.open(bg_image_path)
            background_image_pil = background_image_pil.resize((900, 506), Image.LANCZOS)
            bg_image_tk = ImageTk.PhotoImage(background_image_pil)
            bg_label = tk.Label(root_window, image=bg_image_tk)
            bg_label.image = bg_image_tk
            bg_label.place(relwidth=1, relheight=1)
        else:
            bg_label = tk.Label(root_window, bg="gray50")
            bg_label.place(relwidth=1, relheight=1)
    except Exception as e:
        print(f"Error loading background image: {e}")
        bg_label = tk.Label(root_window, bg="gray50")
        bg_label.place(relwidth=1, relheight=1)

    loading_label = tk.Label(root_window, text="Loading...", fg="white", bg="gray20", font=('Arial', 20, 'bold'))
    loading_label.place(relx=0.5, rely=0.5, anchor="center")

    # Add Exit and Restart buttons (disabled during loading)
    def exit_app():
        print("Exiting application.")
        if root_window: root_window.destroy()
    exit_btn = tk.Button(root_window, text="Exit", command=exit_app, fg="white", bg="red",
                        font=('Arial', 12, 'bold'), width=10, height=2, bd=0,
                        highlightthickness=0, state=tk.DISABLED)
    exit_btn.place(relx=0.5, y=478, anchor='s')

    def restart_app():
        show_loading_screen(root_window)
        def detect_and_finish():
            detected = initialize_monitors()
            root_window.after(0, lambda: finish_gui_setup(detected))
        threading.Thread(target=detect_and_finish, daemon=True).start()
    restart_btn = tk.Button(root_window, text="Restart", command=restart_app, fg="white", bg="red",
                           font=('Arial', 12, 'bold'), width=10, height=2, bd=0,
                           highlightthickness=0, state=tk.DISABLED)
    restart_btn.place(relx=0.5, y=428, anchor='s')

    return loading_label

def create_monitor_control(parent_frame, monitor, monitor_image_tk, x, y, display_name=None):
    frame = tk.Frame(parent_frame, bg="gray20", width=250, height=180)
    frame.place(x=x, y=y)
    
    # Monitor name/model label
    label_text = display_name if display_name else f"Monitor {monitor.index}\n{monitor.get_model()}"
    name_label = tk.Label(frame, text=label_text, 
                         fg="white", bg="gray20", font=('Arial', 10, 'bold'),
                         wraplength=220)
    name_label.place(x=125, y=25, anchor="center")
    # Add monitor model label under the name
    model_label = tk.Label(frame, text=monitor.get_model(), fg="gray80", bg="gray20", font=('Arial', 9, 'italic'))
    model_label.place(x=125, y=48, anchor="center")
    
    # Current input source label
    source_label = tk.Label(frame, text=f"Current: {monitor.get_current_source_str()}", 
                           fg="white", bg="gray20", font=('Arial', 9))
    source_label.place(x=125, y=65, anchor="center")
    
    # Switch button
    btn_config = {
        "compound": "center",
        "fg": "white",
        "bg": "gray20",
        "font": ('Arial', 12, 'bold'),
        "width": 120,
        "height": 45,
        "bd": 0,
        "highlightthickness": 0,
        "text": "Switch Input"
    }
    if monitor_image_tk:
        btn_config["image"] = monitor_image_tk
    
    def update_source_label():
        current = monitor.get_current_source_str()
        source_label.config(text=f"Current: {current}")
    
    def on_switch():
        try:
            success, new_source = control_logic.toggle_monitor_input(monitor)
            if success:
                update_source_label()
                switch_btn.config(bg="green")
            else:
                switch_btn.config(bg="orange")
        except Exception as e:
            print(f"Error switching input: {e}")
            switch_btn.config(bg="red")
        finally:
            frame.after(1500, lambda: switch_btn.config(bg="gray20"))
    
    switch_btn = tk.Button(frame, **btn_config, command=on_switch)
    switch_btn.image = monitor_image_tk
    switch_btn.place(x=125, y=120, anchor="center")
    
    # Add event binding for updates
    frame.bind('<<Update>>', lambda e: update_source_label())
    
    return frame

def finish_gui_setup(monitors=None):
    global identified_monitors_global, root_window
    if monitors is not None:
        identified_monitors_global = monitors
    for widget in root_window.winfo_children():
        widget.destroy()

    try:
        bg_image_path = resource_path("background.jpg")
        if os.path.exists(bg_image_path):
            background_image_pil = Image.open(bg_image_path)
            background_image_pil = background_image_pil.resize((900, 506), Image.LANCZOS)
            bg_image_tk = ImageTk.PhotoImage(background_image_pil)
            bg_label = tk.Label(root_window, image=bg_image_tk)
            bg_label.image = bg_image_tk
            bg_label.place(relwidth=1, relheight=1)
        else:
            print(f"Warning: Background image not found at {bg_image_path}. Using gray background.")
            bg_label = tk.Label(root_window, bg="gray50")
            bg_label.place(relwidth=1, relheight=1)
    except Exception as e:
        print(f"Error loading background image: {e}")
        traceback.print_exc()
        bg_label = tk.Label(root_window, bg="gray50")
        bg_label.place(relwidth=1, relheight=1)

    dragging = False
    x_offset = y_offset = 0
    def start_move(event): nonlocal x_offset, y_offset, dragging; dragging=True; x_offset=event.x; y_offset=event.y
    def on_motion(event):
        if dragging: root_window.geometry(f"+{root_window.winfo_pointerx()-x_offset}+{root_window.winfo_pointery()-y_offset}")
    def stop_move(event): nonlocal dragging; dragging=False
    
    bg_label.bind("<ButtonPress-1>", start_move)
    bg_label.bind("<B1-Motion>", on_motion)
    bg_label.bind("<ButtonRelease-1>", stop_move)

    monitor_image_tk = None
    try:
        icon_filename_png = "monitor_icon.png"
        icon_path_png = resource_path(icon_filename_png)
        icon_filename_jpg = "monitor_icon.jpg"
        icon_path_jpg = resource_path(icon_filename_jpg)
        
        actual_icon_path = None
        loaded_filename = ""

        if os.path.exists(icon_path_png):
            actual_icon_path = icon_path_png
            loaded_filename = icon_filename_png
        elif os.path.exists(icon_path_jpg):
            print(f"Info: '{icon_filename_png}' not found, using '{icon_filename_jpg}'.")
            actual_icon_path = icon_path_jpg
            loaded_filename = icon_filename_jpg

        if actual_icon_path:
            print(f"Loading icon: {loaded_filename}")
            monitor_icon_original = Image.open(actual_icon_path)
            if monitor_icon_original.mode != 'RGBA' and loaded_filename.endswith('.png'):
                monitor_icon_original = monitor_icon_original.convert('RGBA')
            elif monitor_icon_original.mode == 'P' and 'transparency' in monitor_icon_original.info:
                monitor_icon_original = monitor_icon_original.convert('RGBA')

            icon_size = (90, 90)
            monitor_icon_resized = monitor_icon_original.resize(icon_size, Image.LANCZOS)
            monitor_image_tk = ImageTk.PhotoImage(monitor_icon_resized)
        else:
            print(f"Warning: Monitor icon not found as '{icon_filename_png}' or '{icon_filename_jpg}'. Buttons will lack icon.")
    except Exception as e:
        print(f"Error loading monitor icon: {e}")
        traceback.print_exc()
        monitor_image_tk = None

    # Find specific monitors
    c24g2u_monitor = None
    ed32qur_monitor = None
    other_monitors = []
    print("Detected monitors:")
    for monitor in identified_monitors_global:
        print(f"  Index {monitor.index}: {monitor.get_model()}")
        model = monitor.get_model().upper()
        if "C24G2U" in model:
            c24g2u_monitor = monitor
        elif ("ED32" in model and "QUR" in model):
            ed32qur_monitor = monitor
        else:
            other_monitors.append(monitor)

    # Layout constants
    window_width = 900
    window_height = 506
    control_width = 250
    control_height = 180
    margin_x = 40
    margin_y = 40
    spacing_y = 40

    # Left monitors (other two)
    left1_y = margin_y
    left2_y = margin_y + control_height + spacing_y
    swap_btn_y = margin_y + control_height + spacing_y // 2

    # Track the order of left monitors
    left_monitor_order = [0, 1] if len(other_monitors) >= 2 else []
    left_monitor_frames = [None, None]

    def render_left_monitors():
        # Remove old frames if they exist
        for frame in left_monitor_frames:
            if frame is not None:
                frame.destroy()
        # Create new frames in the current order
        if len(other_monitors) >= 2:
            left_monitor_frames[0] = create_monitor_control(root_window, other_monitors[left_monitor_order[0]], monitor_image_tk, margin_x, left1_y, display_name="Top Left")
            left_monitor_frames[1] = create_monitor_control(root_window, other_monitors[left_monitor_order[1]], monitor_image_tk, margin_x, left2_y, display_name="Bottom Left")

    def swap_left_buttons():
        if len(left_monitor_order) == 2:
            left_monitor_order[0], left_monitor_order[1] = left_monitor_order[1], left_monitor_order[0]
            render_left_monitors()

    if len(other_monitors) >= 2:
        render_left_monitors()
        swap_btn = tk.Button(root_window, text="↑↓", fg="white", bg="gray20",
                             font=('Arial', 10, 'bold'), width=2, height=1,
                             command=swap_left_buttons)
        swap_btn.place(x=margin_x + control_width // 2, y=swap_btn_y, anchor="center")

    # C24G2U top right
    if c24g2u_monitor:
        c24g2u_x = window_width - control_width - margin_x
        c24g2u_y = margin_y
        create_monitor_control(root_window, c24g2u_monitor, monitor_image_tk, c24g2u_x, c24g2u_y, display_name="Top Right")

    # ED32QUR bottom right
    if ed32qur_monitor:
        ed32qur_x = window_width - control_width - margin_x
        ed32qur_y = window_height - control_height - margin_y
        create_monitor_control(root_window, ed32qur_monitor, monitor_image_tk, ed32qur_x, ed32qur_y, display_name="Bottom Right")

    def exit_app():
        print("Exiting application.")
        if root_window: root_window.destroy()

    exit_btn = tk.Button(root_window, text="Exit", command=exit_app, fg="white", bg="red",
                        font=('Arial', 12, 'bold'), width=10, height=2, bd=0,
                        highlightthickness=0)
    exit_btn.place(relx=0.5, y=478, anchor='s')

    def restart_app():
        show_loading_screen(root_window)
        def detect_and_finish():
            detected = initialize_monitors()
            root_window.after(0, lambda: finish_gui_setup(detected))
        threading.Thread(target=detect_and_finish, daemon=True).start()

    # Add restart button just above the exit button, styled the same
    restart_btn = tk.Button(root_window, text="Restart", command=restart_app, fg="white", bg="red",
                           font=('Arial', 12, 'bold'), width=10, height=2, bd=0,
                           highlightthickness=0)
    restart_btn.place(relx=0.5, y=428, anchor='s')

    footer_text = f"Property of MCDIX incorporated, {time.strftime('%m.%Y')} - Gemini 2.5"
    footer_font = ('Arial', 8)
    footer_fg = "gray"
    footer_bg = "gray10"
    footer_label = tk.Label(root_window, text=footer_text, font=footer_font, fg=footer_fg, bg=footer_bg)
    footer_label.place(x=10, rely=1.0, y=-2, anchor='sw')

    root_window.lift()
    root_window.attributes("-topmost", True)
    root_window.after_idle(root_window.attributes, '-topmost', False)

def create_gui():
    global identified_monitors_global, root_window

    if root_window is None:
        root_window = tk.Tk()
        root_window.title("Monitor Input Switcher")
        root_window.geometry("900x506")
        root_window.overrideredirect(True)
        # Set taskbar icon on Windows
        if sys.platform == 'win32':
            ico_path = resource_path('monitor_icon.ico')
            if os.path.exists(ico_path):
                root_window.iconbitmap(ico_path)

    show_loading_screen(root_window)

    # Remove drag bindings from the root window
    # Only the background label will be draggable (handled in show_loading_screen and finish_gui_setup)

    def detect_and_finish():
        detected = initialize_monitors()
        root_window.after(0, lambda: finish_gui_setup(detected))
    threading.Thread(target=detect_and_finish, daemon=True).start()

if __name__ == "__main__":
    create_gui()
    root_window.mainloop()