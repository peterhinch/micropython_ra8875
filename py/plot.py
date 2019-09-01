# lplot.py Graph plotting extension for Pybboard TFT GUI

# Released under the MIT License (MIT). See LICENSE.
# Copyright (c) 2019 Peter Hinch

from math import pi
from cmath import rect
from micropython import const
from array import array

from micropython_ra8875.py.ugui import NoTouch, Screen
from micropython_ra8875.py.colors import *

type_gen = type((lambda: (yield))())  # type of a generator

# Line clipping outcode bits
_TOP = const(1)
_BOTTOM = const(2)
_LEFT = const(4)
_RIGHT = const(8)
# Bounding box for line clipping
_XMAX = const(1)
_XMIN = const(-1)
_YMAX = const(1)
_YMIN = const(-1)


class Curve():
    @staticmethod
    def _outcode(x, y):
        oc = _TOP if y > 1 else 0
        oc |= _BOTTOM if y < -1 else 0
        oc |= _RIGHT if x > 1 else 0
        oc |= _LEFT if x < -1 else 0
        return oc

    def __init__(self, graph, populate=None, args=[], origin=(0, 0),
                 excursion=(1, 1), color=YELLOW):
        if not isinstance(self, PolarCurve):  # Check not done in subclass
            if not isinstance(graph, CartesianGraph):
                raise ValueError('Curve must use a CartesianGraph instance.')
        self.graph = graph
        self.populate = populate
        self.args = args
        self.origin = origin
        self.excursion = excursion
        self.color = color
        self.graph.addcurve(self)
        self.lastpoint = None
        self.newpoint = None

    def point(self, x=None, y=None):
        if x is None or y is None:
            self.newpoint = None
            self.lastpoint = None
            return

        self.newpoint = self._scale(x, y)  # In-range points scaled to +-1 bounding box
        if self.lastpoint is None:  # Nothing to plot. Save for next line.
            self.lastpoint = self.newpoint
            return

        res = self._clip(*(self.lastpoint + self.newpoint))  # Clip to +-1 box
        if res is not None:  # Ignore lines which don't intersect
            self.graph.line(res[0:2], res[2:5], self.color)
        self.lastpoint = self.newpoint  # Scaled but not clipped

    # Cohen–Sutherland line clipping algorithm
    # If self.newpoint and self.lastpoint are valid clip them so that both lie
    # in +-1 range. If both are outside the box return None.
    def _clip(self, x0, y0, x1, y1):
        oc1 = self._outcode(x0, y0)
        oc2 = self._outcode(x1, y1)
        while True:
            if not oc1 | oc2:  # OK to plot
                return x0, y0, x1, y1
            if oc1 & oc2:  # Nothing to do
                return
            oc = oc1 if oc1 else oc2
            if oc & _TOP:
                x = x0 + (_YMAX - y0)*(x1 - x0)/(y1 - y0)
                y = _YMAX
            elif oc & _BOTTOM:
                x = x0 + (_YMIN - y0)*(x1 - x0)/(y1 - y0)
                y = _YMIN
            elif oc & _RIGHT:
                y = y0 + (_XMAX - x0)*(y1 - y0)/(x1 - x0)
                x = _XMAX
            elif oc & _LEFT:
                y = y0 + (_XMIN - x0)*(y1 - y0)/(x1 - x0)
                x = _XMIN
            if oc is oc1:
                x0, y0 = x, y
                oc1 = self._outcode(x0, y0)
            else:
                x1, y1 = x, y
                oc2 = self._outcode(x1, y1)

    def show(self):
        self.graph.addcurve(self) # May have been removed by clear()
        self.lastpoint = None
        if self.populate is not None:
            pop = self.populate(self, *self.args)
            if isinstance(pop, type_gen):
                # populate was a generator function, pop is a generator.
                for x, y in pop:
                    self.point(x, y)

    def _scale(self, x, y):  # Scale to +-1.0
        x0, y0 = self.origin
        xr, yr = self.excursion
        xs = (x - x0) / xr
        ys = (y - y0) / yr
        return xs, ys

class PolarCurve(Curve): # Points are complex
    def __init__(self, graph, populate=None, args=[], color=YELLOW):
        if not isinstance(graph, PolarGraph):
            raise ValueError('PolarCurve must use a PolarGraph instance.')
        super().__init__(graph, populate, args, color=color)

    def point(self, z=None):
        if z is None:
            self.newpoint = None
            self.lastpoint = None
            return

        # In-range points scaled to +-1 bounding box
        self.newpoint = self._scale(z.real, z.imag)
        if self.lastpoint is None:  # Nothing to plot. Save for next line.
            self.lastpoint = self.newpoint
            return

        res = self._clip(*(self.lastpoint + self.newpoint))  # Clip to +-1 box
        if res is not None:  # At least part of line was in box
            start = res[0] + 1j*res[1]
            end = res[2] + 1j*res[3]
            self.graph.cline(start, end, self.color)
        self.lastpoint = self.newpoint  # Scaled but not clipped

    def show(self):
        self.graph.addcurve(self) # May have been removed by clear()
        self.lastpoint = None
        if self.populate is not None:
            pop = self.populate(self, *self.args)
            if isinstance(pop, type_gen):
                # populate was a generator function, pop is a generator.
                for z in pop:
                    self.point(z)


