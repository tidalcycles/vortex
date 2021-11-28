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

# Couldn't subclass Fraction to call it "Time" for some strange inheritance
# issue (inheritance of magic methods). Stuck with Fraction for now. Someone
# might know how to properly subclass Fraction.

Time = Fraction # Time is rational
def sam(frac: Time) -> Time: return Time(floor(frac))
def nextSam(frac: Time) -> Time: return Time(sam(frac) + 1)
def wholeCycle(frac: Time) -> Arc: return Arc(sam(frac), nextSam(frac))


class Arc:

    """ Arc is (Time, Time) """

    def __init__(self, begin: Time, end: Time):
        self.begin = begin
        self.end = end

    # TODO - make this more imperative
    def spanCycles(self) -> list:

        # Tests
        endLower = self.end <= self.begin
        endEqual = sam(self.begin) == sam(self.end)

        if endLower:
            return []
        elif endEqual:
            return [self]
        else:
            nextB = nextSam(self.begin)
            spans = Arc(nextB, self.end).spanCycles()
            spans.insert(0, Arc(self.begin, nextB))
            return spans

    def withTime(self, f) -> Arc:
        return Arc(f(self.begin), f(self.end))
    
    def __repr__(self) -> str:
        return ("Arc(" + self.begin.__repr__() + ", " 
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

    def fast(self, factor) -> Pattern:
        """ Fast speeds up a pattern """
        fastQuery = self.withQueryTime(lambda t: t*factor)
        fastEvents = fastQuery.withEventTime(lambda t: t/factor)
        return fastEvents
    
    def slow(self, factor) -> Pattern:
        """ Slow slows down a pattern """
        return self.fast(1/factor)

    def early(self, offset) -> Pattern:
        """ Equivalent of Haskell Tidal <~ operator """
        return self.withQueryTime(
                lambda t: t+offset).withEventTime(lambda t: t-offset)

    def late(self, offset) -> Pattern:
        """ Equivalent of Haskell Tidal ~> operator """
        return self.early(0-offset)
    
    def firstCycle(self) -> Pattern:
        return self.query(Arc(Time(0), Time(1)))
    

def atom(value) -> Pattern:
    def query(span):
        return list(map(
            lambda subspan: Event(
                wholeCycle(subspan.begin), subspan, value),
            span.spanCycles()))
    return Pattern(query)

def slowcat(pats) -> Pattern:
    """ Concatenation: will join two patterns """
    def query(span):
        pat = pats[floor(span.begin) % len(pats)]
        return pat.query(span)
    return Pattern(query).splitQueries()

def fastcat(pats) -> Pattern:
    """ Concatenation: pushes everything into a pattern """
    return slowcat(pats).fast(len(pats))

def stack(pats) -> Pattern:
    """ Pile up patterns """
    def query(span):
        return concat(list(map(lambda pat: pat.query(span), pats)))
    return Pattern(query)


def pattern_pretty_printing(pattern: Pattern, query_arc: Arc) -> None:
    """ Better formatting for printing Tidal Patterns """
    for event in pattern.query(query_arc):
        print(event)

# Should this be a value or a function?
silence = Pattern(lambda _: [])


if __name__ == "__main__":

    # Simple pattern
    a = atom("hello")
    b = atom("world")
    c = fastcat([a,b])

    # Printing the pattern
    print("\n== TEST PATTERN ==\n")
    pattern_pretty_printing(
            pattern= c, 
            query_arc= Arc(Time(0),Time(2)))

    # Printing the pattern with fast
    print("\n== SAME BUT FASTER==\n")
    pattern_pretty_printing(
            pattern= c.fast(2),
            query_arc= Arc(Time(0), Time(1)))
