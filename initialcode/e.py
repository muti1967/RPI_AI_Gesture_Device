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
from bluezero import peripheral
from bluezero import adapter
import asyncio

# ----------------------------------------------------------------
# Pre-Initialization: Clear leftover GPIO state and disable warnings
# ----------------------------------------------------------------
GPIO.setwarnings(False)
GPIO.cleanup()        # Free any leftover resources
GPIO.setmode(GPIO.BCM)  # Ensure BCM numbering is used

# ----------------------------------------------------------------
# Sensor/Gesture Constants and Register Arrays
# ----------------------------------------------------------------

#i2c address
PAJ7620U2_I2C_ADDRESS   = 0x73
#Register Bank select
PAJ_BANK_SELECT			= 0xEF			#Bank0== 0x00,Bank1== 0x01
#Register Bank 0
PAJ_SUSPEND				= 0x03		#I2C suspend command (Write = 0x01 to enter suspend state). I2C wake-up command is slave ID wake-up. Refer to topic “I2C Bus Timing Characteristics and Protocol”
PAJ_INT_FLAG1_MASK		= 0x41		#Gesture detection interrupt flag mask
PAJ_INT_FLAG2_MASK		= 0x42		#Gesture/PS detection interrupt flag mask
PAJ_INT_FLAG1		    = 0x43		#Gesture detection interrupt flag
PAJ_INT_FLAG2			= 0x44		#Gesture/PS detection interrupt flag
PAJ_STATE				= 0x45		#State indicator for gesture detection (Only functional at gesture detection mode)
PAJ_PS_HIGH_THRESHOLD	= 0x69		#PS hysteresis high threshold (Only functional at proximity detection mode)		
PAJ_PS_LOW_THRESHOLD	= 0x6A		#PS hysteresis low threshold (Only functional at proximity detection mode)
PAJ_PS_APPROACH_STATE	= 0x6B		#PS approach state,  Approach = 1 , (8 bits PS data >= PS high threshold),  Not Approach = 0 , (8 bits PS data <= PS low threshold)(Only functional at proximity detection mode)
PAJ_PS_DATA				= 0x6C		#PS 8 bit data(Only functional at gesture detection mode)
PAJ_OBJ_BRIGHTNESS		= 0xB0		#Object Brightness (Max. 255)
PAJ_OBJ_SIZE_L			= 0xB1		#Object Size(Low 8 bit)		
PAJ_OBJ_SIZE_H			= 0xB2		#Object Size(High 8 bit)	
#Register Bank 1
PAJ_PS_GAIN				= 0x44	    #PS gain setting (Only functional at proximity detection mode)
PAJ_IDLE_S1_STEP_L		= 0x67		#IDLE S1 Step, for setting the S1, Response Factor(Low 8 bit)
PAJ_IDLE_S1_STEP_H		= 0x68		#IDLE S1 Step, for setting the S1, Response Factor(High 8 bit)	
PAJ_IDLE_S2_STEP_L		= 0x69		#IDLE S2 Step, for setting the S2, Response Factor(Low 8 bit)
PAJ_IDLE_S2_STEP_H		= 0x6A		#IDLE S2 Step, for setting the S2, Response Factor(High 8 bit)
PAJ_OPTOS1_TIME_L		= 0x6B		#OPtoS1 Step, for setting the OPtoS1 time of operation state to standby 1 state(Low 8 bit)	
PAJ_OPTOS2_TIME_H		= 0x6C		#OPtoS1 Step, for setting the OPtoS1 time of operation state to standby 1 stateHigh 8 bit)	
PAJ_S1TOS2_TIME_L		= 0x6D		#S1toS2 Step, for setting the S1toS2 time of standby 1 state to standby 2 state(Low 8 bit)	
PAJ_S1TOS2_TIME_H		= 0x6E		#S1toS2 Step, for setting the S1toS2 time of standby 1 state to standby 2 stateHigh 8 bit)	
PAJ_EN					= 0x72		#Enable/Disable PAJ7620U2
#Gesture detection interrupt flag
PAJ_UP				    = 0x01 
PAJ_DOWN			    = 0x02
PAJ_LEFT			    = 0x04 
PAJ_RIGHT			    = 0x08
PAJ_FORWARD		    	= 0x10 
PAJ_BACKWARD		    = 0x20
PAJ_CLOCKWISE			= 0x40
PAJ_COUNT_CLOCKWISE		= 0x80
PAJ_WAVE				= 0x100
#Power up initialize array
Init_Register_Array = (
	(0xEF,0x00),
	(0x37,0x07),
	(0x38,0x17),
	(0x39,0x06),
	(0x41,0x00),
	(0x42,0x00),
	(0x46,0x2D),
	(0x47,0x0F),
	(0x48,0x3C),
	(0x49,0x00),
	(0x4A,0x1E),
	(0x4C,0x20),
	(0x51,0x10),
	(0x5E,0x10),
	(0x60,0x27),
	(0x80,0x42),
	(0x81,0x44),
	(0x82,0x04),
	(0x8B,0x01),
	(0x90,0x06),
	(0x95,0x0A),
	(0x96,0x0C),
	(0x97,0x05),
	(0x9A,0x14),
	(0x9C,0x3F),
	(0xA5,0x19),
	(0xCC,0x19),
	(0xCD,0x0B),
	(0xCE,0x13),
	(0xCF,0x64),
	(0xD0,0x21),
	(0xEF,0x01),
	(0x02,0x0F),
	(0x03,0x10),
	(0x04,0x02),
	(0x25,0x01),
	(0x27,0x39),
	(0x28,0x7F),
	(0x29,0x08),
	(0x3E,0xFF),
	(0x5E,0x3D),
	(0x65,0x96),
	(0x67,0x97),
	(0x69,0xCD),
	(0x6A,0x01),
	(0x6D,0x2C),
	(0x6E,0x01),
	(0x72,0x01),
	(0x73,0x35),
	(0x74,0x00),
	(0x77,0x01),
)
#Approaches register initialization array
Init_PS_Array = (
	(0xEF,0x00),
	(0x41,0x00),
	(0x42,0x00),
	(0x48,0x3C),
	(0x49,0x00),
	(0x51,0x13),
	(0x83,0x20),
	(0x84,0x20),
	(0x85,0x00),
	(0x86,0x10),
	(0x87,0x00),
	(0x88,0x05),
	(0x89,0x18),
	(0x8A,0x10),
	(0x9f,0xf8),
	(0x69,0x96),
	(0x6A,0x02),
	(0xEF,0x01),
	(0x01,0x1E),
	(0x02,0x0F),
	(0x03,0x10),
	(0x04,0x02),
	(0x41,0x50),
	(0x43,0x34),
	(0x65,0xCE),
	(0x66,0x0B),
	(0x67,0xCE),
	(0x68,0x0B),
	(0x69,0xE9),
	(0x6A,0x05),
	(0x6B,0x50),
	(0x6C,0xC3),
	(0x6D,0x50),
	(0x6E,0xC3),
	(0x74,0x05),
)
#Gesture register initializes array
Init_Gesture_Array = (
	(0xEF,0x00),
	(0x41,0x00),
	(0x42,0x00),
	(0xEF,0x00),
	(0x48,0x3C),
	(0x49,0x00),
	(0x51,0x10),
	(0x83,0x20),
	(0x9F,0xF9),
	(0xEF,0x01),
	(0x01,0x1E),
	(0x02,0x0F),
	(0x03,0x10),
	(0x04,0x02),
	(0x41,0x40),
	(0x43,0x30),
	(0x65,0x96),
	(0x66,0x00),
	(0x67,0x97),
	(0x68,0x01),
	(0x69,0xCD),
	(0x6A,0x01),
	(0x6B,0xB0),
	(0x6C,0x04),
	(0x6D,0x2C),
	(0x6E,0x01),
	(0x74,0x00),
	(0xEF,0x00),
	(0x41,0xFF),
	(0x42,0x01),
)

