import math
import sys
from fractions import Fraction
from functools import partial, total_ordering
from itertools import accumulate
from pprint import pformat
from typing import Optional

from .utils import *

"""Returns the start of the cycle."""
Fraction.sam = lambda self: Fraction(math.floor(self))

"""Returns the start of the next cycle."""
Fraction.next_sam = lambda self: self.sam() + 1

"""Returns a TimeSpan representing the begin and end of the Time value's cycle"""
Fraction.whole_cycle = lambda self: TimeSpan(self.sam(), self.next_sam())

"""Returns the position of a time value relative to the start of its cycle."""
Fraction.cycle_pos = lambda self: self - self.sam()


@total_ordering
class TimeSpan(object):

    """TimeSpan is (Time, Time)"""

    def __init__(self, begin: Fraction, end: Fraction):
        self.begin = Fraction(begin)
        self.end = Fraction(end)

    def span_cycles(self) -> list:
        """Splits a timespan at cycle boundaries"""
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

    def with_time(self, func_time):
        """Applies given function to both the begin and end time value of the timespan"""
        return TimeSpan(func_time(self.begin), func_time(self.end))

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
            raise ValueError(f"TimeSpan {self} and TimeSpan {other} do not intersect")
        return result

    def midpoint(self):
        return self.begin + ((self.end - self.begin) / 2)

    def __repr__(self) -> str:
        return f"TimeSpan({repr(self.begin)}, {repr(self.end)})"

    def __str__(self) -> str:
        return f"({show_fraction(self.begin)}, {show_fraction(self.end)})"

    def __eq__(self, other) -> bool:
        if isinstance(other, TimeSpan):
            return self.begin == other.begin and self.end == other.end
        return False

    def __le__(self, other) -> bool:
        return self.begin <= other.begin and self.end <= other.end


@total_ordering
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
        """Returns a new event with the function f applies to the event timespan."""
        whole = None if not self.whole else func(self.whole)
        return Event(whole, func(self.part), self.value)

    def with_value(self, func):
        """Returns a new event with the function f applies to the event value."""
        return Event(self.whole, self.part, func(self.value))

    def has_onset(self) -> bool:
        """Test whether the event contains the onset, i.e that
        the beginning of the part is the same as that of the whole timespan."""
        return self.whole and self.whole.begin == self.part.begin

    def __repr__(self) -> str:
        return f"Event({repr(self.whole)}, {repr(self.part)}, {repr(self.value)})"

    def __str__(self) -> str:
        return f"({self.whole}, {self.part}, {pformat(self.value)})"

    def __eq__(self, other) -> bool:
        if isinstance(other, Event):
            return (
                self.whole == other.whole
                and self.part == other.part
                and self.value == other.value
            )
        return False

    def __le__(self, other) -> bool:
        return (
            self.whole
            and other.whole
            and self.whole <= other.whole
            and self.part
            and other.part
            and self.part <= other.part
            and self.value
            and other.value
            and self.value <= other.value
        )


