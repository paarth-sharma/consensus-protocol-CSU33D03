import threading
import socket
import sys
from collections import Counter
import random


# Have to use a class to perform threading
class ClientHandler(threading.Thread):
    def __init__(self, client_socket, address, active_connections,voting_list, client_service, voted_clients,riddles, answers):
        # Handler initalising itself
        super().__init__()
        # Declaring all parameters within
        self.client_socket = client_socket
        self.address = address
        self.active_connections = active_connections
        self.max_attempts = 3
        self.voting_list=voting_list
        self.client_service= client_service
        self.voted_clients = voted_clients
        self.riddles = riddles
        self.answers= answers
        self.service= None
        self.vote= None

    def run(self):
        try:
            # Send the inital server message
            self.riddle()
        finally:
            #Closes the connections at the end if not already closed
            self.close_connection()
        
    def initial_message(self):
        #Send our opening message requesting what services the client performs
        riddle = "\nCorrect answer!!! What services does your client offer?"
        print(f"Sending: {riddle}")
        self.client_socket.send(riddle.encode())
        #Decode and strip the white space of the reply
        answer = self.client_socket.recv(1024).decode().strip()
        print(f"Received answer: {answer}")
        #Server chooses if they want this client to join its network
        sentence = input("Does the server want this client to enter the network? ")
        if sentence.lower() == "yes":
            with global_lock:
                #Add this to the list so that we can send to client
                self.client_service.append(answer)
                self.service= answer
                # If server agrres, we sent the riddle
            self.correct_answer()
        else: 
            # Otherwise, we reject the client and close the connection
            self.reject()

    
    def riddle(self):
        # Select a random riddle for this client
        index = random.randint(0, len(self.riddles) - 1)
        riddle = (f"Hello, I am a server that can offer information about other clients, once a voting consensus has been reached.\nPlease answer this riddle to continue your connection.\n{self.riddles[index]}\n")
        correct_ans = self.answers[index]
        print(f"Sending: Hello, I am a server that can offer information about other clients, once a voting consensus has been reached.\nPlease answer this riddle to continue your connection.\n{riddle}")
        self.client_socket.send(riddle.encode())
        answer = self.client_socket.recv(1024).decode().strip()
        print(f"Received answer: {answer}")
        #David is the correct answer, if this is received we go to correct function, otherwise incorrect function
        if answer.lower() == correct_ans.lower():
            self.initial_message()
        else: 
            self.incorrect_answer()
   
    def correct_answer(self):
        #if client answers correctly, it can cast its vote, however we offer a choise in case the client wants to exit
        info_message = f"Would you to cast your vote?"
        print(f"Sending: {info_message}")
        self.client_socket.send(info_message.encode())
        #Decode and strip the white space of the reply
        sentence = self.client_socket.recv(1024).decode().strip()
        print(f"Received: {sentence}")
        #Depending on the answerm we branch to correct paths
        if sentence.lower() == 'yes':
            self.yes_message()
        else: 
            self.no_message()
                
    def yes_message(self):
        # This handles the actual casting of votes
        vote_message = "Enter your a letter of the alphabet for your vote:"
        print(f"Sending: {vote_message}")
        self.client_socket.send(vote_message.encode())
        vote = self.client_socket.recv(1024).decode().strip()
        print(f"Received vote: {vote}")
        with global_lock:
            #Add the vote to the list that can be accessed by all threads
             self.voting_list.append(vote)
             self.vote=vote
             self.voted_clients.append(self.address)
        # Once vote is cast, we attempt to find a consensus
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
        if len(self.voted_clients) == len(self.active_connections):
            #This will count type of votes for us and decide which has highest amount
            vote_counts = Counter(self.voting_list)
            # This finds the maximum type of vote case
            max_count = max(vote_counts.values())
            # Selecting options that received the maximum count of votes
            consensus_options = [option for option, count in vote_counts.items() if count == max_count]
        
            # If there's a tie, you have to recast your vote
            if len(consensus_options) > 1:
                consensus_message = f"Consensus not reached.\n Press yes to recast votes!"
                print(f"Sending: {consensus_message}")
                self.client_socket.send(consensus_message.encode())
                sentence = self.client_socket.recv(1024).decode().strip()
                # Must remove current vote from list and retry
                if self.vote in self.voting_list:
                    self.voting_list.remove(self.vote)
                print(f"Received sentence: {sentence}")
                # If yes, retry otherwise close connection
                if sentence.lower() == 'yes':
                    self.yes_message()
                else: self.no_message()
        
            else:
                #Consensus has been reached so we can print and offer info about clients
                self.consensus = consensus_options[0]
                consensus_message = f"Consensus reached: {self.consensus}.\nEnter yes to start receiving information or no to kill program!"
                print(f"Sending: {consensus_message}")
                self.client_socket.send(consensus_message.encode())
                sentence = self.client_socket.recv(1024).decode().strip()
                print(f"Received sentence: {sentence}")
                #If yes, send info otherwise close connection
                if sentence.lower() == 'yes':
                    self.information()
                else: self.close_connection()
        else:
            consensus_message = f"Waiting for other clients to cast votes. Enter yes to retry or no to exit the program"
            print(f"Sending: {consensus_message}")
            self.client_socket.send(consensus_message.encode())
            sentence = self.client_socket.recv(1024).decode().strip()
            print(f"Received sentence: {sentence}")
            # Retry or close the connection
            if sentence.lower() == 'yes':
                self.find_consensus()
            else: self.close_connection()

    def information(self): 
        #This sends the list of clients that the server is connected to, the service they offer, vote they cast
        info_message = f"Ok. Sending information now!\nActive connections:{self.active_connections}.\nServices offered:{self.client_service}.\nVotes:{self.voting_list}\nThank you for partaking! Enter any input to close connection!"
        print(f"Sending: {info_message}")
        self.client_socket.send(info_message.encode())
        sentence = self.client_socket.recv(1024).decode().strip()
        # Once a reply is received, we close the connection
        print(f"Received sentence: {sentence}")
        self.close_connection()

    def close_connection(self):
        #Closes the connections, nealry all paths lead here 
        close_message = "Connection closed. Goodbye!"
        print(f"Sending: {close_message}")
        self.client_socket.send(close_message.encode())
        # Remove all parameters from respective lists
        with global_lock:
            self.active_connections.remove(self.address)
            self.voted_clients.remove(self.address)
            if self.service in self.client_service:
                self.client_service.remove(self.service)
            if self.vote in self.voting_list:
                self.voting_list.remove(self.vote)
        self.client_socket.close()
        return
        
    def reject(self):
        #Handles server rejecting the client- essentially the same as close connectionsb but with a diff message and  not removing additional items
        close_message = "The server has rejected your connection. Goodbye!"
        print(f"Sending: {close_message}")
        self.client_socket.send(close_message.encode())
        with global_lock:
            self.active_connections.remove(self.address)
        self.client_socket.close()
        
    def incorrect_answer(self):
        #This handles the wrong answers for the riddles, max 3 tries
        while self.max_attempts > 1:
            # Remove an attempt every time
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
                
        wrong_message = "Exceeded maximum attempts. Closing connection for security reasons."
        print(f"Sending: {wrong_message}")
        self.client_socket.send(wrong_message.encode())
        with global_lock:
            self.active_connections.remove(self.address)
            self.client_service.remove(self.service)  # corrected line
        self.client_socket.close()

