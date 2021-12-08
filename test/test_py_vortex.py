import pytest
import py_vortex as pyt


@pytest.fixture
def multi_list():
    return [[1, 2, 3], [4, 5, 6]]


def test_concat(multi_list):
    flat_list = pyt.concat(multi_list)
    assert flat_list == [1, 2, 3, 4, 5, 6]

def test_remove_none(multi_list):
    multi_list[0].append(None)
    no_none_list = pyt.removeNone(multi_list[0])
    assert list(no_none_list) == [1, 2, 3]


def test_sam():
    a = pyt.Time(3, 2).sam()
    assert a == 1
    a = pyt.Time(3, 2).nextSam()
    assert a == 2


def test_whole_cycle():
    a = pyt.Time(3, 2).wholeCycle()
    assert a.begin == 1
    assert a.end == 2


def test_sect():
    a = pyt.TimeSpan(1, 4)
    sector = a.sect(pyt.TimeSpan(3, 6))
    assert sector.begin == pyt.TimeSpan(3, 4).begin
    assert sector.end == pyt.TimeSpan(3, 4).end

def test_with_time():
    a = pyt.TimeSpan(1, 4)
    wt = a.withTime(lambda x:x*2)
    assert wt.begin == pyt.TimeSpan(2, 8).begin
    assert wt.end == pyt.TimeSpan(2, 8).end


def test_span_cycles():
    a = pyt.TimeSpan(0.25, 2.5)
    sc = a.spanCycles()
    print(sc)
    assert sc[0].begin == a.begin
    assert sc[0].end == pyt.Time(1)
    assert sc[1].begin == pyt.Time(1)
    assert sc[1].end == pyt.Time(2)
    assert sc[2].begin == pyt.Time(2)
    assert sc[2].end == a.end

def test_event_span():
    e = pyt.Event(0.25, 0.5, 1)
    ws = e.withSpan(lambda x: x * 2)
    assert ws.whole == 0.5
    assert ws.part == 1
    assert ws.value == 1

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

