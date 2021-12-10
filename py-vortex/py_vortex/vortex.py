"""
Experiment: porting Tidalcycles to Python 3.x.
"""

from __future__ import annotations
from fractions import Fraction
# from dataclasses import dataclass
# from typing import Any, Union
from math import floor
import logging
from functools import partial

logging.basicConfig(level=logging.INFO)

# -> utils.py?

# flatten list of lists
def concat(t) -> list:
    logging.debug(f"CONCAT: list {t}")
    return [item for sublist in t for item in sublist]

def remove_none(t) -> list:
    logging.debug(f"remove_none: list {t}")
    return filter(lambda x: x != None, t)

def id(x):
    """Identity function"""
    return x

def partial_function(f):
    def wrapper(*args):
        try:
            return f(*args)
        except (TypeError) as e:
            return partial(f, *args)
    return wrapper

# -> pattern.py?

class Time(Fraction):
    """Fraction is immutable so new instead of init"""
    def __new__(cls, *args, **kwargs) -> Time:
        self = super(Time, cls).__new__(cls, *args, **kwargs)
        return self

    def sam(self):
        logging.debug(f"SAM: {self}")
        return floor(self)

    def nextSam(self):
        logging.debug(f"NEXT SAM: {self}")
        return self.sam() + 1

    def wholeCycle(self):
        logging.debug(f"in wholeCycle {self.sam()} {self.nextSam()}")
        return TimeSpan(self.sam(), self.nextSam())


class TimeSpan(object):

    """ TimeSpan is (Time, Time) """
    def __init__(self, begin: Time, end: Time):
        self.begin = Time(begin)
        self.end = Time(end)
        logging.debug(f"TIMESPAN: __init__ {self}")

    def span_cycles(self) -> list:
        logging.debug(f"TIMESPAN: span_cycles {self}")
        """ Splits a timespan at cycle boundaries """

        # TODO - a loop rather than recursion might be more efficient in
        # python?
        if self.end <= self.begin:
            # no cycles in the timespan..
            return []
        elif self.begin.sam() == self.end.sam():
            # Timespan is all within one cycle
            return [self]
        else:
            nextB = self.begin.nextSam()
            spans = TimeSpan(nextB, self.end).span_cycles()
            spans.insert(0, TimeSpan(self.begin, nextB))
            return spans

    def with_time(self, f) -> TimeSpan:
        """ Applies given function to both the begin and end value of the timespan"""
        return TimeSpan(f(self.begin), f(self.end))

    def sect(self, other):
        """ Intersection of two timespans """
        logging.debug(f"TIMESPAN: sect {self} {other}")
        return TimeSpan(max(self.begin, other.begin), min(self.end, other.end))

    def maybe_sect(a, b):
        """ Like sect, but returns None if they don't intersect """
        s = a.sect(b)
        if s.end <= s.begin:
            return None
        else:
            return s

    def __repr__(self) -> str:
        return ("TimeSpan(" + self.begin.__repr__() + ", "
                +  self.end.__repr__() + ")")


class Event:

    """
    Event class, representing a value active during the timespan
    'part'. This might be a fragment of an event, in which case the
    timespan will be smaller than the 'whole' timespan, otherwise they
    will be the same. The 'part' must never extend outside of the
    'whole'. If the event represents a continuously changing value
    then the whole will be returned as None, in which case the given
    value will have been sampled from the point halfway between the
    start and end of the 'part' timespan.

    """

    def __init__(self, whole, part, value):
        self.whole = whole
        self.part = part
        self.value = value
        logging.debug(f"EVENT: __init__ {self}")

    def with_span(self, f) -> Event:
        """ Returns a new event with the function f applies to the event timespan. """
        whole = None if not self.whole else f(self.whole)
        return Event(whole, f(self.part), self.value)

    def with_value(self, f) -> Event:
        """ Returns a new event with the function f applies to the event value. """
        return Event(self.whole, self.part, f(self.value))

    def has_onset(self) -> bool:
        return self.whole and self.whole.begin == self.part.begin
    
    def __repr__(self) -> str:
        return ("Event(" + self.whole.__repr__()
                + ", "
                + self.part.__repr__()
                + ", "
                + self.value.__repr__() + ")")

