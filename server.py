"""Represented by MVC Design"""
import pygame as pg
import socket
import threading
import select
import time

# Constant variables
# SERVER = socket.gethostbyname(socket.gethostname())
SERVER = "127.0.0.1"
PORT = 50000
ADDR = (SERVER, PORT)
FORMAT = 'utf-8'
DISCONNECT_MESSAGE = "!DISCONNECT"


# ---------------------------- model -------------------------------------
class Client:

    def __init__(self, name, conn):
        self.name = name
        self.conn = conn
        # ipAddr, port = str(conn)[126:145].split(", ")
        # self.address = (ipAddr, int(port))


class ClientList:

    def __init__(self):
        self.clients = {}

    def add(self, name, conn):
        newClient = Client(name, conn)
        if conn not in self.clients.keys():
            self.clients[conn] = newClient

    def getByConn(self, conn):
        if self.clients[conn] is not None:
            return self.clients[conn]
        return None

    def getConnByName(self, name):
        for client in self.clients.values():
            if name in client.name:
                return client.conn
        return None

    def nameExists(self, name):
        for client in self.clients.values():
            if name in client.name:
                print("--- TRUE ---")
                return True
        return False

    def isConnected(self, conn):
        return self.clients[conn] is not None


class File:
    def __init__(self, name, size):
        self.name = name
        self.size = size
    pass


class FileList:
    def __init__(self):
        self.fileList = {}

    def add(self, name, size):
        self.fileList[name] = size


def handle_call(self, message, conn, inputs):
    """Static methode"""
    details = message.split(": ")
    if details[1] == 'name':
        if not self.clientList.nameExists(details[2]):
            client = self.clientList.getByConn(conn)
            client.name = details[2]
            self.clientList.clients[conn] = client
        else :
            conn.send(f"name: client{self.clientNumber}".encode())
            pass
    # Get calls
    elif details[1] == 'get_users':
        onlineMembers = "get_users: --- start list ---: "
        for client in self.clientList.clients.values():
            onlineMembers += f"{client.name},"
        onlineMembers += ": --- end list ---"
        conn.send(onlineMembers.encode())
    elif details[1] == 'get_list_file':
        fileList = "get_list_file: --- Server File List ---: "
        fileList += f"{self.fileList.fileList},"
        fileList += ": --- End Server File List ---"
        conn.send(fileList.encode())
    # Set calls

    elif details[1] == 'set_msg':
        clientConn = self.clientList.getConnByName(f"{details[3]}")
        if clientConn is not None:
            clientConn.send(f"set_msg: {details[2]}: {details[4]}".encode())
        pass
    elif details[1] == 'set_msg_all':
        if len(details) > 2:
            # Send message to all online clients
            print(f"\n{details}\n")
            for sock in inputs[1:]:
                sock.send(f"set_msg_all: {details[2]}: {details[3]} ".encode())
        pass
    # Disconnect
    elif details[1] == 'disconnect':
        print(inputs)
        for k, v in enumerate(inputs):
            if conn == v:
                del inputs[k]
        print(inputs)
        del self.clientList.clients[conn]
        self.clientNumber -= 1
        pass
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

    def handleMousePress(self,event) -> bool:
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

    # TODO: Fix colors
    def __init__(self):
        self.screen = pg.display.set_mode((800, 600))                                   # set screen
        pg.display.set_caption("Server controller")                                     # set title
        self.colors = {                                                                 # set colors
            "background": (110, 207, 95),
            "clientRect": (188, 240, 180),
            "white": (255, 255, 255),
            "gray": (134, 134, 134),
            "dark-green": (49, 150, 33),
            "black": (0, 0, 0)
        }
        self.font = pg.font.SysFont("Arial", 24)                                        # set font

        # Buttons
        self.startButton = Button(                                                      # set start server button
            panel=Rectangle((170, 20), (140, 50)),
            text=Label("Start server", self.font),
            onColor=self.colors['white'],
            offColor=self.colors['dark-green']
        )
        self.exitButton = Button(  # set exit and turn off the server button
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
        if controller.flag:
            serverDetails = Label(f"Server IP: {socket.gethostbyname(socket.gethostname())}", self.font)
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
        pg.init()
        self.viewController = ViewController()
        self.clientList = ClientList()
        self.fileList = FileList()
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind(ADDR)
        self.flag = False
        self.clientNumber = 0

        print("[STARTING] server is starting...")
        print(f"[LISTENING] Server is listening on {ADDR}")

    # TODO: Finish this constructor

    def run(self):
        """The main function that connect between the server and all the clients"""
        self.server.listen()
        inputs = [self.server]
        outputs = []
        running = True
        while running:

            # Events for pygame
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    running = False
                elif event.type == pg.MOUSEBUTTONDOWN:
                    running = not self.viewController.exitButton.hasMosue()
                    if self.viewController.startButton.handleMousePress(event):
                        self.flag = True

            if self.flag:
                readable, writeable, exceptional = select.select(inputs, outputs, inputs, 0.1)
                for s in readable:
                    if s is self.server:
                        # Listen on server
                        conn, addr = s.accept()
                        conn.setblocking(0)
                        inputs.append(conn)
                        self.clientList.add(f"client{self.clientNumber}", conn)
                        self.clientNumber += 1
                    else:
                        # Client connection
                        if s:
                            message = s.recv(1024).decode()
                            if message:
                                handle_call(self=self, message=message, conn=s, inputs=inputs)
                                print(f"[ONLINE]: {len(self.clientList.clients)}")
                                print(f"[ONLINE]: {[client.name for client in self.clientList.clients.values()]}")
                                print(f"[RECEIVED] {message.split(': ')[1:]}")

            self.viewController.drawScreen(self.clientList, self)  # Update the viewController

    def exit(self):
        pass
# ------------------------------------------------------------------------
if __name__ == '__main__':
    server = Server()
    server.run()
    server.exit()