#!/usr/bin/env python3
"""
Klipper/Moonraker Motor Controller Test Module
Tests connection to Bigtreetech Octopus Pro V1.0 via Moonraker API
"""

import sys
import time
import json

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

MOONRAKER_URL = "http://localhost:7125"

def check_moonraker_connection():
    """Check if Moonraker API is accessible"""
    if not REQUESTS_AVAILABLE:
        return {'success': False, 'error': 'requests library not installed'}
    
    try:
        response = requests.get(f"{MOONRAKER_URL}/printer/info", timeout=2.0)
        if response.status_code == 200:
            data = response.json()
            return {
                'success': True,
                'data': data,
                'message': 'Moonraker connected'
            }
        else:
            return {
                'success': False, 
                'error': f"HTTP {response.status_code}",
                'message': 'Moonraker returned error'
            }
    except requests.exceptions.ConnectionError:
        return {
            'success': False, 
            'error': 'Connection refused',
            'message': 'Moonraker not running (check service)'
        }
    except Exception as e:
        return {'success': False, 'error': str(e)}

def check_mcu_status():
    """Check MCU status via Klipper Object Model"""
    if not REQUESTS_AVAILABLE:
        return {'success': False}

    try:
        # First list objects to find the mcu
        response = requests.get(f"{MOONRAKER_URL}/printer/objects/list", timeout=2.0)
        if response.status_code != 200:
            return {'success': False, 'error': 'Failed to list objects'}
            
        objects = response.json().get('result', {}).get('objects', [])
        mcu_objs = [obj for obj in objects if obj.startswith('mcu')]
        
        if not mcu_objs:
            return {'success': False, 'error': 'No MCU objects found in Klipper config'}
            
        # Query the MCUs found
        query_str = "&".join(mcu_objs)
        response = requests.get(f"{MOONRAKER_URL}/printer/objects/query?{query_str}", timeout=2.0)
        
        if response.status_code == 200:
            data = response.json().get('result', {}).get('status', {})
            return {
                'success': True,
                'mcus': data
            }
        return {'success': False, 'error': 'Failed to query MCU status'}
        
    except Exception as e:
        return {'success': False, 'error': str(e)}

def send_gcode_command(command):
    """Send a G-code command to Klipper"""
    if not REQUESTS_AVAILABLE:
        return {'success': False}
        
    try:
        response = requests.post(
            f"{MOONRAKER_URL}/printer/gcode/script", 
            json={'script': command},
            timeout=2.0
        )
        
        if response.status_code == 200:
            return {'success': True, 'message': f"Command '{command}' sent"}
        else:
            return {'success': False, 'error': f"HTTP {response.status_code}"}
            
    except Exception as e:
        return {'success': False, 'error': str(e)}

def run_test(quick=False):
    """
    Test Klipper/Moonraker connection and MCU status
    """
    result = {
        'status': 'fail',
        'message': '',
        'klipper': {}
    }
    
    if not REQUESTS_AVAILABLE:
        result['error'] = 'requests library not installed (pip install requests)'
        result['message'] = 'Missing dependencies'
        return result
        
    # 1. Check Connection & Info
    conn_result = check_moonraker_connection()
    result['klipper']['connection'] = conn_result
    
    if not conn_result['success']:
        result['status'] = 'fail'
        result['error'] = conn_result.get('error')
        result['message'] = f"Moonraker unreachable: {conn_result.get('error')}"
        return result
        
    klipper_state = conn_result['data'].get('result', {}).get('state', 'unknown')
    klipper_msg = conn_result['data'].get('result', {}).get('state_message', '')
    
    result['klipper']['state'] = klipper_state
    
    if klipper_state != 'ready':
        result['status'] = 'fail'
        result['message'] = f"Klipper state: {klipper_state}"
        if klipper_msg:
            result['message'] += f" ({klipper_msg})"
    
    # 2. Check MCU Status
    mcu_result = check_mcu_status()
    result['klipper']['mcu'] = mcu_result
    
    if mcu_result['success']:
        mcu_info = []
        for name, status in mcu_result['mcus'].items():
            mcu_version = status.get('mcu_version', 'unknown')
            mcu_info.append(f"{name}: v{mcu_version}")
            
        if klipper_state == 'ready':
            result['status'] = 'pass'
            result['message'] = f"Klipper Ready | {', '.join(mcu_info)}"
    else:
        if result['status'] != 'fail':
            result['status'] = 'fail'
            result['message'] = f"MCU check failed: {mcu_result.get('error')}"

    # 3. Test G-Code (Parameter Set/Get simulation)
    # We'll send M115 (Get Firmware Version) as a safe test
    if result['status'] == 'pass':
        gcode_result = send_gcode_command("M115")
        if not gcode_result['success']:
             result['message'] += " (G-code send failed)"
    
    return result

def main():
    """Standalone test execution"""
    print("="*60)
    print("Klipper Motor Controller Test (Octopus Pro)")
    print("="*60)
    
    if not REQUESTS_AVAILABLE:
        print("\n✗ requests library not installed")
        print("Install with: pip3 install requests")
        return 1
        
    print(f"Connecting to Moonraker at {MOONRAKER_URL}...")
    result = run_test()
    
    print(f"\nStatus: {result['status'].upper()}")
    print(f"Message: {result['message']}")
    
    if result.get('klipper', {}).get('connection', {}).get('success'):
        state = result['klipper'].get('state', 'unknown')
        print(f"Klipper State: {state}")
        
        if result['klipper'].get('mcu', {}).get('success'):
            print("\nMCU Status:")
            for name, status in result['klipper']['mcu']['mcus'].items():
                print(f"  {name}:")
                print(f"    Version: {status.get('mcu_version', 'unknown')}")
                print(f"    Load: {status.get('last_stats', {}).get('mcu_task_avg', 0):.1f}%")
    
    if result.get('error'):
        print(f"\nError: {result['error']}")
    
    return 0 if result['status'] == 'pass' else 1

if __name__ == "__main__":
    sys.exit(main())
