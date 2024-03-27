# Import additional libraries
import os
import socket
import threading
import time

# Constants
FORMAT = "'utf-8'"
BUFF = 4096

# Define server IP and port
host = '127.0.0.1'
port = 12345

# Create a socket for the server and start listening for connections
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((host, port))
server.listen()

# Variables and lists
clients = []
names = []
item_name = ''
item_price = ''
buyer_name = ''
bids = False
bid_number = 0
auction_state = False
connected_clients = 0

# Send message to all active clients
def broadcast(message):
    for client in clients:
        client.send(message)

# Handle messages from various clients, and if a client disconnects, remove them from the list of clients
def handle(client):
    global connected_clients
    while True:
        try:
            message = client.recv(BUFF).decode(FORMAT)
            if auction_state == True:
                handle_bids(client, message)
            if auction_state == False:
                client.send("No auction is currently running".encode(FORMAT))
        except:
            index = clients.index(client)
            user_name = names[index]
            clients.remove(client)
            names.remove(user_name)
            connected_clients -= 1
            client.close()
            broadcast(f"{user_name} left the auction house!".encode(FORMAT))
            break

# Receive multiple clients and create a thread for the handle function for each one
def receive():
    global connected_clients
    while connected_clients < 20:
        client, address = server.accept()
        
        user_name = client.recv(BUFF).decode(FORMAT)
        names.append(user_name)
        clients.append(client)
        connected_clients += 1
        if auction_state == True:
            client.send(f"Auction for {item_name} active. Current Price: {item_price}€".encode(FORMAT))
        thread = threading.Thread(target=handle, args=(client,))
        thread.start()

# Receive bids from clients and validate them
def handle_bids(client, message):
    index = clients.index(client)
    user_name = names[index]
    global item_price
    global buyer_name
    global bids
    global bid_number
    try:
        int(message)
        if buyer_name == user_name:
            client.send(f"You cannot bid twice in a row".encode(FORMAT))
        else:
            if int(message) < item_price:
                client.send(f"Bid too low".encode(FORMAT))
            elif int(message) == item_price:
                if not buyer_name:
                    item_price = int(message)
                    buyer_name = user_name
                    bids = True
                    bid_number = 1
                    broadcast(f"{user_name} bid {message}€".encode(FORMAT))
                else:
                    client.send(f"Bid too low".encode(FORMAT))
            else:
                item_price = int(message)
                buyer_name = user_name
                bids = True
                bid_number = 1
                broadcast(f"{user_name} bid {message}€".encode(FORMAT))
    except:
        client.send("Invalid input.".encode(FORMAT))

# Server menu
def menu():
    while(True):
        print_menu()
        op = ''
        try:
            op = int(input("Choose the desired operation: "))
        except:
            print("ERROR. Enter a number...")
        if op == 1:
            create_auction()
        elif op == 2:
            list_clients()
        elif op == 3:
            list_auctions()
        elif op == 4:
            print("Thank you and come again.")
            time.sleep(5)
            os._exit(0)
        else:
            print("Invalid option. Enter a number between 1 and 4.")

# Print menu options
def print_menu():
    print ("1 -- Create Auction" )
    print ("2 -- List of Clients" )
    print ("3 -- Auctioned Items" )
    print ("4 -- Exit" )

# Option to create an auction
def create_auction():
    global auction_state
    global item_name
    global item_price
    global buyer_name
    item_name = input("Choose the name of the object you want to auction: ")
    while True:
        try:
            item_price = int(input("Choose the base price: "))
        except:
            print("ERROR. Enter a number...")
        else:
            break
    broadcast(f"Auction for {item_name} active. Base Price: {item_price}€".encode(FORMAT))
    auction_state = True
    buyer_name = ''
    while True:
        if bids == True:
            timer()
            if auction_state == True:
                continue
            else:
                break
        else:
            continue
    f = open("auctions.txt","a")
    f.write(f"Auctioned Item: {item_name}  Price: {item_price}€  Buyer: {buyer_name}\n")
    f.close()

# Timer so if there are no bids, the auction ends
def timer():
    global bid_number
    global auction_state
    if bid_number > 0:
        bid_number = 0
        time.sleep(5)
        if bid_number == 0:
            time.sleep(10)
            if bid_number == 0:
                broadcast("Going once...".encode(FORMAT))
                time.sleep(3)
                if bid_number == 0:
                    broadcast("Going twice...".encode(FORMAT))
                    time.sleep(3)
                    if bid_number == 0:
                        broadcast("Going three times...".encode(FORMAT))
                        broadcast(f"Auction for {item_name} concluded. Final Price: {item_price}€. Buyer: {buyer_name}".encode(FORMAT))
                        print(f"Auction for {item_name} concluded. Final Price: {item_price}€. Buyer: {buyer_name}")
                        auction_state = False

# Option to list all active clients on the server
def list_clients():
    if names:
        print("")
        print("List of Active Clients")
        print("------------------------")
        for name in names:
            print(name)
        print("------------------------")
        print("")
    else:
        print("")
        print("There are no active clients")
        print("")

# Option to display all auctions recorded in the auctions.txt file
def list_auctions():
    f_size = os.path.getsize("auctions.txt")
    if f_size == 0:
        print("")
        print("There are no auctioned items")
        print("")
    else:
        count = 0
        f = open("auctions.txt","r")
        lines = f.readlines()
        for i in lines:
            count += 1
            if count == 1:
                print("")
                print(i)
            if count > 1:
                print(i)
        f.close()

# Start a thread to receive clients and start the menu on the server
receive_thread = threading.Thread(target=receive)
receive_thread.start()
menu()
