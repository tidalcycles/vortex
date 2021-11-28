
from fractions import Fraction
from math import floor

# flatten list of lists
def concat(t):
    return [item for sublist in t for item in sublist]

Fraction.sam = lambda self: Fraction(floor(self))
Fraction.nextSam = lambda self: self.sam() + 1
Fraction.wholeCycle = lambda self: TimeSpan(self.sam(), self.nextSam())

class TimeSpan:
    def __init__(self, begin, end):
        self.begin = begin
        self.end = end

    # TODO - make this more imperative
    def spanCycles(self):
        if self.end <= self.begin:
            return []
        if self.begin.sam() == self.end.sam():
            return [self]
        
        # otherwise
        nextB = self.begin.nextSam()
        spans = TimeSpan(nextB, self.end).spanCycles()
        spans.insert(0, TimeSpan(self.begin, nextB))
        return spans

    def withTime(self, f):
        return TimeSpan(f(self.begin), f(self.end))
    
    def __repr__(self):
        return ("TimeSpan(" + self.begin.__repr__()
                + ", "
                + self.end.__repr__() + ")"
               )

class Event:
    def __init__(self, whole, part, value):
        self.whole = whole
        self.part = part
        self.value = value

    def withSpan(self, f):
        if self.whole == None:
            whole = None
        else:
            whole = f(self.whole)
        return Event(whole, f(self.part), self.value)
            
    def __repr__(self):
        return ("Event(" + self.whole.__repr__()
                + ", "
                + self.part.__repr__() + ")"
                + ", "
                + self.value.__repr__() + ")"
               )
    
class Pattern:
    def __init__(self, query):
        self.query = query

    # Splits queries at cycle boundaries. Makes some calculations easier
    # to express, as everything then happens within a cycle.
    def splitQueries(self):
        def query(span): 
            return concat(list(map(self.query, span.spanCycles())))
        return Pattern(query)

    def withQuerySpan(self, f):
        return Pattern(lambda span: self.query(f(span)))

    def withQueryTime(self, f):
        return Pattern(lambda span: self.query(span.withTime(f)))

    def withEventSpan(self, f):
        def query(span):
            return list(map(lambda event: event.withSpan(f),
                            self.query(span)
                           )
                       )
        return Pattern(query)
    
    def withEventTime(self, f):
        return self.withEventSpan(lambda span: span.withTime(f))

    def fast(self, factor):
        fastQuery = self.withQueryTime(lambda t: t*factor)
        fastEvents = fastQuery.withEventTime(lambda t: t/factor)
        return fastEvents
    
    def slow(self, factor):
        return self.fast(1/factor)

    def early(self, offset):
        return self.withQueryTime(lambda t: t+offset).withEventTime(lambda t: t-offset)

    def late(self, offset):
        return self.early(0-offset)
    
    def firstCycle(self):
        return self.query(TimeSpan(Fraction(0), Fraction(1)))
    
# Should this be a value or a function?
silence = Pattern(lambda _: [])

def atom(value):
    def query(span):
        return list(map(lambda subspan: Event(subspan.begin.wholeCycle(),
                                              subspan,
                                              value
                                             ),
                        span.spanCycles()
                       )
                   )
    return Pattern(query)

def slowcat(pats):
    def query(span):
        pat = pats[floor(span.begin) % len(pats)]
        return pat.query(span)
    return Pattern(query).splitQueries()

def fastcat(pats):
    return slowcat(pats).fast(len(pats))

a = atom("hello")
b = atom("world")
c = fastcat([a,b])
c.query(TimeSpan(Fraction(0),Fraction(2)))
c.fast(2).query(TimeSpan(Fraction(0), Fraction(1)))
