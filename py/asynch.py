# asynch.py Minimal uasyncio support for ugui
# Code from https://github.com/peterhinch/micropython-async.git

# Released under the MIT License (MIT). See LICENSE.
# Copyright (c) 2019 Peter Hinch

import uasyncio as asyncio
import utime as time

# launch: run a callback or initiate a coroutine depending on which is passed.
async def _g():
    pass
type_coro = type(_g())

# If a callback is passed, run it and return.
# If a coro is passed initiate it and return.
# coros are passed by name i.e. not using function call syntax.
def launch(func, tup_args):
    res = func(*tup_args)
    if isinstance(res, type_coro):
        loop = asyncio.get_event_loop()
        loop.create_task(res)


class Delay_ms(object):
    def __init__(self, func=None, args=(), can_alloc=True, duration=1000):
        self.func = func
        self.args = args
        self.can_alloc = can_alloc
        self.duration = duration  # Default duration
        self.tstop = None  # Not running
        self.loop = asyncio.get_event_loop()
        if not can_alloc:
            self.loop.create_task(self._run())

    async def _run(self):
        while True:
            if self.tstop is None:  # Not running
                await asyncio.sleep_ms(0)
            else:
                await self.killer()

    def stop(self):
        self.tstop = None

    def trigger(self, duration=0):  # Update end time
        if duration <= 0:
            duration = self.duration
        if self.can_alloc and self.tstop is None:  # No killer task is running
            self.tstop = time.ticks_add(time.ticks_ms(), duration)
            # Start a task which stops the delay after its period has elapsed
            self.loop.create_task(self.killer())
        self.tstop = time.ticks_add(time.ticks_ms(), duration)

    def running(self):
        return self.tstop is not None

    __call__ = running

    async def killer(self):
        twait = time.ticks_diff(self.tstop, time.ticks_ms())
        while twait > 0:  # Must loop here: might be retriggered
            await asyncio.sleep_ms(twait)
            if self.tstop is None:
                break  # Return if stop() called during wait
            twait = time.ticks_diff(self.tstop, time.ticks_ms())
        if self.tstop is not None and self.func is not None:
            launch(self.func, self.args)  # Timed out: execute callback
        self.tstop = None  # Not running

class Event():
    def __init__(self, delay_ms=0):
        self.delay_ms = delay_ms
        self.clear()

    def clear(self):
        self._flag = False
        self._data = None

    async def wait(self):  # CPython comptaibility
        while not self._flag:
            await asyncio.sleep_ms(self.delay_ms)

    def __await__(self):
        while not self._flag:
            await asyncio.sleep_ms(self.delay_ms)

    __iter__ = __await__

    def is_set(self):
        return self._flag

    def set(self, data=None):
        self._flag = True
        self._data = data

    def value(self):
        return self._data
