#!/usr/bin/python
# -*- coding:utf-8 -*-
import os
import sys
import time

# Add parent directory to Python path to find initialcode module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from initialcode.PAJ7620U2 import PAJ7620U2

# Wrap the sensor class for uniformity
class GestureSensor(PAJ7620U2):
    def __init__(self):
        super().__init__()
        self.tasks = []  # Initialize empty tasks list
        self.current_task = 1

    def check_gesture(self):
        data = self._read_byte(PAJ_INT_FLAG1)
        if data == PAJ_UP:
            return "UP"
        elif data == PAJ_DOWN:
            return "DOWN"
        elif data == PAJ_LEFT:
            return "LEFT"
        elif data == PAJ_RIGHT:
            return "RIGHT"
        elif data == PAJ_FORWARD:
            return "FORWARD"
        elif data == PAJ_BACKWARD:
            return "BACKWARD"
        return None

# Export PAJ7620U2 from this module (alias GestureSensor) for compatibility with other files
PAJ7620U2 = GestureSensor

if __name__ == '__main__':
    print("\nGesture Sensor Test Program ...\n")
    sensor = GestureSensor()
    while True:
        gesture = sensor.check_gesture()
        if gesture:
            print(f"Detected gesture: {gesture}")
        time.sleep(0.05)
