# Import additional libraries
import socket
import threading

# Constants
FORMAT = "'utf-8'"
BUFF = 4096

# Receive user's name
user_name = input("Insert your name: ")

# Initialize the socket and connect to the server using the IP and port
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect(('127.0.0.1', 12345))

# Send the user's name to the server
client.send(user_name.encode(FORMAT))

# Receive messages from the server
def receive():
    while True:
        try:
            message = client.recv(BUFF).decode(FORMAT)
            print(message)
        except:
            print("Error.")
            client.close()
            break

# Send messages to the server
def write():
    while True:
        message = input()
        client.send(message.encode(FORMAT))

# Start a thread for the receive function and another for the write function
receive_thread = threading.Thread(target=receive)
receive_thread.start()
write()
