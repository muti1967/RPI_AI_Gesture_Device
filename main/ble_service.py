#!/usr/bin/python
# -*- coding:utf-8 -*-

from bluezero import peripheral
import time
import os

def read_callback():
    print("iPhone is reading data...")
    return [0x42]

def write_callback(value):
    print(f"Received from iPhone: {value}")

# BLE characteristic and service UUIDs
char_uuid = '12345678-1234-5678-1234-56789abcdef1'
service_uuid = '12345678-1234-5678-1234-56789abcdef0'

# Initialize BLE characteristic
my_char = peripheral.Characteristic(char_uuid,
                                  ['read', 'write'],
                                  read_callback,
                                  write_callback)

# Initialize BLE service
my_service = peripheral.Service(service_uuid, True)
my_service.add_characteristic(my_char)

# Initialize BLE peripheral
ble_peripheral = peripheral.Peripheral(adapter_addr=None,
                                     local_name='RPi-BLE',
                                     services=[my_service])

def start_ble_advertising():
    os.system("rfkill unblock bluetooth")
    os.system("bluetoothctl power on")
    time.sleep(1)  # Wait for Bluetooth to initialize
    
    try:
        ble_peripheral.publish()
        print("BLE advertising started...")
        return True
    except Exception as e:
        print(f"Error starting BLE: {e}")
        return False

def stop_ble_advertising():
    try:
        ble_peripheral.unpublish()
        print("BLE advertising stopped")
        return True
    except Exception as e:
        print(f"Error stopping BLE: {e}")
        return False
