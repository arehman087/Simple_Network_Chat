import asyncio
import enum
import logging
import pickle


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


class Client(object):
    """
    creates a client that will recieve messages
    """

    def __init__(self, reader, writer, loop):
        self.__reader = reader
        self.__writer = writer
        self.__loop = loop

    def send_name(self):
        ######NEED TO FIX
        x = input('What is your name?')
        self.__writer.write(bytes([0, 0]))

        self.__writer.write(pickle.dumps(x))

    def converse(self):
        pass


async def cl_functions(loop):
    try:
        reader, writer = await asyncio.open_connection(host='localHost', port=4444, loop=loop)
    except ConnectionResetError:
        logging.error("ConnectionResetError")
        return
    except asyncio.streams.IncompleteReadError:
        logging.error("asyncio.streams.IncompleteReadError")
        return
    except OSError:
        logging.error("OSError")
        return

    client = Client(reader, writer, loop)
    client.send_name()


def main():
    loop = asyncio.get_event_loop()
    loop.run_until_complete(cl_functions(loop))


if __name__ == '__main__':
    main()

