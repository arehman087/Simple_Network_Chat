"""
This module defines the ProtoServer class.
"""

import logging
import pickle
import select
import socket
import queue


class Server(object):
    """Defines a client interface meant to interact with Proto Clients.
    This class contains code for connecting to and interacting with the client
    interfaces.
    """

    def __init__(self, ip, port):
        """
        Initializes this ProtoServer interface, and creates a server with the
        specified IP and port number.
        Args:
            ip (str): The IP address of the server.
            port (int): The port number of the server.
        Raises:
            socket.error: If an error occurs while creating the socket for the
                server.
        """

        # Create a socket and start listening process
        self.__address = (ip, port)
        self.__server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.__server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.__server_sock.bind(self.__address)
        self.__server_sock.setblocking(0)
        self.__server_sock.listen(5)

        # Create an empty map of each client's address to its connection
        self.__clients = {}

        # Is the main loop running?
        self.running = False

        # Dictionary which maps a client address to the send/recv message queue
        self.__send_queue = {}
        self.__recv_queue = {}

        logging.info("server connection started on " + str(self.__address))

    def __del__(self):
        """
        Closes the server socket.
        """

        self.__server_sock.close()
        logging.info("server connection closed on " + str(self.__address))

    @property
    def address(self):
        """(): Represents the IP address and port number tuple."""
        return tuple(self.__address)

    @property
    def clients(self):
        """(): Represents the map of client addresses to client connections."""
        return dict(self.__clients)

    def main_loop(self, on_connect=None, on_disconnect=None, on_recv=None):
        """
        Main loop for the server interface. Continually checks for new
        connections.
        Args:
            on_connect (function): The function to be called when a new
                connection is established. This function should take in two
                parameters, them being the client address and the client
                connection.
            on_disconnect (function): The function to be called when some
                client disconnects, either because the connection ends or due
                to some exception. This function should take in one parameter,
                that being the client address.
            on_recv (function): The function to be called when some client
                sends data and it is received by the server. This function
                should take in two parameters, them being the client address
                and the data received.
        """

        # Socket Connections which can be read from and be written to.
        # The socket of this server is included in the readable because a
        # readable server socket can accept connections.
        readable = [self.__server_sock]
        writeable = []

        # Start the server, keep it running until some external thread modifies
        # the running handle.
        self.running = True
        while self.running:
            # Select the readable, writeable, and exceptional connections.
            # Since the self.running handle may change its value while the
            # select function is blocking, use a small timeout so that the
            # handle's value may be rechecked.
            sel_r, sel_w, sel_e = select.select(readable, writeable, readable,
                                                0.01)

            # For each socket in the selected readable connections
            for sock in sel_r:
                # If the readable socket is the socket of this server, then the
                # server has a new connection which it can accept.
                if sock == self.__server_sock:
                    addr, conn = self.__socket_connect(sock)

                    readable.append(conn)
                    writeable.append(conn)

                    if on_connect is not None:
                        on_connect(addr, conn)
                # If the readable socket is a client of this server, then check
                # if we can receive any information from the client.
                else:
                    client_data = sock.recv(4096)
                    client_address = sock.getpeername()

                    # If we did not receive anything from the client, then it
                    # has disconnected from the server.
                    if not client_data:
                        # Remove the socket from readable/writable lists. Also
                        # remove it from the selected writable list so that we
                        # don't try to write to the closed connection.
                        readable.remove(sock)
                        writeable.remove(sock)
                        sel_w.remove(sock)

                        self.__socket_disconnect(sock)

                        if on_disconnect is not None:
                            on_disconnect(client_address)
                    # If we did receive something from the client, then we can
                    # process the data received.
                    else:
                        self.__recv_queue[client_address].put(client_data)
                        logging.info("received message " + str(client_data) +
                                     " from " + str(client_address) + ".")

                        if on_recv is not None:
                            on_recv(client_address, pickle.loads(client_data))

            # For each socket in the selected writeable connections
            for sock in sel_w:
                # Get the messages which will be sent to the socket
                client_address = sock.getpeername()
                messages = self.__send_queue[client_address]

                # Go through each message in the queue and send it to the
                # socket.
                while not messages.empty():
                    msg = messages.get()
                    sock.send(msg)

                    logging.info("sent message " + str(msg) + " to " +
                                 str(client_address) + ".")

            # For each socket in the selected exceptional connections
            for sock in sel_e:
                # Get the socket peer name
                client_address = sock.getpeername()

                # Remove the socket connection, since it has encountered some
                # sort of error.
                if sock in readable:
                    readable.remove(sock)
                if sock in writeable:
                    writeable.remove(sock)
                del self.__clients[client_address]
                del self.__recv_queue[client_address]
                del self.__send_queue[client_address]

                # Call the on_disconnect function, if one is provided
                if on_disconnect is not None:
                    on_disconnect(client_address)

                logging.error(str(client_address) + " encountered some error.")

                sock.close()

    def recv_data(self, addr):
        """
        Dumps the contents of the receive queue of the specified client to a
        list and returns the list. No data is actually received by this method,
        it only dumps what has already been received by the main loop. The
        receive queue is automatically emptied by this method, so that
        previously received messages do not reappear.
        Args:
            addr (tuple): The tuple of the IP address and port number of the
                client. An assertion checks that this is a currently connected
                client.
        Returns:
            The list containing all of the data received from the specified
            address, since the last time this method was called for that
            address. The data inside of the list is unpickled.
        """

        assert addr in self.__clients
        ret = []

        while not self.__recv_queue[addr].empty():
            msg = self.__recv_queue[addr].get()
            msg = pickle.loads(msg)
            ret.append(msg)

        return ret

    def send_data(self, addr, data):
        """
        Adds the specified data to the send queue of the specified client. The
        data is not sent by this method, it is merely added to the queue for
        the client, and it should, ideally, send the data on the next iteration
        of the main loop.
        Args:
            addr (tuple): The tuple of the IP address and port number of the
                client. An assertion checks that this is a currently connected
                client.
            data: The data to be sent to the client. This data is automatically
                pickled before being sent.
        """

        assert addr in self.__clients

        pickled_data = pickle.dumps(data)
        self.__send_queue[addr].put(pickled_data)

    def __socket_connect(self, sock):
        """
        Creates a new connection with the specified client socket. The client
        connection is accepted, and is stored into this instance's clients
        list. Send and receive queues are allocated for the client's address.
        Assertions check that no connection has been established with the
        specified socket yet.
        Args:
            sock (socket): The socket with which a connection is to be
                established.
        Returns:
            The client address and client connection tuple.
        """

        # Accept the connection
        client_connection, client_address = sock.accept()

        # Assert the connection is unique, and has not yet been added to this
        # server.
        assert client_address not in self.__clients
        assert client_address not in self.__send_queue
        assert client_address not in self.__recv_queue

        # Store the client connection, and allocate queues which will store
        # data received from the client or data waiting to be sent to the
        # client.
        self.__clients[client_address] = client_connection
        self.__recv_queue[client_address] = queue.Queue()
        self.__send_queue[client_address] = queue.Queue()

        logging.info("connection opened with " + str(client_address) + ".")
        return client_address, client_connection

    def __socket_disconnect(self, sock):
        """
        Closes the connection with the specified client socket. The client's
        address and connection are removed from this instance's clients list.
        Send and receive queues are deallocated for the client's address.
        Assertions check that the connection between the client and this server
        is currently active.
        Args:
            sock (socket): The socket with which a connection is to be closed.
        """

        client_address = sock.getpeername()

        # Assert the connection exists
        assert client_address in self.__clients
        assert client_address in self.__send_queue
        assert client_address in self.__recv_queue

        # Log a warning if there is some recv/send data left over from the
        # connection that is about to be deleted.
        if not self.__recv_queue[client_address].empty():
            logging.warning("connection with " + str(client_address) +
                            " will be closed but receive queue is not empty.")
        if not self.__send_queue[client_address].empty():
            logging.warning("connection with " + str(client_address) +
                            " will be closed but send queue is not empty.")

        # Remove the connection, deallocate recv/send queues
        del self.__recv_queue[client_address]
        del self.__send_queue[client_address]
        del self.__clients[client_address]

        # Close the socket connection
        logging.info("connection closed with " + str(client_address) + ".")
        sock.close()


# If this is being used as an executable for some reason, just create the
# server wait indefinitely.
if __name__ == "__main__":
    logging.getLogger().setLevel(logging.INFO)

    server = Server("127.0.0.1", 8080)
    try:
        server.main_loop()
    finally:
        del server
