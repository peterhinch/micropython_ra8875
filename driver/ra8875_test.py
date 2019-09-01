# ra8875_test.py Test program for ra8875 driver.

# Released under the MIT License (MIT). See LICENSE.
# Copyright (c) 2019 Peter Hinch

from utime import sleep_ms, ticks_us, ticks_diff
import micropython_ra8875.fonts.font10 as font10
from micropython_ra8875.py.colors import *  # Colors
from micropython_ra8875.driver.tft_local import setup

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
