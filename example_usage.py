#!/usr/bin/env python3
"""
Example: Using diagnostics in your application
This shows how to integrate the diagnostic system into your own code
"""

import sys
sys.path.append('/home/acp/work')

# Example 1: Run full diagnostics programmatically
def example_full_diagnostics():
    """Run complete diagnostics and handle results"""
    from run_diagnostics import run_diagnostics
    
    print("Running hardware diagnostics...\n")
    
    # Run diagnostics (verbose=True for output, quick=True to skip slow tests)
    exit_code = run_diagnostics(verbose=True, quick=True)
    
    if exit_code == 0:
        print("\n✓ All hardware checks passed - safe to start application")
        return True
    else:
        print("\n✗ Hardware diagnostics failed - check errors above")
        return False


# Example 2: Run individual test modules
def example_individual_tests():
    """Run specific tests and access detailed results"""
    import test_temperature
    import test_oled
    
    print("Running temperature sensor test...")
    temp_result = test_temperature.run_test()
    
    if temp_result['status'] == 'pass':
        print(f"✓ Temperature sensors OK: {temp_result['message']}")
        
        # Access individual sensor readings
        for sensor_name, data in temp_result['sensors'].items():
            if data['success']:
                print(f"  {sensor_name}:")
                if 'temperature' in data:
                    print(f"    Temperature: {data['temperature']:.1f}°C")
                if 'humidity' in data:
                    print(f"    Humidity: {data['humidity']:.1f}%")
                if 'pressure' in data:
                    print(f"    Pressure: {data['pressure']:.1f} hPa")
    else:
        print(f"✗ Temperature sensor test failed: {temp_result.get('error', 'Unknown')}")
    
    print("\nRunning OLED display test...")
    oled_result = test_oled.run_test(visual=False)  # Set visual=True for display test
    
    if oled_result['status'] == 'pass':
        print(f"✓ OLED displays OK: {oled_result['message']}")
    else:
        print(f"✗ OLED display test failed")


# Example 3: Silent diagnostics for scripts
def example_silent_check():
    """Run diagnostics silently and only return pass/fail"""
    from run_diagnostics import run_diagnostics
    
    # Run without output
    exit_code = run_diagnostics(verbose=False, quick=True)
    
    return exit_code == 0


# Example 4: Boot-time diagnostic check
def boot_time_diagnostics():
    """
    Example function to call at application startup
    Returns True if hardware is OK, False otherwise
    """
    from run_diagnostics import run_diagnostics
    
    print("="*70)
    print("STARTUP HARDWARE CHECK")
    print("="*70)
    
    exit_code = run_diagnostics(verbose=True, quick=True)
    
    if exit_code == 0:
        print("\n✓ Hardware initialization complete - starting application...")
        return True
    else:
        print("\n✗ Hardware initialization failed!")
        print("Please check hardware connections and restart.")
        return False


# Example 5: Custom application with diagnostic integration
def main():
    """Example main application"""
    print("Starting Application...\n")
    
    # Run diagnostics at startup
    if not boot_time_diagnostics():
        print("Exiting due to hardware failure")
        return 1
    
    print("\n" + "="*70)
    print("APPLICATION RUNNING")
    print("="*70)
    
    # Your application code here
    print("Application is now running with verified hardware...")
    
    # You can also run specific tests during runtime
    print("\nPerforming runtime sensor check...")
    example_individual_tests()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
