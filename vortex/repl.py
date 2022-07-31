from IPython.terminal.embed import InteractiveShellEmbed

from vortex import *
from vortex import __version__


def start_repl(*kwargs):
    """Start the interactive shell inside a Vortex environment"""
    with vortex_dsl() as module:
        ipshell = InteractiveShellEmbed(banner1=f"Vortex REPL, version {__version__}")
        ipshell(module=module)
