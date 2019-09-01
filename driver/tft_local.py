# tft_local.py Configuration for Pybboard TFT GUI

# This file is intended for definition of the local hardware. It's also a
# convenient place to store constants used on a project such as colors.

# Released under the MIT License (MIT). See LICENSE.
# Copyright (c) 2019 Peter Hinch

import uasyncio as asyncio
from machine import Pin, SPI, freq
from micropython import const

# *** EDIT THIS ***
# Match your display: 800*480 or 480*272
_WIDTH = const(480)
_HEIGHT = const(272)
# Match your wiring
_SPI = const(2)
_RESET = 'X4'
_CS = 'X5'
# 0==normal, >0, e.g. 200 == reduce flicker (see docs)
_TOUCH_DELAY = const(0)
# *****************

def setup(driver_test=False, use_async=True):
    # Option for Pyboard D
    # freq(216_000_000)
    pinrst = Pin(_RESET, Pin.OUT, value=1)
    pincs = Pin(_CS, Pin.OUT, value=1)
    spi = SPI(_SPI, baudrate=6_000_000)  # Max that is reliable
    if driver_test:
        from micropython_ra8875.driver.ra8875 import RA8875
        loop = asyncio.get_event_loop() if use_async else None
        return RA8875(spi, pincs, pinrst, _WIDTH, _HEIGHT, loop)

    from micropython_ra8875.py.ugui import Screen
    from micropython_ra8875.driver.tft import TFT
    loop = asyncio.get_event_loop()
    tft = TFT(spi, pincs, pinrst, _WIDTH, _HEIGHT, _TOUCH_DELAY, loop)
    # Touch panel calibration values xmin, ymin, xmax, ymax
    # See docs for calibration procedure
    tft.calibrate(25, 25, 459, 243)  # *** To be updated by cal.py ***
    Screen.setup(tft, tft)
