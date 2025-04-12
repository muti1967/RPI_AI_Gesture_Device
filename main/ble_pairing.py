#!/usr/bin/python
# -*- coding:utf-8 -*-

import asyncio
import time
import threading
from bleak import BleakScanner, BleakClient
import os

from audio_helpers import play_upload_confirmation
from bluetooth_agent import remove_paired_devices

async def enter_pairing_mode():
    print("Entering Bluetooth Pairing Mode")
    remove_paired_devices()

    def blink_led():
        while not connected:
            print("LED ON")
            time.sleep(0.5)
            print("LED OFF")
            time.sleep(0.5)

    connected = False
    blink_thread = threading.Thread(target=blink_led)
    blink_thread.start()

    try:
        print("Waiting for a connection from a phone...")
        while not connected:
            devices = await BleakScanner.discover()
            for device in devices:
                print(device)
                if "YourPhoneName" in device.name:
                    async with BleakClient(device.address) as client:
                        await client.connect()
                        if client.is_connected:
                            connected = True
                            print(f"Connected to {device.name}")
                            play_upload_confirmation()
                            break
        print("LED SOLID")
        while connected:
            await asyncio.sleep(1)
            print("Handling data from the phone...")
    except Exception as e:
        print(f"Connection error: {e}")
    finally:
        connected = True
        blink_thread.join()
        print("LED OFF")
        print("Bluetooth Pairing Mode Exited")
