import sys
import socket

# Check if the correct number of command-line arguments are given or not
if len(sys.argv) != 3:
    print(f"Usage: {sys.argv[0]} <host> <port>")
    sys.exit(1)

# Parse command-line arguments
host, port = sys.argv[1], int(sys.argv[2])

# Create a socket object
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Connect to the server
server_addr = (host, port)
sock.connect(server_addr)

# Main loop to receive and send messages
while True:
    try:
        # Receive data from the server
        recv_data = sock.recv(1024)
        print(f"Received: {recv_data.decode()}")

        # Check for specific server messages to close the connection
        if "Connection closed.Goodbye!" in recv_data.decode():
            print("Server closed the connection.")
            break
        elif "The server has rejected your connection. Goodbye!" in recv_data.decode():
            print("Server rejected the connection.")
            break
        elif "Exceeded maximum attempts. Closing connection for security reasons." in recv_data.decode():
            print("Connection closed due to maximum attempts.")
            break
        else:
            # Prompting the user for a reply
            sentence = input("Enter reply: ")
            sock.send(sentence.encode())
    except KeyboardInterrupt:
        # Handle user interrupt
        print("Caught keyboard interrupt, exiting")
        break
    except socket.error as e:
        # Handle socket errors
        print(f"Socket error: {e}")
        break

# Close the socket
sock.close()