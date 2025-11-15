#!/usr/bin/env python3
"""
OLED Display Test Module
Tests SH1107/SH1106 OLED displays via PCA9548A multiplexer
"""

import time

try:
    import smbus2 as smbus
except ImportError:
    import smbus

try:
    from luma.core.interface.serial import i2c
    from luma.core.render import canvas
    from luma.oled.device import sh1106
    LUMA_AVAILABLE = True
except ImportError:
    LUMA_AVAILABLE = False

I2C_BUS = 1
MUX_ADDR = 0x70

# OLED configuration
OLEDS = [
    {'name': 'OLED_1', 'channel': 2, 'address': 0x3D},
    {'name': 'OLED_2', 'channel': 3, 'address': 0x3C}
]

def select_mux_channel(bus, channel):
    """Select channel on PCA9548A multiplexer"""
    bus.write_byte(MUX_ADDR, 1 << channel)
    time.sleep(0.02)

def test_oled_basic(bus, channel, addr):
    """Basic OLED communication test"""
    try:
        select_mux_channel(bus, channel)
        bus.read_byte(addr)
        return {'success': True, 'message': 'Responding'}
    except Exception as e:
        return {'success': False, 'error': str(e)}

def test_oled_display(channel, addr, name, quick=True):
    """Test OLED display functionality"""
    if not LUMA_AVAILABLE:
        return {'success': False, 'error': 'luma.oled not installed'}
    
    try:
        bus = smbus.SMBus(I2C_BUS)
        select_mux_channel(bus, channel)
        time.sleep(0.05)
        
        serial = i2c(port=I2C_BUS, address=addr)
        device = sh1106(serial, width=128, height=128, rotate=0)
        
        # Quick test - just write text
        with canvas(device) as draw:
            draw.rectangle(device.bounding_box, outline="white", fill="black")
            draw.text((10, 50), f"{name} OK", fill="white")
        
        time.sleep(0.5 if quick else 2.0)
        device.clear()
        
        bus.close()
        return {'success': True, 'message': 'Display working'}
        
    except Exception as e:
        return {'success': False, 'error': str(e)}

def run_test(visual=False):
    """
    Test all OLED displays
    
    Args:
        visual: If True, perform visual display tests (slower)
    
    Returns:
        dict: {
            'status': 'pass'/'fail',
            'message': str,
            'displays': dict,
            'error': str (optional)
        }
    """
    result = {
        'status': 'pass',
        'message': '',
        'displays': {}
    }
    
    try:
        bus = smbus.SMBus(I2C_BUS)
        
        passed = 0
        failed = 0
        
        for oled in OLEDS:
            # Basic communication test
            basic_result = test_oled_basic(bus, oled['channel'], oled['address'])
            
            if visual and basic_result['success'] and LUMA_AVAILABLE:
                # Visual test
                display_result = test_oled_display(
                    oled['channel'], 
                    oled['address'], 
                    oled['name'],
                    quick=True
                )
                result['displays'][oled['name']] = display_result
            else:
                result['displays'][oled['name']] = basic_result
            
            if result['displays'][oled['name']]['success']:
                passed += 1
            else:
                failed += 1
        
        # Disable mux
        bus.write_byte(MUX_ADDR, 0x00)
        bus.close()
        
        if failed > 0:
            result['status'] = 'fail'
        
        result['message'] = f"{passed}/{len(OLEDS)} displays working"
        
        if not LUMA_AVAILABLE and visual:
            result['message'] += " (visual test skipped - luma.oled not available)"
        
    except Exception as e:
        result['status'] = 'fail'
        result['error'] = str(e)
    
    return result

def main():
    """Standalone test execution"""
    print("="*60)
    print("OLED Display Test")
    print("="*60)
    
    result = run_test(visual=True)
    
    print(f"\nStatus: {result['status'].upper()}")
    print(f"Message: {result['message']}")
    
    if result.get('displays'):
        print("\nDisplay Status:")
        for name, data in result['displays'].items():
            if data['success']:
                print(f"  {name}: OK - {data.get('message', 'Working')}")
            else:
                print(f"  {name}: FAIL - {data.get('error', 'Unknown')}")
    
    if result.get('error'):
        print(f"\nError: {result['error']}")
    
    return 0 if result['status'] == 'pass' else 1

if __name__ == "__main__":
    exit(main())
