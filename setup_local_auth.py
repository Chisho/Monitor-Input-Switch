import sys
import json
import logging
import time
import ssl
import os
from samsung_tizen_controller import SamsungTizenController

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(message)s')

def save_local_config(ip, mac, name):
    config = {
        "use_local_control": True,
        "monitor_ip": ip,
        "monitor_mac": mac,
        "monitor_name": name
    }
    with open("local_config.json", "w") as f:
        json.dump(config, f, indent=4)
    print(f"\n✅ Configuration saved to local_config.json")

def discover_tvs():
    # Simple SSDP discovery or just ask user for IP
    pass

if __name__ == "__main__":
    print("="*60)
    print("Samsung Monitor - Local Network Setup (Tizen)")
    print("="*60)
    print("This will pair with your monitor via your local network (Wi-Fi/Ethernet).")
    print("NOTE: The monitor must be ON and connected to the same network.")
    print("NOTE: You will need to click 'Allow' on the Monitor screen during this process.")
    
    ip_address = input("\nEnter Monitor IP Address (e.g., 192.168.1.50): ").strip()
    if not ip_address:
        print("IP address required. Exiting.")
        sys.exit(1)
        
    print(f"\nAttempting to connect to {ip_address}...")
    
    # Define Token Path (AppData) to match App behavior
    app_data_dir = os.path.join(os.environ.get('APPDATA', '.'), 'MonitorInputSwitch')
    os.makedirs(app_data_dir, exist_ok=True)
    token_file = os.path.join(app_data_dir, "samsung_g8_token.txt")
    print(f"Token will be saved to: {token_file}")
    
    # Try one connection to trigger the Auth popup
    controller = SamsungTizenController(ip_address, token_file=token_file)
    
    print("\n--> Please look at your Monitor now!")
    print("--> Use the remote to select 'Allow' if asked.")
    
    try:
        # Connect triggers the auth flow
        if controller.connect():
            print("\n✅ Success! Paired with monitor.")
            
            # The token is handled automatically by the library and saved to samsung_token.txt by default
            
            save_local_config(ip_address, "Unknown-MAC", "Samsung Monitor")
            
            print("\nYou can now build the EXE or run the app.")
        else:
            print("\n❌ Failed to connect. Did you click Allow?")
            
    except Exception as e:
        print(f"\nError: {e}")
        print("Make sure the Monitor is ON and you entered the correct IP.")
