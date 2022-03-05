import math
import threading
import pygame as pg
import socket
import select
import time


# Constant variables

PORT = 50000
SERVER = '127.0.0.1'
FORMAT = 'utf-8'
ADDR = (SERVER, PORT)
BUFFER_SIZE = 1024

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


def receiveFileUDP(socketUDP, controller, lastFileSize, lastFileName):
    socketUDP.setblocking(0)
    inputs = [socketUDP]
    outputs = [socketUDP]
    # Variables
    fileSize = int(lastFileSize)
    numOfPackets = math.ceil(fileSize / BUFFER_SIZE)
    onePacketPercent = round(100 / numOfPackets, 2)
    countPackets = 0
    fileSegments = fileToFrames(numOfPackets, fileSize)
    receivedDict = {key: False for key in range(numOfPackets)}
    serverAddr = None
    running = True
    while running:
        readable, writeable, exceptional = select.select(inputs, outputs, inputs, 0.1)

        for r in writeable:
            for i in range(countPackets):
                if not receivedDict[i] and serverAddr is not None:
                    if i < 10:
                        print(f'resend {i}')
                        r.sendto(f'resend: 0{i}'.encode(), serverAddr)
                    else:
                        key = i/10
                        key2 = i % 10
                        print(f'resend {key}{key2}')
                        r.sendto(f'resend: {key}{key2}'.encode(), serverAddr)
            time.sleep(0.05)
            # for item in receivedDict.items():
            #     if not item[1] and serverAddr is not None:
            #         if item[0] < 10:
            #             print(f'resend {item[0]}')
            #             socketUDP.sendto(f'resend: 0{item[0]}'.encode(), serverAddr)
            #         else:
            #             key = item[0]/10
            #             key2 = item[0]%10
            #             socketUDP.sendto(f'resend: {key}{key2}'.encode(), serverAddr)

        for s in readable:
            if s is socketUDP:
                bytes_read, serverAddress = s.recvfrom(BUFFER_SIZE + 4)
                if bytes_read:
                    serverAddr = serverAddress
                    key = int(bytes_read[:1])  # unpack the key from bytes_read
                    key2 = int(bytes_read[1:2])  # unpack the key from bytes_read
                    data = bytes_read[4:]  # unpack the bytes from bytes_read
                    if fileSegments[key][key2] is None:
                        print(key, key2)
                        controller.viewController.downloadBar.updateBar(onePacketPercent,
                                                                        numOfPackets)  # update downloadbar
                        fileSegments[key][key2] = data
                        if serverAddr is not None:
                            # print(f'ACK{key}{key2}')
                            s.sendto(f'ACK: {key}{key2}'.encode(), serverAddr)
                        countPackets += 1
                        if key == 0:
                            receivedDict[key2] = True
                        else:
                            num = key*10+key2
                            receivedDict[num] = True
            time.sleep(0.05)

        # Check if all packets has received
        numOfFalse = 0
        for item in fileSegments.items():
            for v in fileSegments[item[0]].values():
                if v is None:
                    numOfFalse += 1
        if numOfFalse == 0:
            running = False
            break
    # Done , writing the bytes into file
    if serverAddr is not None:
        socketUDP.sendto(f'done: 00'.encode(), serverAddr)
    if countPackets == numOfPackets:
        print("Start write the file")
        with open(lastFileName, 'wb') as f:
            testSize = 0
            for item in fileSegments.items():
                for k, item2 in enumerate(item[1].values()):
                    f.write(item2)
                    testSize += len(item2)
    print(f'Finished to write this size: {testSize}')
    controller.readyToReceive = False
    f.close()
    socketUDP.close()


