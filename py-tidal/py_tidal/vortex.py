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
    print(f"CONCAT: list {t}")
    return [item for sublist in t for item in sublist]

def removeNone(t) -> list:
    print(f"REMOVENONE: list {t}")
    return filter(lambda x: x != None, t)

# Couldn't subclass Fraction to call it "Time" for some strange inheritance
# issue (inheritance of magic methods). Stuck with Fraction for now. Someone
# might know how to properly subclass Fraction.

class Time(Fraction):
    """Fraction is immutable so new instead of init"""

    def new(cls, numerator=0, denominator=None):
        self = super(Time, cls).new(cls, numerator, denominator)
        return self

    def sam(frac: Time) -> Time:
        log.debug(f"SAM: {frac}")
        return Time(floor(frac))

    def nextSam(frac: Time) -> Time:
        log.debug(f"NEXT SAM: {frac}")
        return Time(self.sam(frac) + 1)

    def wholeCycle(frac: Time) -> TimeSpan:
        print(f"in wholeCycle {self.sam(frac)} {self.nextSam(frac)}")
        return TimeSpan(self.sam(frac), self.nextSam(frac))


class TimeSpan:

    """ TimeSpan is (Time, Time) """

    def __init__(self, begin: Time, end: Time):
        self.begin = begin
        self.end = end
        print(f"TIMESPAN: __init__ {self}")

    def spanCycles(self) -> list:
        print(f"TIMESPAN: spanCycles {self}")
        """ Splits a timespan at cycle boundaries """

        # TODO - make this more imperative

        if self.end <= self.begin:
            # no cycles in the timespan..
            return []
        elif sam(self.begin) == sam(self.end):
            # Timespan is all within one cycle
            print(f"TIMESPAN: spanCycles sam(begin) == sam(end) {self}")
            return [self]
        else:
            print(f"TIMESPAN: spanCycles {self}")
            nextB = nextSam(self.begin)
            spans = TimeSpan(nextB, self.end).spanCycles()
            print(f"before insert {spans}")
            spans.insert(0, TimeSpan(self.begin, nextB))
            print(f"TIMESPAN: spanCycles {spans}")
            return spans

    def withTime(self, f) -> TimeSpan:
        print(f"TIMESPAN: withTime {f} {self}")
        return TimeSpan(f(self.begin), f(self.end))

    def sect(self, other):
        """ Intersection of two timespans """
        print(f"TIMESPAN: sect {self} {other}")
        return TimeSpan(max(self.begin, other.begin), min(self.end, other.end))

    def maybeSect(a, b):
        print(f"TIMESPAN: maybeSect {a} {b}")
        """ Like sect, but returns None if they don't intersect """
        s = a.sect(b)
        print(f"TIMESPAN: maybeSect {s}")
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
        print(f"EVENT: __init__ {self}")

    def withSpan(self, f) -> Event:
        whole = None if not self.whole else f(self.whole)
        print(f"EVENT: withSpan {self} {f}")
        return Event(whole, f(self.part), self.value)

    def withValue(self, f) -> Event:
        print(f"EVENT: withValue {self} {f}")
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
        print(f"PATTERN: __init__ {self} {query}")

    def splitQueries(self) -> Pattern:
        """ Splits queries at cycle boundaries. Makes some calculations easier
        to express, as everything then happens within a cycle. """
        print(f"PATTERN: splitQueries {self} {self.query}")

        def query(span) -> list:
            return concat([self.query(subspan) for subspan in span.spanCycles()])

        return Pattern(query)

    def withQuerySpan(self, f) -> Pattern:
        print(f"PATTERN: withQuerySpan {self} {self.query} {f}")
        return Pattern(lambda span: self.query(f(span)))

    def withQueryTime(self, f) -> Pattern:
        print(f"PATTERN: withQueryTime {self} {self.query} {f}")
        return Pattern(lambda span: self.query(span.withTime(f)))

    def withEventSpan(self, f) -> Pattern:
        print(f"PATTERN: withEventSpan {self} {self.query} {f}")
        def query(span):
            return [event.withSpan(f) for event in self.query(span)]
        return Pattern(query)

    def withEventTime(self, f) -> Pattern:
        print(f"PATTERN: withEventTime {self} {self.query} {f}")
        return self.withEventSpan(lambda span: span.withTime(f))

    def withValue(self, f) -> Pattern:
        print(f"PATTERN: withValue {self} {self.query} {f}")
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
        print(f"PATTERN: _appWhole {self} {self.query} {wf} {patv}")
        patf = self
        def query(span):
            print(f"PATTERN: _appWhole query {wf} {patf} {span}")
            efs = patf.query(span)
            evs = patv.query(span)
            print(f"PATTERN: _appWhole query {efs} {evs}")
            def apply(ef, ev):
                print(f"PATTERN: _appWhole apply {ef} {ev}")
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
        print(f"PATTERN: app <*> {self} {self.query} {patv}")
        """ Tidal's <*> """
        def wholef(a, b):
            if a == None or b == None:
                return None
            return a.sect(b)

        print(f"PATTERN: app {wholef} {patv}")
        return self._appWhole(wholef, patv)

    def appl(self, patv):
        """ Tidal's <* """
        print(f"PATTERN: appl <* {self} {self.query} {patv}")
        def wholef(a, b):
            if a == None or b == None:
                return None
            return a

        print(f"PATTERN: appl {wholef} {patv}")
        return self._appWhole(wholef, patv)

    def appr(self, patv):
        """ Tidal's *> """
        print(f"PATTERN: appr *> {self} {self.query} {patv}")
        def wholef(a, b):
            if a == None or b == None:
                return None
            return b

        print(f"PATTERN: appr {wholef} {patv}")
        return self._appWhole(wholef, patv)

    def _bindWhole(self, chooseWhole, f):
        print(f"PATTERN: _bindwhole *> {self} {chooseWhole} {f}")
        patv = self
        def query(span):
            def withWhole(a, b):
                print(f"PATTERN: _bindwhole withWhole *> {a} {b}")
                return Event(chooseWhole(a.whole, b.whole), b.part,
                             b.value
                            )
            def match(a):
                print(f"PATTERN: _bindwhole match *> {a} {b}")
                return [withWhole(a, b) for b in f(a.value).query(a.part)]

            return concat([match(ev) for ev in patv.query(span)])
        return Pattern(query)

    def bind(self, f):
        print(f"PATTERN: bind {self} {f}")
        def wholef(a, b):
            print(f"PATTERN: bind wholef {a} {b}")
            if a == None or b == None:
                return None
            return a.sect(b)
        return self._bindWhole(wholef, f)

    def bindInner(self, f):
        print(f"PATTERN: bindInner {self} {f}")
        def wholef(a, b):
            print(f"PATTERN: bindInner wholef {a} {b}")
            if a == None or b == None:
                return None
            return a
        return self._bindWhole(wholef, f)

    def bindOuter(self, f):
        print(f"PATTERN: bindOuter {self} {f}")
        def wholef(a, b):
            print(f"PATTERN: bindOuter wholef {a} {b}")
            if a == None or b == None:
                return None
            return b
        return self._bindInner(wholef, f)

    def fast(self, factor) -> Pattern:
        """ Fast speeds up a pattern """
        print(f"PATTERN: fast {self} {factor}")
        fastQuery = self.withQueryTime(lambda t: t*factor)
        fastEvents = fastQuery.withEventTime(lambda t: t/factor)
        print(f"PATTERN: fast fastEvents {fastEvents}")
        return fastEvents

    def slow(self, factor) -> Pattern:
        print(f"PATTERN: slow {self} {factor}")
        """ Slow slows down a pattern """
        return self.fast(1/factor)

    def early(self, offset) -> Pattern:
        """ Equivalent of Tidal's <~ operator """
        print(f"PATTERN: early {self} {offset}")
        return self.withQueryTime(
                lambda t: t+offset).withEventTime(lambda t: t-offset)

    def late(self, offset) -> Pattern:
        """ Equivalent of Tidal's ~> operator """
        print(f"PATTERN: late {self} {offset}")
        return self.early(0-offset)

    def firstCycle(self):
        print(f"PATTERN: firstCycle {self}")
        return self.query(TimeSpan(Time(0), Time(1)))

