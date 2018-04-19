import socket
import enum
import logging
import pickle
import MessagePacket


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
    REFRESH_CLIENTS = 7


class Client(object):
    """
    creates a client that will receive messages
    """

    def __init__(self, host, port):
        self.__sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.__host = host
        self.__port = port
        self.__clients = []

    def make_connection(self):
        """
        makes the connection to the host.
        """

        self.__sock.connect((self.__host, self.__port))

    def send_name(self, name):
        """
        send name to server on initial connection
        :return 1 if the name is longer than 2 characters and unique else return 0
        """
        if name is None:
            return 0
        self.__sock.sendall(pickle.dumps(MessagePacket.MessagePacket(None, MessageType.ON_CONNECT.value, name)))
        chk = pickle.loads(self.__sock.recv(4096))
        if chk.get_message_type() == MessageType.OKAY_NAME.value:
            return 1
        else:
            return 0

    def send_to_server(self, message, mess_type, client_name):
        """
        send message to the server
        :param message: message being sent
        :param mess_type: type of message; whisper, shout, regular message
        :param client_name: name of the client if the message is a whisper
        """
        self.__sock.sendall(pickle.dumps(MessagePacket.MessagePacket(message,mess_type, client_name)))
        return

    def receive_from_server(self):
        """
        recieve the message from the server
        :return: string of what was received
        """
        message = pickle.loads(self.__sock.recv(4096))
        if message.get_message_type() == MessageType.REFRESH_CLIENTS.value:
            self.refresh_clients(message)
            print(self.__clients)
            if message.get_client_name() is None:
                return ''
            return str(message.get_client_name()) + " has connected\n"
        return str(message.get_message())

    def refresh_clients(self, message_pack):
        """
        update the client dictionary
        :param message_pack: packet that holds the dictionary
        """
        self.__clients = message_pack.get_message()

    def get_clients(self):
        return self.__clients