def fileToFrames(numOfPackets, fileSize):
    """
    Split the file to segments that represent by id of their keys
    e.g : {0: 3: b'data'}       -> the id to this data is 03
    :param numOfPackets: number of packets to know how to build the structure
    :param fileSize: fileSize to know how to divide the data into segments
    :return: allPackets
    """

    allPackets = {}
    totalPackets = numOfPackets
    while totalPackets > 0:
        for key in range(math.ceil(numOfPackets / 10)):
            allPackets[key] = {}
            for key2 in range(10):
                # Set all ids value to None, when the client start to receive files he fill this structure
                allPackets[key][key2] = None
                totalPackets -= 1
                if totalPackets == 0:
                    return allPackets
                if fileSize == 0 and round(len(allPackets) / 10) == round(numOfPackets / 10):
                    break

    return allPackets


def requestTCP(viewController, controller, call):
    if call == "Login":
        if not controller.connectedTCP:
            if viewController.addrField.text.text == 'localhost' or viewController.addrField.text.text == '':
                try:
                    controller.socketTCP.connect(ADDR)
                    controller.connectedTCP = True
                except ConnectionError:
                    controller.messageList.add('[SYSTEM]', 'Failed connection, try other IP Address')
                    pass
            else:
                try:
                    controller.socketTCP.connect((viewController.addrField.text.text, PORT))
                    controller.socketTCP.settimeout(10)
                    controller.connectedTCP = True
                except ConnectionError:
                    controller.messageList.add('[SYSTEM]', 'Failed connection, try other IP Address')
                    pass
            # Connection successfully
            time.sleep(0.04)

        if controller.socketTCP and controller.connectedTCP:
            controller.socketTCP.send(
                f'{controller.socketTCP}: change: {viewController.userNameField.text.text}'.encode())

    if controller.connectedTCP:
        if call == "Show online":
            controller.socketTCP.send(f"{controller.socketTCP}: get_users".encode())

        elif call == "Clear":
            # work well
            controller.messageList.messages = []
            controller.viewController.downloadBar.onRect = Rectangle((10, 670), (0, 20))
            controller.viewController.downloadBar.text.text = '0%'

        elif call == "Send":
            messageTo = viewController.messageToField.text.text
            message = viewController.messageField.text.text
            if viewController.messageToField.text.text == "":
                controller.socketTCP.send(
                    f"{controller.socketTCP.getsockname()}: set_msg_all: {controller.name}: {message}".encode())

            else:
                controller.socketTCP.send(
                    f"{controller.socketTCP}: set_msg: {controller.name}: {messageTo}: {message}".encode())
                controller.messageList.add(f"[TO] {messageTo}", message)

        elif call == 'Show server files':
            controller.socketTCP.send(f"{controller.socketTCP}: get_list_file".encode())
        elif call == 'Download':
            if controller.viewController.serverFileNameField.text.text != '':
                controller.socketTCP.send(f'{controller.socketTCP}: download: '
                                          f'{controller.viewController.serverFileNameField.text.text}: '
                                          f'{controller.viewController.clientFileNameField.text.text}: '
                                          f'{controller.detailsUDP}'.encode())
        elif call == 'Disconnect':
            controller.socketTCP.send(f"{controller.socketTCP}: disconnect".encode())
            controller.socketTCP.close()
            controller.connectedTCP = False

            pass