def main():
    # Global lock to synchronize access to shared resources
    global global_lock
    global_lock = threading.Lock()
    global global_active_connections
    global_active_connections = []
    global global_voting_list
    global_voting_list= []
    global global_client_service
    global_client_service= []
    global global_voted_clients
    global_voted_clients=[]

    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <host> <port>")
        sys.exit(1)
    # Permanet socket that the server uses to listen on
    host, port = sys.argv[1], int(sys.argv[2])
    lsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM) #IPV4, TCP 
    lsock.bind((host, port))
    lsock.listen()
    
    print("Server listening on IP address: " + host + " and port number: " + str(port))
    
    riddles= [
        "What has keys but cannot open locks?",
        "I'm tall when I'm young, and I'm short when I'm old. What am I?",
        "David’s parents have three sons: Snap, Crackle, and what’s the name of the third son?"
    ]

    answers= [
        "Piano", "Candle", "David"
    ]

    while True:
        # New individual for each client socket that can be used for threading
        client_socket, addr = lsock.accept()
        print("Accepted connection from:", addr)
        with global_lock:
            global_active_connections.append(addr)
        
        #Call the client handler class that will perform all the riddle logic
        client_handler = ClientHandler(client_socket, addr, global_active_connections, global_voting_list, global_client_service, global_voted_clients, riddles,answers)
        client_handler.start()
        
        
if __name__ == "__main__":
    main()
