"""
Experiment: porting Tidalcycles to Python 3.x.
"""

from __future__ import annotations

import logging

from vortex.pattern import *


def pattern_pretty_printing(pattern: Pattern, query_span: TimeSpan) -> None:
    """Better formatting for logging.debuging Tidal Patterns"""
    for event in pattern.query(query_span):

        logging.debug(event)


if __name__ == "__main__":
    # Simple patterns
    a = pure("hello")
    b = pure("world")
    c = fastcat(a, b)
    d = stack(a, b)

    # printing the pattern
    logging.debug("\n== TEST PATTERN ==\n")
    logging.debug('Like: "hello world" (over two cycles)')
    pattern_pretty_printing(pattern=c, query_span=TimeSpan(0, 2))

    # printing the pattern with fast
    logging.debug("\n== SAME BUT FASTER==\n")
    logging.debug('Like: fast 4 "hello world"')
    pattern_pretty_printing(pattern=c._fast(2), query_span=TimeSpan(0, 1))

    # printing the pattern with patterned fast
    logging.debug("\n== PATTERNS OF FAST OF PATTERNS==\n")
    logging.debug('Like: fast "2 4" "hello world"')
    pattern_pretty_printing(pattern=c.fast(fastcat(2, 4)), query_span=TimeSpan(0, 1))

    # printing the pattern with stack
    logging.debug("\n== STACK ==\n")
    pattern_pretty_printing(pattern=d, query_span=TimeSpan(0, 1))

    # printing the pattern with late
    logging.debug("\n== LATE ==\n")
    pattern_pretty_printing(pattern=c.late(0.5), query_span=TimeSpan(0, 1))

    # Apply pattern of values to a pattern of functions
    logging.debug("\n== APPLICATIVE ==\n")
    x = fastcat(pure(lambda x: x + 1), pure(lambda x: x + 4))
    y = fastcat(3, 4, 5)
    z = x.app(y)
    pattern_pretty_printing(pattern=z, query_span=TimeSpan(0, 1))

    # Add number patterns together
    logging.debug("\n== ADDITION ==\n")
    numbers = fastcat(*[pure(v) for v in [2, 3, 4, 5]])
    more_numbers = fastcat(pure(10), pure(100))
    pattern_pretty_printing(pattern=numbers + more_numbers, query_span=TimeSpan(0, 1))

    logging.debug("\n== EMBEDDED SEQUENCES ==\n")
    # sequence([0,1,[2, [3, 4]]]) is the same as "[0 1 [2 [3 4]]]" in mininotation
    pattern_pretty_printing(
        pattern=sequence(0, 1, [2, [3, 4]]), query_span=TimeSpan(0, 1)
    )

    logging.debug("\n== Polyrhythm ==\n")
    pattern_pretty_printing(
        pattern=polyrhythm([0, 1, 2, 3], [20, 30]), query_span=TimeSpan(0, 1)
    )

    logging.debug("\n== Polyrhythm with fewer steps ==\n")
    pattern_pretty_printing(
        pattern=polyrhythm([0, 1, 2, 3], [20, 30], steps=2), query_span=TimeSpan(0, 1)
    )

    logging.debug("\n== Polymeter ==\n")
    pattern_pretty_printing(
        pattern=polymeter([0, 1, 2], [20, 30]), query_span=TimeSpan(0, 1)
    )

    logging.debug("\n== Polymeter with embedded polyrhythm ==\n")
    pattern_pretty_printing(
        pattern=pm(pr([100, 200, 300, 400], [0, 1]), [20, 30]),
        query_span=TimeSpan(0, 1),
    )

    logging.debug("\n== Every with partially applied 'fast' ==\n")
    pattern_pretty_printing(pattern=c.every(3, fast(2)), query_span=TimeSpan(0, 1))
