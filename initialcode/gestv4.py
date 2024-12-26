#!/usr/bin/python
# -*- coding:utf-8 -*-
import time
import smbus
import bluetooth
import RPi.GPIO as GPIO

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

# GPIO setup (mocked)
print("GPIO setup mocked")
print("LED control mocked")


class PAJ7620U2(object):
    def __init__(self, address=PAJ7620U2_I2C_ADDRESS):
        self._address = address
        self._bus = smbus.SMBus(1)
        time.sleep(0.5)
        self._initialize_sensor()

    def _initialize_sensor(self):
        if self._read_byte(0x00) == 0x20:
            print("\nGesture Sensor READY\n")
            for num in range(len(Init_Gesture_Array)):
                self._write_byte(Init_Gesture_Array[num][0], Init_Gesture_Array[num][1])
        else:
            print("\nGesture Sensor NOT READY - check pin connections\n")

    def _read_byte(self, cmd):
        return self._bus.read_byte_data(self._address, cmd)

    def _write_byte(self, cmd, val):
        self._bus.write_byte_data(self._address, cmd, val)

    def check_gesture(self):
        global current_task
        Gesture_Data = self._read_u16(0x43)

        if Gesture_Data == PAJ_UP:
            print(f"Playing task[{current_task}]")
        elif Gesture_Data == PAJ_DOWN:
            print(f"Stopping task[{current_task}]")
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
        elif Gesture_Data == PAJ_COUNT_CLOCKWISE:
            print(f"Undo last action")
        elif Gesture_Data == PAJ_WAVE:
            print("Wave gesture detected: Playing calming audio")

        return Gesture_Data

    def _read_u16(self, cmd):
        LSB = self._bus.read_byte_data(self._address, cmd)
        MSB = self._bus.read_byte_data(self._address, cmd + 1)
        return (MSB << 8) + LSB


# Bluetooth pairing
def enter_pairing_mode():
    print("Entering Bluetooth Pairing Mode")
    server_sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
    server_sock.bind(("", bluetooth.PORT_ANY))
    server_sock.listen(1)
    port = server_sock.getsockname()[1]

    bluetooth.advertise_service(
        server_sock,
        "GestureDevice",
        service_classes=[bluetooth.SERIAL_PORT_CLASS],
        profiles=[bluetooth.SERIAL_PORT_PROFILE],
    )

    print(f"Device is discoverable. Waiting for a connection on RFCOMM channel {port}")

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
        client_sock, client_info = server_sock.accept()
        connected = True
        print("LED SOLID")  # Solid LED when connected
        print(f"Accepted connection from {client_info}")

        # Handle incoming data
        while True:
            data = client_sock.recv(1024)
            if not data:
                break
            print(f"Received: {data.decode('utf-8')}")
    except Exception as e:
        print(f"Connection error: {e}")
    finally:
        connected = True
        blink_thread.join()
        client_sock.close()
        server_sock.close()
        print("LED OFF")  # Turn off LED
        print("Bluetooth Pairing Mode Exited")


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
        elif gesture == PAJ_WAVE:
            print("Playing calming audio")


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


if __name__ == '__main__':
    print("\nGesture Sensor Test Program ...")
    sensor = PAJ7620U2()
    current_task = 1

    try:
        enter_default_state()
        while True:
            button_pressed = input(
                "Enter button press (1 for Default State, 2 for Editing State, hold for Pairing Mode): ")
            start_time = time.time()

            while button_pressed == "hold":
                if time.time() - start_time > 3:
                    enter_pairing_mode()
                    break

            if button_pressed == "1":
                enter_default_state()
            elif button_pressed == "2":
                enter_editing_state()
    except KeyboardInterrupt:
        print("Exiting program...")
    finally:
        print("GPIO cleanup mocked")
