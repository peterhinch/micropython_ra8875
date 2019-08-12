# ra8875.py A MicroPython driver for TFT displays based on the RA8875 chip, in
# particular those from Adafruit:
# RA8875 breakout
# https://www.adafruit.com/product/1590
# Supported displays
# 800x480 https://www.adafruit.com/product/2354
# Also https://www.adafruit.com/product/1596
# 480x272 https://www.adafruit.com/product/1591

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

# The following sources were used in writing this driver.
# CircuitPython library https://github.com/adafruit/Adafruit_CircuitPython_RA8875
# written by Melissa LeBlanc-Williams for Adafruit Industries.
# Arduino library https://github.com/adafruit/Adafruit_RA8875
# written by Limor Fried/Ladyada for Adafruit Industries.
# Datasheet: https://cdn-shop.adafruit.com/datasheets/RA8875_DS_V19_Eng.pdf
# App note: https://cdn-shop.adafruit.com/datasheets/ra8875+app+note.pdf

from utime import sleep_ms
import uasyncio as asyncio
from uctypes import addressof
from micropython import const

MAX_CHAR_WIDTH = const(100)

# Copy a row of a glyph to a destination buffer. Each bit is output as a 16 bit
# color value
# r0 Pointer to source bytes
# r1 Pointer to destination bytes
# r2 Bit count (columns) << 16 | backgound color
# r3 Color value (LS 16 bits RGB565 little endian)
# Viper version adds 3% to glyph rendering time compared to assembler: I
# accepted a minimal overhead in the name of portability.

@micropython.viper
def lcopy(ps : ptr8, pd : ptr8, bcbg : int, fgc : int):
    bgc0 = bcbg & 0xff
    bgc1 = (bcbg & 0xff00) >> 8
    bc = bcbg >> 16  # bit count
    fgc0 = fgc & 0xff
    fgc1 = (fgc & 0xff00) >> 8
    mask = 0x80
    dp = 3  # Skip preamble
    sp = 0
    for bit in range(bc):
        one = ps[sp] & mask
        pd[dp] = fgc0 if one else bgc0
        dp += 1
        pd[dp] = fgc1 if one else bgc1
        dp += 1
        mask >>= 1
        if not mask:
            mask = 0x80
            sp += 1

