
from decimal import ExtendedContext
from functools import partial, partialmethod
import sys
from fractions import Fraction
import math
from .utils import *

"""Returns the start of the cycle."""
Fraction.sam = lambda self: Fraction(math.floor(self))

"""Returns the start of the next cycle."""
Fraction.next_sam = lambda self: self.sam() + 1

"""Returns a TimeSpan representing the begin and end of the Time value's cycle"""
Fraction.whole_cycle = lambda self: TimeSpan(self.sam(), self.next_sam())

class TimeSpan(object):

    """ TimeSpan is (Time, Time) """
    def __init__(self, begin: Fraction, end: Fraction):

        # Is this needed?
        if not isinstance(begin, Fraction):
            begin = Fraction(begin)

        if not isinstance(end, Fraction):
            end = Fraction(end)

        self.begin = begin
        self.end = end

    def span_cycles(self) -> list:
        """ Splits a timespan at cycle boundaries """
        spans = []
        begin = self.begin
        end = self.end
        end_sam = end.sam()

        while end > begin:
            # If begin and end are in the same cycle, we're done.
            if begin.sam() == end_sam:
                spans.append(TimeSpan(begin, self.end))
                break
            # add a timespan up to the next sam
            next_begin = begin.next_sam()
            spans.append(TimeSpan(begin, next_begin))

            # continue with the next cycle
            begin = next_begin
        return spans

    def with_time(self, f):
        """ Applies given function to both the begin and end value of the timespan"""
        return TimeSpan(f(self.begin), f(self.end))

    def intersection(self, other):
        """Intersection of two timespans, returns None if they don't intersect."""
        intersect_begin = max(self.begin, other.begin)
        intersect_end = min(self.end, other.end)

        if intersect_begin > intersect_end:
            return None
        if intersect_begin == intersect_end:
            # Zero-width (point) intersection - doesn't intersect if it's at the end of a
            # non-zero-width timespan.
            if intersect_begin == self.end and self.begin < self.end:
                return None
            if intersect_begin == other.end and other.begin < other.end:
                return None 

        return TimeSpan(intersect_begin, intersect_end)

    def intersection_e(self, other):
        """Like 'sect', but raises an exception if the timespans don't intersect."""
        result = self.intersection(other)
        if result == None:
            raise ValueError(f'TimeSpan {self} and TimeSpan {other} do not intersect')
        return result

    def midpoint(self):
        return self.begin + ((self.end-self.begin)/2)

    def __repr__(self) -> str:
        return ("TimeSpan(" + self.begin.__repr__() + ", "
                +  self.end.__repr__() + ")")


