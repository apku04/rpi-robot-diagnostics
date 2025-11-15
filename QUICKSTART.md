# Hardware Diagnostics - Quick Reference

## Quick Commands

```bash
# Run full diagnostics
python3 run_diagnostics.py

# Run quick test (skip visual tests)
python3 run_diagnostics.py --quick

# Run silently (for scripts)
python3 run_diagnostics.py --quiet

# List available tests
python3 run_diagnostics.py --list

# Test individual components
python3 test_multiplexer.py
python3 test_temperature.py
python3 test_oled.py
```

## Hardware Setup

| Channel | Device | Address | Description |
|---------|--------|---------|-------------|
| - | PCA9548A | 0x70 | I2C Multiplexer |
| 0 | SHT31 | 0x44 | Temp & Humidity |
| 1 | BMP280 | 0x76 | Temp & Pressure |
| 2 | OLED 1 | 0x3D | Display 128x128 |
| 3 | OLED 2 | 0x3C | Display 128x128 |

## Python Integration

### Simple Check
```python
from run_diagnostics import run_diagnostics

if run_diagnostics(verbose=False, quick=True) == 0:
    print("Hardware OK")
else:
    print("Hardware Failed")
```

### Individual Test
```python
import test_temperature

result = test_temperature.run_test()
if result['status'] == 'pass':
    for name, data in result['sensors'].items():
        print(f"{name}: {data['temperature']:.1f}°C")
```

## File Structure

```
work/
├── run_diagnostics.py       # Main runner
├── test_multiplexer.py      # Multiplexer test
├── test_temperature.py      # Temperature test
├── test_oled.py             # OLED test
├── example_usage.py         # Integration examples
└── README.md                # Full documentation
```

## Adding New Tests

1. Create `test_newdevice.py` with `run_test()` function
2. Edit `run_diagnostics.py` TESTS list:
```python
{
    'name': 'New Device',
    'module': 'test_newdevice',
    'critical': False,
    'enabled': True
}
```

## Boot-Time Setup

### Systemd Service
```bash
sudo nano /etc/systemd/system/hardware-diagnostics.service
```
```ini
[Unit]
Description=Hardware Diagnostics
After=network.target

[Service]
Type=oneshot
User=pi
WorkingDirectory=/home/acp/work
ExecStart=/usr/bin/python3 /home/acp/work/run_diagnostics.py --quiet

[Install]
WantedBy=multi-user.target
```
```bash
sudo systemctl enable hardware-diagnostics.service
```

### Cron @reboot
```bash
crontab -e
# Add:
@reboot sleep 30 && cd /home/acp/work && python3 run_diagnostics.py >> /var/log/diagnostics.log 2>&1
```

## Troubleshooting

```bash
# Check I2C is enabled
ls /dev/i2c*

# Scan I2C bus
i2cdetect -y 1

# Test I2C permissions
groups | grep i2c

# Add user to i2c group
sudo usermod -a -G i2c $USER
```

## Exit Codes

- `0` = All tests passed
- `1` = One or more tests failed

## Common Issues

**Device not found:**
- Check connections
- Run `i2cdetect -y 1`
- Verify addresses in test module

**Import errors:**
- `sudo apt-get install python3-smbus python3-luma.oled python3-pil`

**Permission denied:**
- Add user to i2c group
- Logout and login

---
Last Updated: November 2025
