# hst.py Demo/test program for horizontal slider class for Pyboard RA8875 GUI

# Released under the MIT License (MIT). See LICENSE.
# Copyright (c) 2019 Peter Hinch

import urandom
import uasyncio as asyncio
from micropython_ra8875.py.ugui import Screen
from micropython_ra8875.py.colors import *

from micropython_ra8875.widgets.buttons import Button, ButtonList
from micropython_ra8875.widgets.label import Label
from micropython_ra8875.widgets.led import LED
from micropython_ra8875.widgets.meter import Meter
from micropython_ra8875.widgets.dial import Dial
from micropython_ra8875.widgets.sliders import HorizSlider

from micropython_ra8875.fonts import font10, font14
from micropython_ra8875.driver.tft_local import setup

# STANDARD BUTTONS

def quitbutton():
    def quit(button):
        Screen.shutdown()
    Button((390, 240), font = font14, callback = quit, fgcolor = RED, text = 'Quit', width=80, height=30)

def to_string(val):
    return '{:3.1f}Ω'.format(val * 10)

class SliderScreen(Screen):
    def __init__(self):
        super().__init__()
        labels = { 'width' : 60,
                'fontcolor' : WHITE,
                'border' : 2,
                'fgcolor' : RED,
                'bgcolor' : DARKGREEN,
                'font' : font10,
                }
        quitbutton()
        meter1 = Meter((320, 0), barcolor=YELLOW, fgcolor=CYAN, bgcolor=BLACK)
        meter2 = Meter((360, 0), font=font10, legends=('0','5','10'), barcolor=GREEN,
                           fgcolor=CYAN, bgcolor=BLACK, cb_move=self.meter_change)
        x = 230
        lstlbl = []
        for n in range(3):
            lstlbl.append(Label((x, 40 + 60 * n), **labels))
        led = LED((420, 0), border = 2)
        slave1 = HorizSlider((10, 100), fgcolor = GREEN,
                                 cb_move = self.slave_moved, cbm_args = (lstlbl[1],), border = 2)
        slave2 = HorizSlider((10, 160), fgcolor = GREEN,
                                 cb_move = self.slave_moved, cbm_args = (lstlbl[2],), border = 2)
        master = HorizSlider((10, 40), font = font10, fgcolor = YELLOW, fontcolor = WHITE,
                                  legends = ('0', '5', '10'), cb_end = self.callback,
                                  cbe_args = ('Master',), cb_move = self.master_moved, cbm_args = (lstlbl[0], slave1, slave2, led),
                                  value=0.5, border = 2)
    # On/Off toggle: enable/disable quit button and one slider
        bs = ButtonList(self.cb_en_dis)
        lst_en_dis = [slave1, slave2, master]
        bs.add_button((280, 240), font = font14, fontcolor = BLACK, fgcolor = GREEN,
                      text = 'Disable', height=30, width=90, args = [True, lst_en_dis])
        bs.add_button((280, 240), font = font14, fontcolor = BLACK, fgcolor = RED,
                      text = 'Enable', height=30, width=90, args = [False, lst_en_dis])
        loop = asyncio.get_event_loop()
        loop.create_task(self.test_meter(meter1))
        loop.create_task(self.test_meter(meter2))

# CALLBACKS
# cb_end occurs when user stops touching the control
    def callback(self, slider, device):
        print('{} returned {}'.format(device, slider.value()))

    def master_moved(self, slider, label, slave1, slave2, led):
        val = slider.value()
        led.value(val > 0.8)
        slave1.value(val)
        slave2.value(val)
        label.value(to_string(val))

    def cb_en_dis(self, button, disable, itemlist):
        for item in itemlist:
            item.greyed_out(disable)

    def meter_change(self, meter):
        val = meter.value()
        if val > 0.8:
            meter.color(RED)
        elif val < 0.2:
            meter.color(BLUE)
        else:
            meter.color(GREEN)

# Either slave has had its slider moved (by user or by having value altered)
    def slave_moved(self, slider, lbl):
        val = slider.value()
        if val > 0.8:
            slider.color(RED)
        else:
            slider.color(GREEN)
        lbl.value(to_string(val))

# COROUTINE
    async def test_meter(self, meter):
        oldvalue = 0
        await asyncio.sleep(0)
        while True:
            val = urandom.getrandbits(16) / 2**16
            steps = 20
            delta = (val - oldvalue) / steps
            for _ in range(steps):
                oldvalue += delta
                meter.value(oldvalue)
                await asyncio.sleep_ms(100)


def test():
    print('Test TFT panel...')
    # Instantiate loop before calling setup to change queue sizes
    loop = asyncio.get_event_loop()
    setup()
    Screen.set_grey_style(desaturate = False) # dim
    Screen.change(SliderScreen)       # Run it!

test()
