import math
import os.path

import pygame as pg
import socket
import select
import threading
import time
from os import listdir

# Constant variables
SERVER = f'{socket.gethostbyname(socket.gethostname())}'
print(f'{socket.gethostbyname(socket.gethostname())}')
PORT = 50000
ADDR = (SERVER, PORT)
FORMAT = 'utf-8'
BUFFER_SIZE = 1024


# ---------------------------- model -------------------------------------
class Client:

    def __init__(self, name, addr):
        self.name = name
        self.conn = addr


class ClientList:

    def __init__(self):
        self.clients = {}

    def add(self, name, conn, addr):
        newClient = Client(name, addr)
        if conn not in self.clients.keys():
            self.clients[conn] = newClient

    def getByConn(self, conn):
        for con in self.clients.keys():
            if con == conn:
                return self.clients[con]
        return None

    def getByAddr(self, addr):
        if self.clients[addr] is not None:
            return self.clients[addr]
        return None

    def getConnByName(self, name):
        for item in self.clients.items():
            if name == item[1].name:
                return item[0]
        # for client in self.clients.values():
        #     if name in client.name:
        #         return client.conn
        return None

    def nameExists(self, name):
        for client in self.clients.values():
            if name == client.name:
                print("--- TRUE ---")
                return True
        return False

    def deleteByAddr(self, addr):
        if self.clients[addr] is not None:
            del self.clients[addr]
        pass

    def isConnected(self, conn):
        if self.getByConn(conn):
            return True
        return False


class FileList:
    def __init__(self):
        onlyfiles = {f: os.path.getsize(f) for f in listdir('.') if
                     0 <= os.path.getsize(f) <= 64000 and '.py' not in f}
        self.fileList = onlyfiles

    def add(self, name, size):
        self.fileList[name] = size


class PortUDP:
    def __init__(self, isUsed, client_addr, sock):
        self.isUsed = isUsed
        self.client_addr = client_addr
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)


class PortUDPList:
    def __init__(self):
        self.portList = {port: PortUDP(False, None, None) for port in range(55000, 55016)}

    def availablePort(self):
        for item in self.portList.items():
            if not item[1].isUsed and item[1].client_addr is None:
                return item[0]
        return None


class ReliableUDP:
    """
    This class reliably represents file transfer
    Constructor contains the number of packets
    and a data structure that stores the packets in it by serial number
    """

    def __init__(self, numOfPackets, packetsOfFile):
        self.numOfPackets = numOfPackets
        self.packetsOfFile = packetsOfFile

    def sendPackets(self, sockUDP, client_addr, portUDPList):
        """Explanation in readme"""
        sockUDP.setblocking(1)
        inputs = [sockUDP]
        outputs = [sockUDP]
        # Variables
        receivedDict = {key: False for key in range(self.numOfPackets)}
        packetCount = 0
        key1 = 0
        key2 = 0
        running = True
        print(client_addr)
        while running:
            readable, writeable, exceptional = select.select(inputs, outputs, inputs, 0.1)
            # while packetCount < self.numOfPackets and key1 != len(self.packetsOfFile.keys()):
            for s in readable:
                if s is sockUDP:
                    bytes_read, addr = s.recvfrom(16)
                    bytes_read = bytes_read.decode().split(': ')
                    if bytes_read[0] == 'resend' or bytes_read[0] == 'ACK':
                        try:
                            temp1 = int(bytes_read[1][0])
                            temp2 = int(bytes_read[1][1])
                        except:
                            temp1 = temp2 = 0
                        if bytes_read[0] == 'resend':
                            print(f'resend {temp1, temp2}')
                            details = f'{temp1}{temp2}: '.encode() + self.packetsOfFile[temp1][temp2]
                            s.sendto(details, addr)
                        elif bytes_read[0] == 'ACK':
                            # print(f'ACK {temp1, temp2}')          # print for testing
                            if temp1 == 0:
                                receivedDict[temp2] = True
                            else:
                                num = temp1 * 10 + temp2
                                receivedDict[num] = True
                    elif bytes_read[0] == 'done':
                        print(f'Done')
                        inputs.pop(0)
                        outputs.pop(0)
                        running = False
                        break
                else:
                    print('nothing received')

            for r in writeable:
                if key2 < len(self.packetsOfFile[key1].keys()) and key1 <= len(self.packetsOfFile.keys()):
                    details = f'{key1}{key2}: '.encode() + self.packetsOfFile[key1][key2]
                    sockUDP.sendto(details, client_addr)
                    if (key2 + 1) % len(self.packetsOfFile[key1]) == 0:
                        key1 = (key1 + 1) % len(self.packetsOfFile.keys())
                    key2 = (key2 + 1) % 10

        portUDPList[sockUDP.getsockname()[1]].isUsed = False
        portUDPList[sockUDP.getsockname()[1]].client_addr = None
        # portUDPList[sockUDP.getsockname()[1]].sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # sockUDP.close()


