import tkinter as tk
import Client
from Client import Client

LARGE_FONT = ('Verdana', 12)


class ClientGui(tk.Tk):
    """
    GUI for the client side of the network Chat.
    """

    def __init__(self, *args, **kwargs):
        """
        initializes the gui
        """

        # make the connection
        self.client = Client.Client('localHost', 4444)
        self.client.make_connection()

        while True: 
            dialog = Dialog('Enter Name')
            if self.client.send_name(dialog.message) is 1:
                break

        tk.Tk.__init__(self, *args, **kwargs)
        # set weights accordingly for each row and column
        self.resizable(width=False, height=False)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # make the title label
        label = tk.Label(self, text='Network Chat', font=LARGE_FONT)
        label.grid(column=0, row=0, columnspan=2, sticky='EW')

        # make the receiving box
        self.receiver_box = tk.Text(self)
        self.receiver_box.config(state='disabled')
        self.receiver_box.grid(column=0, row=1, columnspan=3,  sticky='EW')
        import threading
        threading.Thread(target=self.r_box).start()
        # make the sending box
        self.send_box = tk.Entry(self)
        self.send_box.grid(column=0, row=2, sticky='EW')

        # make the button for sending
        button1 = tk.Button(self, text="Send", command=self.s_button)
        button1.grid(column=1, row=2, sticky="EW")

        self.tkraise()

    def r_box(self):
        """
        receives messages from other clients
        """
        while True:
            message = self.client.receive_from_server()
            self.receiver_box.config(state='normal')
            self.receiver_box.insert(tk.END, message)
            self.receiver_box.config(state='disabled')

    def s_box(self):
        """
        gets the message that will be sent to the other clients
        """
        message = self.send_box.get()
        self.send_box.delete(0, tk.END)
        return str(message + '\n')

    def s_button(self):
        """
        sends message to the other clients
        """
        self.client.send_to_server(self.s_box(),
                                   Client.MessageType.MESSAGE.value)


class Dialog(tk.Tk):

    def __init__(self, message):
        """
        initializes the dialog box to take in user input to send initial data
        to server
        :param message: message that needs to be displayed
        """
        tk.Tk.__init__(self, message)
        self.e = tk.Entry()
        self.e.pack()

        self.e.focus_set()
        self.message = ''
        self.button = tk.Button(text='OK', width=10, command=self.dialog_get)
        self.button.pack()
        self.mainloop()

    def dialog_get(self):
        """
        Gets the message from the dialog box
        """
        self.message = self.e.get()
        self.destroy()


def main():
    import logging
    logging.basicConfig(level=logging.DEBUG)
    client_gui = ClientGui()
    client_gui.mainloop()


if __name__ == '__main__':
    main()