current_task = 1
HOME_DIR = "/home/senior"  # Hardcoded for correct paths under sudo
BASE_DIR = os.path.join(HOME_DIR, "RPI_AI_Gesture_Device")
INFO_FILE_PATH = os.path.join(BASE_DIR, "finalv/info/info.txt")
AUDIO_FILES_DIR = os.path.join(BASE_DIR, "finalv/audio_files")
NAV_AUDIO_DIR = os.path.join(AUDIO_FILES_DIR, "navaudio")

# ----------------------------------------------------------------
# Additional Audio Helper Functions
# ----------------------------------------------------------------

def play_bootup_sound():
    file_bootup = os.path.join(NAV_AUDIO_DIR, "bootup.mp3")
    if os.path.exists(file_bootup):
        print("Playing bootup sound...")
        try:
            subprocess.run(["ffplay", "-nodisp", "-autoexit", file_bootup],
                           capture_output=True, text=True)
        except Exception as e:
            print(f"Error playing bootup sound: {e}")
    else:
        print("Bootup file not found:", file_bootup)

def play_upload_confirmation():
    file_confirm = os.path.join(NAV_AUDIO_DIR, "upload_conformation.mp3")
    if os.path.exists(file_confirm):
        print("Playing upload confirmation sound...")
        try:
            subprocess.run(["ffplay", "-nodisp", "-autoexit", file_confirm],
                           capture_output=True, text=True)
        except Exception as e:
            print(f"Error playing upload confirmation: {e}")
    else:
        print("Upload confirmation file not found:", file_confirm)

