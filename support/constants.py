# constants.py Micropython GUI library for TFT displays: useful constants
# constants.py Constants for TFT GUI library

# The MIT License (MIT)
#
# Copyright (c) 2016 Peter Hinch
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

CIRCLE = 1
RECTANGLE = 2
CLIPPED_RECT = 3

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
GREY = (100, 100, 100)
MAGENTA = (255, 0, 255)
CYAN = (0, 255, 255)
LIGHTGREEN = (0, 80, 0)
DARKGREEN = (0, 40, 0)
LIGHTBLUE = (0, 0, 80)


# Internal font for RA8875 - subset of font_to_py methods to minimise code.
class IFont:
    def __init__(self, scale):
        scale = max(0, min(3, scale))
        self._scale = scale
        self._width = 8 * (scale + 1)
        self._height = 2 * self._width

    def scale(self):
        return self._scale

    def get_ch(self, _):
        return None, self._height, self._width

    def height(self):
        return self._height

    def hmap(self):
        return True

# Instantiate the only available sizes
IFONT16 = IFont(0)
IFONT32 = IFont(1)
IFONT48 = IFont(2)
IFONT64 = IFont(3)
