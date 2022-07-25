from vortex.pattern import TimeSpan, Fraction, pure, stack


def assert_equal_patterns(input, expected, span=None):
    """Assert patterns by queyring them and comparing events"""
    if not span:
        span = TimeSpan(Fraction(0), Fraction(1))
    assert input.query(span) == expected.query(span)


def test_superimpose():
    assert_equal_patterns(
        pure("bd").superimpose(lambda p: p.fast(3)),
        stack(pure("bd"), pure("bd").fast(3)),
    )
