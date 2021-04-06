# scale_ctrl_test.py Test/demo of ScaleCtrl widget for Pybboard RA8875 GUI

# Released under the MIT License (MIT). See LICENSE.
# Copyright (c) 2021 Peter Hinch

# Usage:
# import micropython_ra8875.demos.scale_ctrl_test

import uasyncio as asyncio
from micropython_ra8875.driver.constants import *
from micropython_ra8875.py.colors import *
from micropython_ra8875.py.ugui import Screen
from micropython_ra8875.fonts import font10, font14
from micropython_ra8875.widgets.buttons import Button
from micropython_ra8875.widgets.label import Label
from micropython_ra8875.widgets.scale_ctrl import ScaleCtrl
from micropython_ra8875.driver.tft_local import setup


def quitbutton(x, y):
    def quit(button):
        Screen.shutdown()
    Button((x, y), height = 30, font = font14, callback = quit, fgcolor = RED,
           text = 'Quit', shape = RECTANGLE, width = 80)


class BaseScreen(Screen):
    def __init__(self):
        super().__init__()
        # Scale with custom variable and legends.
        Label((0, 0), font = font14, value = 'FM radio scale 88-108MHz.')
        lbl_result0 = Label((0, 240), font = font14, fontcolor = WHITE, width = 100,
                            border = 2, fgcolor = RED, bgcolor = DARKGREEN)
        lbl_result1 = Label((200, 240), font = font14, fontcolor = WHITE, width = 70,
                            border = 2, fgcolor = RED, bgcolor = DARKGREEN)
        def legendcb(f):
            return '{:2.0f}'.format(88 + ((f + 1) / 2) * (108 - 88))
        self.scale0 = ScaleCtrl((0, 30), font10, legendcb = legendcb, width = 350, height = 60,
                                bgcolor = BLACK, fgcolor = GREEN, pointercolor = RED, fontcolor = YELLOW,
                                cb_move=self.scale_move, cbm_args=(lbl_result0, 0))
        # Scale with varying color.
        Label((0, 130), font = font14, value = 'Default scale -1 to +1, varying colors.')
        def tickcb(f, c):
            if f > 0.8:
                return RED
            if f < -0.8:
                return BLUE
            return c
        self.scale1 = ScaleCtrl((0, 160), font10, tickcb = tickcb, width = 350, height = 60,
                                bgcolor = BLACK, fgcolor = GREEN, pointercolor = RED, fontcolor = YELLOW,
                                cb_move=self.scale_move, cbm_args=(lbl_result1, 1))
        x = 390
        y = 242
        quitbutton(x, y)
        y -= 50
        Button((x, y), height = 30, font = font14, callback = self.en, fgcolor = GREEN,
                fontcolor=BLACK, text = 'Enable', shape = RECTANGLE, width = 80)
        y -= 50
        Button((x, y), height = 30, font = font14, callback = self.dis, fgcolor = YELLOW,
                fontcolor=BLACK, text = 'Disable', shape = RECTANGLE, width = 80)

    def scale_move(self, scale, label, n):
        sv = scale.value()
        if n:
            label.value('{:4.3f}'.format(sv))
        else:
            sv = (sv + 1) / 2  # 0 <= sv <= 1
            label.value('{:6.2f}'.format(sv*(108 - 88) + 88))

    def en(self, _):
        self.scale0.greyed_out(False)
        self.scale1.greyed_out(False)

    def dis(self, _):
        self.scale0.greyed_out(True)
        self.scale1.greyed_out(True)
        
        
def test():
    setup()
    Screen.change(BaseScreen)

test()
