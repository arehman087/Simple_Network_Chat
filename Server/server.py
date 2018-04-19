import asyncio
from collections import namedtuple
import enum
import logging
import pickle
import socket
import MessagePacket

Person = namedtuple("Person", "name, reader, writer")


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


class Server(object):
    """
    Server that will handle clients and reroute messages
    """

    def __init__(self, host, port):
        """
        initializes the server with a dictionary of clients
        """
        # will use dictionary to keep track of clients
        self.__clients = {}
        self.__host = host
        self.__port = port
        self.__limit = 10

    def kill_and_remove_client(self, person):
        """
        kills client and removes them from the client list
        :param person: namedtuple that holds the name, reader, and writer
        """
        del self.__clients[person.name]
        person.writer.close()

    def kill_client(self, writer):
        """
        kills client on connecf for sending a bad message
        :param writer:
        """
        writer.close()

    def get_client(self, message_pack):
        """
        gets the client from the message sent and sends the message to the
        client
        """
        logging.debug('%s was received from message', message_pack.get_client_name())
        if message_pack.get_client_name is None:
            logging.debug('invalid format!')
            return 0

        try:
            self.__clients[message_pack.get_client_name()].writer.write(pickle.dumps
                                                                        (MessagePacket.MessagePacket
                                                                         (message_pack.get_message(),
                                                                          MessageType.MESSAGE.value, None)))
        except KeyError:
            return 0
        return 1

    async def converse(self, person):
        """
        does the conversation for the client
        :param person: named tuple that holds the name, reader, and writer
        """
        while True:
            client_shake = pickle.loads(await person.reader.read(4096))

            if client_shake.get_message_type() == MessageType.MESSAGE.value:
                logging.debug("server has received type message")
                # make sure to get all messages.

                message = client_shake.get_message()
                message = person.name + ': ' + message

                # if a new client connects update list from all clients.
                message_pack = MessagePacket.MessagePacket(message, MessageType.ON_CONNECT.value, person.name)
                for p in self.__clients:
                    # may need to add message types in client
                    self.__clients[p].writer.write(pickle.dumps(message_pack))

            elif client_shake.get_message_type() == MessageType.WHISPER.value:
                logging.debug("server has received type whisper")
                message = pickle.loads(await person.reader.read(4096))
                val = self.get_client(message)
                if val == 0:
                    person.writer.write(pickle.dumps('error sending message'))

            elif client_shake == MessageType.SHOUT.value:
                pass

    async def __client_handler(self, reader, writer):
        """
        handle new clients
        :param reader: reader for the client
        :param writer: writer for the client
        """
        logging.debug("add client to the dictionary")

        while True:
            message_pack = pickle.loads(await reader.read(4096))
            logging.debug("client sent %s", message_pack.get_message_type())
            if message_pack.get_message_type() != MessageType.ON_CONNECT.value:
                logging.debug("Client sent something wrong, killing client")
                self.kill_client(writer)
                return
            if message_pack.get_client_name() in self.__clients.keys():
                logging.debug("asking for a different name")
                writer.write(pickle.dumps(MessagePacket.MessagePacket(None, MessageType.RESEND_NAME.value, None)))
            else:
                writer.write(pickle.dumps(MessagePacket.MessagePacket(None, MessageType.OKAY_NAME.value, None)))
                logging.debug("%s has connected", message_pack.get_client_name())
                new_client = Person(name=message_pack.get_client_name(), reader=reader, writer=writer)
                self.__clients[message_pack.get_client_name()] = new_client
                await self.converse(new_client)

    def start_server(self):
        logging.debug("starting server")

        loop = asyncio.get_event_loop()
        server_loop = asyncio.start_server(self.__client_handler, host=self.__host, port=self.__port)
        server_side = loop.run_until_complete(server_loop)

        logging.debug("Serving on %s", (server_side.sockets[0].getsockname()))

        try:
            loop.run_forever()
        except KeyboardInterrupt:
            pass
        finally:
            server_side.close()
            loop.run_until_complete(server_side.wait_closed())
            loop.close()


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    x = socket.gethostbyname(socket.gethostname())
    print("Host: %s", x)
    print("Port: 4444")

    server = Server(x, 4444)
    server.start_server()
