"""
Samsung G8 Monitor Local Control via Tizen WebSocket API
Uses samsungtvws library to launch Tizen apps corresponding to input sources.
Works entirely on local network - NO cloud/internet required.
"""

import os
import json
from samsungtvws import SamsungTVWS

class SamsungTizenController:
    """Local control for Samsung G8 monitor via Tizen app launching"""
    
    # Tizen app IDs for input sources on G8 OLED
    INPUT_APP_MAP = {
        "HDMI1": "org.tizen.viewer.hdmi1",
        "HDMI2": "org.tizen.viewer.hdmi2", 
        "DP1": "org.tizen.viewer.dp1",
        "USB-C": "org.tizen.viewer.dp1",  # DP1 is usually USB-C on G8
    }
    
    def __init__(self, ip_address, token_file="samsung_token.txt"):
        """
        Initialize Samsung Tizen controller.
        
        Args:
            ip_address: IP address of the Samsung monitor
            token_file: Path to file for storing auth token
        """
        self.ip_address = ip_address
        self.token_file = token_file
        self.token = self._load_token()
        self.tv = None
        # Track current state (Initialized to DisplayPort/DP1 as requested)
        # Assuming typical setup: HDMI1 is Left, DP1 is Right
        self.current_app_state = "DP1" 
        
    def _load_token(self):
        """Load saved token from file."""
        if os.path.exists(self.token_file):
            try:
                with open(self.token_file, 'r') as f:
                    return f.read().strip()
            except:
                pass
        return None
    
    def _save_token(self, token):
        """Save token to file for future use."""
        try:
            with open(self.token_file, 'w') as f:
                f.write(token)
            print(f"Token saved to {self.token_file}")
        except Exception as e:
            print(f"Warning: Could not save token: {e}")
    
    def connect(self):
        """
        Establish connection to the monitor.
        On first run, user must accept the pairing popup on the monitor.
        
        Returns:
            True if connected, False otherwise
        """
        try:
            print(f"Connecting to {self.ip_address}:8002...")
            
            # Create connection with token_file (library handles token saving/loading)
            self.tv = SamsungTVWS(
                host=self.ip_address,
                port=8002,
                token_file=self.token_file,  # Let library manage token
                timeout=30,
                name="MonitorSwitcher"
            )
            
            # Test connection by getting device info
            info = self.tv.rest_device_info()
            print(f"✓ Connected to: {info.get('device', {}).get('name', 'Samsung Monitor')}")
            
            return True
            
        except Exception as e:
            if "unauthorized" in str(e).lower():
                print("\n⚠️  PAIRING REQUIRED!")
                print("Check your Samsung G8 monitor screen for a popup.")
                print("Use the monitor's remote/buttons to select 'Allow'.")
                print("Then run this script again.")
            else:
                print(f"Connection error: {e}")
            return False
    
    def set_input_source(self, source, use_macro=True):
        """
        Switch monitor input using '123/Gear' Menu Navigation.
        Strategy: Gear -> Enter -> Sources Menu -> Move Left/Right -> Enter
        
        Assumption: HDMI1 is Left, DP1 is Right.
        Initialized to DP1.
        """
        if not self.tv:
            print("Not connected. Call connect() first.")
            return False
            
        # Normalize: Treat USB-C same as DP1, etc.
        target = source.upper()
        if "HDMI" in target: target = "HDMI1" # Simplify to just HDMI vs DP logic
        if "DP" in target or "USB" in target: target = "DP1"
        
        print(f"Request source: {target} (Current State: {self.current_app_state})")
        
        if target == self.current_app_state:
            print("Already on target source (internal state). Skipping macro.")
            return True
            
        import time
        
        try:
            print("Executing Input Switch Macro (Gear -> Enter -> Nav -> Enter)...")
            
            # Step 1: Open Quick Menu (Gear/123 button)
            # KEY_MORE is typically the '123/Color' button on smart remotes
            self.send_key("KEY_MORE") 
            time.sleep(1.0) # Wait for menu
            
            # Step 2: Enter 'Sources' (User says pressing Enter goes to sources)
            self.send_key("KEY_ENTER")
            time.sleep(1.0) # Wait for source list to appear
            
            # Step 3: Navigation logic
            # Current theory: HDMI1 (Left) <-> DP1 (Right)
            
            # If we are currently at HDMI1 (Left) and want DP1 (Right)
            if self.current_app_state == "HDMI1" and target == "DP1":
                print("Moving Right (HDMI1 -> DP1)")
                self.send_key("KEY_RIGHT")
                
            # If we are currently at DP1 (Right) and want HDMI1 (Left)
            elif self.current_app_state == "DP1" and target == "HDMI1":
                 print("Moving Left (DP1 -> HDMI1)")
                 self.send_key("KEY_LEFT")
            
            time.sleep(0.5)
            
            # Step 4: Select
            self.send_key("KEY_ENTER")
            
            # Update internal state only if success
            self.current_app_state = target
            print(f"State updated to: {self.current_app_state}")
            return True
            
        except Exception as e:
            print(f"Error executing macro: {e}")
            return False

    def send_key(self, key_code):
            # Step 2: Navigate to sidebar (press LEFT multiple times)
            for _ in range(3):
                self.send_key("KEY_LEFT")
                time.sleep(0.1)
            
            time.sleep(0.2)
            
            # Step 3: Navigate down to "Connected Devices" or input list
            self.send_key("KEY_DOWN")  # Move to Connected Devices
            time.sleep(0.1)
            self.send_key("KEY_ENTER")  # Open it
            time.sleep(0.3)
            
            # Step 4: Navigate to specific input
            if down_count > 0:
                for _ in range(down_count):
                    self.send_key("KEY_DOWN")
                    time.sleep(0.1)
            
            # Step 5: Move right to the input item (DP needs 2 rights)
            for _ in range(right_count):
                self.send_key("KEY_RIGHT")
                time.sleep(0.1)
            
            # Step 6: Select the input
            self.send_key("KEY_ENTER")
            self.send_key("KEY_ENTER")
            time.sleep(0.2)
            
            print(f"✓ OSD navigation sequence complete for {source}")
            print("  (Monitor should switch in 1-2 seconds)")
            return True
            
        except Exception as e:
            print(f"Failed to execute OSD macro: {e}")
            return False
    
    def get_installed_apps(self):
        """
        Get list of installed Tizen apps on the monitor.
        Useful for discovering the correct input app IDs.
        
        Returns:
            List of app info dictionaries
        """
        if not self.tv:
            print("Not connected. Call connect() first.")
            return []
        
        try:
            apps = self.tv.app_list()
            return apps
        except Exception as e:
            print(f"Failed to get app list: {e}")
            return []
    
    def send_key(self, key_code):
        """
        Send a remote control key press (fallback method).
        
        Args:
            key_code: Samsung key code (e.g., "KEY_SOURCE", "KEY_HOME")
        
        Returns:
            True if successful, False otherwise
        """
        if not self.tv:
            print("Not connected. Call connect() first.")
            return False
        
        try:
            self.tv.send_key(key_code)
            return True
        except Exception as e:
            print(f"Failed to send key {key_code}: {e}")
            return False
    
    def disconnect(self):
        """Close connection."""
        if self.tv:
            try:
                self.tv.close()
            except:
                pass
            self.tv = None


