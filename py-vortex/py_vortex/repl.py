from IPython.terminal.embed import InteractiveShellEmbed

from py_vortex import *
from py_vortex import __version__


def start_repl():
    # Every binding defined here will be available on the REPL...
    foo = "bar"

    ipshell = InteractiveShellEmbed(banner1=f"Vortex {__version__}")
    ipshell()
