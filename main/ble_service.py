#!/usr/bin/python
# -*- coding:utf-8 -*-

from bluezero import adapter
from bluezero import peripheral
import time
import os

# Get the first available Bluetooth adapter
adapter_list = list(adapter.Adapter.available())
if adapter_list:
    adapter_address = adapter_list[0].address
else:
    adapter_address = None

# BLE characteristic and service UUIDs
SERVICE_UUID = '12345678-1234-5678-1234-56789abcdef0'
CHAR_UUID = '12345678-1234-5678-1234-56789abcdef1'

# Create BLE peripheral instance
periph = peripheral.Peripheral(adapter_address, local_name='RPi-BLE')

def init_ble():
    # Add service
    periph.add_service(service_id=1, uuid=SERVICE_UUID, primary=True)
    
    # Add characteristic
    periph.add_characteristic(service_id=1, 
                            char_id=1, 
                            uuid=CHAR_UUID,
                            value=[0x00],
                            notifying=False,
                            flags=['read', 'write'],
                            read_callback=lambda: [0x42],
                            write_callback=lambda x: print(f"Received: {x}"))

def start_ble_advertising():
    os.system("rfkill unblock bluetooth")
    os.system("bluetoothctl power on")
    time.sleep(1)
    
    try:
        init_ble()
        periph.publish()
        print("BLE advertising started...")
        return True
    except Exception as e:
        print(f"Error starting BLE: {e}")
        return False

def stop_ble_advertising():
    try:
        periph.unpublish()
        print("BLE advertising stopped")
        return True
    except Exception as e:
        print(f"Error stopping BLE: {e}")
        return False

# Initialize BLE on import
init_ble()
