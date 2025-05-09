# Monitor Input Switch

A cross-platform desktop application for switching monitor input sources (e.g., HDMI/DP) with a modern GUI. Built with Python, Tkinter, and monitorcontrol.

---

## Table of Contents
- [Project Overview](#project-overview)
- [Features](#features)
- [Architecture Diagram](#architecture-diagram)
- [Folder Structure](#folder-structure)
- [Core Components](#core-components)
  - [app_ui.py (GUI)](#app_uipy-gui)
  - [monitor_manager.py (Monitor Abstraction)](#monitor_managerpy-monitor-abstraction)
  - [control_logic.py (Input Switching Logic)](#control_logicpy-input-switching-logic)
  - [pyinstaller.py (Packaging)](#pyinstallerpy-packaging)
- [Implementation Details](#implementation-details)
  - [Monitor Detection](#monitor-detection)
  - [Input Switching](#input-switching)
  - [GUI Layout & User Experience](#gui-layout--user-experience)
  - [Error Handling](#error-handling)
  - [Packaging with PyInstaller](#packaging-with-pyinstaller)
- [Example Usage](#example-usage)
- [Troubleshooting & FAQ](#troubleshooting--faq)
- [Credits](#credits)

---

## Project Overview

Monitor Input Switch is a desktop utility that allows users to quickly switch the input source of their connected monitors (e.g., from HDMI to DisplayPort) using a graphical interface. It is especially useful for multi-monitor setups and KVM-like workflows.

## Features
- Detects all connected monitors and displays their model names.
- Allows toggling input source (HDMI1/DP1) per monitor.
- Modern, draggable, borderless GUI with custom background and icons.
- Fast switching with visual feedback (button color changes).
- Restart and Exit controls.
- Cross-platform (Windows, Linux, macOS*), packaged as a single executable via PyInstaller.

*Note: Full functionality depends on monitorcontrol library support for your OS and monitor hardware.

## Architecture Diagram

```mermaid
graph TD
    UI[app_ui.py (Tkinter GUI)]
    MM[monitor_manager.py (Monitor Abstraction)]
    CL[control_logic.py (Switch Logic)]
    PyI[pyinstaller.py (Packaging)]
    MonLib[monitorcontrol (3rd party)]
    
    UI -- "calls" --> MM
    UI -- "calls" --> CL
    MM -- "wraps" --> MonLib
    CL -- "uses" --> MM
    PyI -- "packages" --> UI
```

## Folder Structure

```
├── app_ui.py              # Main GUI application
├── monitor_manager.py     # Monitor abstraction and detection
├── control_logic.py       # Input switching logic
├── pyinstaller.py         # Build script for packaging
├── background.jpg         # GUI background image
├── monitor_icon.jpg/png   # Monitor icon for buttons
├── icon.webp              # App icon (converted for packaging)
├── requirements.txt       # Python dependencies
├── ...
```

## Core Components

### app_ui.py (GUI)
- Implements the Tkinter-based GUI.
- Handles layout, monitor controls, drag-to-move, and visual feedback.
- Loads background and icons dynamically.
- Calls monitor_manager to detect monitors and control_logic to switch inputs.

**Key snippet:**
```python
from monitor_manager import initialize_monitors
import control_logic
# ...
def create_gui():
    # ...
    show_loading_screen(root_window)
    def detect_and_finish():
        detected = initialize_monitors()
        root_window.after(0, lambda: finish_gui_setup(detected))
    threading.Thread(target=detect_and_finish, daemon=True).start()
```

### monitor_manager.py (Monitor Abstraction)
- Wraps the monitorcontrol library.
- Provides MyMonitor class for safe querying and input switching.
- Handles errors and retries.

**Key snippet:**
```python
class MyMonitor:
    def __init__(self, index, monitor_obj):
        # ...
        with self.monitor:
            self.vcp = self.monitor.get_vcp_capabilities()
            self.model = self.vcp.get('model', 'N/A')
            # ...
    def set_input_source(self, desired_source_str):
        with self.monitor:
            self.monitor.set_input_source(desired_source_str)
```

### control_logic.py (Input Switching Logic)
- Contains logic to toggle between HDMI1 and DP1.
- Adds delay for monitor stabilization.

**Key snippet:**
```python
def toggle_monitor_input(monitor):
    current_source = monitor.get_current_source_str()
    new_source = "DP1" if current_source == "HDMI1" else "HDMI1"
    success = monitor.set_input_source(new_source)
    time.sleep(2)
    return success, new_source
```

### pyinstaller.py (Packaging)
- Automates building a standalone executable.
- Handles icon conversion (e.g., .webp/.jpg → .ico for Windows).
- Adds required data files (background, icons).

**Key snippet:**
```python
command = [
    sys.executable, '-m', 'PyInstaller', '--onefile', '--windowed',
    '--name', 'MonitorInputSwitch',
    f'--add-data=background.jpg{data_sep}.',
    f'--add-data=monitor_icon.jpg{data_sep}.',
]
# ...icon handling...
subprocess.run(command, ...)
```

## Implementation Details

### Monitor Detection
- Uses `monitorcontrol.get_monitors()` to enumerate all connected displays.
- Each monitor is wrapped in a `MyMonitor` object for safe access and error handling.
- Model names and current input sources are queried and displayed in the GUI.

### Input Switching
- The GUI button for each monitor calls `toggle_monitor_input()`.
- The function toggles between HDMI1 and DP1 (can be extended for more sources).
- Visual feedback is provided (button color changes on success/failure).

### GUI Layout & User Experience
- Borderless, draggable window (drag on background image).
- Monitors are arranged in a 2x2 grid (top/bottom left/right), with swap functionality for left monitors.
- Custom background and icons for a modern look.
- Exit and Restart buttons at the bottom.

**GUI Layout Example:**
![image](https://github.com/user-attachments/assets/51aa1d0c-d1e2-4dfd-bd2d-a9c374411295)


### Error Handling
- All monitor operations are wrapped in try/except blocks.
- Errors are printed to the console and reflected in the GUI (e.g., button turns red).
- Initialization errors are shown as "Error" in the monitor status.

### Packaging with PyInstaller
- `pyinstaller.py` script automates building the app for distribution.
- Handles icon conversion and data file inclusion.
- Produces a single-file executable for easy deployment.

## Example Usage

1. **Run the app:**
   ```sh
   python app_ui.py
   ```
2. **Build an executable:**
   ```sh
   python pyinstaller.py
   # Output will be in the 'dist' folder
   ```
3. **Switch monitor input:**
   - Click the "Switch Input" button for any monitor in the GUI.
   - Button turns green on success, orange/red on error.

## Troubleshooting & FAQ

- **Q: No monitors detected?**
  - Ensure your monitors support DDC/CI and are connected.
  - Try running as administrator (Windows) or with sudo (Linux).
  - Check that the `monitorcontrol` library supports your hardware.

- **Q: Input not switching?**
  - Not all monitors support input switching via DDC/CI.
  - Check the console for error messages.

- **Q: App window not draggable?**
  - Drag the background image area, not the controls.

- **Q: Packaging fails?**
  - Ensure all dependencies are installed (`pip install -r requirements.txt`).
  - For icon conversion, Pillow is required (`pip install Pillow`).

## Credits
- Developed by MCDIX incorporated
- Powered by [monitorcontrol](https://github.com/newAM/monitorcontrol)
- GUI: Tkinter, Pillow
- Packaging: PyInstaller

---

*For questions or contributions, open an issue or pull request on GitHub.*
