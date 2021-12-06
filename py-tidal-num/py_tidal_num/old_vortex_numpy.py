"""
Experiment: porting Tidalcycles to Python 3.x.
"""

from fractions import Fraction
from typing import Any, Union, Callable, List
import numpy as np
import logging


# def pattern(function_list: List[Callable]) -> Any:
#     def query(input: np.array=np.array([])):
#         res = input
#         for funk in function_list:
#             log.info(f"Calling {str(function)}")
#             res = funk(res)
#         return res
#
#     return query

def sam_np(frac: Fraction) -> int:
    return np.floor(frac)


def next_sam(frac: Fraction) -> int:
    return np.ceil(frac)


def whole_cycle(time_span: np.array = np.array([])) -> np.array:
    return np.array([sam_np(time_span[0]), next_sam(time_span[1])])


# def sect(timespan_a: np.array, timespan_b: np.array) -> np.array:
#     return (
#         np.array(
#             [
#                 np.maximum(timespan_a[0], timespan_b[0]),
#                 np.minimum(timespan_a[1], timespan_b[1]),
#             ]
#         )
#         if timespan_a[1] > timespan_b[0]
#         else None
#     )

def sect_events_part(part: np.array = np.array([[]]), query: np.array = np.array([])):
    parts_sect = [np.clip(part, q[0], q[1]) for q in query if part[1] > q[0] and q[1] > part[0]]
    print(parts_sect)
    return np.concatenate(parts_sect)

def part_whole_belong(flat_parts: list, whole: np.array):
    parts = flat_parts.reshape(int(flat_parts.shape[0]/2),2)
    wholes = [whole for part in parts if part[0] >= whole[0] and part[1] <= whole[1]]
    if wholes is not None:
        return wholes

def value_whole_belong(events, whole_belong):
    wholes, parts, values  = events
    i = 0
    for whole in wholes:
        if list(whole) == list(whole_belong):
            return values[i]
        i = i + 1

def sect(events, query):
    wholes, parts, values = events
    parts = [sect_events_part(part, query) for part in parts]
    wholes_belong = [part_whole_belong(flat_part, whole) for flat_part in parts for whole in wholes]
    wholes = np.concatenate([whole for whole in wholes_belong if whole])
    flat_sect = np.concatenate(parts)
    parts = flat_sect.reshape(int(flat_sect.shape[0]/2),2)
    values = np.array([value_whole_belong(events, whole) for whole in wholes])
    return wholes, parts, values

def create_event(value_id: Any):
    def event(event_span: np.array = np.array([[]])):
        return event_span, value_id

    return event


# def span_cycles(events: np.array) -> np.array:
#     wholes, parts, values = events
#     y = np.arange(sam_np(parts[0][0]), next_sam(parts[0][1])+1, 1)
#     y[0] = parts[0][0]
#     y[-1] = parts[0][1]
#     y = np.array([y[:-1], y[1:]]).T
#     print(y)
#     print(y[0])
#     print(y[1])
#     x = np.array([np.floor(y[0]), np.ceil(y[-1])])
#     return x, y, values

# def span_cycles(timespan: np.array=np.array([])):
#     min = int(np.ceil(np.min(timespan)))
#     max = int(np.floor(np.max(timespan)))
#     spans = np.insert(timespan, 1, np.repeat(np.linspace(min, max, max-min+1),2)).reshape(max-min+2, 2)
#     return spans
#
# def span_cycles_vec(wholes):
#     v_span = np.vectorize(span_cycles, signature='(n)->(m,n)')
#     return v_span(wholes)

def create_late(offset):
    def late(pattern: tuple = tuple()):
        event, value_id = pattern
        whole = span_cycles(whole_cycle(event[0]) - offset)
        part = np.array([sect(event[1], event[1] - offset), sect(event[1], event[1] + offset)])
        return np.array([whole, part]), value_id

    return late


def fast_cat(events: np.array = np.array([[]])):
    whole, part, values = events
    return whole / whole.shape[0], part / part.shape[0], values


def events(atoms: np.array = np.array([[]])):
    lin_atoms = np.linspace(0, atoms.shape[0], atoms.shape[0] + 1)
    whole = np.array([lin_atoms[:-1], lin_atoms[1:]]).T
    part = np.array([lin_atoms[:-1], lin_atoms[1:]]).T
    return whole, part, atoms


def split_query(atoms: np.array = np.array([]), offset=0):
    lin_atoms = np.linspace(atoms[0], atoms[1], atoms[1] - atoms[0] + 1)
    query = np.array([lin_atoms[:-1], lin_atoms[1:]]).T+offset
    return query


def create_late(offset):
    def late(events: np.array = np.array([[]])):
        events, values = events
        # events = span_cycles(whole_cycle(events) - offset)
        return events - offset, values

    return late


################################################################################################################

def span_cycles(events: np.array) -> np.array:
    wholes, parts, values = events
    y = np.arange(sam_np(parts[0][0]), next_sam(parts[0][1]) + 1, 1)
    y[0] = parts[0][0]
    y[-1] = parts[0][1]
    y = np.array([y[:-1], y[1:]]).T
    x = np.array([np.floor(y[0]), np.ceil(y[-1])])
    return x, y, values


def late_part(events, offset):
    wholes, parts, values = events
    return np.floor(parts - offset), parts - offset, values


def late_event(events, offset):
    wholes, parts, values = events
    return wholes + offset, parts + offset, values

def query(query_span:np.array=np.array([])):
    #query_spans = queries(query_span)
    def events(events:tuple=tuple()):
        wholes, parts, values = events
        print(sect(events, query_span))
        return wholes, parts, values
    return events

