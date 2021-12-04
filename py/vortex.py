"""
Experiment: porting Tidalcycles to Python 3.x.
"""

from __future__ import annotations
from fractions import Fraction
# from dataclasses import dataclass
# from typing import Any, Union
from math import floor
import logging

logging.basicConfig(level=logging.INFO)

# flatten list of lists
def concat(t) -> list:
    logging.debug(f"CONCAT: list {t}")
    return [item for sublist in t for item in sublist]

def removeNone(t) -> list:
    logging.debug(f"REMOVENONE: list {t}")
    return filter(lambda x: x != None, t)

# Identity function
def id(x):
    return x

# Couldn't subclass Fraction to call it "Time" for some strange inheritance
# issue (inheritance of magic methods). Stuck with Fraction for now. Someone
# might know how to properly subclass Fraction.

Time = Fraction # Time is rational
def sam(frac: Time) -> Time:
    logging.debug(f"SAM: {frac}")
    return Time(floor(frac))

def nextSam(frac: Time) -> Time:
    logging.debug(f"NEXT SAM: {frac}")
    return Time(sam(frac) + 1)

def wholeCycle(frac: Time) -> TimeSpan:
    logging.debug(f"in wholeCycle {frac}")
    return TimeSpan(sam(frac), nextSam(frac))


class TimeSpan:

    """ TimeSpan is (Time, Time) """

    def __init__(self, begin: Time, end: Time):
        self.begin = begin
        self.end = end
        logging.debug(f"TIMESPAN: __init__ {self}")

    def spanCycles(self) -> list:
        logging.debug(f"TIMESPAN: spanCycles {self}")
        """ Splits a timespan at cycle boundaries """

        # TODO - make this more imperative

        if self.end <= self.begin:
            # no cycles in the timespan..
            return []
        elif sam(self.begin) == sam(self.end):
            # Timespan is all within one cycle
            logging.debug(f"TIMESPAN: spanCycles sam(begin) == sam(end) {self}")
            return [self]
        else:
            logging.debug(f"TIMESPAN: spanCycles {self}")
            nextB = nextSam(self.begin)
            spans = TimeSpan(nextB, self.end).spanCycles()
            logging.debug(f"before insert {spans}")
            spans.insert(0, TimeSpan(self.begin, nextB))
            logging.debug(f"TIMESPAN: spanCycles {spans}")
            return spans

    def withTime(self, f) -> TimeSpan:
        logging.debug(f"TIMESPAN: withTime {f} {self}")
        return TimeSpan(f(self.begin), f(self.end))

    def sect(self, other):
        """ Intersection of two timespans """
        logging.debug(f"TIMESPAN: sect {self} {other}")
        return TimeSpan(max(self.begin, other.begin), min(self.end, other.end))

    def maybeSect(a, b):
        logging.debug(f"TIMESPAN: maybeSect {a} {b}")
        """ Like sect, but returns None if they don't intersect """
        s = a.sect(b)
        logging.debug(f"TIMESPAN: maybeSect {s}")
        if s.end <= s.begin:
            return None
        else:
            return s

    def __repr__(self) -> str:
        return ("TimeSpan(" + self.begin.__repr__() + ", "
                +  self.end.__repr__() + ")")


class Event:

    """ Event class """

    def __init__(self, whole, part, value):
        self.whole = whole
        self.part = part
        self.value = value
        logging.debug(f"EVENT: __init__ {self}")

    def withSpan(self, f) -> Event:
        whole = None if not self.whole else f(self.whole)
        logging.debug(f"EVENT: withSpan {self} {f}")
        return Event(whole, f(self.part), self.value)

    def withValue(self, f) -> Event:
        logging.debug(f"EVENT: withValue {self} {f}")
        return Event(self.whole, self.part, f(self.value))

    def __repr__(self) -> str:
        return ("Event(" + self.whole.__repr__()
                + ", "
                + self.part.__repr__()
                + ", "
                + self.value.__repr__() + ")")


