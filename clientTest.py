import time
import unittest
import server as sr
import client as cl


class clientTest(unittest.TestCase):

    def setUp(self):
        self.serverTest = sr.Server()
        self.client0 = cl.Client()
        self.client1 = cl.Client()

        self.serverTest.serverTCP.listen()

        self.client0.socketTCP.connect(self.serverTest.serverTCP.getsockname())
        self.client1.socketTCP.connect(self.serverTest.serverTCP.getsockname())
        self.conn0, self.addr0 = self.serverTest.serverTCP.accept()
        self.conn1, self.addr1 = self.serverTest.serverTCP.accept()
        self.client0.connectedTCP = True
        self.client1.connectedTCP = True

        self.serverTest.clientList.add('client0', self.conn0, self.addr0)
        self.serverTest.clientList.add('client1', self.conn1, self.addr1)

        self.inputs = [self.serverTest, self.conn0, self.conn1]
        pass

    def tearDown(self):
        self.client0.socketTCP.send(f'{self.client0}: disconnect'.encode())
        self.client1.socketTCP.send(f'{self.client1}: disconnect'.encode())
        self.serverTest.serverTCP.close()

    def test_a_connection(self):
        self.client0.socketTCP.sendto(f'Message to server'.encode(), self.serverTest.serverTCP.getsockname())
        self.assertEqual(self.conn0.recv(1024).decode(), 'Message to server')

        self.client1.socketTCP.sendto(f'Message to server'.encode(), self.serverTest.serverTCP.getsockname())
        self.assertEqual(self.conn1.recv(1024).decode(), 'Message to server')

    def test_b_requestTCP_and_responseTCP(self):
        print()
        """ ---------------------------------- Test request&response ShowOnline ------------------------------------ """
        cl.requestTCP(self.client0.viewController, self.client0, 'Show online')
        msg = self.conn0.recv(1024).decode()
        print(msg)
        sr.handle_call(self.serverTest, msg, self.conn0, self.inputs)
        msg = self.client0.socketTCP.recv(1024).decode()
        print(msg)
        cl.responseTCP(self.client0.viewController, self.client0, msg)

        self.assertTrue('client0' in msg and 'client1' in msg, msg)

        ''' -------------------------------------------------------------------------------------------------------- '''
        # clear chat window for next test
        cl.requestTCP(self.client0.viewController, self.client0, 'Clear')
        """ ---------------------------------- Test request&response Clear ----------------------------------------- """
        self.client0.messageList.add('[TEST]', 'Clear messages0')
        self.client0.messageList.add('[TEST]', 'Clear messages1')
        self.client0.messageList.add('[TEST]', 'Clear messages2')

        self.assertEqual(len(self.client0.messageList.messages), 3)
        # Calling to clear request
        cl.requestTCP(self.client0.viewController, self.client0, 'Clear')
        # 0 mean for num of messages on 'screen'
        self.assertEqual(len(self.client0.messageList.messages), 0)
        ''' -------------------------------------------------------------------------------------------------------- '''

        """ ---------------------------------- Test request&response Send ------------------------------------------ """
        self.client0.viewController.messageToField.text.text = 'client1'
        self.client0.viewController.messageField.text.text = 'TEST'

        # Private message from 'client0' to 'client1'
        cl.requestTCP(self.client0.viewController, self.client0, 'Send')
        # Server response message to client1
        msg = self.conn0.recv(1024).decode()
        print(msg)
        sr.handle_call(self.serverTest, msg, self.conn0, self.inputs)
        # client1 receive the message
        msg = self.client1.socketTCP.recv(1024).decode()
        print(msg)
        cl.responseTCP(self.client1.viewController, self.client1, msg)
        for message in self.client1.messageList.messages:
            if 'TEST' in message.message:
                self.assertEqual(msg.split(': ')[2], 'TEST', message.message)

        # message for all

        ''' -------------------------------------------------------------------------------------------------------- '''
        # clear chat window for next test
        cl.requestTCP(self.client0.viewController, self.client0, 'Clear')
        """ ---------------------------------- Test request&response ShowServerFiles ------------------------------- """
        cl.requestTCP(self.client0.viewController, self.client0, 'Show server files')
        msg = self.conn0.recv(1024).decode()
        print(msg)
        sr.handle_call(self.serverTest, msg, self.conn0, self.inputs)
        msg = self.client0.socketTCP.recv(1024).decode()
        print(msg)
        cl.responseTCP(self.client0.viewController, self.client0, msg)

        for file in self.serverTest.fileList.fileList.items():
            if file[0] in 'test.jpg':
                self.assertEqual('test.jpg', file[0])
            if file[0] in 'text.txt':
                self.assertEqual('text.txt', file[0])
        self.assertTrue('test.jpg' in msg and 'text.txt' in msg, msg)

        ''' -------------------------------------------------------------------------------------------------------- '''