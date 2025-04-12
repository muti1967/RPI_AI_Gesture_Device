#!/usr/bin/python
# -*- coding:utf-8 -*-

from bluezero import adapter
from bluezero import peripheral
import time
import os
import subprocess
import threading

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

class BLEService:
    def __init__(self):
        self.periph = None
        self.adapter = None
    
    def cleanup(self):
        try:
            if self.periph:
                try:
                    self.periph.publish(False)  # Stop advertising
                except:
                    pass
                self.periph = None
            # Reset adapter state
            subprocess.run(["bluetoothctl", "power", "off"], check=False)
            time.sleep(1)
            subprocess.run(["bluetoothctl", "power", "on"], check=False)
            time.sleep(1)
            subprocess.run(["bluetoothctl", "discoverable", "on"], check=False)
            subprocess.run(["bluetoothctl", "pairable", "on"], check=False)
        except Exception as e:
            print(f"Error in cleanup: {e}")

# Create global BLE service instance
ble_service = BLEService()

def init_ble():
    ensure_bluetooth_powered()
    ble_service.cleanup()  # Clean up any existing state
    
    bt_adapter = get_adapter()
    if not bt_adapter:
        print("No Bluetooth adapter found")
        return None
        
    try:
        # Create new peripheral instance
        periph = peripheral.Peripheral(adapter_address=bt_adapter.address, local_name='RPi-BLE')
        periph.add_service(srv_id=1, uuid=SERVICE_UUID, primary=True)
        periph.add_characteristic(
            srv_id=1,
            chr_id=1,
            uuid=CHAR_UUID,
            value=[0x00],
            notifying=False,
            flags=['read', 'write'],
            read_callback=lambda: [0x42],
            write_callback=lambda x: print(f"Received: {x}")
        )
        ble_service.periph = periph
        return periph
    except Exception as e:
        print(f"Error initializing BLE: {e}")
        return None

def start_ble_advertising():
    ensure_bluetooth_powered()
    global periph
    periph = init_ble()
    
    if periph:
        try:
            periph.publish()
            print("BLE advertising started...")
            # Schedule BLE shutdown after 5 minutes
            threading.Timer(300, stop_ble_advertising).start()
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

def stop_ble_service():
    """Clean up BLE service and D-Bus connections"""
    try:
        ble_service.cleanup()
        # Ensure Bluetooth is properly reset
        subprocess.run(["bluetoothctl", "disconnect"], check=False)
        subprocess.run(["bluetoothctl", "power", "off"], check=False)
        time.sleep(1)
    except Exception as e:
        print(f"Error stopping BLE service: {e}")

# Initialize periph as None at module level
periph = None
