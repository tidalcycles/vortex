import pytest
import py_vortex as pyt
from fractions import Fraction

@pytest.fixture
def multi_list():
    return [[1, 2, 3], [4, 5, 6]]

# Utilities
def test_concat(multi_list):
    flat_list = pyt.concat(multi_list)
    assert flat_list == [1, 2, 3, 4, 5, 6]

def test_remove_none(multi_list):
    multi_list[0].append(None)
    no_none_list = pyt.remove_nones(multi_list[0])
    assert list(no_none_list) == [1, 2, 3]


#Time Class tests
def test_sam():
    a = Fraction(3, 2).sam()
    assert a == 1
    a = Fraction(3, 2).next_sam()
    assert a == 2


def test_whole_cycle():
    a = Fraction(3, 2).whole_cycle()
    assert a.begin == 1
    assert a.end == 2


# TimeSpan Class tests
def test_intersection():
    a = pyt.TimeSpan(1, 4)
    span = a.intersection(pyt.TimeSpan(3, 6))
    assert span.begin == pyt.TimeSpan(3, 4).begin
    assert span.end == pyt.TimeSpan(3, 4).end
    a = pyt.TimeSpan(1, 2)
    try:
        span = a.intersection(pyt.TimeSpan(3, 6))
    except ValueError as v:
        assert str(v) == "TimeSpan TimeSpan(Time(1, 1), Time(2, 1)) and TimeSpan TimeSpan(Time(3, 1), Time(6, 1)) do not intersect"

def test_with_time():
    a = pyt.TimeSpan(1, 4)
    wt = a.with_time(lambda x:x*2)
    assert wt.begin == pyt.TimeSpan(2, 8).begin
    assert wt.end == pyt.TimeSpan(2, 8).end


def test_span_cycles():
    a = pyt.TimeSpan(0.25, 2.5)
    sc = a.span_cycles()
    print(sc)
    assert sc[0].begin == a.begin
    assert sc[0].end == Fraction(1)
    assert sc[1].begin == Fraction(1)
    assert sc[1].end == Fraction(2)
    assert sc[2].begin == Fraction(2)
    assert sc[2].end == a.end

# Event Class tests
def test_event_span():
    e = pyt.Event(0.25, 0.5, 1)
    ws = e.with_span(lambda x: x * 2)
    assert ws.whole == 0.5
    assert ws.part == 1
    assert ws.value == 1

def test_event_value():
    e = pyt.Event(pyt.TimeSpan(0, 1), pyt.TimeSpan(0.25, 0.5), 1)
    ws = e.with_value(lambda x: x * 2)
    print(ws)
    print(ws.whole)
    print(ws.whole.begin)
    assert ws.whole.begin == 0
    assert ws.whole.end == 1
    assert ws.part.begin == 0.25
    assert ws.part.end == 0.5
    assert ws.value == 2

def test_has_onset():
    e = pyt.Event(pyt.TimeSpan(0.5, 1.5), pyt.TimeSpan(0.5, 1), "hello")
    assert e.has_onset
