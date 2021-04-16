# scale_log.py Extension to ugui providing the ScaleLog class

# Released under the MIT License (MIT). See LICENSE.
# Copyright (c) 2021 Peter Hinch

# A logarithmic Scale which acts as a touch control
# Usage:
# from micropython_ra8875.widgets.scale_log import ScaleCtrl


import uasyncio as asyncio
from time import ticks_ms, ticks_diff
from math import log10
from micropython_ra8875.py.ugui import Touchable
from micropython_ra8875.driver.constants import SYS_BGCOLOR

# Null function
dolittle = lambda *_ : None


# Start value is 1.0. User applies scaling to value and ticks callback.
class ScaleLog(Touchable):
    def __init__(self, location, font, *, decades=5,
                 height=60, width=300, border=2, value=1.0,
                 fgcolor=None, bgcolor=None, pointercolor=None, fontcolor=None,
                 legendcb=None, tickcb=None,
                 cb_end=dolittle, cbe_args=[], cb_move=dolittle, cbm_args=[]):
        # For correct text rendering inside control must explicitly set bgcolor
        bgcolor = SYS_BGCOLOR if bgcolor is None else bgcolor
        if decades < 3:
            raise ValueError('decades must be >= 3')
        self.mval = 10**decades   # Max value
        self.tickcb = tickcb
        def lcb(f):
            return '{:<1.0f}'.format(f)
        self.legendcb = legendcb if legendcb is not None else lcb
        text_ht = font.height()
        ctrl_ht = 12  # Minimum height for ticks
        min_ht = text_ht + 2 * border + 2  # Ht of text, borders and gap between text and ticks
        if height < min_ht + ctrl_ht:
            height = min_ht + ctrl_ht  # min workable height
        else:
            ctrl_ht = height - min_ht  # adjust ticks for greater height
        width &= 0xfffe  # Make divisible by 2: avoid 1 pixel pointer offset
        # can_drag=True: cause repeated _touched calls
        super().__init__(location, font, height, width,
                         fgcolor, bgcolor, fontcolor, border,
                         True, None, self._constrain(value))
        super()._set_callbacks(cb_move, cbm_args, cb_end, cbe_args)
        border = self.border # border width
        self.x0 = self.location[0] + border
        self.x1 = self.location[0] + self.width - border
        self.y0 = self.location[1] + border
        self.y1 = self.location[1] + self.height - border
        self.ptrcolor = pointercolor if pointercolor is not None else self.fgcolor
        # Define tick dimensions
        ytop = self.y0 + text_ht + 2  # Top of scale graphic (2 pixel gap)
        ycl = ytop + (self.y1 - ytop) // 2  # Centre line
        self.sdl = round(ctrl_ht * 1 / 3)  # Length of small tick.
        self.sdy0 = ycl - self.sdl // 2
        self.mdl = round(ctrl_ht * 2 / 3)  # Medium tick
        self.mdy0 = ycl - self.mdl // 2
        self.ldl = ctrl_ht  # Large tick
        self.ldy0 = ycl - self.ldl // 2
        # Pixel offset of ticks relative to start of decade
        self.toff = []
        self.dw = (self.x1 - self.x0) // 2  # Pixel width of a decade
        #for x in range(1, 11):
            #self.toff.append(log10(x))
        # Bound variables for touch
        self.touch = asyncio.Event()
        self.distance = 0  # Touch distance normalised to -100 <= d <= 100
        self.set_touch()
        asyncio.create_task(self._monitor())

    # itime=time per increment in ms.
    def set_touch(self, itime=200, fmul=1.1, smul=1.01):
        self.itime = itime  # ms per increment
        if fmul <= 1.0:
            raise ValueError('set_touch: fmul must be >1')
        if smul <= 1.0:
            raise ValueError('set_touch: smul must be >1')
        self.fmul = fmul
        self.smul = smul

    # Pre calculated log10(x) for x in range(1, 10)
    def show(self, logs=(0.0, 0.3010, 0.4771, 0.6021, 0.6990, 0.7782, 0.8451, 0.9031, 0.9542)):
        #start = ticks_ms()
        tft = self.tft
        x0: int = self.x0  # Internal rectangle occupied by scale and text
        x1: int = self.x1
        y0: int = self.y0
        y1: int = self.y1
        xc: int = x0 + (x1 - x0) // 2  # x location of pointer
        dw: int = self.dw  # Width of a decade in pixels
        tft.fill_rectangle(x0, y0, x1, y1, self.bgcolor)
        if self._value is None:  # Initial show
            self.value(self._initial_value, show = False) # Prevent recursion
        vc = self._value  # Current value, corresponds to centre of display

        d = int(log10(vc)) - 1  # 10**d is start of a decade guaranteed to be outside display
        vs = max(10 ** d, 1.0)  # vs: start value of current decade
        while True:  # For each decade until we run out of space
            done = True  # Assume completion
            xs: float = xc - dw * log10(vc / vs)  # x location of start of scale
            tick: int
            q: float
            # log10 ~38us on Pi Pico
            for tick, q in enumerate(logs):
                vt: float = vs * (1 + tick)  # Value of current tick
                x: int = round(xs + q * dw)  # x location of current tick
                if x >= x1:
                    break  # All visible ticks drawn
                elif x > x0:  # Tick is visible
                    if not tick:
                        txt = self.legendcb(vt)
                        tlen, _ = tft.get_stringsize(txt, self.font)
                        tft.print_left(min(x, x1 - tlen), y0, txt, self.text_style)
                        ys = self.ldy0  # Large tick
                        yl = self.ldl
                    elif tick == 4:
                        ys = self.mdy0
                        yl = self.mdl
                    else:
                        ys = self.sdy0
                        yl = self.sdl
                    if self.tickcb is None:
                        color = self.fgcolor
                    else:
                        color = self.tickcb(vt, self.fgcolor)
                    tft.draw_vline(x, ys, yl, color)  # Draw tick
                    if (not tick) and (vt > 0.999 * self.mval):
                        break  # Drawn last tick at end of data
            else:
                vs *= 10  # More to do. Next decade.
                done = False
            if done:
                break

        tft.draw_vline(xc, y0, y1 - y0, self.ptrcolor) # Draw pointer
        #print(ticks_diff(ticks_ms(), start)) 75-95ms on Pyboard D depending on calbacks

    def _constrain(self, v):
        return min(max(v, 1.0), self.mval)

    def value(self, val=None, show=True): # User method to get or set value
        if val is not None:
            v = self._constrain(val)
            if self._value is None or v != self._value:
                self._value = v
                self._value_change(show)
        return self._value

    # Process touches. Integer processing for performance on platforms with no
    # FPU, also to reduce allocation.
    async def _monitor(self):
        while True:
            self.distance: int
            if self.distance == 0:
                await self.touch.wait()  # Suspend until touched
                start: int = ticks_ms()
            distance: int = self.distance  # -100 <= distance <= 100
            acc = 1.0 + ticks_diff(ticks_ms(), start) / 2000  # Acceleration
            if distance != 0:
                # Allow fine control near centre
                ad = abs(distance)
                factor = self.smul if ad < 50 else self.fmul
                f = factor * acc if distance > 0 else 1 / (factor * acc)
                self.value(self._value * f, True)  # Show
            await asyncio.sleep_ms(self.itime)
            
    # Touched in bounding box. A long press will call repeatedly.
    def _touched(self, x, y):
        # -100 <= .distance <= 100 Distance is integer for zero detection
        self.distance: int = 200 * (x - self.x0 - self.width // 2) // self.width
        self.touch.set()

    def _untouched(self):
        super()._untouched()
        self.touch.clear()
        self.distance: int = 0
