import bluetooth
import os
import dbus
import dbus.service
from dbus.mainloop.glib import DBusGMainLoop

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
        print(f"DisplayPasskey {device} {passkey} {entered}")

    @dbus.service.method("org.bluez.Agent1", in_signature="os", out_signature="")
    def RequestConfirmation(self, device, passkey):
        print(f"RequestConfirmation {device} {passkey}")
        return

    @dbus.service.method("org.bluez.Agent1", in_signature="o", out_signature="")
    def AuthorizeService(self, device, uuid):
        print(f"AuthorizeService {device} {uuid}")
        return

    @dbus.service.method("org.bluez.Agent1", in_signature="o", out_signature="")
    def Cancel(self, device):
        print(f"Cancel {device}")

def start_bluetooth_agent():
    DBusGMainLoop(set_as_default=True)
    bus = dbus.SystemBus()
    agent = BluetoothAgent(bus, "/test/agent")
    obj = bus.get_object("org.bluez", "/org/bluez")
    manager = dbus.Interface(obj, "org.bluez.AgentManager1")
    manager.RegisterAgent("/test/agent", "NoInputNoOutput")
    manager.RequestDefaultAgent("/test/agent")
    print("Bluetooth agent started for pairing")

def start_bluetooth_server():
    server_sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
    port = bluetooth.PORT_ANY
    server_sock.bind(("", port))
    server_sock.listen(1)

    # Advertise the service
    bluetooth.advertise_service(
        server_sock,
        "RPiFileTransfer",
        service_classes=[bluetooth.SERIAL_PORT_CLASS],
        profiles=[bluetooth.SERIAL_PORT_PROFILE],
    )

    print("Waiting for a connection from a phone...")
    client_sock, client_info = server_sock.accept()
    print(f"Accepted connection from {client_info}")

    try:
        # Receive file data
        with open("received_file.txt", "wb") as file:
            while True:
                data = client_sock.recv(1024)
                if not data:
                    break
                file.write(data)
                print(f"Received {len(data)} bytes")
        print("File received successfully")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        client_sock.close()
        server_sock.close()
        print("Connection closed")

if __name__ == "__main__":
    print("Starting Bluetooth server...")
    start_bluetooth_agent()
    start_bluetooth_server()
