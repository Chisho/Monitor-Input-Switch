# Samsung Odyssey G8 SmartThings Setup Guide

Your Samsung Odyssey G8 will now be controlled via the SmartThings API instead of VCP/DDC-CI!

## Quick Setup (5 minutes)

### Step 1: Get Your SmartThings API Token
1. Go to: https://account.smartthings.com/tokens
2. Sign in with your Samsung account
3. Click "Generate new token"
4. Give it a name (e.g., "Monitor Control")
5. Select the following permissions:
   - **Devices** (List all devices, See all devices, Control all devices)
6. Click "Generate token"
7. **IMPORTANT**: Copy the token immediately (you won't see it again!)

### Step 2: Find Your Monitor's Device ID
Run this command in PowerShell:
```powershell
D:/PythonProjects/MonitorInputSwitch/.venv/Scripts/python.exe get_smartthings_info.py
```

This will:
- Ask for your API token
- List all your SmartThings devices
- Show your monitor's Device ID and supported inputs

### Step 3: Configure the App
1. Open `smartthings_config.json` in this folder
2. Replace `YOUR_DEVICE_ID_HERE` with your monitor's Device ID (from Step 2)
3. Replace `YOUR_API_TOKEN_HERE` with your API token (from Step 1)
4. Remove the `"instructions"` section (optional)
5. Save the file

Your config should look like this:
```json
{
    "device_id": "12345678-abcd-1234-abcd-123456789abc",
    "api_token": "a1b2c3d4-1234-5678-90ab-cdef12345678"
}
```

### Step 4: Test It!
Run your monitor control app:
```powershell
D:/PythonProjects/MonitorInputSwitch/.venv/Scripts/python.exe app_ui.py
```

Monitor Index 3 (your G8) should now show "Samsung (SmartThings)" as the model and will switch inputs via the cloud API!

## How It Works

- **Monitors 0, 1, 2**: Use traditional VCP/DDC-CI control (local, instant)
- **Monitor 3 (G8)**: Uses SmartThings cloud API (requires internet, ~1-2 second delay)

The app automatically detects which method to use for each monitor.

## Troubleshooting

### "SmartThings not configured"
- Check that `smartthings_config.json` exists and has valid credentials
- Run `get_smartthings_info.py` to verify your token works

### "Error getting status: 401"
- Your API token is invalid or expired
- Generate a new token at https://account.smartthings.com/tokens

### "Error getting status: 404"
- Your device_id is incorrect
- Run `get_smartthings_info.py` to get the correct device ID

### Monitor doesn't switch
- Check that your G8 is online in the SmartThings app
- Verify the input sources match what SmartThings supports
- Check the console output for detailed error messages

## Input Source Names

SmartThings uses these input source names (your G8 may vary):
- `HDMI1`, `HDMI2` - HDMI ports
- `DisplayPort1`, `DisplayPort2` - DisplayPort
- `USB-C` - USB-C input (if available)

The app automatically converts between internal names (HDMI1, DP1) and SmartThings names.

## Security Note

Your API token gives access to control your SmartThings devices. Keep it secure:
- Don't share `smartthings_config.json` publicly
- Add it to `.gitignore` if using version control
- Revoke old tokens at https://account.smartthings.com/tokens if needed

## Need Help?

Check the console output when running the app - it shows detailed debug information about:
- Which monitors use VCP vs SmartThings
- Current input sources
- API requests and responses
- Any errors that occur
