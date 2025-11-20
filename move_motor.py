#!/usr/bin/env python3
import requests
import sys
import time

MOONRAKER_URL = "http://localhost:7125"

def move_manual_stepper(stepper_name, distance, speed):
    """
    Moves a manual stepper using Klipper's MANUAL_STEPPER command.
    """
    # Construct G-Code command
    # ENABLE=1 ensures the stepper is powered
    # MOVE=distance sets the target position relative to current if we don't set SET_POSITION
    # However, MANUAL_STEPPER MOVE is absolute by default unless we use relative mode or sync?
    # Actually, for manual_stepper, MOVE is a relative move if we don't specify SET_POSITION? 
    # No, "The MOVE parameter specifies the target position." (Absolute)
    # To do a relative move, we can use SET_POSITION=0 first.
    
    print(f"Attempting to move {stepper_name} by {distance}mm at {speed}mm/s...")

    # 1. Reset position to 0 so our move is relative
    cmd_reset = f"MANUAL_STEPPER STEPPER={stepper_name} SET_POSITION=0"
    requests.post(f"{MOONRAKER_URL}/printer/gcode/script", params={"script": cmd_reset})
    
    # 2. Execute Move (Blocking with SYNC=1)
    cmd_move = f"MANUAL_STEPPER STEPPER={stepper_name} ENABLE=1 MOVE={distance} SPEED={speed} SYNC=1"
    response = requests.post(f"{MOONRAKER_URL}/printer/gcode/script", params={"script": cmd_move})
    
    if response.status_code == 200:
        print(f"✓ Move complete: {cmd_move}")
        
        # 3. Release Motor
        cmd_release = f"MANUAL_STEPPER STEPPER={stepper_name} ENABLE=0"
        requests.post(f"{MOONRAKER_URL}/printer/gcode/script", params={"script": cmd_release})
        print(f"✓ Motor released")
    else:
        print(f"✗ Failed: {response.text}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 move_motor.py <stepper_name> [distance] [speed]")
        print("Example: python3 move_motor.py stepper_0 10 10")
        sys.exit(1)
        
    stepper = sys.argv[1]
    dist = sys.argv[2] if len(sys.argv) > 2 else "10"
    speed = sys.argv[3] if len(sys.argv) > 3 else "10"
    
    move_manual_stepper(stepper, dist, speed)
