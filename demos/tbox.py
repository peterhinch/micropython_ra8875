# tbox.py Test/demo of Textbox

# Released under the MIT License (MIT). See LICENSE.
# Copyright (c) 2019-2020 Peter Hinch

# Updated for uasyncio V3

import uasyncio as asyncio
from micropython_ra8875.py.ugui import Screen
from micropython_ra8875.py.colors import *
from micropython_ra8875.driver.constants import *

from micropython_ra8875.widgets.buttons import Button
from micropython_ra8875.widgets.label import Label
from micropython_ra8875.widgets.textbox import Textbox

from micropython_ra8875.fonts import font10, font14
from micropython_ra8875.driver.tft_local import setup

# **** STANDARD BUTTON TYPES ****

def quitbutton(x=379, y=242):
    def quit(button):
        Screen.shutdown()
    Button((x, y), height = 30, font = font14, callback = quit, fgcolor = RED,
           text = 'Quit', shape = RECTANGLE, width = 100)

def fwdbutton(x, y, cls_screen, text='Next'):
    def fwd(button):
        Screen.change(cls_screen)
    Button((x, y), height = 30, font = font14, callback = fwd, fgcolor = RED,
           text = text, shape = RECTANGLE, width = 100)

def backbutton(x=399, y=242):
    def back(button):
        Screen.back()
    Button((x, y), height = 30, font = font14, fontcolor = BLACK, callback = back,
           fgcolor = CYAN,  text = 'Back', shape = RECTANGLE, width = 80)

# **** STANDARDISE CONTROLS ACROSS SCREENS ****
# Appearance for Textbox instances
tbargs = {'fontcolor' : GREEN,
            'fgcolor' : RED,
            'bgcolor' : DARKGREEN,
            'repeat' : False,
            }

# Appearance for buttons
btntable = {'fgcolor' : LIGHTBLUE,
            'font' : font14,
            'height' : 30,
            'width' : 100,
            'litcolor' : GREEN,
            }

# Appearance for labels
labels = {'fontcolor' : WHITE,
            'border' : 2,
            'fgcolor' : RED,
            'bgcolor' : DARKGREEN,
            'font' : font10,
            }

# **** NEXT SCREEN CLASS ****

# Fast populate a textbox
def populate(button, tb):
    s = '''The textbox displays multiple lines of text in a field of fixed dimensions. \
Text may be clipped to the width of the control or may be word-wrapped. If the number \
of lines of text exceeds the height available, scrolling may be performed, either \
by calling a method or by touching the control.
'''
    tb.append(s, ntrim = 100, line = 0)

def clear(button, tb):
    tb.clear()

class BackScreen(Screen):
    def __init__(self):
        super().__init__()
        backbutton()
        tb = Textbox((0, 0), 200, 8, font=IFONT16, clip = False, tab=64, **tbargs)
        Button((0, 180), text = 'Fill', callback = populate, args = (tb,), **btntable)
        Button((120, 180), text = 'Clear', callback = lambda b, tb: tb.clear(), args = (tb,), **btntable)

# **** TAB SCREEN CLASS ****

def pop_tabs(button, tb):
    s = '''x\t100.0\t1.76
alpha\t1.73\t2.51
beta\t91.84\t8.76
gamma\t9.29\t0.05
'''
    tb.append(s)

def clear(button, tb):
    tb.clear()

class TabScreen(Screen):
    def __init__(self):
        super().__init__()
        backbutton()
        tb = Textbox((0, 0), 200, 8, font=font10, clip = False, tab=64, **tbargs)
        Button((0, 180), text = 'Fill', callback = pop_tabs, args = (tb,), **btntable)
        Button((120, 180), text = 'Clear', callback = lambda b, tb: tb.clear(), args = (tb,), **btntable)

# **** MAIN SCREEEN CLASS ****

# Coroutine slowly populates a text box
async def txt_test(textbox, btns):
    phr0 = ('short', 'longer line', 'much longer line with spaces',
               'antidisestablishmentarianism', 'with\nline break')
    for n in range(len(phr0)):
        textbox.append('Test {:3d} {:s}'.format(n, phr0[n]), 15)
        await asyncio.sleep(1)

    for n in range(n, 15):
        textbox.append('Scroll test {:3d}'.format(n), 15)
        await asyncio.sleep(1)

    if isinstance(btns, tuple):
        for btn in btns:
            btn.greyed_out(False)

# Callback for scroll buttons
def btn_cb(button, tb1, tb2, n):
    tb1.scroll(n)
    tb2.scroll(n)

class TScreen(Screen):
    def __init__(self):
        super().__init__()
        fwdbutton(0, 242, BackScreen, 'Fast')
        fwdbutton(120, 242, TabScreen, 'Tabs')
        quitbutton()
        tb1 = Textbox((0, 0), 200, 8, font=IFONT16, **tbargs)
        tb2 = Textbox((210, 0), 200, 8, font=IFONT16, clip = False, **tbargs)
        Label((0, 135), width = 200, value = 'Clipping', **labels)
        Label((210, 135), width = 200, value = 'Wrapping', **labels)

        btns = (Button((0, 180), text = 'Up', callback = btn_cb, args = (tb1, tb2, 1), **btntable),
                Button((120, 180), text = 'Down', callback = btn_cb, args = (tb1, tb2, -1), **btntable))
        for btn in btns:
            btn.greyed_out(True)  # Disallow until textboxes are populated

        self.reg_task(txt_test(tb1, None))
        self.reg_task(txt_test(tb2, btns))


def test():
    print('''Main screen populates text boxes slowly to show
    clipping and wrapping in action. "Fast" screen
    shows fast updates using internal font. "Tab"
    screen shows use of tab characters with Python
    font.
    Text boxes may be scrolled by touching them near
    the top or bottom.''')
    setup()
    try:
        Screen.change(TScreen)
    finally:
        asyncio.new_event_loop()

test()
