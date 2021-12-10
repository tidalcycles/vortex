from IPython.terminal.embed import InteractiveShellEmbed

from py_vortex import *
from py_vortex import __version__


def start_repl(*kwargs):
    """Start the interactive shell inside a Vortex environment"""
    with vortex_dsl() as module:
        ipshell = InteractiveShellEmbed(banner1=f"Vortex {__version__}")
        ipshell(module=module)
