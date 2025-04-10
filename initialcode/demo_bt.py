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

# ----------------------------------------------------------------
# Sensor/gesture constants and register arrays (unchanged)
# ----------------------------------------------------------------

# i2c address
PAJ7620U2_I2C_ADDRESS = 0x73
# Register Bank select
PAJ_BANK_SELECT = 0xEF  # Bank0== 0x00,Bank1== 0x01
# Register Bank 0
PAJ_SUSPEND = 0x03  # I2C suspend command (Write = 0x01 to enter suspend state).
PAJ_INT_FLAG1_MASK = 0x41  # Gesture detection interrupt flag mask
PAJ_INT_FLAG2_MASK = 0x42  # Gesture/PS detection interrupt flag mask
PAJ_INT_FLAG1 = 0x43  # Gesture detection interrupt flag
PAJ_INT_FLAG2 = 0x44  # Gesture/PS detection interrupt flag
PAJ_STATE = 0x45  # State indicator for gesture detection
PAJ_PS_HIGH_THRESHOLD = 0x69  # PS hysteresis high threshold
PAJ_PS_LOW_THRESHOLD = 0x6A  # PS hysteresis low threshold
PAJ_PS_APPROACH_STATE = 0x6B  # PS approach state
PAJ_PS_DATA = 0x6C  # PS 8 bit data
PAJ_OBJ_BRIGHTNESS = 0xB0  # Object Brightness (Max. 255)
PAJ_OBJ_SIZE_L = 0xB1  # Object Size (Low 8 bit)
PAJ_OBJ_SIZE_H = 0xB2  # Object Size (High 8 bit)
# Register Bank 1
PAJ_PS_GAIN = 0x44  # PS gain setting
PAJ_IDLE_S1_STEP_L = 0x67
PAJ_IDLE_S1_STEP_H = 0x68
PAJ_IDLE_S2_STEP_L = 0x69
PAJ_IDLE_S2_STEP_H = 0x6A
PAJ_OPTOS1_TIME_L = 0x6B
PAJ_OPTOS2_TIME_H = 0x6C
PAJ_S1TOS2_TIME_L = 0x6D
PAJ_S1TOS2_TIME_H = 0x6E
PAJ_EN = 0x72  # Enable/Disable sensor

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

# ----------------------------------------------------------------
# Global Variables & Task Setup
# ----------------------------------------------------------------

current_task = 1  # Initialize task index

# Define file paths
HOME_DIR = os.path.expanduser("~")
BASE_DIR = os.path.join(HOME_DIR, "RPI_AI_Gesture_Device")
INFO_FILE_PATH = os.path.join(BASE_DIR, "finalv/info/info.txt")
AUDIO_FILES_DIR = os.path.join(BASE_DIR, "finalv/audio_files")
NAV_AUDIO_DIR = os.path.join(AUDIO_FILES_DIR, "navaudio")

# ----------------------------------------------------------------
# Task class and file handler (unchanged)
# ----------------------------------------------------------------

class Task:
    def __init__(self, task_number, audio_file, play_time):
        self.task_number = task_number
        self.audio_file = os.path.join(AUDIO_FILES_DIR, audio_file)  # Full path
        self.play_time = play_time
        self.completed = False

    def play_nav_audio(self):
        nav_file = os.path.join(NAV_AUDIO_DIR, f"{self.task_number}.mp3")
        if os.path.exists(nav_file):
            try:
                subprocess.run(["ffplay", "-nodisp", "-autoexit", nav_file], 
                               capture_output=True, text=True)
            except Exception as e:
                print(f"Error playing navigation audio: {e}")

class InfoFileHandler(FileSystemEventHandler):
    def __init__(self, sensor):
        self.sensor = sensor
        self.last_modified = 0

    def on_modified(self, event):
        if event.src_path == INFO_FILE_PATH:
            current_time = time.time()
            if current_time - self.last_modified > 1:
                print("Info file changed, reloading tasks...")
                self.sensor.tasks = read_task_info()
                schedule.clear()
                for task in self.sensor.tasks:
                    schedule.every().day.at(task.play_time).do(play_scheduled_audio, task)
                self.last_modified = current_time

