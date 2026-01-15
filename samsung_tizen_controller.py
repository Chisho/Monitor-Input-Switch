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
        Switch monitor input using OSD menu navigation (blind macro strategy).
        
        Args:
            source: Input source name ("HDMI1", "HDMI2", "DP1", "USB-C", etc.)
            use_macro: If True, use OSD navigation. If False, try direct KEY_SOURCE.
        
        Returns:
            True if successful, False otherwise
        """
        if not self.tv:
            print("Not connected. Call connect() first.")
            return False
        
        # Normalize source name
        source_upper = source.upper()
        
        if use_macro:
            return self._switch_via_osd_macro(source_upper)
        else:
            # Try direct KEY_SOURCE command (may work on some firmware)
            return self.send_key("KEY_SOURCE")
    
    def _switch_via_osd_macro(self, source):
        """
        Navigate OSD menu to switch input source.
        Sends key sequence: HOME -> LEFT x3 -> DOWN to target -> ENTER
        
        Args:
            source: Input source name (HDMI1, HDMI2, DP1)
        
        Returns:
            True if sequence completed, False on error
        """
        import time
        
        # Map source to menu position (number of DOWN presses needed)
        # Assumes menu order: HDMI1, HDMI2, DisplayPort
        source_positions = {
            "HDMI1": {"down": 0, "right": 1},  # First item, one right
            "HDMI2": {"down": 1, "right": 1},  # Second item, one right  
            "DP1": {"down": 2, "right": 2},    # Third item, TWO rights
            "USB-C": {"down": 2, "right": 2},  # Same as DP1
        }
        
        nav_info = source_positions.get(source)
        if nav_info is None:
            print(f"Unknown source: {source}")
            return False
        
        down_count = nav_info["down"]
        right_count = nav_info["right"]
        
        try:
            print(f"Navigating OSD to switch to {source}...")
            
            # Step 1: Open home menu
            self.send_key("KEY_HOME")
            time.sleep(0.3)
            
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
