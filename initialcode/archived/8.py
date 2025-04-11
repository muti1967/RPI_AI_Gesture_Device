#This version has these changes:
#1. pulls info from info.txt
#2. schedules tasks using info.txt
#3. plays the assigned audio files at the assigned times

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

# i2c address
PAJ7620U2_I2C_ADDRESS = 0x73
# Register Bank select
PAJ_BANK_SELECT = 0xEF  # Bank0== 0x00,Bank1== 0x01
# Register Bank 0
PAJ_SUSPEND = 0x03  # I2C suspend command (Write = 0x01 to enter suspend state). I2C wake-up command is slave ID wake-up. Refer to topic "I2C Bus Timing Characteristics and Protocol"
PAJ_INT_FLAG1_MASK = 0x41  # Gesture detection interrupt flag mask
PAJ_INT_FLAG2_MASK = 0x42  # Gesture/PS detection interrupt flag mask
PAJ_INT_FLAG1 = 0x43  # Gesture detection interrupt flag
PAJ_INT_FLAG2 = 0x44  # Gesture/PS detection interrupt flag
PAJ_STATE = 0x45  # State indicator for gesture detection (Only functional at gesture detection mode)
PAJ_PS_HIGH_THRESHOLD = 0x69  # PS hysteresis high threshold (Only functional at proximity detection mode)
PAJ_PS_LOW_THRESHOLD = 0x6A  # PS hysteresis low threshold (Only functional at proximity detection mode)
PAJ_PS_APPROACH_STATE = 0x6B  # PS approach state,  Approach = 1 , (8 bits PS data >= PS high threshold),  Not Approach = 0 , (8 bits PS data <= PS low threshold)(Only functional at proximity detection mode)
PAJ_PS_DATA = 0x6C  # PS 8 bit data(Only functional at gesture detection mode)
PAJ_OBJ_BRIGHTNESS = 0xB0  # Object Brightness (Max. 255)
PAJ_OBJ_SIZE_L = 0xB1  # Object Size(Low 8 bit)
PAJ_OBJ_SIZE_H = 0xB2  # Object Size(High 8 bit)
# Register Bank 1
PAJ_PS_GAIN = 0x44  # PS gain setting (Only functional at proximity detection mode)
PAJ_IDLE_S1_STEP_L = 0x67  # IDLE S1 Step, for setting the S1, Response Factor(Low 8 bit)
PAJ_IDLE_S1_STEP_H = 0x68  # IDLE S1 Step, for setting the S1, Response Factor(High 8 bit)
PAJ_IDLE_S2_STEP_L = 0x69  # IDLE S2 Step, for setting the S2, Response Factor(Low 8 bit)
PAJ_IDLE_S2_STEP_H = 0x6A  # IDLE S2 Step, for setting the S2, Response Factor(High 8 bit)
PAJ_OPTOS1_TIME_L = 0x6B  # OPtoS1 Step, for setting the OPtoS1 time of operation state to standby 1 state(Low 8 bit)
PAJ_OPTOS2_TIME_H = 0x6C  # OPtoS1 Step, for setting the OPtoS1 time of operation state to standby 1 stateHigh 8 bit)
PAJ_S1TOS2_TIME_L = 0x6D  # S1toS2 Step, for setting the S1toS2 time of standby 1 state to standby 2 state(Low 8 bit)
PAJ_S1TOS2_TIME_H = 0x6E  # S1toS2 Step, for setting the S1toS2 time of standby 1 state to standby 2 stateHigh 8 bit)
PAJ_EN = 0x72  # Enable/Disable PAJ7620U2
# Gesture detection interrupt flag
PAJ_UP = 0x01
PAJ_DOWN = 0x02
PAJ_LEFT = 0x04
PAJ_RIGHT = 0x08
PAJ_FORWARD = 0x10
PAJ_BACKWARD = 0x20
PAJ_CLOCKWISE = 0x40
PAJ_COUNT_CLOCKWISE = 0x80
PAJ_WAVE = 0x100

