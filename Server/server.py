import asyncio
from collections import namedtuple
import enum
import logging
import sys

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


class Server(object):
    """
    Server that will handle clients and reroute messages
    """

    def __init__(self):
        """
        initializes the server with a dictionary of clients
        """
        # will use namedtuples to keep track of clients
        self.__clients = {}
        self.__host = 'localHost'
        self.__port = 4444
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

    def get_client(self, message):
        """
        gets the client from the message sent and sends the message to the
        client
        """
        x = message.find('whisper: ')
        if x == -1:
            logging.debug('invalid format')
        y = message.find(':', 9)
        client_name = message[9:y]
        client_message = message[y+2:]
        self.__clients[client_name].writer.write(bytes(client_message))

    async def converse(self, person):
        """
        does the conversation for the client
        :param person: named tuple that holds the name, reader, and writer
        """
        while True:
            client_shake = await person.reader.readexactly(1)

            if client_shake[0] == MessageType.MESSAGE.value:
                logging.debug("server has received type message")
                # make sure to get all messages.
                message = await person.reader.read(4096)
                for p in self.__clients:
                    self.__clients[p].writer.write(bytes([MessageType.MESSAGE.value, message]))

            elif client_shake[0] == MessageType.WHISPER.value:
                logging.debug("server has received type whisper")
                message = await person.reader.read(4096)
                decoded_message = bytes.decode(message)
                self.get_client(decoded_message)

            elif client_shake[0] == MessageType.SHOUT.value:
                pass

    async def __client_handler(self, reader, writer):
        """
        handle new clients
        :param reader: reader for the client
        :param writer: writer for the client
        """
        logging.debug("add client to the dictionary")
        while True:
            client_shake = await reader.readexactly(1)
            logging.debug("client sent %s", client_shake)
            if client_shake[0] != MessageType.ON_CONNECT.value:
                logging.debug("Client sent something wrong, killing client")
                self.kill_client(writer)
            client_name = reader.read(4096)
            # check if client name already used
            if client_name in self.__clients.keys():
                logging.debug("asking for a different name")
                writer.write(bytes([MessageType.RESEND_NAME.value]))
            else:
                logging.debug("%s has connected", client_name)
                new_client = Person(name=client_name, reader=reader, writer=writer)
                self.__clients[client_name] = new_client
                await self.converse(new_client)

    def start_server(self):
        logging.debug("starting server")

        loop = asyncio.get_event_loop()
        server_loop = asyncio.start_server(self.__client_handler, host=self.__host, port=self.__port)
        server = loop.run_until_complete(server_loop)

        logging.debug("Serving on %s", (server.sockets[0].getsockname()))

        try:
            loop.run_forever()
        except KeyboardInterrupt:
            pass
        finally:
            server.close()
            loop.run_until_complete(server.wait_closed())
            loop.close()

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    server = Server()
    server.start_server()