def sendFileUDPReliable(sockUDP, filename, portUDPList, client_addr):
    """
    This method prepares the data for the reliable transfer
    """
    fileSize = os.path.getsize(filename)                                   # Size of the file (bytes unit)
    numOfPackets = math.ceil(fileSize / BUFFER_SIZE)                       # total packets number
    fileToFrame = fileToFrames(filename, numOfPackets, fileSize)           # Convert the file into small packets
    srp = ReliableUDP(numOfPackets=numOfPackets, packetsOfFile=fileToFrame)  # Represent select and repeat protocl
    srp.sendPackets(sockUDP, client_addr, portUDPList)          # Select and repeat method for reliable transfer files


def fileToFrames(filename, numOfPackets, fileSize):
    """
    This method breaks down the file into small parts, and gives each part a serial number,
    and finally stores it in a data structure
    e.g : {0: 3: b'data'}       -> the id to this data is 03
    :return: allPackets
    """
    allPackets = {}
    totalPackets = numOfPackets
    with open(filename, 'rb') as f:
        while totalPackets > 0:
            for key in range(math.ceil(numOfPackets / 10)):
                allPackets[key] = {}
                for key2 in range(10):
                    bytes_read = f.read(BUFFER_SIZE)
                    if bytes_read:
                        allPackets[key][key2] = bytes_read
                        fileSize -= len(bytes_read)
                        totalPackets -= 1
                        if fileSize == 0 and round(len(allPackets) / 10) == round(numOfPackets / 10):
                            break
    return allPackets


