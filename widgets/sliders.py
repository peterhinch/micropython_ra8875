# sliders.py Extension to ugui providing linear "potentiometer" widgets.

# Released under the MIT License (MIT). See LICENSE.
# Copyright (c) 2019 Peter Hinch

from micropython_ra8875.ugui import Touchable
from micropython_ra8875.widgets.label import Label

# Null function
dolittle = lambda *_ : None

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
                offset = tft.get_stringsize(legend, font)[0] / 2
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
