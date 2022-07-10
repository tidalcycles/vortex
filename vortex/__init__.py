import contextlib
import importlib
import sys

if sys.version_info[:2] >= (3, 8):
    # TODO: Import directly (no need for conditional) when `python_requires = >= 3.8`
    from importlib.metadata import PackageNotFoundError, version  # pragma: no cover
else:
    from importlib_metadata import PackageNotFoundError, version  # pragma: no cover

try:
    # Change here if project is renamed and does not equal the package name
    dist_name = __name__
    __version__ = version(dist_name)
except PackageNotFoundError:  # pragma: no cover
    __version__ = "unknown"
finally:
    del version, PackageNotFoundError


from .utils import *
from .pattern import *
from .vortex import *
from .control import *


@contextlib.contextmanager
def vortex_dsl():
    """
    Create a Vortex DSL context, with a default LinkClock and some functions for
    managing Streams

    Returns
    -------
    ModuleType
        Vortex DSL module

    """
    # Import DSL module and get variables
    mod = importlib.import_module("vortex.boot")
    locals = vars(mod)

    # Start clock
    clock = locals["_default_clock"]
    clock.start()

    yield mod

    # We're exiting context, so stop clock thread
    clock.stop()
