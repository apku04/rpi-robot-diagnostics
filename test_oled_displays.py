#!/usr/bin/env python3
"""
OLED Display Test for SH1107 (128x128) via PCA9548A multiplexer
Compatible with skipper-face-tracker setup
"""

import time
try:
    import smbus2 as smbus
except ImportError:
    import smbus

try:
    from luma.core.interface.serial import i2c
    from luma.core.render import canvas
    from luma.oled.device import sh1106  # SH1106 is compatible with SH1107
    from PIL import ImageFont
    LUMA_AVAILABLE = True
except ImportError:
    print("⚠ luma.oled not installed. Install with: pip3 install luma.core luma.oled pillow")
    LUMA_AVAILABLE = False

I2C_BUS = 1
MUX_ADDR = 0x70

# OLED configuration from quick test results
OLED_CONFIGS = [
    {'channel': 2, 'address': 0x3D, 'name': 'OLED 1'},
    {'channel': 3, 'address': 0x3C, 'name': 'OLED 2'}
]

def select_mux_channel(bus, channel):
    """Select channel on PCA9548A multiplexer"""
    bus.write_byte(MUX_ADDR, 1 << channel)
    time.sleep(0.02)

def disable_mux_channels(bus):
    """Disable all multiplexer channels"""
    bus.write_byte(MUX_ADDR, 0x00)
    time.sleep(0.02)

def test_oled_basic(bus, channel, addr, name):
    """Basic OLED communication test"""
    print(f"\nTesting {name} (Channel {channel}, Address 0x{addr:02X})...")
    
    try:
        select_mux_channel(bus, channel)
        
        # Try to read from device
        bus.read_byte(addr)
        print(f"  ✓ {name} responding")
        return True
    except Exception as e:
        print(f"  ✗ {name} not responding: {e}")
        return False

def test_oled_display(channel, addr, name):
    """Test OLED with luma library (SH1107/SH1106 128x128)"""
    if not LUMA_AVAILABLE:
        return False
    
    print(f"\n  Testing display functionality for {name}...")
    
    try:
        # Create device with multiplexer channel switching
        # Note: luma.oled handles I2C, but we need mux switching
        bus = smbus.SMBus(I2C_BUS)
        select_mux_channel(bus, channel)
        time.sleep(0.05)
        
        # Initialize SH1106 device (compatible with SH1107)
        serial = i2c(port=I2C_BUS, address=addr)
        device = sh1106(serial, width=128, height=128, rotate=0)
        
        # Clear display
        with canvas(device) as draw:
            draw.rectangle(device.bounding_box, outline="white", fill="black")
        
        time.sleep(0.2)
        
        # Test 1: Display text
        print(f"    Test 1: Displaying text...")
        with canvas(device) as draw:
            draw.rectangle(device.bounding_box, outline="white", fill="black")
            draw.text((10, 10), f"{name}", fill="white")
            draw.text((10, 30), f"Channel {channel}", fill="white")
            draw.text((10, 50), f"Addr: 0x{addr:02X}", fill="white")
            draw.text((10, 70), "Test OK!", fill="white")
        
        time.sleep(2)
        
        # Test 2: Draw shapes
        print(f"    Test 2: Drawing shapes...")
        with canvas(device) as draw:
            draw.rectangle(device.bounding_box, outline="white", fill="black")
            draw.rectangle((10, 10, 118, 118), outline="white", fill="black")
            draw.ellipse((30, 30, 98, 98), outline="white", fill="black")
            draw.line((64, 30, 64, 98), fill="white")
            draw.line((30, 64, 98, 64), fill="white")
        
        time.sleep(2)
        
        # Test 3: Progress bar animation
        print(f"    Test 3: Progress bar...")
        for progress in range(0, 101, 10):
            with canvas(device) as draw:
                draw.rectangle(device.bounding_box, outline="white", fill="black")
                draw.text((30, 40), "Loading...", fill="white")
                # Progress bar
                bar_width = int((128 - 20) * progress / 100)
                draw.rectangle((10, 60, 118, 75), outline="white", fill="black")
                if bar_width > 0:
                    draw.rectangle((10, 60, 10 + bar_width, 75), outline="white", fill="white")
                draw.text((50, 85), f"{progress}%", fill="white")
            time.sleep(0.1)
        
        time.sleep(1)
        
        # Test 4: Inverted display
        print(f"    Test 4: Inverted display...")
        with canvas(device) as draw:
            draw.rectangle(device.bounding_box, outline="white", fill="white")
            draw.text((20, 55), "INVERTED", fill="black")
        
        time.sleep(2)
        
        # Clear display
        with canvas(device) as draw:
            draw.rectangle(device.bounding_box, outline="white", fill="black")
            draw.text((30, 55), "Test Done!", fill="white")
        
        time.sleep(1)
        
        # Final clear
        device.clear()
        
        bus.close()
        print(f"    ✓ All tests passed for {name}")
        return True
        
    except Exception as e:
        print(f"    ✗ Display test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("="*60)
    print("OLED Display Test - SH1107 128x128")
    print("PCA9548A Multiplexer + Luma.OLED")
    print("="*60)
    
    try:
        bus = smbus.SMBus(I2C_BUS)
        
        # Test multiplexer
        print(f"\nTesting multiplexer at 0x{MUX_ADDR:02X}...")
        try:
            state = bus.read_byte(MUX_ADDR)
            print(f"✓ Multiplexer OK (state: 0b{state:08b})")
        except Exception as e:
            print(f"✗ Multiplexer not found: {e}")
            return 1
        
        # Basic communication tests
        print("\n" + "="*60)
        print("Basic Communication Tests")
        print("="*60)
        
        results = {}
        for config in OLED_CONFIGS:
            success = test_oled_basic(bus, config['channel'], config['address'], config['name'])
            results[config['name']] = success
        
        # Disable channels before display tests
        disable_mux_channels(bus)
        bus.close()
        
        # Display functionality tests (if luma available)
        if LUMA_AVAILABLE:
            print("\n" + "="*60)
            print("Display Functionality Tests")
            print("="*60)
            print("Running visual tests on each display...")
            
            for config in OLED_CONFIGS:
                if results[config['name']]:
                    test_oled_display(config['channel'], config['address'], config['name'])
                    time.sleep(0.5)
        
        # Summary
        print("\n" + "="*60)
        print("TEST SUMMARY")
        print("="*60)
        
        passed = sum(1 for v in results.values() if v)
        total = len(results)
        
        for name, success in results.items():
            status = "✓ PASS" if success else "✗ FAIL"
            print(f"{name}: {status}")
        
        print(f"\nTotal: {passed}/{total} displays working")
        
        if passed == total:
            print("\n✓ All OLED displays are working correctly!")
            return 0
        else:
            print(f"\n⚠ {total - passed} display(s) failed")
            return 1
        
    except Exception as e:
        print(f"\n✗ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit(main())
