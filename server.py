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
    data = types.SimpleNamespace(addr=addr, inb=b"", outb=b"", state="RECEIVING", connid=addr, attempts=0)
    sel.register(conn, selectors.EVENT_READ | selectors.EVENT_WRITE, data=data)
    active_connections.append(conn)  # Add to the list of active connections

def inital_message (sock,data):
    info_request_message = "David’s parents have three sons: Snap, Crackle, and what’s the name of the third son?"
    print(f"Sending: {info_request_message}")
    sock.send(info_request_message.encode())
    # Register the socket for read events to handle the client's response
    sel.modify(sock, selectors.EVENT_READ, data=data)

def correct_answer(sock,data):

    info_message = f"Correct answer! Would you like information?"
    print(f"Sending: {info_message}")
    sock.send(info_message.encode())
    # Register the socket for read events to handle the client's response
    sel.modify(sock, selectors.EVENT_READ, data=data)
    sel.select(timeout=10)  # Adjust the timeout as needed
    recv_data = sock.recv(1024)  # Should be ready to read
    if recv_data:
        sentence = recv_data.decode().strip()  # Strip whitespace
        print(f"Received: {sentence} from connection {data.connid}")
        if sentence.lower() == 'yes':
            yes_message(sock,data)
        else: 
            no_message(sock,data)



def yes_message(sock,data):
    info_message = f"Ok. Sending information now! Active connections:\n{active_connections}\n Would you like to close the connection after?"
    print(f"Sending: {info_message}")
    sock.send(info_message.encode())
    # Register the socket for read events to handle the client's response
    sel.modify(sock, selectors.EVENT_READ, data=data)
    sel.select(timeout=10)  # Adjust the timeout as needed
    recv_data = sock.recv(1024)  # Should be ready to read
    sentence = recv_data.decode().strip()  # Strip whitespace
    if sentence.lower() == 'yes':
        close_connection(sock,data)

def no_message(sock,data):
    info_message = "Ok. Would you like to close the connection?"
    print(f"Sending: {info_message}")
    sock.send(info_message.encode())
    # Register the socket for read events to handle the client's response
    sel.modify(sock, selectors.EVENT_READ, data=data)
    recv_data = sock.recv(1024)  # Should be ready to read
    if recv_data:
        sentence = recv_data.decode().strip()  # Strip whitespace
        print(f"Received: {sentence} from connection {data.connid}")
        if sentence.lower() == 'yes':
            close_connection(sock,data)

def close_connection(sock,data):
    close_message = "Closing connection. Enter any letter to close the program! Goodbye!"
    print(f"Sending: {close_message}")
    sock.send(close_message.encode())
    active_connections.remove(sock)
    sel.unregister(sock)
    sock.close()
    data.closed = True  # Mark the connection as closed

def incorrect_answer(sock,data):
    # Wrong answer feedback
    wrong_message = ""
    if data.attempts == 0:
        wrong_message = "Wrong answer. You have two more tries."
        print(f"Sending: {wrong_message}")
        sock.send(wrong_message.encode())
    elif data.attempts == 1:
        wrong_message = "Wrong answer. You have one more try."
        print(f"Sending: {wrong_message}")
        sock.send(wrong_message.encode())
    else:
        wrong_message = "Exceeded maximum attempts. Closing connection for security reasons. Enter any letter to close the program!"
        print(f"Sending: {wrong_message}")
        sock.send(wrong_message.encode())
        if sock in sel.get_map():
            sel.unregister(sock)
            sock.close()
            data.closed = True  # Mark the connection as closed

    
    



# Function to service existing connections
def service_connection(key, mask):
    sock = key.fileobj
    data = key.data
    if mask & selectors.EVENT_WRITE and not data.outb:
        inital_message(sock,data)
    

    if mask & selectors.EVENT_READ:
        recv_data = sock.recv(1024)
        if recv_data:
            data.inb += recv_data
            process_received_data(data)
            sentence = recv_data.decode().strip()  # Strip whitespace
            print(f"Received: {sentence} from connection {data.connid}")
            if sentence.lower() == 'david':
               correct_answer(sock,data)
            else: 
                incorrect_answer(sock,data)
                # Increment the attempts
                data.attempts += 1

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
