# tft_local.py Configuration for Pybboard TFT GUI

# This file is intended for definition of the local hardware. It's also a
# convenient place to store constants used on a project such as colors.

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

import uasyncio as asyncio
from machine import Pin, SPI, freq
from micropython import const

_WIDTH = const(480)  # Edit to match your display: 800*480 or 480*272
_HEIGHT = const(272)
_SPI = const(2)  # Edit to match connections
_RESET = 'X4'
_CS = 'X5'

def setup(driver_test=False, use_async=True):
    # Option for Pyboard D
    # freq(216_000_000)
    pinrst = Pin(_RESET, Pin.OUT, value=1)
    pincs = Pin(_CS, Pin.OUT, value=1)
    spi = SPI(_SPI, baudrate=6_000_000)
    if driver_test:
        from micropython_ra8875.driver.ra8875 import RA8875
        loop = asyncio.get_event_loop() if use_async else None
        return RA8875(spi, pincs, pinrst, _WIDTH, _HEIGHT, loop)

    from micropython_ra8875.ugui import Screen, TFT
    loop = asyncio.get_event_loop()
    tft = TFT(spi, pincs, pinrst, _WIDTH, _HEIGHT, loop)
    # Touch panel calibration values xmin, ymin, xmax, ymax
    # values read from ra8875_test.py touching top left and bottom right corners
    # of displayable area (ideally with a stylus for accuracy)
    tft.calibrate(25, 25, 459, 243)
    Screen.setup(tft, tft)
