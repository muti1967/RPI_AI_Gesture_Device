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

def handle_file_transfer(data):
    """Handle received file data from iPhone"""
    temp_dir = os.path.join(os.path.expanduser('~'), 'bluetooth_temp')
    os.makedirs(temp_dir, exist_ok=True)
    
    try:
        from bluetooth_file_handler import process_received_files
        
        # Save received data to temporary location
        with open(os.path.join(temp_dir, 'received_data.bin'), 'wb') as f:
            f.write(data)
            
        # Process the received files
        process_received_files(temp_dir)
        
        # Clean up
        shutil.rmtree(temp_dir)
        
        # Play confirmation sound
        from audio_helpers import play_upload_confirmation
        play_upload_confirmation()
        
        return True
    except Exception as e:
        print(f"Error processing received files: {e}")
        return False

def init_ble():
    """Initialize BLE peripheral with file transfer service"""
    ensure_bluetooth_powered()
    
    bt_adapter = get_adapter()
    if not bt_adapter:
        print("No Bluetooth adapter found")
        return None
        
    try:
        # Create BLE peripheral instance
        periph = peripheral.Peripheral(adapter_address=bt_adapter.address, local_name='RPi-BLE')
        
        # Add service with required srv_id
        periph.add_service(srv_id=1, uuid=SERVICE_UUID, primary=True)
        
        # Add characteristic with required srv_id and chr_id
        periph.add_characteristic(srv_id=1,
                                chr_id=1,
                                uuid=CHAR_UUID,
                                value=[0x00],
                                notifying=False,
                                flags=['read', 'write'],
                                read_callback=lambda: [0x42],
                                write_callback=handle_file_transfer)
        
        # Start advertising
        periph.publish()
        print("BLE service initialized and advertising")
        return periph
        
    except Exception as e:
        print(f"Error initializing BLE: {e}")
        return None

periph = None  # Global variable to track peripheral instance

def start_ble_advertising():
    """Start BLE advertising"""
    global periph
    ensure_bluetooth_powered()
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
    """Stop BLE advertising"""
    global periph
    try:
        if periph:
            periph.unpublish()
            print("BLE advertising stopped")
            return True
    except Exception as e:
        print(f"Error stopping BLE: {e}")
    return False

def stop_ble_service():
    """Clean up BLE service"""
    global periph
    try:
        if periph:
            periph.unpublish()
            periph = None
        # Reset adapter state
        bt_adapter = get_adapter()
        if bt_adapter:
            subprocess.run(["bluetoothctl", "discoverable", "off"])
            subprocess.run(["bluetoothctl", "pairable", "off"])
    except Exception as e:
        print(f"Error stopping BLE service: {e}")
    finally:
        # Force removal of any remaining connections
        subprocess.run(["bluetoothctl", "disconnect"])
