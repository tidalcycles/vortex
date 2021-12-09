import math

# import sys
import time
import threading

import liblo
import link

from py_vortex import *


class LinkClock:
    def __init__(self, bpm=120):
        self.bpm = bpm

        self._subscribers = []
        self._link = link.Link(bpm)
        self._play_thread = threading.Thread(target=self._play_thread_target)
        self._mutex = threading.Lock()

    def subscribe(self, subscriber):
        with self._mutex:
            self._subscribers.append(subscriber)

    def unsubscribe(self, subscriber):
        with self._mutex:
            self._subscribers.delete(subscriber)

    def play(self):
        with self._mutex:
            self._is_playing = True
        self._play_thread.start()

    def stop(self):
        with self._mutex:
            self._is_playing = False

    @property
    def is_playing(self):
        return self._is_playing

    def _play_thread_target(self):
        self._link.enabled = True
        self._link.startStopSyncEnabled = True

        start = self._link.clock().micros()
        mill = 1000000
        start_beat = self._link.captureSessionState().beatAtTime(start, 4)
        print("start: " + str(start_beat))

        ticks = 0

        # FIXME rate, bpc and latency should be constructor parameters
        rate = 1 / 20
        frame = rate * mill
        bpc = 4

        while self._is_playing:
            ticks = ticks + 1

            logical_now = math.floor(start + (ticks * frame))
            logical_next = math.floor(start + ((ticks + 1) * frame))

            now = self._link.clock().micros()

            # wait until start of next frame
            wait = (logical_now - now) / mill
            if wait > 0:
                time.sleep(wait)

            if not self._is_playing:
                continue

            s = self._link.captureSessionState()
            cps = (s.tempo() / bpc) / 60
            cycle_from = s.beatAtTime(logical_now, 0) / bpc
            cycle_to = s.beatAtTime(logical_next, 0) / bpc

            for sub in self._subscribers:
                sub.notify_tick((cycle_from, cycle_to), s, cps, bpc, mill, now)

            # sys.stdout.write(
            #     "cps %.2f | playing %s | cycle %.2f\r"
            #     % (cps, s.isPlaying(), cycle_from)
            # )

            # sys.stdout.flush()


class SuperDirtStream:
    def __init__(self, port=57120, latency=0.2):
        self.pattern = None
        self.latency = latency

        self._port = port
        self._address = liblo.Address(port)
        self._is_playing = True

    def play(self):
        self._is_playing = True

    def stop(self):
        self._is_playing = False

    @property
    def is_playing(self):
        return self._is_playing

    @property
    def port(self):
        return self._port

    def notify_tick(self, cycle, s, cps, bpc, mill, now):
        if not self._is_playing or not self.pattern:
            return

        cycle_from, cycle_to = cycle
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
            link_secs = now / mill
            liblo_diff = liblo.time() - link_secs
            ts = (link_on / mill) + liblo_diff + self.latency

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
            liblo.send(self._address, bundle)


if __name__ == "__main__":
    clock = LinkClock(120)
    clock.play()

    stream = SuperDirtStream()
    clock.subscribe(stream)

    print("wait a sec")
    time.sleep(0.5)

    print("set pattern")
    stream.pattern = (
        s(stack([pure("gabba").fast(pure(4)), pure("cp").fast(pure(3))]))
        >> speed(sequence([pure(2), pure(3)]))
        >> room(pure(0.5))
        >> size(pure(0.8))
    )
    time.sleep(3)

    print("unset pattern")
    stream.pattern = None
    time.sleep(2)

    clock.stop()
    print("done")