def responseTCP(viewController, controller, call):
    splitted = call.split(": ")
    if splitted[0] == 'name':
        controller.messageList.add("", "This name is taken, please enter other username and press login again")
        controller.name = splitted[1]
        pass

    elif splitted[0] == 'get_list_file' or splitted[0] == 'get_users':
        controller.messageList.add("", splitted[1])
        controller.messageList.add("", splitted[2])
        controller.messageList.add("", splitted[3])
        pass

    elif splitted[0] == 'set_msg':
        controller.messageList.add(f"[FROM] {splitted[1]}", splitted[2])
        pass

    elif splitted[0] == 'set_msg_all':
        controller.messageList.add(splitted[1], splitted[2])
        pass

    elif splitted[0] == 'download':
        port = int(splitted[2])
        try:
            print(f'before {controller.socketUDP}')
            indicator = controller.socketUDP.connect_ex((splitted[1], port))
            print(indicator)
            if indicator != 0:
                controller.socketUDP = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                controller.socketUDP.connect_ex((splitted[1], port))
            controller.connectedUDP = True
            controller.readyToReceive = True
            controller.detailsUDP = (splitted[1], port)
            controller.lastFileName = splitted[3]
            controller.lastFileSize = splitted[4]
            controller.socketUDP.sendto(
                f'{controller.socketUDP.getsockname()[0]}: {controller.socketUDP.getsockname()[1]}'.encode(),
                controller.detailsUDP)
            print(f'after {controller.socketUDP}')

            # Reset the downloadBar if downloaded something before:
            viewController.downloadBar.onRect.rect[2] = 5
        except ConnectionError or ConnectionRefusedError:
            print(f'[SYSTEM] Connection error')

    elif splitted[0] == 'finish_upload':
        controller.connectedUDP = False
        print('finish upload')
        controller.socketUDP.close()

    elif splitted[0] == 'response':
        controller.name = viewController.userNameField.text.text

    elif splitted[0] == 'disconnect':
        controller.socketTCP.close()
        del controller.inputsTCP[0]
    pass


# ---------------------------- view --------------------------------------

class Label:
    def __init__(self, text, fontStyle):
        self.text = text
        self.font = fontStyle
        self.upperCase = False

    def draw(self, surface, x, y, color):
        surface.blit(self.font.render(self.text, True, color), (x + 7, y + 7))


class Rectangle:
    def __init__(self, topLeft, bottomRight):
        self.rect = [topLeft[0], topLeft[1], bottomRight[0], bottomRight[1]]

    def hasMouse(self):
        (x, y) = pg.mouse.get_pos()
        left = self.rect[0]
        right = self.rect[0] + self.rect[2]
        up = self.rect[1]
        down = self.rect[1] + self.rect[3]
        return left < x < right and up < y < down

    def draw(self, surface, color):
        pg.draw.rect(surface, color, self.rect, 0, 8, 8, 8, 8)


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
        if self.ready:
            self.ready = False
            requestTCP(viewController, controller, self.text.text)

    def draw(self, surface, viewController, x, y):
        panelColor = self.offColor
        textColor = self.onColor
        if self.hasMosue():
            panelColor = self.onColor
            textColor = self.offColor
        self.panel.draw(surface, panelColor)
        self.text.draw(surface, self.panel.rect[0] + x, self.panel.rect[1] + y, textColor)


class InputField:

    def __init__(self, text, panel):
        self.text = text
        self.panel = panel
        self.ready = False
        self.active = False
        self.firstTimeClicked = True

    def hasMouse(self):
        return self.panel.hasMouse()

    def handleKeyPress(self, event, controller):
        if self.active:

            if pg.key.name(event.key) == 'delete':
                self.text.text = ""
            elif event.key == pg.K_RETURN:
                self.ready = True
                if controller.connectedTCP and self.text.text != '' and controller.viewController.messageField.active:
                    '''When pressed enter in "messageField" it send the message to server and reset the field'''
                    requestTCP(controller.viewController, controller, "Send")
                    controller.viewController.messageField.text.text = ''
                elif controller.viewController.messageToField.active:
                    '''When pressed enter in "messageToField" - moved to "messageField"'''
                    controller.viewController.messageToField.active = False
                    controller.viewController.messageField.active = True

            elif event.key == pg.K_CAPSLOCK:
                if not self.text.upperCase:
                    self.text.upperCase = True
                else:
                    self.text.upperCase = False

            elif event.key == pg.K_BACKSPACE:
                self.text.text = self.text.text[:-1]
            elif event.key == pg.K_SPACE:
                self.text.text += " "
            elif event.key == pg.K_RCTRL or \
                    event.key == pg.K_LCTRL or \
                    event.key == pg.K_RSHIFT or \
                    event.key == pg.K_LSHIFT or \
                    event.key == pg.K_LALT or \
                    event.key == pg.K_RALT:
                pass
            else:
                # if 'a' <= pg.key.name(event.key) <= 'z' or '0' <= pg.key.name(event.key) <= '9':
                strLen = str(pg.key.name(event.key))[:1]
                if 33 <= ord(strLen) <= 125:
                    if self.text.upperCase:
                        self.text.text += pg.key.name(event.key).upper()
                    else:
                        self.text.text += pg.key.name(event.key)

    def handleMousePress(self, controller):
        if self.hasMouse():
            self.active = True
            if self.firstTimeClicked:
                self.text.text = ''
                self.firstTimeClicked = False
        else:
            self.active = False

    def draw(self, surface, panelColor, textColor, x, y):
        if self.active:
            temp = panelColor
            panelColor = textColor
            textColor = temp

        self.panel.draw(surface, panelColor)
        self.text.draw(surface, self.panel.rect[0] + x, self.panel.rect[1] + y, textColor)


