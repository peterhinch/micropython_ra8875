# ptg.py Test/demo of graph plotting extension for RA8875 GUI
# Tests time sequence and generators as populate functions.

# Released under the MIT License (MIT). See LICENSE.
# Copyright (c) 2019-2020 Peter Hinch

import uasyncio as asyncio
from math import sin, cos, pi
from cmath import rect

from micropython_ra8875.py.ugui import Screen
from micropython_ra8875.py.colors import *
from micropython_ra8875.py.plot import PolarGraph, PolarCurve, CartesianGraph, Curve, TSequence

from micropython_ra8875.widgets.buttons import Button
from micropython_ra8875.widgets.label import Label
from micropython_ra8875.fonts import font10
from micropython_ra8875.driver.tft_local import setup

# STANDARD BUTTONS

def quitbutton():
    def quit(button):
        Screen.shutdown()
    return Button((390, 242), font = font10, callback = quit, height = 25,
                  width = 80, fgcolor = RED, text = 'Quit')

def fwdbutton(x, y, screen, text='Next'):
    def fwd(button, screen):
        Screen.change(screen)
    return Button((x, y), font = font10, fontcolor = BLACK, callback = fwd,
                  height = 25, width = 70, args = [screen], fgcolor = CYAN, text = text)

def backbutton():
    def back(button):
        Screen.back()
    return Button((454, 0), font = font10, fontcolor = BLACK, callback = back,
           fgcolor = RED,  text = 'X', height = 25, width = 25)

def ovlbutton():
    def fwd(button):
        Screen.change(BackScreen)
    return Button((400, 100), font = font10, fontcolor = BLACK, callback = fwd,
                  fgcolor = CYAN, text = 'Fwd', height = 25, width = 70)

def clearbutton(graph):
    def clear(button):
        graph.clear()
    return Button((400, 150), font = font10, fontcolor = BLACK, callback = clear,
           fgcolor = GREEN,  text = 'Clear', height = 25, width = 70)

def refreshbutton(curvelist):
    def refresh(button):
        for curve in curvelist:
            curve.show()
    return Button((400, 200), font = font10, fontcolor = BLACK, callback = refresh,
           fgcolor = GREEN,  text = 'Refresh', height = 25, width = 70)

# SCREEN CREATION

class BackScreen(Screen):
    def __init__(self):
        super().__init__()
        Label((0, 0), font = font10, value = 'Refresh test')
        backbutton()

class BaseScreen(Screen):
    def __init__(self):
        super().__init__()
        Label((0, 0), font = font10, value = 'Plot module demonstrator.')
        y = 30
        dy = 42
        fwdbutton(0, y, Tseq, 'TSeq')
        Label((75, y + 5), font = font10, value = 'Time sequence demo.')
        y += dy
        fwdbutton(0, y, PolarScreen, 'Polar')
        Label((75, y + 5), font = font10, value = 'A polar plot.')
        y += dy
        fwdbutton(0, y, XYScreen, 'XY')
        Label((75, y + 5), font = font10, value = 'Cartesian plot.')
        y += dy
        fwdbutton(0, y, RealtimeScreen, 'RT')
        Label((75, y + 5), font = font10, value = 'Realtime demo.')
        y += dy
        fwdbutton(0, y, PolarORScreen, 'Over')
        Label((75, y + 5), font = font10, value = 'Two demos of clipping.')
        y += dy
        fwdbutton(0, y, DiscontScreen, 'Lines')
        quitbutton()

class PolarScreen(Screen):
    def __init__(self):
        super().__init__()
        backbutton()
        ovlbutton()
        g = PolarGraph((0, 0), border = 4)
        clearbutton(g)
        curve = PolarCurve(g, self.populate)
        refreshbutton((curve,))

    def populate(self, curve):  # Test generator function as bound method
        def f(theta):
            return rect(sin(3 * theta), theta) # complex
        nmax = 150
        for n in range(nmax + 1):
            theta = 2 * pi * n / nmax
            yield f(theta)


