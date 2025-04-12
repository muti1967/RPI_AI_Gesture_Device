#!/usr/bin/python
# -*- coding:utf-8 -*-

from bluezero import peripheral
from bluezero import adapter
import os
import time
import sys

def read_callback():
    return [ord(c) for c in 'Hello']

service_uuid = '12345678-1234-5678-1234-56789abcdef0'
characteristic_uuid = '12345678-1234-5678-1234-56789abcdef1'

try:
    adapter_list = list(adapter.Adapter.available())
    if not adapter_list:
        raise IndexError("No Bluetooth adapter found.")
    adapter_address = adapter_list[0].address
    print(f"Using Bluetooth adapter address: {adapter_address}")
except IndexError:
    print("Error: No Bluetooth adapter found. Ensure Bluetooth is enabled and available.")
    sys.exit(1)

# Ensure Bluetooth adapter is powered on for Bluezero
os.system("rfkill unblock bluetooth")
os.system("bluetoothctl power on")
time.sleep(1)

periph = peripheral.Peripheral(adapter_address=adapter_address, local_name='RPi-BLE')
periph.add_service(1, service_uuid, primary=True)
periph.add_characteristic(1, 1, characteristic_uuid,
                          value=[0x00],
                          notifying=False,
                          flags=['read'],
                          read_callback=read_callback)