# SPI: Adafruit recommend 6MHz. Default polarity and phase (0)
class RA8875:
    # colors: the GUI uses an (r, g, b) tuple of bytes. Panel uses RGB565.
    # Convert tuple to little endian RGB565
    @staticmethod
    def _to_rgb565(rgb):
        r, g, b = rgb
        return (r & 0xf8) | ((g & 0xe0) >> 5) | ((g & 0x1c) << 11) | ((b & 0xf8) << 5)

    def __init__(self, spi, pincs, pinrst, width, height, loop=None):
        if (width, height) not in ((800, 480), (480, 272)):
            raise ValueError('Supported sizes are 800x480 and 480x272')
        self._spi = spi
        self._pincs = pincs
        self._pinrst = pinrst
        self._width = width
        self._height = height
        self._touch_data = None
        # Default touchscreen calibration
        self._calibrated = False
        self._xmin = 0
        self._ymin = 0
        self._xcal = 1
        self._ycal = 1
        # Buffers for optimised glyph rendering
        # Buffer to hold one line of largest permissible glyph
        self._mvlb = memoryview(bytearray(3 + 2 * MAX_CHAR_WIDTH))
        self._mvlb[0:3] = b'\x80\x02\x00'  # Preamble to line: memory write command
        self._xl = bytearray(b'\x80\x46\x00\x00')
        self._xh = bytearray(b'\x80\x47\x00\x00')
        self._yl = bytearray(b'\x80\x48\x00\x00')
        self._yh = bytearray(b'\x80\x49\x00\x00')

        self._reset()  # Strictly display should be powered down until reset is done
        self._set_pll(width, height)
        self._write_reg(0x10, 0x0c)  # 16 bits/pixel 8 bit MCU
        self._init_panel(width, height)
        self._write_reg(0x01, 0x80)  # RA8875_PWRR_NORMAL | RA8875_PWRR_DISPON)
        self._write_reg(0xC7, 1)  # Enable TFT - display enable tied to GPIOX
        # Backlight
        self._write_reg(0x8A, 0x80 | 0x0a)  # RA8875_P1CR, RA8875_P1CR_ENABLE | RA8875_PWM_CLK_DIV1024
        self._write_reg(0x8B, 0xff)  # tft.PWM1out(255);
        if loop is not None:
            loop.create_task(self._dotouch())

    def calibrate(self, xmin, ymin, xmax, ymax):
        self._calibrated = True
        self._xmin = xmin
        self._ymin = ymin
        self._xcal = (self._width - 1) / (xmax - xmin)
        self._ycal = (self._height - 1) / (ymax - ymin)

    def _reset(self):
        self._pincs(1)
        self._pinrst(0)
        sleep_ms(2)
        self._pinrst(1)
        sleep_ms(20)

    # System clock: the crystal apperas to be 20MHz but the schematic is hard to read.
    # If so, the systam clock is 60MHz (value 0x0b) or 55MHz (value 0x0a)
    def _set_pll(self, width, height):
        self._write_reg(0x88, 0x0a if width == 480 else 0x0b)  # Application note suggests these values
        sleep_ms(1)
        self._write_reg(0x89, 2)
        sleep_ms(1)

    def _init_panel(self, width, height):
        if width == 480 and height == 272:
            pixclk = 0x80 | 2
            hsync_nondisp = 10
            hsync_start = 8
            hsync_pw = 48
            vsync_nondisp = 3
            vsync_start = 8
            vsync_pw = 10
        else: # (_size == RA8875_800x480)
            pixclk = 0x80 | 1
            hsync_nondisp = 26
            hsync_start = 32
            hsync_pw = 96
            vsync_nondisp = 32
            vsync_start = 23
            vsync_pw = 2

        self._write_reg(0x04, pixclk)
        sleep_ms(1)

        # Horizontal settings registers
        self._write_reg(0x14, width // 8 - 1)  # H width: (HDWR + 1) * 8 = 480
        self._write_reg(0x15, 0)  # RA8875_HNDFTR_DE_HIGH
        self._write_reg(0x16, (hsync_nondisp - 2) // 8)  # H non-display: HNDR * 8 + HNDFTR + 2 = 10
        self._write_reg(0x17, hsync_start // 8 - 1)  # Hsync start: (HSTR + 1)*8
        self._write_reg(0x18, hsync_pw // 8 - 1)  # HSync pulse width = (HPWR+1) * 8

        # Vertical settings registers
        self._write_reg(0x19, (height - 1) & 0xFF)
        self._write_reg(0x1a, (height - 1) >> 8)
        self._write_reg(0x1b, vsync_nondisp - 1)  # V non-display period = VNDR + 1
        self._write_reg(0x1c, (vsync_nondisp -1) >> 8)
        self._write_reg(0x1d, vsync_start - 1)  # Vsync start position = VSTR + 1
        self._write_reg(0x1e, (vsync_start - 1) >> 8)
        self._write_reg(0x1f, vsync_pw - 1)  # Vsync pulse width = VPWR + 1

        # Set active window X
        self._write_reg(0x30, 0)  # horizontal start point
        self._write_reg(0x31, 0)
        self._write_reg(0x34, (width - 1) & 0xFF)  # horizontal end point
        self._write_reg(0x35, (width - 1) >> 8)

        # Set active window Y
        self._write_reg(0x32, 0)  # vertical start point
        self._write_reg(0x33, 0)
        self._write_reg(0x36, (height - 1) & 0xFF) # vertical end point
        self._write_reg(0x37, (height - 1) >> 8)

        # Clear the entire window
        self.clr_scr()
        sleep_ms(50)
        self._write_reg(0x40, 0)  # Always in graphic mode

    def _write_reg(self, reg, val):
        self._pincs(0)
        self._spi.write(b'\x80')  # RA8875_CMDWRITE
        self._spi.write(int.to_bytes(reg, 1, 'little'))
        self._pincs(1)  # min th = 90ns
        self._pincs(0)
        self._spi.write(b'\x00')  # RA8875_DATAWRITE
        self._spi.write(int.to_bytes(val, 1, 'little'))
        self._pincs(1)

    def _read_reg(self, reg, buf=bytearray(1)):
        self._pincs(0)
        self._spi.write(b'\x80')  # RA8875_CMDWRITE
        self._spi.write(int.to_bytes(reg, 1, 'little'))
        self._pincs(1)
        self._pincs(0)
        self._spi.write(b'\x40')  # RA8875_DATAREAD
        self._spi.readinto(buf)
        self._pincs(1)
        return buf[0]

    def _wait_complete(self, reg=0x90, mask=0x80):
        while self._read_reg(reg) & mask:
            sleep_ms(1)

    def width(self):
        return self._width

    def height(self):
        return self._height

    # **** GRAPHICS PRIMITIVES ****

    def clr_scr(self):  # Clear screen
        self._write_reg(0x8e, 0x80)
        self._wait_complete(0x8e)

    # Given an (r, g, b) tuple, set the device's color registers
    def _set_color(self, rgb):
        r, g, b = rgb
        self._write_reg(0x63, (r & 0xff) >> 3)  # R
        self._write_reg(0x64, (g & 0xff) >> 2)  # G
        self._write_reg(0x65, (b & 0xff) >> 3)  # B

    # Set ends of line, rectangle, clipped rectangle
    def _set_start_end(self, x1, y1, x2, y2):
        x1 = int(x1)
        y1 = int(y1)
        x2 = int(x2)
        y2 = int(y2)
        self._write_reg(0x91, x1 & 0xff)  # Start
        self._write_reg(0x92, x1 >> 8)
        self._write_reg(0x93, y1 & 0xff)
        self._write_reg(0x94, y1 >> 8)

        self._write_reg(0x95, x2 & 0xff)  # End
        self._write_reg(0x96, x2 >> 8)
        self._write_reg(0x97, y2 & 0xff)
        self._write_reg(0x98, y2 >> 8)

    def draw_vline(self, x1, y1, l, rgb):
        self.draw_line(x1, y1, x1, y1 + l, rgb)

    def draw_hline(self, x1, y1, l, rgb):
        self.draw_line(x1, y1, x1 + l, y1, rgb)

    def draw_line(self, x1, y1, x2, y2, rgb):
        self._set_start_end(x1, y1, x2, y2)
        self._set_color(rgb)

        self._write_reg(0x90, 0)  # Draw draw_line
        self._write_reg(0x90, 0x80)  # Start draw
        self._wait_complete()

    def draw_rectangle(self, x1, y1, x2, y2, rgb):
        self._draw_rect(x1, y1, x2, y2, rgb, False)

    def fill_rectangle(self, x1, y1, x2, y2, rgb):
        self._draw_rect(x1, y1, x2, y2, rgb, True)

    def _draw_rect(self, x1, y1, x2, y2, rgb, fill):
        self._set_start_end(x1, y1, x2, y2)
        self._set_color(rgb)

        self._write_reg(0x90, 0xb0 if fill else 0x90)  # Draw rectangle
        self._wait_complete()

    def draw_clipped_rectangle(self, x1, y1, x2, y2, rgb, radius=3):
        self._dcr(x1, y1, x2, y2, rgb, radius, False)

    def fill_clipped_rectangle(self, x1, y1, x2, y2, rgb, radius=3):
        self._dcr(x1, y1, x2, y2, rgb, radius, True)

    def _dcr(self, x1, y1, x2, y2, rgb, radius, fill):
        self._set_start_end(x1, y1, x2, y2)

        self._write_reg(0xa1, radius & 0xff)  # LSB
        self._write_reg(0xa2, radius >> 8)  # MSB
        self._write_reg(0xa3, radius & 0xff)  # repeat radius
        self._write_reg(0xa4, radius >> 8)

        self._set_color(rgb)

        self._write_reg(0xa0, 0xe0 if fill else 0xa0)  # Draw circle square
        self._wait_complete(0xa0)

    def draw_circle(self, x1, y1, r, rgb):
        self._draw_circ(x1, y1, r, rgb, False)

    def fill_circle(self, x1, y1, r, rgb):
        self._draw_circ(x1, y1, r, rgb, True)

    def _draw_circ(self, x1, y1, radius, rgb, fill):
        x1 = int(x1)
        y1 = int(y1)
        radius = int(radius)
        self._write_reg(0x99, x1 & 0xff)  # Centre
        self._write_reg(0x9a, x1 >> 8)
        self._write_reg(0x9b, y1 & 0xff)
        self._write_reg(0x9c, y1 >> 8)

        self._write_reg(0x9d, radius)
        self._set_color(rgb)

        self._write_reg(0x90, 0x60 if fill else 0x40)
        self._wait_complete(0x90, 0x40)

    # **** PIXEL LEVEL PRIMITIVES ****

    # Set memory write X and Y pixel coordinates
    def _setxy(self, x, y, write):
        if write:
            self._write_reg(0x46, x & 0xff)  # Memory write cursor
            self._write_reg(0x47, x >> 8)
            self._write_reg(0x48, y & 0xff)
            self._write_reg(0x49, y >> 8)
        else:
            self._write_reg(0x4a, x & 0xff)  # Memory read cursor
            self._write_reg(0x4b, x >> 8)
            self._write_reg(0x4c, y & 0xff)
            self._write_reg(0x4d, y >> 8)

    # Draw single pixel
    def draw_pixel(self, x, y, rgb):  # OK
        self._setxy(x, y, True)
        self._pincs(0)
        self._spi.write(b'\x80\x02')  # RA8875_CMDWRITE
        self._pincs(1)
        self._pincs(0)
        self._spi.write(b'\x00' + int.to_bytes(RA8875._to_rgb565(rgb), 2, 'little'))  # MSB 1st
        self._pincs(1)

    # Read back RGB565 value of a pixel.
    def get_pixel(self, x, y, buf=bytearray(3)):
        self._setxy(x, y, False)

        self._pincs(0)
        self._spi.write(b'\x80\x02')  # RA8875_CMDWRITE RA8875_DATAREAD
        self._pincs(1)
        self._pincs(0)
        self._spi.write(b'\x40')
        self._spi.readinto(buf, 0x40)  # Data read
        self._pincs(1)
        return int.from_bytes(buf[1:], 'big')

    # Draw a glyph. Note mv is a memoryview into the horizontally mapped glyph.
    # Caller must validate dimensions.
    # Optimisation: don't deassert CS between writing register no. and writing
    # the memory write command (\x00).
    # Time to render a font10 "A" 3.4ms.
    @micropython.native
    def draw_glyph(self, mv, x, y, rows, cols, fgcolor, bgcolor):
        gbytes = ((cols - 1) >> 3) + 1  # Source bytes per row
        # Note that dest[0] is 0: the memory write command. Subsequent values are
        # 16 bit rgb565 color values for each pixel.
        dest = self._mvlb  # memoryview into line buffer
        # https://github.com/micropython/micropython/issues/4936 (use of addressof)
        # mv is a memoryview into a readonly (bytes) object.
        src = addressof(mv)
        offs = 0  # Offset into source
        on = RA8875._to_rgb565(fgcolor)  # Integer (16 bit half word)
        cx = RA8875._to_rgb565(bgcolor) | (cols << 16)
        xl = self._xl  # Cache the command buffers
        xh = self._xh
        yl = self._yl
        yh = self._yh
        xl[3] = x & 0xff
        xh[3] = x >> 8
        for row in range(rows):
            # dest[0:3] holds b'\x80\x02\x00' RA8875_CMDWRITE, MRWC, RA8875_DATAWRITE
            # populated by constructor.
            # lcopy populates dest[3:] with color value for each pixel in row.
            lcopy(src + offs, dest, cx, on)
            yl[3] = y & 0xff
            yh[3] = y >> 8
            self._pincs(0)
            self._spi.write(xl)  # Fast register write
            self._pincs(1)  # min th = 90ns
            self._pincs(0)
            self._spi.write(xh)
            self._pincs(1)
            self._pincs(0)
            self._spi.write(yl)
            self._pincs(1)
            self._pincs(0)
            self._spi.write(yh)
            self._pincs(1)
            self._pincs(0)
            self._spi.write(dest[: 3 + 2*cols])
            self._pincs(1)
            y += 1
            offs += gbytes


    # Save a region of the framebuf into a supplied memoryview. Data is saved
    # as 16-bit RGB565 values.
    # Reading a region is not guaranteed to work: the RA8875 does not behave
    # consistently. Accordingly in the GUI I removed the need for it except in
    # the case of the Meter class.
    def save_region(self, mv, x1, y1, x2, y2):
        self._setxy(x1, y1, False)  # Set up device for a read
        self._pincs(0)
        self._spi.write(b'\x80\x02')  # RA8875_CMDWRITE, MRWC
        self._pincs(1)
        self._pincs(0)
        self._spi.read(1, 0x40)  # HACK Discarding an initial read seems to help
        self._spi.read(1, 0x40)
        self._spi.read(1, 0x40)
        self._pincs(1)
        offs = 0
        for y in range(y1, y2 + 1):  # x and y ranges are inclusive
            for x in range(x1, x2 + 1):
                self._setxy(x, y, False)  # Set up device for a read
                self._pincs(0)
                self._spi.write(b'\x80\x02')  # RA8875_CMDWRITE, MRWC
                self._pincs(1)
                self._pincs(0)
                self._spi.read(1, 0x40)  # RA8875_DATAREAD Discard 1st byte
                self._spi.readinto(mv[offs : offs + 2])
                offs += 2
                self._pincs(1)

    def restore_region(self, mv, x1, y1, x2, y2):  # OK
        bpr = 2 * (x2 - x1 + 1)  # Bytes per row (2 bytes/pixel)
        rows = y2 - y1 + 1
        offs = 0
        for row in range(rows):
            self._setxy(x1, y1, True)
            self._pincs(0)
            self._spi.write(b'\x80\x02')  # RA8875_CMDWRITE, MRWC 
            self._pincs(1)
            self._pincs(0)
            self._spi.write(b'\x00')  # RA8875_DATAWRITE
            self._spi.write(mv[offs : offs + bpr])
            self._pincs(1)
            offs += bpr
            y1 += 1

    # **** TOUCH PANEL ****

    # Is fresh touch data available?
    def ready(self):
        if self._touch_data is None:
            return False  # Data not yet ready
        return self._read_reg(0xf1) & 0x04  # Check interrupt

    # Is screen currently being touched?
    # Reading MSB of reg 0x74 doesn't work, nor does reading status register.
    # The only way seems to be to check the interrupt, which relies on there
    # being a coro which issues .get_touch to clear down the interrupt.
    def touched(self):
        return self._read_reg(0xf1) & 0x04  # This is how Adafruit do it.

    # Caller tests for .ready() before calling.
    def get_touch(self):  # Read data and invalidate ready
        self._write_reg(0xf1, 0x04)  # Clear interrupt
        d = self._touch_data
        self._touch_data = None
        return d

    # Given raw touch values return calibrated values guaranteed to lie
    # within screen coordinates
    def _tdata(self, x, y):
        x = int(max(min((x - self._xmin) * self._xcal, self._width -1), 0))
        y = int(max(min((y - self._ymin) * self._ycal, self._height - 1), 0))
        return x, y

    # Task monitors touch panel and stores data
    async def _dotouch(self):
        self._write_reg(0xf1, 0x04)  # Clear TP interrupt
        # Enable touch panel. 4096 clocks for data ready. ADC clock is sysclock /16 for
        # 800x480 display, otherwise sysclock/4. Copied from Adafruit ra8875.py
        adcclock = 4 if (self._width == 800 and self._height == 480) else 2
        self._write_reg(0x70, 0xb0 | adcclock)
        self._write_reg(0x71, 0x04)  # Auto mode, debounce on
        self._write_reg(0xf0, 0x04)  # Enable TP interrupt
        while True:
            lb = self._read_reg(0xf1)
            if lb & 0x04:  # Touched
                lx = lb & 3  # Get LS 2 bits of x and y
                ly = (lb & 0x0c) >> 2
                # Combine MSB and LS 2 bits
                # Convert to screen coords
                x = ((self._read_reg(0x72) << 2) | lx) * self._width >> 10
                y = ((self._read_reg(0x73) << 2) | ly) * self._height >> 10
                if self._calibrated:
                    self._touch_data = self._tdata(x, y)
                else:  # Return raw data which can go out of range so user can calibrate
                    self._touch_data = x, y
            await asyncio.sleep_ms(30)
