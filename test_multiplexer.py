#!/usr/bin/env python3
"""
I2C Multiplexer Test Module
Tests PCA9548A multiplexer connectivity
"""

try:
    import smbus2 as smbus
except ImportError:
    import smbus

I2C_BUS = 1
MUX_ADDR = 0x70

def run_test():
    """
    Test PCA9548A multiplexer
    
    Returns:
        dict: {
            'status': 'pass'/'fail',
            'message': str,
            'channels': dict,
            'error': str (optional)
        }
    """
    result = {
        'status': 'pass',
        'message': '',
        'channels': {}
    }
    
    try:
        bus = smbus.SMBus(I2C_BUS)
        
        # Test multiplexer
        try:
            state = bus.read_byte(MUX_ADDR)
            result['message'] = f"Multiplexer OK at 0x{MUX_ADDR:02X}"
        except Exception as e:
            result['status'] = 'fail'
            result['error'] = f"Multiplexer not found: {e}"
            return result
        
        # Scan each channel
        total_devices = 0
        for ch in range(8):
            bus.write_byte(MUX_ADDR, 1 << ch)
            
            devices = []
            for addr in range(0x03, 0x78):
                if addr == MUX_ADDR:
                    continue
                try:
                    bus.read_byte(addr)
                    devices.append(f"0x{addr:02X}")
                except:
                    pass
            
            result['channels'][ch] = devices
            total_devices += len(devices)
        
        # Disable all channels
        bus.write_byte(MUX_ADDR, 0x00)
        bus.close()
        
        result['message'] += f" | {total_devices} devices found across {len([c for c in result['channels'].values() if c])} channels"
        
    except Exception as e:
        result['status'] = 'fail'
        result['error'] = str(e)
    
    return result

def main():
    """Standalone test execution"""
    print("="*60)
    print("I2C Multiplexer Test")
    print("="*60)
    
    result = run_test()
    
    print(f"\nStatus: {result['status'].upper()}")
    print(f"Message: {result['message']}")
    
    if result.get('channels'):
        print("\nChannels:")
        for ch, devices in result['channels'].items():
            if devices:
                print(f"  Channel {ch}: {', '.join(devices)}")
    
    if result.get('error'):
        print(f"Error: {result['error']}")
    
    return 0 if result['status'] == 'pass' else 1

if __name__ == "__main__":
    exit(main())
