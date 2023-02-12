from __future__ import annotations

import logging
import math
import threading
import time
from abc import ABC
from fractions import Fraction
from typing import Any, Dict

import liblo
import link

from vortex import *

_logger = logging.getLogger(__name__)


class LinkClock:
    """
    This class handles synchronization between different devices using the Link
    protocol.

    You can subscribe other objects (i.e. Streams), which will be notified on
    each clock tick. It expects that subscribers define a `notify_tick` method.

    Parameters
    ----------
    bpm: float
        beats per minute (default: 120)

    """

    def __init__(self, bpm=120):
        self.bpm = bpm

        self._subscribers = []
        self._link = link.Link(bpm)
        self._is_running = False
        self._mutex = threading.Lock()

    def subscribe(self, subscriber):
        """Subscribe an object to tick notifications"""
        with self._mutex:
            self._subscribers.append(subscriber)

    def unsubscribe(self, subscriber):
        """Unsubscribe from tick notifications"""
        with self._mutex:
            self._subscribers.remove(subscriber)

    def start(self):
        """Start the clock"""
        with self._mutex:
            if self._is_running:
                return
            self._is_running = True
        self._create_notify_thread()

    def stop(self):
        """Stop the clock"""
        with self._mutex:
            self._is_running = False
        # Wait until thread has stopped
        # Will block until (at least) the next start of frame
        self._notify_thread.join()

    @property
    def is_playing(self):
        """Returns whether clock is currently running"""
        return self._is_running

    def _create_notify_thread(self):
        self._notify_thread = threading.Thread(target=self._notify_thread_target)
        self._notify_thread.start()

    def _notify_thread_target(self):
        _logger.info("Link enabled")
        self._link.enabled = True
        self._link.startStopSyncEnabled = True

        start = self._link.clock().micros()
        mill = 1000000
        start_beat = self._link.captureSessionState().beatAtTime(start, 4)
        _logger.info("Start beat: %f", start_beat)

        ticks = 0

        # FIXME rate, bpc and latency should be constructor parameters
        rate = 1 / 20
        frame = rate * mill
        bpc = 4

        while self._is_running:
            ticks = ticks + 1

            logical_now = math.floor(start + (ticks * frame))
            logical_next = math.floor(start + ((ticks + 1) * frame))

            now = self._link.clock().micros()

            # wait until start of next frame
            wait = (logical_now - now) / mill
            if wait > 0:
                time.sleep(wait)

            if not self._is_running:
                break

            s = self._link.captureSessionState()
            cps = (s.tempo() / bpc) / 60
            cycle_from = s.beatAtTime(logical_now, 0) / bpc
            cycle_to = s.beatAtTime(logical_next, 0) / bpc

            try:
                for sub in self._subscribers:
                    sub.notify_tick((cycle_from, cycle_to), s, cps, bpc, mill, now)
            except:
                pass

            # sys.stdout.write(
            #     "cps %.2f | playing %s | cycle %.2f\r"
            #     % (cps, s.isPlaying(), cycle_from)
            # )

            # sys.stdout.flush()

        self._link.enabled = False
        _logger.info("Link disabled")
        return


class BaseStream(ABC):
    """
    A class for playing control pattern events

    It should be subscribed to a LinkClock instance.

    Parameters
    ----------
    name: Optional[str]
        Name of the stream instance

    """

    def __init__(self, name: str = None):
        self.name = name
        self.pattern = None

    def notify_tick(self, cycle, s, cps, bpc, mill, now):
        """Called by a Clock every time it ticks, when subscribed to it"""
        if not self.pattern:
            return

        cycle_from, cycle_to = cycle
        es = self.pattern.onsets_only().query(TimeSpan(cycle_from, cycle_to))
        if len(es):
            _logger.debug("%s", [e.value for e in es])

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
            nudge = e.value.get("nudge", 0)
            ts = (link_on / mill) + liblo_diff + self.latency + nudge

            # print("liblo time %f link_time %f link_on %f cycle_on %f liblo_diff %f ts %f" % (liblo.time(), link_secs, link_on, cycle_on, liblo_diff, ts))
            self.notify_event(
                e.value,
                timestamp=ts,
                cps=float(cps),
                cycle=float(cycle_on),
                delta=float(delta_secs),
            )

    def notify_event(
        self,
        event: Dict[str, Any],
        timestamp: float,
        cps: float,
        cycle: float,
        delta: float,
    ):
        """Called by `notify_tick` with the event and timestamp that should be played"""
        raise NotImplementedError

    def __repr__(self):
        pattern_repr = " \n" + repr(self.pattern) if self.pattern else ""
        return f"<{self.__class__.__name__} {repr(self.name)}{pattern_repr}>"


class SuperDirtStream(BaseStream):
    """
    This Stream class sends control pattern messages to SuperDirt via OSC

    Parameters
    ----------
    port: int
        The port where SuperDirt is listening
    latency: float
        SuperDirt latency

    """

    def __init__(self, port=57120, latency=0.2, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.latency = latency

        self._port = port
        self._address = liblo.Address(port)

    @property
    def port(self):
        """SuperDirt listening port"""
        return self._port

    def notify_event(
        self,
        event: Dict[str, Any],
        timestamp: float,
        cps: float,
        cycle: float,
        delta: float,
    ):
        msg = []
        for key, val in event.items():
            if isinstance(val, Fraction):
                val = float(val)
            msg.append(key)
            msg.append(val)
        msg.extend(["cps", cps, "cycle", cycle, "delta", delta])
        _logger.info("%s", msg)

        # liblo.send(superdirt, "/dirt/play", *msg)
        bundle = liblo.Bundle(timestamp, liblo.Message("/dirt/play", *msg))
        liblo.send(self._address, bundle)

def setup_logging(loglevel):
    """Setup basic logging

    Args:
      loglevel (int): minimum loglevel for emitting messages
    """
    logformat = "[%(asctime)s] %(levelname)s:%(name)s:%(message)s"
    logging.basicConfig(
        level=loglevel, stream=sys.stdout, format=logformat, datefmt="%Y-%m-%d %H:%M:%S"
    )
    
if __name__ == "__main__":
    setup_logging(logging.DEBUG)
    clock = LinkClock(120)
    clock.start()

    stream = SuperDirtStream()
    clock.subscribe(stream)

    logging.info(">> Wait a sec")
    time.sleep(1)

    logging.info(">> Set pattern and let it play for 2 seconds")
    stream.pattern = s(stack("gabba*4", "cp*3")).speed("2 3") >> room(0.5).size(0.8)
    time.sleep(2)

    logging.info(">> Stop the clock momentarily")
    clock.stop()

    logging.info(">> Now, wait 3 secs")
    time.sleep(3)

    logging.info(">> Start again...")
    clock.start()

    time.sleep(2)

    logging.info(">> Stop the clock")
    clock.stop()
    logging.info(">> Done")
