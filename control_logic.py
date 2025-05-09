import time

def toggle_monitor_input(monitor):
    """
    Toggle a monitor's input between DP1 and HDMI1.
    Returns: (bool, str) - (success, new_source)
    """
    print(f"Action: Toggle input for monitor {monitor.index} ({monitor.get_model()})")
    current_source = monitor.get_current_source_str()
    new_source = "DP1" if current_source == "HDMI1" else "HDMI1"
    
    success = monitor.set_input_source(new_source)
    if not success:
        raise RuntimeError(f"Monitor {monitor.index} failed to switch to {new_source}")
    
    # Add delay to allow monitor to stabilize after input switch
    time.sleep(2)
    return success, new_source