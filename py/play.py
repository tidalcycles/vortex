
import os
import sys
import time
import math

lib_dir = os.path.normpath(os.path.dirname(os.path.realpath(__file__)) + '/lib/')
sys.path.insert(0, lib_dir)

import link
import vortex


l = link.Link(135)

l.enabled = True
l.startStopSyncEnabled = True

start = l.clock().micros();
ticks = 0
frame = (1/20) * 1000000
bpc = 4

try:
    while True:
        ticks = ticks + 1
        
        logical_now = math.floor(start + (ticks * frame))
        # wait until start of next frame
        wait = (logical_now - l.clock().micros())/1000000;
        if wait > 0:
            time.sleep(wait)

        s = l.captureSessionState()
        cycle = s.beatAtTime(logical_now, 0) / bpc
        cps = (s.tempo() / bpc) / 60

        sys.stdout.write("cps %.2f | playing %s | cycle %.2f\r"
                         % (cps, s.isPlaying(), cycle))
        
        sys.stdout.flush()

except KeyboardInterrupt:
    pass
