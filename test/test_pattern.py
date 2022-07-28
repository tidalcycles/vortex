from vortex.control import s
from vortex.pattern import (
    Event,
    Fraction,
    TimeSpan,
    fastcat,
    irand,
    pure,
    rand,
    rev,
    slowcat,
    stack,
    timecat,
)


def assert_equal_patterns(input, expected, span=None):
    """Assert patterns by queyring them and comparing events"""
    if not span:
        span = TimeSpan(0, 1)
    assert sorted(input.query(span)) == sorted(expected.query(span))


def test_add():
    assert_equal_patterns(pure(3) + 2, pure(5))
    assert_equal_patterns(3 + pure(5), pure(8))


def test_sub():
    assert_equal_patterns(pure(3) - 1.5, pure(1.5))
    assert_equal_patterns(3 - pure(1), pure(2))


def test_mul():
    assert_equal_patterns(pure(3) * 2, pure(6))
    assert_equal_patterns(10 * pure(3), pure(30))


def test_truediv():
    assert_equal_patterns(pure(3) / 0.5, pure(6))
    assert_equal_patterns(3 / pure(2), pure(3 / 2))


def test_floordiv():
    assert_equal_patterns(pure(3) // 2, pure(1))
    assert_equal_patterns(3 // pure(5), pure(0))


def test_mod():
    assert_equal_patterns(pure(7) % 5, pure(2))
    assert_equal_patterns(3 % pure(2), pure(1))


def test_pow():
    assert_equal_patterns(pure(3) ** 2, pure(9))
    assert_equal_patterns(2 ** pure(4), pure(16))


def test_superimpose():
    assert_equal_patterns(
        pure("bd").superimpose(lambda p: p.fast(3)),
        stack(pure("bd"), pure("bd").fast(3)),
    )


def test_layer():
    basepat = fastcat(pure("bd"), pure("sd"))
    assert_equal_patterns(
        basepat.layer(rev, lambda p: p.fast(2)),
        stack(basepat.rev(), basepat.fast(2)),
    )


def test_iter():
    assert_equal_patterns(
        fastcat(pure("bd"), pure("hh"), pure("sn"), pure("cp")).iter(4),
        slowcat(
            fastcat(pure("bd"), pure("hh"), pure("sn"), pure("cp")),
            fastcat(pure("hh"), pure("sn"), pure("cp"), pure("bd")),
            fastcat(pure("sn"), pure("cp"), pure("bd"), pure("hh")),
            fastcat(pure("cp"), pure("bd"), pure("hh"), pure("sn")),
        ),
        span=TimeSpan(0, 4),
    )


def test_reviter():
    assert_equal_patterns(
        fastcat(pure("bd"), pure("hh"), pure("sn"), pure("cp")).reviter(4),
        slowcat(
            fastcat(pure("bd"), pure("hh"), pure("sn"), pure("cp")),
            fastcat(pure("cp"), pure("bd"), pure("hh"), pure("sn")),
            fastcat(pure("sn"), pure("cp"), pure("bd"), pure("hh")),
            fastcat(pure("hh"), pure("sn"), pure("cp"), pure("bd")),
        ),
        span=TimeSpan(0, 4),
    )


def test_overlay():
    assert_equal_patterns(
        pure("bd").fast(2).overlay(pure("sd")), stack(pure("bd").fast(2), pure("sd"))
    )


def test_fastgap():
    assert fastcat(pure("bd"), pure("sd")).fastgap(4).first_cycle() == [
        Event(TimeSpan(0, 1 / 8), TimeSpan(0, 1 / 8), "bd"),
        Event(TimeSpan(1 / 8, 1 / 4), TimeSpan(1 / 8, 1 / 4), "sd"),
    ]


def test_compress():
    assert fastcat(pure("bd"), pure("sd")).compress(
        Fraction(1, 4), Fraction(3, 4)
    ).first_cycle() == [
        Event(TimeSpan(1 / 4, 1 / 2), TimeSpan(1 / 4, 1 / 2), "bd"),
        Event(TimeSpan(1 / 2, 3 / 4), TimeSpan(1 / 2, 3 / 4), "sd"),
    ]


def test_compress_invalid_span():
    assert pure("bd").fast(4).compress(1, 2).first_cycle() == []
    assert pure("bd").fast(4).compress(-1, 0).first_cycle() == []


def test_compress_floats():
    assert fastcat(pure("bd"), pure("sd")).compress(1 / 4, 3 / 4).first_cycle() == [
        Event(TimeSpan(1 / 4, 1 / 2), TimeSpan(1 / 4, 1 / 2), "bd"),
        Event(TimeSpan(1 / 2, 3 / 4), TimeSpan(1 / 2, 3 / 4), "sd"),
    ]


def test_timecat():
    assert timecat((3, pure("bd").fast(4)), (1, pure("hh").fast(8))).first_cycle() == [
        Event(TimeSpan(0, (3 / 16)), TimeSpan(0, (3 / 16)), "bd"),
        Event(TimeSpan((3 / 16), 3 / 8), TimeSpan((3 / 16), 3 / 8), "bd"),
        Event(TimeSpan(3 / 8, (9 / 16)), TimeSpan(3 / 8, (9 / 16)), "bd"),
        Event(TimeSpan((9 / 16), 3 / 4), TimeSpan((9 / 16), 3 / 4), "bd"),
        Event(TimeSpan(3 / 4, (25 / 32)), TimeSpan(3 / 4, (25 / 32)), "hh"),
        Event(TimeSpan((25 / 32), (13 / 16)), TimeSpan((25 / 32), (13 / 16)), "hh"),
        Event(TimeSpan((13 / 16), (27 / 32)), TimeSpan((13 / 16), (27 / 32)), "hh"),
        Event(TimeSpan((27 / 32), 7 / 8), TimeSpan((27 / 32), 7 / 8), "hh"),
        Event(TimeSpan(7 / 8, (29 / 32)), TimeSpan(7 / 8, (29 / 32)), "hh"),
        Event(TimeSpan((29 / 32), (15 / 16)), TimeSpan((29 / 32), (15 / 16)), "hh"),
        Event(TimeSpan((15 / 16), (31 / 32)), TimeSpan((15 / 16), (31 / 32)), "hh"),
        Event(TimeSpan((31 / 32), 1), TimeSpan((31 / 32), 1), "hh"),
    ]


def test_striate():
    assert fastcat(s("bd"), s("sd")).striate(4).first_cycle() == [
        Event(
            TimeSpan(Fraction(0, 1), Fraction(1, 1)),
            TimeSpan(Fraction(0, 1), Fraction(1, 8)),
            {"s": "bd", "begin": 0.0, "end": 0.25},
        ),
        Event(
            TimeSpan(Fraction(0, 1), Fraction(1, 1)),
            TimeSpan(Fraction(1, 8), Fraction(1, 4)),
            {"s": "sd", "begin": 0.0, "end": 0.25},
        ),
        Event(
            TimeSpan(Fraction(0, 1), Fraction(1, 1)),
            TimeSpan(Fraction(1, 4), Fraction(3, 8)),
            {"s": "bd", "begin": 0.25, "end": 0.5},
        ),
        Event(
            TimeSpan(Fraction(0, 1), Fraction(1, 1)),
            TimeSpan(Fraction(3, 8), Fraction(1, 2)),
            {"s": "sd", "begin": 0.25, "end": 0.5},
        ),
        Event(
            TimeSpan(Fraction(0, 1), Fraction(1, 1)),
            TimeSpan(Fraction(1, 2), Fraction(5, 8)),
            {"s": "bd", "begin": 0.5, "end": 0.75},
        ),
        Event(
            TimeSpan(Fraction(0, 1), Fraction(1, 1)),
            TimeSpan(Fraction(5, 8), Fraction(3, 4)),
            {"s": "sd", "begin": 0.5, "end": 0.75},
        ),
        Event(
            TimeSpan(Fraction(0, 1), Fraction(1, 1)),
            TimeSpan(Fraction(3, 4), Fraction(7, 8)),
            {"s": "bd", "begin": 0.75, "end": 1.0},
        ),
        Event(
            TimeSpan(Fraction(0, 1), Fraction(1, 1)),
            TimeSpan(Fraction(7, 8), Fraction(1, 1)),
            {"s": "sd", "begin": 0.75, "end": 1.0},
        ),
    ]


def test_rand():
    assert rand().segment(4).first_cycle() == [
        Event(TimeSpan(0, 1 / 4), TimeSpan(0, 1 / 4), 0.3147844299674034),
        Event(TimeSpan(1 / 4, 1 / 2), TimeSpan(1 / 4, 1 / 2), 0.6004995740950108),
        Event(TimeSpan(1 / 2, 3 / 4), TimeSpan(1 / 2, 3 / 4), 0.1394200474023819),
        Event(TimeSpan(3 / 4, 1), TimeSpan(3 / 4, 1), 0.3935417253524065),
    ]


def test_irand():
    assert irand(8).segment(4).first_cycle() == [
        Event(TimeSpan(0, 1 / 4), TimeSpan(0, 1 / 4), 2),
        Event(TimeSpan(1 / 4, 1 / 2), TimeSpan(1 / 4, 1 / 2), 4),
        Event(TimeSpan(1 / 2, 3 / 4), TimeSpan(1 / 2, 3 / 4), 1),
        Event(TimeSpan(3 / 4, 1), TimeSpan(3 / 4, 1), 3),
    ]
