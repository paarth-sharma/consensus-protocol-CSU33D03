import sys
import socket
import selectors
import types

# Initialize the selector
sel = selectors.DefaultSelector()

# Function to handle new connections
def accept_wrapper(sock):
    conn, addr = sock.accept()  # Should be ready to read
    print(f"Accepted connection from {addr}")
    conn.setblocking(False)
    data = types.SimpleNamespace(addr=addr, inb=b"", outb=b"", state="RECEIVING")
    sel.register(conn, selectors.EVENT_READ | selectors.EVENT_WRITE, data=data)
    active_connections.append(conn)  # Add to the list of active connections

# Function to service existing connections
def service_connection(key, mask):
    sock = key.fileobj
    data = key.data

    if mask & selectors.EVENT_READ:
        recv_data = sock.recv(1024)
        if recv_data:
            data.inb += recv_data
            process_received_data(data)
        else:
            print(f"Closing connection to {data.addr}")
            active_connections.remove(sock)  # Remove from the list of active connections
            sel.unregister(sock)
            sock.close()

    if mask & selectors.EVENT_WRITE and data.outb:
        try:
            sent = sock.send(data.outb)
            data.outb = data.outb[sent:]
        except BlockingIOError:
            pass

# Function to process received data
def process_received_data(data):
    if "\n" in data.inb.decode():
        received_msg, _, remainder = data.inb.partition(b'\n')
        data.inb = remainder
        handle_client_message(data, received_msg.decode().strip())

# Function to handle messages based on their content
def handle_client_message(data, message):
    print(f"Message from {data.addr}: {message}")
    response = "Echo: " + message + "\n"
    data.outb += response.encode()

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <host> <port>")
        sys.exit(1)

    host, port = sys.argv[1], int(sys.argv[2])
    lsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    lsock.bind((host, port))
    lsock.listen()
    print(f"Listening on {(host, port)}")
    lsock.setblocking(False)
    sel.register(lsock, selectors.EVENT_READ, data=None)

    active_connections = []  # List to track active connections

    try:
        while True:
            events = sel.select(timeout=None)
            for key, mask in events:
                if key.data is None:
                    accept_wrapper(key.fileobj)
                else:
                    service_connection(key, mask)
    except KeyboardInterrupt:
        print("Caught keyboard interrupt, exiting")
    finally:
        sel.close()