class TSequence(Curve):
    def __init__(self, graph, color, size, yorigin=0, yexc=1):
        super().__init__(graph, populate=None, args=[], origin=(0, yorigin),
                         excursion=(1, yexc), color=color)
        self.data = array('f', (0 for _ in range(size)))
        self.cur = 0
        self.size = size
        self.count = 0

    def add(self, v):
        p = self.cur
        size = self.size
        self.data[self.cur] = v
        self.cur += 1
        self.cur %= size
        if self.count < size:
            self.count += 1
        x = 0
        dx = 1/size
        for _ in range(self.count):
            self.point(x, self.data[p])
            x -= dx
            p -= 1
            p %= size
        self.point()


class Graph():
    def __init__(self, location, height, width, gridcolor):
        border = self.border # border width
        self.x0 = self.location[0] + border
        self.x1 = self.location[0] + self.width - border
        self.y0 = self.location[1] + border
        self.y1 = self.location[1] + self.height - border
        self.gridcolor = gridcolor
        self.curves = set()

    def addcurve(self, curve):
        self.curves.add(curve)

    def clear(self):
        tft = Screen.tft
        self.curves = set()
        tft.fill_rectangle(self.x0, self.y0, self.x1, self.y1, self.bgcolor)
        self.show()

class CartesianGraph(NoTouch, Graph):
    def __init__(self, location, *, height=250, width=250, fgcolor=WHITE,
                 bgcolor=None, border=None, gridcolor=LIGHTGREEN, xdivs=10,
                 ydivs=10, xorigin=5, yorigin=5):
        NoTouch.__init__(self, location, None, height, width, fgcolor, bgcolor,
                         None, border, None, None)
        Graph.__init__(self, location, height, width, gridcolor)
        self.xdivs = xdivs
        self.ydivs = ydivs
        self.xorigin = xorigin
        self.yorigin = yorigin
        height -= 2 * self.border
        width -= 2 * self.border
        # Max distance from origin in pixels
        self.x_axis_len = max(xorigin, xdivs - xorigin) * width / xdivs
        self.y_axis_len = max(yorigin, ydivs - yorigin) * height / ydivs
        self.xp_origin = self.x0 + xorigin * width / xdivs # Origin in pixels
        self.yp_origin = self.y0 + (ydivs - yorigin) * height / ydivs

    def show(self):
        tft = self.tft
        x0 = self.x0
        x1 = self.x1
        y0 = self.y0
        y1 = self.y1
        #tft.fill_rectangle(x0, y0, x1, y1, self.bgcolor)
        if self.ydivs > 0:
            height = y1 - y0
            dy = height / (self.ydivs) # Y grid line
            for line in range(self.ydivs + 1):
                color = self.fgcolor if line == self.yorigin else self.gridcolor
                ypos = int(y1 - dy * line)
                tft.draw_hline(x0, ypos, x1 - x0, color)
        if self.xdivs > 0:
            width = x1 - x0
            dx = width / (self.xdivs) # X grid line
            for line in range(self.xdivs + 1):
                color = self.fgcolor if line == self.xorigin else self.gridcolor
                xpos = int(x0 + dx * line)
                tft.draw_vline(xpos, y0, y1 - y0, color)
        for curve in self.curves:
            curve.show()

    # start and end relative to origin and scaled -1 .. 0 .. +1
    def line(self, start, end, color):
        xs = round(self.xp_origin + start[0] * self.x_axis_len)
        ys = round(self.yp_origin - start[1] * self.y_axis_len)
        xe = round(self.xp_origin + end[0] * self.x_axis_len)
        ye = round(self.yp_origin - end[1] * self.y_axis_len)
        self.tft.draw_line(xs, ys, xe, ye, color)

class PolarGraph(NoTouch, Graph):
    def __init__(self, location, *, height=250, fgcolor=WHITE, bgcolor=None,
                 border=None, gridcolor=LIGHTGREEN, adivs=3, rdivs=4):
        NoTouch.__init__(self, location, None, height, height, fgcolor,
                         bgcolor, None, border, None, None)
        Graph.__init__(self, location, height, height, gridcolor)
        self.adivs = 2 * adivs # No. of divisions of Pi radians
        self.rdivs = rdivs # No. of divisions of radius
        height -= 2 * self.border
        self.radius = int(height / 2) # Unit: pixels
        self.xp_origin = self.x0 + self.radius # Origin in pixels
        self.yp_origin = self.y0 + self.radius

    def show(self):
        tft = self.tft
        x0 = self.x0
        y0 = self.y0
        #tft.fill_rectangle(x0, y0, self.x1, self.y1, self.bgcolor)
        radius = self.radius
        diam = 2 * radius
        if self.rdivs > 0:
            for r in range(1, self.rdivs + 1):
                tft.draw_circle(self.xp_origin, self.yp_origin,
                                int(radius * r / self.rdivs), self.gridcolor)
        if self.adivs > 0:
            v = complex(1)
            m = rect(1, pi / self.adivs)
            for _ in range(self.adivs):
                self.cline(-v, v, self.gridcolor)
                v *= m
        tft.draw_vline(x0 + radius, y0, diam, self.fgcolor)
        tft.draw_hline(x0, y0 + radius, diam, self.fgcolor)
        for curve in self.curves:
            curve.show()

    # start and end are complex, 0 <= magnitude <= 1
    def cline(self, start, end, color):
        xs = round(self.xp_origin + start.real * self.radius)
        ys = round(self.yp_origin - start.imag * self.radius)
        xe = round(self.xp_origin + end.real * self.radius)
        ye = round(self.yp_origin - end.imag * self.radius)
        self.tft.draw_line(xs, ys, xe, ye, color)