# to do list for this  code
'''
1. once we recieve hardware parts will be able to use this fully with windows app
2. incorperate github for other rpi's so we can just push the code wirlessly
3. ...



'''
# Initialize task index
current_task = 1

# Power up initialize array
Init_Register_Array = (
    (0xEF, 0x00),
    (0x37, 0x07),
    (0x38, 0x17),
    (0x39, 0x06),
    (0x41, 0x00),
    (0x42, 0x00),
    (0x46, 0x2D),
    (0x47, 0x0F),
    (0x48, 0x3C),
    (0x49, 0x00),
    (0x4A, 0x1E),
    (0x4C, 0x20),
    (0x51, 0x10),
    (0x5E, 0x10),
    (0x60, 0x27),
    (0x80, 0x42),
    (0x81, 0x44),
    (0x82, 0x04),
    (0x8B, 0x01),
    (0x90, 0x06),
    (0x95, 0x0A),
    (0x96, 0x0C),
    (0x97, 0x05),
    (0x9A, 0x14),
    (0x9C, 0x3F),
    (0xA5, 0x19),
    (0xCC, 0x19),
    (0xCD, 0x0B),
    (0xCE, 0x13),
    (0xCF, 0x64),
    (0xD0, 0x21),
    (0xEF, 0x01),
    (0x02, 0x0F),
    (0x03, 0x10),
    (0x04, 0x02),
    (0x25, 0x01),
    (0x27, 0x39),
    (0x28, 0x7F),
    (0x29, 0x08),
    (0x3E, 0xFF),
    (0x5E, 0x3D),
    (0x65, 0x96),
    (0x67, 0x97),
    (0x69, 0xCD),
    (0x6A, 0x01),
    (0x6D, 0x2C),
    (0x6E, 0x01),
    (0x72, 0x01),
    (0x73, 0x35),
    (0x74, 0x00),
    (0x77, 0x01),
)
# Approaches register initialization array
Init_PS_Array = (
    (0xEF, 0x00),
    (0x41, 0x00),
    (0x42, 0x00),
    (0x48, 0x3C),
    (0x49, 0x00),
    (0x51, 0x13),
    (0x83, 0x20),
    (0x84, 0x20),
    (0x85, 0x00),
    (0x86, 0x10),
    (0x87, 0x00),
    (0x88, 0x05),
    (0x89, 0x18),
    (0x8A, 0x10),
    (0x9f, 0xf8),
    (0x69, 0x96),
    (0x6A, 0x02),
    (0xEF, 0x01),
    (0x01, 0x1E),
    (0x02, 0x0F),
    (0x03, 0x10),
    (0x04, 0x02),
    (0x41, 0x50),
    (0x43, 0x34),
    (0x65, 0xCE),
    (0x66, 0x0B),
    (0x67, 0xCE),
    (0x68, 0x0B),
    (0x69, 0xE9),
    (0x6A, 0x05),
    (0x6B, 0x50),
    (0x6C, 0xC3),
    (0x6D, 0x50),
    (0x6E, 0xC3),
    (0x74, 0x05),
)
# Gesture register initializes array
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

