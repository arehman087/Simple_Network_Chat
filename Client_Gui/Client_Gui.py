import logging
import tkinter as tk
import Client.Client as C

LARGE_FONT = ('Verdana', 12)


class ClientGui(tk.Tk):
    """
    GUI for the client side of the network Chat.
    """

    def __init__(self, *args, **kwargs):
        """
        initializes the gui
        """
        tk.Tk.__init__(self, *args, **kwargs)
        container = tk.Frame(self)

        container.pack(side='top', fill='both', expand=True)

        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        self.frame = {}

        frame = StartPage(container, self)

        self.frame[StartPage] = frame

        frame.grid(row=0, column=0, sticky='nsew')
        self.show_frame(StartPage)

    def show_frame(self, cont):

        frame = self.frame[cont]
        frame.tkraise()


class StartPage(tk.Frame):

    def __init__(self, parent, cont):
        tk.Frame.__init__(self, parent)
        label = tk.Label(self, text='Start Page', font=LARGE_FONT)
        label.pack(pady=10, padx=10)


def main():
    client = ClientGui()
    client.mainloop()


if __name__ == '__main__':
    main()