def handle_call(self, message, conn, inputs):
    """Static methode"""
    details = message.split(": ")
    if details[1] == 'change':
        if not self.clientList.nameExists(details[2]):
            serverSock = self.clientList.getByConn(conn)
            serverSock.name = details[2]
            conn.send(f'response: Name changed successfully'.encode())
        else:
            conn.send(f'response: Name exists, choose new name and press login again'.encode())

    # Get calls
    elif details[1] == 'get_users':
        onlineMembers = "get_users: --- start list ---: "
        for serverSock in self.clientList.clients.values():
            onlineMembers += f"{serverSock.name},"
        onlineMembers += ": --- end list ---"
        conn.send(onlineMembers.encode())

    elif details[1] == 'get_list_file':
        fileList = "get_list_file: --- Server File List ---: "
        fileList += f"{[f for f in self.fileList.fileList.keys() if not '.idea' in f]}"
        fileList += ": --- End Server File List ---"
        conn.send(fileList.encode())
    # Set calls

    elif details[1] == 'set_msg':
        clientConn = self.clientList.getConnByName(f"{details[3]}")
        if clientConn is not None:
            clientConn.send(f"set_msg: {details[2]}: {details[4]}".encode())
        else:
            conn.send(f'set_msg: : \'{details[3]}\' does not exists'.encode())

    elif details[1] == 'set_msg_all':
        if len(details) > 2:
            # Send message to all online clients
            print(f"\n{details}\n")
            for sock in inputs[1:]:
                sock.send(f"set_msg_all: {details[2]}: {details[3]} ".encode())


    # Download
    elif details[1] == 'download':
        sameEndFile = details[2].split('.')[1] == details[3].split('.')[1]
        print(f'sameEndFile: {sameEndFile}')
        print(details)
        print('----------------- download -----------------------')
        if details[2] in self.fileList.fileList.keys() and sameEndFile:
            """If the file exist in server folder && serverFileName and clientFileName have the same end"""
            port = self.portUDPList.availablePort()
            serverSock = self.portUDPList.portList[port]
            print(serverSock)
            try:
                if 'laddr' not in str(serverSock.sock):
                    serverSock.sock.bind((SERVER, port))
                serverSock.isUsed = True
                self.connectedUDP = True
                ''' Send back to client the details about the port & filename & file size '''
                conn.send(
                    f'download: {socket.gethostbyname(socket.gethostname())}: {port}: {details[3]}: {os.path.getsize(details[2])}'.encode())
                ''' Receiving details about the client connected '''
                msgs, client_addr = serverSock.sock.recvfrom(BUFFER_SIZE)
                msgs = msgs.decode()
                msgs = msgs.split(': ')
                serverSock.client_addr = (msgs[0], int(msgs[1]))
                thread = threading.Thread(
                    target=sendFileUDPReliable,
                    args=(serverSock.sock, details[2], self.portUDPList.portList, client_addr)
                )
                time.sleep(1)
                thread.start()
            except ConnectionError:
                conn.send(f'response: [SYSTEM]: Error for binding the socket, please try again'.encode())
                self.portUDPList.portList[port].sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        else:
            conn.send(f'response: [SYSTEM]: Download error, try again and make sure all fields are correct'.encode())

    elif details[1] == 'finish':
        addr = (details[2], int(details[3]))
        print(addr)
        for item in self.portUDPList.portList.items():
            if item[1].client_addr == addr:
                item[1].isUsed = False
                item[1].client_addr = None
                item[1].sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                break
    # Disconnect
    elif details[1] == 'disconnect':
        for k, v in enumerate(inputs):
            if conn == v:
                inputs[k].close()
                del inputs[k]
                print("[SYSTEM] Closed socketTCP")
                break
        del self.clientList.clients[conn]
        self.clientNumber -= 1


# ---------------------------- view --------------------------------------


class Label:
    def __init__(self, text, fontStyle):
        self.text = text
        self.font = fontStyle

    def draw(self, surface, x, y, color):
        surface.blit(self.font.render(self.text, True, color), (x + 8, y + 8))


class Rectangle:
    def __init__(self, topLeft, bottomRight):
        self.rect = (topLeft[0], topLeft[1], bottomRight[0], bottomRight[1])

    def draw(self, surface, color):
        pg.draw.rect(surface, color, self.rect)


class Button:
    def __init__(self, panel, text, onColor, offColor):
        self.panel = panel
        self.text = text
        self.onColor = onColor
        self.offColor = offColor

    def hasMosue(self):
        (x, y) = pg.mouse.get_pos()
        left = self.panel.rect[0]
        right = self.panel.rect[0] + self.panel.rect[2]
        up = self.panel.rect[1]
        down = self.panel.rect[1] + self.panel.rect[3]
        return left < x < right and up < y < down

    def handleMousePress(self, event) -> bool:
        if self.hasMosue():
            print(f"{self.text.text}t")
            return True

    def draw(self, surface):
        panelColor = self.offColor
        textColor = self.onColor
        if self.hasMosue():
            panelColor = self.onColor
            textColor = self.offColor
        self.panel.draw(surface, panelColor)
        self.text.draw(surface, self.panel.rect[0] + 5, self.panel.rect[1] + 5, textColor)


