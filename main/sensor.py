#!/usr/bin/python
# -*- coding:utf-8 -*-
import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'initialcode'))
import time
from initialcode.PAJ7620U2 import PAJ7620U2  # Use the original gesture sensor logic

# Optionally, wrap it for uniformity (here it simply inherits without change)
class GestureSensor(PAJ7620U2):
    pass

if __name__ == '__main__':
    print("\nGesture Sensor Test Program ...\n")
    sensor = GestureSensor()
    while True:
        sensor.check_gesture()
        time.sleep(0.05)
