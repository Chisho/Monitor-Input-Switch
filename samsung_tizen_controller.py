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
    
    def __init__(self, ip_address, token_file="samsung_token.txt", initial_state="DP1"):
        """
        Initialize Samsung Tizen controller.
        
        Args:
            ip_address: IP address of the Samsung monitor
            token_file: Path to file for storing auth token
            initial_state: The current known state (HDMI1, DP1, etc.)
        """
        self.ip_address = ip_address
        self.token_file = token_file
        self.token = self._load_token()
        self.tv = None
        # Track current state (Initialized to DisplayPort/DP1 as requested)
        # Assuming typical setup: HDMI1 is Left, DP1 is Right
        self.current_app_state = self._normalize_state(initial_state)

    def _normalize_state(self, state):
        s = str(state).upper()
        if "HDMI" in s: return "HDMI1"
        if "DP" in s or "DISPLAYPORT" in s or "USB" in s: return "DP1"
        # Default
        return "DP1" 
        
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
        Switch monitor input using '123/Gear' Menu Navigation (Relative).
        Assumption: Cursor starts on current active source.
        Logic:
           HDMI -> DP : Move RIGHT
           DP -> HDMI : Move LEFT
        """
        if not self.tv:
            print("Not connected. Call connect() first.")
            return False
            
        # Normalize target
        target = source.upper()
        # Normalize internal state just in case
        current = self.current_app_state.upper()
        
        # Helper to categorize
        def is_hdmi(s): return "HDMI" in s
        def is_dp(s): return "DP" in s or "USB" in s or "DISPLAYPORT" in s
        
        print(f"Request source: {target} (Current State: {current})")
        
        import time
        
        try:
            print("Executing Input Switch Macro (Relative)...")
            
            # Step 1: Open Quick Menu
            self.send_key("KEY_MORE") 
            time.sleep(2.0)
            
            # Step 2: Enter 'Sources'
            self.send_key("KEY_ENTER")
            time.sleep(2.0)
            
            # Step 3: Relative Navigation
            # This assumes the cursor is currently ON the active source
            
            if is_hdmi(current) and is_dp(target):
                print("Action: Move RIGHT (HDMI -> DP)")
                self.send_key("KEY_RIGHT")
                time.sleep(0.5)
                
            elif is_dp(current) and is_hdmi(target):
                print("Action: Move LEFT (DP -> HDMI)")
                self.send_key("KEY_LEFT")
                time.sleep(0.5)
            
            else:
                print(f"No movement logic for {current} -> {target}. Selecting current.")

            # Step 4: Select
            self.send_key("KEY_ENTER")
            
            # Update internal state
            self.current_app_state = target
            print(f"State updated to: {self.current_app_state}")
            return True
            
        except Exception as e:
            print(f"Error executing macro: {e}")
            return False
            
        except Exception as e:
            print(f"Error executing macro: {e}")
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