# ----------------------------------------------------------------
# GPIO Setup for Gesture Sensor
# ----------------------------------------------------------------
GESTURE_SENSOR_PIN = 7  # Pin 4 from the left corresponds to GPIO 7
GPIO.setup(GESTURE_SENSOR_PIN, GPIO.OUT)
GPIO.output(GESTURE_SENSOR_PIN, GPIO.LOW)

# ----------------------------------------------------------------
# Task Class and File Handler
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
                # Schedule the task one-two playback every minute.
                schedule.every(1).minute.do(play_task_one_two)
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
                        print(f"Info: Audio file not found: {audio_path}")  # Changed from Warning to Info
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
        try:
            subprocess.run(["ffplay", "-nodisp", "-autoexit", task.audio_file],
                           capture_output=True, text=True)
        except Exception as e:
            print(f"Error playing audio: {e}")

def play_task_one_two():
    file1 = os.path.join(AUDIO_FILES_DIR, "1.mp3")
    file2 = os.path.join(AUDIO_FILES_DIR, "2.mp3")
    if os.path.exists(file1):
        print("Playing Task 1 (1.mp3)")
        try:
            subprocess.run(["ffplay", "-nodisp", "-autoexit", file1],
                           capture_output=True, text=True)
        except Exception as e:
            print(f"Error playing Task 1: {e}")
    else:
        print("Task 1 file not found:", file1)
    if os.path.exists(file2):
        print("Playing Task 2 (2.mp3)")
        try:
            subprocess.run(["ffplay", "-nodisp", "-autoexit", file2],
                           capture_output=True, text=True)
        except Exception as e:
            print(f"Error playing Task 2: {e}")
    else:
        print("Task 2 file not found:", file2)

def schedule_tasks(tasks):
    for task in tasks:
        schedule.every().day.at(task.play_time).do(play_scheduled_audio, task)
    # Also schedule play_task_one_two to run every minute.
    schedule.every(1).minute.do(play_task_one_two)
    while True:
        schedule.run_pending()
        time.sleep(1)

# ----------------------------------------------------------------
# Unified PAJ7620U2 Sensor Class (Using Actual I²C and Gesture Detection)
# ----------------------------------------------------------------

class PAJ7620U2(object):
    def __init__(self, address=PAJ7620U2_I2C_ADDRESS):
        self._address = address
        # Ensure the gesture sensor pin is set to LOW during initialization
        GPIO.output(GESTURE_SENSOR_PIN, GPIO.LOW)
        self._bus = smbus.SMBus(1)
        self.tasks = read_task_info()
        self._initialize_sensor()

    def _initialize_sensor(self):
        # Power on the gesture sensor by setting the pin to HIGH
        GPIO.output(GESTURE_SENSOR_PIN, GPIO.HIGH)
        retries = 3
        while retries > 0:
            try:
                if self._read_byte(0x00) == 0x20:
                    print("\nGesture Sensor READY\n")
                    for reg, val in Init_Gesture_Array:
                        self._write_byte(reg, val)
                    return
                else:
                    print("\nGesture Sensor NOT READY - check connections\n")
            except Exception as e:
                print(f"Error initializing sensor: {e}")
                retries -= 1
                time.sleep(1)
        print("Failed to initialize gesture sensor after multiple attempts.")
        GPIO.output(GESTURE_SENSOR_PIN, GPIO.LOW)

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

    def check_gesture(self):
        global current_task
        try:
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
        elif Gesture_Data == PAJ_DOWN:
            print(f"Gesture DOWN detected: Replaying task[{current_task}]")
            self.play_audio("/home/senior/RPI_AI_Gesture_Device/audio_test.mp3")
        elif Gesture_Data == PAJ_LEFT:
            if current_task > 1:
                current_task -= 1
            else:
                current_task = 1
            if current_task <= len(self.tasks) and self.tasks:
                task = self.tasks[current_task - 1]
                print(f"Gesture LEFT detected: Navigating to task[{current_task}]")
                task.play_nav_audio()
            else:
                print("Gesture LEFT detected but no task available.")
        elif Gesture_Data == PAJ_RIGHT:
            current_task += 1
            if current_task > len(self.tasks):
                current_task = len(self.tasks)
            if current_task <= len(self.tasks) and self.tasks:
                task = self.tasks[current_task - 1]
                print(f"Gesture RIGHT detected: Navigating to task[{current_task}]")
                task.play_nav_audio()
            else:
                print("Gesture RIGHT detected but no task available.")
        elif Gesture_Data == PAJ_FORWARD:
            if 1 <= current_task <= len(self.tasks) and self.tasks:
                task = self.tasks[current_task - 1]
                print(f"Gesture FORWARD detected: Playing audio for task[{current_task}]")
                self.play_audio(task.audio_file)
            else:
                print("Gesture FORWARD detected: Invalid task index")
        elif Gesture_Data == PAJ_BACKWARD:
            print("Gesture BACKWARD detected: Turning ON Bluetooth and playing 'bluetoothon.mp3'")
            os.system("rfkill unblock bluetooth")
            os.system("bluetoothctl power on")
            bluetooth_on_file = os.path.join(NAV_AUDIO_DIR, "bluetoothon.mp3")
            self.play_audio(bluetooth_on_file)
        return Gesture_Data

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
        print(f"Info: Agent not registered previously: {e}")  # Changed to Info
    try:
        manager.RegisterAgent("/test/agent", "DisplayYesNo")
        manager.RequestDefaultAgent("/test/agent")
        print("Bluetooth agent started for pairing")
    except dbus.exceptions.DBusException as e:
        print(f"Error starting Bluetooth agent: {e}")

