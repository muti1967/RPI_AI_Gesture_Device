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
        
        # Play the upload confirmation audio
        upload_audio = os.path.join(os.path.expanduser('~'), 'R
