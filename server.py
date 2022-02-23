"""Represented by MVC Design"""
import pygame as pg
import socket
import threading
import select
import time

# Constant variables
SERVER = socket.gethostbyname(socket.gethostname())
PORT = 50000
ADDR = (SERVER, PORT)
FORMAT = 'utf-8'
DISCONNECT_MESSAGE = "!DISCONNECT"


# ---------------------------- model -------------------------------------
class Client:

    def __init__(self, name):
        self.name = name


class ClientList:

    def __init__(self):
        self.clients = {}

    def add(self, name):
        newClient = Client(name)
        if name not in self.clients.keys():
            self.clients[newClient.name] = True


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
        pg.display.set_caption("Server controller")
        self.colors = {                                                                 # set colors
            "background": (110, 207, 95),
            "clientRect": (188, 240, 180),
            "white": (255, 255, 255),
            "gray": (134, 134, 134),
            "dark-green": (49, 150, 33),
            "black": (0, 0, 0)
        }
        self.font = pg.font.SysFont("Arial", 24)                                        # set font
        self.clientRect = Rectangle((80, 80), (650, 500))                       # init rectangle contains online clients

        self.startButton = Button(                                                      # set start server button
            panel=Rectangle((170, 20), (140, 40)),
            text=Label("Start server", self.font),
            onColor=self.colors['white'],
            offColor=self.colors['dark-green']
        )
        self.exitButton = Button(  # set exit and turn off the server button
            panel=Rectangle((370, 20), (170, 40)),
            text=Label("Exit server", self.font),
            onColor=self.colors['white'],
            offColor=self.colors['dark-green']
        )

        self.clientLabel = Label("...", self.font)

    def drawScreen(self, clientList):
        self.screen.fill(self.colors["background"])
        self.clientRect.draw(self.screen, self.colors["clientRect"])
        self.startButton.draw(self.screen)

        # Draw the active clients
        client = clientList.clients
        y = 90
        for key in client:
            self.clientLabel.text = key
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
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        print("[STARTING] server is starting...")
        self.server.bind(ADDR)
        print(f"[LISTENING] Server is listenting on {ADDR}")

    # TODO: Finish this constructor

    def run(self):
        """The main function that connect between the server and all the clients"""
        self.server.listen()
        inputs = [self.server]
        outputs = []
        clientNumber = 0
        running = True
        while running:

            # Events for pygame
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    running = False
                elif event.type == pg.MOUSEBUTTONDOWN:
                    running = not self.viewController.exitButton.hasMosue()

            readable, writeable, exceptional = select.select(inputs, outputs, inputs, 0.1)
            for s in readable:
                if s is self.server:
                    # Listen on server
                    conn, addr = s.accept()
                    conn.setblocking(0)
                    inputs.append(conn)
                    self.clientList.add(f"Client{clientNumber}")
                    clientNumber += 1
                else:
                    # Client connection
                    message = s.recv(1024).decode()
                    if message:
                        print(f"Got message \"{message}\"\n")
                # TODO: Finish receive messages from clients

            self.viewController.drawScreen(self.clientList)  # Update the viewController

    # TODO: Fix the problem to get connections into the server

    # def handle_client(self, conn, addr):
    #     print(f"[NEW CONNECTION] {addr} connected")
    #
    #     connected = True
    #     while connected:
    #         msg_length = conn.recv(64).decode(FORMAT)
    #         if msg_length:
    #             msg_length = int(msg_length)
    #             msg = conn.recv(msg_length).decode(FORMAT)
    #             if msg == DISCONNECT_MESSAGE:
    #                 connected = False
    #             conn.send("MASSAGE RECEIVED".encode(FORMAT))
    #             print(f"[{addr}]: {msg}")
    #
    #     conn.close()
    #
    # def start_server(self):
    #
    #     running = True
    #     while running:
    #         conn, addr = self.server.accept()
    #         thread = threading.Thread(target=self.handle_client, args=(conn, addr))
    #         thread.start()
    #         print(f"\n[ACTIVE CONNECTION] {threading.active_count() - 1}")

    def exit(self):
        pass


# ------------------------------------------------------------------------

if __name__ == '__main__':
    server = Server()
    server.run()
    server.exit()
