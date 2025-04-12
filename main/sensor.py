#!/usr/bin/python
# -*- coding:utf-8 -*-
from config import PAJ7620U2_I2C_ADDRESS, Init_Gesture_Array, Init_Register_Array, PAJ_BANK_SELECT, NAV_AUDIO_DIR
from config import PAJ_INT_FLAG1, PAJ_UP, PAJ_DOWN, PAJ_LEFT, PAJ_RIGHT, PAJ_FORWARD, PAJ_BACKWARD
from config import PAJ_CLOCKWISE, PAJ_COUNT_CLOCKWISE, PAJ_WAVE
from config import PAJ_SUSPEND, PAJ_PS_HIGH_THRESHOLD, PAJ_PS_LOW_THRESHOLD, PAJ_PS_APPROACH_STATE
from config import PAJ_OBJ_BRIGHTNESS, PAJ_OBJ_SIZE_L, PAJ_OBJ_SIZE_H, PAJ_PS_DATA
from config import PAJ_PS_GAIN, PAJ_IDLE_S1_STEP_L, PAJ_IDLE_S1_STEP_H, PAJ_IDLE_S2_STEP_L
import os
import sys
import time
import subprocess
import threading
import smbus2 as smbus

# Import configuration constants and initialization arrays from config.py
from config import (
    PAJ7620U2_I2C_ADDRESS,
    PAJ_BANK_SELECT,
    Init_Register_Array,
    Init_Gesture_Array,
    PAJ_INT_FLAG1,
    PAJ_UP, PAJ_DOWN, PAJ_LEFT, PAJ_RIGHT, PAJ_FORWARD, PAJ_BACKWARD,
    PAJ_CLOCKWISE, PAJ_COUNT_CLOCKWISE, PAJ_WAVE
)
# Import task information function (for accessing navigation audio tasks)
from task_manager import read_task_info

from task_manager import read_task_info
#!/usr/bin/python
# -*- coding:utf-8 -*-

import os
import sys
import time
import subprocess
import smbus2 as smbus

# Import sensor configuration settings from config.py
from config import (
    PAJ7620U2_I2C_ADDRESS,
    Init_Gesture_Array,
    PAJ_UP,
    PAJ_DOWN,
    PAJ_LEFT,
    PAJ_RIGHT,
    PAJ_FORWARD,
    PAJ_BACKWARD,
    NAV_AUDIO_DIR
)
# Import task information function (for accessing navigation audio tasks)
from task_manager import read_task_info

