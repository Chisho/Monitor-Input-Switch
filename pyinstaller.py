import subprocess
import sys
import os
import tempfile # Required for temporary files
from PIL import Image # Required for image conversion (install with: pip install Pillow)

def run_pyinstaller(script_name, icon_path=None):
    # Determine OS-specific separator for --add-data paths
    if sys.platform == "win32":
        data_sep = ";"
        required_icon_ext = ".ico"
    else:
        data_sep = ":"
        required_icon_ext = ".icns" # .icns for macOS, .png/.xpm often for Linux

    # Base command using the current Python interpreter to run PyInstaller
    command = [
        sys.executable,
        '-m', 'PyInstaller',
        '--onefile',
        '--windowed',
        '--name', 'MonitorInputSwitch',
        f'--add-data=background.jpg{data_sep}.',
        f'--add-data=monitor_icon.jpg{data_sep}.',
        f'--add-data=dark_icon.png{data_sep}.',
        '--hidden-import=samsung_tizen_controller',
        '--hidden-import=monitor_manager',
        '--hidden-import=control_logic',
        '--hidden-import=requests',
        '--hidden-import=monitorcontrol',
        '--hidden-import=samsungtvws',
        '--hidden-import=websocket',
    ]

    # --- Icon Handling Logic ---
    temp_icon_file = None # To store path to temporary icon if needed
    actual_icon_path_to_use = None

    if icon_path:
        if not os.path.exists(icon_path):
            print(f"Error: Provided icon file '{icon_path}' does not exist.")
            sys.exit(1)

        # Check if conversion is needed (Windows specifically needs .ico)
        if sys.platform == "win32" and not icon_path.lower().endswith(required_icon_ext):
            print(f"Icon '{icon_path}' is not a {required_icon_ext} file. Attempting automatic conversion...")
            try:
                # Create a temporary file with .ico suffix
                # Using delete=False and manual cleanup in finally for robustness
                fd, temp_icon_file = tempfile.mkstemp(suffix=required_icon_ext)
                os.close(fd) # Close the file descriptor

                img = Image.open(icon_path)
                # Save as ICO, potentially specifying multiple sizes for better results
                img.save(temp_icon_file, format='ICO', sizes=[(16,16), (32, 32), (48, 48), (64, 64), (256, 256)])
                print(f"Successfully converted '{icon_path}' to temporary icon '{temp_icon_file}'")
                actual_icon_path_to_use = temp_icon_file
            except ImportError:
                print("Error: Pillow library not found. Cannot convert icon.")
                print("Please install it: pip install Pillow")
                if temp_icon_file and os.path.exists(temp_icon_file):
                    os.remove(temp_icon_file) # Clean up if temp file was created before error
                sys.exit(1)
            except Exception as e:
                print(f"Error converting icon '{icon_path}' to {required_icon_ext}: {e}")
                if temp_icon_file and os.path.exists(temp_icon_file):
                    os.remove(temp_icon_file) # Clean up on conversion error
                # Optionally fallback to no icon or exit
                print("Proceeding without a custom icon.")
                actual_icon_path_to_use = None # Reset path if conversion failed
                # Or uncomment below to exit if icon is mandatory
                # sys.exit(1)
        else:
            # Icon is already in the correct format or not on Windows
            # Still check if the required format is met on other OS if needed
            if not icon_path.lower().endswith(required_icon_ext):
                 print(f"Warning: Icon file '{icon_path}' does not have the expected extension ('{required_icon_ext}' on {sys.platform}).")
                 # PyInstaller might handle common formats like .png on Linux/macOS even if .icns is preferred on macOS
            actual_icon_path_to_use = icon_path

    # Add the script name itself
    command.append(script_name)

    # Add the icon command if we have a valid path (original or temporary)
    if actual_icon_path_to_use:
        command.extend(['--icon', actual_icon_path_to_use])


    # --- Execute PyInstaller ---
    try:
        print(f"Running command: {' '.join(command)}")
        result = subprocess.run(command, check=True, capture_output=True, text=True, encoding='utf-8')
        print("PyInstaller output:\n", result.stdout)
        print(f"{script_name} successfully built into an executable.")
    except subprocess.CalledProcessError as e:
        print(f"Error occurred during PyInstaller execution:")
        print(f"Command: {' '.join(e.cmd)}")
        print(f"Return code: {e.returncode}")
        print(f"Output:\n{e.stdout}")
        print(f"Error Output:\n{e.stderr}")
        sys.exit(1)
    except FileNotFoundError as e:
        print(f"Error: Could not find Python executable or PyInstaller module.")
        print(e)
        sys.exit(1)
    finally:
        # --- Cleanup: Remove temporary icon file if created ---
        if temp_icon_file and os.path.exists(temp_icon_file):
            try:
                os.remove(temp_icon_file)
                print(f"Removed temporary icon file: {temp_icon_file}")
            except OSError as e:
                print(f"Warning: Could not remove temporary icon file '{temp_icon_file}': {e}")


if __name__ == "__main__":
    # Use dark_icon.png as the application icon
    icon_to_use = 'dark_icon.png'
    
    run_pyinstaller('app_ui.py', icon_to_use)