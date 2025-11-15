#!/usr/bin/env python3
"""
Temperature and Humidity Sensor Test
PCA9548A Multiplexer with SHT31/SHT4x and BME280/BMP280
"""

import time
import struct

try:
    import smbus2 as smbus
except ImportError:
    import smbus

I2C_BUS = 1
MUX_ADDR = 0x70

# Sensor configuration from quick test
SENSORS = [
    {
        'name': 'SHT31/SHT4x',
        'channel': 0,
        'address': 0x44,
        'type': 'sht3x'
    },
    {
        'name': 'BME280/BMP280',
        'channel': 1,
        'address': 0x76,
        'type': 'bme280'
    }
]

def select_mux_channel(bus, channel):
    """Select channel on PCA9548A multiplexer"""
    bus.write_byte(MUX_ADDR, 1 << channel)
    time.sleep(0.02)

def disable_mux_channels(bus):
    """Disable all multiplexer channels"""
    bus.write_byte(MUX_ADDR, 0x00)
    time.sleep(0.02)

def read_sht3x(bus, addr):
    """Read temperature and humidity from SHT3x sensor"""
    try:
        # Send measurement command (high repeatability, clock stretching disabled)
        bus.write_i2c_block_data(addr, 0x24, [0x00])
        time.sleep(0.02)  # Wait for measurement
        
        # Read 6 bytes of data
        data = bus.read_i2c_block_data(addr, 0x00, 6)
        
        # Convert temperature data
        temp_raw = (data[0] << 8) | data[1]
        temp_c = -45 + (175 * temp_raw / 65535.0)
        
        # Convert humidity data
        hum_raw = (data[3] << 8) | data[4]
        humidity = 100 * hum_raw / 65535.0
        
        return {
            'temperature': temp_c,
            'humidity': humidity,
            'success': True
        }
    except Exception as e:
        return {
            'temperature': None,
            'humidity': None,
            'success': False,
            'error': str(e)
        }

