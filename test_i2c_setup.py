#!/usr/bin/env python3
"""
Test script for I2C setup with PCA9548A multiplexer
Connected devices:
- Temperature sensors
- Temperature/Humidity sensors
- 2 OLED LCD displays
"""

import time
import sys

try:
    import smbus2 as smbus
except ImportError:
    import smbus

# I2C Configuration
I2C_BUS = 1  # Default I2C bus for Raspberry Pi
PCA9548A_ADDR = 0x70  # Default address for PCA9548A multiplexer

# Common sensor addresses
TEMP_SENSOR_ADDRS = [0x48, 0x49, 0x4A, 0x4B]  # Common temp sensor addresses (like TMP102, LM75)
TEMP_HUM_ADDRS = [0x40, 0x44, 0x76, 0x77]  # Common temp/humidity sensors (HTU21D, SHT31, BME280)
OLED_ADDRS = [0x3C, 0x3D]  # Common OLED display addresses (SSD1306)

class PCA9548A:
    """PCA9548A I2C Multiplexer"""
    
    def __init__(self, bus, address=0x70):
        self.bus = bus
        self.address = address
    
    def select_channel(self, channel):
        """Select a channel (0-7) on the multiplexer"""
        if channel < 0 or channel > 7:
            raise ValueError("Channel must be between 0 and 7")
        self.bus.write_byte(self.address, 1 << channel)
        time.sleep(0.01)  # Small delay for channel switching
    
    def disable_all_channels(self):
        """Disable all channels"""
        self.bus.write_byte(self.address, 0x00)
        time.sleep(0.01)
    
    def get_current_channel(self):
        """Read current channel configuration"""
        return self.bus.read_byte(self.address)


def scan_i2c_bus(bus):
    """Scan I2C bus for devices"""
    devices = []
    print("Scanning I2C bus...")
    for addr in range(0x03, 0x78):
        try:
            bus.read_byte(addr)
            devices.append(addr)
            print(f"  Found device at 0x{addr:02X}")
        except:
            pass
    return devices


def test_multiplexer(bus, mux_addr):
    """Test PCA9548A multiplexer"""
    print(f"\n{'='*60}")
    print("Testing PCA9548A Multiplexer")
    print(f"{'='*60}")
    
    try:
        mux = PCA9548A(bus, mux_addr)
        
        # Test reading current state
        current = mux.get_current_channel()
        print(f"✓ Multiplexer found at 0x{mux_addr:02X}")
        print(f"  Current channel state: 0b{current:08b}")
        
        # Disable all channels
        mux.disable_all_channels()
        print("✓ All channels disabled")
        
        return mux
    except Exception as e:
        print(f"✗ Error accessing multiplexer: {e}")
        return None


def scan_mux_channels(bus, mux, num_channels=8):
    """Scan each channel of the multiplexer for devices"""
    print(f"\n{'='*60}")
    print("Scanning Multiplexer Channels")
    print(f"{'='*60}")
    
    channel_devices = {}
    
    for channel in range(num_channels):
        print(f"\nChannel {channel}:")
        try:
            mux.select_channel(channel)
            devices = []
            
            for addr in range(0x03, 0x78):
                if addr == mux.address:
                    continue
                try:
                    bus.read_byte(addr)
                    devices.append(addr)
                    print(f"  ✓ Device found at 0x{addr:02X}")
                except:
                    pass
            
            if not devices:
                print("  (No devices found)")
            
            channel_devices[channel] = devices
            
        except Exception as e:
            print(f"  ✗ Error scanning channel {channel}: {e}")
            channel_devices[channel] = []
    
    mux.disable_all_channels()
    return channel_devices


def test_temperature_sensor(bus, mux, channel, addr):
    """Test temperature sensor (generic)"""
    print(f"\n  Testing temperature sensor on channel {channel} at 0x{addr:02X}...")
    
    try:
        mux.select_channel(channel)
        
        # Try reading temperature (works for many sensors like LM75, TMP102)
        data = bus.read_i2c_block_data(addr, 0x00, 2)
        temp = ((data[0] << 8) | data[1]) >> 4
        if temp > 2047:
            temp -= 4096
        temp = temp * 0.0625
        
        print(f"    ✓ Temperature: {temp:.2f}°C")
        return True
    except Exception as e:
        print(f"    ⚠ Could not read temperature: {e}")
        return False


def test_oled_display(bus, mux, channel, addr):
    """Test OLED display (SSD1306 compatible)"""
    print(f"\n  Testing OLED display on channel {channel} at 0x{addr:02X}...")
    
    try:
        mux.select_channel(channel)
        
        # Try to read from display
        bus.read_byte(addr)
        print(f"    ✓ OLED display responding")
        
        # Optional: Try to initialize display (commented out to avoid changing display state)
        # bus.write_i2c_block_data(addr, 0x00, [0xAE])  # Display off command
        
        return True
    except Exception as e:
        print(f"    ⚠ Could not communicate with OLED: {e}")
        return False


