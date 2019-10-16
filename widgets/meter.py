# meter.py Extension to ugui providing a linear "meter" widget.

# Released under the MIT License (MIT). See LICENSE.
# Copyright (c) 2019 Peter Hinch

from micropython_ra8875.py.ugui import NoTouch
from micropython_ra8875.widgets.label import Label

# Null function
dolittle = lambda *_ : None

class Meter(NoTouch):
    def __init__(self, location, *, font=None, height=200, width=30,
                 fgcolor=None, bgcolor=None, barcolor=None, fontcolor=None,
                 divisions=10, legends=None, cb_move=dolittle, cbm_args=[], value=0):
        border = 5
        super().__init__(location, font, height, width, fgcolor, bgcolor, fontcolor, border, value, None)
        super()._set_callbacks(cb_move, cbm_args)
        self.x0 = self.location[0]
        self.x1 = self.location[0] + width
        self.y0 = self.location[1] + border
        self.y1 = self.location[1] + height - border
        self.divisions = divisions
        self.legends = legends
        self.ticklen = int(width / 3)
        self.barcolor = barcolor if barcolor is not None else self.fgcolor
        self.ptr_y = None # Invalidate old position
        # Prevent Label objects being added to display list when already there.
        self.drawn = False

    def show(self):
        tft = self.tft
        width = self.width
        font = self.font
        fh = self.font.height()
        fhdelta = fh / 2
        tl = self.ticklen
        x0 = self.x0
        x1 = self.x1
        y0 = self.y0
        y1 = self.y1
        height = y1 - y0
        if self.redraw:  # An overlaying screen has closed. Force redraw.
            self.redraw = False
            self.drawn = False
            self.ptr_y = None  # Invalidate previous bar so it's redrawn.
        if not self.drawn:
            self.drawn = True
            if self.divisions > 0:
                xs = x0 + 1
                xe = x1 - 1
                dy = height / (self.divisions) # Tick marks
                for tick in range(self.divisions + 1):
                    ypos = int(y0 + dy * tick)
                    tft.draw_line(xs, ypos, xe, ypos, self.fgcolor)

            if self.legends is not None and font is not None: # Legends
                if len(self.legends) <= 1:
                    dy = 0
                else:
                    dy = height / (len(self.legends) -1)
                yl = self.y1 # Start at bottom
                for legend in self.legends:
                    # constrain y to vertical extent of widget
                    loc = (x1 + 4, min(y1 - fh, max(y0, int(yl - fhdelta))))
                    Label(loc, font = font, fontcolor = self.fontcolor, value = legend)
                    yl -= dy

        ptr_y = round(y1 - self._value * (height - 1))  # y position of top of bar
        if self.ptr_y is None:
            tft.fill_rectangle(x0 + tl, y0 + 1, x1 - tl, y1 - 1, self.bgcolor)
            self.ptr_y = y1
        if ptr_y < self.ptr_y:  # Bar has moved up
            tft.fill_rectangle(x0 + tl, ptr_y, x1 - tl, self.ptr_y, self.barcolor)
        elif ptr_y > self.ptr_y:  # Moved down, blank the area
            tft.fill_rectangle(x0 + tl, ptr_y, x1 - tl, self.ptr_y, self.bgcolor)
        self.ptr_y = ptr_y

    def color(self, color):
        if self.barcolor != color:
            self.barcolor = color
            tl = self.ticklen
            x0 = self.x0
            x1 = self.x1
            y0 = self.y0
            y1 = self.y1
            # Blank bar and set .ptr_y to correspond to a value of 0
            self.tft.fill_rectangle(x0 + tl, y0 + 1, x1 - tl, y1 - 1, self.bgcolor)
            self.ptr_y = y1
