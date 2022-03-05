# Chat app

### Introduction:
The project represents a multiplayer messenger app(using TCP), while at the same time the possibility of transferring files using reliable udp.

The project shows our capabilities in using sockets, unittest, object-oriented programming, and GUI

The application should consist a client program and a server program. The server program control every request and send back the response to specific client, or to all online sockets(e.g send a message to all the chat) and even transfer files using kind of 'selective repeat protocol' with a little bit changes (explanation in 'Problem statement').


# Problem statement

 The application should consist a client program and a server program. 
 
 The server program hosts files and responds to requests for files.
 
 The client can ask the server which file he can transfer, the server is response to this request and now the client can request from the server to transfer specific file from a  list.
 
 The server breaks the file into segments (we choose 512 bytes to each segment (e.g 3mb/512bytes = 6 segments, and the last segment is less then 512 bytes)) and a unique number to each segment.
 The server start to send it for the client (in a specific format that i made to unpack it easy at the client server (e.g ID: bytes)). 
 
 When the client finished to received the files, he iterate   the receiving structure and check what is received and what lost, then he send back to server that he lost some packets (e.g packet with serial number :3, 11,20).
 
 The server get request to send back all the missing packets,
 The client check it again and when finished to receive all the packets he send back to server that he finished to receive and then the connection between them is gone.


https://user-images.githubusercontent.com/92351152/156900203-7c148dbb-0671-4cd5-a512-ba325832e3d9.mp4

