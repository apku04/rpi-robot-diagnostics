# Hardware Diagnostics Test Suite

A modular and extensible system for testing I2C peripherals connected via PCA9548A multiplexer.

## Overview

This diagnostic suite tests:
- ✅ PCA9548A I2C Multiplexer (8-channel)
- ✅ SHT31/SHT4x Temperature & Humidity Sensor
- ✅ BMP280/BME280 Temperature & Pressure Sensor
- ✅ SH1107/SH1106 OLED Displays (128x128)

## Quick Start

### Run Full Diagnostics
```bash
python3 run_diagnostics.py
```

### Run Quick Test (Skip Visual Tests)
```bash
python3 run_diagnostics.py --quick
```

### Run Silently (For Scripts)
```bash
python3 run_diagnostics.py --quiet
echo $?  # 0 = pass, 1 = fail
```

### List Available Tests
```bash
python3 run_diagnostics.py --list
```

## Test Modules

### Individual Test Execution

Each test module can be run standalone:

```bash
# Test I2C multiplexer
python3 test_multiplexer.py

# Test temperature sensors
python3 test_temperature.py

# Test OLED displays
python3 test_oled.py
```

### Module Structure

Each test module follows this structure:

```python
def run_test(**kwargs):
    """
    Run the test
    
    Returns:
        dict: {
            'status': 'pass'/'fail',
            'message': str,
            'error': str (optional),
            # Additional data specific to test
        }
    """
    result = {
        'status': 'pass',
        'message': 'Test result summary'
    }
    
    try:
        # Test implementation
        pass
    except Exception as e:
        result['status'] = 'fail'
        result['error'] = str(e)
    
    return result
```

## Hardware Configuration

### Current Setup

```
I2C Bus 1 (Default Raspberry Pi)
│
├── PCA9548A Multiplexer (0x70)
    │
    ├── Channel 0: SHT31 (0x44) - Temp & Humidity
    ├── Channel 1: BMP280 (0x76) - Temp & Pressure
    ├── Channel 2: OLED Display 1 (0x3D) - SH1107 128x128
    └── Channel 3: OLED Display 2 (0x3C) - SH1107 128x128
```

### Modify Hardware Config

Edit individual test modules to match your hardware:

**test_temperature.py:**
```python
SENSORS = [
    {'name': 'SHT31', 'channel': 0, 'address': 0x44, 'type': 'sht3x'},
    {'name': 'BMP280', 'channel': 1, 'address': 0x76, 'type': 'bme280'}
]
```

**test_oled.py:**
```python
OLEDS = [
    {'name': 'OLED_1', 'channel': 2, 'address': 0x3D},
    {'name': 'OLED_2', 'channel': 3, 'address': 0x3C'}
]
```

## Adding New Tests

### Step 1: Create Test Module

Create a new file `test_yourdevice.py`:

```python
#!/usr/bin/env python3
"""
Your Device Test Module
Description of what this tests
"""

def run_test(**kwargs):
    """
    Test your device
    
    Args:
        **kwargs: Optional arguments for test configuration
    
    Returns:
        dict: Test results with 'status' and 'message' keys
    """
    result = {
        'status': 'pass',
        'message': '',
    }
    
    try:
        # Your test implementation here
        # ...
        
        result['message'] = 'Device working correctly'
        
    except Exception as e:
        result['status'] = 'fail'
        result['error'] = str(e)
        result['message'] = 'Device test failed'
    
    return result

def main():
    """Standalone test execution"""
    print("Testing Your Device...")
    result = run_test()
    print(f"Status: {result['status']}")
    print(f"Message: {result['message']}")
    return 0 if result['status'] == 'pass' else 1

if __name__ == "__main__":
    exit(main())
```

### Step 2: Register Test in Diagnostics

Edit `run_diagnostics.py` and add to the `TESTS` list:

```python
TESTS = [
    # ... existing tests ...
    {
        'name': 'Your Device',
        'module': 'test_yourdevice',
        'critical': False,  # Set True if failure should stop all tests
        'enabled': True,    # Set False to disable without removing
        'args': {}          # Optional arguments passed to run_test()
    }
]
```

### Step 3: Test Your Addition

```bash
# List tests to verify it's registered
python3 run_diagnostics.py --list

# Run diagnostics
python3 run_diagnostics.py
```

## Boot-Time Diagnostics

### Method 1: Systemd Service

Create `/etc/systemd/system/hardware-diagnostics.service`:

```ini
[Unit]
Description=Hardware Diagnostics
After=network.target

[Service]
Type=oneshot
User=pi
WorkingDirectory=/home/acp/work
ExecStart=/usr/bin/python3 /home/acp/work/run_diagnostics.py --quiet
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable hardware-diagnostics.service
sudo systemctl start hardware-diagnostics.service

# Check status
sudo systemctl status hardware-diagnostics.service

# View logs
journalctl -u hardware-diagnostics.service
```

### Method 2: Cron Job (@reboot)

```bash
crontab -e

# Add this line:
@reboot sleep 30 && cd /home/acp/work && /usr/bin/python3 run_diagnostics.py >> /var/log/hardware-diagnostics.log 2>&1
```

