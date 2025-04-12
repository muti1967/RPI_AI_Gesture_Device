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
from add_task import add_task

def enter_default_state():
    print("Entering Default State: Monitoring gestures")
    current_task = 1
    total_tasks = 9
    ble_active = False
    
    while True:
        gesture = sensor.check_gesture()
        if gesture:
            print(f"Detected gesture: {gesture}")
            
        if gesture == "DOWN":
            print("Down gesture detected. Turning off Bluetooth...")
            # Force stop all Bluetooth functionality
            stop_ble_advertising()
            stop_ble_service()
            subprocess.run(["bluetoothctl", "power", "off"], check=True)
            subprocess.run(["rfkill", "block", "bluetooth"], check=True)
            ble_active = False
            
            # Play audio feedback
            bluetooth_off_file = os.path.join(NAV_AUDIO_DIR, "bluetoothoff.mp3")
            if os.path.exists(bluetooth_off_file):
                try:
                    subprocess.run(["ffplay", "-nodisp", "-autoexit", bluetooth_off_file],
                                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                except subprocess.CalledProcessError as e:
                    print(f"Error playing audio: {e}")
            
        elif gesture == "RIGHT":
            current_task = min(current_task + 1, total_tasks)
            play_nav_audio(current_task)
            
        elif gesture == "LEFT":
            current_task = max(current_task - 1, 1)
            play_nav_audio(current_task)
            
        elif gesture == "UP":
            print("Up gesture detected. Starting task recording...")
            new_task = add_task()  # Use default 4-second duration
            if new_task:
                print(f"Task {new_task} added successfully")
                # Reload tasks after adding new one
                sensor.tasks = read_task_info()
        
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
