#!/usr/bin/python
# -*- coding:utf-8 -*-
import os
import sys
# Insert the initialcode folder at the start of sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'initialcode'))
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