# Test/demo code
if __name__ == "__main__":
    print("=" * 70)
    print("Samsung G8 Monitor - Local Tizen Control Test")
    print("=" * 70)
    print()
    
    # Configuration
    monitor_ip = input("Enter monitor IP address (e.g., 192.168.0.52): ").strip()
    
    if not monitor_ip:
        print("No IP provided")
        exit(1)
    
    # Create controller
    controller = SamsungTizenController(monitor_ip)
    
    # Connect
    print("\n[1/4] Connecting to monitor...")
    if not controller.connect():
        print("\n❌ Connection failed")
        exit(1)
    
    print("\n[2/4] Getting installed apps...")
    apps = controller.get_installed_apps()
    
    if apps:
        print(f"Found {len(apps)} installed apps")
        print("\nInput-related apps:")
        for app in apps:
            app_id = app.get('appId', '')
            name = app.get('name', 'Unknown')
            if 'hdmi' in app_id.lower() or 'dp' in app_id.lower() or 'viewer' in app_id.lower():
                print(f"  - {name}: {app_id}")
    else:
        print("Could not retrieve app list (may not be supported)")
    
    print("\n[3/4] Testing input switching...")
    print("Available inputs:", ", ".join(controller.INPUT_APP_MAP.keys()))
    
    test_input = input("\nWhich input to test? (e.g., HDMI1, DP1): ").strip()
    
    if test_input:
        controller.set_input_source(test_input)
        print("\nCheck your monitor - did the input switch?")
    
    print("\n[4/4] Cleanup...")
    controller.disconnect()
    
    print("\n✓ Test complete!")
    print("\nIf input switching worked, your monitor supports local control!")
    print("If not, we'll need to stick with the SmartThings cloud API.")
