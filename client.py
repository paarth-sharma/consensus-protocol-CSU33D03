import sys
import socket
import types

sockets = []  # List to store socket objects

def start_connections(host, port):

    server_addr = (host, port)
    print(f"Starting connection to {server_addr}")
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setblocking(False)
    try:
        # Attempt to connect to the server
        sock.connect(server_addr)
    except BlockingIOError:
        pass  # Connection is in progress, move forward
        
    sockets.append((sock, types.SimpleNamespace(
        outb=b"",
        inb=b"",
        prompt=False 
        )))


def service_connection(sock, data):
    try:
        recv_data = sock.recv(1024)
        if recv_data:
            print(f"Received: {recv_data.decode()}")
            # Prompt for input every time we receive data
            data.prompt = True
        else:
            print(f"Connection closed by the server.")
            sockets.remove((sock, data))
            sock.close()
            return
    except BlockingIOError:
            pass  # No data available to read, continue without printing an error
    except Exception as e:
            print(f"Error receiving data from server: {e}")


    if data.prompt:
        # Prompt the user for input only if necessary
        sentence = input("Enter reply: ")
        if sentence:
            data.outb = sentence.encode()
            data.prompt = False  # Stop prompting for input
    elif data.outb:
        # If there's data to send, send it
        try:
            sock.send(data.outb)
            data.outb = b""  # Clear the output buffer after sending
        except Exception as e:
            print(f"Error sending data to server: {e}")


if len(sys.argv) != 3:
    print(f"Usage: {sys.argv[0]} <host> <port> ")
    sys.exit(1)

host, port = sys.argv[1], int(sys.argv[2])
start_connections(host, port)

try:
    while sockets:
        for sock, data in sockets.copy():
            service_connection(sock, data)
except KeyboardInterrupt:
    print("Caught keyboard interrupt, exiting")
finally:
    for sock, _ in sockets:
        sock.close()
