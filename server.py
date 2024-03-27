import threading
import socket
import sys

# Have to use a class to perform threading
class ClientHandler(threading.Thread):
    def __init__(self, client_socket, address, active_connections):
        #Handler initalising itself
        super().__init__()
        self.client_socket = client_socket
        self.address = address
        self.active_connections = active_connections
        self.max_attempts = 3
    
    def run(self):
        try:
             #Send initial message if it hasn't been sent yet
            if not self.initial_message_sent:
                self.client_socket.send(b"Hello, I am sending you a riddle! If you answer correctly, I will send you a list of my connected clients!\n")
                self.initial_message_sent = True
                self.initial_message()
        finally:
            #Closes the connections at the end if not already closed
            self.close_connection()
        
    def initial_message(self):
        riddle = "David’s parents have three sons: Snap, Crackle, and what’s the name of the third son?"
        print(f"Sending: {riddle}")
        self.client_socket.send(riddle.encode())
        
        #Decode and strip the white space of the reply
        answer = self.client_socket.recv(1024).decode().strip()
        if answer.lower() == "david":
            self.correct_answer()
        else: 
            self.incorrect_answer()

    def correct_answer(self):
        info_message = f"Correct answer! Would you like information?"
        print(f"Sending: {info_message}")
        self.client_socket.send(info_message.encode())
        sentence = self.client_socket.recv(1024).decode().strip()
        if sentence.lower() == 'yes':
            self.yes_message()
        else: 
            self.no_message()
                
    def yes_message(self):
        info_message = f"Ok. Sending information now! Active connections:\n{self.active_connections}\n Would you like to close the connection after?"
        print(f"Sending: {info_message}")
        self.client_socket.send(info_message.encode())
        sentence = self.client_socket.recv(1024).decode().strip()
        if sentence.lower() == 'yes':
            self.close_connection()
    
    def no_message(self):
        info_message = "Ok. Would you like to close the connection?"
        print(f"Sending: {info_message}")
        self.client_socket.send(info_message.encode())
        sentence = self.client_socket.recv(1024).decode().strip()
        if sentence.lower() == 'yes':
            self.close_connection()
        
    def close_connection(self):
        close_message = "Closing connection. Enter any letter to close the program! Goodbye!"
        print(f"Sending: {close_message}")
        self.client_socket.send(close_message.encode())
        with global_lock:
            self.active_connections.remove(self.address)
        self.client_socket.close()
        
    def incorrect_answer(self):
        while self.max_attempts > 0:
            if self.max_attempts == 1:
                wrong_message = f"Wrong answer. You have {self.max_attempts} more try. Try again"
            else:
                wrong_message = f"Wrong answer. You have {self.max_attempts} more tries. Try again"
            print(f"Sending: {wrong_message}")
            self.client_socket.send(wrong_message.encode())
            
            self.max_attempts -= 1
            
            request = self.client_socket.recv(1024).decode().strip()
            if request.lower() == "david":
                self.correct_answer()
                return  # Exit the method if the answer is correct
                
        wrong_message = "Exceeded maximum attempts. Closing connection for security reasons. Enter any letter to close the program!"
        print(f"Sending: {wrong_message}")
        self.client_socket.send(wrong_message.encode())
        self.client_socket.close()

def main():
    #Threading locking
    global global_lock
    global_lock = threading.Lock()
    global global_active_connections
    global_active_connections = []
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <host> <port>")
        sys.exit(1)
    # Permanet socket that the server uses to listen on
    host, port = sys.argv[1], int(sys.argv[2])
    lsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    lsock.bind((host, port))
    lsock.listen()
    
    print("Server listening on " + host + ":" + str(port))
    
    while True:
        # New individual client socket that can be used for threading
        client_socket, addr = lsock.accept()
        print("Accepted connection from:", addr)
        with global_lock:
            global_active_connections.append(addr)
        
        #Call the client handler class that will perform all the riddle logic
        client_handler = ClientHandler(client_socket, addr, global_active_connections)
        client_handler.start()
        
if __name__ == "__main__":
    main()
