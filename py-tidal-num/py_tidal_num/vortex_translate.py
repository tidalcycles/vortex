"""
Experiment: porting Tidalcycles to Python 3.x.
"""

from fractions import Fraction
from typing import Any, Union, Callable, List
import numpy as np
import logging

logging.basicConfig()
log = logging.getLogger()

# Utilities


def flatten_numpy(a_rray: np.array = np.array([])):
    return a_rray.flatten()


def remove_none_np(a_rray: np.array = np.array([])):
    return a_rray[a_rray != None]


# Classes defintions


# class TimeNP(Fraction):
#     """Fraction is immutable so new instead of init"""
#
#     def __new__(cls, numerator=0, denominator=None):
#         self = super(TimeNP, cls).__new__(cls, numerator, denominator)
#         return self
#
#
# class TimeSpanNP(object):
#     """TimeSpan is (Time, Time)"""
#
#     def __init__(self, time_span: np.array):
#         self.time_span = time_span
#         super(TimeSpanNP, self).__init__()
#
#
# class Event(object):
#     def __init__(self, whole, part, value):
#         self.whole = whole
#         self.part = part
#         self.value = value
#         super(Event, self).__init__()


# class Pattern(object):
#    def __init__(self, query):
#        self.query = query
#        super(Pattern, self).__init__()


def pattern(function_list: List[Callable]) -> Any:
    def query(input=None):
        res = input
        for function in function_list:
            log.info(f"Calling {str(function)}")
            res = function(res)
        return res

    return query


# Functions


def sam_np(frac: Fraction) -> np.array:
    return np.floor(frac)


def next_sam_np(frac: Fraction) -> np.array:
    return np.ceil(frac)


def whole_cycle_np(frac: Fraction) -> np.array:
    return np.array([sam_np(frac), next_sam_np(frac)])


def sect_numpy(timespan_a: np.array, timespan_b: np.array) -> np.array:
    return (
        np.array(
            [
                np.maximum(timespan_a[0], timespan_b[0]),
                np.minimum(timespan_a[1], timespan_b[1]),
            ]
        )
        if timespan_a[1] > timespan_b[0]
        else None
    )


def create_with_time(func: Callable):
    def with_time(time_span: np.array):
        return func(time_span)

    return with_time


def span_cycles(time_span: np.array) -> np.array:
    x = np.arange(sam_np(time_span[0]), next_sam_np(time_span[1])+1, 1)
    x[0] = time_span[0]
    x[-1] = time_span[1]
    return np.array([x[:-1], x[1:]]).T


def create_event_with_span(part, value, func):
    def with_span(whole=None):
        whole = func(whole) if whole is not None else None
        return whole, func(part), value

    return with_span


def create_event_with_value(whole_part, func):
    def with_value(value):
        return whole_part, func(value)

    return with_value


def create_query(func: Callable):
    def query(span: np.array) -> np.array:
        return func(span)

    return query


def pure(value) -> np.array:
    """ Returns a pattern that repeats the given value once per cycle """
    def query(span):
        return [np.array(whole_cycle_np(subspan), subspan, value) for subspan in span_cycles(span)]
    return pattern(query)

#def create_query_time(func: Callable, begin, end):
#    def query_time(span: TimeSpanNP) -> TimeSpanNP:
#        create_with_time(func, begin, end)(span)
#
#    return query_time


