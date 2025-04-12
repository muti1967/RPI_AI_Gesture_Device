#!/usr/bin/python
# -*- coding:utf-8 -*-

import time
from datetime import datetime
from audio_helpers import play_task_audio, play_nav_audio
import subprocess
import os
from config import NAV_AUDIO_DIR

def enter_default_state():
    print("Entering Default State: Monitoring gestures")
    current_task = 1
    total_tasks = 9  # Assuming 9 tasks total
    
    while True:
        print("Default state active at", datetime.now().strftime("%H:%M:%S"))
        gesture = sensor.check_gesture()
        
        if gesture == "RIGHT":
            current_task = min(current_task + 1, total_tasks)
            play_nav_audio(current_task)
            
        elif gesture == "LEFT":
            current_task = max(current_task - 1, 1)
            play_nav_audio(current_task)
            
        elif gesture == "FORWARD":
            play_task_audio(current_task)
            
        elif gesture == "BACKWARD":
            subprocess.run(["bluetoothctl", "power", "on"])
            print("Bluetooth turned ON")
            bluetooth_on_file = os.path.join(NAV_AUDIO_DIR, "bluetoothon.mp3")
            if os.path.exists(bluetooth_on_file):
                subprocess.run(["ffplay", "-nodisp", "-autoexit", bluetooth_on_file],
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
        elif gesture == "DOWN":
            subprocess.run(["bluetoothctl", "power", "off"])
            print("Bluetooth turned OFF")
            bluetooth_off_file = os.path.join(NAV_AUDIO_DIR, "bluetoothoff.mp3")
            if os.path.exists(bluetooth_off_file):
                subprocess.run(["ffplay", "-nodisp", "-autoexit", bluetooth_off_file],
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        time.sleep(0.1)

def enter_editing_state():
    print("Entering Editing State")
    while True:
        gesture = sensor.check_gesture()
        time.sleep(1)