def identify_devices(channel_devices):
    """Try to identify what type of device is on each channel"""
    print(f"\n{'='*60}")
    print("Device Identification")
    print(f"{'='*60}")
    
    device_map = {
        'temperature_sensors': [],
        'temp_humidity_sensors': [],
        'oled_displays': [],
        'unknown': []
    }
    
    for channel, devices in channel_devices.items():
        if not devices:
            continue
            
        print(f"\nChannel {channel}:")
        for addr in devices:
            if addr in OLED_ADDRS:
                print(f"  0x{addr:02X} - Likely OLED Display (SSD1306)")
                device_map['oled_displays'].append((channel, addr))
            elif addr in TEMP_SENSOR_ADDRS:
                print(f"  0x{addr:02X} - Likely Temperature Sensor")
                device_map['temperature_sensors'].append((channel, addr))
            elif addr in TEMP_HUM_ADDRS:
                print(f"  0x{addr:02X} - Likely Temperature/Humidity Sensor")
                device_map['temp_humidity_sensors'].append((channel, addr))
            else:
                print(f"  0x{addr:02X} - Unknown device")
                device_map['unknown'].append((channel, addr))
    
    return device_map


def run_functional_tests(bus, mux, device_map):
    """Run functional tests on identified devices"""
    print(f"\n{'='*60}")
    print("Functional Tests")
    print(f"{'='*60}")
    
    results = {'passed': 0, 'failed': 0}
    
    # Test temperature sensors
    if device_map['temperature_sensors']:
        print("\nTesting Temperature Sensors:")
        for channel, addr in device_map['temperature_sensors']:
            if test_temperature_sensor(bus, mux, channel, addr):
                results['passed'] += 1
            else:
                results['failed'] += 1
    
    # Test OLED displays
    if device_map['oled_displays']:
        print("\nTesting OLED Displays:")
        for channel, addr in device_map['oled_displays']:
            if test_oled_display(bus, mux, channel, addr):
                results['passed'] += 1
            else:
                results['failed'] += 1
    
    # Test temp/humidity sensors
    if device_map['temp_humidity_sensors']:
        print("\nTesting Temperature/Humidity Sensors:")
        for channel, addr in device_map['temp_humidity_sensors']:
            if test_temperature_sensor(bus, mux, channel, addr):
                results['passed'] += 1
            else:
                results['failed'] += 1
    
    return results


def print_summary(device_map, test_results):
    """Print test summary"""
    print(f"\n{'='*60}")
    print("TEST SUMMARY")
    print(f"{'='*60}")
    
    total_devices = sum(len(devices) for devices in device_map.values())
    print(f"\nTotal devices found: {total_devices}")
    print(f"  - Temperature sensors: {len(device_map['temperature_sensors'])}")
    print(f"  - Temp/Humidity sensors: {len(device_map['temp_humidity_sensors'])}")
    print(f"  - OLED displays: {len(device_map['oled_displays'])}")
    print(f"  - Unknown devices: {len(device_map['unknown'])}")
    
    print(f"\nFunctional tests:")
    print(f"  ✓ Passed: {test_results['passed']}")
    print(f"  ✗ Failed: {test_results['failed']}")
    
    print(f"\n{'='*60}")


def main():
    """Main test routine"""
    print(f"{'='*60}")
    print("I2C Setup Test Script")
    print("PCA9548A Multiplexer with Sensors and Displays")
    print(f"{'='*60}")
    
    try:
        # Initialize I2C bus
        print(f"\nInitializing I2C bus {I2C_BUS}...")
        bus = smbus.SMBus(I2C_BUS)
        print("✓ I2C bus initialized")
        
        # Scan main I2C bus
        main_devices = scan_i2c_bus(bus)
        
        if not main_devices:
            print("\n✗ No I2C devices found on main bus!")
            print("  Check your connections and ensure I2C is enabled.")
            return 1
        
        # Test multiplexer
        mux = test_multiplexer(bus, PCA9548A_ADDR)
        
        if not mux:
            print("\n✗ Could not initialize multiplexer!")
            print(f"  Make sure PCA9548A is connected at address 0x{PCA9548A_ADDR:02X}")
            return 1
        
        # Scan all channels
        channel_devices = scan_mux_channels(bus, mux)
        
        # Identify devices
        device_map = identify_devices(channel_devices)
        
        # Run functional tests
        test_results = run_functional_tests(bus, mux, device_map)
        
        # Print summary
        print_summary(device_map, test_results)
        
        # Cleanup
        mux.disable_all_channels()
        bus.close()
        
        print("\n✓ Test completed successfully!")
        return 0
        
    except Exception as e:
        print(f"\n✗ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