class Pattern:
    """
    Pattern class, representing discrete and continuous events as a
    function of time.
    """

    def __init__(self, query):
        self.query = query

    def split_queries(self):
        """Splits queries at cycle boundaries. This makes some calculations
        easier to express, as all events are then constrained to happen within
        a cycle."""

        def query(span) -> list:
            return concat([self.query(subspan) for subspan in span.span_cycles()])

        return Pattern(query)

    def with_query_span(self, func):
        """Returns a new pattern, with the function applied to the timespan of the query."""
        return Pattern(lambda span: self.query(func(span)))

    def with_query_time(self, func):
        """Returns a new pattern, with the function applied to both the begin
        and end of the the query timespan."""
        return Pattern(lambda span: self.query(span.with_time(func)))

    def with_event_span(self, func):
        """Returns a new pattern, with the function applied to each event
        timespan."""

        def query(span):
            return [event.with_span(func) for event in self.query(span)]

        return Pattern(query)

    def with_event_time(self, func):
        """Returns a new pattern, with the function applied to both the begin
        and end of each event timespan.
        """
        return self.with_event_span(lambda span: span.with_time(func))

    def with_value(self, func):
        """Returns a new pattern, with the function applied to the value of
        each event. It has the alias 'fmap'.

        """

        def query(span):
            return [event.with_value(func) for event in self.query(span)]

        return Pattern(query)

    # alias
    fmap = with_value

    def _filter_events(self, event_test):
        return Pattern(lambda span: list(filter(event_test, self.query(span))))

    def _filter_values(self, value_test):
        return Pattern(
            lambda span: list(
                filter(lambda event: value_test(event.value), self.query(span))
            )
        )

    def onsets_only(self):
        """Returns a new pattern that will only return events where the start
        of the 'whole' timespan matches the start of the 'part'
        timespan, i.e. the events that include their 'onset'.
        """
        return self._filter_events(Event.has_onset)

    # applyPatToPatLeft :: Pattern (a -> b) -> Pattern a -> Pattern b
    # applyPatToPatLeft pf px = Pattern q
    #    where q st = catMaybes $ concatMap match $ query pf st
    #            where
    #              match ef = map (withFX ef) (query px $ st {arc = wholeOrPart ef})
    #              withFX ef ex = do let whole' = whole ef
    #                                part' <- subArc (part ef) (part ex)
    #                                return (Event (combineContexts [context ef, context ex]) whole' part' (value ef $ value ex))

    def _app_whole(self, whole_func, pat_val):
        """
        Assumes self is a pattern of functions, and given a function to
        resolve wholes, applies a given pattern of values to that
        pattern of functions.
        """

        def query(span):
            event_funcs = self.query(span)
            event_vals = pat_val.query(span)

            def apply(event_func, event_val):
                s = event_func.part.intersection(event_val.part)
                if s == None:
                    return None
                return Event(
                    whole_func(event_func.whole, event_val.whole),
                    s,
                    event_func.value(event_val.value),
                )

            return concat(
                [
                    remove_nones(
                        [apply(event_func, event_val) for event_val in event_vals]
                    )
                    for event_func in event_funcs
                ]
            )

        return Pattern(query)

    # A bit more complicated than this..
    def app_both(self, pat_val):
        """Tidal's <*>"""

        def whole_func(span_a, span_b):
            if span_a == None or span_b == None:
                return None
            return span_a.intersection_e(span_b)

        return self._app_whole(whole_func, pat_val)

    def app_left(self, pat_val):
        pat_func = self

        def query(span):
            events = []
            for event_func in pat_func.query(span):
                event_vals = pat_val.query(event_func.part)
                for event_val in event_vals:
                    new_whole = event_func.whole
                    new_part = event_func.part.intersection_e(event_val.part)
                    new_value = event_func.value(event_val.value)
                    events.append(Event(new_whole, new_part, new_value))
            return events

        return Pattern(query)

    def app_right(self, pat_val):
        pat_func = self

        def query(span):
            events = []
            for event_val in pat_val.query(span):
                event_funcs = pat_func.query(event_val.part)
                for event_func in event_funcs:
                    new_whole = event_val.whole
                    new_part = event_func.part.intersection_e(event_val.part)
                    new_value = event_func.value(event_val.value)
                    events.append(Event(new_whole, new_part, new_value))
            return events

        return Pattern(query)

    def __add__(self, other):
        return self.fmap(lambda x: lambda y: x + y).app_left(reify(other))

    def __radd__(self, other):
        return self.fmap(lambda x: lambda y: y + x).app_left(reify(other))

    def __sub__(self, other):
        return self.fmap(lambda x: lambda y: x - y).app_left(reify(other))

    def __rsub__(self, other):
        return self.fmap(lambda x: lambda y: y - x).app_left(reify(other))

    def __mul__(self, other):
        return self.fmap(lambda x: lambda y: x * y).app_left(reify(other))

    def __rmul__(self, other):
        return self.fmap(lambda x: lambda y: y * x).app_left(reify(other))

    def __truediv__(self, other):
        return self.fmap(lambda x: lambda y: x / y).app_left(reify(other))

    def __rtruediv__(self, other):
        return self.fmap(lambda x: lambda y: y / x).app_left(reify(other))

    def __floordiv__(self, other):
        return self.fmap(lambda x: lambda y: x // y).app_left(reify(other))

    def __rfloordiv__(self, other):
        return self.fmap(lambda x: lambda y: y // x).app_left(reify(other))

    def __mod__(self, other):
        return self.fmap(lambda x: lambda y: x % y).app_left(reify(other))

    def __rmod__(self, other):
        return self.fmap(lambda x: lambda y: y % x).app_left(reify(other))

    def __pow__(self, other):
        return self.fmap(lambda x: lambda y: x**y).app_left(reify(other))

    def __rpow__(self, other):
        return self.fmap(lambda x: lambda y: y**x).app_left(reify(other))

    def union(self, other):
        return self.fmap(lambda x: lambda y: {**x, **y}).app_left(other)

    def __rshift__(self, other):
        """Overrides the >> operator to support combining patterns of
        dictionaries (AKA 'control patterns'). Produces the union of
        two patterns of dictionaries, with values from right replacing
        any with the same name from the left
        """
        return self.union(other)

    def __lshift__(self, other):
        """Like >>, but matching values from left replace those on the right"""
        return self.fmap(lambda x: lambda y: {**y, **x}).app_left(other)

    def _bind_whole(self, choose_whole, func):
        pat_val = self

        def query(span):
            def withWhole(a, b):
                return Event(choose_whole(a.whole, b.whole), b.part, b.value)

            def match(a):
                return [withWhole(a, b) for b in func(a.value).query(a.part)]

            return concat([match(ev) for ev in pat_val.query(span)])

        return Pattern(query)

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
            return a

        return self._bind_whole(whole_func, func)

    def inner_join(self):
        """Flattens a pattern of patterns into a pattern, where wholes are
        taken from inner events."""
        return self.inner_bind(id)

    def outer_bind(self, func):
        def whole_func(a, b):
            return b

        return self._bind_whole(whole_func, func)

    def outer_join(self):
        """Flattens a pattern of patterns into a pattern, where wholes are
        taken from outer events."""
        return self.outer_bind(id)

    def _patternify(method):
        def patterned(self, *args):
            pat_arg = sequence(*args)
            return pat_arg.fmap(lambda arg: method(self, arg)).outer_join()

        return patterned

    def _fast(self, factor):
        """Speeds up a pattern by the given factor"""
        fastQuery = self.with_query_time(lambda t: t * factor)
        fastEvents = fastQuery.with_event_time(lambda t: t / factor)
        return fastEvents

    fast = _patternify(_fast)

    def _slow(self, factor):
        """Slow slows down a pattern"""
        return self._fast(1 / factor)

    slow = _patternify(_slow)

    def _early(self, offset):
        """Equivalent of Tidal's <~ operator"""
        offset = Fraction(offset)
        return self.with_query_time(lambda t: t + offset).with_event_time(
            lambda t: t - offset
        )

    early = _patternify(_early)

    def _late(self, offset):
        """Equivalent of Tidal's ~> operator"""
        return self._early(0 - offset)

    late = _patternify(_late)

    def when(self, binary_pat, func):
        binary_pat = sequence(binary_pat)
        true_pat = binary_pat._filter_values(id)
        false_pat = binary_pat._filter_values(lambda val: not val)
        with_pat = true_pat.fmap(lambda _: lambda y: y).app_right(func(self))
        without_pat = false_pat.fmap(lambda _: lambda y: y).app_right(self)
        return stack(with_pat, without_pat)

    def off(self, time_pat, func):
        return stack(self, func(self.early(time_pat)))

    def every(self, n, func):
        pats = [func(self)] + ([self] * (n - 1))
        return slowcat(*pats)

    def append(self, other):
        return fastcat(self, other)

    def rev(self):
        def query(span):
            cycle = span.begin.sam()
            next_cycle = span.begin.next_sam()

            def reflect(to_reflect):
                reflected = to_reflect.with_time(
                    lambda time: cycle + (next_cycle - time)
                )
                (reflected.begin, reflected.end) = (reflected.end, reflected.begin)
                return reflected

            events = self.query(reflect(span))
            return [event.with_span(reflect) for event in events]

        return Pattern(query).split_queries()

    def jux(self, func, by=1):
        by = by / 2

        def elem_or(dict, key, default):
            if key in dict:
                return dict[key]
            return default

        left = self.with_value(
            lambda val: dict(
                list(val.items()) + [("pan", elem_or(val, "pan", 0.5) - by)]
            )
        )
        right = self.with_value(
            lambda val: dict(
                list(val.items()) + [("pan", elem_or(val, "pan", 0.5) + by)]
            )
        )

        return stack(left, func(right))

    def first_cycle(self):
        return sorted(self.query(TimeSpan(Fraction(0), Fraction(1))))

    def superimpose(self, func):
        """
        Play a modified version of a pattern at the same time as the original pattern,
        resulting in two patterns being played at the same time.

        >>> s("bd sn [cp ht] hh").superimpose(lambda p: p.fast(2))
        >>> s("bd sn cp hh").superimpose(lambda p: p.speed(2).early(0.125))

        """
        return stack(self, func(self))

    def layer(self, *list_funcs):
        """
        Layer up multiple functions on one pattern.

        For example, the following will play two versions of the pattern at the
        same time, one reversed and one at twice the speed:

        >>> s("arpy [~ arpy:4]").layer(rev, lambda p: p.fast(2)])

        If you want to include the original version of the pattern in the
        layering, use the `id` function:

        >>> s("arpy [~ arpy:4]").layer(id, rev, lambda p: p.fast(2)])

        """
        return stack(*[func(self) for func in list_funcs])

    def iter(self, n):
        """
        Divides a pattern into a given number of subdivisions, plays the
        subdivisions in order, but increments the starting subdivision each
        cycle.

        The pattern wraps to the first subdivision after the last subdivision is
        played.

        >>> s("bd hh sn cp").iter(4)

        """
        return slowcat(*[self.early(Fraction(i, n)) for i in range(n)])

    def reviter(self, n):
        """
        Same as `iter` but in the other direction.

        >>> s("bd hh sn cp").reviter(4)

        """
        return slowcat(*[self.late(Fraction(i, n)) for i in range(n)])

    def overlay(self, pat):
        """Combine itself with another pattern"""
        return Pattern(lambda span: concat([self.query(span), pat.query(span)]))

    def compress(self, begin, end):
        """Squeeze pattern within the specified time span"""
        begin = Fraction(begin)
        end = Fraction(end)
        if begin > end or end > 1 or begin > 1 or begin < 0 or end < 0:
            return silence()
        return self.fastgap(Fraction(1, end - begin)).late(begin)

    def fastgap(self, factor):
        """
        Similar to `fast` but maintains its cyclic alignment.

        For example, `p.fastgap(2)` would squash the events in pattern `p` into
        the first half of each cycle (and the second halves would be empty).

        The factor should be at least 1.

        """
        if factor <= 0:
            return silence()

        factor_ = max(1, factor)

        def munge_query(t):
            return t.sam() + min(1, factor_ * t.cycle_pos())

        def event_span_func(span):
            begin = span.begin.sam() + Fraction(span.begin - span.begin.sam(), factor_)
            end = span.begin.sam() + Fraction(span.end - span.begin.sam(), factor_)
            return TimeSpan(begin, end)

        def query(span):
            new_span = TimeSpan(munge_query(span.begin), munge_query(span.end))
            if new_span.begin == span.begin.next_sam():
                return []
            return [e.with_span(event_span_func) for e in self.query(new_span)]

        return Pattern(query).split_queries()

    def striate(self, n_pat):
        """
        Cut samples into bits in a similar way to `chop`

        Pattern must be an `s` control pattern, and the resulting pattern will
        contain `begin` and `end` values to be interpreted by the synth
        (SuperDirt, Dirt, etc.)

        """
        return reify(n_pat).fmap(lambda n: self._striate(n)).inner_join()

    def _striate(self, n):
        def merge_sample(samp_range):
            return self.fmap(
                lambda v: {"s": v["s"] if isinstance(v, dict) else v, **samp_range}
            )

        samp_ranges = [dict(begin=i / n, end=(i + 1) / n) for i in range(n)]
        return fastcat(*[merge_sample(r) for r in samp_ranges])

    def segment(self, n):
        """
        Samples the pattern at a rate of `n` events per cycle.

        Useful for turning a continuous pattern into a discrete one.

        >>> rand().segment(4)

        """
        return pure(id).fast(n).app_left(self)

    def range(self, min, max):
        """
        Rescales values to the range [min, max]

        Assumes pattern is numerical, containing unipolar values in the range
        [0, 1].

        """
        return self * (max - min) + min

    def rangex(self, min, max):
        """
        Rescales values to the range [min, max] following an exponential curve

        Assumes pattern is numerical, containing unipolar values in the range
        [0, 1].

        """
        return self.range(math.log(min), math.log(max)).fmap(math.exp)

    def degrade(self, val=0.5, prand=None):
        """
        Randomly removes events from pattern.

        By default, chance is 50% (0.5). You can control control the percentage
        of events that are removed with `val`. With `prand` you can specify a
        different random pattern, must be a numerical 0-1 ranged pattern.

        """
        if not prand:
            prand = rand()
        return self.fmap(lambda a: lambda _: a).app_left(
            prand._filter_values(lambda v: v > val)
        )

    def __repr__(self):
        events = [str(e) for e in self.first_cycle()]
        events_str = ",\n ".join(events).replace("\n", "\n ")
        return f"~[{events_str}] ...~"

    def __eq__(self, other):
        raise NotImplementedError(
            "Patterns cannot be compared. Evaluate them with `.first_cycle()` or similar"
        )


def pure(value):
    """Returns a pattern that repeats the given value once per cycle"""

    def query(span):
        return [
            Event(Fraction(subspan.begin).whole_cycle(), subspan, value)
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
    """Pile up patterns"""
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
        return (x, 1)
    else:
        return (pure(x), 1)


def sequence(*args):
    return _sequence_count(args)[0]


def polymeter(*args, steps=None):
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
            pats.append(seq[0]._fast(Fraction(steps) / Fraction(seq[1])))
    return stack(*pats)


# alias
pm = polymeter


def polyrhythm(*xs):
    seqs = [sequence(x) for x in xs]

    if len(seqs) == 0:
        return silence()

    return stack(seqs)


# alias
pr = polyrhythm


def reify(x):
    if not isinstance(x, Pattern):
        return pure(x)
    return x


# Randomness
RANDOM_CONSTANT = 2**29
RANDOM_CYCLES_LENGTH = 300


def xorwise(x: int) -> int:
    """
    Xorshift RNG

    cf. George Marsaglia (2003). "Xorshift RNGs". Journal of Statistical Software 8:14.
    https://www.jstatsoft.org/article/view/v008i14

    """
    a = (x << 13) ^ x
    b = (a >> 17) ^ a
    return (b << 5) ^ b


def time_to_int_seed(a: float) -> int:
    """
    Stretch RANDOM_CYCLES_LENGTH cycles over the range of [0, RANDOM_CONSTANT)
    then apply the xorshift algorithm.

    """
    return xorwise(math.trunc((a / RANDOM_CYCLES_LENGTH) * RANDOM_CONSTANT))


def int_seed_to_rand(a: int) -> float:
    return (a % RANDOM_CONSTANT) / RANDOM_CONSTANT


def time_to_rand(a):
    return int_seed_to_rand(time_to_int_seed(a))


# Signals

silence = lambda: Pattern(lambda _: [])


def signal(func):
    def query(span):
        return [Event(None, span, func(span.midpoint()))]

    return Pattern(query)


sine2 = lambda: signal(lambda t: math.sin(math.pi * 2 * t))
sine = lambda: signal(lambda t: (math.sin(math.pi * 2 * t) + 1) / 2)

cosine2 = lambda: sine2().early(0.25)
cosine = lambda: sine().early(0.25)

saw2 = lambda: signal(lambda t: (t % 1) * 2)
saw = lambda: signal(lambda t: t % 1)

isaw2 = lambda: signal(lambda t: (1 - (t % 1)) * 2)
isaw = lambda: signal(lambda t: 1 - (t % 1))

tri2 = lambda: fastcat(isaw2(), saw2())
tri = lambda: fastcat(isaw(), saw())

square2 = lambda: signal(lambda t: (math.floor((t * 2) % 2) * 2) - 1)
square = lambda: signal(lambda t: math.floor((t * 2) % 2))


def rand():
    """
    Generate a continuous pattern of pseudo-random numbers between `0` and `1`.

    >>> rand().segment(4)

    """
    return signal(time_to_rand)


def irand(n: int):
    """
    Generate a pattern of pseudo-random whole numbers between `0` to `n-1` inclusive.

    e.g this generates a pattern of 8 events per cycle, with values ranging from
    0 to 15 inclusive.

    >>> irand(16).segment(8)

    """
    return signal(lambda t: math.floor(time_to_rand(t) * n))


def _perlin_with(p: Pattern) -> Pattern:
    """
    1D Perlin noise. Takes a pattern as the RNG's "input" for Perlin noise, instead of
    automatically using the cycle count.

    """
    pa = p.fmap(math.floor)
    pb = p.fmap(lambda v: math.floor(v) + 1)
    smoother_step = lambda x: 6.0 * x**5 - 15.0 * x**4 + 10.0 * x**3
    interp = lambda x: lambda a: lambda b: a + smoother_step(x) * (b - a)
    return (
        (p - pa)
        .fmap(interp)
        .app_both(pa.fmap(time_to_rand))
        .app_both(pb.fmap(time_to_rand))
    )


def perlin(p: Optional[Pattern] = None) -> Pattern:
    """
    1D Perlin (smooth) noise, works like rand but smoothly moves between random
    values each cycle.

    """
    if not p:
        p = signal(id)
    return _perlin_with(p)


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


@partial_decorator
def jux(arg, pat):
    return pat.jux(arg)


@partial_decorator
def union(pat_a, pat_b):
    return pat_b.union(pat_a)


def rev(pat):
    return pat.rev()


## Combinators


def run(n):
    return sequence(list(range(n)))


def scan(n):
    return slowcat(*[run(k) for k in range(1, n + 1)])


def timecat(*time_pat_tuples):
    """
    Like `fastcat` except that you provide proportionate sizes of the
    patterns to each other for when they're concatenated into one cycle.

    The larger the value in the list, the larger relative size the pattern
    takes in the final loop. If all values are equal then this is equivalent
    to `fastcat`.

    >>> timecat((1, s("bd*4")), (1, s("hh27*8")))

    """
    total = sum(Fraction(time) for time, _ in time_pat_tuples)
    arranged = []
    accum = Fraction(0)
    for time, pat in time_pat_tuples:
        arranged.append((accum, accum + Fraction(time), pat))
        accum += time
    return stack(
        *[
            pat.compress(Fraction(s, total), Fraction(e, total))
            for s, e, pat in arranged
        ]
    )


def chooseby(pat, *vals):
    """
    Randomly picks an element from the given list

    Values are samples using the 0-1 ranged numerical pattern `pat`.
    """
    return pat.range(0, len(vals)).fmap(lambda v: vals[math.floor(v)])


def choose(*vals):
    """Randomly picks an element from the given list"""
    return chooseby(rand(), *vals)


def wchooseby(pat, *pairs):
    """
    Like @choose@, but works on an a list of tuples of values and weights

    Values are samples using the 0-1 ranged numerical pattern `pat`.

    """
    values, weights = list(zip(*pairs))
    cweights = list(accumulate(w for _, w in pairs))
    total = sum(weights)

    def match(r):
        if r < 0 or r > 1:
            raise ValueError(
                "value from random pattern used by `wchooseby` is outside 0-1 range"
            )
        indices = [i for i, c in enumerate(cweights) if c >= r * total]
        return values[indices[0]]

    return pat.fmap(match)


def wchoose(*vals):
    """Like @choose@, but works on an a list of tuples of values and weights"""
    return wchooseby(rand(), *vals)
