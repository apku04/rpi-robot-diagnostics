#!/usr/bin/env python3
"""
Microphone Test Module
Tests USB microphone connectivity and audio capture
"""

import sys
import time

try:
    import sounddevice as sd
    import numpy as np
    SOUNDDEVICE_AVAILABLE = True
except ImportError:
    SOUNDDEVICE_AVAILABLE = False

def list_audio_devices():
    """List all available audio devices"""
    if not SOUNDDEVICE_AVAILABLE:
        return None
    
    try:
        devices = sd.query_devices()
        return devices
    except Exception as e:
        return None

def find_usb_microphone():
    """Find USB microphone device"""
    if not SOUNDDEVICE_AVAILABLE:
        return None, "sounddevice not installed"
    
    try:
        devices = sd.query_devices()
        
        # Look for USB microphone (input devices)
        for idx, device in enumerate(devices):
            name = device['name'].lower()
            if device['max_input_channels'] > 0:
                # Common USB mic indicators
                if any(keyword in name for keyword in ['usb', 'webcam', 'c920', 'blue', 'yeti', 'microphone']):
                    return idx, device
        
        # If no USB mic found by name, return first input device
        for idx, device in enumerate(devices):
            if device['max_input_channels'] > 0:
                return idx, device
        
        return None, "No input device found"
        
    except Exception as e:
        return None, str(e)

def test_microphone_basic(device_idx):
    """Test basic microphone connectivity"""
    if not SOUNDDEVICE_AVAILABLE:
        return {'success': False, 'error': 'sounddevice not installed'}
    
    try:
        device_info = sd.query_devices(device_idx)
        
        # Try to open the device
        with sd.InputStream(device=device_idx, channels=1):
            pass
        
        return {
            'success': True,
            'name': device_info['name'],
            'channels': device_info['max_input_channels'],
            'sample_rate': device_info['default_samplerate']
        }
        
    except Exception as e:
        return {'success': False, 'error': str(e)}

def test_microphone_audio(device_idx, duration=2.0):
    """Test actual audio capture and level detection"""
    if not SOUNDDEVICE_AVAILABLE:
        return {'success': False, 'error': 'sounddevice not installed'}
    
    try:
        device_info = sd.query_devices(device_idx)
        sample_rate = int(device_info['default_samplerate'])
        
        print(f"  Recording {duration}s of audio (speak into the microphone)...")
        
        # Record audio
        recording = sd.rec(
            int(duration * sample_rate),
            samplerate=sample_rate,
            channels=1,
            device=device_idx,
            dtype='float32'
        )
        sd.wait()
        
        # Analyze audio
        audio_data = recording.flatten()
        rms = np.sqrt(np.mean(audio_data**2))
        peak = np.max(np.abs(audio_data))
        
        # Check if we got any signal
        has_signal = rms > 0.001  # Threshold for detecting audio
        
        return {
            'success': True,
            'rms_level': float(rms),
            'peak_level': float(peak),
            'has_signal': has_signal,
            'sample_rate': sample_rate,
            'duration': duration
        }
        
    except Exception as e:
        return {'success': False, 'error': str(e)}

