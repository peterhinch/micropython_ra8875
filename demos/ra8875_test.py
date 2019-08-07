# ra8875_test.py Test program for ra8875 driver.

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
from utime import sleep_ms, ticks_us, ticks_diff
from machine import SPI, Pin
try:
    import font10  # Hopefully frozen bytecode
except ImportError:
    import micropython_ra8875.demos.font10 as font10
from micropython_ra8875.ra8875 import RA8875
from micropython_ra8875.constants import *  # Colors

# Change for pin numbers and display size

loop = asyncio.get_event_loop()
pinrst = Pin('X4', Pin.OUT, value=1)
pincs = Pin('X5', Pin.OUT, value=1)
spi = SPI(2, baudrate=6_000_000)
tft = RA8875(spi, pincs, pinrst, 480, 272, loop)

# Draw basic shapes
x = 10
y = 10
tft.fill_rectangle(x, y, x + 40, y + 40, RED)
x += 50
tft.draw_rectangle(x, y, x + 40, y + 40, GREEN)
x += 50
tft.draw_clipped_rectangle(x, y, x + 40, y + 40, YELLOW, 5)
x += 50
tft.fill_clipped_rectangle(x, y, x + 40, y + 40, BLUE, 5)

y += 20
x += 70
tft.fill_circle(x, y, 20, RED)
x += 50
tft.draw_circle(x, y, 20, GREEN)

# Test line drawing
ll = 20  # Crosshairs for calibration
lc = YELLOW
tft.draw_hline(0, 0, ll, lc)
tft.draw_vline(0, 0, ll, lc)
tft.draw_hline(tft.width() -ll - 1, tft.height() - 1, ll, lc)
tft.draw_vline(tft.width() - 1, tft.height() -ll - 1, ll, lc)
x = 10
y = 80
tft.draw_hline(x, y, 50, GREEN)
tft.draw_vline(x, y, 50, GREEN)
tft.draw_hline(x, y + 50, 50, GREEN)
tft.draw_vline(x + 50, y, 50, GREEN)
tft.draw_line(x, y, x + 50, y + 50, GREEN)
tft.draw_line(x, y + 50, x + 50, y, GREEN)

# Save and restore a region
mv = memoryview(bytearray(4*(40 + 3)))
tft.save_region(mv, 9, 10, 14, 11)
print(bytes(mv))
tft.restore_region(mv, 9, 150, 14, 151)

# Render a glyph and measure performance.
mv, rows, cols = font10.get_ch('A')
x = 200
nchars = 20
t = ticks_us()
for _ in range(nchars):
    tft.draw_glyph(mv, x, 100, rows, cols, GREEN, BLACK)
    x += cols
print('Time per char (us)', ticks_diff(ticks_us(), t)/nchars)  # 3.4ms for font10.

# Verify glyph doesn't exceed bounding box
x, y = 100, 200
tft.fill_rectangle(x, y, x + 40, y + 40, GREEN)
x = 88
tft.draw_glyph(mv, x, y, rows, cols, BLACK, YELLOW)

for x in range(10, 15):
    tft.draw_pixel(x, 180, YELLOW)
    print(hex(tft.get_pixel(x, 180)))

# Test touch panel
msg = '''To calibrate touch the screen at the top left and bottom right
hand corners of the displayable area, ideally with a stylus. Record
the maximum and minimum x and y values and adapt tft_local.py accordingly.'''
async def do_touch(tft):
    print(msg)
    while True:
        if tft.ready():
            print(tft.get_touch())
        if tft.touched():
            print('touched')
        await asyncio.sleep_ms(20)

loop.run_until_complete(do_touch(tft))
