# ugui.py Micropython GUI library

# Released under the MIT License (MIT). See LICENSE.
# Copyright (c) 2019 Peter Hinch

import uasyncio as asyncio
import gc

from micropython_ra8875.support.aswitch import Delay_ms
from micropython_ra8875.support.asyn import Event
from micropython_ra8875.support.constants import *

gc.collect()

# Null function
dolittle = lambda *_ : None


class Screen:
    current_screen = None
    tft = None
    objtouch = None
    is_shutdown = Event()

    @classmethod
    def setup(cls, tft, objtouch=None):
        cls.objtouch = objtouch if objtouch is not None else tft
        cls.tft = tft

    @classmethod
    def _get_tft(cls, greyed_out=False):
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
        if Screen.current_screen is None: # Initialising class and task
            loop = asyncio.get_event_loop()
            loop.create_task(Screen.objtouch.touchtest()) # One task only
            loop.create_task(self._garbage_collect())
        Screen.current_screen = self
        self.parent = None

    def _do_open(self, old_screen): # Aperture overrides
        show_all = True
        tft = Screen._get_tft()
# If opening a Screen from an Aperture just blank and redraw covered area
        if old_screen.modal:
            show_all = False
            x0, y0, x1, y1 = old_screen._list_dims()
            tft.fill_rectangle(x0, y0, x1, y1, SYS_BGCOLOR) # Blank to screen BG
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
        tft = Screen._get_tft()
        self.fgcolor = fgcolor if fgcolor is not None else SYS_FGCOLOR
        self.bgcolor = bgcolor if bgcolor is not None else SYS_BGCOLOR

    def locn(self, x, y):
        return (self.location[0] + x, self.location[1] + y)

    def _do_open(self, old_screen):
        tft = Screen._get_tft()
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
        tft = Screen._get_tft(False) # Not greyed out
        if font is None:
            self.font = DEFAULT_FONT
        else:
            self.font = font

        if fgcolor is None:
            self.fgcolor = SYS_FGCOLOR
            if bgcolor is None:
                self.bgcolor = SYS_BGCOLOR
            else:
                self.bgcolor = bgcolor
            self.fontbg = self.bgcolor
        else:
            self.fgcolor = fgcolor
            if bgcolor is None:
                self.bgcolor = SYS_BGCOLOR  # black surround to circle button etc
                # Fonts are drawn on bg of foreground color e.g. for buttons
                self.fontbg = fgcolor
            else:
                self.bgcolor = bgcolor
                self.fontbg = bgcolor

        self.text_style = tft.text_style((self.fontcolor, self.fontbg, self.font))
        self.border = 0 if border is None else int(max(border, 0)) # width
        self.bdcolor = self.fgcolor  # Border is always drawn in original fgcolor
        self.callback = dolittle # Value change callback
        self.args = []
        self.cb_end = dolittle # Touch release callbacks
        self.cbe_args = []

    @property
    def tft(self):
        return Screen._get_tft(self._greyed_out)

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
            if self.border > 0:  # Draw a bounding box in original fgcolor
                tft.draw_rectangle(x, y, x + self.width, y + self.height, self.bdcolor)
        return self.border # border width in pixels

    def overlaps(self, xa, ya, xb, yb): # Args must be sorted: xb > xa and yb > ya
        x0 = self.location[0]
        y0 = self.location[1]
        x1 = x0 + self.width
        y1 = y0 + self.height
        if (ya <= y1 and yb >= y0) and (xa <= x1 and xb >= x0):
            return True
        return False

    def _set_callbacks(self, cb, args):
        self.callback = cb
        self.args = args

# Base class for touch-enabled classes.
class Touchable(NoTouch):
    def __init__(self, location, font, height, width, fgcolor, bgcolor, fontcolor, border, can_drag, value, initial_value):
        super().__init__(location, font, height, width, fgcolor, bgcolor, fontcolor, border, value, initial_value)
        self.can_drag = can_drag
        self.busy = False
        self.was_touched = False

    def _set_callbacks(self, cb, args, cb_end=None, cbe_args=None):
        super()._set_callbacks(cb, args)
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