def read_task_info():
    tasks = []
    try:
        with open(INFO_FILE_PATH, 'r') as file:
            for line in file:
                line = line.strip()
                if line:
                    task_number, audio_file, play_time = line.split(',')
                    audio_path = os.path.join(AUDIO_FILES_DIR, audio_file)
                    if not os.path.exists(audio_path):
                        print(f"Warning: Audio file not found: {audio_path}")
                    tasks.append(Task(int(task_number), audio_file, play_time))
        if len(tasks) < 9:
            print("Updating info.txt to include all 9 tasks...")
            with open(INFO_FILE_PATH, 'w') as file:
                for i in range(1, 10):
                    file.write(f"{i},{i}.mp3,09:00\n")
            tasks = []
            with open(INFO_FILE_PATH, 'r') as file:
                for line in file:
                    line = line.strip()
                    if line:
                        task_number, audio_file, play_time = line.split(',')
                        tasks.append(Task(int(task_number), audio_file, play_time))
        print(f"Loaded {len(tasks)} tasks from info.txt")
        return tasks
    except FileNotFoundError:
        print(f"{INFO_FILE_PATH} not found. Creating default file with 9 tasks...")
        os.makedirs(os.path.dirname(INFO_FILE_PATH), exist_ok=True)
        with open(INFO_FILE_PATH, 'w') as file:
            for i in range(1, 10):
                file.write(f"{i},{i}.mp3,09:00\n")
        return read_task_info()
    except Exception as e:
        print(f"Error reading {INFO_FILE_PATH}: {e}")
        return []

def play_scheduled_audio(task):
    if not task.completed:
        print(f"Playing task {task.task_number}: {task.audio_file}")
        if not os.path.exists(task.audio_file):
            print(f"Error: Audio file not found: {task.audio_file}")
            return
        file_ext = os.path.splitext(task.audio_file)[1].lower()
        print(f"Playing audio with ffplay... ({file_ext})")
        result = subprocess.run(["ffplay", "-nodisp", "-autoexit", task.audio_file],
                                capture_output=True, text=True)
        if result.returncode != 0:
            print(f"Error playing audio with ffplay: {result.stderr}")
            print("Check if:")
            print("1. ffplay is installed (sudo apt-get install ffmpeg)")
            print("2. The audio system is properly configured")
            print("3. The file format is supported")

def schedule_tasks(tasks):
    for task in tasks:
        schedule.every().day.at(task.play_time).do(play_scheduled_audio, task)
    while True:
        schedule.run_pending()
        time.sleep(1)

def get_keyboard_input():
    if select.select([sys.stdin], [], [], 0.0)[0]:
        return sys.stdin.read(1)
    return None

def handle_keyboard_input(sensor):
    while True:
        key = get_keyboard_input()
        if key:
            if key == 'l':
                print("Simulating LEFT gesture")
                sensor._simulate_gesture(PAJ_LEFT)
            elif key == 'r':
                print("Simulating RIGHT gesture")
                sensor._simulate_gesture(PAJ_RIGHT)
            elif key == 'd':
                print("Simulating DOWN gesture")
                sensor._simulate_gesture(PAJ_DOWN)
            elif key == 'f':
                print("Simulating FORWARD gesture")
                sensor._simulate_gesture(PAJ_FORWARD)
            elif key == 'cc':
                print("Simulating COUNTER-CLOCKWISE gesture")
                sensor._simulate_gesture(PAJ_COUNT_CLOCKWISE)
            elif key == 'q':
                print("Quitting program...")
                sys.exit(0)
        time.sleep(0.1)

# ----------------------------------------------------------------
# PAJ7620U2 sensor class (with placeholder methods)
# ----------------------------------------------------------------