class Pattern:

    """
    Pattern class, representing discrete and continuous events as a
    function of time.
    """

    def __init__(self, query):
        self.query = query
        logging.debug(f"PATTERN: __init__ {self} {query}")

    def split_queries(self) -> Pattern:
        """ Splits queries at cycle boundaries. This makes some calculations 
        easier to express, as all events are then constrained to happen within 
        a cycle. """
        def query(span) -> list:
            return concat([self.query(subspan) for subspan in span.span_cycles()])

        return self.__class__(query)

    def with_query_span(self, f) -> Pattern:
        """ Returns a new pattern, with the function applied to the timespan of the query. """
        logging.debug(f"PATTERN: with_query_span {self} {self.query} {f}")
        return self.__class__(lambda span: self.query(f(span)))

    def with_query_time(self, f) -> Pattern:
        """ Returns a new pattern, with the function applied to both the begin
        and end of the the query timespan. """
        return self.__class__(lambda span: self.query(span.with_time(f)))

    def with_event_span(self, f) -> Pattern:
        """ Returns a new pattern, with the function applied to each event
        timespan. """
        def query(span):
            return [event.with_span(f) for event in self.query(span)]
        return self.__class__(query)

    def with_event_time(self, f) -> Pattern:
        """ Returns a new pattern, with the function applied to both the begin
        and end of each event timespan.
        """
        return self.with_event_span(lambda span: span.with_time(f))

    def with_value(self, f):
        """Returns a new pattern, with the function applied to the value of
        each event. It has the alias 'fmap'.

        """
        def query(span):
            return [event.with_value(f) for event in self.query(span)]
        return self.__class__(query)

    # alias
    fmap = with_value

    def onsets_only(self) -> Pattern:
        """Returns a new pattern that will only return events where the start
        of the 'whole' timespan matches the start of the 'part'
        timespan, i.e. the events that include their 'onset'.

        """
        return self.__class__(lambda span: list(filter(Event.has_onset, self.query(span))))
    
    def _app_whole(self, wf, patv):
        """
        Assumes self is a pattern of functions, and given a function to
        resolve wholes, applies a given pattern of values to that
        pattern of functions.

        """
        logging.debug(f"PATTERN: _app_whole {self} {self.query} {wf} {patv}")
        patf = self
        def query(span):
            logging.debug(f"PATTERN: _app_whole query {wf} {patf} {span}")
            efs = patf.query(span)
            evs = patv.query(span)
            logging.debug(f"PATTERN: _app_whole query {efs} {evs}")
            def apply(ef, ev):
                logging.debug(f"PATTERN: _app_whole apply {ef} {ev}")
                s = ef.part.maybe_sect(ev.part)
                if s == None:
                    return None
                return Event(wf(ef.whole, ev.whole), s, ef.value(ev.value))
            return concat([remove_none([apply(ef, ev) for ev in evs])
                           for ef in efs
                          ]
                         )
        return self.__class__(query)

    def app(self, patv):
        logging.debug(f"PATTERN: app <*> {self} {self.query} {patv}")
        """ Tidal's <*> """
        def wholef(a, b):
            if a == None or b == None:
                return None
            return a.sect(b)

        logging.debug(f"PATTERN: app {wholef} {patv}")
        return self._app_whole(wholef, patv)

    def appl(self, patv):
        """ Tidal's <* """
        logging.debug(f"PATTERN: appl <* {self} {self.query} {patv}")
        def wholef(a, b):
            if a == None or b == None:
                return None
            return a

        logging.debug(f"PATTERN: appl {wholef} {patv}")
        return self._app_whole(wholef, patv)

    def appr(self, patv):
        """ Tidal's *> """
        logging.debug(f"PATTERN: appr *> {self} {self.query} {patv}")
        def wholef(a, b):
            if a == None or b == None:
                return None
            return b

        logging.debug(f"PATTERN: appr {wholef} {patv}")
        return self._app_whole(wholef, patv)

    def __add__(self, other):
        return self.fmap(lambda x: lambda y: x + y).app(other)

    def __radd__(self, other):
        return self.__add__(other)
    
    def __sub__(self, other):
        return self.fmap(lambda x: lambda y: x - y).app(other)

    def __rsub__(self, other):
        if not (other.__class__ == Pattern):
            return self - self.__class__(other)
        raise ValueError # or return NotImplemented?

    # TODO - make a ControlPattern subclass for patterns of dictionaries?
    def __rshift__(self, other):
        """Overrides the >> operator to support combining patterns of
        dictionaries (AKA 'control patterns'). Produces the union of
        two patterns of dictionaries, with values from right replacing
        any with the same name from the left

        """
        return self.fmap(lambda x: lambda y: {**x, **y}).app(other)

    def __lshift__(self, other):
        """Like >>, but matching values from left replace those on the right"""
        return self.fmap(lambda x: lambda y: {**y, **x}).app(other)
    
    def _bind_whole(self, chooseWhole, f):
        patv = self
        def query(span):
            def withWhole(a, b):
                return Event(chooseWhole(a.whole, b.whole), b.part,
                             b.value
                            )
            def match(a):
                return [withWhole(a, b) for b in f(a.value).query(a.part)]

            return concat([match(ev) for ev in patv.query(span)])
        return self.__class__(query)

    def bind(self, f):
        logging.debug(f"PATTERN: bind {self} {f}")
        def wholef(a, b):
            logging.debug(f"PATTERN: bind wholef {a} {b}")
            if a == None or b == None:
                return None
            return a.sect(b)
        return self._bind_whole(wholef, f)

    def join(self):
        """Flattens a pattern of patterns into a pattern, where wholes are
        the intersection of matched inner and outer events."""
        return self.bind(id)
    
    def inner_bind(self, f):
        logging.debug(f"PATTERN: inner_bind {self} {f}")
        def wholef(a, b):
            logging.debug(f"PATTERN: inner_bind wholef {a} {b}")
            if a == None or b == None:
                return None
            return a
        return self._bind_whole(wholef, f)

    def inner_join(self):
        """Flattens a pattern of patterns into a pattern, where wholes are
        taken from inner events."""
        return self.inner_bind(id)
    
    def outer_bind(self, f):
        logging.debug(f"PATTERN: outer_bind {self} {f}")
        def wholef(a, b):
            logging.debug(f"PATTERN: outer_bind wholef {a} {b}")
            if a == None or b == None:
                return None
            return b
        return self._bind_whole(wholef, f)

    def outer_join(self):
        """Flattens a pattern of patterns into a pattern, where wholes are
        taken from outer events."""
        return self.outer_bind(id)
    
    def _fast(self, factor) -> Pattern:
        """ Speeds up a pattern by the given factor"""
        logging.debug(f"PATTERN: fast {self} {factor}")
        fastQuery = self.with_query_time(lambda t: t*factor)
        fastEvents = fastQuery.with_event_time(lambda t: t/factor)
        logging.debug(f"PATTERN: fast fastEvents {fastEvents}")
        return fastEvents

    def every(self, n, f):
        return self.slowcat([f(self)] + ([self] * (n-1)))

    def fast(self, pfactor) -> Pattern:
        """ Speeds up a pattern using the given pattern of factors"""
        logging.debug(f"PATTERN: fast {self} {pfactor}")
        if not isinstance(pfactor, Pattern):
            # Not patterned, run normally
            return self._fast(pfactor)
        return pfactor.fmap(lambda factor: self._fast(factor)).outer_join()
        
    def slow(self, factor) -> Pattern:
        logging.debug(f"PATTERN: slow {self} {factor}")
        """ Slow slows down a pattern """
        return self._fast(1/factor)

    def early(self, offset) -> Pattern:
        """ Equivalent of Tidal's <~ operator """
        logging.debug(f"PATTERN: early {self} {offset}")
        return self.with_query_time(
                lambda t: t+offset).with_event_time(lambda t: t-offset)

    def late(self, offset) -> Pattern:
        """ Equivalent of Tidal's ~> operator """
        logging.debug(f"PATTERN: late {self} {offset}")
        return self.early(0-offset)

    def first_cycle(self):
        logging.debug(f"PATTERN: first_cycle {self}")
        return self.query(TimeSpan(Time(0), Time(1)))

    @classmethod
    def silence(cls):
        cls(lambda _: [])

    @classmethod
    def checkType(cls, value) -> bool:
        return True
    
    @classmethod
    def pure(cls, v) -> Pattern:
        """ Returns a pattern that repeats the given value once per cycle """
        if not cls.checkType(v):
            raise ValueError
        
        def query(span):
            return [Event(Time(subspan.begin).wholeCycle(), subspan, v)
                    for subspan in span.span_cycles()
            ]
        return cls(query)
    
    @classmethod
    def slowcat(cls, pats) -> Pattern:
        """Concatenation: combines a list of patterns, switching between them
        successively, one per cycle.
        (currently behaves slightly differently from Tidal)

        """
        def query(span):
            pat = pats[floor(span.begin) % len(pats)]
            return pat.query(span)
        return cls(query).split_queries()

    @classmethod
    def fastcat(cls,pats) -> Pattern:
        """Concatenation: as with slowcat, but squashes a cycle from each
        pattern into one cycle"""
        return cls.slowcat(pats)._fast(len(pats))

    # alias
    cat = fastcat

    @classmethod
    def stack(cls, pats) -> Pattern:
        """ Pile up patterns """
        def query(span):
            return concat([pat.query(span) for pat in pats])
        return cls(query)

    @classmethod
    def _sequence(cls,xs):
        if type(xs) == list:
            return (cls.fastcat([cls.sequence(x) for x in xs]), len(xs))
        elif isinstance(xs, Pattern):
            return (xs,1)
        else:
            return (cls.pure(xs), 1)

    @classmethod
    def sequence(cls, xs):
        return cls._sequence(xs)[0]

    @classmethod
    def polyrhythm(cls, xs, steps=None):
        seqs = [cls._sequence(x) for x in xs]
        if len(seqs) == 0:
            return cls.silence
        if not steps:
            steps = seqs[0][1]
        pats = []
        for seq in seqs:
            if seq[1] == 0:
                next
            if steps == seq[1]:
                pats.append(seq[0])
            else:
                pats.append(seq[0]._fast(Time(steps)/Time(seq[1])))
        return cls.stack(pats)

    # alias
    @classmethod
    def pr(cls, xs, steps=None):
        return cls.polyrhythm(xs, steps)

    @classmethod
    def polymeter(cls, xs):
        seqs = [cls.sequence(x) for x in xs]

        if len(seqs) == 0:
            return cls.silence

        return cls.stack(seqs)

    @classmethod
    def pm(cls, xs):
        return cls.polymeter(xs)

