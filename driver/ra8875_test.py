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

from utime import sleep_ms, ticks_us, ticks_diff
import micropython_ra8875.support.font10 as font10
from micropython_ra8875.support.constants import *  # Colors
from micropython_ra8875.tft_local import setup

tft = setup(True, False)  # No aysncio

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
x = 10
y = 80
tft.draw_hline(x, y, 50, GREEN)
tft.draw_vline(x, y, 50, GREEN)
tft.draw_hline(x, y + 50, 50, GREEN)
tft.draw_vline(x + 50, y, 50, GREEN)
tft.draw_line(x, y, x + 50, y + 50, GREEN)
tft.draw_line(x, y + 50, x + 50, y, GREEN)


# Render a glyph and measure performance.
xstart = 100
y = 80
tft.draw_str('Measure render speed of Python font:', xstart, y, GREEN, BLACK)
y += 20
mv, rows, cols = font10.get_ch('A')
nchars = 30
x = xstart
t = ticks_us()
for _ in range(nchars):
    tft.draw_glyph(mv, x, y, rows, cols, GREEN, BLACK)
    x += cols
y += rows
x = xstart
dt = ticks_diff(ticks_us(), t) / (nchars * 1000)
tft.draw_str('Time per char: {:4.1f}ms'.format(dt), xstart, y, GREEN, BLACK)

# Verify glyph doesn't exceed bounding box
x, y = 400, 10
tft.fill_rectangle(x, y, x + 40, y + 40, GREEN)
x = 388
tft.draw_glyph(mv, x, y, rows, cols, BLACK, YELLOW)

# Test pixel draw
for x in range(10, 320, 3):
    tft.draw_pixel(x, 179, CYAN)
    tft.draw_pixel(x, 197, CYAN)

tft.draw_str('Test of pixel draw and internal font *1', 10, 180, CYAN, BLACK)
tft.draw_str('Internal font *2 size', 10, 220, YELLOW, BLACK, 1)
