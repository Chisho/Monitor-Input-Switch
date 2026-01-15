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

    def __init__(self, index, monitor_obj, use_smartthings=False):
        self.index = index
        self.monitor = monitor_obj
        self.vcp = {}
        self.model = "N/A"
        self.current_source = "Unknown"
        self.software_source = None  # For models that don't report source correctly
        self.error = None
        self.use_smartthings = use_smartthings
        
        # Load Local Config (Tizen)
        self.local_config = self._load_local_config()
        self.force_local = self.local_config.get("use_local_control", False)

        # If this monitor was tagged for "SmartThings" (Network Control), check if we use Local Tizen
        if self.use_smartthings:
            if self.force_local:
                self.model = "Samsung (Local)"
                monitor_ip = self.local_config.get("monitor_ip")
                
                if monitor_ip:
                    print(f"[Monitor {self.index}] Initializing Local Tizen Control at {monitor_ip}")
                    self.smartthings = SamsungTizenController(monitor_ip) 
                    # We reuse self.smartthings variable name to keep app_ui compatible 
                    # (duck typing: both controllers should have get_current_source / set_source)
                    
                    # Try to get initial source
                    try:
                        # Tizen doesn't always strictly report "HDMI1", but we can try
                        # For now default to HDMI1 as Tizen query is slow/async
                        self.current_source = "HDMI1" 
                    except:
                        self.current_source = "Unknown"
                else:
                    print(f"[Monitor {self.index}] Local control enabled but no IP configured.")
                    self.error = Exception("Local IP not configured")
                return
            else:
                 # Logic for SmartThings (Removed) or fallback
                print(f"[Monitor {self.index}] Network control requested but no method configured.")
                self.model = "Samsung (Unknown)"
            return
        
        # Normal VCP initialization for non-SmartThings monitors
        try:
            with self.monitor:
                self.vcp = self.monitor.get_vcp_capabilities()
                self.model = self.vcp.get('model', 'N/A')
                source_obj = self.monitor.get_input_source()
                print(f"[DEBUG] Monitor {self.index} ({self.model}) get_input_source() raw: {repr(source_obj)}, type: {type(source_obj)}")
                
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
        import json
        import os
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
        # Use SmartThings placeholder
        if self.use_smartthings:
             return self.current_source

        if self.error: 
            return "Error"
        if self.is_ed32qur() and self.software_source:
            # Use software-remembered source for this model
            print(f"[DEBUG] Monitor {self.index} ({self.model}) using software_source: {self.software_source}")
            return self.software_source
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                with self.monitor:
                    source_obj = self.monitor.get_input_source()
                    print(f"[DEBUG] Monitor {self.index} ({self.model}) get_input_source() raw: {repr(source_obj)}, type: {type(source_obj)} (get_current_source_str)")
                    
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
                    time.sleep(1)  # Wait before retry
                    continue
                print(f"Error checking source for Monitor {self.index}: {e}")
                return "Unknown (Error checking)"

    def set_input_source(self, desired_source_str, offline_mode=False):
        # Use local WebSocket control if offline_mode is enabled OR if force_local is enabled
        if self.use_smartthings and (offline_mode or self.force_local):
            print(f"Setting Monitor Index {self.index} to source '{desired_source_str}' via LOCAL WebSocket...")
            try:
                from samsung_tizen_controller import SamsungTizenController
                import os
                
                # Use configured IP if available
                monitor_ip = self.local_config.get("monitor_ip", "192.168.0.52")

                # Save token in Windows AppData folder (proper location for app data)
                app_data_dir = os.path.join(os.environ.get('APPDATA', '.'), 'MonitorInputSwitch')
                os.makedirs(app_data_dir, exist_ok=True)  # Create folder if it doesn't exist
                token_file = os.path.join(app_data_dir, "samsung_g8_token.txt")
                print(f"[DEBUG] Token file location: {token_file}")
                
                controller = SamsungTizenController(monitor_ip, token_file=token_file)
                if controller.connect():
                    success = controller.set_input_source(desired_source_str)
                    controller.disconnect()
                    if success:
                        self.current_source = desired_source_str
                        print(f"Monitor Index {self.index} set successfully via local WebSocket.")
                    return success
                else:
                    print(f"Failed to connect to monitor via local WebSocket")
                    return False
            except Exception as e:
                print(f"Error using local WebSocket control: {e}")
                import traceback
                traceback.print_exc()
                return False
        
        # Use Tizen/SmartThings Controller (Unified)
        if self.use_smartthings and hasattr(self, 'smartthings') and self.smartthings:
            print(f"Setting Monitor Index {self.index} (Samsung) to source '{desired_source_str}'...")
            # Detect if it's the Tizen controller (it has set_source instead of set_input_source in some versions, check compatibility)
            # Actually both usually use set_source or similar. Let's check samsung_tizen_controller.py if needed.
            # Assuming set_input_source is the standard interface we built.
            
            try:
                success = self.smartthings.set_input_source(desired_source_str)
                if success:
                    self.current_source = desired_source_str
                    print(f"Monitor Index {self.index} set successfully via Network Controller.")
                return success
            except Exception as e:
                 print(f"Error setting source via network: {e}")
                 return False
        
        if self.error:
            print(f"Monitor Index {self.index} ({self.get_model()}) had an initialization error. Cannot set source.")
            return False
        try:
            with self.monitor:
                print(f"Setting Monitor Index {self.index} ({self.get_model()}) to source '{desired_source_str}'...")
                self.monitor.set_input_source(desired_source_str)
                self.current_source = desired_source_str
                if self.is_ed32qur():
                    self.software_source = desired_source_str  # Remember last set for this model
                print(f"Monitor Index {self.index} set successfully.")
                return True
        except ValueError:
             print(f"ERROR: Monitor Index {self.index} ({self.get_model()}) does not support source name '{desired_source_str}'. Check available sources.")
             return False
        except Exception as e:
            print(f"ERROR setting source for Monitor Index {self.index} ({self.get_model()}): {e}")
            import traceback
            traceback.print_exc()
            return False

def initialize_monitors():
    print("--- Detecting Monitors ---")
    identified_monitors_list = []
    monitor_handles = get_monitors()

    if not monitor_handles:
        print("!!! No monitors detected by monitorcontrol library.")
    else:
        for i, monitor_obj in enumerate(monitor_handles):
            print(f"\nProcessing Monitor Index: {i}")
            
            # Check if this monitor should use SmartThings (monitor index 3 is the G8)
            use_smartthings = (i == 3)
            
            mon = MyMonitor(i, monitor_obj, use_smartthings=use_smartthings)
            identified_monitors_list.append(mon)
            print(f"  Index: {mon.index}")
            if mon.error:
                print(f"  Error: Could not fully query this monitor.")
                print(f"         Details: {type(mon.error).__name__}: {mon.error}")
            else:
                print(f"  Model: {mon.get_model()}")
                print(f"  Current Source: {mon.get_current_source_str()}")

    print("\n--- Monitor Detection Complete ---")
    print(f"Found {len(identified_monitors_list)} monitor(s).")
    print("-" * 30 + "\n")
    return identified_monitors_list