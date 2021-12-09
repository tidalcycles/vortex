from IPython.terminal.embed import InteractiveShellEmbed

from py_vortex import *
from py_vortex.stream import LinkClock, SuperDirtStream
from py_vortex import __version__


def start_repl(*kwargs):
    # Every binding defined here will be available on the REPL...
    default_clock = LinkClock(bpm=120)
    default_clock.start()

    # Define a few useful functions...
    _patterns = {}

    def p(key, pattern):
        if key not in _patterns:
            stream = SuperDirtStream(*kwargs)
            default_clock.subscribe(stream)
            _patterns[key] = stream
        _patterns[key].pattern = pattern
        return pattern

    # Start the interactive shell
    ipshell = InteractiveShellEmbed(banner1=f"Vortex {__version__}")
    ipshell()

    default_clock.stop()
