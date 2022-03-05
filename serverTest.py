import socket
import threading
import time
import unittest
import server as sr
import client as cl


class ServerTests(unittest.TestCase):
    """
    In this testclass we will test all the responses from server back to client
    """

    def setUp(self):
        self.serverTest = sr.Server()
        self.serverTest.serverTCP.listen(5)
        self.client0 = cl.Client()
        self.client1 = cl.Client()
        self.client2 = cl.Client()
        self.client3 = cl.Client()
        time.sleep(0.5)
        ip = self.serverTest.serverTCP.getsockname()
        print(self.client0.socketTCP.connect_ex(ip))

        self.client1.socketTCP.connect(self.serverTest.serverTCP.getsockname())
        self.client2.socketTCP.connect(self.serverTest.serverTCP.getsockname())
        self.client3.socketTCP.connect(self.serverTest.serverTCP.getsockname())
        self.conn0, self.addr0 = self.serverTest.serverTCP.accept()
        self.conn1, self.addr1 = self.serverTest.serverTCP.accept()
        self.conn2, self.addr2 = self.serverTest.serverTCP.accept()
        self.conn3, self.addr3 = self.serverTest.serverTCP.accept()
        print(f'\n{self.conn1, self.conn2, self.conn3}\n{self.addr1, self.addr2, self.addr3}')
        self.serverTest.clientList.add('client0', self.conn0, self.addr0)
        self.serverTest.clientList.add('client1', self.conn1, self.addr1)
        self.serverTest.clientList.add('client2', self.conn2, self.addr2)
        self.serverTest.clientList.add('client3', self.conn3, self.addr3)

        self.inputs = [self.serverTest.serverTCP, self.conn0, self.conn1, self.conn2, self.conn3]

    def tearDown(self) -> None:
        self.client1.socketTCP.send(f'{self.client1}: disconnect'.encode())
        self.client2.socketTCP.send(f'{self.client2}: disconnect'.encode())
        self.client3.socketTCP.send(f'{self.client3}: disconnect'.encode())
        self.serverTest.serverTCP.close()

    def test_a_connection(self):
        self.client1.socketTCP.sendto(f'Message to server'.encode(), self.serverTest.serverTCP.getsockname())
        self.assertEqual(self.conn1.recv(1024).decode(), 'Message to server')

        self.conn1.sendto(f'Message to client'.encode(), self.addr1)
        self.assertEqual(self.client1.socketTCP.recv(1024).decode(), 'Message to client')

        self.client2.socketTCP.sendto(f'Message to server'.encode(), self.serverTest.serverTCP.getsockname())
        self.assertEqual(self.conn2.recv(1024).decode(), 'Message to server')

        self.conn2.sendto(f'Message to client'.encode(), self.addr2)
        self.assertEqual(self.client2.socketTCP.recv(1024).decode(), 'Message to client')

        self.client3.socketTCP.sendto(f'Message to server'.encode(), self.serverTest.serverTCP.getsockname())
        self.assertEqual(self.conn3.recv(1024).decode(), 'Message to server')

        self.conn3.sendto(f'Message to client'.encode(), self.addr3)
        self.assertEqual(self.client3.socketTCP.recv(1024).decode(), 'Message to client')

    def test_b_handleCalls(self):
        """Test the response for every request from client to server"""
        print(self.serverTest.clientList.clients.items())

        ''' -------------------------------------- Test change name response --------------------------------------- '''
        self.client1.socketTCP.send(f'{self.client1.socketTCP}: change: client11'.encode())  # Request
        msg = self.conn1.recv(1024).decode()
        sr.handle_call(self.serverTest, msg, self.conn1, self.inputs)
        # Response from server
        self.assertEqual(self.client1.socketTCP.recv(1024).decode(), 'response: Name changed successfully')
        # Check if the name is changed in data structure
        self.assertEqual(self.serverTest.clientList.getConnByName('client11'), self.conn1)

        # change for exists name
        self.client2.socketTCP.send(f'{self.client1.socketTCP}: change: client11'.encode())  # Request
        msg = self.conn2.recv(1024).decode()
        sr.handle_call(self.serverTest, msg, self.conn2, self.inputs)
        # Response from server
        self.assertEqual(self.client2.socketTCP.recv(1024).decode(),
                         'response: Name exists, choose new name and press login again')

        ''' -------------------------------------------------------------------------------------------------------- '''

        ''' -------------------------------------- Test get_user response ------------------------------------------ '''
        self.client1.socketTCP.send(f'{self.client1.socketTCP}: get_users'.encode())  # Request
        msg = self.conn1.recv(1024).decode()
        sr.handle_call(self.serverTest, msg, self.conn1, self.inputs)
        # Response from server
        msg = self.client1.socketTCP.recv(1024).decode()
        self.assertTrue('client11' in msg and 'client2' in msg and 'client3' in msg)
        ''' -------------------------------------------------------------------------------------------------------- '''

        ''' ------------------------------- Test set_msg (private message) response ------------------------------- '''
        # 'client11' send private message to 'client2'
        self.client1.socketTCP.send(
            f'{self.client1.socketTCP}: set_msg: client11: client2: test_private_message'.encode())  # Request
        msg = self.conn1.recv(1024).decode()
        sr.handle_call(self.serverTest, msg, self.conn1, self.inputs)
        # Response from server to destination client
        msg = self.client2.socketTCP.recv(1024).decode()  # 'client2' has received message from 'client11'
        self.assertEqual('set_msg: client11: test_private_message', msg)
        ''' -------------------------------------------------------------------------------------------------------- '''

        ''' --------------------------------------- Test set_msg_all response -------------------------------------- '''
        self.client1.socketTCP.send(f'{self.client1.socketTCP}: set_msg_all: client11: test_all_message'.encode())
        msg = self.conn1.recv(1024).decode()
        sr.handle_call(self.serverTest, msg, self.conn1,
                       self.inputs)
        msg1 = self.client1.socketTCP.recv(1024).decode()
        msg2 = self.client2.socketTCP.recv(1024).decode()
        msg3 = self.client3.socketTCP.recv(1024).decode()
        self.assertEqual(msg1, msg2, msg3)
        ''' -------------------------------------------------------------------------------------------------------- '''

        ''' --------------------------------------- Test get_list_file response ------------------------------------ '''
        self.client1.socketTCP.send(f'{self.client1.socketTCP}: get_list_file: '.encode())
        msg = self.conn1.recv(1024).decode()
        sr.handle_call(self.serverTest, msg, self.conn1, self.inputs)
        msg = self.client1.socketTCP.recv(1024).decode()
        print(msg)
        # cl.responseTCP(self.client1.viewController, self.client1, msg)
        for file in self.serverTest.fileList.fileList.items():
            if file[0] in 'test.jpg':
                self.assertEqual('test.jpg', file[0])
            if file[0] in 'text.txt':
                self.assertEqual('text.txt', file[0])
        self.assertTrue('test.jpg' in msg and 'text.txt' in msg)

        ''' ------------------------------- Test download response (Via reliable UDP connection ---------------------'''
        # # self.client0.send(f'')
        # self.client1.socketTCP.send(f'{self.client1}: download: test.jpg: client1.jpg: empty'.encode())
        # msg = self.conn1.recv(1024).decode()
        # thread0 = threading.Thread(target=sr.handle_call, args=(self.serverTest, msg, self.conn1, self.inputs))
        # thread0.start()
        # # sr.handle_call(self.serverTest, msg, self.conn1, self.inputs)
        # msg = self.client1.socketTCP.recv(1024).decode()
        # # time.sleep(1)
        # # thread1 = threading.Thread(target=cl.responseTCP,
        # #                            args=(self.client1.viewController, self.client1, msg))
        # # thread1.start()
        # cl.responseTCP(self.client1.viewController, self.client1, msg)
        # # time.sleep(0.5)

        ''' -------------------------------------------------------------------------------------------------------- '''


if __name__ == '__main__':
    unittest.main()