class ChatWindow:

    def __init__(self, text, panel):
        self.text = text
        self.panel = panel

    def draw(self, surface, panelColor, textColor):
        self.panel.draw(surface, panelColor)
        self.text.draw(surface, self.panel.rect[0] + 7, self.panel.rect[1] + 7, textColor)


class DownloadBar:
    def __init__(self, text, offRect, onRect):
        self.text = text
        self.size = None
        self.offRect = offRect
        self.onRect = onRect

    def draw(self, surface, offRectColor, onRectColor, textColor):
        pg.draw.rect(surface, offRectColor, self.offRect, 0)
        pg.draw.rect(surface, onRectColor, self.onRect, 1, 0)
        self.text.draw(surface, 350, 660, textColor)

    def updateBar(self, onePacketPercent, totalPackets):
        if self.onRect.rect[2] < self.offRect.rect[2]:

            # 780 is the length of downloadBar
            self.onRect.rect[2] += 780 / totalPackets

            temp = self.text.text.split('%')
            percent = round(float(temp[0]), 2)
            percent += round(onePacketPercent, 2)
            if percent > 99:
                percent = 100
            self.text.text = f'{round(percent, 2)}%'


class ViewController:

    def __init__(self):
        self.screen = pg.display.set_mode((800, 700))                               # set screen
        pg.display.set_caption("Chat application")                                  # title

        self.colors = {  # set colors
            "background": (36, 152, 152),
            "green": (71, 185, 59),
            "white": (255, 255, 255),
            "gray": (134, 134, 134),
            "light-blue": (112, 187, 187),
            "blue": (102, 186, 186),
            "black": (0, 0, 0),
            "red": (219, 2, 18)
        }  # colors
        self.font = pg.font.SysFont("Arial", 20)                                        # set font

        # Buttons
        self.loginButton = Button(                                                      # login button
            panel=Rectangle((602, 10), (187, 50)),
            text=Label("Login", pg.font.SysFont("Arial", 20)),
            onColor=self.colors['white'],
            offColor=self.colors['green']
        )

        self.showOnlineButton = Button(                                                 # showOnline button
            panel=Rectangle((402, 65), (190, 50)),
            text=Label("Show online", self.font),
            onColor=self.colors['white'],
            offColor=self.colors['blue']
        )

        self.clearButton = Button(                                                      # clear button
            panel=Rectangle((10, 65), (187, 50)),
            text=Label("Clear", self.font),
            onColor=self.colors['white'],
            offColor=self.colors['blue']
        )
        self.showServerFilesButton = Button(                                            # show server files button
            panel=Rectangle((207, 65), (187, 50)),
            text=Label("Show server files", self.font),
            onColor=self.colors['white'],
            offColor=self.colors['blue']
        )
        self.sendButton = Button(                                                       # send message button
            panel=Rectangle((685, 550), (105, 45)),
            text=Label("Send", self.font),
            onColor=self.colors['white'],
            offColor=self.colors['blue']
        )
        self.downloadButton = Button(                                                    # download button
            panel=Rectangle((685, 622), (105, 42)),
            text=Label("Download", self.font),
            onColor=self.colors['white'],
            offColor=self.colors['blue']
        )
        self.disconnectButton = Button(
            panel=Rectangle((602, 65), (187, 50)),
            text=Label("Disconnect", self.font),
            onColor=self.colors['white'],
            offColor=self.colors['red']
        )

        # List of buttons
        self.buttonsList = [self.sendButton, self.loginButton, self.clearButton, self.downloadButton,
                            self.showOnlineButton, self.showServerFilesButton, self.disconnectButton]

        # Input fields
        userNameLabel = Label("username", pg.font.SysFont('ariel', 30))
        userNamePanel = Rectangle((100, 10), (180, 50))
        self.userNameField = InputField(userNameLabel, userNamePanel)                             # Username input field

        addrLabel = Label("localhost", pg.font.SysFont('ariel', 30))
        addrPanel = Rectangle((410, 10), (180, 50))
        self.addrField = InputField(addrLabel, addrPanel)                                          # Address input field

        messageToLabel = Label("", pg.font.SysFont("ariel", 19))
        self.messageToField = InputField(messageToLabel, Rectangle((10, 550), (135, 45)))        # MessageTO input field

        messageLabel = Label("", pg.font.SysFont("ariel", 19))
        self.messageField = InputField(messageLabel, Rectangle((160, 550), (515, 45)))             # Message input field

        serverFileNameLabel = Label("Enter file name", pg.font.SysFont("ariel", 20))            # Server name file input
        self.serverFileNameField = InputField(serverFileNameLabel, Rectangle((10, 622), (327, 42)))  # field

        clientFileNameLabel = Label("Enter file name (as you want to save)",
                                    pg.font.SysFont("ariel", 20))                               # Server name file input
        self.clientFileNameField = InputField(clientFileNameLabel, Rectangle((347, 622), (327, 42)))

        # List of input fields
        self.inputFieldList = [self.addrField, self.clientFileNameField, self.userNameField, self.messageField,
                               self.messageToField, self.serverFileNameField]

        # Labels
        self.userNameLabel = Label("Name: ", pg.font.SysFont('ariel', 35))                                  # Name label
        self.addrLabel = Label("Address: ", pg.font.SysFont('ariel', 35))                                # Address label
        self.messageToLabel = Label("To (blank to all)", pg.font.SysFont("ariel", 19))          # MessageTo string label
        self.messageLabel = Label("Message", pg.font.SysFont("ariel", 20))                               # Message label
        self.serverFileNameLabel = Label("Server File Name", pg.font.SysFont("ariel", 20))        # ServerFileName Label
        self.clientFileNameLabel = Label("Client File Name(save as...)", pg.font.SysFont("ariel", 20))  # ClientFileName

        # Chat window
        self.messagesRect = Rectangle((10, 120), (780, 400))                                           # messages window
        self.messagesLabel = Label("", pg.font.SysFont("ariel", 20))

        # Download bar
        self.downloadBar = DownloadBar(
            text=Label("0%", self.font),
            offRect=Rectangle((10, 670), (780, 20)),
            onRect=Rectangle((10, 670), (0, 20))
        )

    def drawScreen(self, messagesList):
        self.screen.fill(self.colors["background"])                                                    # Draw background
        # Buttons
        self.loginButton.draw(self.screen, viewController=self, x=63, y=7)                            # Draw loginButton
        self.showOnlineButton.draw(self.screen, viewController=self, x=40, y=7)                  # Draw showOnlineButton
        self.clearButton.draw(self.screen, viewController=self, x=60, y=7)                            # Draw clearButton
        self.showServerFilesButton.draw(self.screen, viewController=self, x=20, y=7)       # Draw showServerFiles Button
        self.sendButton.draw(self.screen, viewController=self, x=25, y=2)                             # Draw send button
        self.downloadButton.draw(self.screen, viewController=self, x=10, y=2)                     # Draw download button
        self.disconnectButton.draw(self.screen, viewController=self, x=45, y=7)

        # Input fields
        self.userNameField.draw(self.screen, self.colors['blue'], self.colors['white'], x=5, y=10)  # Draw userNameInput
        self.addrField.draw(self.screen, self.colors['blue'], self.colors['white'], x=5, y=10)      # Draw AddressInput
        self.messageToField.draw(self.screen, self.colors['blue'], self.colors['white'], x=15,
                                 y=8)  # Draw To input field
        self.messageField.draw(self.screen, self.colors['blue'], self.colors['white'], x=15,
                               y=8)  # Draw message input field
        self.serverFileNameField.draw(self.screen, self.colors['blue'], self.colors['white'], x=15, y=8)  #
        self.clientFileNameField.draw(self.screen, self.colors['blue'], self.colors['white'], x=15, y=8)

        # Labels
        self.userNameLabel.draw(self.screen, 10, 17, self.colors['black'])                               # Draw userName
        self.addrLabel.draw(self.screen, 290, 20, self.colors['black'])                                   # Draw Address
        self.messageToLabel.draw(self.screen, 5, 525, self.colors['black'])                              # Draw To label
        self.messageLabel.draw(self.screen, 160, 525, self.colors['black'])                         # Draw message label
        self.serverFileNameLabel.draw(self.screen, 5, 598, self.colors['black'])             # Draw serverFileName label
        self.clientFileNameLabel.draw(self.screen, 343, 598, self.colors['black'])

        # Chat window
        self.messagesRect.draw(self.screen, self.colors['white'])                                 # Draw messages screen
        y = 110
        for message in messagesList:
            self.messagesLabel.text = f"{message.name}: {message.message}"
            self.messagesLabel.draw(self.screen, 15, y + 10, self.colors['black'])
            y += 15
            if y > 515:
                for i in range(6):
                    messagesList.pop(i)

        # Download Bar
        self.downloadBar.draw(self.screen, self.colors['blue'], self.colors['white'], self.colors['black'])
        pg.display.update()