class S(Pattern):
    @classmethod
    def checkType(cls, value) -> bool:
        return isinstance(value, str)


class F(Pattern):
    @classmethod
    def checkType(cls, value) -> bool:
        return isinstance(value, float) or isinstance(value, int)


class I(Pattern):
    @classmethod
    def checkType(cls, value) -> bool:
        return isinstance(value, int)


class T(Pattern):
    @classmethod
    def checkType(cls, value) -> bool:
        return isinstance(value, Time)

class Control(Pattern):
    @classmethod
    def checkType(cls, value) -> Bool:
        return isinstance(value, dict)

# -> partials.py?

# Hippie partial application..

@partial_function
def fast(a, b):
    return b.fast(a)

@partial_function
def slow(a, b):
    return b.slow(a)

@partial_function
def early(a, b):
    return b.early(a)

@partial_function
def late(a, b):
    return b.late(a)

# Hippie type inference..
    
def guess_value_class(v):
    if isinstance(v, int):
        return I
    if isinstance(v, str):
        return S
    if isinstance(v, float):
        return F
    if isinstance(v, Time):
        return T
    if isinstance(v, dict):
        return Control
    return Pattern

    
def silence():
    return Pattern.silence()

def pure(v):
    return guess_value_class(v).pure(v)

def slowcat(pats) -> Pattern:
    if len(pats) == 0:
        return Pattern.silence()
    return pats[0].__class__.slowcat(pats)

