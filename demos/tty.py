# tty.py Demo/test program for 800x480 screen with RA8875 GUI

# Released under the MIT License (MIT). See LICENSE.
# Copyright (c) 2019-2020 Peter Hinch

# Updated for uasyncio V3

# TODO add buttons for reset, ctrl-c, ctrl-d
# Consider cursor
# Logic for text input
import uasyncio as asyncio
from micropython_ra8875.py.ugui import Screen
from micropython_ra8875.py.colors import *
from micropython_ra8875.driver.constants import *
from micropython_ra8875.widgets.buttons import Button, ButtonList, RadioButtons
from micropython_ra8875.widgets.label import Label
from micropython_ra8875.widgets.textbox import Textbox
from micropython_ra8875.fonts import font10, font14
from micropython_ra8875.driver.tft_local import setup
from pyb import UART, Pin
from utime import ticks_diff, ticks_ms

CURSOR = '_'
NLINES = 20
pin_rst = Pin('Y3', Pin.OUT_OD)
pin_rst.value(1)

class Key(Button):  # A Key is a Button whose text may dynamically change
    def __init__(self, x, y, text, shift, uart):
        super().__init__((x, y), font = font14, shape = CIRCLE, fgcolor = LIGHTGREEN,
                         litcolor = YELLOW, text = text, fontcolor = WHITE,
                         callback = bcb, args = (uart,))
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

def bcb(button, uart):  # Callback from normal keys
    ch = button.text
    d = { 'En' : b'\r\n', 'Bs' : b'\x08', 'Tab' : b'\x09', 'Ctrl-c' : b'\x03', 'Ctrl-d' : b'\x04'}
    if ch in d:
        ch = d[ch]
    uart.write(ch)

def process_char(ch, tb):
    if tb.lines:
        line = tb.lines[-1]  # Last line
        tb.lines = tb.lines[:-1]  # Strip last line
    else:
        line = ''
    if ch == 'Bs':
        if line:
            line = line[:-1]
        elif tb.lines:
            line = tb.lines[-1]
            tb.lines = tb.lines[:-1]  # Strip last line
    else:
        line = ''.join((line, '\n') if ch == '\n' else (line, ch))
    tb.append(line, ntrim = NLINES)  # No of lines for scrolling

def make_keys(uart):  # Create alphanumeric keys
    rows = (('`1234567890-=', '¬!"£$%^&*()_+', 0),
            ('qwertyuiop[]', 'QWERTYUIOP{}', 81),
            ("asdfghjkl;'#", "ASDFGHJKL:@~", 107), 
            ('\zxcvbnm,./', '|ZXCVBNM<>?', 81))
    def row(x, y, legends, shift):
        for n, l in enumerate(legends):
            keys.add(Key(x, y, l, shift[n], uart))
            x += 55
    y = 0
    keys = set()
    for legends, shift, x in rows:
        row(x, y, legends, shift)
        y += 55
    return keys

async def do_rst():
    print('RESET', 0)  # TODO
    pin_rst.value(0)
    await asyncio.sleep_ms(500)
    pin_rst.value(1)
    print('RESET', 1)  # TODO

def rst(_):
    asyncio.create_task(do_rst())

def ctrl(uart, keys):  # Create control keys
    table = { 'shape' : CIRCLE, 'fgcolor' : RED, 'fontcolor' : WHITE, 'litcolor' : YELLOW, }
    def shift(_):
        for k in keys:
            k.do_shift()
    Button((741, 55), font = font14, text = 'En', callback=bcb, args = (uart,), **table)
    Button((27, 55), font = font14, text = 'Tab', callback=bcb, args = (uart,), **table)
    Button((715, 0), font = font14, text = 'Bs', callback=bcb, args = (uart,), **table)
    Button((300, 225), font = font14, shape = CLIPPED_RECT, width = 200, height = 30,
           litcolor = YELLOW, fgcolor = LIGHTGREEN, callback = bcb, args = (uart,), text = " ")  # Spacebar
    Button((715, 170), font = font14, width = 80, height = 40, text = 'Ctrl-c', callback=bcb, args = (uart,),
           shape = CLIPPED_RECT, fgcolor = RED, fontcolor = WHITE, litcolor = YELLOW)
    Button((715, 225), font = font14, width = 80, height = 40, text = 'Ctrl-d', callback=bcb, args = (uart,),
           shape = CLIPPED_RECT, fgcolor = RED, fontcolor = WHITE, litcolor = YELLOW)
    Button((715, 280), font = font14, width = 80, height = 40, text = 'Reset', callback=rst,
           shape = CLIPPED_RECT, fgcolor = RED, fontcolor = WHITE, litcolor = YELLOW)
    Button((0, 170), font = font14, text = 'Shift', height = 40, callback=shift,
           shape = CLIPPED_RECT, fgcolor = RED, fontcolor = WHITE, litcolor = YELLOW)

def tbox(x, y):  # Textbox
    return Textbox((x, y), 600, 11, font=IFONT16, fgcolor = RED, bgcolor = DARKGREEN,
                   fontcolor = GREEN, repeat = False, clip = False)

# This is a bit of a hack. Processing a character at a time leads to flicker
# when handling programmatic output so we try to detect if user is typing
async def handle_input(uart, sr, tb):
    while True:
        ch = await sr.readexactly(1)
        ch = ch.decode()
        #print('ch=', ch, hex(ord(ch)))
        if ch == '\r':
            continue
        if ch == '\x08':  # Pyboard echoes Backspace + VT100 code
            await sr.readexactly(3)  # discard VT100
            process_char('Bs', tb)
            continue
        else:
            await asyncio.sleep_ms(10)
            n = uart.any()
            if n:  # rapid input: assume programmatic
                s = await sr.readexactly(n)
                s = s.decode().replace('\r','')
                #for char in s:
                    #print('s:', char, hex(ord(char)))
                tb.append(''.join((ch, s)), ntrim = NLINES)  # TODO splits line on tab expansion because tb.append puts on new line
            else:
                process_char(ch, tb)


class KBD(Screen):
    def __init__(self):
        super().__init__()
        uart = UART(1, 115200, read_buf_len=256)
        sreader = asyncio.StreamReader(uart)
        quitbutton()
        tb = tbox(0, 280)  # Create textbox
        keys = make_keys(uart)  # Create normal keys
        ctrl(uart, keys)  # Create control keys
        self.reg_task(handle_input(uart, sreader, tb))

print('Test TFT panel...')
setup()  # Initialise GUI (see tft_local.py)
Screen.change(KBD)       # Run it!
