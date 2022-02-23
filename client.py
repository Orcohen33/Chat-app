"""Represented by MVC Design"""
import pygame as pg
import socket
import threading
import select
import time

# Constant variables
PORT = 50000
SERVER = "192.168.1.100"
FORMAT = 'utf-8'
ADDR = (SERVER, PORT)
DISCONNECT_MESSAGE = "!DISCONNECT"


# ---------------------------- model -------------------------------------
class Functions:

    def login(self):
        pass

    def userName(self):
        pass

    def address(self):
        pass

    def showOnline(self):
        pass

    def clearMessages(self):
        pass

    def showServerFiles(self):
        pass

# ---------------------------- view --------------------------------------


class Label:
    def __init__(self, text, fontStyle):
        self.text = text
        self.font = fontStyle

    def draw(self, surface, x, y, color):
        surface.blit(self.font.render(self.text, True, color), (x + 7, y + 7))


class Rectangle:
    def __init__(self, topLeft, bottomRight):
        self.rect = (topLeft[0], topLeft[1], bottomRight[0], bottomRight[1])

    def hasMouse(self):
        (x, y) = pg.mouse.get_pos()
        left = self.rect[0]
        right = self.rect[0] + self.rect[2]
        up = self.rect[1]
        down = self.rect[1] + self.rect[3]
        return left < x < right and up < y < down

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

    def handleMousePress(self):
        if self.hasMosue():
            print(f"{self.text.text}")

    def draw(self, surface):
        panelColor = self.offColor
        textColor = self.onColor
        if self.hasMosue():
            panelColor = self.onColor
            textColor = self.offColor
        self.panel.draw(surface, panelColor)
        self.text.draw(surface, self.panel.rect[0] + 5, self.panel.rect[1] + 5, textColor)


class InputField:

    def __init__(self, text, panel):
        self.text = text
        self.panel = panel
        self.ready = False
        self.active = False

    def hasMouse(self):
        return self.panel.hasMouse()

    def handleKeyPress(self, event):
        if self.active:
            if event.key == pg.K_RETURN:
                self.ready = True
                print(f"Username : {self.text.text.split(': ')}")  # Test

            elif event.key == pg.K_BACKSPACE:
                self.text.text = self.text.text[:-1]
            elif event.key == pg.K_SPACE:
                self.text.text += " "
            else:
                self.text.text += pg.key.name(event.key)
                print(f"User pressed \"{pg.key.name(event.key)}\"")  # Test

    def handleMousePress(self, event):
        if self.hasMouse():
            self.active = True
            print("Clicked")
        else:
            self.active = False

    def draw(self, surface, panelColor, textColor):
        if self.active:
            temp = panelColor
            panelColor = textColor
            textColor = temp

        self.panel.draw(surface, panelColor)
        self.text.draw(surface, self.panel.rect[0] + 7, self.panel.rect[1] + 7, textColor)