# Test clipping
class PolarORScreen(Screen):
    def __init__(self):
        super().__init__()
        def populate(curve, rot):
            def f(theta):
                return rect(1.15*sin(5 * theta), theta)*rot # complex
            nmax = 150
            for n in range(nmax + 1):
                theta = 2 * pi * n / nmax
                yield f(theta)

        backbutton()
        ovlbutton()
        g = PolarGraph((5, 5), border = 4)
        clearbutton(g)
        curve = PolarCurve(g, populate, (1,))
        curve1 = PolarCurve(g, populate, (rect(1, pi/5),), color=RED)
        refreshbutton((curve, curve1))


class XYScreen(Screen):
    def __init__(self):
        super().__init__()
        def populate_1(curve, func):
            x = -1
            while x < 1.01:
                y = func(x)
                yield x, y
                x += 0.1

        def populate_2(curve):
            x = -1
            while x < 1.01:
                y = x**2
                yield x, y
                x += 0.1

        backbutton()
        ovlbutton()
        g = CartesianGraph((0, 0), yorigin = 2) # Asymmetric y axis
        clearbutton(g)
        curve1 = Curve(g, populate_1, (lambda x : x**3 + x**2 -x,)) # args demo
        curve2 = Curve(g, populate_2, color = RED)
        refreshbutton((curve1, curve2))


# Test of discontinuous curves and those which provoke clipping
class DiscontScreen(Screen):
    def __init__(self):
        super().__init__()
        def populate_3(curve):
            for x, y in ((-2, -0.2), (-2, 0.2), (-0.2, -2), (0.2, -2), (2, 0.2), (2, -0.2), (0.2, 2), (-0.2, 2)):
                yield x, y
                yield 0, 0
                yield None, None

        def populate_1(curve, mag):
            theta = 0
            delta = pi/32
            while theta <= 2 * pi:
                yield mag*sin(theta), mag*cos(theta)
                theta += delta

        backbutton()
        ovlbutton()
        g = CartesianGraph((5, 5))
        clearbutton(g)
        curve1 = Curve(g, populate_1, (1.1,))
        curve2 = Curve(g, populate_1, (1.05,), color=RED)
        curve3 = Curve(g, populate_3, color=BLUE)
        refreshbutton((curve1, curve2, curve3))


# Simulate slow real time data acquisition and plotting
class RealtimeScreen(Screen):
    def __init__(self):
        super().__init__()
        self.aqu_task = None
        backbutton()
        ovlbutton()
        cartesian_graph = CartesianGraph((0, 0))
        self.clearbutton(cartesian_graph)
        curve = Curve(cartesian_graph, self.go)
        refreshbutton((curve,))

    def go(self, curve):
        self.aqu_task = asyncio.create_task(self.acquire(curve))
        self.reg_task(self.aqu_task, True)

    async def acquire(self, curve):
        x = -1
        await asyncio.sleep(0)
        while x < 1.01:
            y = max(1 - x * x, 0) # possible precison issue
            curve.point(x, y ** 0.5)
            x += 0.05
            await asyncio.sleep_ms(100)
        while x > -1.01:
            y = max(1 - x * x, 0)
            curve.point(x, -(y ** 0.5))
            x -= 0.05
            await asyncio.sleep_ms(100)

    def clearbutton(self, graph):
        def clear(button):
            self.aqu_task.cancel()
            graph.clear()
        return Button((400, 150), font = font10, fontcolor = BLACK, callback = clear,
            fgcolor = GREEN,  text = 'Clear', height = 25, width = 70)

class Tseq(Screen):
    def __init__(self):
        super().__init__()
        g = CartesianGraph((0, 0), height = 250, width = 250, xorigin = 10)
        tsy = TSequence(g, YELLOW, 50)
        tsr = TSequence(g, RED, 50)
        self.reg_task(self.acquire(g, tsy, tsr), True)  # Cancel on screen change
        backbutton()

    async def acquire(self, graph, tsy, tsr):
        t = 0.0
        while True:
            graph.clear()
            tsy.add(0.9 * sin(t))
            tsr.add(0.4 * cos(t))
            await asyncio.sleep_ms(500)
            t += 0.1

def pt():
    print('Testing plot module...')
    setup()
    Screen.change(BaseScreen)

pt()