def read_bme280(bus, addr):
    """Read temperature, humidity, and pressure from BME280/BMP280"""
    try:
        # Read chip ID to determine if BME280 or BMP280
        chip_id = bus.read_byte_data(addr, 0xD0)
        
        is_bme280 = (chip_id == 0x60)
        is_bmp280 = (chip_id == 0x58)
        
        if not (is_bme280 or is_bmp280):
            return {
                'temperature': None,
                'humidity': None,
                'pressure': None,
                'success': False,
                'error': f'Unknown chip ID: 0x{chip_id:02X}'
            }
        
        # Reset the device
        bus.write_byte_data(addr, 0xE0, 0xB6)
        time.sleep(0.01)
        
        # Read calibration data
        cal = bus.read_i2c_block_data(addr, 0x88, 24)
        if is_bme280:
            cal += bus.read_i2c_block_data(addr, 0xE1, 7)
        
        # Parse calibration coefficients
        dig_T1 = cal[0] | (cal[1] << 8)
        dig_T2 = struct.unpack('<h', bytes([cal[2], cal[3]]))[0]
        dig_T3 = struct.unpack('<h', bytes([cal[4], cal[5]]))[0]
        
        dig_P1 = cal[6] | (cal[7] << 8)
        dig_P2 = struct.unpack('<h', bytes([cal[8], cal[9]]))[0]
        dig_P3 = struct.unpack('<h', bytes([cal[10], cal[11]]))[0]
        dig_P4 = struct.unpack('<h', bytes([cal[12], cal[13]]))[0]
        dig_P5 = struct.unpack('<h', bytes([cal[14], cal[15]]))[0]
        dig_P6 = struct.unpack('<h', bytes([cal[16], cal[17]]))[0]
        dig_P7 = struct.unpack('<h', bytes([cal[18], cal[19]]))[0]
        dig_P8 = struct.unpack('<h', bytes([cal[20], cal[21]]))[0]
        dig_P9 = struct.unpack('<h', bytes([cal[22], cal[23]]))[0]
        
        if is_bme280:
            dig_H1 = cal[24]
            dig_H2 = struct.unpack('<h', bytes([cal[25], cal[26]]))[0]
            dig_H3 = cal[27]
            dig_H4 = (cal[28] << 4) | (cal[29] & 0x0F)
            dig_H5 = (cal[30] << 4) | (cal[29] >> 4)
            dig_H6 = struct.unpack('<b', bytes([cal[31]]))[0]
        
        # Configure sensor (normal mode, oversampling)
        if is_bme280:
            bus.write_byte_data(addr, 0xF2, 0x01)  # humidity oversampling x1
        bus.write_byte_data(addr, 0xF4, 0x27)  # temp and pressure oversampling x1, normal mode
        bus.write_byte_data(addr, 0xF5, 0xA0)  # config: standby 1000ms, filter off
        
        time.sleep(0.1)  # Wait for measurement
        
        # Read raw data
        data = bus.read_i2c_block_data(addr, 0xF7, 8)
        
        adc_p = (data[0] << 12) | (data[1] << 4) | (data[2] >> 4)
        adc_t = (data[3] << 12) | (data[4] << 4) | (data[5] >> 4)
        adc_h = (data[6] << 8) | data[7] if is_bme280 else None
        
        # Temperature compensation
        var1 = ((adc_t / 16384.0) - (dig_T1 / 1024.0)) * dig_T2
        var2 = (((adc_t / 131072.0) - (dig_T1 / 8192.0)) ** 2) * dig_T3
        t_fine = int(var1 + var2)
        temp_c = (var1 + var2) / 5120.0
        
        # Pressure compensation
        var1 = (t_fine / 2.0) - 64000.0
        var2 = var1 * var1 * dig_P6 / 32768.0
        var2 = var2 + var1 * dig_P5 * 2.0
        var2 = (var2 / 4.0) + (dig_P4 * 65536.0)
        var1 = (dig_P3 * var1 * var1 / 524288.0 + dig_P2 * var1) / 524288.0
        var1 = (1.0 + var1 / 32768.0) * dig_P1
        
        if var1 == 0:
            pressure_hpa = 0
        else:
            p = 1048576.0 - adc_p
            p = ((p - var2 / 4096.0) * 6250.0) / var1
            var1 = dig_P9 * p * p / 2147483648.0
            var2 = p * dig_P8 / 32768.0
            pressure_hpa = (p + (var1 + var2 + dig_P7) / 16.0) / 100.0
        
        # Humidity compensation (BME280 only)
        humidity = None
        if is_bme280 and adc_h is not None:
            h = t_fine - 76800.0
            h = (adc_h - (dig_H4 * 64.0 + dig_H5 / 16384.0 * h)) * \
                (dig_H2 / 65536.0 * (1.0 + dig_H6 / 67108864.0 * h * 
                (1.0 + dig_H3 / 67108864.0 * h)))
            h = h * (1.0 - dig_H1 * h / 524288.0)
            humidity = max(0.0, min(100.0, h))
        
        chip_name = "BME280" if is_bme280 else "BMP280"
        
        return {
            'temperature': temp_c,
            'humidity': humidity,
            'pressure': pressure_hpa,
            'chip': chip_name,
            'success': True
        }
        
    except Exception as e:
        return {
            'temperature': None,
            'humidity': None,
            'pressure': None,
            'success': False,
            'error': str(e)
        }