def pure(value) -> Pattern:
    print(f"PURE: value {value}")
    """ Returns a pattern that repeats the given value once per cycle """
    def query(span):
        print(f"PURE: span {span}")
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
    print(f"PURE: slowCat {pats}")
    def query(span):
        print(f"PURE: slowCat query {span}")
        pat = pats[floor(span.begin) % len(pats)]
        return pat.query(span)
    return Pattern(query).splitQueries()

def fastcat(pats) -> Pattern:
    """Concatenation: as with slowcat, but squashes a cycle from each
    pattern into one cycle"""
    print(f"PURE: fastCat {pats}")
    return slowcat(pats).fast(len(pats))




# alias
cat = fastcat

def stack(pats) -> Pattern:
    """ Pile up patterns """
    print(f"STACK: pats {pats}")
    def query(span):
        print(f"STACK: query span {span}")
        return concat([pat.query(span) for pat in pats])
    return Pattern(query)

def pattern_pretty_printing(pattern: Pattern, query_span: TimeSpan) -> None:
    """ Better formatting for printing Tidal Patterns """
    for event in pattern.query(query_span):
        logging.info(event)

# Should this be a value or a function?
silence = Pattern(lambda _: [])

def add_1(x):
    return x + 1

def add_4(x):
    return x + 4

