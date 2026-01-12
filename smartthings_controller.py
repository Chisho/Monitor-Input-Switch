"""
SmartThings API controller for Samsung monitors that support SmartThings integration.
This module handles input switching for monitors that don't support VCP/DDC-CI.
"""

import requests
import json
import os
import sys


def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


class SmartThingsController:
    """Controller for Samsung monitors via SmartThings API."""
    
    def __init__(self, device_id=None, api_token=None):
        """
        Initialize SmartThings controller.
        
        Args:
            device_id: SmartThings device ID (optional, will try to load from config)
            api_token: SmartThings API token (optional, will try to load from config)
        """
        self.base_url = "https://api.smartthings.com/v1"
        self.device_id = device_id
        self.api_token = api_token
        self.current_source = None
        
        # Try to load from config if not provided
        if not self.device_id or not self.api_token:
            self._load_config()
    
    def _load_config(self):
        """Load SmartThings credentials from config file."""
        config_path = resource_path("smartthings_config.json")
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    config = json.load(f)
                    self.device_id = config.get('device_id', self.device_id)
                    self.api_token = config.get('api_token', self.api_token)
                    print(f"[SmartThings] Loaded config from {config_path}")
            except Exception as e:
                print(f"[SmartThings] Error loading config: {e}")
        else:
            print(f"[SmartThings] Config file not found at {config_path}")
    
    def _get_headers(self):
        """Get HTTP headers for SmartThings API requests."""
        return {
            'Authorization': f'Bearer {self.api_token}',
            'Content-Type': 'application/json'
        }
    
    def is_configured(self):
        """Check if SmartThings is properly configured."""
        return bool(self.device_id and self.api_token)
    
    def get_current_source(self):
        """
        Get the current input source from the monitor.
        
        Returns:
            str: Current input source name (e.g., "HDMI1", "DP1") or None if error
        """
        if not self.is_configured():
            print("[SmartThings] Not configured - missing device_id or api_token")
            return None
        
        try:
            url = f"{self.base_url}/devices/{self.device_id}/status"
            response = requests.get(url, headers=self._get_headers(), timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                # Try samsungvd.mediaInputSource first (more reliable for Samsung monitors)
                try:
                    input_source = data['components']['main']['samsungvd.mediaInputSource']['inputSource']['value']
                    self.current_source = self._normalize_source_name(input_source)
                    print(f"[SmartThings] Current source: {self.current_source} (raw: {input_source})")
                    return self.current_source
                except KeyError:
                    pass
                
                # Fall back to standard mediaInputSource
                try:
                    input_source = data['components']['main']['mediaInputSource']['inputSource']['value']
                    self.current_source = self._normalize_source_name(input_source)
                    print(f"[SmartThings] Current source: {self.current_source} (raw: {input_source})")
                    return self.current_source
                except KeyError:
                    print(f"[SmartThings] Could not parse input source from response")
                    return self.current_source
            else:
                print(f"[SmartThings] Error getting status: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            print(f"[SmartThings] Exception getting current source: {e}")
            return None
    
    def set_input_source(self, source):
        """
        Set the input source on the monitor.
        
        Args:
            source: Input source name (e.g., "HDMI1", "HDMI2", "DP1", "DP2")
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.is_configured():
            print("[SmartThings] Not configured - missing device_id or api_token")
            return False
        
        # Convert our standard names to SmartThings format
        st_source = self._to_smartthings_source(source)
        
        try:
            url = f"{self.base_url}/devices/{self.device_id}/commands"
            
            payload = {
                "commands": [
                    {
                        "component": "main",
                        "capability": "samsungvd.mediaInputSource",
                        "command": "setInputSource",
                        "arguments": [st_source]
                    }
                ]
            }
            
            print(f"[SmartThings] Setting input to {source} (SmartThings: {st_source})")
            response = requests.post(url, headers=self._get_headers(), 
                                   json=payload, timeout=10)
            
            if response.status_code in [200, 201]:
                print(f"[SmartThings] Successfully set input to {source}")
                self.current_source = source
                return True
            else:
                print(f"[SmartThings] Error setting input: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print(f"[SmartThings] Exception setting input: {e}")
            return False
    
    def _normalize_source_name(self, st_source):
        """
        Convert SmartThings source name to our standard format.
        
        Args:
            st_source: SmartThings source name (varies by device)
            
        Returns:
            str: Normalized source name (HDMI1, HDMI2, DP1, etc.)
        """
        if st_source is None:
            return "Unknown"
        
        st_source_upper = st_source.upper()
        
        # Common mappings
        mappings = {
            'HDMI1': 'HDMI1',
            'HDMI2': 'HDMI2',
            'HDMI3': 'HDMI3',
            'HDMI': 'HDMI1',
            'DISPLAY PORT': 'DP1',
            'DISPLAYPORT1': 'DP1',
            'DISPLAYPORT2': 'DP2',
            'DISPLAYPORT': 'DP1',
            'DP1': 'DP1',
            'DP2': 'DP2',
            'PC': 'DP1',  # Some Samsung monitors call DP "PC"
            'USB-C': 'USB-C',
        }
        
        # Try direct mapping first
        for key, value in mappings.items():
            if key in st_source_upper:
                return value
        
        # Return original if no mapping found
        return st_source
    
    def _to_smartthings_source(self, source):
        """
        Convert our standard source name to SmartThings format.
        
        Args:
            source: Our standard source name (HDMI1, DP1, etc.)
            
        Returns:
            str: SmartThings compatible source name
        """
        source_upper = source.upper()
        
        # Map to SmartThings format (varies by device, these are common)
        # Using samsungvd.mediaInputSource which accepts custom strings
        # Based on GitHub issue: https://github.com/ollo69/ha-samsungtv-smart/issues/274
        # Samsung G8 uses "Display Port" (with space, capitalized) for DisplayPort
        mappings = {
            'HDMI1': 'HDMI1',
            'HDMI2': 'HDMI2',
            'HDMI3': 'HDMI3',
            'DP1': 'Display Port',  # G8 DisplayPort - must match ID from supportedInputSourcesMap
            'DP2': 'DisplayPort2',
            'USB-C': 'USB-C',
        }
        
        return mappings.get(source_upper, source)
