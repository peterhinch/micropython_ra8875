# tbox.py Test/demo of Textbox

# The MIT License (MIT)
#
# Copyright (c) 2019 Peter Hinch
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

import uasyncio as asyncio
from micropython_ra8875.support.constants import *
from micropython_ra8875.ugui import Textbox, Label, Button, Screen
from micropython_ra8875.tft_local import setup
import micropython_ra8875.support.font14 as font14
import micropython_ra8875.support.font10 as font10

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

class BackScreen(Screen):
    def __init__(self):
        super().__init__()
        Label((0, 0), font = font14, value = 'Ensure back refreshes properly')
        backbutton()

# Create a random vector. Interpolate between current vector and the new one.
# Change pointer color dependent on magnitude.
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

def btn_cb(button, tb1, tb2, n):
    tb1.scroll(n)
    tb2.scroll(n)

class TScreen(Screen):
    def __init__(self, loop):
        super().__init__()
        labels = {'fontcolor' : WHITE,
                  'border' : 2,
                  'fgcolor' : RED,
                  'bgcolor' : DARKGREEN,
                  'font' : font10,
                  }
        tbargs = {'fontcolor' : GREEN,
                  'fgcolor' : RED,
                  'bgcolor' : DARKGREEN,
                  'font' : IFONT16,
                  'repeat' : False,
                  }
        btntable = {'fgcolor' : LIGHTBLUE,
                    'font' : font14,
                    'height' : 30,
                    'width' : 100,
                    'litcolor' : GREEN,
                    'callback' : btn_cb,
                    }
        fwdbutton(0, 242, BackScreen, 'Forward')
        quitbutton()
        tb1 = Textbox((0, 0), 200, 8, **tbargs)
        tb2 = Textbox((210, 0), 200, 8, clip = False, **tbargs)
        Label((0, 135), width = 200, value = 'Clipping', **labels)
        Label((210, 135), width = 200, value = 'Wrapping', **labels)

        btns = (Button((0, 180), text = 'Up', args = (tb1, tb2, 1), **btntable),
                Button((120, 180), text = 'Down', args = (tb1, tb2, -1), **btntable))
        for btn in btns:
            btn.greyed_out(True)  # Disallow until textboxes are populated

        loop.create_task(txt_test(tb1, None))
        loop.create_task(txt_test(tb2, btns))


print('Test TFT panel...')
# Instantiate loop before calling setup if you need to change queue sizes
loop = asyncio.get_event_loop()
setup()
Screen.change(TScreen, args=(loop,))
