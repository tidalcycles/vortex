
from functools import partialmethod
import sys
from fractions import Fraction
from math import floor


class Time(Fraction):
    """Fraction is immutable so new instead of init"""
    def __new__(cls, *args, **kwargs):
        self = super(Time, cls).__new__(cls, *args, **kwargs)
        return self

    def sam(self):
        """Returns the start of the cycle."""
        return Time(floor(self))

    def next_sam(self):
        """Returns the start of the next cycle."""
        # Operators still return Fraction objects..
        return Time(self.sam() + 1)

    def whole_cycle(self):
        """Returns a TimeSpan representing the begin and end of the Time value's cycle"""
        return TimeSpan(self.sam(), self.next_sam())


class TimeSpan(object):

    """ TimeSpan is (Time, Time) """
    def __init__(self, begin: Time, end: Time):
        self.begin = Time(begin)
        self.end = Time(end)

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

    def sect(self, other):
        """Intersection of two timespans, returns None if they don't intersect."""
        if self.begin >= other.end or self.end <= other.begin:
            return None
        else:
            return TimeSpan(max(self.begin, other.begin), min(self.end, other.end))

    def sect_e(self, other):
        """Like 'sect', but raises an exception if the timespans don't intersect."""
        result = self.sect(other)
        if result == None:
            raise ValueError(f'TimeSpan {self} and TimeSpan {other} do not intersect')
        return result

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
                s = event_funcs.part.sect(event_vals.part)
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
            return a.sect_e(b)

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
            return a.sect_e(b)
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

    def every(self, n, func):
        return self.slowcat([func(self)] + ([self] * (n-1)))

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
        return self.query(TimeSpan(Time(0), Time(1)))

    @classmethod
    def silence(cls):
        cls(lambda _: [])

    @classmethod
    def checkType(cls, value) -> bool:
        return True
    
    @classmethod
    def pure(cls, v):
        """ Returns a pattern that repeats the given value once per cycle """
        if not cls.checkType(v):
            raise ValueError
        
        def query(span):
            return [Event(Time(subspan.begin).whole_cycle(), subspan, v)
                    for subspan in span.span_cycles()
            ]
        return cls(query)
    
    @classmethod
    def slowcat(cls, pats):
        """Concatenation: combines a list of patterns, switching between them
        successively, one per cycle.
        (currently behaves slightly differently from Tidal)

        """
        def query(span):
            pat = pats[floor(span.begin) % len(pats)]
            return pat.query(span)
        return cls(query).split_queries()

    @classmethod
    def fastcat(cls,pats):
        """Concatenation: as with slowcat, but squashes a cycle from each
        pattern into one cycle"""
        return cls.slowcat(pats)._fast(len(pats))

    # alias
    cat = fastcat

    @classmethod
    def stack(cls, pats):
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
    def checkType(cls, value) -> bool:
        return isinstance(value, dict)

# Hippie type inference..
    
def guess_value_class(val):
    if isinstance(val, int):
        return I
    if isinstance(val, str):
        return S
    if isinstance(val, float):
        return F
    if isinstance(val, Time):
        return T
    if isinstance(val, dict):
        return Control
    return Pattern

module_obj = sys.modules[__name__]

# Hack to make module-level function versions of pattern methods.

def func_maker(name):
    def func(*args):
        args = list(args)
        pat = args.pop()
        method = getattr(pat, name)
        try:
            return method(*args)
        except (TypeError) as e:
            return partialmethod(method, *args)

        return method(arg)
    return func

for name in ["fast", "slow", "early", "late"]:
    setattr(module_obj, name, func_maker(name))

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