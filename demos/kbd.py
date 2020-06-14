# kbd.py Demo/test program for 800x480 screen with RA8875 GUI

# Released under the MIT License (MIT). See LICENSE.
# Copyright (c) 2019-2020 Peter Hinch

# Updated for uasyncio V3

import uasyncio as asyncio
from micropython_ra8875.py.ugui import Screen
from micropython_ra8875.py.colors import *
from micropython_ra8875.driver.constants import *
from micropython_ra8875.widgets.buttons import Button, ButtonList, RadioButtons
from micropython_ra8875.widgets.label import Label
from micropython_ra8875.widgets.textbox import Textbox
from micropython_ra8875.fonts import font10, font14
from micropython_ra8875.driver.tft_local import setup

CURSOR = '_'

class Key(Button):  # A Key is a Button whose text may dynamically change
    def __init__(self, x, y, text, shift, tb):
        super().__init__((x, y), font = font14, shape = CIRCLE, fgcolor = LIGHTGREEN,
                         litcolor = YELLOW, text = text, fontcolor = WHITE,
                         callback = bcb, args = (tb,))
        self.shift = shift
        self.norm = text
        self.upper = True

    def do_shift(self):
        if self.upper:
            self.text = self.shift
        else:
            self.text = self.norm
        self.upper = not self.upper
        self.show()

def quitbutton():
    Button((719, 449), font = font14, height = 30, width = 80, shape = RECTANGLE,
           fgcolor = RED, text = 'Quit', callback = lambda _ : Screen.shutdown())

def bcb(button, tb):  # Callback from normal keys
    ch = button.text
    line = tb.lines[-1][:-1]  # Last line less cursor
    tb.lines = tb.lines[:-1]  # Strip last line
    if ch == 'En':
        line = ''.join((line, '\n', CURSOR))
    elif ch == 'Bs':
        if line:
            line = ''.join((line[:-1], CURSOR))
        elif tb.lines:
            line = ''.join((tb.lines[-1], CURSOR))
            tb.lines = tb.lines[:-1]  # Strip last line
    else:
        line = ''.join((line, ch, CURSOR))
    tb.append(line, ntrim = 20)  # Scroll up to 20 lines

def make_keys(tb):  # Create alphanumeric keys
    rows = (('`1234567890-=', '¬!"£$%^&*()_+', 0),
            ('qwertyuiop[]', 'QWERTYUIOP{}', 81),
            ("asdfghjkl;'#", "ASDFGHJKL:@~", 107), 
            ('\zxcvbnm,./', '|ZXCVBNM<>?', 81))
    def row(x, y, legends, shift):
        for n, l in enumerate(legends):
            keys.add(Key(x, y, l, shift[n], tb))
            x += 55
    y = 0
    keys = set()
    for legends, shift, x in rows:
        row(x, y, legends, shift)
        y += 55
    return keys

def ctrl(tb, keys):  # Create control keys
    table = { 'shape' : CIRCLE, 'fgcolor' : RED, 'fontcolor' : WHITE, 'litcolor' : YELLOW, }
    def shift(_):
        for k in keys:
            k.do_shift()
    Button((741, 55), font = font14, text = 'En', callback=bcb, args = (tb,), **table)
    Button((715, 0), font = font14, text = 'Bs', callback=bcb, args = (tb,), **table)
    Button((300, 220), font = font14, shape = CLIPPED_RECT, width = 200, height = 30,
           fgcolor = LIGHTGREEN, litcolor = YELLOW, callback = bcb, args = (tb,), text = " ")  # Spacebar
    Button((0, 165), font = font14, text = 'Shift', callback=shift,
           shape = CLIPPED_RECT, fgcolor = RED, fontcolor = WHITE, litcolor = YELLOW)

def tbox(x, y):  # Textbox
    return Textbox((x, y), 600, 8, font=IFONT16, fgcolor = RED, bgcolor = DARKGREEN,
                   fontcolor = GREEN, repeat = False, clip = False)


class KBD(Screen):
    def __init__(self):
        super().__init__()
        quitbutton()
        tb = tbox(0, 280)  # Create textbox
        tb.append(CURSOR)  # display a cursor
        keys = make_keys(tb)  # Create normal keys
        ctrl(tb, keys)  # Create control keys

def test():
    print('Test TFT panel...')
    setup()  # Initialise GUI (see tft_local.py)
    try:
        Screen.change(KBD)       # Run it!
    finally:
        asyncio.new_event_loop()

test()