def remove_paired_devices():
    os.system("bluetoothctl -- remove *")
    print("Cleared all previously paired devices.")

# ----------------------------------------------------------------
# BLE Pairing & Advertisement Section
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
                            # Play upload confirmation sound upon receiving audio (simulate here)
                            play_upload_confirmation()
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
        print("Default state active at", datetime.now().strftime("%H:%M:%S"))
        gesture = sensor.check_gesture()
        time.sleep(1)

def enter_editing_state():
    print("Entering Editing State")
    while True:
        gesture = sensor.check_gesture()
        time.sleep(1)

# ----------------------------------------------------------------
# BLE Service Definition and Peripheral Setup (Bluezero)
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

# Ensure Bluetooth adapter is powered on for Bluezero
os.system("rfkill unblock bluetooth")
os.system("bluetoothctl power on")
time.sleep(1)


periph = peripheral.Peripheral(adapter_address=adapter_address, local_name='RPi-BLE')
periph.add_service(1, service_uuid, primary=True)
periph.add_characteristic(1, 1, characteristic_uuid,
                          value=[0x00],
                          notifying=False,
                          flags=['read'],
                          read_callback=read_callback)

# ----------------------------------------------------------------
# Main Section
# ----------------------------------------------------------------

if __name__ == '__main__':
    print("\nGesture Sensor Test Program ...")
    if os.path.exists(INFO_FILE_PATH):
        print("Removing existing info.txt to ensure fresh start...")
        os.remove(INFO_FILE_PATH)
    sensor = PAJ7620U2()
    current_task = 1

    # Play bootup sound once at startup.
    play_bootup_sound()

    try:
        os.makedirs(os.path.dirname(INFO_FILE_PATH), exist_ok=True)
        os.makedirs(AUDIO_FILES_DIR, exist_ok=True)
        os.makedirs(NAV_AUDIO_DIR, exist_ok=True)

        # Start scheduler thread for tasks and for playing tasks 1 and 2 every minute.
        scheduler_thread = threading.Thread(target=schedule_tasks, args=(sensor.tasks,))
        scheduler_thread.daemon = True
        scheduler_thread.start()

        # Start file observer to monitor info.txt changes.
        event_handler = InfoFileHandler(sensor)
        observer = Observer()
        observer.schedule(event_handler, path=os.path.dirname(INFO_FILE_PATH), recursive=False)
        observer.start()
        print(f"Monitoring {INFO_FILE_PATH} for changes...")
        print(f"Total number of tasks: {len(sensor.tasks)}")
        print("Current task: 1")

        remove_paired_devices()
        start_bluetooth_agent()

        # Enter the default state loop to continuously check for gestures.
        enter_default_state()

    except KeyboardInterrupt:
        print("Exiting program...")
        observer.stop()
    finally:
        observer.join()
        print("Cleaning up GPIO")
        GPIO.cleanup()