def add_7(x):
    return x + 7

if __name__ == "__main__":

    # Simple patterns
    a = atom("hello")
    b = atom("world")
    c = fastcat([a,b])
    d = stack([a, b])

    # Printing the pattern
    print("\n== TEST PATTERN ==\n")
    pattern_pretty_printing(
            pattern= c,
            query_span= TimeSpan(Time(0),Time(2)))

    # Printing the pattern with fast
    print("\n== SAME BUT FASTER==\n")
    pattern_pretty_printing(
            pattern= c.fast(2),
            query_span= TimeSpan(Time(0), Time(1)))

    # Printing the pattern with stack
    print("\n== STACK ==\n")
    pattern_pretty_printing(
            pattern=d,
            query_span= TimeSpan(Time(0), Time(1)))

    # Printing the pattern with late
    print("\n== LATE 0.5 ==\n")
    pattern_pretty_printing(
            pattern=c.late(0.5),
            query_span= TimeSpan(Time(0), Time(1)))

    print("\n== LATE  0.25 ==\n")
    pattern_pretty_printing(
        pattern=c.late(-0.25),
        query_span=TimeSpan(Time(0), Time(1)))

    print("\n== LATE 2 ==\n")
    pattern_pretty_printing(
        pattern=c.late(2.0),
        query_span=TimeSpan(Time(0), Time(1)))

    # Apply pattern of values to a pattern of functions
    print("\n== APPLICATIVE ==\n")
    x = fastcat([atom(add_1), atom(add_4), atom(add_7)])
    y = fastcat([atom(3),atom(4),atom(5), atom(6)])
    z = x.app(y)
    pattern_pretty_printing(
            pattern= z,
            query_span= TimeSpan(Time(0), Time(1)))

    # Apply pattern of values to a pattern of functions
    print("\n== APPLICATIVE LEFT ==\n")
    x = fastcat([atom(add_1), atom(add_4)])
    y = fastcat([atom(3),atom(4),atom(5)])
    z = x.appl(y)
    pattern_pretty_printing(
            pattern= z,
            query_span= TimeSpan(Time(0), Time(1)))

    # Apply pattern of values to a pattern of functions
    print("\n== APPLICATIVE RIGHT ==\n")
    x = fastcat([atom(add_1), atom(add_4), atom(add_7)])
    y = fastcat([atom(3),atom(4),atom(5), atom(6)])
    z = x.appr(y)
    pattern_pretty_printing(
            pattern= z,
            query_span= TimeSpan(Time(0), Time(1)))

