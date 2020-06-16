# vst.py Demo/test program for vertical slider class for Pyboard RA8875 GUI

# Released under the MIT License (MIT). See LICENSE.
# Copyright (c) 2019-2020 Peter Hinch

# Updated for uasyncio V3

import uasyncio as asyncio
from math import pi

from micropython_ra8875.py.ugui import Screen
from micropython_ra8875.py.colors import *

from micropython_ra8875.widgets.buttons import Button, ButtonList
from micropython_ra8875.widgets.label import Label
from micropython_ra8875.widgets.dial import Dial
from micropython_ra8875.widgets.sliders import Slider

from micropython_ra8875.fonts import font10, font14
from micropython_ra8875.driver.tft_local import setup

def to_string(val):
    return '{:3.1f}Ω'.format(val * 10)

def quit(button):
    Screen.shutdown()

class VerticalSliderScreen(Screen):
    def __init__(self):
        super().__init__()
# Common args for the labels
        labels = { 'width' : 60,
                'fontcolor' : WHITE,
                'border' : 2,
                'fgcolor' : RED,
                'bgcolor' : (0, 40, 0),
                }
# Common args for all three sliders
        table = {'fontcolor' : WHITE,
                'legends' : ('0', '5', '10'),
                'cb_end' : self.callback,
                }
        btnquit = Button((390, 240), font = font14, callback = quit, fgcolor = RED,
            text = 'Quit', shape = RECTANGLE, width = 80, height = 30)
        self.dial1 = Dial((350, 10), fgcolor = YELLOW, border = 2, pointers = (0.9, 0.7))
        self.dial2 = Dial((350, 120), fgcolor = YELLOW, border = 2,  pointers = (0.9, 0.7)) 
        self.lstlbl = []
        for n in range(3):
            self.lstlbl.append(Label((80 * n, 240), font = font10, **labels))
        y = 5
        self.slave1 = Slider((80, y), font = font10,
            fgcolor = GREEN, cbe_args = ('Slave1',), cb_move = self.slave_moved, cbm_args = (1,), **table)
        self.slave2 = Slider((160, y), font = font10,
            fgcolor = GREEN, cbe_args = ('Slave2',), cb_move = self.slave_moved, cbm_args = (2,), **table)
        master = Slider((0, y), font = font10,
            fgcolor = YELLOW, cbe_args = ('Master',), cb_move = self.master_moved, value=0.5, border = 2, **table)
        self.reg_task(self.task1())
        self.reg_task(self.task2())
    # On/Off toggle: enable/disable quit button and one slider
        bs = ButtonList(self.cb_en_dis)
        lst_en_dis = [self.slave1, btnquit]
        button = bs.add_button((280, 240), font = font14, fontcolor = BLACK, height = 30, width = 90,
                            fgcolor = GREEN, shape = RECTANGLE, text = 'Disable', args = [True, lst_en_dis])
        button = bs.add_button((280, 240), font = font14, fontcolor = BLACK, height = 30, width = 90,
                            fgcolor = RED, shape = RECTANGLE, text = 'Enable', args = [False, lst_en_dis])

# CALLBACKS
# cb_end occurs when user stops touching the control
    def callback(self, slider, device):
        print('{} returned {}'.format(device, slider.value()))

    def master_moved(self, slider):
        val = slider.value()
        self.slave1.value(val)
        self.slave2.value(val)
        self.lstlbl[0].value(to_string(val))

# Either slave has had its slider moved (by user or by having value altered)
    def slave_moved(self, slider, idx):
        val = slider.value()
        self.lstlbl[idx].value(to_string(val))

    def cb_en_dis(self, button, disable, itemlist):
        for item in itemlist:
            item.greyed_out(disable)

# TASKS
    async def task1(self):
        angle = 0
        while True:
            await asyncio.sleep_ms(100)
            delta = self.slave1.value()
            angle += pi * 2 * delta / 10
            self.dial1.value(angle)
            self.dial1.value(angle /10, 1)

    async def task2(self):
        angle = 0
        while True:
            await asyncio.sleep_ms(100)
            delta = self.slave2.value()
            angle += pi * 2 * delta / 10
            self.dial2.value(angle)
            self.dial2.value(angle /10, 1)


def test():
    print('Test TFT panel...')
    setup()  # Initialise GUI (see tft_local.py)
    Screen.set_grey_style(desaturate = False) # dim
    Screen.change(VerticalSliderScreen)       # Run it!

test()
