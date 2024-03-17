import sys
import socket
import selectors
import types

# a selector object to multiplex input and output channels
sel = selectors.DefaultSelector()

# HOST = "127.0.0.1"  # Standard loopback interface address (localhost)
# PORT = 65432  # Port to listen on (non-privileged ports are > 1023)

#instead of hardcoding the host and port, we will use command line arguments in a tuple
host, port = sys.argv[1], int(sys.argv[2])

lsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
lsock.bind((host, port))
lsock.listen()
print(f"Listening on {(host, port)}")
lsock.setblocking(False)
sel.register(lsock, selectors.EVENT_READ, data=None)

# call sock.accept() and then call conn.setblocking(False) to put the socket in non-blocking mode.
# the main objective in this version of the server because you don’t want it to block. 
# If it blocks, then the entire server is stalled until it returns. 
# That means other sockets are left waiting even though the server isn't actively working.
# If this isn't prevented, the server will "hang"
def accept_wrapper(sock):
    conn, addr = sock.accept()  # Should be ready to read
    print(f"Accepted connection from {addr}")
    conn.setblocking(False)
    data = types.SimpleNamespace(addr=addr, inb=b"", outb=b"")
    events = selectors.EVENT_READ | selectors.EVENT_WRITE
    sel.register(conn, events, data=data)

# 'key' is the 'namedtuple' returned from .select() that contains the socket object (fileobj) and data object. 
# 'mask' contains the events that are ready.
# if the socket is ready for reading, then mask & selectors.EVENT_READ will evaluate to True, so sock.recv() is called. 
# any data that’s read is appended to data.outb so that it can be sent later.
def service_connection(key, mask):
    sock = key.fileobj
    data = key.data
    if mask & selectors.EVENT_READ:
        recv_data = sock.recv(1024)  # Should be ready to read
        if recv_data:
            data.outb += recv_data

        # If no data is received, this means that the client has closed their socket, so the server should too. 
        # call sel.unregister() before closing, so it’s no longer monitored by .select().
        else:
            print(f"Closing connection to {data.addr}")
            sel.unregister(sock)
            sock.close()

    # .send() method returns the number of bytes sent. 
    # we can slice .outb buffer to discard the bytes sent and only keep the unsent data.        
    if mask & selectors.EVENT_WRITE:
        if data.outb:
            print(f"Echoing {data.outb!r} to {data.addr}")
            sent = sock.send(data.outb)  # Should be ready to write
            data.outb = data.outb[sent:]

# 
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