def fastcat(pats) -> Pattern:
    if len(pats) == 0:
        return Pattern.silence()
    return pats[0].__class__.fastcat(pats)

cat = fastcat

def stack(pats) -> Pattern:
    if len(pats) == 0:
        return Pattern.silence()
    return pats[0].__class__.stack(pats)

def _sequence(pats):
    if len(pats) == 0:
        return Pattern.silence()
    return pats[0].__class__._sequence(pats)

def sequence(xs):
    if len(xs) == 0:
        return Pattern.silence()
    return xs[0].__class__.sequence(xs)

def polyrhythm(xs, steps=None):
    if len(xs) == 0:
        return Pattern.silence()
    if isinstance(xs[0], Pattern):
        cls = xs[0].__class__
    else:
        cls = guess_value_class(xs[0])
    return cls.polyrhythm(xs, steps)

pr = polyrhythm

def polymeter(xs):
    if len(xs) == 0:
        return Pattern.silence()
    if isinstance(xs[0], Pattern):
        cls = xs[0].__class__
    else:
        cls = guess_value_class(xs[0])
    return cls.polymeter(xs)

pm = polyrhythm

# -> control.py?

# Create functions for making control patterns (patterns of dictionaries)
controls = [
    (S, "S", ["s", "vowel"]),
    (F, "F", ["n", "note", "gain", "pan", "speed", "room", "size"])
]

# This had to go in its own function, for weird scoping reasons..
def setter(cls, clsname, name):
    setattr(cls, name, lambda pat: Control(pat.fmap(lambda v: {name: v}).query))

