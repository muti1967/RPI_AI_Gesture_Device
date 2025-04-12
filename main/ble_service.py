#!/usr/bin/python
# -*- coding:utf-8 -*-

from bluezero import adapter
from bluezero import peripheral
import time
import os
import subprocess

def get_adapter():
    adapter_list = list(adapter.Adapter.available())
    if adapter_list:
        return adapter_list[0]
    return None

def ensure_bluetooth_powered():
    # Enable Bluetooth at system level
    subprocess.run(["rfkill", "unblock", "bluetooth"])
    subprocess.run(["bluetoothctl", "power", "on"])
    time.sleep(2)  # Give the system time to power up Bluetooth

# BLE characteristic and service UUIDs
SERVICE_UUID = '12345678-1234-5678-1234-56789abcdef0'
CHAR_UUID = '12345678-1234-5678-1234-56789abcdef1'

def init_ble():
    ensure_bluetooth_powered()
    
    bt_adapter = get_adapter()
    if not bt_adapter:
        print("No Bluetooth adapter found")
        return None
        
    # Create BLE peripheral instance
    try:
        periph = peripheral.Peripheral(bt_adapter.address, local_name='RPi-BLE')
        
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
        return periph
    except Exception as e:
        print(f"Error initializing BLE: {e}")
        return None

def start_ble_advertising():
    ensure_bluetooth_powered()
    periph = init_ble()
    
    if periph:
        try:
            periph.publish()
            print("BLE advertising started...")
            return True
        except Exception as e:
            print(f"Error starting BLE advertising: {e}")
    return False

def stop_ble_advertising():
    try:
        if periph:
            periph.unpublish()
            print("BLE advertising stopped")
            return True
    except Exception as e:
        print(f"Error stopping BLE: {e}")
    return False

# Initialize periph as None at module level
periph = None
