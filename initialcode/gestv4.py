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

# LED pin
LED_PIN = 18

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

# GPIO setup
GPIO.setmode(GPIO.BCM)
GPIO.setup(LED_PIN, GPIO.OUT)
GPIO.output(LED_PIN, GPIO.LOW)


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
            GPIO.output(LED_PIN, GPIO.HIGH)
            time.sleep(0.5)
            GPIO.output(LED_PIN, GPIO.LOW)
            time.sleep(0.5)

    connected = False
    import threading
    blink_thread = threading.Thread(target=blink_led)
    blink_thread.start()

    try:
        client_sock, client_info = server_sock.accept()
        connected = True
        GPIO.output(LED_PIN, GPIO.HIGH)  # Solid LED when connected
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
        GPIO.output(LED_PIN, GPIO.LOW)  # Turn off LED
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
        GPIO.cleanup()