for controltype in controls:
    cls = controltype[0]
    clsname = controltype[1]
    for name in controltype[2]:
        setter(cls, clsname, name)
        # Couldn't find a better way of adding functions to __main__ ..
        exec("%s = %s.%s" % (name, clsname, name))

def pattern_pretty_printing(pattern: Pattern, query_span: TimeSpan) -> None:
    """ Better formatting for logging.debuging Tidal Patterns """
    for event in pattern.query(query_span):
        logging.debug(event)

if __name__ == "__main__":
    # Simple patterns
    a = S.pure("hello")
    b = S.pure("world")
    c = S.fastcat([a, b])
    d = S.stack([a, b])

    # logging.debuging the pattern
    logging.debug("\n== TEST PATTERN ==\n")
    logging.debug('Like: "hello world" (over two cycles)')
    pattern_pretty_printing(
        pattern=c,
        query_span=TimeSpan(Time(0), Time(2)))

    # logging.debuging the pattern with fast
    logging.debug("\n== SAME BUT FASTER==\n")
    logging.debug('Like: fast 4 "hello world"')
    pattern_pretty_printing(
        pattern=c._fast(2),
        query_span=TimeSpan(Time(0), Time(1)))

    # logging.debuging the pattern with patterned fast
    logging.debug("\n== PATTERNS OF FAST OF PATTERNS==\n")
    logging.debug('Like: fast "2 4" "hello world"')
    pattern_pretty_printing(
        pattern=c.fast(S.fastcat([F.pure(2), F.pure(4)])),
        query_span=TimeSpan(Time(0), Time(1)))

    # logging.debuging the pattern with stack
    logging.debug("\n== STACK ==\n")
    pattern_pretty_printing(
        pattern=d,
        query_span=TimeSpan(Time(0), Time(1)))

    # logging.debuging the pattern with late
    logging.debug("\n== LATE ==\n")
    pattern_pretty_printing(
        pattern=c.late(0.5),
        query_span=TimeSpan(Time(0), Time(1)))

    # Apply pattern of values to a pattern of functions
    logging.debug("\n== APPLICATIVE ==\n")
    x = F.fastcat([Pattern.pure(lambda x: x + 1), Pattern.pure(lambda x: x + 4)])
    y = F.fastcat([F.pure(3), F.pure(4), F.pure(5)])
    z = x.app(y)
    pattern_pretty_printing(
        pattern=z,
        query_span=TimeSpan(Time(0), Time(1)))

    # Add number patterns together
    logging.debug("\n== ADDITION ==\n")
    numbers = F.fastcat([F.pure(v) for v in [2, 3, 4, 5]])
    more_numbers = F.fastcat([F.pure(10), F.pure(100)])
    pattern_pretty_printing(
        pattern=numbers + more_numbers,
        query_span=TimeSpan(Time(0), Time(1)))

    logging.debug("\n== EMBEDDED SEQUENCES ==\n")
    # sequence([0,1,[2, [3, 4]]]) is the same as "[0 1 [2 [3 4]]]" in mininotation
    pattern_pretty_printing(
        pattern=I.sequence([0, 1, [2, [3, 4]]]),
        query_span=TimeSpan(Time(0), Time(1)))

    logging.debug("\n== Polyrhythm ==\n")
    pattern_pretty_printing(
        pattern=I.polyrhythm([[0, 1, 2, 3], [20, 30]]),
        query_span=TimeSpan(Time(0), Time(1)))

    logging.debug("\n== Polyrhythm with fewer steps ==\n")
    pattern_pretty_printing(
        pattern=I.polyrhythm([[0, 1, 2, 3], [20, 30]], steps=2),
        query_span=TimeSpan(Time(0), Time(1)))

    logging.debug("\n== Polymeter ==\n")
    pattern_pretty_printing(
        pattern=I.polymeter([[0, 1, 2], [20, 30]]),
        query_span=TimeSpan(Time(0), Time(1)))

    logging.debug("\n== Polymeter with embedded polyrhythm ==\n")
    pattern_pretty_printing(
        pattern=I.pm([I.pr([[100, 200, 300, 400],
                            [0, 1]]),
                      [20, 30]]),
        query_span=TimeSpan(Time(0), Time(1)))

    logging.debug("\n== Every with partially applied 'fast' ==\n")
    pattern_pretty_printing(
        pattern=c.every(3, fast(2)),
        query_span=TimeSpan(Time(0), Time(1)))
