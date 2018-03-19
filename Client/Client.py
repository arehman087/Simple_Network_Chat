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
        x = input('What is your name?')
        self.__writer.write(bytes([MessageType.ON_CONNECT.value, MessageType.ON_CONNECT.value]))
        self.__writer.write(pickle.dumps(x))

    def send_to_server(self, message, mess_type):
        # send handshake
        self.__writer.write(bytes([mess_type, mess_type]))
        self.__writer.write(pickle.dumps(message))
        return

    async def receive_from_server(self):
        message = pickle.loads(await self.__reader.read(4096))
        print(message)
        return

    async def converse(self):
        while True:
            x = input('message: ')
            chk = x.find('whisper: ', 0, len('whisper: ')+2)
            chk2 = x.find('client: ', len('whisper: '))
            chk3 = x.find('message: ',len('whisper: ')+len('client: '))
            logging.debug("chk1 = %d, chk2 = %d, chk3 = %d", chk, chk2, chk3)

            if chk == -1 and chk2 == -1 and chk3 == -1:
                self.send_to_server(x, MessageType.MESSAGE.value)
            else:
                self.send_to_server(x, MessageType.WHISPER.value)

            await self.receive_from_server()


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
    await client.converse()


def main():
    loop = asyncio.get_event_loop()
    loop.run_until_complete(cl_functions(loop))


if __name__ == '__main__':
    main()
