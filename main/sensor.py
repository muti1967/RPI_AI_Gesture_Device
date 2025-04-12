#!/usr/bin/python
# -*- coding:utf-8 -*-
import os
import sys
# Insert the absolute path for the initialcode folder into sys.path
initialcode_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'initialcode'))
sys.path.insert(0, initialcode_path)
import time
from initialcode.PAJ7620U2 import PAJ7620U2  # Use the original gesture sensor logic

# Wrap the sensor class for uniformity
class GestureSensor(PAJ7620U2):
    pass

# Export PAJ7620U2 from this module (alias GestureSensor) for compatibility with other files
PAJ7620U2 = GestureSensor

if __name__ == '__main__':
    print("\nGesture Sensor Test Program ...\n")
    sensor = GestureSensor()
    while True:
        sensor.check_gesture()
        time.sleep(0.05)
