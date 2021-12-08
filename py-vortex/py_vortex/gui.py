import tkinter as tk
from tkinter import ttk


DEFAULT_THEME_NAME = "clam"


class App(tk.Tk):
    def __init__(self):
        super().__init__()

        # Root window
        self.title("Vortex")
        self.geometry("400x300")
        self.style = ttk.Style(self)

        # Select default theme (if available)
        theme_names = self.style.theme_names()
        print(theme_names)
        if DEFAULT_THEME_NAME in theme_names:
            self.style.theme_use(DEFAULT_THEME_NAME)

        scrollbar = tk.Scrollbar(self)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        document = tk.Text(self, yscrollcommand=scrollbar.set)
        document.pack(fill=tk.BOTH)

        scrollbar.config(command=document.yview)


def start_gui():
    app = App()
    app.mainloop()
