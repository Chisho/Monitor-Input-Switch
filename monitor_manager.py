from monitorcontrol import get_monitors
import traceback
import sys
from samsung_tizen_controller import SamsungTizenController
import json
import os

class MyMonitor:
    VCP_INPUT_CODES = {
        15: "DisplayPort 1",
        16: "DisplayPort 2",
        17: "HDMI 1",
        18: "HDMI 2",
        27: "USB-C",
        3: "DVI 1",
        4: "DVI 2",
        1: "VGA 1",
        12: "VGA 1" # Sometimes
    }

    def __init__(self, index, monitor_obj, is_tizen=False):
        self.index = index
        self.monitor = monitor_obj
        self.vcp = {}
        self.model = "N/A"
        self.current_source = "Unknown"
        self.software_source = None
        self.error = None
        self.is_tizen = is_tizen
        self.tizen_controller = None
        
        # Load Local Config (Tizen)
        self.local_config = self._load_local_config()

        # If this is the Tizen Monitor (Samsung G8)
        if self.is_tizen:
            self.model = "Samsung OLED G8 (Local)"
            monitor_ip = self.local_config.get("monitor_ip")
            
            if monitor_ip:
                print(f"[Monitor {self.index}] Initializing Local Tizen Control at {monitor_ip}")
                
                # Setup Token Path
                app_data_dir = os.path.join(os.environ.get('APPDATA', '.'), 'MonitorInputSwitch')
                os.makedirs(app_data_dir, exist_ok=True)
                token_file = os.path.join(app_data_dir, "samsung_g8_token.txt")
                
                # Initialize Controller (Disconnected initially)
                # Default source assumption: DP1
                self.current_source = "DisplayPort 1"
                
                # Initialize controller with default state
                self.tizen_controller = SamsungTizenController(
                    monitor_ip, 
                    token_file=token_file, 
                    initial_state=self.current_source
                )
                
            else:
                print(f"[Monitor {self.index}] Tizen control enabled but no IP configured.")
                self.error = Exception("Local IP not configured in local_config.json")
            return
        
        # Normal VCP initialization for standard monitors
        try:
            with self.monitor:
                self.vcp = self.monitor.get_vcp_capabilities()
                self.model = self.vcp.get('model', 'N/A')
                source_obj = self.monitor.get_input_source()
                # print(f"[DEBUG] Monitor {self.index} ({self.model}) get_input_source() raw: {repr(source_obj)}")
                
                # Handle raw int codes or Enum members
                if isinstance(source_obj, int):
                    self.current_source = self.VCP_INPUT_CODES.get(source_obj, str(source_obj))
                elif hasattr(source_obj, 'name'):
                    self.current_source = source_obj.name
                else:
                    self.current_source = str(source_obj)
                
                # If this is the buggy model, initialize software_source
                if self.is_ed32qur():
                    self.software_source = self.current_source
        except Exception as e:
            self.error = e
            print(f"Error initializing Monitor Index {self.index}: {type(e).__name__}: {e}")

    def _load_local_config(self):
        try:
            if os.path.exists("local_config.json"):
                with open("local_config.json", 'r') as f:
                    return json.load(f)
        except:
            pass
        return {}

    def is_ed32qur(self):
        return "ED32" in self.model.upper() and "QUR" in self.model.upper()

    def get_model(self):
        return self.model

    def get_current_source_str(self):
        # Tizen Monitor: Return tracked state
        if self.is_tizen:
             if self.tizen_controller:
                 # Map 'DP1' to 'DisplayPort 1' if needed to match UI expectations? 
                 # Or keep 'DP1' as the internal string. 
                 # The UI might display just 'DP1', checking app_ui later.
                 return self.tizen_controller.current_app_state
             return self.current_source

        if self.error: 
            return "Error"
        if self.is_ed32qur() and self.software_source:
             return self.software_source
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                with self.monitor:
                    source_obj = self.monitor.get_input_source()
                    
                    if isinstance(source_obj, int):
                         self.current_source = self.VCP_INPUT_CODES.get(source_obj, str(source_obj))
                    elif hasattr(source_obj, 'name'):
                         self.current_source = source_obj.name
                    else:
                         self.current_source = str(source_obj)
                         
                    return self.current_source
            except Exception as e:
                if attempt < max_retries - 1:
                    import time
                    time.sleep(1)
                    continue
                return "Unknown (Error checking)"

    def set_input_source(self, desired_source_str, offline_mode=False):
        # Tizen Control
        if self.is_tizen and self.tizen_controller:
            print(f"Setting Tizen Monitor {self.index} to '{desired_source_str}'...")
            try:
                # Update controller's knowledge of current state before action
                # We update the controller state with what we THINK is current, if needed.
                # Actually, the controller maintains state.
                
                if self.tizen_controller.connect():
                    success = self.tizen_controller.set_input_source(desired_source_str)
                    self.tizen_controller.disconnect()
                    if success:
                        self.current_source = desired_source_str
                        print(f"Tizen Monitor {self.index} switched successfully.")
                    return success
                else:
                    print("Failed to connect to Tizen monitor.")
                    return False
            except Exception as e:
                print(f"Error controlling Tizen monitor: {e}")
                traceback.print_exc()
                return False
        
        # Standard VCP Control
        return self._set_vcp_source(desired_source_str)

    def _set_vcp_source(self, desired_source_str):
        if self.error:
            print(f"Monitor {self.index} has error state.")
            return False
            
        try:
            with self.monitor:
                print(f"Setting Monitor {self.index} ({self.model}) to '{desired_source_str}' via VCP...")
                self.monitor.set_input_source(desired_source_str)
                self.current_source = desired_source_str
                if self.is_ed32qur():
                    self.software_source = desired_source_str
                return True
        except Exception as e:
            print(f"VCP Error Monitor {self.index}: {e}")
            traceback.print_exc()
            return False

def initialize_monitors():
    print("--- Detecting Monitors ---")
    identified_monitors_list = []
    monitor_handles = get_monitors()

    if not monitor_handles:
        print("!!! No monitors detected.")
    else:
        for i, monitor_obj in enumerate(monitor_handles):
            print(f"\nProcessing Monitor Index: {i}")
            
            # Configure Index 3 as the Tizen/Samsung Monitor
            is_tizen = (i == 3)
            
            mon = MyMonitor(i, monitor_obj, is_tizen=is_tizen)
            identified_monitors_list.append(mon)
            
            print(f"  Index: {mon.index}")
            print(f"  Model: {mon.get_model()}")
            print(f"  Source: {mon.get_current_source_str()}")

    print("\n--- Monitor Detection Complete ---")
    print(f"Found {len(identified_monitors_list)} monitor(s).")
    print("-" * 30 + "\n")
    return identified_monitors_list
