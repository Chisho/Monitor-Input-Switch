from monitorcontrol import get_monitors
import traceback

class MyMonitor:
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
            print(f"Error initializing Monitor Index {self.index}: {type(e).__name__}: {e}")

    def get_model(self):
        return self.model

    def get_current_source_str(self):
        if self.error: 
            return "Error"
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                with self.monitor:
                    source_obj = self.monitor.get_input_source()
                    self.current_source = source_obj.name if hasattr(source_obj, 'name') else str(source_obj)
                    return self.current_source
            except Exception as e:
                if attempt < max_retries - 1:
                    import time
                    time.sleep(1)  # Wait before retry
                    continue
                print(f"Error checking source for Monitor {self.index}: {e}")
                return "Unknown (Error checking)"

    def set_input_source(self, desired_source_str):
        if self.error:
            print(f"Monitor Index {self.index} ({self.get_model()}) had an initialization error. Cannot set source.")
            return False
        try:
            with self.monitor:
                print(f"Setting Monitor Index {self.index} ({self.get_model()}) to source '{desired_source_str}'...")
                self.monitor.set_input_source(desired_source_str)
                self.current_source = desired_source_str
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
            mon = MyMonitor(i, monitor_obj)
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