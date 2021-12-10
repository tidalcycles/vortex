import tkinter as tk
import tkinter.font
from tkinter import ttk

from py_vortex.stream import vortex_dsl


class App(tk.Tk):
    def __init__(self, vortex_module):
        super().__init__()

        self._vortex_module = vortex_module

        # Root window
        self.title("Vortex")
        self.style = ttk.Style(self)

        scrollbar = tk.Scrollbar(self)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.document = tk.Text(self, yscrollcommand=scrollbar.set, padx=5, pady=5)
        self.document.pack(expand=True, fill=tk.BOTH)

        font = tkinter.font.Font(family="monospace", size=14)
        self.document.configure(
            font=font,
            blockcursor=True,
            insertbackground="white",
            bg="black",
            fg="white",
        )

        scrollbar.config(command=self.document.yview)

        self.document.bind("<Control-Return>", self.evaluate_block)
        # self.bind_all("<Escape>", lambda e: self.destroy())

        self.document.focus()

    def evaluate_block(self, event=None):
        print("TODO: Evaluate code")
        code = "hush()"
        print(f"Eval: '{code}'")
        exec(code, vars(self._vortex_module))
        return "break"


def start_gui():
    with vortex_dsl() as module:
        app = App(vortex_module=module)
        app.mainloop()
