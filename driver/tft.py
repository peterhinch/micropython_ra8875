# tft.py TFT class for Pybboard TFT GUI

# Released under the MIT License (MIT). See LICENSE.
# Copyright (c) 2019 Peter Hinch

# This file is intended to provide a compatibility layer between the GUI and a
# device driver. It subclasses the driver to enable greying out of controls.
# When porting the GUI to use a driver for another large display, only this
# file, constants.py and tft_local.py should need adapting.

import uasyncio as asyncio
from micropython_ra8875.driver.ra8875 import RA8875
from micropython_ra8875.py.ugui import Screen
from micropython_ra8875.py.colors import *
from micropython_ra8875.driver.constants import *


class TFT(RA8875):
    @staticmethod
    def get_stringsize(s, font):
        hor = 0
        for c in s:
            _, vert, cols = font.get_ch(c)
            hor += cols
        return hor, vert

    def __init__(self, spi, pincs, pinrst, width, height, tdelay, loop):
        super().__init__(spi, pincs, pinrst, width, height, loop)
        self.tdelay = tdelay  # Touch mode
        self._is_grey = False  # Not greyed-out
        self.dim(2)  # Default grey-out: dim colors by factor of 2
        self.desaturate(True)

    # Return a text style (fgcolor, bgcolor, font) modified by tft grey status
    # colors are (r, g, b)
    def text_style(self, style):
        if self._is_grey:
            text_bgc = self._greyfunc(style[1], self._factor)
        else:
            text_bgc = style[1]
        font = style[2]
        if not font.hmap():
            raise UguiException('Font must be horizontally mapped')
        return (style[0], text_bgc, font)

    # Style is (fgcolor, bgcolor, font)
    # Rudimentary: prints a single line.
    def print_left(self, x, y, s, style, tab=32):
        if s == '':
            return
        fgc, bgc, font = self.text_style(style)
        if isinstance(font, IFont):  # Internal font
            self.draw_str(s, x, y, fgc, bgc, font.scale())
        else:
            for c in s:
                if c == '\t':
                    x += tab - x % tab
                else:
                    fmv, rows, cols = font.get_ch(c)
                    self.draw_glyph(fmv, x, y, rows, cols, fgc, bgc)
                    x += cols

    def print_centered(self, x, y, s, style):
        font = style[2]
        length, height = self.get_stringsize(s, font)
        self.print_left(max(x - length // 2, 0), max(y - height // 2, 0), s, style)

    def _getcolor(self, color):
        if self._is_grey:
            color = self._greyfunc(color, self._factor)
        return color

    def desaturate(self, value=None):
        if value is not None:  # Pass a bool to specify desat or dim
            self._desaturate = value  # Save so it can be queried
            def do_dim(color, factor): # Dim a color
                if color is not None:
                    return tuple(int(x / factor) for x in color)

            def do_desat(color, factor): # Desaturate and dim
                if color is not None:
                    f = int(max(color) / factor)
                    return (f, f, f)
            # Specify the local function
            self._greyfunc = do_desat if value else do_dim
        return self._desaturate

    def dim(self, factor=None):
        if factor is not None:
            if factor <= 1:
                raise ValueError('Dim factor must be > 1')
            self._factor = factor
        return self._factor

    def usegrey(self, val): # tft.usegrey(True) sets greyed-out
        self._is_grey = val

    # Clear screen. Base class method is unreliable.
    def clr_scr(self):
        super().fill_rectangle(0, 0, self.width() -1, self.height() -1, BLACK)

    def draw_rectangle(self, x1, y1, x2, y2, color):
        super().draw_rectangle(x1, y1, x2, y2, self._getcolor(color))

    def fill_rectangle(self, x1, y1, x2, y2, color):
        super().fill_rectangle(x1, y1, x2, y2, self._getcolor(color))

    def draw_clipped_rectangle(self, x1, y1, x2, y2, color):
        super().draw_clipped_rectangle(x1, y1, x2, y2, self._getcolor(color))

    def fill_clipped_rectangle(self, x1, y1, x2, y2, color):
         super().fill_clipped_rectangle(x1, y1, x2, y2, self._getcolor(color))

    def draw_circle(self, x, y, radius, color):
        super().draw_circle(x, y, radius, self._getcolor(color))

    def fill_circle(self, x, y, radius, color):
        super().fill_circle(x, y, radius, self._getcolor(color))

    def draw_vline(self, x, y, l, color):
        super().draw_vline(x, y, l, self._getcolor(color))

    def draw_hline(self, x, y, l, color):
        super().draw_hline(x, y, l, self._getcolor(color))

    def draw_line(self, x1, y1, x2, y2, color):
        super().draw_line(x1, y1, x2, y2, self._getcolor(color))

    async def touchtest(self): # Singleton task tests all touchable instances
        td = self.tdelay  # Delay in ms (0 is normal mode)
        x = 0  # Current touch coords
        y = 0
        def dotouch():
            for obj in Screen.current_screen.touchlist:
                if obj.visible and not obj.greyed_out():
                    obj._trytouch(x, y)
        if td:
            tdelay = Delay_ms(func = dotouch, duration = td)
        while True:
            await asyncio.sleep_ms(0)
            if self.ready():
                x, y = self.get_touch()
                if td:
                    if not tdelay():
                        tdelay.trigger()
                else:
                    dotouch()  # Process immediately
            elif not self.touched():
                for obj in Screen.current_screen.touchlist:
                    if obj.was_touched:
                        obj.was_touched = False # Call _untouched once only
                        obj.busy = False
                        obj._untouched()