# GPIO setup
try:
    # Set GPIO mode
    print("Setting GPIO mode to BCM")
    GPIO.setmode(GPIO.BCM)

    # Set up GPIO17 as input with pull-up resistor
    print("Setting up GPIO17 as input with pull-up resistor")
    GPIO.setup(17, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    print("GPIO setup complete")
except Exception as e:
    print(f"Error during GPIO setup: {e}")
finally:
    print("GPIO cleanup will happen at program exit")

# Define paths
HOME_DIR = os.path.expanduser("~")
BASE_DIR = os.path.join(HOME_DIR, "RPI_AI_Gesture_Device")
INFO_FILE_PATH = os.path.join(BASE_DIR, "finalv/info/info.txt")
AUDIO_FILES_DIR = os.path.join(BASE_DIR, "finalv/audio_files")
NAV_AUDIO_DIR = os.path.join(AUDIO_FILES_DIR, "navaudio")

class Task:
    def __init__(self, task_number, audio_file, play_time):
        self.task_number = task_number
        self.audio_file = os.path.join(AUDIO_FILES_DIR, audio_file)  # Use full path for audio file
        self.play_time = play_time
        self.completed = False

    def play_nav_audio(self):
        nav_file = os.path.join(NAV_AUDIO_DIR, f"{self.task_number}.mp3")
        if os.path.exists(nav_file):
            try:
                subprocess.run(["ffplay", "-nodisp", "-autoexit", nav_file], 
                             capture_output=True, 
                             text=True)
            except Exception as e:
                print(f"Error playing navigation audio: {e}")

class InfoFileHandler(FileSystemEventHandler):
    def __init__(self, sensor):
        self.sensor = sensor
        self.last_modified = 0

    def on_modified(self, event):
        if event.src_path == INFO_FILE_PATH:
            current_time = time.time()
            # Prevent multiple reloads within 1 second
            if current_time - self.last_modified > 1:
                print("Info file changed, reloading tasks...")
                self.sensor.tasks = read_task_info()
                # Reschedule all tasks
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
                if line:  # Skip empty lines
                    task_number, audio_file, play_time = line.split(',')
                    # Verify the audio file exists
                    audio_path = os.path.join(AUDIO_FILES_DIR, audio_file)
                    if not os.path.exists(audio_path):
                        print(f"Warning: Audio file not found: {audio_path}")
                    tasks.append(Task(int(task_number), audio_file, play_time))
        return tasks
    except FileNotFoundError:
        print(f"{INFO_FILE_PATH} not found. Creating default file...")
        os.makedirs(os.path.dirname(INFO_FILE_PATH), exist_ok=True)
        with open(INFO_FILE_PATH, 'w') as file:
            file.write("1,1.mp3,23:05\n2,2.mp3,09:00")
        return read_task_info()
    except Exception as e:
        print(f"Error reading {INFO_FILE_PATH}: {e}")
        return []

def play_scheduled_audio(task):
    if not task.completed:
        print(f"Playing task {task.task_number}: {task.audio_file}")
        try:
            # Check if file exists
            if not os.path.exists(task.audio_file):
                print(f"Error: Audio file not found: {task.audio_file}")
                return
                
            # Get file extension
            file_ext = os.path.splitext(task.audio_file)[1].lower()
            
            # Play the audio file using ffplay
            print(f"Playing audio with ffplay... ({file_ext})")
            result = subprocess.run(["ffplay", "-nodisp", "-autoexit", task.audio_file], 
                                 capture_output=True, 
                                 text=True)
            
            if result.returncode != 0:
                print(f"Error playing audio with ffplay: {result.stderr}")
                print("Please check if:")
                print("1. ffplay is installed (sudo apt-get install ffmpeg)")
                print("2. The audio system is properly configured")
                print("3. The file format is supported")
        except Exception as e:
            print(f"Error playing audio: {e}")
            print("Please check if:")
            print("1. The audio file exists and is accessible")
            print("2. ffplay is installed (sudo apt-get install ffmpeg)")
            print("3. The audio system is properly configured")

def schedule_tasks(tasks):
    for task in tasks:
        schedule.every().day.at(task.play_time).do(play_scheduled_audio, task)
    
    while True:
        schedule.run_pending()
        time.sleep(1)

class PAJ7620U2(object):
    def __init__(self, address=PAJ7620U2_I2C_ADDRESS):
        self._address = address  # Set the I2C address
        self._bus = None
        self._initialize_i2c()
        self._initialize_sensor()  # Initialize the sensor
        self.tasks = read_task_info()  # Load tasks from info.txt
        # Test audio system
        self._test_audio_system()

    def _initialize_i2c(self):
        try:
            print("Initializing I2C bus...")
            self._bus = smbus.SMBus(1)  # Initialize I2C bus
            time.sleep(0.1)  # Short delay after bus initialization
            
            # First write to select Bank 0
            self._write_byte(PAJ_BANK_SELECT, 0x00)
            time.sleep(0.1)
            
            # Test I2C communication
            try:
                device_id = self._read_byte(0x00)
                print(f"Device ID: 0x{device_id:02X}")
                if device_id != 0x20:
                    print("Warning: Unexpected device ID. Expected 0x20")
            except Exception as e:
                print(f"Error reading device ID: {e}")
                raise
                
        except Exception as e:
            print(f"Error initializing I2C: {e}")
            print("Please check:")
            print("1. I2C is enabled (sudo raspi-config)")
            print("2. Sensor is properly connected")
            print("3. Correct I2C address (0x73)")
            raise

    def _initialize_sensor(self):
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                print(f"\nAttempting to initialize sensor (attempt {retry_count + 1}/{max_retries})...")
                
                # First select Bank 0
                self._write_byte(PAJ_BANK_SELECT, 0x00)
                time.sleep(0.1)
                
                # Read and verify device ID
                device_id = self._read_byte(0x00)
                print(f"Device ID: 0x{device_id:02X}")
                
                if device_id == 0x20:
                    print("\nGesture Sensor READY")
                    
                    # Initialize gesture registers in Bank 0
                    for num in range(len(Init_Gesture_Array)):
                        self._write_byte(Init_Gesture_Array[num][0], Init_Gesture_Array[num][1])
                        time.sleep(0.01)  # Small delay between register writes
                    
                    print("Gesture registers initialized successfully")
                    
                    # Enable gesture detection
                    self._write_byte(PAJ_BANK_SELECT, 0x00)
                    self._write_byte(PAJ_EN, 0x01)
                    
                    return
                else:
                    print(f"\nUnexpected device ID: 0x{device_id:02X}")
                    print("Expected: 0x20")
                    retry_count += 1
                    time.sleep(1)  # Wait before retry
                    
            except Exception as e:
                print(f"Error during initialization attempt {retry_count + 1}: {e}")
                retry_count += 1
                time.sleep(1)  # Wait before retry
                
        print("\nFailed to initialize sensor after multiple attempts")
        print("Please check:")
        print("1. Sensor connections")
        print("2. I2C address (0x73)")
        print("3. Power supply")
        raise Exception("Sensor initialization failed")

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

    def check_gesture(self):
        try:
            # Make sure we're in Bank 0 for gesture reading
            self._write_byte(PAJ_BANK_SELECT, 0x00)
            time.sleep(0.01)
            
            Gesture_Data = self._read_u16(0x43)
            if Gesture_Data != 0:
                print(f"Gesture Data: 0x{Gesture_Data:04X}")  # Print in hex format
        except Exception as e:
            print(f"Error reading gesture data: {e}")
            return 0

        if Gesture_Data == PAJ_UP:
            # Move to next task
            current_task = min(current_task + 1, len(self.tasks))
            if 1 <= current_task <= len(self.tasks):
                task = self.tasks[current_task - 1]
                print(f"Moving to task[{current_task}]")
                task.play_nav_audio()
        elif Gesture_Data == PAJ_DOWN:
            # Move to previous task
            current_task = max(1, current_task - 1)
            if 1 <= current_task <= len(self.tasks):
                task = self.tasks[current_task - 1]
                print(f"Moving to task[{current_task}]")
                task.play_nav_audio()
        elif Gesture_Data == PAJ_FORWARD:
            # Play the current task's audio
            if 1 <= current_task <= len(self.tasks):
                task = self.tasks[current_task - 1]
                print(f"Playing task[{current_task}]")
                self.play_audio(task.audio_file)
        elif Gesture_Data == PAJ_BACKWARD:
            # Go back to task 1
            current_task = 1
            if len(self.tasks) > 0:
                task = self.tasks[0]
                print("Going back to task 1")
                task.play_nav_audio()
        elif Gesture_Data == PAJ_CLOCKWISE:
            # Mark current task as complete
            if 1 <= current_task <= len(self.tasks):
                self.tasks[current_task - 1].completed = True
                print(f"Task[{current_task}] marked complete")
        elif Gesture_Data == PAJ_COUNT_CLOCKWISE:
            # Undo completion of current task
            if 1 <= current_task <= len(self.tasks):
                self.tasks[current_task - 1].completed = False
                print(f"Task[{current_task}] marked incomplete")
        elif Gesture_Data == PAJ_WAVE:
            # Play all tasks in sequence
            print("Playing all tasks in sequence")
            for task in self.tasks:
                if not task.completed:
                    self.play_audio(task.audio_file)
                    time.sleep(0.5)  # Small delay between tasks

        return Gesture_Data

    def _read_u16(self, cmd):
        LSB = self._bus.read_byte_data(self._address, cmd)
        MSB = self._bus.read_byte_data(self._address, cmd + 1)
        return (MSB << 8) + LSB

    def _test_audio_system(self):
        print("Testing audio system...")
        try:
            # Try to play a test sound
            subprocess.run(["speaker-test", "-t", "wav", "-c", "2", "-D", "hw:0,0", "-l", "1"], 
                         capture_output=True)
            print("Audio system test completed")
        except Exception as e:
            print(f"Warning: Audio system test failed: {e}")
            print("Please check your audio configuration using 'alsamixer'")

    def play_audio(self, file_path):
        try:
            # Check if file exists
            if not os.path.exists(file_path):
                print(f"Error: Audio file not found: {file_path}")
                return
                
            # Get file extension
            file_ext = os.path.splitext(file_path)[1].lower()
            
            # Play the audio file using ffplay
            print(f"Playing audio with ffplay... ({file_ext})")
            result = subprocess.run(["ffplay", "-nodisp", "-autoexit", file_path], 
                                 capture_output=True, 
                                 text=True)
            
            if result.returncode != 0:
                print(f"Error playing audio with ffplay: {result.stderr}")
                print("Please check if:")
                print("1. ffplay is installed (sudo apt-get install ffmpeg)")
                print("2. The audio system is properly configured")
                print("3. The file format is supported")
        except Exception as e:
            print(f"Error playing audio: {e}")
            print("Please check if:")
            print("1. The audio file exists and is accessible")
            print("2. ffplay is installed (sudo apt-get install ffmpeg)")
            print("3. The audio system is properly configured")

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
    
    # Unregister any existing agents
    try:
        manager.UnregisterAgent("/test/agent")
    except dbus.exceptions.DBusException as e:
        print(f"Agent not registered previously: {e}")
    
    # Register the new agent with DisplayYesNo mode
    manager.RegisterAgent("/test/agent", "DisplayYesNo")
    manager.RequestDefaultAgent("/test/agent")
    print("Bluetooth agent started for pairing")

def remove_paired_devices():
    os.system("bluetoothctl -- remove *")
    print("Cleared all previously paired devices.")

# Bluetooth pairing
async def enter_pairing_mode():
    print("Entering Bluetooth Pairing Mode")
    remove_paired_devices()

    # Start LED blinking
    def blink_led():
        while not connected:
            print("LED ON")
            time.sleep(0.5)
            print("LED OFF")
            time.sleep(0.5)

    connected = False
    import threading
    blink_thread = threading.Thread(target=blink_led)
    blink_thread.start()

    try:
        # Wait for a connection from a phone
        print("Waiting for a connection from a phone...")
        while not connected:
            devices = await BleakScanner.discover()
            # Check for a specific device or connection status here
            for device in devices:
                print(device)  # Print discovered devices
                if "YourPhoneName" in device.name:
                    async with BleakClient(device.address) as client:
                        await client.connect()
                        if client.is_connected:
                            connected = True
                            print(f"Connected to {device.name}")
                            break

        print("LED SOLID")  # Solid LED when connected

        # Handle incoming data
        while connected:
            await asyncio.sleep(1)
            print("Handling data from the phone...")
            # Implement actual data handling logic here
    except Exception as e:
        print(f"Connection error: {e}")
    finally:
        connected = True
        blink_thread.join()
        print("LED OFF")  # Turn off LED
        print("Bluetooth Pairing Mode Exited")

# Check button press
def check_button_press():
    button_press_count = 0
    button_pressed_time = 0
    start_time = time.time()
    
    while True:
        if GPIO.input(17) == GPIO.LOW:
            button_pressed_time += 1
            print(f"Button held for {button_pressed_time * 0.1} seconds")
            time.sleep(0.1)  # Debounce delay
            
            if button_pressed_time >= 30:  # 3 seconds
                print("Button held for 3 seconds, entering pairing mode...")
                import asyncio
                asyncio.run(enter_pairing_mode())
                break
        else:
            if button_pressed_time > 0:
                button_press_count += 1
                print(f"Button pressed {button_press_count} time(s)")
                button_pressed_time = 0
                time.sleep(0.1)  # Debounce delay

            if button_press_count >= 2 and (time.time() - start_time) <= 3:
                print("Button pressed 2 times within 3 seconds, entering editing mode...")
                enter_editing_state()
                break
            elif (time.time() - start_time) > 3:
                button_press_count = 0
                start_time = time.time()
        time.sleep(0.1)

# Task states
def enter_default_state():
    print("Entering Default State: Playing tasks")
    while True:
        gesture = sensor.check_gesture()
        if gesture == PAJ_FORWARD:
            print("Stopping task playback and marking task complete")
            break
        elif gesture == PAJ_CLOCKWISE:
            print("Replaying last task")
            sensor.play_audio("/home/senior/RPI_AI_Gesture_Device/audio_test.mp3")
        elif gesture == PAJ_WAVE:
            print("Playing calming audio")
            sensor.play_audio("/home/senior/RPI_AI_Gesture_Device/audio_test.mp3")
        
        # Check button press in a non-blocking manner
        if GPIO.input(17) == GPIO.LOW:
            button_press_count = 0
            button_pressed_time = 0
            start_time = time.time()
            while GPIO.input(17) == GPIO.LOW:
                button_pressed_time += 1
                print(f"Button held for {button_pressed_time * 0.1} seconds")
                time.sleep(0.1)  # Debounce delay
                
                if button_pressed_time >= 30:  # 3 seconds
                    print("Button held for 3 seconds, entering pairing mode...")
                    import asyncio
                    asyncio.run(enter_pairing_mode())
                    return
            if button_pressed_time > 0:
                button_press_count += 1
                print(f"Button pressed {button_press_count} time(s)")
                button_pressed_time = 0
                time.sleep(0.1)  # Debounce delay

            if button_press_count >= 2 and (time.time() - start_time) <= 3:
                print("Button pressed 2 times within 3 seconds, entering editing mode...")
                enter_editing_state()
                return
            elif (time.time() - start_time) > 3:
                button_press_count = 0
                start_time = time.time()
        time.sleep(0.1)

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

async def scan():
    print("Scanning for Bluetooth devices...")
    devices = await BleakScanner.discover()
    for device in devices:
        print(device)

if __name__ == '__main__':
    print("\nGesture Sensor Test Program ...")
    sensor = PAJ7620U2()
    current_task = 1

    try:
        # Create directories if they don't exist
        os.makedirs(os.path.dirname(INFO_FILE_PATH), exist_ok=True)
        os.makedirs(AUDIO_FILES_DIR, exist_ok=True)

        # Start the scheduling thread
        scheduler_thread = threading.Thread(target=schedule_tasks, args=(sensor.tasks,))
        scheduler_thread.daemon = True
        scheduler_thread.start()

        # Set up file monitoring
        event_handler = InfoFileHandler(sensor)
        observer = Observer()
        observer.schedule(event_handler, path=os.path.dirname(INFO_FILE_PATH), recursive=False)
        observer.start()
        print(f"Monitoring {INFO_FILE_PATH} for changes...")

        remove_paired_devices()
        start_bluetooth_agent()
        enter_default_state()
    except KeyboardInterrupt:
        print("Exiting program...")
        observer.stop()
    finally:
        observer.join()
        print("GPIO cleanup mocked")
        GPIO.cleanup()

    # For testing Bluetooth scanning
    # import asyncio
    # asyncio.run(scan())
