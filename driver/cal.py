# cal.py Calibration utility for ra8875 driver.

# Released under the MIT License (MIT). See LICENSE.
# Copyright (c) 2019 Peter Hinch

import uasyncio as asyncio
import uos as os
import sys
from micropython_ra8875.support.constants import *  # Colors
from micropython_ra8875.tft_local import setup

tft = setup(True, True)

ll = 20  # Crosshairs for calibration
lc = YELLOW
tft.draw_hline(0, 0, ll, lc)
tft.draw_vline(0, 0, ll, lc)
tft.draw_hline(tft.width() -ll - 1, tft.height() - 1, ll, lc)
tft.draw_vline(tft.width() - 1, tft.height() -ll - 1, ll, lc)

msg1 = '''To calibrate touch the screen at the top left
and bottom right hand corners of the screen
where the yellow lines meet - ideally with a
stylus.
Record the resultant x and y values.
Adapt tft_local.py accordingly.

Press ctrl-c to quit.'''

x = 50
y = 80
for s in msg1.split('\n'):
    tft.draw_str(s, x, y, GREEN, BLACK)
    y += 16

data = [0, 0, 0, 0]
async def do_touch(tft):
    while True:
        if tft.ready():
            x, y = tft.get_touch()
            offs = 0 if x < 100 else 2
            data[offs : offs + 2] = x, y
            print(x, y)
        await asyncio.sleep_ms(20)

print('See on-screen instructions.')
loop = asyncio.get_event_loop()
try:
    loop.run_until_complete(do_touch(tft))
except KeyboardInterrupt:
    loop.close()

if not input('Keep these calibration values (y/n)? ').lower() == 'y':
    print('No changes made. Quitting.')
    sys.exit(0)

source = 'micropython_ra8875/tft_local.py'
temp = 'micropython_ra8875/tft_local.bak'
try:
    with open(source, 'r') as fr, open(temp, 'w') as fw:
        for line in fr:
            if 'tft.calibrate' in line:
                line = '    tft.calibrate({:d},{:d},{:d},{:d})  # Auto updated by cal.py\n'.format(*data)
            fw.write(line)
except OSError:
    print('Could not open {:s} for reading or {:s} for writing.'.format(source, temp))
    sys.exit(1)

try:
    os.remove(source)
    os.rename(temp, source)
except OSError:
    print('Could not replace {:s} with {:s}.'.format(source, temp))
    sys.exit(1)

print('Successfully updated your calibration data.')
