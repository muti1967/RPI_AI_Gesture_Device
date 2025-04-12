#!/usr/bin/python
# -*- coding:utf-8 -*-

import os
import sys
import time
import threading
import schedule
import subprocess
from datetime import datetime
import RPi.GPIO as GPIO

# ----------------------------------------------------------------
# Pre-Initialization: Clear leftover GPIO state and disable warnings
# ----------------------------------------------------------------
GPIO.setwarnings(False)
GPIO.cleanup()        # Free any leftover resources
GPIO.setmode(GPIO.BCM)  # Ensure BCM numbering is used

# ----------------------------------------------------------------
# Import Modules
# ----------------------------------------------------------------
from audio_helpers import play_bootup_sound
from task_manager import schedule_tasks, read_task_info, InfoFileHandler
from sensor import PAJ7620U2
from bluetooth_agent import remove_paired_devices, start_bluetooth_agent
from ble_service import init_ble  # Update import
from ble_pairing import enter_pairing_mode
import state

print("\nGesture Sensor Test Program ...")
from config import INFO_FILE_PATH, AUDIO_FILES_DIR, NAV_AUDIO_DIR

if os.path.exists(INFO_FILE_PATH):
    print("Removing existing info.txt to ensure fresh start...")
    os.remove(INFO_FILE_PATH)

sensor = PAJ7620U2()
# Set global variable for current_task (used by sensor.check_gesture)
current_task = 1

# Initialize tasks before creating threads
sensor.tasks = read_task_info()

# Make sensor available to state functions via module-level variable
state.sensor = sensor

# Play bootup sound once at startup.
play_bootup_sound()

try:
    os.makedirs(os.path.dirname(INFO_FILE_PATH), exist_ok=True)
    os.makedirs(AUDIO_FILES_DIR, exist_ok=True)
    os.makedirs(NAV_AUDIO_DIR, exist_ok=True)

    # Start scheduler thread for tasks
    if sensor.tasks:  # Only start scheduler if there are tasks
        scheduler_thread = threading.Thread(target=schedule_tasks, args=(sensor.tasks,))
        scheduler_thread.daemon = True
        scheduler_thread.start()

    # Start file observer to monitor info.txt changes.
    from watchdog.observers import Observer
    event_handler = InfoFileHandler(sensor)
    observer = Observer()
    observer.schedule(event_handler, path=os.path.dirname(INFO_FILE_PATH), recursive=False)
    observer.start()
    print(f"Monitoring {INFO_FILE_PATH} for changes...")
    print(f"Total number of tasks: {len(sensor.tasks)}")
    print("Current task: 1")

    # Initialize Bluetooth components first
    remove_paired_devices()
    start_bluetooth_agent()

    # Initialize Bluetooth and BLE
    from ble_service import ensure_bluetooth_powered
    ensure_bluetooth_powered()  # Make sure Bluetooth is powered before starting state thread

    # Start the default state thread last
    default_state_thread = threading.Thread(target=state.enter_default_state)
    default_state_thread.daemon = True
    default_state_thread.start()

    # Mainloop - handle exceptions and keep program running
    while True:
        try:
            time.sleep(0.1)
        except dbus.exceptions.DBusException as e:
            print(f"DBus error (continuing): {e}")
            continue

except KeyboardInterrupt:
    print("Exiting program...")
    observer.stop()
finally:
    observer.join()
    print("Cleaning up GPIO")
    GPIO.cleanup()
