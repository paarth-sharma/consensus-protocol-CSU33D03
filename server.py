import sys
import socket
import selectors
import types

# a selector object to multiplex input and output channels
sel = selectors.DefaultSelector()

# HOST = "127.0.0.1"  # Standard loopback interface address (localhost)
# PORT = 65432  # Port to listen on (non-privileged ports are > 1023)

#instead of hardcoding the host and port, we will use command line arguments in a tuple
active_connections = []
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
    data = types.SimpleNamespace(addr=addr, inb=b"", outb=b"", connid=addr)
    events = selectors.EVENT_READ | selectors.EVENT_WRITE
    sel.register(conn, events, data=data)
    # Add the connection to the active connections list
    active_connections.append(conn)

# 'key' is the 'namedtuple' returned from .select() that contains the socket object (fileobj) and data object.
# 'mask' contains the events that are ready.
# If the socket is ready for reading, then mask & selectors.EVENT_READ will evaluate to True, so sock.recv() is called.
# Any data that’s read is appended to data.outb so that it can be sent later.
connection_list = ''

def service_connection(key, mask):
    global connection_list  # Declare connection_list as global
    sock = key.fileobj
    data = key.data

    # Count the number of attempts
    if not hasattr(data, 'attempts'):
        data.attempts = 0

    # Send the initial message asking if the client wants information
    if mask & selectors.EVENT_WRITE:
        if not data.outb:
            info_request_message = "David’s parents have three sons: Snap, Crackle, and what’s the name of the third son?"
            print(f"Sending: {info_request_message}")
            sock.send(info_request_message.encode())
            # Register the socket for read events to handle the client's response
            sel.modify(sock, selectors.EVENT_READ, data=data)

    elif mask & selectors.EVENT_READ:
        try:
            recv_data = sock.recv(1024)  # Should be ready to read
            if recv_data:
                sentence = recv_data.decode().strip()  # Strip whitespace
                print(f"Received: {sentence} from connection {data.connid}")

                # Check if the response is correct
                if sentence.lower() == 'david':
                    info_message = f"Correct answer! Would you like information?"
                    print(f"Sending: {info_message}")
                    sock.send(info_message.encode())
                    # Register the socket for read events to handle the client's response
                    sel.modify(sock, selectors.EVENT_READ, data=data)
                    # Set a timeout for receiving the response
                    sel.modify(sock, selectors.EVENT_READ, data=data)
                    sel.select(timeout=10)  # Adjust the timeout as needed
                    recv_data = sock.recv(1024)  # Should be ready to read

                    if recv_data:
                        # Update the list of active connections
                        connection_list = '\n'.join([str(conn.getpeername()) for conn in active_connections])
                        sentence = recv_data.decode().strip()  # Strip whitespace
                        print(f"Received: {sentence} from connection {data.connid}")
                        if sentence.lower() == 'yes':
                            info_message = f"Ok. Sending information now! Active connections:\n{connection_list}\n Would you like to close the connection after?"

                            print(f"Sending: {info_message}")
                            sock.send(info_message.encode())

                            # Register the socket for read events to handle the client's response
                            sel.modify(sock, selectors.EVENT_READ, data=data)

                            # Set a timeout for receiving the response
                            sel.modify(sock, selectors.EVENT_READ, data=data)
                            sel.select(timeout=10)  # Adjust the timeout as needed
                            recv_data = sock.recv(1024)  # Should be ready to read

                            if recv_data:
                                sentence = recv_data.decode().strip()  # Strip whitespace
                                print(f"Received: {sentence} from connection {data.connid}")
                                if sentence.lower() == 'yes':
                                    close_message = "Closing connection. Enter any letter to close the program! Goodbye!"
                                    print(f"Sending: {close_message}")
                                    sock.send(close_message.encode())
                                    sel.unregister(sock)
                                    sock.close()
                                    data.closed = True  # Mark the connection as closed

                                elif sentence.lower() == 'no':
                                    continue_message = "Connection will remain open."
                                    print(f"Sending: {continue_message}")
                                    sock.send(continue_message.encode())
                        elif sentence.lower() == 'no':
                            info_message = "Ok. Would you like to close the connection?"
                            print(f"Sending: {info_message}")
                            sock.send(info_message.encode())
                            # Register the socket for read events to handle the client's response
                            sel.modify(sock, selectors.EVENT_READ, data=data)

                            # Set a timeout for receiving the response
                            sel.modify(sock, selectors.EVENT_READ, data=data)
                            sel.select(timeout=10)  # Adjust the timeout as needed
                            recv_data = sock.recv(1024)  # Should be ready to read

                            if recv_data:
                                sentence = recv_data.decode().strip()  # Strip whitespace
                                print(f"Received: {sentence} from connection {data.connid}")
                                if sentence.lower() == 'yes':
                                    info_message = "Ok closing connection! Enter any letter to close the program! Goodbye."
                                    print(f"Sending: {info_message}")
                                    sock.send(info_message.encode())
                                    sel.unregister(sock)
                                    sock.close()
                                    data.closed = True  # Mark the connection as closed

                                elif sentence.lower() == 'no':
                                    info_message = "Ok! Connection will remain open."
                                    print(f"Sending: {info_message}")
                                    sock.send(info_message.encode())
                    else:
                        # Handle if no response is received within the timeout period
                        print("No response from client within the timeout period.")
                        # Optionally, you can choose to close the connection or take other actions
                        if sock in sel.get_map():
                            sel.unregister(sock)
                            sock.close()
                            data.closed = True  # Mark the connection as closed

                else:
                    # Wrong answer feedback
                    wrong_message = ""
                    if data.attempts == 0:
                        wrong_message = "Wrong answer. You have two more tries."
                    elif data.attempts == 1:
                        wrong_message = "Wrong answer. You have one more try."
                    else:
                        wrong_message = "Exceeded maximum attempts. Closing connection for security reasons. Enter any letter to close the program!"
                        print(f"Sending: {wrong_message}")
                        sock.send(wrong_message.encode())
                        if sock in sel.get_map():
                            sel.unregister(sock)
                            sock.close()
                            data.closed = True  # Mark the connection as closed

                    print(f"Sending: {wrong_message}")
                    sock.send(wrong_message.encode())
                    # Increment the attempts
                data.attempts += 1

        except BlockingIOError:
            pass  # No data available to read, continue
        except Exception as e:
            print(f"Error receiving data from client: {e}")

    # Check if the connection has been closed
    if hasattr(data, 'closed') and data.closed:
        # Remove the connection from the active connections list
        active_connections.remove(sock)


if len(sys.argv) != 3:
    print(f"Usage: {sys.argv[0]} <host> <port>")
    sys.exit(1)

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