class PAJ7620U2(object):
    def __init__(self, address=PAJ7620U2_I2C_ADDRESS):
        self._address = address
        self._bus = None
        self.tasks = read_task_info()
        self._test_audio_system()
        self.keyboard_thread = threading.Thread(target=handle_keyboard_input, args=(self,))
        self.keyboard_thread.daemon = True
        self.keyboard_thread.start()

    def _initialize_i2c(self):
        print("Skipping I2C initialization as the gesture sensor is not connected.")

    def _initialize_sensor(self):
        print("Skipping sensor initialization as the gesture sensor is not connected.")

    def check_gesture(self):
        print("Skipping gesture check as the gesture sensor is not connected.")
        return 0

    def _read_byte(self, cmd):
        try:
            return self._bus.read_byte_data(self._address, cmd)
        except Exception as e:
            print(f"Error reading byte at address 0x{cmd:02X}: {e}")
            raise

    def _write_byte(self, cmd, val):
        try:
            self._bus.write_byte_data(self._address, cmd, val)
        except Exception as e:
            print(f"Error writing byte 0x{val:02X} to address 0x{cmd:02X}: {e}")
            raise

    def _read_u16(self, cmd):
        LSB = self._bus.read_byte_data(self._address, cmd)
        MSB = self._bus.read_byte_data(self._address, cmd + 1)
        return (MSB << 8) + LSB

    def _test_audio_system(self):
        print("Testing audio system...")
        try:
            subprocess.run(["speaker-test", "-t", "wav", "-c", "2", "-D", "hw:0,0", "-l", "1"],
                           capture_output=True)
            print("Audio system test completed")
        except Exception as e:
            print(f"Warning: Audio system test failed: {e}")
            print("Please check your audio configuration using 'alsamixer'")

    def play_audio(self, file_path):
        try:
            if not os.path.exists(file_path):
                print(f"Error: Audio file not found: {file_path}")
                return
            file_ext = os.path.splitext(file_path)[1].lower()
            print(f"Playing audio with ffplay... ({file_ext})")
            result = subprocess.run(["ffplay", "-nodisp", "-autoexit", file_path],
                                    capture_output=True, text=True)
            if result.returncode != 0:
                print(f"Error playing audio with ffplay: {result.stderr}")
                print("Ensure:")
                print("1. ffplay is installed (sudo apt-get install ffmpeg)")
                print("2. The audio system is configured")
                print("3. The file format is supported")
        except Exception as e:
            print(f"Error playing audio: {e}")
            print("Ensure:")
            print("1. The audio file exists and is accessible")
            print("2. ffplay is installed (sudo apt-get install ffmpeg)")
            print("3. The audio system is properly configured")

    def _simulate_gesture(self, gesture):
        global current_task
        if gesture == PAJ_LEFT:
            current_task = max(1, current_task - 1)
            if 1 <= current_task <= len(self.tasks):
                task = self.tasks[current_task - 1]
                print(f"Moving to task[{current_task}] of {len(self.tasks)}")
                task.play_nav_audio()
        elif gesture == PAJ_RIGHT:
            current_task = min(current_task + 1, len(self.tasks))
            if 1 <= current_task <= len(self.tasks):
                task = self.tasks[current_task - 1]
                print(f"Moving to task[{current_task}] of {len(self.tasks)}")
                task.play_nav_audio()
        elif gesture == PAJ_DOWN:
            current_task = max(1, current_task - 1)
            if 1 <= current_task <= len(self.tasks):
                task = self.tasks[current_task - 1]
                print(f"Moving to task[{current_task}] of {len(self.tasks)}")
                task.play_nav_audio()
        elif gesture == PAJ_FORWARD:
            if 1 <= current_task <= len(self.tasks):
                task = self.tasks[current_task - 1]
                print(f"Playing task[{current_task}] of {len(self.tasks)}")
                self.play_audio(task.audio_file)
        elif gesture == PAJ_COUNT_CLOCKWISE:
            if 1 <= current_task <= len(self.tasks):
                self.tasks[current_task - 1].completed = False
                print(f"Task[{current_task}] of {len(self.tasks)} marked incomplete")
        return 0

# ----------------------------------------------------------------
# Bluetooth Agent for Classic Bluetooth (unchanged)
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
# BLE Pairing & Advertisement Section (Modified)
# ----------------------------------------------------------------

async def enter_pairing_mode():
    print("Entering Bluetooth Pairing Mode")
    remove_paired_devices()

    # LED blinking simulation
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

def check_button_press():
    button_press_count = 0
    button_pressed_time = 0
    start_time = time.time()
    while True:
        if GPIO.input(17) == GPIO.LOW:
            button_pressed_time += 1
            print(f"Button held for {button_pressed_time * 0.1} seconds")
            time.sleep(0.1)
            if button_pressed_time >= 30:  # ~3 seconds
                print("Button held for 3 seconds, entering pairing mode...")
                import asyncio
                asyncio.run(enter_pairing_mode())
                break
        else:
            if button_pressed_time > 0:
                button_press_count += 1
                print(f"Button pressed {button_press_count} time(s)")
                button_pressed_time = 0
                time.sleep(0.1)
            if button_press_count >= 2 and (time.time() - start_time) <= 3:
                print("Button pressed 2 times within 3 seconds, entering editing mode...")
                enter_editing_state()
                break
            elif (time.time() - start_time) > 3:
                button_press_count = 0
                start_time = time.time()
        time.sleep(0.1)

def play_task_1_periodically(sensor):
    task_1_audio_path = os.path.join(BASE_DIR, "finalv/audio_files/1.mp3")
    task_2_audio_path = os.path.join(BASE_DIR, "finalv/audio_files/2.mp3")
    play_task_1 = True
    while True:
        current_audio_path = task_1_audio_path if play_task_1 else task_2_audio_path
        if os.path.exists(current_audio_path):
            print(f"Playing {'task 1' if play_task_1 else 'task 2'} periodically...")
            try:
                subprocess.run(["ffplay", "-nodisp", "-autoexit", current_audio_path],
                               capture_output=True, text=True)
            except Exception as e:
                print(f"Error playing {'task 1' if play_task_1 else 'task 2'} audio: {e}")
        else:
            print(f"{'Task 1' if play_task_1 else 'Task 2'} audio file not found: {current_audio_path}")
        play_task_1 = not play_task_1
        time.sleep(15)

