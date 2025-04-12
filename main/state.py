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
        if gesture:
            print(f"Detected gesture: {gesture}")
            
        if gesture == "DOWN":
            print("Down gesture detected. Turning off Bluetooth...")
            stop_ble_advertising()
            stop_ble_service()
            # Add delay to ensure cleanup completes
            time.sleep(1)
            subprocess.run(["bluetoothctl", "power", "off"], check=False)
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
            
        elif gesture == "FORWARD":
            play_task_audio(current_task)
            
        elif gesture == "BACKWARD":
            if not ble_active:
                print("Backward gesture detected. Starting BLE...")
                # Ensure clean state before starting
                stop_ble_service()
                time.sleep(1)
                
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
