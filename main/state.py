#!/usr/bin/python
# -*- coding:utf-8 -*-

import time
from datetime import datetime

def enter_default_state():
    print("Entering Default State: Monitoring gestures")
    while True:
        print("Default state active at", datetime.now().strftime("%H:%M:%S"))
        # The variable 'sensor' must be set from the main script.
        gesture = sensor.check_gesture()
        print("Gesture handled, continuing loop...")
        time.sleep(1)  # Add a short delay to prevent blocking

def enter_editing_state():
    print("Entering Editing State")
    while True:
        # The variable 'sensor' must be set from the main script.
        gesture = sensor.check_gesture()
        time.sleep(1)
