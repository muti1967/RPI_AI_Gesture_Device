#!/usr/bin/python
# -*- coding:utf-8 -*-

import time
import smbus
from bleak import BleakScanner, BleakClient
import RPi.GPIO as GPIO
import os
import dbus
import dbus.service
from dbus.mainloop.glib import DBusGMainLoop
import subprocess
from datetime import datetime
import threading
import schedule
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import sys
import select
from gpiozero import Button
from bluezero import peripheral
from bluezero import adapter
import asyncio

# ----------------------------------------------------------------
# Sensor Constants and Register Arrays
# ----------------------------------------------------------------

PAJ7620U2_I2C_ADDRESS = 0x73
PAJ_BANK_SELECT = 0xEF
PAJ_SUSPEND = 0x03
PAJ_INT_FLAG1 = 0x43
PAJ_INT_FLAG2 = 0x44
PAJ_STATE = 0x45
PAJ_PS_HIGH_THRESHOLD = 0x69
PAJ_PS_LOW_THRESHOLD = 0x6A
PAJ_PS_APPROACH_STATE = 0x6B
PAJ_PS_DATA = 0x6C
PAJ_OBJ_BRIGHTNESS = 0xB0
PAJ_OBJ_SIZE_L = 0xB1
PAJ_OBJ_SIZE_H = 0xB2

# Gesture detection flags
PAJ_UP = 0x01
PAJ_DOWN = 0x02
PAJ_LEFT = 0x04
PAJ_RIGHT = 0x08
PAJ_FORWARD = 0x10
PAJ_BACKWARD = 0x20
PAJ_CLOCKWISE = 0x40
PAJ_COUNT_CLOCKWISE = 0x80
PAJ_WAVE = 0x100

# Example initialization array for gesture sensor registers
Init_Gesture_Array = (
    (0xEF, 0x00),
    (0x41, 0x00),
    (0x42, 0x00),
    (0xEF, 0x00),
    (0x48, 0x3C),
    (0x49, 0x00),
    (0x51, 0x10),
    (0x83, 0x20),
    (0x9F, 0xF9),
    (0xEF, 0x01),
    (0x01, 0x1E),
    (0x02, 0x0F),
    (0x03, 0x10),
    (0x04, 0x02),
    (0x41, 0x40),
    (0x43, 0x30),
    (0x65, 0x96),
    (0x66, 0x00),
    (0x67, 0x97),
    (0x68, 0x01),
    (0x69, 0xCD),
    (0x6A, 0x01),
    (0x6B, 0xB0),
    (0x6C, 0x04),
    (0x6D, 0x2C),
    (0x6E, 0x01),
    (0x74, 0x00),
    (0xEF, 0x00),
    (0x41, 0xFF),
    (0x42, 0x01),
)

# ----------------------------------------------------------------
# Global Variables and Paths
# ----------------------------------------------------------------

current_task = 1
HOME_DIR = os.path.expanduser("~")
BASE_DIR = os.path.join(HOME_DIR, "RPI_AI_Gesture_Device")
# (You can define additional paths for tasks and audio files as needed)

# ----------------------------------------------------------------
# GPIO Setup
# ----------------------------------------------------------------