class Pattern:

    """ Pattern class """

    def __init__(self, query):
        self.query = query
        logging.debug(f"PATTERN: __init__ {self} {query}")

    def splitQueries(self) -> Pattern:
        """ Splits queries at cycle boundaries. Makes some calculations easier
        to express, as everything then happens within a cycle. """
        logging.debug(f"PATTERN: splitQueries {self} {self.query}")

        def query(span) -> list:
            return concat([self.query(subspan) for subspan in span.spanCycles()])

        return Pattern(query)

    def withQuerySpan(self, f) -> Pattern:
        logging.debug(f"PATTERN: withQuerySpan {self} {self.query} {f}")
        return Pattern(lambda span: self.query(f(span)))

    def withQueryTime(self, f) -> Pattern:
        logging.debug(f"PATTERN: withQueryTime {self} {self.query} {f}")
        return Pattern(lambda span: self.query(span.withTime(f)))

    def withEventSpan(self, f) -> Pattern:
        logging.debug(f"PATTERN: withEventSpan {self} {self.query} {f}")
        def query(span):
            return [event.withSpan(f) for event in self.query(span)]
        return Pattern(query)

    def withEventTime(self, f) -> Pattern:
        logging.debug(f"PATTERN: withEventTime {self} {self.query} {f}")
        return self.withEventSpan(lambda span: span.withTime(f))

    def withValue(self, f) -> Pattern:
        logging.debug(f"PATTERN: withValue {self} {self.query} {f}")
        def query(span):
            return [event.withValue(f) for event in self.query(span)]
        return Pattern(query)

    # alias
    fmap = withValue

    def _appWhole(self, wf, patv):
        """
        Assumes self is a pattern of functions, and given a function to
        resolve wholes, applies a given pattern of values to that
        pattern of functions.

        """
        logging.debug(f"PATTERN: _appWhole {self} {self.query} {wf} {patv}")
        patf = self
        def query(span):
            efs = patf.query(span)
            evs = patv.query(span)
            def apply(ef, ev):
                s = ef.part.maybeSect(ev.part)
                if s == None:
                    return None
                return Event(wf(ef.whole, ev.whole), s, ef.value(ev.value))
            return concat([removeNone([apply(ef, ev) for ev in evs])
                           for ef in efs
                          ]
                         )
        return Pattern(query)

    def app(self, patv):
        logging.debug(f"PATTERN: app <*> {self} {self.query} {patv}")
        """ Tidal's <*> """
        def wholef(a, b):
            if a == None or b == None:
                return None
            return a.sect(b)

        logging.debug(f"PATTERN: app {wholef} {patv}")
        return self._appWhole(wholef, patv)

    def appl(self, patv):
        """ Tidal's <* """
        logging.debug(f"PATTERN: appl <* {self} {self.query} {patv}")
        def wholef(a, b):
            if a == None or b == None:
                return None
            return a

        logging.debug(f"PATTERN: appl {wholef} {patv}")
        return self._appWhole(wholef, patv)

    def appr(self, patv):
        """ Tidal's *> """
        logging.debug(f"PATTERN: appr *> {self} {self.query} {patv}")
        def wholef(a, b):
            if a == None or b == None:
                return None
            return b

        logging.debug(f"PATTERN: appr {wholef} {patv}")
        return self._appWhole(wholef, patv)

    def __add__(self, other):
        # If we're passed a non-pattern, turn it into a pattern
        if not (other.__class__ == Pattern):
            other = atom(other)
        return self.fmap(lambda x: lambda y: x + y).app(other)

    def __radd__(self, other):
        return self.__add__(other)
    
    def __sub__(self, other):
        # If we're passed a non-pattern, turn it into a pattern
        if not (other.__class__ == Pattern):
            other = atom(other)
        return self.fmap(lambda x: lambda y: x - y).app(other)

    def __rsub__(self, other):
        if not (other.__class__ == Pattern):
            return self - Pattern(other)
        raise ValueError # or return NotImplemented?
    
    def _bindWhole(self, chooseWhole, f):
        logging.debug(f"PATTERN: _bindwhole *> {self} {chooseWhole} {f}")
        patv = self
        def query(span):
            def withWhole(a, b):
                logging.debug(f"PATTERN: _bindwhole withWhole *> {a} {b}")
                return Event(chooseWhole(a.whole, b.whole), b.part,
                             b.value
                            )
            def match(a):
                logging.debug(f"PATTERN: _bindwhole match *> {a} {b}")
                return [withWhole(a, b) for b in f(a.value).query(a.part)]

            return concat([match(ev) for ev in patv.query(span)])
        return Pattern(query)

    def bind(self, f):
        logging.debug(f"PATTERN: bind {self} {f}")
        def wholef(a, b):
            logging.debug(f"PATTERN: bind wholef {a} {b}")
            if a == None or b == None:
                return None
            return a.sect(b)
        return self._bindWhole(wholef, f)

    def join(self):
        """Flattens a pattern of patterns into a pattern, where wholes are
        the intersection of matched inner and outer events."""
        return self.bind(id)
    
    def bindInner(self, f):
        logging.debug(f"PATTERN: bindInner {self} {f}")
        def wholef(a, b):
            logging.debug(f"PATTERN: bindInner wholef {a} {b}")
            if a == None or b == None:
                return None
            return a
        return self._bindWhole(wholef, f)

    def joinInner(self):
        """Flattens a pattern of patterns into a pattern, where wholes are
        taken from inner events."""
        return self.bindInner(id)
    
    def bindOuter(self, f):
        logging.debug(f"PATTERN: bindOuter {self} {f}")
        def wholef(a, b):
            logging.debug(f"PATTERN: bindOuter wholef {a} {b}")
            if a == None or b == None:
                return None
            return b
        return self._bindWhole(wholef, f)

    def joinOuter(self):
        """Flattens a pattern of patterns into a pattern, where wholes are
        taken from outer events."""
        return self.bindOuter(id)
    
    def _fast(self, factor) -> Pattern:
        """ Speeds up a pattern by the given factor"""
        logging.debug(f"PATTERN: fast {self} {factor}")
        fastQuery = self.withQueryTime(lambda t: t*factor)
        fastEvents = fastQuery.withEventTime(lambda t: t/factor)
        logging.debug(f"PATTERN: fast fastEvents {fastEvents}")
        return fastEvents

    def fast(self, pfactor) -> Pattern:
        """ Speeds up a pattern using the given pattern of factors"""
        logging.debug(f"PATTERN: fast {self} {pfactor}")
        return pfactor.fmap(lambda factor: self._fast(factor)).joinOuter()
        
    def slow(self, factor) -> Pattern:
        logging.debug(f"PATTERN: slow {self} {factor}")
        """ Slow slows down a pattern """
        return self._fast(1/factor)

    def early(self, offset) -> Pattern:
        """ Equivalent of Tidal's <~ operator """
        logging.debug(f"PATTERN: early {self} {offset}")
        return self.withQueryTime(
                lambda t: t+offset).withEventTime(lambda t: t-offset)

    def late(self, offset) -> Pattern:
        """ Equivalent of Tidal's ~> operator """
        logging.debug(f"PATTERN: late {self} {offset}")
        return self.early(0-offset)

    def firstCycle(self):
        logging.debug(f"PATTERN: firstCycle {self}")
        return self.query(TimeSpan(Time(0), Time(1)))

