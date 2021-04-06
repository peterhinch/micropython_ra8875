# scaletest.py Test/demo of scale widget for Pybboard RA8875 GUI

# Released under the MIT License (MIT). See LICENSE.
# Copyright (c) 2020 Peter Hinch

# Usage:
# import micropython_ra8875.demos.scaletest

import uasyncio as asyncio
from micropython_ra8875.driver.constants import *
from micropython_ra8875.py.colors import *
from micropython_ra8875.py.ugui import Screen
from micropython_ra8875.fonts import font10, font14
from micropython_ra8875.widgets.buttons import Button
from micropython_ra8875.widgets.label import Label
from micropython_ra8875.widgets.scale import Scale
from micropython_ra8875.driver.tft_local import setup


def quitbutton(x, y):
    def quit(button):
        Screen.shutdown()
    Button((x, y), height = 30, font = font14, callback = quit, fgcolor = RED,
           text = 'Quit', shape = RECTANGLE, width = 80)


class BaseScreen(Screen):
    def __init__(self):
        super().__init__()
        # Scale with custom variable and legends.
        Label((0, 0), font = font14, value = 'FM radio scale 88-108MHz.')
        def legendcb(f):
            return '{:2.0f}'.format(88 + ((f + 1) / 2) * (108 - 88))
        self.scale = Scale((0, 30), font10, legendcb = legendcb, width = 350, height = 60,
                           bgcolor = BLACK, fgcolor = GREEN, pointercolor = RED, fontcolor = YELLOW)
        self.reg_task(self.radio())
        # Scale with varying color.
        Label((0, 130), font = font14, value = 'Default scale -1 to +1, varying colors.')
        def tickcb(f, c):
            if f > 0.8:
                return RED
            if f < -0.8:
                return BLUE
            return c
        self.lbl_result = Label((0, 240), font = font14, fontcolor = WHITE, width = 70,
                                border = 2, fgcolor = RED, bgcolor = DARKGREEN)
        self.scale1 = Scale((0, 160), font10, tickcb = tickcb, width = 350, height = 60,
                           bgcolor = BLACK, fgcolor = GREEN, pointercolor = RED, fontcolor = YELLOW)
        self.reg_task(self.default())
        quitbutton(390, 242)

# COROUTINES
    async def radio(self):
        cv = 88.0  # Current value
        val = 108.0  # Target value
        while True:
            v1, v2 = val, cv
            steps = 200
            delta = (val - cv) / steps
            for _ in range(steps):
                cv += delta
                # Map user variable to -1.0..+1.0
                self.scale.value(2 * (cv - 88)/(108 - 88) - 1)
                await asyncio.sleep_ms(200)
            val, cv = v2, v1

    async def default(self):
        cv = -1.0  # Current
        val = 1.0
        while True:
            v1, v2 = val, cv
            steps = 400
            delta = (val - cv) / steps
            for _ in range(steps):
                cv += delta
                self.scale1.value(cv)
                self.lbl_result.value('{:4.3f}'.format(cv))
                await asyncio.sleep_ms(250)
            val, cv = v2, v1


def test():
    setup()
    Screen.change(BaseScreen)

test()
