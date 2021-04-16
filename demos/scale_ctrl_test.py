# scale_ctrl_test.py Test/demo of ScaleCtrl widget for Pybboard RA8875 GUI

# Released under the MIT License (MIT). See LICENSE.
# Copyright (c) 2021 Peter Hinch

# Usage:
# import micropython_ra8875.demos.scale_ctrl_test

import uasyncio as asyncio
from micropython_ra8875.py.colors import *
from micropython_ra8875.py.ugui import Screen
from micropython_ra8875.fonts import font10, font14
from micropython_ra8875.widgets.buttons import Button
from micropython_ra8875.widgets.label import Label
from micropython_ra8875.widgets.scale_ctrl import ScaleCtrl
from micropython_ra8875.widgets.scale_log import ScaleLog
from micropython_ra8875.driver.tft_local import setup  # Local wiring

# Arguments common to sets of controls
buttons = {'font': font14,
            'width': 80,
            'height': 30,
            'shape': RECTANGLE,
            'fontcolor': BLACK, }

labels = {'font': font14,
            'width': 140,
            'border': 2,
            'fontcolor': WHITE,
            'bgcolor': DARKGREEN,
            'fgcolor': RED, }

scales = {'font': font10,
            'width': 350,
            'height': 60,
            'pointercolor': RED,
            'fontcolor': YELLOW,
            'fgcolor': GREEN,
            'bgcolor': BLACK, }

# STANDARD BUTTONS

def quitbutton(x, y):
    def quit(button):
        Screen.shutdown()
    Button((x, y), callback = quit, fgcolor = RED, text = 'Quit', **buttons)

def fwdbutton(x, y, cls_screen, text='Next'):
    def fwd(button):
        Screen.change(cls_screen)
    Button((x, y), callback = fwd, fgcolor = GREEN, text = text, **buttons)

def backbutton(x, y):
    def back(button):
        Screen.back()
    Button((x, y), callback = back, fgcolor = CYAN, text = 'Back', **buttons)

class linearScreen(Screen):
    def __init__(self):
        super().__init__()

        # Scale 0 with custom variable and legends.
        Label((0, 0), font = font14, value = 'FM radio scale 88-108MHz.')
        lbl_result0 = Label((0, 240), **labels)
        # Define callbacks for scale 0
        def legendcb(f):
            return '{:2.0f}'.format(88 + ((f + 1) / 2) * (108 - 88))

        def scale_move0(scale):
            sv = scale.value()
            sv = (sv + 1) / 2  # 0 <= sv <= 1
            lbl_result0.value('{:6.2f}'.format(sv*(108 - 88) + 88))

        self.scale0 = ScaleCtrl((0, 30), legendcb = legendcb,
                                cb_move=scale_move0, **scales)
        # Scale 1 with varying color.
        Label((0, 130), font = font14, value = 'Default scale -1 to +1, varying colors.')
        lbl_result1 = Label((200, 240), **labels)
        # Define callbacks for scale 1
        def tickcb(f, c):
            if f > 0.8:
                return RED
            if f < -0.8:
                return BLUE
            return c

        def scale_move1(scale):
            sv = scale.value()
            lbl_result1.value('{:4.3f}'.format(sv))

        self.scale1 = ScaleCtrl((0, 160), tickcb = tickcb,
                                cb_move=scale_move1, **scales)
        # Define buttons
        x = 390
        y = 242
        backbutton(x, y)
        #Button((x, y), fgcolor = RED, text = 'Quit',
               #callback = lambda _: Screen.shutdown(), **buttons)
        y -= 50
        Button((x, y), fgcolor = GREEN, text = 'Enable',
               callback = self.en, **buttons)
        y -= 50
        Button((x, y), fgcolor = YELLOW, text = 'Disable',
               callback = self.dis, **buttons)
        y -= 50
        Button((x, y), fgcolor = BLUE, text = 'Zero',
               callback = lambda _: self.scale1.value(0), **buttons)


    def en(self, _):  # Discard button arg
        self.scale0.greyed_out(False)
        self.scale1.greyed_out(False)

    def dis(self, _):
        self.scale0.greyed_out(True)
        self.scale1.greyed_out(True)

class LogScreen(Screen):
    def __init__(self):
        super().__init__()

        # Scale 0
        Label((0, 0), font = font14, value = 'Default scale 5 decades.')
        lbl_result0 = Label((0, 240), **labels)
        # Define callbacks for scale 0
        def legendcb(f):
            if f < 999:
                return '{:<1.0f}'.format(f)
            return '{:<1.0f}K'.format(f/1000)

        def scale_move0(scale):
            sv = scale.value()
            lbl_result0.value('{:6.2f}'.format(sv))
            self.scale1.value(scale.value())  # Cause lower scale to mimic this one

        self.scale0 = ScaleLog((0, 30), legendcb = legendcb, value=15,
                                cb_move=scale_move0, **scales)
        # Scale 1 with varying color.
        Label((0, 130), font = font14, value = 'Varying colors, follows top scale.')
        lbl_result1 = Label((200, 240), **labels)
        # Define callbacks for scale 1
        def tickcb(f, c):
            if f > 30000:
                return RED
            if f < 10:
                return BLUE
            return c

        def scale_move1(scale):
            sv = scale.value()
            lbl_result1.value('{:6.2f}'.format(sv))

        self.scale1 = ScaleLog((0, 160), tickcb = tickcb,
                                cb_move=scale_move1, **scales)
        # Define buttons
        x = 390
        y = 242
        backbutton(x, y)
        y -= 50
        Button((x, y), fgcolor = GREEN, text = 'Enable',
               callback = self.en, **buttons)
        y -= 50
        Button((x, y), fgcolor = YELLOW, text = 'Disable',
               callback = self.dis, **buttons)
        y -= 50
        Button((x, y), fgcolor = BLUE, text = 'Reset',
               callback = lambda _: self.scale1.value(1), **buttons)


    def en(self, _):  # Discard button arg
        self.scale0.greyed_out(False)
        self.scale1.greyed_out(False)

    def dis(self, _):
        self.scale0.greyed_out(True)
        self.scale1.greyed_out(True)

class ChoiceScreen(Screen):
    def __init__(self):
        super().__init__()
        Label((0, 0), font = font14, value = 'Demo of linear and log scale controls.')
        fwdbutton(10, 50, linearScreen, 'Linear')
        fwdbutton(10, 100, LogScreen, 'Log')
        quitbutton(200, 242)
    
def test():
    setup()
    Screen.change(ChoiceScreen)

test()
