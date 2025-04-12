#!/usr/bin/python
# -*- coding:utf-8 -*-

import time
from datetime import datetime
from audio_helpers import play_task_audio, play_nav_audio
import subprocess
import os
from config import NAV_AUDIO_DIR
from ble_service import start_ble_advertising, stop_ble_advertising, stop_ble_service
import threading

def enter_default_state():
    print("Entering Default State: Monitoring gestures")
    current_task = 1
    total_tasks = 9
    ble_active = False
    
    while True:
        gesture = sensor.check_gesture()
        if gesture:  # Only print when gesture is detected
            print(f"Detected gesture: {gesture}")
            
        if gesture == "DOWN" and ble_active:
            print("Down gesture detected. Turning off Bluetooth...")
            stop_ble_advertising()
            stop_ble_service()
            subprocess.run(["bluetoothctl", "power", "off"])
            bluetooth_off_file = os.path.join(NAV_AUDIO_DIR, "bluetoothoff.mp3")
            if os.path.exists(bluetooth_off_file):
                subprocess.run(["ffplay", "-nodisp", "-autoexit", bluetooth_off_file],
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            ble_active = False
            
        elif gesture == "RIGHT":
            current_task = min(current_task + 1, total_tasks)
            play_nav_audio(current_task)
            
        elif gesture == "LEFT":
            current_task = max(current_task - 1, 1)
            play_nav_audio(current_task)
            
        elif gesture == "FORWARD":
            play_task_audio(current_task)
            
        elif gesture == "BACKWARD":
            if not ble_active:
                print("Backward gesture detected. Starting BLE...")
                # Start BLE advertising in a separate thread
                def start_ble():
                    nonlocal ble_active
                    ble_active = start_ble_advertising()
                
                ble_thread = threading.Thread(target=start_ble)
                ble_thread.daemon = True
                ble_thread.start()
                
                # Play audio feedback
                bluetooth_on_file = os.path.join(NAV_AUDIO_DIR, "bluetoothon.mp3")
                if os.path.exists(bluetooth_on_file):
                    subprocess.run(["ffplay", "-nodisp", "-autoexit", bluetooth_on_file],
                                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        time.sleep(0.1)

def enter_editing_state():
    print("Entering Editing State")
    while True:
        gesture = sensor.check_gesture()
        time.sleep(1)
