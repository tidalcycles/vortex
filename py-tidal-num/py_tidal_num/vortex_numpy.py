 import numpy as np
 from typing import Any, Callable, List

 def sam_np(time: float=0):
     print(time)
     return int(np.floor(time))

 def next_sam(time: float=0):
     return int(np.ceil(time))

 def whole_cycle(time_span: np.array=np.array([])):
     print(time_span)
     begin, end = time_span.flatten()
     return np.array([sam_np(begin), next_sam(end)])

def row_clip(target_span, cycle):
    cycle_sam, cycle_next_sam = cycle
    return np.clip(target_span, cycle_sam, cycle_next_sam)

def span_cycles(query_value: np.array=np.array([])):
    print(f"span_cycles {query_value}")
    query, value = query_value
    begin, end = query
    framing_cycles = np.linspace(sam_np(begin), next_sam(end), next_sam(end)-sam_np(begin)+1)
    framing_cycles = np.array([framing_cycles[:-1], framing_cycles[1:]]).T
    return np.array([row_clip(query, c) for c in framing_cycles]), value

def modify_time_span(function: Callable):
    def with_time(time_span: np.array=np.array([])):
        return function(time_span)
    return with_time

def sect_time_spans(span_one: np.array=np.array([]), span_two: np.array=np.array([])):
    begin_one, end_one = span_one
    begin_two, end_two = span_two
    if begin_one < begin_two:
        return np.clip(span_one, begin_two, end_two) if end_one > begin_two  else np.array([])
    else:
        return np.clip(span_two, begin_one, end_one) if end_two > begin_one  else np.array([])

def modify_event(function: Callable):
    def with_span(event: np.array=np.array([[]])):
        whole, part, value = event
        return np.array([function(whole), function(part), value])
    return with_span

def modify_event_value(function: Callable):
    def value(event: np.array=np.array([[]])):
        whole, part, value = event
        return np.array([whole, part, function(value)])
    return value

def split_queries(query_span: np.array=np.array([])):
    return np.concatenate([span_cycles(query_span)])

def chain(function_list: List[Callable]) -> Any:
    def reaction(input: Any):
        res = input
        for funk in function_list:
            print(f"Calling {str(funk)}")
            res = funk(res)
        return res

    return reaction

def event_whole_cycle(events: np.array=np.array([])):
    print(events)
    wholes, values = events
    return whole_cycle(wholes), wholes, values

def create_event(event: np.array=np.array([])):
    value, whole = event
    return np.array([whole, whole, value])

def create_query(time_span: np.array=np.array([])):
    def with_value(value):
        return time_span, value
    return with_value

atom_np = chain([span_cycles, event_whole_cycle])