#
# class Pattern:
#
#     """Pattern class"""
#
#     def __init__(self, query):
#         self.query = query
#
#     def splitQueries(self) -> Pattern:
#         """Splits queries at cycle boundaries. Makes some calculations easier
#         to express, as everything then happens within a cycle."""
#
#         def query(span) -> list:
#             return concat([self.query(subspan) for subspan in span.spanCycles()])
#
#         return Pattern(query)
#
#     def withQuerySpan(self, f) -> Pattern:
#         return Pattern(lambda span: self.query(f(span)))
#
#     def withQueryTime(self, f) -> Pattern:
#         return Pattern(lambda span: self.query(span.withTime(f)))
#
#     def withEventSpan(self, f) -> Pattern:
#         def query(span):
#             return [event.withSpan(f) for event in self.query(span)]
#
#         return Pattern(query)
#
#     def withEventTime(self, f) -> Pattern:
#         return self.withEventSpan(lambda span: span.withTime(f))
#
#     def withValue(self, f) -> Pattern:
#         def query(span):
#             return [event.withValue(f) for event in self.query(span)]
#
#         return Pattern(query)
#
#     # alias
#     fmap = withValue
#
#     def _appWhole(self, wf, patv):
#         """
#         Assumes self is a pattern of functions, and given a function to
#         resolve wholes, applies a given pattern of values to that
#         pattern of functions.
#
#         """
#         patf = self
#
#         def query(span):
#             efs = patf.query(span)
#             evs = patv.query(span)
#
#             def apply(ef, ev):
#                 s = ef.part.maybeSect(ev.part)
#                 if s == None:
#                     return None
#                 return Event(wf(ef.whole, ev.whole), s, ef.value(ev.value))
#
#             return concat([removeNone([apply(ef, ev) for ev in evs]) for ef in efs])
#
#         return Pattern(query)
#
#     def app(self, patv):
#         """Tidal's <*>"""
#
#         def wholef(a, b):
#             if a == None or b == None:
#                 return None
#             return a.sect(b)
#
#         return self._appWhole(wholef, patv)
#
#     def appl(self, patv):
#         """Tidal's <*"""
#
#         def wholef(a, b):
#             if a == None or b == None:
#                 return None
#             return a
#
#         return self._appWhole(wholef, patv)
#
#     def appr(self, patv):
#         """Tidal's *>"""
#
#         def wholef(a, b):
#             if a == None or b == None:
#                 return None
#             return b
#
#         return self._appWhole(wholef, patv)
#
#     def _bindWhole(self, chooseWhole, f):
#         patv = self
#
#         def query(span):
#             def withWhole(a, b):
#                 return Event(chooseWhole(a.whole, b.whole), b.part, b.value)
#
#             def match(a):
#                 return [withWhole(a, b) for b in f(a.value).query(a.part)]
#
#             return concat([match(ev) for ev in patv.query(span)])
#
#         return Pattern(query)
#
#     def bind(self, f):
#         def wholef(a, b):
#             if a == None or b == None:
#                 return None
#             return a.sect(b)
#
#         return self._bindWhole(wholef, f)
#
#     def bindInner(self, f):
#         def wholef(a, b):
#             if a == None or b == None:
#                 return None
#             return a
#
#         return self._bindWhole(wholef, f)
#
#     def bindOuter(self, f):
#         def wholef(a, b):
#             if a == None or b == None:
#                 return None
#             return b
#
#         return self._bindInner(wholef, f)
#
#     def fast(self, factor) -> Pattern:
#         """Fast speeds up a pattern"""
#         fastQuery = self.withQueryTime(lambda t: t * factor)
#         fastEvents = fastQuery.withEventTime(lambda t: t / factor)
#         return fastEvents
#
#     def slow(self, factor) -> Pattern:
#         """Slow slows down a pattern"""
#         return self.fast(1 / factor)
#
#     def early(self, offset) -> Pattern:
#         """Equivalent of Tidal's <~ operator"""
#         return self.withQueryTime(lambda t: t + offset).withEventTime(
#             lambda t: t - offset
#         )
#
#     def late(self, offset) -> Pattern:
#         """Equivalent of Tidal's ~> operator"""
#         return self.early(0 - offset)
#
#     def firstCycle(self):
#         return self.query(TimeSpan(Time(0), Time(1)))
#
#
# def pure(value) -> Pattern:
#     """Returns a pattern that repeats the given value once per cycle"""
#
#     def query(span):
#         return [
#             Event(wholeCycle(subspan.begin), subspan, value)
#             for subspan in span.spanCycles()
#         ]
#
#     return Pattern(query)
#
#
# # alias
# atom = pure
#
#
# def slowcat(pats) -> Pattern:
#     """Concatenation: combines a list of patterns, switching between them
#     successively, one per cycle.
#     (currently behaves slightly differently from Tidal)
#
#     """
#
#     def query(span):
#         pat = pats[floor(span.begin) % len(pats)]
#         return pat.query(span)
#
#     return Pattern(query).splitQueries()
#
#
# def fastcat(pats) -> Pattern:
#     """Concatenation: as with slowcat, but squashes a cycle from each
#     pattern into one cycle"""
#     return slowcat(pats).fast(len(pats))
#
#
# # alias
# cat = fastcat
#
#
# def stack(pats) -> Pattern:
#     """Pile up patterns"""
#
#     def query(span):
#         return concat([pat.query(span) for pat in pats])
#
#     return Pattern(query)
#
#
# def pattern_pretty_printing(pattern: Pattern, query_span: TimeSpan) -> None:
#     """Better formatting for printing Tidal Patterns"""
#     for event in pattern.query(query_span):
#         print(event)
#
#
# # Should this be a value or a function?
# silence = Pattern(lambda _: [])
#
#
# if __name__ == "__main__":
#
#     # Simple patterns
#     a = atom("hello")
#     b = atom("world")
#     c = fastcat([a, b])
#
#     # Printing the pattern
#     print("\n== TEST PATTERN ==\n")
#     pattern_pretty_printing(pattern=c, query_span=TimeSpan(Time(0), Time(2)))
#
#     # Printing the pattern with fast
#     print("\n== SAME BUT FASTER==\n")
#     pattern_pretty_printing(pattern=c.fast(2), query_span=TimeSpan(Time(0), Time(1)))
#
#     # Apply pattern of values to a pattern of functions
#     print("\n== APPLICATIVE ==\n")
#     x = fastcat([atom(lambda x: x + 1), atom(lambda x: x + 2)])
#     y = fastcat([atom(3), atom(4), atom(5)])
#     z = x.app(y)
#     pattern_pretty_printing(pattern=z, query_span=TimeSpan(Time(0), Time(1)))
