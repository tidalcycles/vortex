from vortex import *
from vortex.stream import LinkClock, SuperDirtStream

_default_clock = LinkClock(bpm=120)
_streams = {}


def p(key, pattern):
    if key not in _streams:
        stream = SuperDirtStream()
        _default_clock.subscribe(stream)
        _streams[key] = stream
    _streams[key].pattern = pattern
    return pattern


def hush():
    for stream in _streams.values():
        stream.pattern = silence
        _default_clock.unsubscribe(stream)
    _streams.clear()