def pure(value) -> Pattern:
    logging.debug(f"PURE: value {value}")
    """ Returns a pattern that repeats the given value once per cycle """
    def query(span):
        logging.debug(f"PURE: span {span}")
        return [Event(wholeCycle(subspan.begin), subspan, value)
                for subspan in span.spanCycles()
               ]
    return Pattern(query)

# alias
atom = pure

def slowcat(pats) -> Pattern:
    """Concatenation: combines a list of patterns, switching between them
    successively, one per cycle.
    (currently behaves slightly differently from Tidal)

    """
    logging.debug(f"PURE: slowCat {pats}")
    def query(span):
        logging.debug(f"PURE: slowCat query {span}")
        pat = pats[floor(span.begin) % len(pats)]
        return pat.query(span)
    return Pattern(query).splitQueries()

def fastcat(pats) -> Pattern:
    """Concatenation: as with slowcat, but squashes a cycle from each
    pattern into one cycle"""
    logging.debug(f"PURE: fastCat {pats}")
    return slowcat(pats)._fast(len(pats))




# alias
cat = fastcat

def stack(pats) -> Pattern:
    """ Pile up patterns """
    logging.debug(f"STACK: pats {pats}")
    def query(span):
        logging.debug(f"STACK: query span {span}")
        return concat([pat.query(span) for pat in pats])
    return Pattern(query)

def pattern_pretty_printing(pattern: Pattern, query_span: TimeSpan) -> None:
    """ Better formatting for printing Tidal Patterns """
    for event in pattern.query(query_span):
        logging.info(event)

# Should this be a value or a function?
silence = Pattern(lambda _: [])


if __name__ == "__main__":

    # Simple patterns
    a = atom("hello")
    b = atom("world")
    c = fastcat([a,b])
    d = stack([a, b])

    # Printing the pattern
    print("\n== TEST PATTERN ==\n")
    print('Like: "hello world" (over two cycles)')
    pattern_pretty_printing(
            pattern= c,
            query_span= TimeSpan(Time(0),Time(2)))

    # Printing the pattern with fast
    print("\n== SAME BUT FASTER==\n")
    print('Like: fast 4 "hello world"')
    pattern_pretty_printing(
            pattern= c._fast(2),
            query_span= TimeSpan(Time(0), Time(1)))

    # Printing the pattern with patterned fast
    print("\n== PATTERNS OF FAST OF PATTERNS==\n")
    print('Like: fast "2 4" "hello world"')
    pattern_pretty_printing(
            pattern= c.fast(fastcat([atom(2), atom(4)])),
            query_span= TimeSpan(Time(0), Time(1)))

    # Printing the pattern with stack
    print("\n== STACK ==\n")
    pattern_pretty_printing(
            pattern=d,
            query_span= TimeSpan(Time(0), Time(1)))

    # Printing the pattern with late
    print("\n== LATE ==\n")
    pattern_pretty_printing(
            pattern=c.late(0.5),
            query_span= TimeSpan(Time(0), Time(1)))

    # Apply pattern of values to a pattern of functions
    print("\n== APPLICATIVE ==\n")
    x = fastcat([atom(lambda x: x + 1), atom(lambda x: x + 4)])
    y = fastcat([atom(3),atom(4),atom(5)])
    z = x.app(y)
    pattern_pretty_printing(
            pattern= z,
            query_span= TimeSpan(Time(0), Time(1)))

    # Add number patterns together
    print("\n== ADDITION ==\n")
    numbers = fastcat([atom(v) for v in [2,3,4,5]])
    more_numbers = fastcat([atom(10), atom(100)])
    pattern_pretty_printing(
            pattern= numbers + more_numbers,
            query_span= TimeSpan(Time(0), Time(1)))