class Event:

    """
    Event class, representing a value active during the timespan
    'part'. This might be a fragment of an event, in which case the
    timespan will be smaller than the 'whole' timespan, otherwise the
    two timespans will be the same. The 'part' must never extend outside of the
    'whole'. If the event represents a continuously changing value
    then the whole will be returned as None, in which case the given
    value will have been sampled from the point halfway between the
    start and end of the 'part' timespan.
    """

    def __init__(self, whole, part, value):
        self.whole = whole
        self.part = part
        self.value = value

    def with_span(self, func):
        """ Returns a new event with the function f applies to the event timespan. """
        whole = None if not self.whole else func(self.whole)
        return Event(whole, func(self.part), self.value)

    def with_value(self, func):
        """ Returns a new event with the function f applies to the event value. """
        return Event(self.whole, self.part, func(self.value))

    def has_onset(self) -> bool:
        """ Test whether the event contains the onset, i.e that
        the beginning of the part is the same as that of the whole timespan."""
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

    def split_queries(self):
        """ Splits queries at cycle boundaries. This makes some calculations 
        easier to express, as all events are then constrained to happen within 
        a cycle. """
        def query(span) -> list:
            return concat([self.query(subspan) for subspan in span.span_cycles()])

        return self.__class__(query)

    def with_query_span(self, func):
        """ Returns a new pattern, with the function applied to the timespan of the query. """
        return self.__class__(lambda span: self.query(func(span)))

    def with_query_time(self, func):
        """ Returns a new pattern, with the function applied to both the begin
        and end of the the query timespan. """
        return self.__class__(lambda span: self.query(span.with_time(func)))

    def with_event_span(self, func):
        """ Returns a new pattern, with the function applied to each event
        timespan. """
        def query(span):
            return [event.with_span(func) for event in self.query(span)]
        return self.__class__(query)

    def with_event_time(self, func):
        """ Returns a new pattern, with the function applied to both the begin
        and end of each event timespan.
        """
        return self.with_event_span(lambda span: span.with_time(func))

    def with_value(self, func):
        """Returns a new pattern, with the function applied to the value of
        each event. It has the alias 'fmap'.

        """
        def query(span):
            return [event.with_value(func) for event in self.query(span)]
        return self.__class__(query)

    # alias
    fmap = with_value

    def onsets_only(self):
        """Returns a new pattern that will only return events where the start
        of the 'whole' timespan matches the start of the 'part'
        timespan, i.e. the events that include their 'onset'.
        """
        return self.__class__(lambda span: list(filter(Event.has_onset, self.query(span))))
    
    def _app_whole(self, whole_func, patv):
        """
        Assumes self is a pattern of functions, and given a function to
        resolve wholes, applies a given pattern of values to that
        pattern of functions.

        """
        pat_func = self
        def query(span):
            event_funcs = pat_func.query(span)
            event_vals = patv.query(span)
            def apply(event_funcs, event_vals):
                s = event_funcs.part.intersection(event_vals.part)
                if s == None:
                    return None
                return Event(whole_func(event_funcs.whole, event_vals.whole), s, event_funcs.value(event_vals.value))
            return concat([remove_nones([apply(event_func, event_val) for event_val in event_vals])
                           for event_func in event_funcs
                          ]
                         )
        return self.__class__(query)

    def app(self, pat_val):
        """ Tidal's <*> """
        def whole_func(a, b):
            if a == None or b == None:
                return None
            return a.intersection_e(b)

        return self._app_whole(whole_func, pat_val)

    def app_left(self, pat_val):
        """ Tidal's <* """
        def whole_func(a, b):
            if a == None or b == None:
                return None
            return a

        return self._app_whole(whole_func, pat_val)

    def app_right(self, pat_val):
        """ Tidal's *> """
        def whole_func(a, b):
            if a == None or b == None:
                return None
            return b

        return self._app_whole(whole_func, pat_val)

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
    
    def _bind_whole(self, choose_whole, func):
        pat_val = self
        def query(span):
            def withWhole(a, b):
                return Event(choose_whole(a.whole, b.whole), b.part,
                             b.value
                            )
            def match(a):
                return [withWhole(a, b) for b in func(a.value).query(a.part)]

            return concat([match(ev) for ev in pat_val.query(span)])
        return self.__class__(query)

    def bind(self, func):
        def whole_func(a, b):
            if a == None or b == None:
                return None
            return a.intersection_e(b)
        return self._bind_whole(whole_func, func)

    def join(self):
        """Flattens a pattern of patterns into a pattern, where wholes are
        the intersection of matched inner and outer events."""
        return self.bind(id)
    
    def inner_bind(self, func):
        def whole_func(a, b):
            if a == None or b == None:
                return None
            return a
        return self._bind_whole(whole_func, func)

    def inner_join(self):
        """Flattens a pattern of patterns into a pattern, where wholes are
        taken from inner events."""
        return self.inner_bind(id)
    
    def outer_bind(self, func):
        def whole_func(a, b):
            if a == None or b == None:
                return None
            return b
        return self._bind_whole(whole_func, func)

    def outer_join(self):
        """Flattens a pattern of patterns into a pattern, where wholes are
        taken from outer events."""
        return self.outer_bind(id)
    
    def _fast(self, factor):
        """ Speeds up a pattern by the given factor"""
        fastQuery = self.with_query_time(lambda t: t*factor)
        fastEvents = fastQuery.with_event_time(lambda t: t/factor)
        return fastEvents

    def append(self, other):
        return fastcat(self,other)

    def every(self, n, func):
        pats = [func(self)] + ([self] * (n-1))
        return slowcat(*pats)

    def fast(self, pat_factor):
        """ Speeds up a pattern using the given pattern of factors"""
        if not isinstance(pat_factor, Pattern):
            # Not patterned, run normally
            return self._fast(pat_factor)
        return pat_factor.fmap(lambda factor: self._fast(factor)).outer_join()
        
    def slow(self, factor):
        """ Slow slows down a pattern """
        return self._fast(1/factor)

    def early(self, offset):
        """ Equivalent of Tidal's <~ operator """
        return self.with_query_time(
                lambda t: t+offset).with_event_time(lambda t: t-offset)

    def late(self, offset):
        """ Equivalent of Tidal's ~> operator """
        return self.early(0-offset)

    def first_cycle(self):
        return self.query(TimeSpan(Fraction(0), Fraction(1)))

