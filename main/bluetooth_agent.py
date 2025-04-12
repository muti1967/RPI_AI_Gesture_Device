#!/usr/bin/python
# -*- coding:utf-8 -*-

import os
import sys
import dbus
import dbus.service
from dbus.mainloop.glib import DBusGMainLoop
import threading
from gi.repository import GLib
import time

class BluetoothAgent(dbus.service.Object):
    def __init__(self, bus, path):
        dbus.service.Object.__init__(self, bus, path)

    @dbus.service.method("org.bluez.Agent1", in_signature="", out_signature="")
    def Release(self):
        print("Release")

    @dbus.service.method("org.bluez.Agent1", in_signature="o", out_signature="")
    def RequestPinCode(self, device):
        print(f"RequestPinCode {device}")
        return "0000"

    @dbus.service.method("org.bluez.Agent1", in_signature="o", out_signature="u")
    def RequestPasskey(self, device):
        print(f"RequestPasskey {device}")
        return dbus.UInt32(0)

    @dbus.service.method("org.bluez.Agent1", in_signature="ouq", out_signature="")
    def DisplayPasskey(self, device, passkey, entered):
        print("\n" + "="*50)
        print(f"BLUETOOTH PAIRING CODE")
        print(f"Device: {device}")
        print(f"Code: {passkey}")
        print(f"Digits entered: {entered}")
        print("="*50 + "\n")

    @dbus.service.method("org.bluez.Agent1", in_signature="ou", out_signature="")
    def RequestConfirmation(self, device, passkey):
        print("\n" + "="*50)
        print(f"BLUETOOTH PAIRING REQUEST")
        print(f"Device: {device}")
        print(f"Pairing code: {passkey}")
        print("Automatically accepting...")
        print("="*50 + "\n")
        return

    @dbus.service.method("org.bluez.Agent1", in_signature="os", out_signature="")
    def AuthorizeService(self, device, uuid):
        print(f"Authorizing service {uuid} for device {device}")
        return

    @dbus.service.method("org.bluez.Agent1", in_signature="o", out_signature="")
    def Cancel(self, device):
        print(f"Cancel {device}")

def start_bluetooth_agent():
    DBusGMainLoop(set_as_default=True)
    mainloop = GLib.MainLoop()
    
    def run_loop():
        mainloop.run()
    
    # Start D-Bus main loop in a separate thread
    thread = threading.Thread(target=run_loop)
    thread.daemon = True
    thread.start()
    
    bus = dbus.SystemBus()
    agent = BluetoothAgent(bus, "/test/agent")
    obj = bus.get_object("org.bluez", "/org/bluez")
    manager = dbus.Interface(obj, "org.bluez.AgentManager1")
    
    try:
        manager.UnregisterAgent("/test/agent")
    except dbus.exceptions.DBusException as e:
        print(f"Agent not registered previously: {e}")
        
    print(f"Using Bluetooth adapter address: {get_adapter_address()}")
    manager.RegisterAgent("/test/agent", "KeyboardDisplay")
    manager.RequestDefaultAgent("/test/agent")
    print("Bluetooth agent started for pairing")

def get_adapter_address():
    bus = dbus.SystemBus()
    manager = dbus.Interface(bus.get_object("org.bluez", "/"),
                           "org.freedesktop.DBus.ObjectManager")
    objects = manager.GetManagedObjects()
    
    for path, interfaces in objects.items():
        if "org.bluez.Adapter1" in interfaces:
            return interfaces["org.bluez.Adapter1"]["Address"]
    return "Unknown"

def remove_paired_devices():
    os.system("bluetoothctl -- remove *")
    print("Cleared all previously paired devices.")
