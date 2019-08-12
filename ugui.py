# ugui.py Micropython GUI library for RA8875 displays
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
import math
import gc
from micropython import const

from micropython_ra8875.support.aswitch import Delay_ms
from micropython_ra8875.support.asyn import Event
from micropython_ra8875.driver.ra8875 import RA8875
from micropython_ra8875.support.constants import *

TWOPI = 2 * math.pi
gc.collect()

# *********** UTILITY FUNCTIONS ***********

class ugui_exception(Exception):
    pass

# Null function
dolittle = lambda *_ : None

def get_stringsize(s, font):
    hor = 0
    for c in s:
        _, vert, cols = font.get_ch(c)
        hor += cols
    return hor, vert

# Style is (fgcolor, bgcolor, font)
def print_centered(tft, x, y, s, style):
    font = style[2]
    length, height = get_stringsize(s, font)
    tft.text_style(style)
    tft.print_string(s, max(x - length // 2, 0), max(y - height // 2, 0))

def print_left(tft, x, y, s, style):
    tft.text_style(style)
    tft.print_string(s, x, y)

def dim(color, factor): # Dim a color
    if color is not None:
        return tuple(int(x / factor) for x in color)

def desaturate(color, factor): # Desaturate and dim
    if color is not None:
        f = int(max(color) / factor)
        return (f, f, f)

# *********** TFT CLASS ************
# Subclass TFT to enable greying out of controls
# Some TFT methods call drawHLine and drawVLine: the bound variable 'raw` forces them
# to use the color of the calling method
class TFT(RA8875):
    def __init__(self, spi, pincs, pinrst, width, height, loop):
        super().__init__(spi, pincs, pinrst, width, height, loop)
        self._is_grey = False
        self._desaturate = True
        self._greyfunc = desaturate
        self._factor = 2 # Default grey-out methd: dim colors
        self.fgcolor = WHITE
        self.bgcolor = BLACK
        self.text_fgcolor = self.fgcolor # colors set by user
        self.text_bgcolor = self.bgcolor
        self.text_fgc = self.fgcolor    # colors used by text rendering allowing for grey status
        self.text_bgc = self.bgcolor
        self.text_font = None

    def get_fgcolor(self):
        return self.fgcolor

    def get_bgcolor(self):
        return self.bgcolor

    # Get or set the text style (fgcolor, bgcolor, font)
    # colors are (r, g, b)
    # Sets self.text_bgc and self.text_fgc for rendering methods
    def text_style(self, style=None):
        if style is None:
            return (self.text_fgcolor, self.text_bgcolor, self.text_font)

        if self._is_grey:
            self.text_bgc = self._greyfunc(style[1], self._factor)
        else:
            self.text_bgc = style[1]
        self.text_fgc = style[0]
        font = style[2]
        if not font.hmap():
            raise UguiException('Font must be horizontally mapped')
        self.text_font = font
        return (self.text_fgc, self.text_bgc, font)

    # Rudimentary: prints a single line. No handling of control chars
    def print_string(self, s, x, y):
        font = self.text_font
        fgc = self.text_fgc
        bgc = self.text_bgc
        for c in s:
            fmv, rows, cols = font.get_ch(c)
            self.draw_glyph(fmv, x, y, rows, cols, fgc, bgc)
            x += cols

    def _getcolor(self, color):
        if self._is_grey:
            color = self._greyfunc(color, self._factor)
        return color

    def desaturate(self, value=None):
        if value is not None:  # Pass a bool to specify desat or dim
            self._desaturate = value  # Save so it can be queried
            # Specify the global function
            self._greyfunc = desaturate if value else dim
        return self._desaturate

    def dim(self, factor=None):
        if factor is not None:
            if factor <= 1:
                raise ValueError('Dim factor must be > 1')
            self._factor = factor
        return self._factor

    def usegrey(self, val): # tft.usegrey(True) sets greyed-out
        self._is_grey = val

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

# *********** BASE CLASSES ***********

class Screen:
    current_screen = None
    tft = None
    objtouch = None
    is_shutdown = Event()

    @classmethod
    def setup(cls, tft, objtouch=None):
        cls.objtouch = objtouch if objtouch is not None else tft
        cls.tft = tft

# get_tft() when called from user code, ensure greyed_out status is updated.
    @classmethod
    def get_tft(cls, greyed_out=False):
        cls.tft.usegrey(greyed_out)
        return cls.tft

    @classmethod
    def set_grey_style(cls, *, desaturate=True, factor=2):
        cls.tft.dim(factor)
        cls.tft.desaturate(desaturate)
        if Screen.current_screen is not None: # Can call before instantiated
            for obj in Screen.current_screen.displaylist:
                if obj.visible and obj.greyed_out():
                    obj.redraw = True # Redraw static content
                    obj.draw_border()
                    obj.show()

    @classmethod
    def show(cls):
        for obj in cls.current_screen.displaylist:
            if obj.visible: # In a buttonlist only show visible button
                obj.redraw = True # Redraw static content
                obj.draw_border()
                obj.show()

    @classmethod
    def change(cls, cls_new_screen, *, forward=True, args=[], kwargs={}):
        init = cls.current_screen is None
        if init:
            Screen() # Instantiate a blank starting screen
        cs_old = cls.current_screen
        cs_old.on_hide() # Optional method in subclass
        if forward:
            if isinstance(cls_new_screen, type):
                new_screen = cls_new_screen(*args, **kwargs) # Instantiate new screen
            else:
                raise ValueError('Must pass Screen class or subclass (not instance)')
            new_screen.parent = cs_old
            cs_new = new_screen
        else:
            cs_new = cls_new_screen # An object, not a class
        cls.current_screen = cs_new
        cs_new.on_open() # Optional subclass method
        cs_new._do_open(cs_old) # Clear and redraw
        cs_new.after_open() # Optional subclass method
        if init:
            loop = asyncio.get_event_loop()
            loop.run_until_complete(Screen.monitor())

    @classmethod
    async def monitor(cls):
        await cls.is_shutdown

    @classmethod
    def back(cls):
        parent = cls.current_screen.parent
        if parent is not None:
            cls.change(parent, forward = False)

    @classmethod
    def addobject(cls, obj):
        if cls.current_screen is None:
            raise OSError('You must create a Screen instance')
        if isinstance(obj, Touchable):
            cls.current_screen.touchlist.append(obj)
        cls.current_screen.displaylist.append(obj)

    @classmethod
    def shutdown(cls):
        cls.tft.clr_scr()
        cls.is_shutdown.set()

    def __init__(self):
        self.touchlist = []
        self.displaylist = []
        self.modal = False
        if Screen.current_screen is None: # Initialising class and thread
            loop = asyncio.get_event_loop()
            loop.create_task(self._touchtest()) # One thread only
            loop.create_task(self._garbage_collect())
        Screen.current_screen = self
        self.parent = None

    async def _touchtest(self): # Singleton thread tests all touchable instances
        touch_panel = Screen.objtouch
        while True:
            await asyncio.sleep_ms(0)
            if touch_panel.ready():
                x, y = touch_panel.get_touch()
                for obj in Screen.current_screen.touchlist:
                    if obj.visible and not obj.greyed_out():
                        obj._trytouch(x, y)
            elif not touch_panel.touched():
                for obj in Screen.current_screen.touchlist:
                    if obj.was_touched:
                        obj.was_touched = False # Call _untouched once only
                        obj.busy = False
                        obj._untouched()

    def _do_open(self, old_screen): # Aperture overrides
        show_all = True
        tft = Screen.get_tft()
# If opening a Screen from an Aperture just blank and redraw covered area
        if old_screen.modal:
            show_all = False
            x0, y0, x1, y1 = old_screen._list_dims()
            tft.fill_rectangle(x0, y0, x1, y1, tft.get_bgcolor()) # Blank to screen BG
            for obj in [z for z in self.displaylist if z.overlaps(x0, y0, x1, y1)]:
                if obj.visible:
                    obj.redraw = True # Redraw static content
                    obj.draw_border()
                    obj.show()
# Normally clear the screen and redraw everything
        else:
            tft.clr_scr()
            Screen.show()

    def on_open(self): # Optionally implemented in subclass
        return

    def after_open(self): # Optionally implemented in subclass
        return

    def on_hide(self): # Optionally implemented in subclass
        return

    async def _garbage_collect(self):
        while True:
            await asyncio.sleep_ms(100)
            gc.collect()
            gc.threshold(gc.mem_free() // 4 + gc.mem_alloc())

# Very basic window class. Cuts a rectangular hole in a screen on which content may be drawn
class Aperture(Screen):
    _value = None
    def __init__(self, location, height, width, *, draw_border=True, bgcolor=None, fgcolor=None):
        Screen.__init__(self)
        self.location = location
        self.height = height
        self.width = width
        self.draw_border = draw_border
        self.modal = True
        tft = Screen.get_tft()
        self.fgcolor = fgcolor if fgcolor is not None else tft.get_fgcolor()
        self.bgcolor = bgcolor if bgcolor is not None else tft.get_bgcolor()

    def locn(self, x, y):
        return (self.location[0] + x, self.location[1] + y)

    def _do_open(self, old_screen):
        tft = Screen.get_tft()
        x, y = self.location[0], self.location[1]
        tft.fill_rectangle(x, y, x + self.width, y + self.height, self.bgcolor)
        if self.draw_border:
            tft.draw_rectangle(x, y, x + self.width, y + self.height, self.fgcolor)
        Screen.show()

    def _list_dims(self):
        x0 = self.location[0]
        x1 = self.location[0] + self.width
        y0 = self.location[1]
        y1 = self.location[1] + self.height
        return x0, y0, x1, y1

    @classmethod
    def value(cls, val=None): # Mechanism for testing the outcome of a dialog box
        if val is not None:
            cls._value = val
        return cls._value

# Base class for all displayable objects
class NoTouch:
    _greyed_out = False # Disabled by user code

    def __init__(self, location, font, height, width, fgcolor, bgcolor, fontcolor, border, value, initial_value):
        Screen.addobject(self)
        self.screen = Screen.current_screen
        self.redraw = True # Force drawing of static part of image
        self.location = location
        self._value = value
        self._initial_value = initial_value # Optionally enables show() method to handle initialisation
        self.fontcolor = WHITE if fontcolor is None else fontcolor
        self.height = height
        self.width = width
        self.fill = bgcolor is not None
        self.visible = True # Used by ButtonList class for invisible buttons
        tft = Screen.get_tft(False) # Not greyed out
        if font is None:
            self.font = tft.text_font
        else:
            self.font = font

        if fgcolor is None:
            self.fgcolor = tft.get_fgcolor()
            if bgcolor is None:
                self.bgcolor = tft.get_bgcolor()
            else:
                self.bgcolor = bgcolor
            self.fontbg = self.bgcolor
        else:
            self.fgcolor = fgcolor
            if bgcolor is None:
                self.bgcolor = tft.get_bgcolor()  # black surround to circle button etc
                # Fonts are drawn on bg of foreground color e.g. for buttons
                self.fontbg = fgcolor
            else:
                self.bgcolor = bgcolor
                self.fontbg = bgcolor

        self.text_style = tft.text_style((self.fontcolor, self.fontbg, self.font))
        self.border = 0 if border is None else int(max(border, 0)) # width
        self.callback = dolittle # Value change callback
        self.args = []
        self.cb_end = dolittle # Touch release callbacks
        self.cbe_args = []

    @property
    def tft(self):
        return Screen.get_tft(self._greyed_out)

    def greyed_out(self):
        return self._greyed_out # Subclass may be greyed out

    def value(self, val=None, show=True): # User method to get or set value
        if val is not None:
            if type(val) is float:
                val = min(max(val, 0.0), 1.0)
            if val != self._value:
                self._value = val
                self._value_change(show)
        return self._value

    def _value_change(self, show): # Optional override in subclass
        self.callback(self, *self.args) # CB is not a bound method. 1st arg is self
        if show:
            self.show_if_current()

    def show_if_current(self):
        if self.screen is Screen.current_screen:
            self.show()

# Called by Screen.show(). Draw background and bounding box if required
    def draw_border(self):
        if self.screen is Screen.current_screen:
            tft = self.tft
            x = self.location[0]
            y = self.location[1]
            if self.fill:
                tft.fill_rectangle(x, y, x + self.width, y + self.height, self.bgcolor)
            if self.border > 0: # Draw a bounding box
                tft.draw_rectangle(x, y, x + self.width, y + self.height, self.fgcolor)
        return self.border # border width in pixels

    def overlaps(self, xa, ya, xb, yb): # Args must be sorted: xb > xa and yb > ya
        x0 = self.location[0]
        y0 = self.location[1]
        x1 = x0 + self.width
        y1 = y0 + self.height
        if (ya <= y1 and yb >= y0) and (xa <= x1 and xb >= x0):
            return True
        return False

# Base class for touch-enabled classes.
class Touchable(NoTouch):
    def __init__(self, location, font, height, width, fgcolor, bgcolor, fontcolor, border, can_drag, value, initial_value):
        super().__init__(location, font, height, width, fgcolor, bgcolor, fontcolor, border, value, initial_value)
        self.can_drag = can_drag
        self.busy = False
        self.was_touched = False

    def _set_callbacks(self, cb, args, cb_end=None, cbe_args=None):
        self.callback = cb
        self.args = args
        if cb_end is not None:
            self.cb_end = cb_end
            self.cbe_args = cbe_args

    def greyed_out(self, val=None):
        if val is not None and self._greyed_out != val:
            tft = self.tft
            tft.usegrey(val)
            self._greyed_out = val
            self.draw_border()
            self.redraw = True
            self.show_if_current()
        return self._greyed_out

    def _trytouch(self, x, y): # If touched in bounding box, process it otherwise do nothing
        x0 = self.location[0]
        x1 = self.location[0] + self.width
        y0 = self.location[1]
        y1 = self.location[1] + self.height
        if x0 <= x <= x1 and y0 <= y <= y1:
            self.was_touched = True
            if not self.busy or self.can_drag:
                self._touched(x, y) # Called repeatedly for draggable objects
                self.busy = True # otherwise once only

    def _untouched(self): # Default if not defined in subclass
        self.cb_end(self, *self.cbe_args) # Callback not a bound method so pass self

# *********** DISPLAYS: NON-TOUCH CLASSES FOR DATA DISPLAY ***********

class Label(NoTouch):
    def __init__(self, location, *, font, border=None, width=None, fgcolor=None, bgcolor=None, fontcolor=None, value=None):
        if width is None:
            if value is None:
                raise ValueError('If label value unspecified, must define the width')
            width, _ = get_stringsize(value, font) 
        super().__init__(location, font, None, width, fgcolor, bgcolor, fontcolor, border, value, None)
        self.height = self.font.height()
        self.height += 2 * self.border  # Height determined by font and border

    def show(self):
        tft = self.tft
        bw = self.border
        x = self.location[0]
        y = self.location[1]
        tft.fill_rectangle(x + bw, y + bw, x + self.width - bw, y + self.height - bw, self.bgcolor)
        if self._value is not None:
            print_left(tft, x + bw, y + bw, self._value, self.text_style)

# class displays angles. Angle 0 is vertical, +ve increments are clockwise.
class Dial(NoTouch):
    def __init__(self, location, *, height=100, fgcolor=None, bgcolor=None, border=None, pointers=(0.9,), ticks=4):
        super().__init__(location, None, height, height, fgcolor, bgcolor, None, border, 0, 0)
        border = self.border # border width
        radius = height / 2 - border
        self.radius = radius
        self.ticks = ticks
        self.xorigin = location[0] + border + radius
        self.yorigin = location[1] + border + radius
        self.pointers = tuple(z * self.radius for z in pointers) # Pointer lengths
        self.angles = [None for _ in pointers]
        self.new_value = None

    def show(self):
        tft = self.tft
        ticks = self.ticks
        radius = self.radius
        ticklen = 0.1 * radius
        for tick in range(ticks):
            theta = 2 * tick * math.pi / ticks
            x_start = int(self.xorigin + radius * math.sin(theta))
            y_start = int(self.yorigin - radius * math.cos(theta))
            x_end = int(self.xorigin + (radius - ticklen) * math.sin(theta))
            y_end = int(self.yorigin - (radius - ticklen) * math.cos(theta))
            tft.draw_line(x_start, y_start, x_end, y_end, self.fgcolor)
        tft.draw_circle(self.xorigin, self.yorigin, radius, self.fgcolor)
        for idx, ang in enumerate(self.angles):
            if ang is not None:
                self._drawpointer(ang, idx, self.bgcolor) # erase old
        if self.new_value is not None:
            self.angles[self.new_value[1]] = self.new_value[0]
            self.new_value = None

        for idx, ang in enumerate(self.angles):
            if ang is not None:
                self._drawpointer(ang, idx, self.fgcolor)

    def value(self, angle, pointer=0):
        if pointer > len(self.pointers):
            raise ValueError('pointer index out of range')
        self.new_value = [angle, pointer]
        self.show_if_current()

    def _drawpointer(self, radians, pointer, color):
        tft = self.tft
        length = self.pointers[pointer]
        x_end = int(self.xorigin + length * math.sin(radians))
        y_end = int(self.yorigin - length * math.cos(radians))
        tft.draw_line(int(self.xorigin), int(self.yorigin), x_end, y_end, color)

class LED(NoTouch):
    def __init__(self, location, *, border=2, height=30, fgcolor=None, bgcolor=None, color=RED):
        super().__init__(location, None, height, height, fgcolor, bgcolor, None, border, False, False)
        self._value = False
        self._color = color
        self.radius = (self.height - 2 * self.border) / 2
        self.x = location[0] + self.radius + self.border
        self.y = location[1] + self.radius + self.border

    def show(self):
        tft = self.tft
        color = self._color if self._value else BLACK
        tft.fill_circle(int(self.x), int(self.y), int(self.radius), color)
        tft.draw_circle(int(self.x), int(self.y), int(self.radius), self.fgcolor)

    def color(self, color):
        self._color = color
        self.show_if_current()

class Meter(NoTouch):
    def __init__(self, location, *, font=None, height=200, width=30,
                 fgcolor=None, bgcolor=None, pointercolor=None, fontcolor=None,
                 divisions=10, legends=None, value=0):
        border = 5 if font is None else 1 + font.height() / 2
        super().__init__(location, font, height, width, fgcolor, bgcolor, fontcolor, border, value, None)
        border = self.border # border width
        self.savebuf = memoryview(bytearray((self.width + 3) * 2))  # 2 bytes per pixel
        self.x0 = self.location[0]
        self.x1 = self.location[0] + self.width
        self.y0 = self.location[1] + border + 2
        self.y1 = self.location[1] + self.height - border
        self.divisions = divisions
        self.legends = legends
        self.pointercolor = pointercolor if pointercolor is not None else self.fgcolor
        self.ptr_y = None # Invalidate old position

    def show(self):
        tft = self.tft
        width = self.width
        dx = 5
        x0 = self.x0
        x1 = self.x1
        y0 = self.y0
        y1 = self.y1
        height = y1 - y0
        if self.divisions > 0:
            dy = height / (self.divisions) # Tick marks
            for tick in range(self.divisions + 1):
                ypos = int(y0 + dy * tick)
                tft.draw_hline(x0, ypos, dx, self.fgcolor)
                tft.draw_hline(x1 - dx, ypos, dx, self.fgcolor)

        if self.legends is not None and self.font is not None: # Legends
            if len(self.legends) <= 1:
                dy = 0
            else:
                dy = height / (len(self.legends) -1)
            yl = self.y1 # Start at bottom
            for legend in self.legends:
                print_centered(tft, int(self.x0 + self.width /2), int(yl), legend, self.text_style)
                yl -= dy

        tft = self.tft
        if self.ptr_y is not None: # Restore background if it was saved
            tft.restore_region(self.savebuf, x0 - 2, self.ptr_y, x1, self.ptr_y)
        self.ptr_y = int(self.y1 - self._value * height) # y position of slider
        tft.save_region(self.savebuf, x0 - 1, self.ptr_y, x1 + 1, self.ptr_y) # Read background
        tft.draw_hline(x0, self.ptr_y, width, self.pointercolor) # Draw pointer

class MeterFlicker(NoTouch):
    def __init__(self, location, *, font=None, height=200, width=30,
                 fgcolor=None, bgcolor=None, pointercolor=None, fontcolor=None,
                 divisions=10, legends=None, value=0):
        border = 5 if font is None else 1 + font.height() / 2
        super().__init__(location, font, height, width, fgcolor, bgcolor, fontcolor, border, value, None)
        border = self.border # border width
        self.x0 = self.location[0]
        self.x1 = self.location[0] + self.width
        self.y0 = self.location[1] + border + 2
        self.y1 = self.location[1] + self.height - border
        self.divisions = divisions
        self.legends = legends
        self.pointercolor = pointercolor if pointercolor is not None else self.fgcolor
        self.ptr_y = None # Invalidate old position

    def show(self):
        tft = self.tft
        width = self.width
        dx = 5
        x0 = self.x0
        x1 = self.x1
        y0 = self.y0
        y1 = self.y1
        height = y1 - y0
        tft.fill_rectangle(x0 + 1, y0, x1 - 1, y1, self.bgcolor)
        if self.divisions > 0:
            dy = height / (self.divisions) # Tick marks
            for tick in range(self.divisions + 1):
                ypos = int(y0 + dy * tick)
                tft.draw_hline(x0, ypos, dx, self.fgcolor)
                tft.draw_hline(x1 - dx, ypos, dx, self.fgcolor)

        if self.legends is not None and self.font is not None: # Legends
            if len(self.legends) <= 1:
                dy = 0
            else:
                dy = height / (len(self.legends) -1)
            yl = self.y1 # Start at bottom
            for legend in self.legends:
                print_centered(tft, int(self.x0 + self.width /2), int(yl), legend, self.text_style)
                yl -= dy

        self.ptr_y = int(self.y1 - self._value * height) # y position of slider
        tft.draw_hline(x0 + 2, self.ptr_y, x1 - x0 - 4, self.pointercolor) # Draw pointer

# *********** PUSHBUTTON AND CHECKBOX CLASSES ***********

# Button coordinates relate to bounding box (BB). x, y are of BB top left corner.
# likewise width and height refer to BB, regardless of button shape
# If font is None button will be rendered without text

class Button(Touchable):
    lit_time = 1000
    long_press_time = 1000
    def __init__(self, location, *, font, shape=RECTANGLE, height=50, width=50, fill=True,
                 fgcolor=None, bgcolor=None, fontcolor=None, litcolor=None, text='',
                 callback=dolittle, args=[], onrelease=True, lp_callback=None, lp_args=[]):
        super().__init__(location, font, height, width, fgcolor, bgcolor, fontcolor, None, False, text, None)
        self.shape = shape
        self.radius = height // 2
        self.fill = fill
        self.litcolor = litcolor
        self.text = text
        self.callback = callback
        self.callback_args = args
        self.onrelease = onrelease
        self.lp_callback = lp_callback
        self.lp_args = lp_args
        self.lp = False # Long press not in progress
        self.orig_fgcolor = fgcolor
        if self.litcolor is not None:
            self.delay = Delay_ms(self.shownormal)
        self.litcolor = litcolor if self.fgcolor is not None else None

    def show(self):
        tft = self.tft
        x = self.location[0]
        y = self.location[1]
        if not self.visible:   # erase the button
            tft.usegrey(False)
            tft.fill_rectangle(x, y, x + self.width, y + self.height, self.bgcolor)
            return
        if self.shape == CIRCLE:  # Button coords are of top left corner of bounding box
            x += self.radius
            y += self.radius
            if self.fill:
                tft.fill_circle(x, y, self.radius, self.fgcolor)
            else:
                tft.draw_circle(x, y, self.radius, self.fgcolor)
            if self.font is not None and len(self.text):
                print_centered(tft, x, y, self.text, self.text_style)
        else:
            x1 = x + self.width
            y1 = y + self.height
            if self.shape == RECTANGLE: # rectangle
                if self.fill:
                    tft.fill_rectangle(x, y, x1, y1, self.fgcolor)
                else:
                    tft.draw_rectangle(x, y, x1, y1, self.fgcolor)
                if self.font  is not None and len(self.text):
                    print_centered(tft, (x + x1) // 2, (y + y1) // 2, self.text, self.text_style)
            elif self.shape == CLIPPED_RECT: # clipped rectangle
                if self.fill:
                    tft.fill_clipped_rectangle(x, y, x1, y1, self.fgcolor)
                else:
                    tft.draw_clipped_rectangle(x, y, x1, y1, self.fgcolor)
                if self.font  is not None and len(self.text):
                    print_centered(tft, (x + x1) // 2, (y + y1) // 2, self.text, self.text_style)

    def shownormal(self):
        self.fgcolor = self.orig_fgcolor
        tft = self.tft
        self.text_style = tft.text_style((self.fontcolor, self.fontbg, self.font))
        self.show_if_current()

    def _touched(self, x, y): # Process touch
        if self.litcolor is not None:
            self.fgcolor = self.litcolor
            tft = self.tft
            self.text_style = tft.text_style((self.fontcolor, self.fgcolor, self.font))
            self.show() # must be on current screen
            self.delay.trigger(Button.lit_time)
        if self.lp_callback is not None:
            loop = asyncio.get_event_loop()
            loop.create_task(self.longpress())
        if not self.onrelease:
            self.callback(self, *self.callback_args) # Callback not a bound method so pass self

    def _untouched(self):
        self.lp = False
        if self.onrelease:
            self.callback(self, *self.callback_args) # Callback not a bound method so pass self

    async def longpress(self):
        self.lp = True
        await asyncio.sleep_ms(self.long_press_time)
        if self.lp:
            self.lp_callback(self, *self.lp_args)

# Group of buttons, typically at same location, where pressing one shows
# the next e.g. start/stop toggle or sequential select from short list
class ButtonList:
    def __init__(self, callback=dolittle):
        self.user_callback = callback
        self.lstbuttons = []
        self.current = None # No current button
        self._greyed_out = False

    def add_button(self, *args, **kwargs):
        button = Button(*args, **kwargs)
        self.lstbuttons.append(button)
        active = self.current is None # 1st button added is active
        button.visible = active
        button.callback = self._callback
        if active:
            self.current = button
        return button

    def value(self, button=None):
        if button is not None and button is not self.current:
            old = self.current
            new = button
            self.current = new
            old.visible = False
            old.show()
            new.visible = True
            new.show()
            self.user_callback(new, *new.callback_args)
        return self.current

    def greyed_out(self, val=None):
        if val is not None and self._greyed_out != val:
            self._greyed_out = val
            for button in self.lstbuttons:
                button.greyed_out(val)
            self.current.show()
        return self._greyed_out

    def _callback(self, button, *args):
        old = button
        old_index = self.lstbuttons.index(button)
        new = self.lstbuttons[(old_index + 1) % len(self.lstbuttons)]
        self.current = new
        old.visible = False
        old.show()
        new.visible = True
        new.busy = True # Don't respond to continued press
        new.show()
        self.user_callback(new, *args) # user gets button with args they specified

# Group of buttons at different locations, where pressing one shows
# only current button highlighted and oes callback from current one
class RadioButtons(object):
    def __init__(self, highlight, callback=dolittle, selected=0):
        self.user_callback = callback
        self.lstbuttons = []
        self.current = None # No current button
        self.highlight = highlight
        self.selected = selected
        self._greyed_out = False

    def add_button(self, *args, **kwargs):
        button = Button(*args, **kwargs)
        self.lstbuttons.append(button)
        button.callback = self._callback
        active = len(self.lstbuttons) == self.selected + 1
        button.fgcolor = self.highlight if active else button.orig_fgcolor
        if active:
            tft = button.tft
            button.text_style = tft.text_style((button.fontcolor, button.fgcolor, button.font))
            self.current = button
        return button

    def value(self, button=None):
        if button is not None and button is not self.current:
            self._callback(button, *button.callback_args)
        return self.current

    def greyed_out(self, val=None):
        if val is not None and self._greyed_out != val:
            self._greyed_out = val
            for button in self.lstbuttons:
                button.greyed_out(val)
        return self._greyed_out

    def _callback(self, button, *args):
        for but in self.lstbuttons:
            if but is button:
                but.fgcolor = self.highlight
                self.current = button
            else:
                but.fgcolor = but.orig_fgcolor
            tft = but.tft
            but.text_style = tft.text_style((but.fontcolor, but.fgcolor, but.font))
            but.show()
        self.user_callback(button, *args) # user gets button with args they specified

class Checkbox(Touchable):
    def __init__(self, location, *, height=30, fillcolor=None,
                 fgcolor=None, bgcolor=None, callback=dolittle, args=[], value=False, border=None):
        super().__init__(location, None, height, height, fgcolor, bgcolor, None, border, False, value, None)
        super()._set_callbacks(callback, args)
        self.fillcolor = fillcolor

    def show(self):
        if self._initial_value is None:
            self._initial_value = True
            value = self._value # As passed to ctor
            if value is None:
                self._value = False # special case: don't execute callback on initialisation
            else:
                self._value = not value # force redraw
                self.value(value)
                return
        self._show()

    def _show(self):
        tft = self.tft
        bw = self.border
        x = self.location[0] + bw
        y = self.location[1] + bw
        height = self.height - 2 * bw
        x1 = x + height
        y1 = y + height
        if self._value:
            if self.fillcolor is not None:
                tft.fill_rectangle(x, y, x1, y1, self.fillcolor)
        else:
            tft.fill_rectangle(x, y, x1, y1, self.bgcolor)
        tft.draw_rectangle(x, y, x1, y1, self.fgcolor)
        if self.fillcolor is None and self._value:
            tft.draw_line(x, y, x1, y1, self.fgcolor)
            tft.draw_line(x, y1, x1, y, self.fgcolor)

    def _touched(self, x, y): # Was touched
        self.value(not self._value) # Upddate and refresh

# *********** SLIDER CLASSES ***********
# A slider's text items lie outside its bounding box (area sensitive to touch)

_SLIDE_DEPTH = const(6)  # Must be divisible by 2
_TICK_VISIBLE = const(3)  # No. of tick pixels visible either side of slider
_HALF_SLOT_WIDTH = const(2)  # Width of slot /2

# Slider ontrols have been rewritten to avoid the need for reading back framebuffer
# contents as this is unreliable on RA8875.
class Slider(Touchable):
    def __init__(self, location, *, font=None, height=200, width=30, divisions=10, legends=None,
                 fgcolor=None, bgcolor=None, fontcolor=None, slidecolor=None, border=None, 
                 cb_end=dolittle, cbe_args=[], cb_move=dolittle, cbm_args=[], value=0.0):
        width &= 0xfe # ensure divisible by 2
        super().__init__(location, font, height, width, fgcolor, bgcolor, fontcolor, border, True, None, value)
        super()._set_callbacks(cb_move, cbm_args, cb_end, cbe_args)
        self.divisions = divisions
        self.legends = legends if font is not None else None
        self.slidecolor = slidecolor
        self.slideheight = _SLIDE_DEPTH
        # Define the internal region of the control
        bw = self.border
        self.x0 = self.location[0] + bw  # Start
        self.y0 = self.location[1] + bw
        self.dx = width - 2 * bw  # Width
        self.x1 = self.x0 + self.dx  # End
        self.y1 = self.location[1] + height - bw
        # Define slider
        self.slide_x0 = self.x0 + _TICK_VISIBLE  # Draw slider shorter than ticks
        self.slide_x1 = self.location[0] + width - bw - _TICK_VISIBLE
        # y coord of top left hand corner of slide when value == 0
        self.slide_y0 = self.location[1] + height - bw - _SLIDE_DEPTH - 1
        # Slot coordinates
        centre = self.x0 + self.dx // 2
        self.slot_x0 = centre - _HALF_SLOT_WIDTH
        self.slot_x1 = centre + _HALF_SLOT_WIDTH
        self.slot_y0 = self.y0 + _SLIDE_DEPTH // 2
        self.slot_y1 = self.y1 - _SLIDE_DEPTH // 2 - 1
        # Length of travel of slider
        self.slot_len = self.slot_y1 - self.slot_y0
        # Prevent Label objects being added to display list when already there.
        self.drawn = False

    def show(self):
        tft = self.tft
        # Blank slot, ticks and slider
        tft.fill_rectangle(self.x0, self.y0, self.x1, self.y1, self.bgcolor)
        self.redraw = False
        x = self.x0
        y = self.slot_y0
        slot_len = self.slot_len # Height of slot
        if self.divisions > 0:
            dy = slot_len / (self.divisions) # Tick marks
            xs = x + 1
            xe = x + self.dx -1
            for tick in range(self.divisions + 1):
                ypos = int(y + dy * tick)
                tft.draw_line(xs, ypos, xe, ypos, self.fgcolor)
        # Blank and redraw slot
        tft.fill_rectangle(self.slot_x0, self.slot_y0, self.slot_x1, self.slot_y1, self.bgcolor)
        tft.draw_rectangle(self.slot_x0, self.slot_y0, self.slot_x1, self.slot_y1, self.fgcolor)

        # Legends: if redrawing, they are already on the Screen's display list
        if self.legends is not None and not self.drawn:
            if len(self.legends) <= 1:
                dy = 0
            else:
                dy = slot_len / (len(self.legends) -1)
            yl = y + slot_len # Start at bottom
            fhdelta = self.font.height() / 2
            font = self.font
            for legend in self.legends:
                loc = (x + self.width, int(yl - fhdelta))
                Label(loc, font = font, fontcolor = self.fontcolor, value = legend)
                yl -= dy
        if self._value is None:
            self.value(self._initial_value, show = False) # Prevent recursion
        self.slide_y = self.slide_y0 - self._value * self.slot_len
        color = self.slidecolor if self.slidecolor is not None else self.fgcolor
        tft.fill_rectangle(self.slide_x0, self.slide_y, self.slide_x1, self.slide_y + self.slideheight, color)
        self.drawn = True

    def color(self, color):
        if color != self.fgcolor:
            self.fgcolor = color
            self.redraw = True
            self.show_if_current()

    def _touched(self, x, y): # Touched in bounding box. A drag will call repeatedly.
        self.value((self.y1 - y) / self.slot_len)


class HorizSlider(Touchable):
    def __init__(self, location, *, font=None, height=30, width=200, divisions=10, legends=None,
                 fgcolor=None, bgcolor=None, fontcolor=None, slidecolor=None, border=None, 
                 cb_end=dolittle, cbe_args=[], cb_move=dolittle, cbm_args=[], value=0.0):
        height &= 0xfe # ensure divisible by 2
        super().__init__(location, font, height, width, fgcolor, bgcolor, fontcolor, border, True, None, value)
        super()._set_callbacks(cb_move, cbm_args, cb_end, cbe_args)
        self.divisions = divisions
        self.legends = legends if font is not None else None
        self.slidecolor = slidecolor
        self.slidewidth = _SLIDE_DEPTH
        # Define the internal region of the control
        bw = self.border
        self.x0 = self.location[0] + bw  # Start
        self.y0 = self.location[1] + bw
        self.dy = height - 2 * bw  # Height
        self.x1 = self.location[0] + width - bw  # End
        self.y1 = self.location[1] + height - bw
        # Define slider
        self.slide_y0 = self.location[1] + bw + _TICK_VISIBLE  # Draw slider shorter than ticks
        self.slide_y1 = self.location[1] + height - bw - _TICK_VISIBLE
        # x coord of top left hand corner of slide when value == 0
        self.slide_x0 = self.x0 + bw - _SLIDE_DEPTH // 2 + 1
        # Slot coordinates
        centre = self.y0 + self.dy // 2
        self.slot_x0 = self.x0 + _SLIDE_DEPTH // 2
        self.slot_x1 = self.x1 - _SLIDE_DEPTH // 2 - 1
        self.slot_y0 = centre - _HALF_SLOT_WIDTH
        self.slot_y1 = centre + _HALF_SLOT_WIDTH
        # Length of travel of slider
        self.slot_len = self.slot_x1 - self.slot_x0
        # Prevent Label objects being added to display list when already there.
        self.drawn = False

    def show(self):
        tft = self.tft
        # Blank slot, ticks and slider
        tft.fill_rectangle(self.x0, self.y0, self.x1, self.y1, self.bgcolor)  # Blank and redraw slot, ticks and slider
        self.redraw = False
        x = self.slot_x0
        y = self.y0
        if self.divisions > 0:
            dx = self.slot_len / (self.divisions) # Tick marks
            ys = y + 1
            ye = y + self.dy - 1
            for tick in range(self.divisions + 1):
                xpos = int(x + dx * tick)
                tft.draw_line(xpos, ys, xpos, ye, self.fgcolor)
        # Blank and redraw slot
        tft.fill_rectangle(self.slot_x0, self.slot_y0, self.slot_x1, self.slot_y1, self.bgcolor)
        tft.draw_rectangle(self.slot_x0, self.slot_y0, self.slot_x1, self.slot_y1, self.fgcolor)

        # Legends: if redrawing, they are already on the Screen's display list
        if self.legends is not None and not self.drawn:
            if len(self.legends) <= 1:
                dx = 0
            else:
                dx = self.slot_len / (len(self.legends) -1)
            xl = x
            font = self.font
            bw = self.border
            for legend in self.legends:
                offset = get_stringsize(legend, font)[0] / 2
                loc = int(xl - offset), y - font.height() - bw - 1
                Label(loc, font = font, fontcolor = self.fontcolor, value = legend)
                xl += dx
        if self._value is None:
            self.value(self._initial_value, show = False) # prevent recursion

        self.slide_x = self.slide_x0 + self._value * self.slot_len
        color = self.slidecolor if self.slidecolor is not None else self.fgcolor
        tft.fill_rectangle(self.slide_x, self.slide_y0, self.slide_x + self.slidewidth, self.slide_y1, color)
        self.drawn = True

    def color(self, color):
        if color != self.fgcolor:
            self.fgcolor = color
            self.redraw = True
            self.show_if_current()

    def _touched(self, x, y): # Touched in bounding box. A drag will call repeatedly.
        self.value((x - self.x0) / self.slot_len)

# *********** CONTROL KNOB CLASS ***********

class Knob(Touchable):
    def __init__(self, location, *, height=100, arc=TWOPI, ticks=9, value=0.0,
                 fgcolor=None, bgcolor=None, color=None, border=None,
                 cb_end=dolittle, cbe_args=[], cb_move=dolittle, cbm_args=[]):
        Touchable.__init__(self, location, None, height, height, fgcolor, bgcolor, None, border, True,  None, value)
        border = self.border # Geometry: border width
        radius = height / 2 - border
        self.arc = min(max(arc, 0), TWOPI) # Usable angle of control
        self.radius = radius
        self.xorigin = location[0] + border + radius
        self.yorigin = location[1] + border + radius
        self.ticklen = 0.1 * radius
        self.pointerlen = radius - self.ticklen - 5
        self.ticks = max(ticks, 2) # start and end of travel
        super()._set_callbacks(cb_move, cbm_args, cb_end, cbe_args)
        self._old_value = None # data: invalidate
        self.color = color

    def show(self):
        tft = self.tft
        if self._value is None or self.redraw: # Initialising
            self.redraw = False
            arc = self.arc
            ticks = self.ticks
            radius = self.radius
            ticklen = self.ticklen
            for tick in range(ticks):
                theta = (tick / (ticks - 1)) * arc - arc / 2
                x_start = int(self.xorigin + radius * math.sin(theta))
                y_start = int(self.yorigin - radius * math.cos(theta))
                x_end = int(self.xorigin + (radius - ticklen) * math.sin(theta))
                y_end = int(self.yorigin - (radius - ticklen) * math.cos(theta))
                tft.draw_line(x_start, y_start, x_end, y_end, self.fgcolor)
            if self.color is not None:
                tft.fill_circle(self.xorigin, self.yorigin, radius - ticklen, self.color)
            tft.draw_circle(self.xorigin, self.yorigin, radius - ticklen, self.fgcolor)
            tft.draw_circle(self.xorigin, self.yorigin, radius - ticklen - 3, self.fgcolor)
            if self._value is None:
                self.value(self._initial_value, show = False)

        if self._old_value is not None: # An old pointer needs erasing
            color = self.bgcolor if self.color is None else self.color # Fill color
            self._drawpointer(self._old_value, color) # erase old
            self.tft # Reset Screen greyed-out status

        self._drawpointer(self._value, self.fgcolor) # draw new
        self._old_value = self._value # update old

    def _touched(self, x, y): # Touched in bounding box. A drag will call repeatedly.
        dy = self.yorigin - y
        dx = x - self.xorigin
        if (dx**2 + dy**2) / self.radius**2 < 0.5:
            return # vector too short
        alpha = math.atan2(dx, dy) # axes swapped: orientate relative to vertical
        arc = self.arc
        alpha = min(max(alpha, -arc / 2), arc / 2) + arc / 2
        self.value(alpha / arc)

    def _drawpointer(self, value, color):
        tft = self.tft
        arc = self.arc
        length = self.pointerlen
        angle = value * arc - arc / 2
        x_end = int(self.xorigin + length * math.sin(angle))
        y_end = int(self.yorigin - length * math.cos(angle))
        tft.draw_line(int(self.xorigin), int(self.yorigin), x_end, y_end, color)

# *********** LISTBOX CLASS ***********

class Listbox(Touchable):
    def __init__(self, location, *, font, elements, width=250, value=0, border=2,
                 fgcolor=None, bgcolor=None, fontcolor=None, select_color=LIGHTBLUE,
                 callback=dolittle, args=[]):
        self.entry_height = font.height() + 2 # Allow a pixel above and below text
        bw = border if border is not None else 0 # Replicate Touchable ctor's handling of self.border
        height = self.entry_height * len(elements) + 2 * bw
        super().__init__(location, font, height, width, fgcolor, bgcolor, fontcolor, border, False, value, None)
        super()._set_callbacks(callback, args)
        self.select_color = select_color
        tft = self.tft
        self.select_style = tft.text_style((self.fgcolor, select_color, self.font))
        fail = False
        try:
            self.elements = [s for s in elements if type(s) is str]
        except:
            fail = True
        else:
            fail = len(self.elements) == 0
        if fail:
            raise ValueError('elements must be a list or tuple of one or more strings')
        if value >= len(self.elements):
            value = 0
        self._value = value # No callback until user touches

    def show(self):
        tft = self.tft
        bw = self.border
        length = len(self.elements)
        x = self.location[0]
        y = self.location[1]
        xs = x + bw # start and end of text field
        xe = x + self.width - 2 * bw
        tft.fill_rectangle(xs, y + 1, xe, y - 1 + self.height - 2 * bw, self.bgcolor)
        for n in range(length):
            ye = y + n * self.entry_height
            if n == self._value:
                tft.fill_rectangle(xs, ye + 1, xe, ye + self.entry_height - 1, self.select_color)
                print_left(tft, xs, ye + 1, self.elements[n], self.select_style)
            else:
                print_left(tft, xs, ye + 1, self.elements[n], self.text_style)

    def textvalue(self, text=None): # if no arg return current text
        if text is None:
            return self.elements[self._value]
        else: # set value by text
            try:
                v = self.elements.index(text)
            except ValueError:
                v = None
            else:
                if v != self._value:
                    self.value(v)
            return v

    def _touched(self, x, y):
        dy = y - (self.location[1])
        self._initial_value = min(dy // self.entry_height, len(self.elements) -1)

    def _untouched(self):
        if self._initial_value is not None:
            self._value = -1  # Force update on every touch
            self.value(self._initial_value, show = True)
            self._initial_value = None

# *********** DROPDOWN LIST CLASS ***********

class _ListDialog(Aperture):
    def __init__(self, location, dropdown, width):
        border = 1 # between Aperture border and list
        dd = dropdown
        font = dd.font
        elements = dd.elements
        entry_height = font.height() + 2 # Allow a pixel above and below text
        height = entry_height * len(elements) + 2 * border
        lb_location = location[0] + border, location[1] + border
        lb_width = width - 2 * border
        super().__init__(location, height, width)
        tft = self.tft
        self.listbox = Listbox(lb_location, font = font, elements = elements, width = lb_width,
                               border = None, fgcolor = dd.fgcolor, bgcolor = dd.bgcolor,
                               fontcolor = tft.text_fgcolor, select_color = dd.select_color,
                               value = dd.value(), callback = self.callback)
        self.dropdown = dd

    def callback(self, obj_listbox):
        if obj_listbox._initial_value is not None: # a touch has occurred
            val = obj_listbox.textvalue()
            Screen.back()
            if self.dropdown is not None: # Part of a Dropdown
                self.dropdown.value(obj_listbox.value()) # Update it
 
class Dropdown(Touchable):
    def __init__(self, location, *, font, elements, width=250, value=0,
                 fgcolor=None, bgcolor=None, fontcolor=None, select_color=LIGHTBLUE,
                 callback=dolittle, args=[]):
        border = 2
        self.entry_height = font.height() + 2 # Allow a pixel above and below text
        height = self.entry_height + 2 * border
        super().__init__(location, font, height, width, fgcolor, bgcolor, fontcolor, border, False, value, None)
        super()._set_callbacks(callback, args)
        self.select_color = select_color
        self.elements = elements

    def show(self):
        tft = self.tft
        bw = self.border
        clip = self.width - (self.height + 2 * bw)
        x, y = self.location[0], self.location[1]
        self._draw(tft, x, y)
        if self._value is not None:
            print_left(tft, x + bw, y + bw + 1, self.elements[self._value], self.text_style)

    def textvalue(self, text=None): # if no arg return current text
        if text is None:
            return self.elements[self._value]
        else: # set value by text
            try:
                v = self.elements.index(text)
            except ValueError:
                v = None
            else:
                if v != self._value:
                    self.value(v)
            return v

    def _draw(self, tft, x, y):
        self.fill = True
        self.draw_border()
        tft.draw_vline(x + self.width - self.height, y, self.height, self.fgcolor)
        xcentre = x + self.width - self.height // 2 # Centre of triangle
        ycentre = y + self.height // 2
        halflength = (self.height - 8) // 2
        length = halflength * 2
        if length > 0:
            tft.draw_hline(xcentre - halflength, ycentre - halflength, length, self.fgcolor)
            tft.draw_line(xcentre - halflength, ycentre - halflength, xcentre, ycentre + halflength, self.fgcolor)
            tft.draw_line(xcentre + halflength, ycentre - halflength, xcentre, ycentre + halflength, self.fgcolor)

    def _touched(self, x, y):
        if len(self.elements) > 1:
            location = self.location[0], self.location[1] + self.height + 1
            args = (location, self, self.width - self.height)
            Screen.change(_ListDialog, args = args)

# *********** DIALOG BOX CLASS ***********
# Enables parameterised creation of button-based dialog boxes. See dialog.py

class DialogBox(Aperture):
    def __init__(self, font, *, elements, location=(20, 20), label=None,
                 bgcolor=DARKGREEN, buttonwidth=25, closebutton=True):
        height = 150
        spacing = 20
        buttonwidth = max(max([get_stringsize(x[0], font)[0] for x in elements]) + 4, buttonwidth)
        buttonheight = max(get_stringsize('x', font)[1], 25)
        nelements = len(elements)
        width = spacing + (buttonwidth + spacing) * nelements
        if label is not None:
            width = max(width, get_stringsize(label, font)[0] + 2 * spacing)
        super().__init__(location, height, width, bgcolor = bgcolor)
        x = self.location[0] + spacing # Coordinates relative to physical display
        gap = 0
        if nelements > 1:
            gap = ((width - 2 * spacing) - nelements * buttonwidth) // (nelements - 1)
        y = self.location[1] + self.height - buttonheight - 10
        if label is not None:
            Label((x, self.location[1] + 50), font = font, bgcolor = bgcolor, value = label)
        for text, color in elements:
            Button((x, y), height = buttonheight, width = buttonwidth, font = font, fontcolor = BLACK, fgcolor = color,
                text = text, shape = RECTANGLE,
                callback = self.back, args = (text,))
            x += buttonwidth + gap
        if closebutton:
            x, y = get_stringsize('X', font)
            size = max(x, y, 25)
            Button((self.location[0] + width - (size + 1), self.location[1] + 1), height = size, width = size, font = font,
                fgcolor = RED,  text = 'X', shape = RECTANGLE,
                callback = self.back, args = ('Close',))

    def back(self, button, text):
        Aperture.value(text)
        Screen.back()
