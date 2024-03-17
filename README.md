# This project contains the code of group 15 for CSU33D03 (2023-24)

## It is a basic implementation of a basic consensus protocol, implemented to be capable of the following tasks:

- **Discover** - discover other nodes on the network that you can potentially interact and collaborate with.
- **Negotiate** - negotiate with each of these nodes to discover their offered services, capabilities and constraints, and to advise them of your offered services, capabilies and constraints.
- **Agreement** -  shared agreement and consensus on the collaborative activity, service or task to be provided.
- **Action** - an action that demonstrates the meaningful and effective use of the agreed consensus which you have just achieved.

## Bonus
Bonus acvity: Build into your consensus mechanism 
1. A capability to detect malicious behaviour intended to meaningfully compromise or adversely impact the consensus approach, and 
2. Effective mechanisms to anticipate and mitigate such approaches.


## Modules and concepts used

- [Socket](https://docs.python.org/3/library/socket.html)
Something interesting to observe was - Blocking Calls

A socket function or method that temporarily suspends your application is a blocking call. For example, .accept(), .connect(), .send(), and .recv() block, meaning they don’t return immediately. Blocking calls have to wait on system calls (I/O) to complete before they can return a value. So you, the caller, are blocked until they’re done or a timeout or other error occurs.

Blocking socket calls can be set to non-blocking mode so they return immediately. If you do this, then you’ll need to at least refactor or redesign your application to handle the socket operation when it’s ready.

Because the call returns immediately, data may not be ready. The callee is waiting on the network and hasn’t had time to complete its work. If this is the case, then the current status is the errno value socket.EWOULDBLOCK. Non-blocking mode is supported with .setblocking().

**By default, sockets are always created in blocking mode.**

### This meant that in the server, calls made to this socket will no longer block. 
### When it’s used with sel.select(), you can wait for events on one or more sockets and then read and write data when it’s ready.

- [Selector](https://docs.python.org/3/library/selectors.html)

## How to?

- To run this project, open up one cmd instance as administrator and run the ```server.py``` file with the 
```python server.py <host> <port>``` command entering you host address and port number for communication.
- Open another cmd instance as administrator and run the ```server.py``` file with the 
```python server.py <host> <port> <no. of connections>``` command.

### All non-privileged ports have value > 1023
### Use host as 127.0.0.1 i.e., standard loopback interface address (localhost) for convenience or run the command ```ipconfig``` to find you local public ip on an administrative cmd instance. 