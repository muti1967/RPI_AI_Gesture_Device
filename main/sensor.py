#!/usr/bin/python
# -*- coding:utf-8 -*-
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