def enter_editing_state():
    print("Entering Editing State")
    while True:
        gesture = sensor.check_gesture()
        if gesture == PAJ_RIGHT:
            print("Navigating to next task")
        elif gesture == PAJ_LEFT:
            print("Navigating to previous task")
        elif gesture == PAJ_UP:
            print("Playing current task")
        elif gesture == PAJ_DOWN:
            print("Resetting audio for current task")
        check_button_press()

# ----------------------------------------------------------------
# BLE Service Definition and Advertising (Modified)
# ----------------------------------------------------------------

def read_callback():
    return [ord(c) for c in 'Hello']

# Define BLE service and characteristic UUIDs
service_uuid = '12345678-1234-5678-1234-56789abcdef0'
characteristic_uuid = '12345678-1234-5678-1234-56789abcdef1'

# Get the Bluetooth adapter address
try:
    adapter_list = list(adapter.Adapter.available())
    if not adapter_list:
        raise IndexError("No Bluetooth adapter found.")
    adapter_address = adapter_list[0].address
    print(f"Using Bluetooth adapter address: {adapter_address}")
except IndexError:
    print("Error: No Bluetooth adapter found. Ensure Bluetooth is enabled and available.")
    sys.exit(1)

# Initialize BLE Peripheral
periph = peripheral.Peripheral(adapter_address=adapter_address, local_name='RPi-BLE')

# Add BLE service and characteristic via Bluezero
periph.add_service(uuid=service_uuid, primary=True)
periph.add_characteristic(service_uuid=service_uuid,
                          uuid=characteristic_uuid,
                          value=[0x00],
                          notifying=False,
                          flags=['read'],
                          read_callback=read_callback)

# ----------------------------------------------------------------
# Main Section
# ----------------------------------------------------------------

if __name__ == '__main__':
    print("\nGesture Sensor Test Program ...")
    print("Keyboard controls:")
    print("l - Simulate LEFT gesture")
    print("r - Simulate RIGHT gesture")
    print("d - Simulate DOWN gesture")
    print("f - Simulate FORWARD gesture")
    print("cc - Simulate COUNTER-CLOCKWISE gesture")
    print("q - Quit program")
    print("Hold the button to make the device discoverable to a phone via BLE.")

    if os.path.exists(INFO_FILE_PATH):
        print("Removing existing info.txt to ensure fresh start...")
        os.remove(INFO_FILE_PATH)

    sensor = PAJ7620U2()
    current_task = 1

    try:
        os.makedirs(os.path.dirname(INFO_FILE_PATH), exist_ok=True)
        os.makedirs(AUDIO_FILES_DIR, exist_ok=True)
        os.makedirs(NAV_AUDIO_DIR, exist_ok=True)

        scheduler_thread = threading.Thread(target=schedule_tasks, args=(sensor.tasks,))
        scheduler_thread.daemon = True
        scheduler_thread.start()

        event_handler = InfoFileHandler(sensor)
        observer = Observer()
        observer.schedule(event_handler, path=os.path.dirname(INFO_FILE_PATH), recursive=False)
        observer.start()
        print(f"Monitoring {INFO_FILE_PATH} for changes...")
        print(f"Total number of tasks: {len(sensor.tasks)}")
        print("Current task: 1")

        remove_paired_devices()
        start_bluetooth_agent()

        periodic_task_1_thread = threading.Thread(target=play_task_1_periodically, args=(sensor,))
        periodic_task_1_thread.daemon = True
        periodic_task_1_thread.start()

        # BLE advertisement loop triggered by button hold.
        button = Button(17)  # Physical button on GPIO17
        while True:
            button_pressed_time = 0
            # While button is held down, count hold time
            while button.is_pressed:
                button_pressed_time += 0.1
                time.sleep(0.1)
                if button_pressed_time >= 3:  # Held for 3 seconds
                    print("Button held for 3 seconds. Starting BLE advertising...")
                    os.system("rfkill unblock bluetooth")
                    os.system("bluetoothctl power on")
                    try:
                        periph.publish()  # Start advertising
                        print("BLE advertising active. Device should be discoverable as 'RPi-BLE'.")
                    except Exception as e:
                        print(f"Error starting BLE advertising: {e}")
                    time.sleep(10)  # Advertise for 10 seconds
                    try:
                        periph.unpublish()  # Stop advertising
                        print("Stopped BLE advertising.\n")
                    except Exception as e:
                        print(f"Error stopping BLE advertising: {e}")
                    break
            time.sleep(0.1)

    except KeyboardInterrupt:
        print("Exiting program...")
        observer.stop()
    finally:
        observer.join()
        print("GPIO cleanup mocked")
        GPIO.cleanup()
