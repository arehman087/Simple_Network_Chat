import socket
import socketserver
import threading
import logging

PORT = 4444
HOST = 'localHost'

SEND_ON_EXIT = -1
SEND_ON_CLIENT_CONN = 1
SEND_ON_CLIENT_DISC = 2
SEND_ON_CLIENT_MSG = 3

class TCPHandler(socketserver.BaseRequestHandler):
    def handle(self):
        self.data = self.request.recv(1024).strip()
        logging.debug("%s sent: %s", self.client_address[0], self.data)
        self.request.sendall(self.data.upper)

class Server:
    def __init__(self):
        logging.debug('Launching server on address %s and port %d', HOST, PORT)
        try:
            self.__server_sock = socketserver.TCPServer(server_address=(HOST, PORT), )
            self.__server_sock.serve_forever()
        except KeyboardInterrupt:
            logging.debug('closing server')
            #kill_server()

if __name__ == '__main__':
    server = Server
