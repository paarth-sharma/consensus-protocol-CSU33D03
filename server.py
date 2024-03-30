import threading
import socket
import sys
from collections import Counter


# Have to use a class to perform threading
class ClientHandler(threading.Thread):
    def __init__(self, client_socket, address, active_connections,voting_list, client_service):
        #Handler initalising itself
        super().__init__()
        self.client_socket = client_socket
        self.address = address
        self.active_connections = active_connections
        self.max_attempts = 3
        self.voting_list=voting_list
        self.client_service= client_service
        self.service= None
        self.vote= None

    def run(self):
        try:
                self.initial_message()
        finally:
            #Closes the connections at the end if not already closed
            self.close_connection()
        
    def initial_message(self):
        #Send our opening message and the riddle
        riddle = "\nHello, I am a server that can offer information about other clients, once a voting consensus has been reached.\nTo cast your vote you must be able to answer a riddle correctly. What services does your client offer?"
        print(f"Sending: {riddle}")
        self.client_socket.send(riddle.encode())
        #Decode and strip the white space of the reply, then check for expected answers
        answer = self.client_socket.recv(1024).decode().strip()
        print(f"Received answer: {answer}")
        #Server chooses if they want this client to join its network
        sentence = input("Does the server want this client to enter the network? ")
        if sentence.lower() == "yes":
            with global_lock:
                #Add this to the list so that we can send to clients
                self.client_service.append(answer)
                self.service= answer
            self.riddle()
        else: self.reject()

    def riddle(self):
        riddle = "David’s parents have three sons: Snap, Crackle, and what’s the name of the third son?"
        print(f"Sending: {riddle}")
        self.client_socket.send(riddle.encode())
        #Decode and strip the white space of the reply, then check for expected answers
        answer = self.client_socket.recv(1024).decode().strip()
        print(f"Received answer: {answer}")
        if answer.lower() == "david":
            self.correct_answer()
        else: 
            self.incorrect_answer()
   
    def correct_answer(self):
        #if client answers correctly, it can cast its vote
        info_message = f"Correct answer! Would you to cast your vote?"
        print(f"Sending: {info_message}")
        self.client_socket.send(info_message.encode())
        sentence = self.client_socket.recv(1024).decode().strip()
        print(f"Received: {sentence}")
        if sentence.lower() == 'yes':
            self.yes_message()
        else: 
            self.no_message()
                
    def yes_message(self):
        vote_message = "Enter your a letter of the alphabet for your vote:"
        print(f"Sending: {vote_message}")
        self.client_socket.send(vote_message.encode())
        vote = self.client_socket.recv(1024).decode().strip()
        print(f"Received vote: {vote}")
        with global_lock:
            #Add the vote to the list that can be accessed by all threads
             self.voting_list.append(vote)
             self.vote=vote
        self.find_consensus()

    def no_message(self):
        #If the client does not vote, it cannot be apart of the consensus and therefore, connection needs to be closed
        info_message = f"Clients cannot receive information without casting a vote\nEnter yes to go back to voting or anything else to close the connection"
        print(f"Sending: {info_message}")
        self.client_socket.send(info_message.encode())
        sentence = self.client_socket.recv(1024).decode().strip()
        print(f"Received: {sentence}")
        if sentence.lower() == 'yes':
            self.yes_message()
        else: self.close_connection()
        
    
    def find_consensus(self):
        #vote_list_str = ', '.join(self.voting_list)
        #info_message = f"Ok All votes: {vote_list_str}\n Enter yes to see consensus results!"
        
        #This will count type ofvotes for us and decide which has highest amount
        vote_counts = Counter(self.voting_list)
        total_votes= sum(vote_counts.values())
        max_count = max(vote_counts.values())
        consensus_options = [option for option, count in vote_counts.items() if count == max_count]
        if total_votes <2:
            consensus_message = f"Not enough votes have been cast to reach a consensus. Enter yes to retry or no to exit the program"
            print(f"Sending: {consensus_message}")
            self.client_socket.send(consensus_message.encode())
            sentence = self.client_socket.recv(1024).decode().strip()
            print(f"Received sentence: {sentence}")
            if sentence.lower() == 'yes':
                self.find_consensus()
            else: self.close_connection()

        # If there's a tie, you have to recast your vote
        if len(consensus_options) > 1:
            consensus_message = f"Consensus not reached.\n Press yes to recast votes!"
            print(f"Sending: {consensus_message}")
            self.client_socket.send(consensus_message.encode())
            sentence = self.client_socket.recv(1024).decode().strip()
            print(f"Received sentence: {sentence}")
            if sentence.lower() == 'yes':
                self.yes_message()
            else: self.no_message()
        
        else:
            #Consensus has been reached
            self.consensus = consensus_options[0]
            consensus_message = f"Consensus reached: {self.consensus}.\nEnter yes to start receiving information or no to kill program!"
            print(f"Sending: {consensus_message}")
            self.client_socket.send(consensus_message.encode())
            sentence = self.client_socket.recv(1024).decode().strip()
            print(f"Received sentence: {sentence}")
            if sentence.lower() == 'yes':
                self.information()
            else: self.close_connection()
            
    def information(self): 
        #This sends the list of clients that the server is connected to
        info_message = f"Ok. Sending information now!\nActive connections:{self.active_connections}.\nServices offered:{self.client_service}.\nVotes:{self.voting_list}\nThank you for partaking! Enter any input to close connection!"
        print(f"Sending: {info_message}")
        self.client_socket.send(info_message.encode())
        sentence = self.client_socket.recv(1024).decode().strip()
        print(f"Received sentence: {sentence}")
        self.close_connection()

    def close_connection(self):
        #Closes the connections, nealry all paths lead here 
        close_message = "Connection closed. Enter any letter to kill the program! Goodbye!"
        print(f"Sending: {close_message}")
        self.client_socket.send(close_message.encode())
        with global_lock:
            self.active_connections.remove(self.address)
            if self.service in self.client_service:
                self.client_service.remove(self.service)
            if self.vote in self.voting_list:
                self.voting_list.remove(self.vote)
        self.client_socket.close()
        return
        
    def reject(self):
        #Handles server rejecting the client- essentially the same as close connectionsb but with a diff message and  not removing additional items
        close_message = "The server has rejected your connection. Goodbye!\nEnter any letter to kill the program."
        print(f"Sending: {close_message}")
        self.client_socket.send(close_message.encode())
        with global_lock:
            self.active_connections.remove(self.address)
        self.client_socket.close()
        
    def incorrect_answer(self):
        #This handles the wrong answers for the riddles, max 3 tries
        while self.max_attempts > 1:
            self.max_attempts -= 1
            wrong_message = f"Wrong answer. You have {self.max_attempts} more tries. Try again!"
            print(f"Sending: {wrong_message}")
            self.client_socket.send(wrong_message.encode())
            
            #If the answer is entered corectly on the 2nd/3rd try
            request = self.client_socket.recv(1024).decode().strip()
            print(f"Received sentence: {request}")
            if request.lower() == "david":
                self.correct_answer()
                return  # Exit the method if the answer is correct
                
        wrong_message = "Exceeded maximum attempts. Closing connection for security reasons. Enter any letter to close the program!"
        print(f"Sending: {wrong_message}")
        self.client_socket.send(wrong_message.encode())
        with global_lock:
            self.active_connections.remove(self.address)
            self.client_service.remove(self.service)  # corrected line
        self.client_socket.close()

def main():
    #Threading locking
    global global_lock
    global_lock = threading.Lock()
    global global_active_connections
    global_active_connections = []
    global global_voting_list
    global_voting_list= []
    global global_client_service
    global_client_service= []

    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <host> <port>")
        sys.exit(1)
    # Permanet socket that the server uses to listen on
    host, port = sys.argv[1], int(sys.argv[2])
    lsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    lsock.bind((host, port))
    lsock.listen()
    
    print("Server listening on IP address: " + host + " and port number: " + str(port))
    
    while True:
        # New individual client socket that can be used for threading
        client_socket, addr = lsock.accept()
        print("Accepted connection from:", addr)
        with global_lock:
            global_active_connections.append(addr)
        
        #Call the client handler class that will perform all the riddle logic
        client_handler = ClientHandler(client_socket, addr, global_active_connections, global_voting_list, global_client_service)
        client_handler.start()
        
        
if __name__ == "__main__":
    main()
