#!/usr/bin/env python3
"""
Quick I2C test - Simple version
Tests PCA9548A multiplexer and scans all channels
"""

try:
    import smbus2 as smbus
except ImportError:
    import smbus

I2C_BUS = 1
MUX_ADDR = 0x70

def run_test():
    print("Quick I2C Test\n" + "="*40)
    
    try:
        bus = smbus.SMBus(I2C_BUS)
        
        # Test multiplexer
        print(f"Testing multiplexer at 0x{MUX_ADDR:02X}...")
        current = bus.read_byte(MUX_ADDR)
        print(f"✓ Multiplexer OK (state: 0b{current:08b})\n")
        
        # Scan each channel
        for ch in range(8):
            bus.write_byte(MUX_ADDR, 1 << ch)
            print(f"Channel {ch}:", end=" ")
            
            devices = []
            for addr in range(0x03, 0x78):
                if addr == MUX_ADDR:
                    continue
                try:
                    bus.read_byte(addr)
                    devices.append(f"0x{addr:02X}")
                except:
                    pass
            
            if devices:
                print(", ".join(devices))
            else:
                print("(empty)")
        
        # Disable all channels
        bus.write_byte(MUX_ADDR, 0x00)
        bus.close()
        
        print("\n✓ Test complete!")
        return {'status': 'pass', 'devices_found': sum(len(devices) for devices in [devices])}
        
    except Exception as e:
        print(f"✗ Error: {e}")
        return {'status': 'fail', 'error': str(e)}

def main():
    result = run_test()
    return 0 if result['status'] == 'pass' else 1

if __name__ == "__main__":
    exit(main())