# Signals

def silence():
    return Pattern(lambda _: [])

def signal(func):
    def query(span):
        return Event(None, span, func(span.midpoint))
    return(Pattern(query))

def sine2():
    return signal(lambda time: math.sin(math.pi * 2 * time))
def sine():
    return signal(lambda time: (math.sin(math.pi * 2 * time) + 1) / 2)
    
def cosine2():
    return sine2().early(0.25)
def cosine():
    return sine().early(0.25)

def saw2():
    return signal(lambda time: (time % 1) * 2)
def saw():
    return signal(lambda time: time % 1)

def isaw2():
    return signal(lambda time: (1 - (time % 1)) * 2)
def isaw():
    return signal(lambda time: 1 - (time % 1))

def tri2():
    return fastcat(isaw2, saw2)
def tri():
    return fastcat(isaw, saw)

def pure(value):
    """ Returns a pattern that repeats the given value once per cycle """
    def query(span):
        return [Event(Fraction(subspan.begin).whole_cycle(), subspan, value)
                for subspan in span.span_cycles()
        ]
    return Pattern(query)

def steady(value):
    def query(span):
        return [Event(None, span, value)]
    return Pattern(query)
    
def slowcat(*pats):
    """
    Concatenation: combines a list of patterns, switching between them
    successively, one per cycle.
    (currently behaves slightly differently from Tidal)
    """
    pats = [reify(pat) for pat in pats]
    def query(span):
        pat = pats[math.floor(span.begin) % len(pats)]
        return pat.query(span)
    return Pattern(query).split_queries()

def fastcat(*pats):
    """Concatenation: as with slowcat, but squashes a cycle from each
    pattern into one cycle"""
    return slowcat(*pats)._fast(len(pats))

# alias
cat = fastcat

def stack(*pats):
    """ Pile up patterns """
    pats = [reify(pat) for pat in pats]
    def query(span):
        return concat([pat.query(span) for pat in pats])
    return Pattern(query)

def _sequence_count(x):
    if type(x) == list or type(x) == tuple:
        if len(x) == 1:
            return _sequence_count(x[0])
        else:
            return (fastcat(*[sequence(x) for x in x]), len(x))
    if isinstance(x, Pattern):
        return (x,1)
    else:
        return (pure(x), 1)

def sequence(*args):
    return _sequence_count(args)[0]

def polyrhythm(*args, steps=None):
        seqs = [_sequence_count(x) for x in args]
        if len(seqs) == 0:
            return silence()
        if not steps:
            steps = seqs[0][1]
        pats = []
        for seq in seqs:
            if seq[1] == 0:
                next
            if steps == seq[1]:
                pats.append(seq[0])
            else:
                pats.append(seq[0]._fast(Fraction(steps)/Fraction(seq[1])))
        return stack(*pats)

# alias
pr = polyrhythm

def polymeter(*xs):
    seqs = [sequence(x) for x in xs]

    if len(seqs) == 0:
        return silence()

    return stack(seqs)

# alias
pm = polymeter

def reify(x):
    if not isinstance(x, Pattern):
        return pure(x)
    return x

# Hack to make module-level function versions of pattern methods.

module_obj = sys.modules[__name__]

def partial_decorator(f):
    def wrapper(*args):
        try:
            return f(*args)
        except (TypeError, AttributeError) as e:
            return partial(f, *args)
    return wrapper

@partial_decorator
def fast(arg, pat):
    return pat.fast(arg)

@partial_decorator
def slow(arg, pat):
    return pat.slow(arg)

@partial_decorator
def early(arg, pat):
    return pat.early(arg)

@partial_decorator
def late(arg, pat):
    return pat.late(arg)
