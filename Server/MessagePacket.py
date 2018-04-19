"""
    MessagePacket.py: creates an object for the messages that will be used sent
     to the users
"""


class MessagePacket(object):
    """
    creates an object that will hold different messages
    """

    def __init__(self, message, message_type, client_name):
        """
        initializes an object that will hold the message
        :param message: The message that will be sent
        :param message_type: Type of message; regular, whisper, shout
        :param client_name: name of the client if any
        """
        self.__message = message
        self.__message_type = message_type
        self.__client_name = client_name

    def get_message(self):
        return self.__message

    def get_message_type(self):
        return self.__message_type

    def get_client_name(self):
        return self.__client_name