# ---------------------------- control -----------------------------------

class Client:
    def __init__(self):
        self.socketTCP = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socketUDP = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        pg.init()
        self.viewController = ViewController()
        self.name = self.viewController.userNameField.text.text

        self.messageList = MessageList()
        self.connectedTCP = False
        self.connectedUDP = False
        self.readyToReceive = False
        self.detailsUDP = None
        self.lastFileName = None
        self.lastFileSize = None
        self.inputsTCP = [self.socketTCP]

    def run(self):
        """
        Client main methode control between model and view and server
        :return: None
        """
        outputsTCP = [self.socketTCP]

        running = True
        while running:

            if self.socketTCP and self.connectedTCP:
                readable, writable, exceptional = select.select(self.inputsTCP, outputsTCP, self.inputsTCP, 0.1)
                for s in readable:
                    msgs = s.recv(BUFFER_SIZE).decode()
                    responseTCP(self.viewController, self, msgs)
                    print(f"[RESPONSE]: {msgs.split(': ')}\n")

            if self.socketUDP and self.connectedUDP and self.readyToReceive:
                thread = threading.Thread(
                    target=receiveFileUDP,
                    args=(self.socketUDP, self, self.lastFileSize, self.lastFileName))
                thread.start()
                self.readyToReceive = False
                self.connectedUDP = False

            # Events for pygame
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    if self.connectedTCP:
                        requestTCP(self.viewController, self, 'Disconnect')
                    running = False
                elif event.type == pg.MOUSEBUTTONDOWN:
                    """This condition checks if any component has been clicked by mouse"""
                    # Buttons
                    for button in self.viewController.buttonsList:
                        button.handleMousePress(self, self.viewController)

                    # Input fields
                    for field in self.viewController.inputFieldList:
                        field.handleMousePress(self)

                elif event.type == pg.KEYDOWN:
                    """This condition checks if any input field has been used"""
                    for field in self.viewController.inputFieldList:
                        field.handleKeyPress(event, self)

            self.viewController.drawScreen(self.messageList.messages)                   # Update the viewController


# ------------------------------------------------------------------------

if __name__ == '__main__':
    client = Client()
    client.run()
