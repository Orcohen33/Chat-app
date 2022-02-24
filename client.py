"""Represented by MVC Design
Or cohen"""
import pygame as pg
import socket
import select
import time

# Constant variables
PORT = 50000
SERVER = "127.0.0.1"
FORMAT = 'utf-8'
ADDR = (SERVER, PORT)
DISCONNECT_MESSAGE = "!DISCONNECT"


# ---------------------------- model -------------------------------------
class Message:
    def __init__(self, name, message):
        self.name = name
        self.message = message


class MessageList:
    def __init__(self):
        self.messages = []

    def __iter__(self):
        return self.messages

    def add(self, name, message):
        newMessage = Message(name, message)
        self.messages.append(newMessage)


# STATIC METHODE
def handle_send_calls(viewController, controller, call):
    if call == "Login":
        try:
            if viewController.addrField.text.text == 'localhost':
                controller.socket.connect(ADDR)
            else :
                controller.socket.connect((viewController.addrField.text.text, PORT))
            controller.connected = True
        except:
            pass
        controller.name = viewController.userNameField.text.text
        try:
            controller.socket.send(f"{controller.socket}: username: {controller.name}".encode())
        except:
            print("Cant send data to server")
    if call == "Show online":
        if controller.connected:
                controller.socket.send(f"{controller.socket}: showonline".encode())

    elif call == "Clear":
        # work well
        controller.messageList.messages = []

    elif call == "Send":
        if controller.connected:
            controller.socket.send(f"{controller.socket}: send".encode())
        print("[TO SERVER] send")
        pass


def handle_recive_call(viewController, controller, call):
    if "online list" in call:
        splitted = call.split(", ")
        controller.messageList.add("", splitted[0])
        controller.messageList.add("", splitted[1])
        controller.messageList.add("", splitted[2])
        print("-----------------------WORK--------------------\n"
              f"{call}")
        print(splitted)
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
        self.ready = False

    def hasMosue(self):
        (x, y) = pg.mouse.get_pos()
        left = self.panel.rect[0]
        right = self.panel.rect[0] + self.panel.rect[2]
        up = self.panel.rect[1]
        down = self.panel.rect[1] + self.panel.rect[3]
        return left < x < right and up < y < down

    def handleMousePress(self, controller, viewController):
        if self.hasMosue():
            self.ready = True
            print(f"{self.text.text}")
        if self.ready:
            self.ready = False
            # controller.socket.send(f"{self.text.text}".encode())
            handle_send_calls(viewController, controller, self.text.text)

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
        self.flag = False

    def hasMouse(self):
        return self.panel.hasMouse()

    def handleKeyPress(self, event):
        if self.active:
            if event.key == pg.K_RETURN:
                self.ready = True

                print(f"name : {self.text.text}")  # Test

            elif event.key == pg.K_BACKSPACE:
                self.text.text = self.text.text[:-1]
            elif event.key == pg.K_SPACE:
                self.text.text += " "
            else:
                self.text.text += pg.key.name(event.key)
                # print(f"user pressed \"{pg.key.name(event.key)}\"")  # Test

    def handleMousePress(self, controller):
        if self.hasMouse():
            self.active = True
            # print("clicked")
        else:
            self.active = False

    def draw(self, surface, panelColor, textColor):
        if self.active:
            temp = panelColor
            panelColor = textColor
            textColor = temp

        self.panel.draw(surface, panelColor)
        self.text.draw(surface, self.panel.rect[0] + 7, self.panel.rect[1] + 7, textColor)


