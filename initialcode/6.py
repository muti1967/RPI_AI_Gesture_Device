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

# i2c address
PAJ7620U2_I2C_ADDRESS = 0x73
# Register Bank select
PAJ_BANK_SELECT = 0xEF  # Bank0== 0x00,Bank1== 0x01
# Register Bank 0
PAJ_SUSPEND = 0x03  # I2C suspend command (Write = 0x01 to enter suspend state). I2C wake-up command is slave ID wake-up. Refer to topic “I2C Bus Timing Characteristics and Protocol”
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

class PAJ7620U2(object):
    def __init__(self, address=PAJ7620U2_I2C_ADDRESS):
        self._address = address  # Set the I2C address
        self._bus = smbus.SMBus(1)  # Initialize I2C bus
        time.sleep(0.5)  # Wait for the device to power up
        self._initialize_sensor()  # Initialize the sensor

    def _initialize_sensor(self):
        try:
            if self._read_byte(0x00) == 0x20:
                print("\nGesture Sensor READY\n")
                for num in range(len(Init_Gesture_Array)):
                    self._write_byte(Init_Gesture_Array[num][0], Init_Gesture_Array[num][1])
            else:
                print("\nGesture Sensor NOT READY - check pin connections\n")
        except Exception as e:
            print(f"Error initializing sensor: {e}")

    def _read_byte(self, cmd):
        return self._bus.read_byte_data(self._address, cmd)

    def _write_byte(self, cmd, val):
        self._bus.write_byte_data(self._address, cmd, val)

    def check_gesture(self):
        global current_task
        Gesture_Data = self._read_u16(0x43)
        if Gesture_Data != 0:
            print(f"Gesture Data: {Gesture_Data}")  # Print only if motion is detected

        if Gesture_Data == PAJ_UP:
            print(f"Playing task[{current_task}]")
            self.play_audio("/home/senior/RPI_AI_Gesture_Device/audio_test.mp3")
        elif Gesture_Data == PAJ_DOWN:
            print(f"Playing recent task[{current_task}]")
            self.play_audio("/home/senior/RPI_AI_Gesture_Device/audio_test.mp3")
        elif Gesture_Data == PAJ_LEFT:
            current_task = max(1, current_task - 1)
            print(f"Moving to task[{current_task}]")
        elif Gesture_Data == PAJ_RIGHT:
            current_task += 1
            print(f"Moving to task[{current_task}]")
        elif Gesture_Data == PAJ_FORWARD:
            print(f"Task[{current_task}] marked complete")
        elif Gesture_Data == PAJ_BACKWARD:
            print(f"Going back in task list")
        elif Gesture_Data == PAJ_CLOCKWISE:
            print(f"Replaying task[{current_task}]")
            self.play_audio("/home/senior/RPI_AI_Gesture_Device/audio_test.mp3")
        elif Gesture_Data == PAJ_COUNT_CLOCKWISE:
            print(f"Undo last action")
        elif Gesture_Data == PAJ_WAVE:
            print("Wave gesture detected: Playing calming audio")
            self.play_audio("/home/senior/RPI_AI_Gesture_Device/audio_test.mp3")

        return Gesture_Data

    def _read_u16(self, cmd):
        LSB = self._bus.read_byte_data(self._address, cmd)
        MSB = self._bus.read_byte_data(self._address, cmd + 1)
        return (MSB << 8) + LSB

    def play_audio(self, file_path):
        try:
            subprocess.run(["mpg123", file_path], check=True)
        except subprocess.CalledProcessError as e:
            print(f"Error playing audio: {e}")

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
        remove_paired_devices()
        start_bluetooth_agent()
        enter_default_state()
    except KeyboardInterrupt:
        print("Exiting program...")
    finally:
        print("GPIO cleanup mocked")
        GPIO.cleanup()

    # For testing Bluetooth scanning
    # import asyncio
    # asyncio.run(scan())
