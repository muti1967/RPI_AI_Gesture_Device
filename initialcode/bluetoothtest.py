import bluetooth

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
    start_bluetooth_server()
