import math
from itertools import groupby

from vortex.control import s, speed
from vortex.pattern import (
    Event,
    TimeSpan,
    choose,
    choose_by,
    choose_cycle,
    fast,
    fastcat,
    irand,
    perlin,
    pure,
    rand,
    randcat,
    rev,
    saw,
    slowcat,
    stack,
    timecat,
    wchoose,
    wchoose_by,
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


def test_fastgap():
    assert fastcat(pure("bd"), pure("sd")).fastgap(4).first_cycle() == [
        Event(TimeSpan(0, 1 / 8), TimeSpan(0, 1 / 8), "bd"),
        Event(TimeSpan(1 / 8, 1 / 4), TimeSpan(1 / 8, 1 / 4), "sd"),
    ]


def test_compress():
    assert fastcat(pure("bd"), pure("sd")).compress(1 / 4, 3 / 4).first_cycle() == [
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
    assert s(fastcat("bd", "sd")).striate(4).first_cycle() == [
        Event(
            TimeSpan(0, 1 / 8),
            TimeSpan(0, 1 / 8),
            {"s": "bd", "begin": 0.0, "end": 0.25},
        ),
        Event(
            TimeSpan(1 / 8, 1 / 4),
            TimeSpan(1 / 8, 1 / 4),
            {"s": "sd", "begin": 0.0, "end": 0.25},
        ),
        Event(
            TimeSpan(1 / 4, 3 / 8),
            TimeSpan(1 / 4, 3 / 8),
            {"s": "bd", "begin": 0.25, "end": 0.5},
        ),
        Event(
            TimeSpan(3 / 8, 1 / 2),
            TimeSpan(3 / 8, 1 / 2),
            {"s": "sd", "begin": 0.25, "end": 0.5},
        ),
        Event(
            TimeSpan(1 / 2, 5 / 8),
            TimeSpan(1 / 2, 5 / 8),
            {"s": "bd", "begin": 0.5, "end": 0.75},
        ),
        Event(
            TimeSpan(5 / 8, 3 / 4),
            TimeSpan(5 / 8, 3 / 4),
            {"s": "sd", "begin": 0.5, "end": 0.75},
        ),
        Event(
            TimeSpan(3 / 4, 7 / 8),
            TimeSpan(3 / 4, 7 / 8),
            {"s": "bd", "begin": 0.75, "end": 1.0},
        ),
        Event(
            TimeSpan(7 / 8, 1),
            TimeSpan(7 / 8, 1),
            {"s": "sd", "begin": 0.75, "end": 1.0},
        ),
    ]


def test_range():
    assert_equal_patterns(saw().range(2, 7), saw() * (7 - 2) + 2)


def test_rangex():
    assert_equal_patterns(
        saw().rangex(2, 7), saw().range(math.log(2), math.log(7)).fmap(math.exp)
    )


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


def test_perlin():
    assert perlin().segment(4).first_cycle() == [
        Event(TimeSpan(0, 1 / 4), TimeSpan(0, 1 / 4), 0.008311405901167745),
        Event(TimeSpan(1 / 4, 1 / 2), TimeSpan(1 / 4, 1 / 2), 0.1424947878645071),
        Event(TimeSpan(1 / 2, 3 / 4), TimeSpan(1 / 2, 3 / 4), 0.3752773577048174),
        Event(TimeSpan(3 / 4, 1), TimeSpan(3 / 4, 1), 0.5094607396681567),
    ]


def test_perlin_with():
    assert perlin(saw() * 4).segment(2).first_cycle() == [
        Event(TimeSpan(0, 1 / 2), TimeSpan(0, 1 / 2), 0.5177721455693245),
        Event(TimeSpan(1 / 2, 1), TimeSpan(1 / 2, 1), 0.8026083502918482),
    ]


def test_choose():
    assert choose("a", "b", "c").segment(4).first_cycle() == [
        Event(TimeSpan(0, 1 / 4), TimeSpan(0, 1 / 4), "a"),
        Event(TimeSpan(1 / 4, 1 / 2), TimeSpan(1 / 4, 1 / 2), "b"),
        Event(TimeSpan(1 / 2, 3 / 4), TimeSpan(1 / 2, 3 / 4), "a"),
        Event(TimeSpan(3 / 4, 1), TimeSpan(3 / 4, 1), "b"),
    ]


def test_choose_by():
    assert choose_by(perlin(), *range(8)).segment(4).first_cycle() == [
        Event(TimeSpan(0, 1 / 4), TimeSpan(0, 1 / 4), 0),
        Event(TimeSpan(1 / 4, 1 / 2), TimeSpan(1 / 4, 1 / 2), 1),
        Event(TimeSpan(1 / 2, 3 / 4), TimeSpan(1 / 2, 3 / 4), 3),
        Event(TimeSpan(3 / 4, 1), TimeSpan(3 / 4, 1), 4),
    ]


def test_choose_distribution():
    values = [e.value for e in choose("a", "b", "c", "d").segment(100).first_cycle()]
    values_groupedby_count = {k: len(list(v)) for k, v in groupby(sorted(values))}
    # Check recurrence of values with uniform random distribution (each item should be around 25~)
    assert values_groupedby_count == {"a": 23, "b": 30, "c": 24, "d": 23}


def test_wchoose():
    assert wchoose(("a", 1), ("e", 0.5), ("g", 2), ("c", 1)).segment(
        4
    ).first_cycle() == [
        Event(TimeSpan(0, 1 / 4), TimeSpan(0, 1 / 4), "e"),
        Event(TimeSpan(1 / 4, 1 / 2), TimeSpan(1 / 4, 1 / 2), "g"),
        Event(TimeSpan(1 / 2, 3 / 4), TimeSpan(1 / 2, 3 / 4), "a"),
        Event(TimeSpan(3 / 4, 1), TimeSpan(3 / 4, 1), "g"),
    ]


def test_wchoose_by():
    assert wchoose_by(
        rand().late(100), ("a", 1), ("e", 0.5), ("g", 2), ("c", 1)
    ).segment(4).first_cycle() == [
        Event(TimeSpan(0, 1 / 4), TimeSpan(0, 1 / 4), "a"),
        Event(TimeSpan(1 / 4, 1 / 2), TimeSpan(1 / 4, 1 / 2), "g"),
        Event(TimeSpan(1 / 2, 3 / 4), TimeSpan(1 / 2, 3 / 4), "c"),
        Event(TimeSpan(3 / 4, 1), TimeSpan(3 / 4, 1), "a"),
    ]


def test_wchoose_distribution():
    values = [
        e.value
        for e in wchoose(("a", 1), ("e", 0.5), ("g", 2), ("c", 1))
        .segment(100)
        .first_cycle()
    ]
    values_groupedby_count = {k: len(list(v)) for k, v in groupby(sorted(values))}
    # Check recurrence of values based on weights and uniform random distribution
    # a =~ 20, e =~ 10, g =~ 50, c =~ 20
    assert values_groupedby_count == {"a": 22, "e": 10, "g": 48, "c": 20}


def test_choose_cycle():
    assert choose_cycle("bd", "sd", "hh").query(TimeSpan(0, 10)) == [
        Event(TimeSpan(0, 1), TimeSpan(0, 1), "bd"),
        Event(TimeSpan(1, 2), TimeSpan(1, 2), "sd"),
        Event(TimeSpan(2, 3), TimeSpan(2, 3), "sd"),
        Event(TimeSpan(3, 4), TimeSpan(3, 4), "sd"),
        Event(TimeSpan(4, 5), TimeSpan(4, 5), "hh"),
        Event(TimeSpan(5, 6), TimeSpan(5, 6), "bd"),
        Event(TimeSpan(6, 7), TimeSpan(6, 7), "bd"),
        Event(TimeSpan(7, 8), TimeSpan(7, 8), "sd"),
        Event(TimeSpan(8, 9), TimeSpan(8, 9), "sd"),
        Event(TimeSpan(9, 10), TimeSpan(9, 10), "bd"),
    ]


def test_randcat():
    assert randcat("bd", "sd", "hh").query(TimeSpan(0, 10)) == choose_cycle(
        "bd", "sd", "hh"
    ).query(TimeSpan(0, 10))


def test_degrade():
    assert_equal_patterns(
        pure("sd").fast(8).degrade(), pure("sd").fast(8).degrade_by(0.5, rand())
    )


def test_degrade_by():
    assert pure("sd").fast(8).degrade_by(0.75).first_cycle() == [
        Event(TimeSpan(1 / 8, 1 / 4), TimeSpan(1 / 8, 1 / 4), "sd"),
        Event(TimeSpan(1 / 2, 5 / 8), TimeSpan(1 / 2, 5 / 8), "sd"),
        Event(TimeSpan(3 / 4, 7 / 8), TimeSpan(3 / 4, 7 / 8), "sd"),
    ]


def test_degrade_by_diff_rand():
    assert pure("sd").fast(8).degrade_by(0.5, rand().late(100)).first_cycle() == [
        Event(TimeSpan(1 / 8, 1 / 4), TimeSpan(1 / 8, 1 / 4), "sd"),
        Event(TimeSpan(3 / 8, 1 / 2), TimeSpan(3 / 8, 1 / 2), "sd"),
        Event(TimeSpan(1 / 2, 5 / 8), TimeSpan(1 / 2, 5 / 8), "sd"),
    ]


def test_undegrade():
    assert_equal_patterns(
        pure("sd").fast(8).undegrade(), pure("sd").fast(8).undegrade_by(0.5, rand())
    )


def test_undegrade_by():
    assert pure("sd").fast(8).undegrade_by(0.25).first_cycle() == [
        Event(TimeSpan(0, 1 / 8), TimeSpan(0, 1 / 8), "sd")
    ]


def test_undegrade_by_diff_rand():
    assert pure("sd").fast(8).undegrade_by(0.5, rand().late(100)).first_cycle() == [
        Event(TimeSpan(0, 1 / 8), TimeSpan(0, 1 / 8), "sd"),
        Event(TimeSpan(1 / 4, 3 / 8), TimeSpan(1 / 4, 3 / 8), "sd"),
        Event(TimeSpan(5 / 8, 3 / 4), TimeSpan(5 / 8, 3 / 4), "sd"),
        Event(TimeSpan(3 / 4, 7 / 8), TimeSpan(3 / 4, 7 / 8), "sd"),
        Event(TimeSpan(7 / 8, 1), TimeSpan(7 / 8, 1), "sd"),
    ]


def test_sometimes():
    assert s("bd").fast(8).sometimes(lambda p: p << speed(2)).first_cycle() == [
        Event(TimeSpan(0, 1 / 8), TimeSpan(0, 1 / 8), {"speed": 2, "s": "bd"}),
        Event(TimeSpan(1 / 8, 1 / 4), TimeSpan(1 / 8, 1 / 4), {"s": "bd"}),
        Event(TimeSpan(1 / 4, 3 / 8), TimeSpan(1 / 4, 3 / 8), {"s": "bd"}),
        Event(TimeSpan(3 / 8, 1 / 2), TimeSpan(3 / 8, 1 / 2), {"s": "bd"}),
        Event(TimeSpan(1 / 2, 5 / 8), TimeSpan(1 / 2, 5 / 8), {"s": "bd"}),
        Event(TimeSpan(5 / 8, 3 / 4), TimeSpan(5 / 8, 3 / 4), {"speed": 2, "s": "bd"}),
        Event(TimeSpan(3 / 4, 7 / 8), TimeSpan(3 / 4, 7 / 8), {"s": "bd"}),
        Event(TimeSpan(7 / 8, 1), TimeSpan(7 / 8, 1), {"s": "bd"}),
    ]


def test_sometimes_by():
    assert s("bd").fast(8).sometimes_by(
        0.75, lambda p: p << speed(3)
    ).first_cycle() == [
        Event(TimeSpan(0, 1 / 8), TimeSpan(0, 1 / 8), {"speed": 3, "s": "bd"}),
        Event(TimeSpan(1 / 8, 1 / 4), TimeSpan(1 / 8, 1 / 4), {"s": "bd"}),
        Event(TimeSpan(1 / 4, 3 / 8), TimeSpan(1 / 4, 3 / 8), {"speed": 3, "s": "bd"}),
        Event(TimeSpan(3 / 8, 1 / 2), TimeSpan(3 / 8, 1 / 2), {"speed": 3, "s": "bd"}),
        Event(TimeSpan(1 / 2, 5 / 8), TimeSpan(1 / 2, 5 / 8), {"s": "bd"}),
        Event(TimeSpan(5 / 8, 3 / 4), TimeSpan(5 / 8, 3 / 4), {"speed": 3, "s": "bd"}),
        Event(TimeSpan(3 / 4, 7 / 8), TimeSpan(3 / 4, 7 / 8), {"s": "bd"}),
        Event(TimeSpan(7 / 8, 1), TimeSpan(7 / 8, 1), {"speed": 3, "s": "bd"}),
    ]


def test_sometimes_pre():
    assert s("bd").fast(8).sometimes_pre(fast(2)).first_cycle() == [
        Event(TimeSpan(1 / 16, 1 / 8), TimeSpan(1 / 16, 1 / 8), {"s": "bd"}),
        Event(TimeSpan(1 / 8, 1 / 4), TimeSpan(1 / 8, 1 / 4), {"s": "bd"}),
        Event(TimeSpan(1 / 4, 5 / 16), TimeSpan(1 / 4, 5 / 16), {"s": "bd"}),
        Event(TimeSpan(1 / 4, 3 / 8), TimeSpan(1 / 4, 3 / 8), {"s": "bd"}),
        Event(TimeSpan(5 / 16, 3 / 8), TimeSpan(5 / 16, 3 / 8), {"s": "bd"}),
        Event(TimeSpan(3 / 8, 1 / 2), TimeSpan(3 / 8, 1 / 2), {"s": "bd"}),
        Event(TimeSpan(7 / 16, 1 / 2), TimeSpan(7 / 16, 1 / 2), {"s": "bd"}),
        Event(TimeSpan(1 / 2, 5 / 8), TimeSpan(1 / 2, 5 / 8), {"s": "bd"}),
        Event(TimeSpan(3 / 4, 7 / 8), TimeSpan(3 / 4, 7 / 8), {"s": "bd"}),
        Event(TimeSpan(13 / 16, 7 / 8), TimeSpan(13 / 16, 7 / 8), {"s": "bd"}),
        Event(TimeSpan(7 / 8, 15 / 16), TimeSpan(7 / 8, 15 / 16), {"s": "bd"}),
        Event(TimeSpan(7 / 8, 1), TimeSpan(7 / 8, 1), {"s": "bd"}),
    ]


def test_sometimes_pre_by():
    assert s("bd").fast(8).sometimes_pre_by(0.25, fast(2)).first_cycle() == [
        Event(TimeSpan(1 / 8, 1 / 4), TimeSpan(1 / 8, 1 / 4), {"s": "bd"}),
        Event(TimeSpan(1 / 4, 3 / 8), TimeSpan(1 / 4, 3 / 8), {"s": "bd"}),
        Event(TimeSpan(5 / 16, 3 / 8), TimeSpan(5 / 16, 3 / 8), {"s": "bd"}),
        Event(TimeSpan(3 / 8, 1 / 2), TimeSpan(3 / 8, 1 / 2), {"s": "bd"}),
        Event(TimeSpan(1 / 2, 5 / 8), TimeSpan(1 / 2, 5 / 8), {"s": "bd"}),
        Event(TimeSpan(5 / 8, 3 / 4), TimeSpan(5 / 8, 3 / 4), {"s": "bd"}),
        Event(TimeSpan(3 / 4, 7 / 8), TimeSpan(3 / 4, 7 / 8), {"s": "bd"}),
        Event(TimeSpan(7 / 8, 1), TimeSpan(7 / 8, 1), {"s": "bd"}),
    ]


def test_somecycles():
    assert s("sd").fast(2).somecycles(lambda p: p << speed(3)).query(
        TimeSpan(0, 4)
    ) == [
        Event(TimeSpan(0, 1 / 2), TimeSpan(0, 1 / 2), {"speed": 3, "s": "sd"}),
        Event(TimeSpan(1 / 2, 1), TimeSpan(1 / 2, 1), {"speed": 3, "s": "sd"}),
        Event(TimeSpan(1, 3 / 2), TimeSpan(1, 3 / 2), {"s": "sd"}),
        Event(TimeSpan(3 / 2, 2 / 1), TimeSpan(3 / 2, 2 / 1), {"s": "sd"}),
        Event(TimeSpan(2 / 1, 5 / 2), TimeSpan(2 / 1, 5 / 2), {"speed": 3, "s": "sd"}),
        Event(TimeSpan(5 / 2, 3 / 1), TimeSpan(5 / 2, 3 / 1), {"speed": 3, "s": "sd"}),
        Event(TimeSpan(3 / 1, 7 / 2), TimeSpan(3 / 1, 7 / 2), {"s": "sd"}),
        Event(TimeSpan(7 / 2, 4 / 1), TimeSpan(7 / 2, 4 / 1), {"s": "sd"}),
    ]


def test_somecycles_by():
    assert s("sd").fast(2).somecycles_by(0.03, lambda p: p << speed(3)).query(
        TimeSpan(0, 6)
    ) == [
        Event(TimeSpan(0, 1 / 2), TimeSpan(0, 1 / 2), {"speed": 3, "s": "sd"}),
        Event(TimeSpan(1 / 2, 1), TimeSpan(1 / 2, 1), {"speed": 3, "s": "sd"}),
        Event(TimeSpan(1, 3 / 2), TimeSpan(1, 3 / 2), {"s": "sd"}),
        Event(TimeSpan(3 / 2, 2 / 1), TimeSpan(3 / 2, 2 / 1), {"s": "sd"}),
        Event(TimeSpan(2 / 1, 5 / 2), TimeSpan(2 / 1, 5 / 2), {"s": "sd"}),
        Event(TimeSpan(5 / 2, 3 / 1), TimeSpan(5 / 2, 3 / 1), {"s": "sd"}),
        Event(TimeSpan(3 / 1, 7 / 2), TimeSpan(3 / 1, 7 / 2), {"s": "sd"}),
        Event(TimeSpan(7 / 2, 4 / 1), TimeSpan(7 / 2, 4 / 1), {"s": "sd"}),
        Event(TimeSpan(4 / 1, 9 / 2), TimeSpan(4 / 1, 9 / 2), {"s": "sd"}),
        Event(TimeSpan(9 / 2, 5 / 1), TimeSpan(9 / 2, 5 / 1), {"s": "sd"}),
        Event(TimeSpan(5 / 1, 11 / 2), TimeSpan(5 / 1, 11 / 2), {"s": "sd"}),
        Event(TimeSpan(11 / 2, 6 / 1), TimeSpan(11 / 2, 6 / 1), {"s": "sd"}),
    ]


def test_struct():
    assert pure("bd").struct(fastcat(1, 1, 0, 1, 0, 0, 1, 0)).first_cycle() == [
        Event(TimeSpan(0, 1 / 8), TimeSpan(0, 1 / 8), "bd"),
        Event(TimeSpan(1 / 8, 1 / 4), TimeSpan(1 / 8, 1 / 4), "bd"),
        Event(TimeSpan(3 / 8, 1 / 2), TimeSpan(3 / 8, 1 / 2), "bd"),
        Event(TimeSpan(3 / 4, 7 / 8), TimeSpan(3 / 4, 7 / 8), "bd"),
    ]


def test_mask():
    assert s(fastcat("bd", "sd", "hh", "cp")).mask(
        fastcat(1, 1, 0, 1, 0, 0, 1, 0)
    ).first_cycle() == [
        Event(TimeSpan(0, 1 / 4), TimeSpan(0, 1 / 8), {"s": "bd"}),
        Event(TimeSpan(0, 1 / 4), TimeSpan(1 / 8, 1 / 4), {"s": "bd"}),
        Event(TimeSpan(1 / 4, 1 / 2), TimeSpan(3 / 8, 1 / 2), {"s": "sd"}),
        Event(TimeSpan(3 / 4, 1), TimeSpan(3 / 4, 7 / 8), {"s": "cp"}),
    ]


def test_euclid():
    assert s("sd").euclid(fastcat(3, 5), 8, fastcat(0, 1)).first_cycle() == [
        Event(TimeSpan(0, 1 / 8), TimeSpan(0, 1 / 8), {"s": "sd"}),
        Event(TimeSpan(3 / 8, 1 / 2), TimeSpan(3 / 8, 1 / 2), {"s": "sd"}),
        Event(TimeSpan(1 / 2, 5 / 8), TimeSpan(1 / 2, 5 / 8), {"s": "sd"}),
        Event(TimeSpan(5 / 8, 3 / 4), TimeSpan(5 / 8, 3 / 4), {"s": "sd"}),
        Event(TimeSpan(7 / 8, 1), TimeSpan(7 / 8, 1), {"s": "sd"}),
    ]


def test_app_left():
    assert saw().segment(1).query(TimeSpan(0, 0.25)) == [
        Event(TimeSpan(0, 1), TimeSpan(0, 1 / 4), 0.5)
    ]
