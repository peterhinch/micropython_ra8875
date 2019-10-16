# audio.py Demo/test program for 800x480 screen with RA8875 GUI

# Released under the MIT License (MIT). See LICENSE.
# Copyright (c) 2019 Peter Hinch

import uasyncio as asyncio
import urandom

from micropython_ra8875.py.ugui import Screen
from micropython_ra8875.py.colors import *
from micropython_ra8875.widgets.buttons import Button, ButtonList, RadioButtons
from micropython_ra8875.widgets.label import Label
from micropython_ra8875.widgets.sliders import Slider, HorizSlider
from micropython_ra8875.widgets.checkbox import Checkbox
from micropython_ra8875.widgets.meter import Meter
from micropython_ra8875.fonts import font10, font14
from micropython_ra8875.driver.tft_local import setup

def quitbutton():
    def quit(button):
        Screen.shutdown()
    Button((769, 0), height = 30, font = font14, callback = quit,
           fgcolor = RED, text = 'X', shape = RECTANGLE, width = 30)

def geq(x, y):  # Graphic equaliser
    fr = ('25Hz', '50Hz', '100Hz', '200Hz', '400Hz', '800Hz',
          '1.5KHz', '3KHz', '6KHz', '12KHz')
    table = {'fontcolor' : WHITE,
            'legends' : ('-20', '0', '20'),
            'font' : font10,
            'fgcolor' : GREEN,
            'value' : 0.5, }
    sliders = []
    for freq in fr:
        sliders.append(Slider((x, y), **table))
        Label((x, y + 210), font=font10, value=freq)
        x += 80
    return sliders

def cb_en_dis(cb, itemlist):  # Enable/disable the graphic eq
    for item in itemlist:
        item.value(0.5)
        item.greyed_out(cb.value())

def passthru(x, y, items):  # Passthru checkbox
    Checkbox((x, y), callback = cb_en_dis, args = (items,))
    Label((x + 40, y), font=font14, value='Flat response')

def volume(x, y):  # Volume slider
    table = {'fontcolor' : WHITE,
            'font' : font10,
            'fgcolor' : YELLOW,
            'legends' : ('0', '5', '11'),
            'value' : 0.7, }
    Label((x + 50, y + 100), font=font14, value='Volume')
    return Slider((x, y + 10), **table)

def balance(x, y):  # Balance slider
    table = {'fontcolor' : WHITE,
            'legends' : ('L', 'C', 'R'),
            'font' : font10,
            'fgcolor' : CYAN,
            'value' : 0.5, }
    Label((x, y + 50), font=font14, value='Balance')
    return HorizSlider((x, y), **table)

def source(x, y, cb=lambda *_:None):  # Source radiobuttons
        rb = RadioButtons(BLUE, cb)
        for t in (('1', 'Radio'), ('2', 'CD'), ('3', 'Vinyl'), ('4', 'TV')):
            button = rb.add_button((x, y), font = font14, fontcolor = WHITE, shape = CIRCLE,
                                fgcolor = (0, 0, 90), height = 40, width = 40, text = t[0])
            Label((x + 50, y + 10), font = font14, value = t[1])
            y += 55

def meters(x, y):
    table = { 'barcolor' : GREEN, 'fgcolor' : GREEN, 'bgcolor' : BLACK, }
    return Meter((x, y), **table), Meter((x + 50, y), **table)

async def run(meters, vctrl, bctrl):
    grv = lambda : urandom.getrandbits(16) / 2**16  # Random: range 0.0 to +1.0
    while True:
        v = 1.5 * grv() * vctrl.value()
        d = 1 + 0.1 * grv()
        vl = v * d * 2 * (1 - bctrl.value())
        vr = (v / d) * 2 * bctrl.value()  # left and right show similar values
        if vl > 0.8:
            meters[0].color(RED if vl >= 1 else YELLOW)
        else:
            meters[0].color(CYAN)
        if vr > 0.8:
            meters[1].color(RED if vr >= 1 else YELLOW)
        else:
            meters[1].color(CYAN)
        meters[0].value(min(1.0, vl))
        meters[1].value(min(1.0, vr))
        await asyncio.sleep_ms(200)

class GEQ(Screen):
    def __init__(self, loop):
        super().__init__()
        quitbutton()
        source(20, 0)
        vctrl = volume(240, 0)
        bctrl = balance(400, 50)
        lst_geq = geq(0, 250)
        passthru(400, 180, lst_geq)
        loop.create_task(run(meters(630, 0), vctrl, bctrl))


print('Test TFT panel...')
loop = asyncio.get_event_loop()
setup()  # Initialise GUI (see tft_local.py)
Screen.set_grey_style(desaturate = False) # dim
Screen.change(GEQ, args=(loop,))       # Run it!