class ChatWindow:

    def __init__(self, text, panel):
        self.text = text
        self.panel = panel

    def draw(self, surface, panelColor, textColor):
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

        # Buttons
        self.loginButton = Button(                                                  # login button
            panel=Rectangle((10, 10), (70, 50)),
            text=Label("Login", pg.font.SysFont("Arial", 20)),
            onColor=self.colors['white'],
            offColor=self.colors['dark-green']
        )

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
        self.showServerFilesButton = Button(                                        # show server files button
            panel=Rectangle((10, 65), (150, 50)),
            text=Label("Show server files", self.font),
            onColor=self.colors['white'],
            offColor=self.colors['dark-green']
        )
        self.sendButton = Button(                                                   # send message button
            panel=Rectangle((670, 550), (85, 40)),
            text=Label("Send", self.font),
            onColor=self.colors['white'],
            offColor=self.colors['dark-green']
        )
        self.downloadButton = Button(                                               # download button
            panel=Rectangle((670, 625), (95, 40)),
            text=Label("Download", self.font),
            onColor=self.colors['white'],
            offColor=self.colors['dark-green']
        )

        # Input fields
        userNameLabel = Label("username", self.font)
        userNamePanel = Rectangle((165, 10), (130, 50))
        self.userNameField = InputField(userNameLabel, userNamePanel)               # Username input field

        addrLabel = Label("localhost", self.font)
        addrPanel = Rectangle((380, 10), (150, 50))
        self.addrField = InputField(addrLabel, addrPanel)                           # Address input field

        messageToLabel = Label("", pg.font.SysFont("ariel", 19))
        self.messageToField = InputField(messageToLabel, Rectangle((10, 550), (120, 40)))   # MessageTO input field

        messageLabel = Label("", pg.font.SysFont("ariel", 19))
        self.messageField = InputField(messageLabel, Rectangle((155, 550), (500, 40)))      # Message input field

        serverFileNameLabel = Label("Enter file name", pg.font.SysFont("ariel", 20))        # Server name file input
        self.serverFileNameField = InputField(serverFileNameLabel, Rectangle((10, 625), (317, 40)))  # field

        self.clientFileNameField = InputField(serverFileNameLabel, Rectangle((337, 625), (317, 40)))


        # Labels
        self.userNameLabel = Label("Name: ", self.font)                                     # Name label
        self.addrLabel = Label("Address: ", self.font)                                      # Address label
        self.messageToLabel = Label("To (blank to all)", pg.font.SysFont("ariel", 19))      # MessageTo string label
        self.messageLabel = Label("Message", pg.font.SysFont("ariel", 20))                  # Message label
        self.serverFileNameLabel = Label("Server File Name", pg.font.SysFont("ariel", 20))  # ServerFileName Label
        self.clientFileNameLabel = Label("Client File Name(save as...)", pg.font.SysFont("ariel", 20))  # ClientFileName

        # Chat window
        self.messagesRect = Rectangle((10, 120), (780, 400))                                # messages window
        self.messagesLabel = Label("", pg.font.SysFont("ariel", 18))

    def drawScreen(self, messagesList):
        self.screen.fill(self.colors["background"])                                             # Draw background

        # Buttons
        self.loginButton.draw(self.screen)                                                      # Draw loginButton
        self.showOnlineButton.draw(self.screen)                                                 # Draw showOnlineButton
        self.clearButton.draw(self.screen)                                                      # Draw clearButton
        self.showServerFilesButton.draw(self.screen)                                       # Draw showServerFiles Button
        self.sendButton.draw(self.screen)                                                   # Draw send button
        self.downloadButton.draw(self.screen)                                               # Draw download button

        # Input fields
        self.userNameField.draw(self.screen, self.colors['dark-green'], self.colors['white'])   # Draw userNameInput
        self.addrField.draw(self.screen, self.colors['dark-green'], self.colors['white'])       # Draw AddressInput
        self.messageToField.draw(self.screen, self.colors['dark-green'], self.colors['white'])  # Draw To input field
        self.messageField.draw(self.screen, self.colors['dark-green'], self.colors['white'])  # Draw message input field
        self.serverFileNameField.draw(self.screen, self.colors['dark-green'], self.colors['white']) #
        self.clientFileNameField.draw(self.screen, self.colors['dark-green'], self.colors['white'])

        # Labels
        self.userNameLabel.draw(self.screen, 95, 20, self.colors['black'])                      # Draw userName
        self.addrLabel.draw(self.screen, 300, 20, self.colors['black'])                         # Draw Address
        self.messageToLabel.draw(self.screen, 5, 525, self.colors['black'])                     # Draw To label
        self.messageLabel.draw(self.screen, 150, 525, self.colors['black'])                     # Draw message label
        self.serverFileNameLabel.draw(self.screen, 5, 600, self.colors['black'])         # Draw serverFileName label
        self.clientFileNameLabel.draw(self.screen, 333, 600, self.colors['black'])

        # Chat window
        self.messagesRect.draw(self.screen, self.colors['white'])                                # Draw messages screen
        y = 110
        for message in messagesList:
            self.messagesLabel.text = f"{message.name}: {message.message}"
            self.messagesLabel.draw(self.screen, 15, y + 10, self.colors['black'])
            y += 15
            if y > 515:
                for i in range(6):
                    messagesList.pop(i)

        pg.display.update()