def run_test(quick=True):
    """
    Test USB microphone
    
    Args:
        quick: If True, skip audio recording test
    
    Returns:
        dict: {
            'status': 'pass'/'fail',
            'message': str,
            'microphone': dict,
            'error': str (optional)
        }
    """
    result = {
        'status': 'fail',
        'message': '',
        'microphone': {}
    }
    
    if not SOUNDDEVICE_AVAILABLE:
        result['error'] = 'sounddevice not installed (pip install sounddevice numpy)'
        result['message'] = 'Cannot test - missing dependencies'
        return result
    
    try:
        # Find USB microphone
        mic_idx, mic_info = find_usb_microphone()
        
        if mic_idx is None:
            result['error'] = mic_info
            result['message'] = 'No microphone found'
            return result
        
        # Test basic connectivity
        basic_test = test_microphone_basic(mic_idx)
        result['microphone'] = basic_test
        
        if not basic_test['success']:
            result['error'] = basic_test.get('error', 'Unknown error')
            result['message'] = 'Microphone not accessible'
            return result
        
        # Test audio capture (if not quick mode)
        if not quick:
            audio_test = test_microphone_audio(mic_idx, duration=2.0)
            
            if audio_test['success']:
                result['microphone'].update(audio_test)
                
                if audio_test.get('has_signal'):
                    result['status'] = 'pass'
                    result['message'] = f"Microphone working | RMS: {audio_test['rms_level']:.4f}"
                else:
                    result['status'] = 'pass'  # Still pass, just low signal
                    result['message'] = f"Microphone connected but low/no signal detected"
            else:
                result['error'] = audio_test.get('error', 'Audio test failed')
                result['message'] = 'Audio capture failed'
        else:
            # Quick mode - just check connectivity
            result['status'] = 'pass'
            result['message'] = f"Microphone detected: {basic_test['name']}"
        
    except Exception as e:
        result['status'] = 'fail'
        result['error'] = str(e)
        result['message'] = 'Microphone test failed'
    
    return result

def main():
    """Standalone test execution"""
    print("="*60)
    print("USB Microphone Test")
    print("="*60)
    
    if not SOUNDDEVICE_AVAILABLE:
        print("\n✗ sounddevice library not installed")
        print("Install with: pip3 install sounddevice numpy")
        return 1
    
    print("\nAvailable Audio Devices:")
    print("-"*60)
    devices = list_audio_devices()
    if devices:
        for idx, device in enumerate(devices):
            dev_type = []
            if device['max_input_channels'] > 0:
                dev_type.append(f"IN:{device['max_input_channels']}")
            if device['max_output_channels'] > 0:
                dev_type.append(f"OUT:{device['max_output_channels']}")
            print(f"  [{idx}] {device['name']} ({', '.join(dev_type)})")
    print()
    
    # Find and test microphone
    mic_idx, mic_info = find_usb_microphone()
    
    if mic_idx is None:
        print(f"✗ No microphone found: {mic_info}")
        return 1
    
    print(f"Found Microphone: {mic_info['name']}")
    print(f"  Device Index: {mic_idx}")
    print(f"  Channels: {mic_info['max_input_channels']}")
    print(f"  Sample Rate: {mic_info['default_samplerate']} Hz")
    print()
    
    # Test basic connectivity
    print("Testing Basic Connectivity...")
    basic_test = test_microphone_basic(mic_idx)
    
    if basic_test['success']:
        print("✓ Microphone accessible")
    else:
        print(f"✗ Microphone test failed: {basic_test.get('error', 'Unknown')}")
        return 1
    
    # Ask for audio test
    print("\n" + "="*60)
    try:
        response = input("Test audio recording? This will record 2 seconds (y/n): ").strip().lower()
    except KeyboardInterrupt:
        print("\n\nTest cancelled")
        return 0
    
    if response == 'y':
        print("\n" + "="*60)
        print("Audio Recording Test")
        print("="*60)
        
        audio_test = test_microphone_audio(mic_idx, duration=2.0)
        
        if audio_test['success']:
            print(f"\n✓ Recording successful!")
            print(f"  Sample Rate: {audio_test['sample_rate']} Hz")
            print(f"  Duration: {audio_test['duration']}s")
            print(f"  RMS Level: {audio_test['rms_level']:.6f}")
            print(f"  Peak Level: {audio_test['peak_level']:.6f}")
            
            if audio_test['has_signal']:
                print(f"\n✓ Audio signal detected - microphone is working!")
            else:
                print(f"\n⚠ Low or no audio detected")
                print("  Make sure to speak into the microphone during recording")
                print("  Check microphone volume/gain settings")
        else:
            print(f"\n✗ Recording failed: {audio_test.get('error', 'Unknown')}")
            return 1
    
    print("\n" + "="*60)
    print("✓ Microphone test complete!")
    print("="*60)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
