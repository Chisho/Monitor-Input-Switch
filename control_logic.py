import time

def toggle_monitor_input(monitor, offline_mode=False):
    """
    Toggle a monitor's input between DP1 and HDMI1.
    
    Args:
        monitor: Monitor object to control
        offline_mode: If True, use local WebSocket control (for Samsung G8)
    
    Returns: (bool, str) - (success, new_source)
    """
    print(f"Action: Toggle input for monitor {monitor.index} ({monitor.get_model()})")
    if offline_mode:
        print("  Using OFFLINE mode (local WebSocket)")
    
    current_source = str(monitor.get_current_source_str())
    
    # Normalize for robust comparison (handle "HDMI 1" vs "HDMI1")
    src_upper = current_source.upper().replace(" ", "").replace("-", "")
    
    # Determine Target
    if "HDMI" in src_upper:
        # Switch to DP
        # InputSource.DP1 = 15. "DP1" is the correct attribute name for monitorcontrol.
        new_source = "DP1"
    else:
        # Switch to HDMI
        # InputSource.HDMI1 = 17. "HDMI1" is the correct attribute name.
        new_source = "HDMI1"
            
    print(f"  Analysis: Current='{current_source}' -> New='{new_source}'")
    
    success = monitor.set_input_source(new_source, offline_mode=offline_mode)
    if not success:
        raise RuntimeError(f"Monitor {monitor.index} failed to switch to {new_source}")
    
    # Add delay to allow monitor to stabilize after input switch
    time.sleep(2)
    return success, new_source