class PAJ7620U2(object):
    def __init__(self, address=PAJ7620U2_I2C_ADDRESS):
        self._address = address
        try:
            self._bus = smbus.SMBus(1)   # open I2C bus 1
            time.sleep(0.5)              # delay for sensor power-up
        except Exception as e:
            print(f"Error opening I2C bus: {e}")
            sys.exit(1)

        # Load tasks (for navigation audio) using task_manager's function
        self.tasks = read_task_info()
        self.current_task = 1   # Initialize current task as an instance variable
        self._initialize_sensor()

    def _initialize_sensor(self):
        try:
            # Check if sensor is responsive (e.g., register 0x00 should return 0x20)
            if self._read_byte(0x00) == 0x20:
                print("\nGesture Sensor READY\n")
                for reg, val in Init_Gesture_Array:
                    self._write_byte(reg, val)
            else:
                print("\nGesture Sensor NOT READY - check connections\n")
                time.sleep(2)
        except Exception as e:
            print(f"Error initializing sensor: {e}")

    def _read_byte(self, cmd):
        """Read a single byte from the given register."""
        return self._bus.read_byte_data(self._address, cmd)

    def _write_byte(self, cmd, val):
        """Write a byte to the given register."""
        self._bus.write_byte_data(self._address, cmd, val)

    def _read_u16(self, cmd):
        """Read two consecutive bytes and return a 16-bit value."""
        LSB = self._bus.read_byte_data(self._address, cmd)
        MSB = self._bus.read_byte_data(self._address, cmd + 1)
        return (MSB << 8) + LSB

    def play_audio(self, file_path):
        """Play an audio file using ffplay asynchronously."""
        try:
            if not os.path.exists(file_path):
                print(f"Error: Audio file not found: {file_path}")
                return
            file_ext = os.path.splitext(file_path)[1].lower()
            print(f"Playing audio with ffplay... ({file_ext})")
            subprocess.Popen(
                ["ffplay", "-nodisp", "-autoexit", file_path],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
        except Exception as e:
            print(f"Error playing audio: {e}")

    def check_gesture(self):
        """
        Read and process gesture data.
        Depending on the gesture detected, perform actions like playing
        audio or changing the navigation task.
        A debounce delay is introduced after processing a gesture.
        """
        try:
            # Read gesture data from register 0x43 (assumed to hold gesture flags)
            Gesture_Data = self._read_u16(0x43)
        except Exception as e:
            print(f"Error reading gesture data: {e}")
            return 0

        if Gesture_Data != 0:
            print(f"Gesture Data: {Gesture_Data}")

        if Gesture_Data == PAJ_UP:
            print("Gesture UP detected: Turning OFF Bluetooth and playing 'bluetoothoff.mp3'")
            os.system("bluetoothctl power off")
            bluetooth_off_file = os.path.join(NAV_AUDIO_DIR, "bluetoothoff.mp3")
            self.play_audio(bluetooth_off_file)
            time.sleep(0.5)
        elif Gesture_Data == PAJ_DOWN:
            print(f"Gesture DOWN detected: Replaying task[{self.current_task}]")
            self.play_audio("/home/senior/RPI_AI_Gesture_Device/audio_test.mp3")
            time.sleep(0.5)
        elif Gesture_Data == PAJ_LEFT:
            if self.current_task > 1:
                self.current_task -= 1
            else:
                self.current_task = 1
            if self.current_task <= len(self.tasks) and self.tasks:
                task = self.tasks[self.current_task - 1]
                print(f"Gesture LEFT detected: Navigating to task[{self.current_task}]")
                task.play_nav_audio()
            else:
                print("Gesture LEFT detected but no task available.")
            time.sleep(0.5)  # added debounce delay for PAJ_LEFT
        elif Gesture_Data == PAJ_RIGHT:
            self.current_task += 1
            if self.current_task > len(self.tasks):
                self.current_task = len(self.tasks)
            if self.current_task <= len(self.tasks) and self.tasks:
                task = self.tasks[self.current_task - 1]
                print(f"Gesture RIGHT detected: Navigating to task[{self.current_task}]")
                task.play_nav_audio()
            else:
                print("Gesture RIGHT detected but no task available.")
            time.sleep(0.5)  # added debounce delay for PAJ_RIGHT
        elif Gesture_Data == PAJ_FORWARD:
            if 1 <= self.current_task <= len(self.tasks) and self.tasks:
                task = self.tasks[self.current_task - 1]
                print(f"Gesture FORWARD detected: Playing audio for task[{self.current_task}]")
                self.play_audio(task.audio_file)
            else:
                print("Gesture FORWARD detected: Invalid task index")
            time.sleep(0.5)
        elif Gesture_Data == PAJ_BACKWARD:
            print("Gesture BACKWARD detected: Turning ON Bluetooth and playing 'bluetoothon.mp3'")
            os.system("rfkill unblock bluetooth")
            os.system("bluetoothctl power on")
            bluetooth_on_file = os.path.join(NAV_AUDIO_DIR, "bluetoothon.mp3")
            self.play_audio(bluetooth_on_file)
            time.sleep(0.5)

        time.sleep(0.1)  # Ensure a short delay after handling gestures
        return Gesture_Data

# For testing sensor functionality independently
if __name__ == '__main__':
    print("\nGesture Sensor Test Program ...\n")
    sensor = PAJ7620U2()
    while True:
        time.sleep(0.05)
        sensor.check_gesture()