### Method 3: rc.local

Add to `/etc/rc.local` (before `exit 0`):

```bash
# Run hardware diagnostics
cd /home/acp/work && /usr/bin/python3 run_diagnostics.py --quiet &
```

## Dependencies

### Required Python Packages
```bash
# Core I2C communication
sudo apt-get install python3-smbus python3-smbus2 i2c-tools

# OLED display support
sudo apt-get install python3-luma.oled python3-pil
```

### Enable I2C
```bash
# Enable I2C interface
sudo raspi-config
# Interface Options -> I2C -> Enable

# Or edit /boot/config.txt
sudo nano /boot/config.txt
# Add: dtparam=i2c_arm=on

# Reboot
sudo reboot
```

### Verify I2C
```bash
# Scan I2C bus
i2cdetect -y 1

# Expected output should show:
#      0  1  2  3  4  5  6  7  8  9  a  b  c  d  e  f
# 00:          -- -- -- -- -- -- -- -- -- -- -- -- -- 
# 10: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- 
# 20: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- 
# 30: -- -- -- -- -- -- -- -- -- -- -- -- 3c 3d -- -- 
# 40: -- -- -- -- 44 -- -- -- -- -- -- -- -- -- -- -- 
# 50: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- 
# 60: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- 
# 70: 70 -- -- -- -- -- -- 76
```

## File Structure

```
work/
├── run_diagnostics.py       # Main diagnostic runner
├── test_multiplexer.py      # PCA9548A multiplexer test
├── test_temperature.py      # Temperature sensor tests
├── test_oled.py             # OLED display tests
├── README.md                # This file
│
# Legacy/standalone test files (optional)
├── quick_test.py            # Quick I2C scan
├── test_i2c_setup.py        # Comprehensive I2C test
├── test_temp_sensors.py     # Interactive temp sensor test
└── test_oled_displays.py    # Interactive OLED test
```

## Troubleshooting

### I2C Device Not Found

```bash
# Check I2C is enabled
ls -l /dev/i2c*

# Scan bus
i2cdetect -y 1

# Check permissions
sudo usermod -a -G i2c $USER
# Logout and login again
```

### Module Import Errors

```bash
# Check Python can find modules
python3 -c "import smbus; print('smbus OK')"
python3 -c "from luma.oled.device import sh1106; print('luma OK')"

# Install missing packages
sudo apt-get install python3-smbus python3-luma.oled python3-pil
```

### Multiplexer Issues

```bash
# Verify multiplexer responds
i2cget -y 1 0x70

# Should return a value, not an error
```

### Display Not Working

```bash
# Test basic I2C communication
python3 test_oled.py

# If communication works but display doesn't show anything:
# - Check display power connections
# - Verify display address (0x3C or 0x3D)
# - Try different SH1106/SSD1306 driver
```

## Integration Examples

### Python Script Integration

```python
#!/usr/bin/env python3
import sys
sys.path.append('/home/acp/work')

from run_diagnostics import run_diagnostics

# Run diagnostics
exit_code = run_diagnostics(verbose=False, quick=True)

if exit_code == 0:
    print("All systems operational")
    # Continue with your application
else:
    print("Hardware failure detected")
    # Handle error condition
```

### Shell Script Integration

```bash
#!/bin/bash

cd /home/acp/work
python3 run_diagnostics.py --quiet

if [ $? -eq 0 ]; then
    echo "Hardware OK - Starting application"
    # Start your application
else
    echo "Hardware diagnostics failed"
    exit 1
fi
```

### Import Individual Tests

```python
#!/usr/bin/env python3
import sys
sys.path.append('/home/acp/work')

import test_temperature

# Run temperature test
result = test_temperature.run_test()

if result['status'] == 'pass':
    # Access sensor data
    for sensor_name, data in result['sensors'].items():
        if data['success']:
            temp = data['temperature']
            print(f"{sensor_name}: {temp:.1f}°C")
```

## API Reference

### run_diagnostics()

Main diagnostic function.

**Arguments:**
- `verbose` (bool): Print detailed output (default: True)
- `quick` (bool): Skip slower tests (default: False)

**Returns:**
- `int`: Exit code (0 = pass, 1 = fail)

**Example:**
```python
from run_diagnostics import run_diagnostics
exit_code = run_diagnostics(verbose=True, quick=False)
```

### Test Module API

All test modules implement:

**run_test(**kwargs) -> dict**

**Returns dict with:**
- `status` (str): 'pass' or 'fail'
- `message` (str): Human-readable summary
- `error` (str): Error message if failed (optional)
- Additional test-specific data

## License

MIT License - Feel free to use and modify

## Contributing

When adding new test modules:
1. Follow the existing module structure
2. Implement `run_test()` with standard return format
3. Include standalone `main()` for direct execution
4. Update this README with configuration details
5. Add comprehensive docstrings

## Support

For issues or questions:
- Check I2C connections and addresses
- Review `i2cdetect -y 1` output
- Run individual test modules for detailed output
- Check system logs: `journalctl -xe`

---

**Last Updated:** November 2025
**Version:** 1.0