try:
    print("Setting GPIO mode to BCM")
    GPIO.setmode(GPIO.BCM)
    print("Setting up GPIO17 as input with pull-up resistor")
    GPIO.setup(17, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    print("GPIO setup complete")
except Exception as e:
    print(f"Error during GPIO setup: {e}")
finally:
    print("GPIO cleanup will happen at program exit")

# ----------------------------------------------------------------
# PAJ7620U2 Sensor Class
# ----------------------------------------------------------------

class PAJ7620U2(object):
    def __init__(self, address=PAJ7620U2_I2C_ADDRESS):
        self._address = address
        self._bus = smbus.SMBus(1)
        time.sleep(0.5)
        self._initialize_sensor()

    def _initialize_sensor(self):
        try:
            if self._read_byte(0x00) == 0x20:
                print("\nGesture Sensor READY\n")
                for reg, val in Init_Gesture_Array:
                    self._write_byte(reg, val)
            else:
                print("\nGesture Sensor NOT READY - check connections\n")
        except Exception as e:
            print(f"Error initializing sensor: {e}")

    def _read_byte(self, cmd):
        return self._bus.read_byte_data(self._address, cmd)

    def _write_byte(self, cmd, val):
        self._bus.write_byte_data(self._address, cmd, val)

    def _read_u16(self, cmd):
        LSB = self._bus.read_byte_data(self._address, cmd)
        MSB = self._bus.read_byte_data(self._address, cmd + 1)
        return (MSB << 8) + LSB

    def play_audio(self, file_path):
        try:
            subprocess.run(["mpg123", file_path], check=True)
        except subprocess.CalledProcessError as e:
            print(f"Error playing audio: {e}")

    def check_gesture(self):
        global current_task
        Gesture_Data = self._read_u16(0x43)
        if Gesture_Data != 0:
            print(f"Gesture Data: {Gesture_Data}")
        if Gesture_Data == PAJ_UP:
            print(f"Gesture UP detected: Playing task[{current_task}]")
            self.play_audio("/home/senior/RPI_AI_Gesture_Device/audio_test.mp3")
        elif Gesture_Data == PAJ_DOWN:
            print(f"Gesture DOWN detected: Replaying task[{current_task}]")
            self.play_audio("/home/senior/RPI_AI_Gesture_Device/audio_test.mp3")
        elif Gesture_Data == PAJ_LEFT:
            if current_task > 1:
                current_task -= 1
            else:
                current_task = 1
            print(f"Left Gesture: Current Task Index is now {current_task}")
        elif Gesture_Data == PAJ_RIGHT:
            # For simplicity, we just increment for this demo.
            current_task += 1
            print(f"Right Gesture: Current Task Index is now {current_task}")
        elif Gesture_Data == PAJ_FORWARD:
            if 1 <= current_task <= len(self.tasks):
                task = self.tasks[current_task - 1]
                print(f"Forward Gesture: Playing task [{current_task}] - {task.audio_file}")
                self.play_audio(task.audio_file)
            else:
                print("Forward Gesture: Invalid task index")
        return Gesture_Data

    def _simulate_gesture(self, gesture):
        global current_task
        if gesture == PAJ_RIGHT:
            if current_task < len(self.tasks):
                current_task += 1
            else:
                current_task = len(self.tasks)
            print(f"Simulated Right Gesture: Current Task Index is now {current_task}")
        elif gesture == PAJ_LEFT:
            if current_task > 1:
                current_task -= 1
            else:
                current_task = 1
            print(f"Simulated Left Gesture: Current Task Index is now {current_task}")
        elif gesture == PAJ_FORWARD:
            if 1 <= current_task <= len(self.tasks):
                task = self.tasks[current_task - 1]
                print(f"Simulated Forward Gesture: Playing task [{current_task}] - {task.audio_file}")
                self.play_audio(task.audio_file)
            else:
                print("Simulated Forward Gesture: Invalid task index")
        return 0

# ----------------------------------------------------------------
# Bluetooth Agent for Classic Bluetooth Pairing
# ----------------------------------------------------------------

class BluetoothAgent(dbus.service.Object):
    def __init__(self, bus, path):
        dbus.service.Object.__init__(self, bus, path)

    @dbus.service.method("org.bluez.Agent1", in_signature="", out_signature="")
    def Release(self):
        print("Release")

    @dbus.service.method("org.bluez.Agent1", in_signature="o", out_signature="")
    def RequestPinCode(self, device):
        print(f"RequestPinCode {device}")
        return "0000"

    @dbus.service.method("org.bluez.Agent1", in_signature="o", out_signature="u")
    def RequestPasskey(self, device):
        print(f"RequestPasskey {device}")
        return dbus.UInt32(0)

    @dbus.service.method("org.bluez.Agent1", in_signature="ouq", out_signature="")
    def DisplayPasskey(self, device, passkey, entered):
        print(f"DisplayPasskey {device} {passkey} {entered}")

    @dbus.service.method("org.bluez.Agent1", in_signature="ou", out_signature="")
    def RequestConfirmation(self, device, passkey):
        print(f"RequestConfirmation {device} {passkey}")
        return

    @dbus.service.method("org.bluez.Agent1", in_signature="os", out_signature="")
    def AuthorizeService(self, device, uuid):
        print(f"AuthorizeService {device} {uuid}")
        return

    @dbus.service.method("org.bluez.Agent1", in_signature="o", out_signature="")
    def Cancel(self, device):
        print(f"Cancel {device}")

def start_bluetooth_agent():
    DBusGMainLoop(set_as_default=True)
    bus = dbus.SystemBus()
    agent = BluetoothAgent(bus, "/test/agent")
    obj = bus.get_object("org.bluez", "/org/bluez")
    manager = dbus.Interface(obj, "org.bluez.AgentManager1")
    try:
        manager.UnregisterAgent("/test/agent")
    except dbus.exceptions.DBusException as e:
        print(f"Agent not registered previously: {e}")
    manager.RegisterAgent("/test/agent", "DisplayYesNo")
    manager.RequestDefaultAgent("/test/agent")
    print("Bluetooth agent started for pairing")

def remove_paired_devices():
    os.system("bluetoothctl -- remove *")
    print("Cleared all previously paired devices.")

# ----------------------------------------------------------------
# BLE Pairing and Advertisement (for BLE Devices)
# ----------------------------------------------------------------

async def enter_pairing_mode():
    print("Entering Bluetooth Pairing Mode")
    remove_paired_devices()

    def blink_led():
        while not connected:
            print("LED ON")
            time.sleep(0.5)
            print("LED OFF")
            time.sleep(0.5)

    connected = False
    blink_thread = threading.Thread(target=blink_led)
    blink_thread.start()

    try:
        print("Waiting for a connection from a phone...")
        while not connected:
            devices = await BleakScanner.discover()
            for device in devices:
                print(device)
                if "YourPhoneName" in device.name:
                    async with BleakClient(device.address) as client:
                        await client.connect()
                        if client.is_connected:
                            connected = True
                            print(f"Connected to {device.name}")
                            break
        print("LED SOLID")
        while connected:
            await asyncio.sleep(1)
            print("Handling data from the phone...")
    except Exception as e:
        print(f"Connection error: {e}")
    finally:
        connected = True
        blink_thread.join()
        print("LED OFF")
        print("Bluetooth Pairing Mode Exited")

# ----------------------------------------------------------------
# State Functions
# ----------------------------------------------------------------

def enter_default_state():
    print("Entering Default State: Monitoring gestures")
    while True:
        # Print a timestamp to show the loop is active
        print("Default state active at", datetime.now().strftime("%H:%M:%S"))
        gesture = sensor.check_gesture()
        time.sleep(1)

def enter_editing_state():
    print("Entering Editing State")
    while True:
        gesture = sensor.check_gesture()
        if gesture == PAJ_RIGHT:
            print("Editing: Navigate to next task")
        elif gesture == PAJ_LEFT:
            print("Editing: Navigate to previous task")
        elif gesture == PAJ_UP:
            print("Editing: Play current task")
        elif gesture == PAJ_DOWN:
            print("Editing: Reset current task")
        time.sleep(1)

# ----------------------------------------------------------------
# BLE Service Definition and Peripheral Setup
# ----------------------------------------------------------------

def read_callback():
    return [ord(c) for c in 'Hello']

service_uuid = '12345678-1234-5678-1234-56789abcdef0'
characteristic_uuid = '12345678-1234-5678-1234-56789abcdef1'

try:
    adapter_list = list(adapter.Adapter.available())
    if not adapter_list:
        raise IndexError("No Bluetooth adapter found.")
    adapter_address = adapter_list[0].address
    print(f"Using Bluetooth adapter address: {adapter_address}")
except IndexError:
    print("Error: No Bluetooth adapter found. Ensure Bluetooth is enabled and available.")
    sys.exit(1)

periph = peripheral.Peripheral(adapter_address=adapter_address, local_name='RPi-BLE')
periph.add_service(1, service_uuid, primary=True)
periph.add_characteristic(1, 1, characteristic_uuid,
                          value=[0x00],
                          notifying=False,
                          flags=['read'],
                          read_callback=read_callback)

# ----------------------------------------------------------------
# BLE Advertising via Button Hold Using gpiozero
# ----------------------------------------------------------------

def advertise_ble():
    print("Button held for 3 seconds. Starting BLE advertising...")
    os.system("rfkill unblock bluetooth")
    os.system("bluetoothctl power on")
    try:
        periph.publish()
        print("BLE advertising active. Device should be discoverable as 'RPi-BLE'.")
        time.sleep(10)  # Advertise for 10 seconds
        periph.unpublish()
        print("Stopped BLE advertising.")
    except Exception as e:
        print(f"Error during BLE advertising: {e}")

ble_button = Button(17, pull_up=True, hold_time=3)
ble_button.when_held = advertise_ble

# ----------------------------------------------------------------
# Main Section
# ----------------------------------------------------------------

if __name__ == '__main__':
    print("\nGesture Sensor Test Program ...")
    sensor = PAJ7620U2()
    # For demonstration, assign an empty tasks list (or load tasks as needed)
    sensor.tasks = []
    current_task = 1

    try:
        remove_paired_devices()
        start_bluetooth_agent()
        # The ble_button event will trigger advertise_ble when held for 3 seconds.
        # Enter the default state loop which prints a timestamp and checks for gestures.
        enter_default_state()
    except KeyboardInterrupt:
        print("Exiting program...")
    finally:
        print("Cleaning up GPIO")
        GPIO.cleanup()