class ViewController:
    """
    This class represent the GUI
    """
    # TODO: Fix colors
    def __init__(self):
        self.screen = pg.display.set_mode((800, 600))                           # set screen
        pg.display.set_caption("Server controller")                             # set title
        self.colors = {                                                         # set colors
            "background": (36, 152, 152),
            "clientRect": (188, 240, 180),
            "white": (255, 255, 255),
            "gray": (134, 134, 134),
            "dark-green": (49, 150, 33),
            "black": (0, 0, 0)
        }
        self.font = pg.font.SysFont("Arial", 24)                                # set font

        # Buttons
        self.startButton = Button(                                              # set start server button
            panel=Rectangle((170, 20), (140, 50)),
            text=Label("Start server", self.font),
            onColor=self.colors['white'],
            offColor=self.colors['dark-green']
        )
        self.exitButton = Button(                                              # set exit and turn off the server button
            panel=Rectangle((370, 20), (170, 50)),
            text=Label("Exit server", self.font),
            onColor=self.colors['white'],
            offColor=self.colors['dark-green']
        )

        # Labels
        self.clientLabel = Label("", self.font)
        # clientOnline rect
        self.clientRect = Rectangle((80, 80), (650, 500))                       # init rectangle contains online clients

    def drawScreen(self, clientList, controller):
        self.screen.fill(self.colors["background"])
        self.clientRect.draw(self.screen, self.colors["clientRect"])
        self.startButton.draw(self.screen)

        # Draw the active clients
        client = clientList.clients.values()
        if controller.connectedTCP:
            serverDetails = Label(f"Server IP: {SERVER}", self.font)
            serverDetails.draw(self.screen, 280, 70, self.colors['black'])
        y = 90
        for value in client:
            self.clientLabel.text = f"{value.name}"
            self.clientLabel.draw(self.screen, 100, y + 25, self.colors['black'])
            y += 50

        self.exitButton.draw(self.screen)
        pg.display.update()


# ---------------------------- control -----------------------------------

class Server:
    def __init__(self):
        # self.viewController = ViewController()
        self.viewController = None
        self.serverTCP = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.serverTCP.bind(ADDR)
        self.clientList = ClientList()
        self.fileList = FileList()
        self.portUDPList = PortUDPList()
        self.clientNumber = 0
        self.connectedTCP = False
        self.connectedUDP = False

    # TODO: Finish this constructor

    def run(self):
        """The main function that connect between the server and all the clients"""
        pg.init()
        self.viewController = ViewController()
        self.serverTCP.listen()

        inputsTCP = [self.serverTCP]
        outputsTCP = []
        running = True
        while running:

            """Events for pygame"""
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    for client in self.clientList.clients.values():
                        client.conn.close()
                    self.serverTCP.close()
                    self.connectedTCP = False
                    running = False
                elif event.type == pg.MOUSEBUTTONDOWN:
                    if self.viewController.exitButton.hasMosue():
                        for conn in self.clientList.clients.keys():
                            conn.send(f'disconnect'.encode())
                        self.serverTCP.close()
                        self.connectedTCP = False
                        running = False

                    if self.viewController.startButton.handleMousePress(event):
                        self.connectedTCP = True

            if self.connectedTCP:
                """RECEIVE NEW CONNECTIONS AND MESSAGES BY TCP CONNECTION"""
                readableTCP, writeable, exceptional = select.select(inputsTCP, outputsTCP, inputsTCP, 0.1)
                for s in readableTCP:
                    if s is self.serverTCP:
                        # Listen on server
                        conn, addr = s.accept()
                        conn.setblocking(0)
                        inputsTCP.append(conn)
                        self.clientList.add(f"client{self.clientNumber}", conn, addr)
                        self.clientNumber += 1
                    else:
                        # Client connection
                        if s:
                            message, addr = s.recvfrom(BUFFER_SIZE)
                            message = message.decode()
                            if message:
                                handle_call(self=self, message=message, conn=s, inputs=inputsTCP)
                                for item in self.portUDPList.portList.items():
                                    if item[1].isUsed:
                                        print(
                                            f'---- Client address: {item[1].client_addr}, Socket: {str(item[1].sock)[54:]} ----')
                                break

            self.viewController.drawScreen(self.clientList, self)  # Update the viewController

    def exit(self):
        pass
# ------------------------------------------------------------------------


if __name__ == '__main__':
    server = Server()
    server.run()
    server.exit()




