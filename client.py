import sys
import socket
import selectors
import types

sel = selectors.DefaultSelector()
messages = [b"Message 1 from client.", b"Message 2 from client."]
sockets = []  # List to store socket objects


def start_connections(host, port, num_conns):
    server_addr = (host, port)
    for i in range(num_conns):
        connid = i + 1
        print(f"Starting connection {connid} to {server_addr}")
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setblocking(False)

        # You use .connect_ex() instead of .connect() because .connect() would immediately raise a BlockingIOError
        # exception. The .connect_ex() method initially returns an error indicator, errno.EINPROGRESS,
        # instead of raising an exception that would interfere with the connection in progress.
        # we need this connect to multiple clients at the same time
        sock.connect_ex(server_addr)

        events = selectors.EVENT_READ | selectors.EVENT_WRITE
        data = types.SimpleNamespace(
            connid=connid,
            outb=b"",
            inb=b"",
            prompt=False # To control whether to prompt for input
        )
        sel.register(sock, events, data=data)
        sockets.append(sock)  # Store socket object in the list


def service_connection(key, mask):
    sock = key.fileobj
    data = key.data 

    if mask & selectors.EVENT_READ:
        try:
            recv_data= sock.recv(1024)
            if recv_data:
                print(f"Received {recv_data.decode()} from connection {data.connid}")
                data.prompt= True
            else:
                print(f"Connection {data.connid} closed by the server.")
                sel.unregister(sock)
                sock.close()
                return
        except Exception as e:
            print(f"Error receiving data from server: {e}")

    if mask & selectors.EVENT_WRITE:
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




if len(sys.argv) != 4:
    print(f"Usage: {sys.argv[0]} <host> <port> <num_connections>")
    sys.exit(1)

host, port, num_conns = sys.argv[1:4]
start_connections(host, int(port), int(num_conns))

try:
    while True:
        events = sel.select(timeout=1)
        if events:
            for key, mask in events:
                service_connection(key, mask)
        # Check for a socket being monitored to continue.
        if not sel.get_map():
            break
except KeyboardInterrupt:
    print("Caught keyboard interrupt, exiting")
finally:
    sel.close()