# ---------------------------- control -----------------------------------

class Client:
    def __init__(self):
        pg.init()
        self.font = pg.font.SysFont("Arial", 24)
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.viewController = ViewController()
        self.name = self.viewController.userNameField.text.text
        self.messageList = MessageList()
        self.connected = False


    # TODO: Finish this constructor

    def run(self):

        inputs = [self.socket]
        outputs = []
        running = True
        while running:

            # Events for pygame
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    running = False
                elif event.type == pg.MOUSEBUTTONDOWN:
                    """This condition checks if any component has been clicked"""
                    # Buttons
                    self.viewController.loginButton.handleMousePress(self, self.viewController)                      # login button
                    self.viewController.showOnlineButton.handleMousePress(self, self.viewController)                 # showOnline button
                    self.viewController.clearButton.handleMousePress(self, self.viewController)                      # clear button
                    self.viewController.showServerFilesButton.handleMousePress(self, self.viewController)                  # showServerFiles button
                    self.viewController.sendButton.handleMousePress(self, self.viewController)
                    self.viewController.downloadButton.handleMousePress(self, self.viewController)

                    # Input fields
                    self.viewController.userNameField.handleMousePress(self)                                         # userNameField
                    self.viewController.addrField.handleMousePress(self)                                             # addrField
                    self.viewController.messageToField.handleMousePress(self)
                    self.viewController.messageField.handleMousePress(self)
                    self.viewController.serverFileNameField.handleMousePress(self)
                    self.viewController.clientFileNameField.handleMousePress(self)
                    # print(pg.mouse.get_pos())

                elif event.type == pg.KEYDOWN:
                    """This condition checks if any input field has been used"""
                    self.viewController.userNameField.handleKeyPress(event)
                    self.viewController.addrField.handleKeyPress(event)
                    self.viewController.messageToField.handleKeyPress(event)
                    self.viewController.messageField.handleKeyPress(event)
                    self.viewController.serverFileNameField.handleKeyPress(event)
                    self.viewController.clientFileNameField.handleKeyPress(event)

            readable, writable, exceptional = select.select(inputs, outputs, inputs, 0.1)
            for s in readable:
                if s is self.socket:
                    msgs = s.recv(1024).decode()
                    message = Message("", msgs)
                    handle_recive_call(self.viewController, self, msgs)
                    self.messageList.messages.append(message)
                    print(f"[RECIVED] :"+msgs)

            self.viewController.drawScreen(self.messageList.messages)                                                # Update the viewController

    def exit(self):
        pass


# ------------------------------------------------------------------------

if __name__ == '__main__':
    client = Client()
    client.run()
    client.exit()



# s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# port = int(input("Connect on port: "))
# s.connect(("192.168.1.242", port))
# this = input("Press any key to exit:")
