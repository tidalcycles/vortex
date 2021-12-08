import math
import sys
import time
import threading

import liblo
import link

from py_vortex import *


class SuperDirtStream:
    def __init__(self, port=57120, bpm=120):
        self.port = port
        self.bpm = bpm

        self.address = liblo.Address(port)
        self.link = link.Link(bpm)

        self.patterns = []
        self.play_thread = threading.Thread(target=self.play)

    def play(self):
        self._is_playing = True

    def stop(self):
        self._is_playing = False

    @property
    def is_playing(self):
        return self._is_playing

    def __setitem__(self, key, control):
        self.patterns[key] = control

    def __getitem__(self, key):
        return self.patterns[key]

    def _play_thread(self):
        self.link.enabled = True
        self.link.startStopSyncEnabled = True

        start = self.link.clock().micros()
        mill = 1000000
        start_beat = self.link.captureSessionState().beatAtTime(start, 4)
        print("start: " + str(start_beat))

        ticks = 0
        # (1/20), bpc and latency should be constructor parameters
        frame = (1 / 20) * mill
        bpc = 4
        latency = 0.2

        while self.is_playing:
            ticks = ticks + 1

            logical_now = math.floor(start + (ticks * frame))
            logical_next = math.floor(start + ((ticks + 1) * frame))

            # wait until start of next frame
            wait = (logical_now - self.link.clock().micros()) / mill
            if wait > 0:
                time.sleep(wait)

            s = self.link.captureSessionState()
            cps = (s.tempo() / bpc) / 60
            cycle_from = s.beatAtTime(logical_now, 0) / bpc
            cycle_to = s.beatAtTime(logical_next, 0) / bpc
            es = self.pattern.onsetsOnly().query(TimeSpan(cycle_from, cycle_to))
            if len(es):
                print("\n" + str([e.value for e in es]))

            for e in es:
                cycle_on = e.whole.begin
                cycle_off = e.whole.end

                link_on = s.timeAtBeat(cycle_on * bpc, 0)
                link_off = s.timeAtBeat(cycle_off * bpc, 0)
                delta_secs = (link_off - link_on) / mill

                # Maybe better to only calc this once??
                # + it would be better to send link time to supercollider..
                link_secs = self.link.clock().micros() / mill
                liblo_diff = liblo.time() - link_secs
                ts = (link_on / mill) + liblo_diff + latency

                # print("liblo time %f link_time %f link_on %f cycle_on %f liblo_diff %f ts %f" % (liblo.time(), link_secs, link_on, cycle_on, liblo_diff, ts))
                v = e.value
                v["cps"] = float(cps)
                v["cycle"] = float(cycle_on)
                v["delta"] = float(delta_secs)

                msg = []
                for key, val in v.items():
                    msg.append(key)
                    msg.append(val)
                print(*msg)

                # liblo.send(superdirt, "/dirt/play", *msg)
                bundle = liblo.Bundle(ts, liblo.Message("/dirt/play", *msg))
                liblo.send(self.address, bundle)

            sys.stdout.write(
                "cps %.2f | playing %s | cycle %.2f\r"
                % (cps, s.isPlaying(), cycle_from)
            )

            sys.stdout.flush()
