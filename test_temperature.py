#!/usr/bin/env python3
"""
Temperature Sensor Test Module
Tests SHT3x and BME280/BMP280 sensors via PCA9548A multiplexer
"""

import time
import struct

try:
    import smbus2 as smbus
except ImportError:
    import smbus

I2C_BUS = 1
MUX_ADDR = 0x70

# Sensor configuration
SENSORS = [
    {'name': 'SHT31', 'channel': 0, 'address': 0x44, 'type': 'sht3x'},
    {'name': 'BMP280', 'channel': 1, 'address': 0x76, 'type': 'bme280'}
]

def select_mux_channel(bus, channel):
    """Select channel on PCA9548A multiplexer"""
    bus.write_byte(MUX_ADDR, 1 << channel)
    time.sleep(0.02)

def read_sht3x(bus, addr):
    """Read temperature and humidity from SHT3x sensor"""
    try:
        bus.write_i2c_block_data(addr, 0x24, [0x00])
        time.sleep(0.02)
        data = bus.read_i2c_block_data(addr, 0x00, 6)
        
        temp_raw = (data[0] << 8) | data[1]
        temp_c = -45 + (175 * temp_raw / 65535.0)
        
        hum_raw = (data[3] << 8) | data[4]
        humidity = 100 * hum_raw / 65535.0
        
        return {'temperature': temp_c, 'humidity': humidity, 'success': True}
    except Exception as e:
        return {'success': False, 'error': str(e)}

def read_bme280(bus, addr):
    """Read temperature and pressure from BME280/BMP280"""
    try:
        chip_id = bus.read_byte_data(addr, 0xD0)
        is_bme280 = (chip_id == 0x60)
        is_bmp280 = (chip_id == 0x58)
        
        if not (is_bme280 or is_bmp280):
            return {'success': False, 'error': f'Unknown chip: 0x{chip_id:02X}'}
        
        # Reset and configure
        bus.write_byte_data(addr, 0xE0, 0xB6)
        time.sleep(0.01)
        
        # Read calibration
        cal = bus.read_i2c_block_data(addr, 0x88, 24)
        if is_bme280:
            cal += bus.read_i2c_block_data(addr, 0xE1, 7)
        
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
            bus.write_byte_data(addr, 0xF2, 0x01)
        bus.write_byte_data(addr, 0xF4, 0x27)
        bus.write_byte_data(addr, 0xF5, 0xA0)
        
        time.sleep(0.1)
        
        data = bus.read_i2c_block_data(addr, 0xF7, 8)
        adc_p = (data[0] << 12) | (data[1] << 4) | (data[2] >> 4)
        adc_t = (data[3] << 12) | (data[4] << 4) | (data[5] >> 4)
        
        # Temperature
        var1 = ((adc_t / 16384.0) - (dig_T1 / 1024.0)) * dig_T2
        var2 = (((adc_t / 131072.0) - (dig_T1 / 8192.0)) ** 2) * dig_T3
        t_fine = int(var1 + var2)
        temp_c = (var1 + var2) / 5120.0
        
        # Pressure
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
        
        chip_name = "BME280" if is_bme280 else "BMP280"
        
        return {
            'temperature': temp_c,
            'pressure': pressure_hpa,
            'chip': chip_name,
            'success': True
        }
        
    except Exception as e:
        return {'success': False, 'error': str(e)}

def run_test():
    """
    Test all temperature sensors
    
    Returns:
        dict: {
            'status': 'pass'/'fail',
            'message': str,
            'sensors': dict,
            'error': str (optional)
        }
    """
    result = {
        'status': 'pass',
        'message': '',
        'sensors': {}
    }
    
    try:
        bus = smbus.SMBus(I2C_BUS)
        
        passed = 0
        failed = 0
        
        for sensor in SENSORS:
            select_mux_channel(bus, sensor['channel'])
            
            if sensor['type'] == 'sht3x':
                reading = read_sht3x(bus, sensor['address'])
            elif sensor['type'] == 'bme280':
                reading = read_bme280(bus, sensor['address'])
            else:
                reading = {'success': False, 'error': 'Unknown type'}
            
            result['sensors'][sensor['name']] = reading
            
            if reading['success']:
                passed += 1
            else:
                failed += 1
        
        # Disable mux
        bus.write_byte(MUX_ADDR, 0x00)
        bus.close()
        
        if failed > 0:
            result['status'] = 'fail'
        
        result['message'] = f"{passed}/{len(SENSORS)} sensors working"
        
    except Exception as e:
        result['status'] = 'fail'
        result['error'] = str(e)
    
    return result

def main():
    """Standalone test execution"""
    print("="*60)
    print("Temperature Sensor Test")
    print("="*60)
    
    result = run_test()
    
    print(f"\nStatus: {result['status'].upper()}")
    print(f"Message: {result['message']}")
    
    if result.get('sensors'):
        print("\nSensor Readings:")
        for name, data in result['sensors'].items():
            if data['success']:
                output = f"  {name}: "
                if 'chip' in data:
                    output += f"({data['chip']}) "
                if 'temperature' in data:
                    output += f"Temp: {data['temperature']:.1f}°C "
                if 'humidity' in data:
                    output += f"Hum: {data['humidity']:.1f}% "
                if 'pressure' in data:
                    output += f"Press: {data['pressure']:.1f} hPa"
                print(output)
            else:
                print(f"  {name}: ERROR - {data.get('error', 'Unknown')}")
    
    if result.get('error'):
        print(f"\nError: {result['error']}")
    
    return 0 if result['status'] == 'pass' else 1

if __name__ == "__main__":
    exit(main())
