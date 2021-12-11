"""
Experiment: porting Tidalcycles to Python 3.x.
"""

from __future__ import annotations
import logging


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

    # printing the pattern
    logging.debug("\n== TEST PATTERN ==\n")
    logging.debug('Like: "hello world" (over two cycles)')
    pattern_pretty_printing(
        pattern=c,
        query_span=TimeSpan(Time(0), Time(2)))

    # printing the pattern with fast
    logging.debug("\n== SAME BUT FASTER==\n")
    logging.debug('Like: fast 4 "hello world"')
    pattern_pretty_printing(
        pattern=c._fast(2),
        query_span=TimeSpan(Time(0), Time(1)))

    # printing the pattern with patterned fast
    logging.debug("\n== PATTERNS OF FAST OF PATTERNS==\n")
    logging.debug('Like: fast "2 4" "hello world"')
    pattern_pretty_printing(
        pattern=c.fast(S.fastcat([F.pure(2), F.pure(4)])),
        query_span=TimeSpan(Time(0), Time(1)))

    # printing the pattern with stack
    logging.debug("\n== STACK ==\n")
    pattern_pretty_printing(
        pattern=d,
        query_span=TimeSpan(Time(0), Time(1)))

    # printing the pattern with late
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
