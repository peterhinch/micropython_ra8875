# cal.py Calibration utility for ra8875 driver.

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
from utime import sleep_ms
from micropython_ra8875.support.constants import *  # Colors
import micropython_ra8875.support.font14 as font14
from micropython_ra8875.tft_local import setup

tft = setup(True, True)

ll = 20  # Crosshairs for calibration
lc = YELLOW
tft.draw_hline(0, 0, ll, lc)
tft.draw_vline(0, 0, ll, lc)
tft.draw_hline(tft.width() -ll - 1, tft.height() - 1, ll, lc)
tft.draw_vline(tft.width() - 1, tft.height() -ll - 1, ll, lc)

def print_string(s, x, y):
    xleft = x
    for c in s:
        if c == '\n':
            x = xleft
            y += rows
        else:
            fmv, rows, cols = font14.get_ch(c)
            tft.draw_glyph(fmv, x, y, rows, cols, GREEN, BLACK)
            x += cols

msg1 = '''To calibrate touch the screen at the top left
and bottom right hand corners of the displayable
area, ideally with a stylus. Record the maximum
and minimum x and y values.
Adapt tft_local.py accordingly.
Press ctrl-c to quit.'''

print_string(msg1, 0, 30)

async def do_touch(tft):
    while True:
        if tft.ready():
            print(tft.get_touch())
        await asyncio.sleep_ms(20)

loop = asyncio.get_event_loop()
try:
    loop.run_until_complete(do_touch(tft))
except KeyboardInterrupt:
    loop.close()
print('Done')
