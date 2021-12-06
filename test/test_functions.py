import pytest
import py_tidal as pyt
from numpy.testing import assert_array_equal
import numpy as np
from fractions import Fraction


@pytest.fixture
def multi_list():
    return [[1, 2, 3], [4, 5, 6]]


def test_concat(multi_list):
    flat_list = pyt.concat(multi_list)
    assert flat_list == [1, 2, 3, 4, 5, 6]
    flat_np_list = pyt.flatten_numpy(np.array(multi_list))
    assert_array_equal(flat_np_list, np.array([1, 2, 3, 4, 5, 6]))


def test_remove_none(multi_list):
    multi_list[0].append(None)
    no_none_list = pyt.removeNone(multi_list[0])
    assert list(no_none_list) == [1, 2, 3]
    no_none_np_list = pyt.remove_none_np(np.array(multi_list[0]))
    assert_array_equal(no_none_np_list, np.array([1, 2, 3]))


def test_sam():
    a = pyt.sam(Fraction(3, 2))
    b = pyt.sam_np(Fraction(3, 2))
    assert a == 1
    assert b == 1
    a = pyt.nextSam(Fraction(3, 2))
    b = pyt.next_sam_np(Fraction(3, 2))
    assert a == 2
    assert b == 2


def test_whole_cycle():
    a = pyt.wholeCycle(Fraction(3, 2))
    b = pyt.whole_cycle_np(Fraction(3, 2))
    assert [a.begin, a.end] == b.tolist()


def test_sect():
    a = pyt.TimeSpan(1, 4)
    sector = a.sect(pyt.TimeSpan(3, 6))
    assert sector.begin == pyt.TimeSpan(3, 4).begin
    assert sector.end == pyt.TimeSpan(3, 4).end
    t = pyt.sect_numpy(np.array([1, 4]), np.array([3, 6]))
    assert_array_equal(t, np.array([3, 4]))
    # Fail
    #a = pyt.TimeSpan(1, 4)
    #sector = a.sect(pyt.TimeSpan(5, 6))
    #assert sector is None
    t = pyt.sect_numpy(np.array([1, 4]), np.array([5, 6]))
    assert t is None

def mult_2(x):
    return x * 2


def test_with_time():
    a = pyt.TimeSpan(1, 4)
    wt = a.withTime(mult_2)
    assert wt.begin == pyt.TimeSpan(2, 8).begin
    assert wt.end == pyt.TimeSpan(2, 8).end
    b = np.array([1, 4])
    wt = pyt.create_with_time(mult_2)(b)
    assert_array_equal(wt, np.array([2, 8]))


def test_span_cycles():
    a = pyt.TimeSpan(0.25, 2.5)
    sc = a.spanCycles()
    print(sc)
    assert sc[0].begin == a.begin
    assert sc[0].end == Fraction(1)
    assert sc[1].begin == Fraction(1)
    assert sc[1].end == Fraction(2)
    assert sc[2].begin == Fraction(2)
    assert sc[2].end == a.end
    b = np.array([0.25, 2.5])
    sc = pyt.span_cycles(b)
    assert_array_equal(sc, np.array([[0.25, 1], [1, 2], [2, 2.5]]))

def test_event_span():
    e = pyt.Event(0.25, 0.5, 1)
    ws = e.withSpan(lambda x: x * 2)
    assert ws.whole == 0.5
    assert ws.part == 1
    assert ws.value == 1
    ws = pyt.create_event_with_span(0.5, 1, lambda x: x * 2)(0.25)
    assert_array_equal(ws, np.array([0.5, 1, 1]))

def test_event_value():
    e = pyt.Event(pyt.TimeSpan(0, 1), pyt.TimeSpan(0.25, 0.5), 1)
    ws = e.withValue(lambda x: x * 2)
    print(ws)
    print(ws.whole)
    print(ws.whole.begin)
    assert ws.whole.begin == 0
    assert ws.whole.end == 1
    assert ws.part.begin == 0.25
    assert ws.part.end == 0.5
    assert ws.value == 2
    ws = pyt.create_event_with_value(np.array([[0,1], [0.25,0.5]]), lambda x: x * 2)(1)
    print(ws)
    assert_array_equal(ws[0], np.array([[0,1], [0.25,0.5]]))
    assert ws[1] == 2

def test_query_span():
    p = pyt.fastcat([pyt.atom(3), pyt.atom(4), pyt.atom(5)])
    new_p = p.withQuerySpan(pyt.fastcat([pyt.atom(lambda x: x * 0.5), pyt.atom(lambda x: x * 0.25)]))
    pyt.pattern_pretty_printing(pattern=new_p, query_span=pyt.TimeSpan(pyt.Time(0), pyt.Time(1)))
    assert p == 0