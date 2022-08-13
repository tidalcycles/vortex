from vortex import *
from vortex.stream import LinkClock, SuperDirtStream

_default_clock = LinkClock(bpm=120)
_streams = {}


def p(key):
    if key not in _streams:
        stream = SuperDirtStream(name=key)
        _default_clock.subscribe(stream)
        _streams[key] = stream
    return _streams[key]


def hush():
    for stream in _streams.values():
        stream.pattern = silence
        _default_clock.unsubscribe(stream)
    _streams.clear()