class ViewController:

    def __init__(self):
        self.screen = pg.display.set_mode((800, 700))                               # set screen
        pg.display.set_caption("Chat application")                                  # title
        self.colors = {  # set colors
            "background": (110, 207, 95),
            "clientRect": (188, 240, 180),
            "white": (255, 255, 255),
            "gray": (134, 134, 134),
            "dark-green": (49, 150, 33),
            "black": (0, 0, 0)
        }                                                         # colors
        self.font = pg.font.SysFont("Arial", 20)                                    # set font
        self.loginButton = Button(                                                  # login button
            panel=Rectangle((10, 10), (70, 50)),
            text=Label("Login", pg.font.SysFont("Arial", 20)),
            onColor=self.colors['white'],
            offColor=self.colors['dark-green']
        )

        self.userNameLabel = Label("Name: ", self.font)                             # Name label
        userNameLabel = Label("username", self.font)
        userNamePanel = Rectangle((165, 10), (130, 50))
        self.userNameField = InputField(userNameLabel, userNamePanel)               # Username input field

        self.addrLabel = Label("Address: ", self.font)                              # Address label
        addrLabel = Label("localhost", self.font)
        addrPanel = Rectangle((380, 10), (150, 50))
        self.addrField = InputField(addrLabel, addrPanel)                           # Address input field

        self.showOnlineButton = Button(                                             # showOnline button
            panel=Rectangle((540, 10), (120, 50)),
            text=Label("Show online", self.font),
            onColor=self.colors['white'],
            offColor=self.colors['dark-green']
        )

        self.clearButton = Button(                                                  # clear button
            panel=Rectangle((670, 10), (70, 50)),
            text=Label("Clear", self.font),
            onColor=self.colors['white'],
            offColor=self.colors['dark-green']
        )
        self.showServerFiles = Button(                                              # show server files button
            panel=Rectangle((10, 65), (150, 50)),
            text=Label("Show server files", self.font),
            onColor=self.colors['white'],
            offColor=self.colors['dark-green']
        )

        self.messageRect = Rectangle((10, 120), (780, 400))                         # message window

    def drawScreen(self):
        self.screen.fill(self.colors["background"])                                             # Draw background
        self.loginButton.draw(self.screen)                                                      # Draw loginButton

        self.userNameLabel.draw(self.screen, 95, 20, self.colors['white'])                      # Draw userName
        self.userNameField.draw(self.screen, self.colors['dark-green'], self.colors['white'])   # Draw userNameInput

        self.addrLabel.draw(self.screen, 300, 20, self.colors['white'])                         # Draw Address
        self.addrField.draw(self.screen, self.colors['dark-green'], self.colors['white'])       # Draw AddressInput

        self.showOnlineButton.draw(self.screen)                                                 # Draw showOnlineButton
        self.clearButton.draw(self.screen)                                                      # Draw clearButton
        self.showServerFiles.draw(self.screen)                                               # Draw showServerFiles Butt

        self.messageRect.draw(self.screen, self.colors['white'])                                # Draw message screen
        pg.display.update()


# ---------------------------- control -----------------------------------

class Client:
    def __init__(self):
        pg.init()

        self.fn = Functions()
        self.font = pg.font.SysFont("Arial", 24)

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        self.viewController = ViewController()

    # TODO: Finish this constructor

    def run(self):
        server = socket.socket.connect(ADDR)

        running = True
        while running:

            # Events for pygame
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    running = False
                elif event.type == pg.MOUSEBUTTONDOWN:
                    """This condition checks if any component has been clicked"""
                    self.viewController.loginButton.handleMousePress()                      # login button
                    self.viewController.userNameField.handleMousePress(event)               # userNameField
                    self.viewController.addrField.handleMousePress(event)                   # addrField
                    self.viewController.showOnlineButton.handleMousePress()                 # showOnline button
                    self.viewController.clearButton.handleMousePress()                      # clear button
                    self.viewController.showServerFiles.handleMousePress()                  # showServerFiles button

                elif event.type == pg.KEYDOWN:
                    """This condition checks if any input field has been used"""
                    self.viewController.userNameField.handleKeyPress(event)
                    self.viewController.addrField.handleKeyPress(event)

            self.viewController.drawScreen()                                                # Update the viewController

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
    #             conn.send("MASSAGE RECIVED".encode(FORMAT))
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
    client = Client()
    client.run()
    client.exit()
# client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# client.connect(ADDR)
#
#
# def send(msg):
#     message = msg.encode(FORMAT)
#     msg_length = len(message)
#     send_length = str(msg_length).encode(FORMAT)
#     send_length += b' ' * (64 - len(send_length))
#     client.send(send_length)
#     client.send(message)
#     print(client.recv(2048).decode(FORMAT))
#
#
# send("Hello world")


# s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# port = int(input("Connect on port: "))
# s.connect(("192.168.1.242", port))
# this = input("Press any key to exit:")
