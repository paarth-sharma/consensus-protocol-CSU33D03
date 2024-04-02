import sys
import socket
import types

sockets = []  # List to store socket objects

if len(sys.argv) != 3:
    print(f"Usage: {sys.argv[0]} <host> <port> ")
    sys.exit(1)

host, port = sys.argv[1], int(sys.argv[2])
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_addr= ( host,port)
sock.connect(server_addr)

yes = True
while yes==True:
    try:
        recv_data = sock.recv(1024)
        print(f"Received: {recv_data.decode()}")
        if "Connection closed.Goodbye!" in recv_data.decode():
            sock.close()
            yes=False
        elif "The server has rejected your connection. Goodbye!" in recv_data.decode():
            sock.close()
            yes=False
        elif "Exceeded maximum attempts. Closing connection for security reasons." in recv_data.decode():
            sock.close()
            yes=False
        else:
            sentence = input("Enter reply: ")
            sock.send(sentence.encode())
    except KeyboardInterrupt:
            print("Caught keyboard interrupt, exiting")
