
from fractions import Fraction
from math import floor

def sam(t):
    return Fraction(floor(t))

def nextSam(t):
    return sam(t)+1

def wholeCycle(t):
    return (sam(t), nextSam(t))

def spanCycles(b, e):
    if e <= b:
        return []
    if sam(b) == sam(e):
        return [(b,e)]
    # otherwise
    nextB = nextSam(b)
    spans = spanCycles(nextB, e)
    spans.insert(0, (b, nextB))
    return spans
    
def concat(t):
    return [item for sublist in t for item in sublist]

class Pattern:
    def __init__(self, query):
        self.query = query

    # Splits queries at cycle boundaries. Makes some calculations easy
    # express, as everything then happens within a cycle.
    def splitQueries(self):
        def query (b, e): 
            return list(map(lambda span: self.query(span[0],span[1]), spanCycles(b, e)))
        return Pattern(query)
        

def silence():
    return Pattern(lambda b, e: [])

def atom(value):
    def query(b, e):
        spans = spanCycles(b,e)
        return list(map(lambda span: (wholeCycle(span[0]), span, value), spans))
    return Pattern(query)

def slowcat(pats):
    def query(b,e):
        pat = pats[floor(b) % len(pats)]
        return pat.query(b,e)
    pat = Pattern(query)
    return pat.splitQueries()

a = atom("hello")
b = atom("world")
c = slowcat([a,b])
c.query(0,2)
