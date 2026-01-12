from monitorcontrol import get_monitors
import traceback
import sys
from smartthings_controller import SmartThingsController

class MyMonitor:
    def __init__(self, index, monitor_obj, use_smartthings=False):
        self.index = index
        self.monitor = monitor_obj
        self.vcp = {}
        self.model = "N/A"
        self.current_source = "Unknown"
        self.software_source = None  # For models that don't report source correctly
        self.error = None
        self.use_smartthings = use_smartthings
        self.smartthings = None
        
        # If this monitor should use SmartThings, initialize the controller
        if self.use_smartthings:
            self.smartthings = SmartThingsController()
            if self.smartthings.is_configured():
                self.model = "Samsung (SmartThings)"
                self.current_source = self.smartthings.get_current_source() or "Unknown"
                print(f"[Monitor {self.index}] Using SmartThings API control")
            else:
                print(f"[Monitor {self.index}] SmartThings not configured properly")
                self.error = Exception("SmartThings not configured")
            return
        
        # Normal VCP initialization for non-SmartThings monitors
        try:
            with self.monitor:
                self.vcp = self.monitor.get_vcp_capabilities()
                self.model = self.vcp.get('model', 'N/A')
                source_obj = self.monitor.get_input_source()
                print(f"[DEBUG] Monitor {self.index} ({self.model}) get_input_source() raw: {repr(source_obj)}, type: {type(source_obj)}")
                self.current_source = source_obj.name if hasattr(source_obj, 'name') else str(source_obj)
                # If this is the buggy model, initialize software_source
                if self.is_ed32qur():
                    self.software_source = self.current_source
        except Exception as e:
            self.error = e
            print(f"Error initializing Monitor Index {self.index}: {type(e).__name__}: {e}")

    def is_ed32qur(self):
        return "ED32" in self.model.upper() and "QUR" in self.model.upper()

    def get_model(self):
        return self.model

    def get_current_source_str(self):
        # Use SmartThings if configured
        if self.use_smartthings and self.smartthings:
            source = self.smartthings.get_current_source()
            return source if source else "Unknown"
        
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
                    self.current_source = source_obj.name if hasattr(source_obj, 'name') else str(source_obj)
                    return self.current_source
            except Exception as e:
                if attempt < max_retries - 1:
                    import time
                    time.sleep(1)  # Wait before retry
                    continue
                print(f"Error checking source for Monitor {self.index}: {e}")
                return "Unknown (Error checking)"

    def set_input_source(self, desired_source_str, offline_mode=False):
        # Use local WebSocket control if offline_mode is enabled
        if self.use_smartthings and offline_mode:
            print(f"Setting Monitor Index {self.index} to source '{desired_source_str}' via LOCAL WebSocket...")
            try:
                from samsung_tizen_controller import SamsungTizenController
                import os
                
                # Save token in Windows AppData folder (proper location for app data)
                app_data_dir = os.path.join(os.environ.get('APPDATA', '.'), 'MonitorInputSwitch')
                os.makedirs(app_data_dir, exist_ok=True)  # Create folder if it doesn't exist
                token_file = os.path.join(app_data_dir, "samsung_g8_token.txt")
                print(f"[DEBUG] Token file location: {token_file}")
                
                controller = SamsungTizenController("192.168.0.52", token_file=token_file)
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
        
        # Use SmartThings cloud if configured and not in offline mode
        if self.use_smartthings and self.smartthings:
            print(f"Setting Monitor Index {self.index} (SmartThings) to source '{desired_source_str}'...")
            success = self.smartthings.set_input_source(desired_source_str)
            if success:
                self.current_source = desired_source_str
                print(f"Monitor Index {self.index} set successfully via SmartThings.")
            return success
        
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