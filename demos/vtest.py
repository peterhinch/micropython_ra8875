# vtest.py Test/demo of VectorDial

# The MIT License (MIT)
#
# Copyright (c) 2019 Peter Hinch
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

# TODO in GUI
# 1. Can overwrite circle and ticks: applies to arrow and line
# 2. Continues drawing pointers when screen not current

import sys
try:
    import pyb
except ImportError:
    print('This demo is Pyboard specific.')
    sys.exit(0)

from math import pi
import cmath
import uasyncio as asyncio
from micropython_ra8875.support.constants import *
from micropython_ra8875.ugui import Pointer, VectorDial, Label, Button, Screen
from micropython_ra8875.tft_local import setup
import micropython_ra8875.support.font14 as font14

def quitbutton(x, y):
    def quit(button):
        Screen.shutdown()
    Button((x, y), height = 30, font = font14, callback = quit, fgcolor = RED,
           text = 'Quit', shape = RECTANGLE, width = 80)

def fwdbutton(x, y, cls_screen, text='Next'):
    def fwd(button):
        Screen.change(cls_screen)
    Button((x, y), height = 30, font = font14, callback = fwd, fgcolor = RED,
           text = text, shape = RECTANGLE, width = 100)

def backbutton(x, y):
    def back(button):
        Screen.back()
    Button((x, y), height = 30, font = font14, fontcolor = BLACK, callback = back,
           fgcolor = CYAN,  text = 'Back', shape = RECTANGLE, width = 80)

class BackScreen(Screen):
    def __init__(self):
        super().__init__()
        Label((0, 0), font = font14, value = 'Ensure back refreshes properly')
        backbutton(390, 242)

class VScreen(Screen):
    def __init__(self):
        super().__init__()
        fwdbutton(0, 242, BackScreen, 'Forward')
        quitbutton(390, 242)
        dial = VectorDial((0, 0), height = 200, ticks = 12, fgcolor = YELLOW, arrow = True)
        pointers = (Pointer(dial), Pointer(dial))
        loop = asyncio.get_event_loop()
        loop.create_task(self.test(pointers[0]))
        loop.create_task(self.test(pointers[1]))

    async def test(self, pointer):
        x0 = 0
        y0 = 0
        while True:
            x1 = pyb.rng() / 2**29 - 1
            y1 = pyb.rng() / 2**29 - 1
            steps = 20
            dx = (x1 - x0) / steps
            dy = (y1 - y0) / steps
            for _ in range(steps):
                x0 += dx
                y0 += dy
                v = complex(x0, y0)
                mag = cmath.polar(v)[0]
                if mag < 0.3:
                    pointer.value(v, BLUE)
                elif mag < 0.7:
                    pointer.value(v, GREEN)
                else:
                    pointer.value(v, RED)
                await asyncio.sleep_ms(200)


def test():
    print('Test TFT panel...')
    # Instantiate loop before calling setup if you need to change queue sizes
    loop = asyncio.get_event_loop()
    setup()
    Screen.change(VScreen)

test()
