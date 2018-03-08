import logging
import socket
import pickle


class Client(object):
    """
    creates a client that will recieve messages
    """

    def __init__(self):
        self.__sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.__name = "Abdul"
        self.__sock.connect(('localHost', 4444))

    def converse(self):
        logging.debug("talking to server")

        try:
            message = input('what would you like to send? ')
            pickleled_data = pickle.dumps(message)
            self.__sock.sendall(pickleled_data)

            while True:
                rec_data = self.__sock.recv(4096)
                data = pickle.loads(rec_data)
                print ("server sent: "+ str(data))

                message = input('what would you like to send? ')
                pickleled_data = pickle.dumps(message)
                self.__sock.sendall(pickleled_data)

        except KeyboardInterrupt:
            pass

        finally:
            self.__sock.close()

def main():
    client = Client
    client.converse()

if __name__ == '__main__':
    main()

