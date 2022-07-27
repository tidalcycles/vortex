from vortex.pattern import (
    Event,
    TimeSpan,
    Fraction,
    fastcat,
    pure,
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
