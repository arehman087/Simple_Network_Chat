import socket
import enum
import logging
import pickle
import threading


class MessageType(enum.Enum):
    """
    byte sent at beginning of the message to specify the type
    """
    ON_CONNECT = 0
    ON_DISCONNECT = 1
    MESSAGE = 2
    WHISPER = 3
    SHOUT = 4
    RESEND_NAME = 5
    OKAY_NAME = 6


class Client(object):
    """
    creates a client that will recieve messages
    """

    def __init__(self, host, port):
        self.__sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.__host = host
        self.__port = port

    def make_connection(self):
        """
        makes the connection to the host.
        :param host: IP address of the server it is connecting to
        :param port: port of the host
        """
        try:
            self.__sock.connect((self.__host, self.__port))
        except socket.error as msg:
            logging.debug("Connection error: %s", msg)

    def send_name(self, name):
        """
        send name to server on initial connection
        :return 1 if the name is longer than 2 characters and unique else return 0
        """
        if len(name) < 2:
            return
        self.__sock.sendall(bytes([MessageType.ON_CONNECT.value, MessageType.ON_CONNECT.value]))
        self.__sock.sendall(pickle.dumps(name))
        chk = self.__sock.recv(2)
        if chk[0] == MessageType.OKAY_NAME.value:
            return 1
        else:
            return 0

    def send_to_server(self, message, mess_type):
        """
        send message to the server
        :param message: message being sent
        :param mess_type: type of message; whisper, shout, regular message
        """
        self.__sock.sendall(bytes([mess_type, mess_type]))
        self.__sock.sendall(pickle.dumps(message))
        return

    def receive_from_server(self):
        """
        recieve the message from the server
        :return: string of what was received
        """
        message = pickle.loads(self.__sock.recv(4096))
        return str(message)