#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Experiment: porting Tidalcycles to Python 3.x.
"""

from __future__ import annotations
from fractions import Fraction
from dataclasses import dataclass
from typing import Any, Union
from math import floor

# flatten list of lists
def concat(t) -> list: 
    return [item for sublist in t for item in sublist]

def removeNone(t) -> list:
    return filter(lambda x: x != None, t)

# Couldn't subclass Fraction to call it "Time" for some strange inheritance
# issue (inheritance of magic methods). Stuck with Fraction for now. Someone
# might know how to properly subclass Fraction.

Time = Fraction # Time is rational
def sam(frac: Time) -> Time: return Time(floor(frac))
def nextSam(frac: Time) -> Time: return Time(sam(frac) + 1)
def wholeCycle(frac: Time) -> TimeSpan: return TimeSpan(sam(frac), nextSam(frac))


class TimeSpan:

    """ TimeSpan is (Time, Time) """
    
    def __init__(self, begin: Time, end: Time):
        self.begin = begin
        self.end = end

    def spanCycles(self) -> list:
        """ Splits a timespan at cycle boundaries """
        
        # TODO - make this more imperative

        if self.end <= self.begin:
            # no cycles in the timespan..
            return []
        elif sam(self.begin) == sam(self.end):
            # Timespan is all within one cycle
            return [self]
        else:
            nextB = nextSam(self.begin)
            spans = TimeSpan(nextB, self.end).spanCycles()
            spans.insert(0, TimeSpan(self.begin, nextB))
            return spans

    def withTime(self, f) -> TimeSpan:
        return TimeSpan(f(self.begin), f(self.end))

    def sect(self, other):
        """ Intersection of two timespans """
        return TimeSpan(max(self.begin, other.begin), min(self.end, other.end))

    def maybeSect(a, b):
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

    """ Event class """

    def __init__(self, whole, part, value):
        self.whole = whole
        self.part = part
        self.value = value

    def withSpan(self, f) -> Event:
        whole = None if not self.whole else f(self.whole)
        return Event(whole, f(self.part), self.value)

    def withValue(self, f) -> Event:
        return Event(self.whole, self.part, f(self.value))

    def __repr__(self) -> str:
        return ("Event(" + self.whole.__repr__()
                + ", "
                + self.part.__repr__() + ")"
                + ", "
                + self.value.__repr__() + ")")
    

class Pattern:

    """ Pattern class """

    def __init__(self, query):
        self.query = query

    def splitQueries(self) -> Pattern:
        """ Splits queries at cycle boundaries. Makes some calculations easier
        to express, as everything then happens within a cycle. """

        def query(span) -> list: 
            return concat(list(map(self.query, span.spanCycles())))
        return Pattern(query)

    def withQuerySpan(self, f) -> Pattern:
        return Pattern(lambda span: self.query(f(span)))

    def withQueryTime(self, f) -> Pattern:
        return Pattern(lambda span: self.query(span.withTime(f)))

    def withEventSpan(self, f) -> Pattern:
        def query(span):
            return list(map(lambda event: event.withSpan(f),
                            self.query(span)))
        return Pattern(query)
    
    def withEventTime(self, f) -> Pattern:
        return self.withEventSpan(lambda span: span.withTime(f))

    def withValue(self, f) -> Pattern:
        def query(span):
            return list(map(lambda event: event.withValue(f),
                            self.query(span)
                           )
                       )
        return Pattern(query)

    # alias
    fmap = withValue
    
    def _app(self, wf, patv):
        """
        Assumes self is a pattern of functions, and given a function to
        resolve wholes, applies a given pattern of values to that
        pattern of functions.

        """
        patf = self
        def query(span):
            efs = patf.query(span)
            evs = patv.query(span)
            def apply(ef, ev):
                s = ef.part.maybeSect(ev.part)
                if s == None:
                    return None
                return Event(wf(ef.whole, ev.whole), s, ef.value(ev.value))
            return list(concat(map (lambda ef: removeNone(map (lambda ev: apply(ef, ev),evs)),efs)))
        return Pattern(query)

    def app(self, patv):
        """ Tidal's <*> """
        def wholef(a, b):
            if a == None or b == None:
                return None
            return a.sect(b)
        return self._app(wholef, patv)

    def appl(self, patv):
        """ Tidal's <* """
        def wholef(a, b):
            if a == None or b == None:
                return None
            return a
        return self._app(wholef, patv)

    def appr(self, patv):
        """ Tidal's *> """
        def wholef(a, b):
            if a == None or b == None:
                return None
            return b
        return self._app(wholef, patv)
    
    def fast(self, factor) -> Pattern:
        """ Fast speeds up a pattern """
        fastQuery = self.withQueryTime(lambda t: t*factor)
        fastEvents = fastQuery.withEventTime(lambda t: t/factor)
        return fastEvents
    
    def slow(self, factor) -> Pattern:
        """ Slow slows down a pattern """
        return self.fast(1/factor)

    def early(self, offset) -> Pattern:
        """ Equivalent of Tidal's <~ operator """
        return self.withQueryTime(
                lambda t: t+offset).withEventTime(lambda t: t-offset)

    def late(self, offset) -> Pattern:
        """ Equivalent of Tidal's ~> operator """
        return self.early(0-offset)
    
    def firstCycle(self):
        return self.query(TimeSpan(Time(0), Time(1)))            

def pure(value) -> Pattern:
    """ Returns a pattern that repeats the given value once per cycle """
    def query(span):
        return list(map(
            lambda subspan: Event(
                wholeCycle(subspan.begin), subspan, value),
            span.spanCycles()))
    return Pattern(query)

# alias
atom = pure

def slowcat(pats) -> Pattern:
    """Concatenation: combines a list of patterns, switching between them
    successively, one per cycle. 
    (currently behaves slightly differently from Tidal)

    """
    def query(span):
        pat = pats[floor(span.begin) % len(pats)]
        return pat.query(span)
    return Pattern(query).splitQueries()

def fastcat(pats) -> Pattern:
    """Concatenation: as with slowcat, but squashes a cycle from each
    pattern into one cycle"""
    return slowcat(pats).fast(len(pats))

# alias
cat = fastcat

def stack(pats) -> Pattern:
    """ Pile up patterns """
    def query(span):
        return concat(list(map(lambda pat: pat.query(span), pats)))
    return Pattern(query)

def pattern_pretty_printing(pattern: Pattern, query_span: TimeSpan) -> None:
    """ Better formatting for printing Tidal Patterns """
    for event in pattern.query(query_span):
        print(event)

# Should this be a value or a function?
silence = Pattern(lambda _: [])


if __name__ == "__main__":

    # Simple patterns
    a = atom("hello")
    b = atom("world")
    c = fastcat([a,b])

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

    # Apply pattern of values to a pattern of functions
    print("\n== APPLICATIVE ==\n")
    x = fastcat([atom(lambda x: x + 1), atom(lambda x: x + 2)])
    y = fastcat([atom(3),atom(4),atom(5)])
    z = x.app(y)
    pattern_pretty_printing(
            pattern= z,
            query_span= TimeSpan(Time(0), Time(1)))