def test_sensor(bus, sensor_config):
    """Test a sensor and return readings"""
    print(f"\n{'='*60}")
    print(f"Testing {sensor_config['name']}")
    print(f"Channel: {sensor_config['channel']}, Address: 0x{sensor_config['address']:02X}")
    print(f"{'='*60}")
    
    # Select multiplexer channel
    select_mux_channel(bus, sensor_config['channel'])
    
    # Read sensor based on type
    if sensor_config['type'] == 'sht3x':
        result = read_sht3x(bus, sensor_config['address'])
    elif sensor_config['type'] == 'bme280':
        result = read_bme280(bus, sensor_config['address'])
    else:
        result = {'success': False, 'error': 'Unknown sensor type'}
    
    # Display results
    if result['success']:
        print(f"✓ Sensor responding")
        
        if result.get('chip'):
            print(f"  Chip: {result['chip']}")
        
        if result.get('temperature') is not None:
            temp_c = result['temperature']
            temp_f = (temp_c * 9/5) + 32
            print(f"  Temperature: {temp_c:.2f}°C ({temp_f:.2f}°F)")
        
        if result.get('humidity') is not None:
            print(f"  Humidity: {result['humidity']:.1f}%")
        
        if result.get('pressure') is not None:
            print(f"  Pressure: {result['pressure']:.2f} hPa")
    else:
        print(f"✗ Error reading sensor: {result.get('error', 'Unknown error')}")
    
    return result

def continuous_monitoring(bus, interval=2.0, duration=None):
    """Continuously monitor all sensors"""
    print(f"\n{'='*60}")
    print("CONTINUOUS MONITORING MODE")
    print(f"{'='*60}")
    print(f"Update interval: {interval}s")
    if duration:
        print(f"Duration: {duration}s")
    print("Press Ctrl+C to stop\n")
    
    start_time = time.time()
    
    try:
        while True:
            current_time = time.time() - start_time
            
            if duration and current_time >= duration:
                break
            
            print(f"\n[{current_time:.1f}s] " + "="*50)
            
            for sensor in SENSORS:
                select_mux_channel(bus, sensor['channel'])
                
                if sensor['type'] == 'sht3x':
                    result = read_sht3x(bus, sensor['address'])
                elif sensor['type'] == 'bme280':
                    result = read_bme280(bus, sensor['address'])
                else:
                    continue
                
                if result['success']:
                    output = f"{sensor['name']:15} | "
                    if result.get('temperature') is not None:
                        output += f"Temp: {result['temperature']:5.1f}°C | "
                    if result.get('humidity') is not None:
                        output += f"Hum: {result['humidity']:4.1f}% | "
                    if result.get('pressure') is not None:
                        output += f"Press: {result['pressure']:7.2f} hPa"
                    print(output)
                else:
                    print(f"{sensor['name']:15} | ERROR: {result.get('error', 'Unknown')}")
            
            time.sleep(interval)
            
    except KeyboardInterrupt:
        print("\n\nMonitoring stopped by user")

def main():
    """Main test routine"""
    print("="*60)
    print("Temperature & Humidity Sensor Test")
    print("PCA9548A Multiplexer")
    print("="*60)
    
    try:
        # Initialize I2C bus
        bus = smbus.SMBus(I2C_BUS)
        
        # Test multiplexer
        print(f"\nTesting multiplexer at 0x{MUX_ADDR:02X}...")
        try:
            state = bus.read_byte(MUX_ADDR)
            print(f"✓ Multiplexer OK (state: 0b{state:08b})")
        except Exception as e:
            print(f"✗ Multiplexer not found: {e}")
            return 1
        
        # Test each sensor
        results = {}
        for sensor in SENSORS:
            result = test_sensor(bus, sensor)
            results[sensor['name']] = result['success']
        
        # Summary
        print(f"\n{'='*60}")
        print("TEST SUMMARY")
        print(f"{'='*60}")
        
        for name, success in results.items():
            status = "✓ PASS" if success else "✗ FAIL"
            print(f"{name}: {status}")
        
        passed = sum(1 for v in results.values() if v)
        total = len(results)
        print(f"\nTotal: {passed}/{total} sensors working")
        
        # Ask for continuous monitoring
        if passed > 0:
            print(f"\n{'='*60}")
            response = input("\nStart continuous monitoring? (y/n): ").strip().lower()
            if response == 'y':
                continuous_monitoring(bus, interval=2.0)
        
        # Cleanup
        disable_mux_channels(bus)
        bus.close()
        
        print("\n✓ Test completed!")
        return 0 if passed == total else 1
        
    except Exception as e:
        print(f"\n✗ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit(main())
