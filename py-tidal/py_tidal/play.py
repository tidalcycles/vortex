
import os
import sys
import time
import math
import liblo

superdirt = liblo.Address(57120)

lib_dir = os.path.normpath(os.path.dirname(os.path.realpath(__file__)) + '/lib/')
sys.path.insert(0, lib_dir)

import link

#from vortex import *
from py_tidal import *

l = link.Link(120)

l.enabled = True
l.startStopSyncEnabled = True

start = l.clock().micros();
mill = 1000000
start_beat = l.captureSessionState().beatAtTime(start,4)
print("start: " + str(start_beat))
ticks = 0
frame = (1/20) * mill
bpc = 4
latency = 0.2

pattern = (s(stack([pure("gabba").fast(pure(4)), pure("cp").fast(pure(3))]))
           >> speed(sequence([pure(2), pure(3)]))
           >> room(pure(0.5))
           >> size(pure(0.8))
)

try:
    while True:
        ticks = ticks + 1
        
        logical_now = math.floor(start + (ticks * frame))
        logical_next = math.floor(start + ((ticks + 1) * frame))

        # wait until start of next frame
        wait = (logical_now - l.clock().micros())/mill;
        if wait > 0:
            time.sleep(wait)

        s = l.captureSessionState()
        cps = (s.tempo() / bpc) / 60
        cycle_from = s.beatAtTime(logical_now, 0) / bpc
        cycle_to = s.beatAtTime(logical_next, 0) / bpc
        es = pattern.onsetsOnly().query(TimeSpan(cycle_from, cycle_to))
        if len(es):
            print("\n" + str([e.value for e in es]))
            
        for e in es:
            cycle_on  = e.whole.begin
            cycle_off = e.whole.end
            
            link_on  = s.timeAtBeat(cycle_on  * bpc, 0)
            link_off = s.timeAtBeat(cycle_off * bpc, 0)
            delta_secs = (link_off - link_on)/mill

            # Maybe better to only calc this once??
            # + it would be better to send link time to supercollider..
            link_secs = l.clock().micros()/mill
            liblo_diff = liblo.time()-link_secs
            ts = (link_on/mill) + liblo_diff + latency
            
            #print("liblo time %f link_time %f link_on %f cycle_on %f liblo_diff %f ts %f" % (liblo.time(), link_secs, link_on, cycle_on, liblo_diff, ts))
            v = e.value
            v["cps"]   = float(cps)
            v["cycle"] = float(cycle_on)
            v["delta"] = float(delta_secs)
            
            msg = [] 
            for key, val in v.items(): 
                msg.append(key)
                msg.append(val)
            print(*msg)
            #liblo.send(superdirt, "/dirt/play", *msg)
            bundle = liblo.Bundle(ts, liblo.Message("/dirt/play", *msg))
            liblo.send(superdirt, bundle)
        
        sys.stdout.write("cps %.2f | playing %s | cycle %.2f\r"
                         % (cps, s.isPlaying(), cycle_from))
        
        sys.stdout.flush()

        
except KeyboardInterrupt:
    pass
