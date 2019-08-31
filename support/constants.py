# constants.py Micropython GUI library for TFT displays: useful constants
# constants.py Constants for TFT GUI library

# Released under the MIT License (MIT). See LICENSE.
# Copyright (c) 2019 Peter Hinch

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
# System defaults
DEFAULT_FONT = IFont(0)
SYS_BGCOLOR = (0, 0, 0)
SYS_FGCOLOR = (255, 255, 255)

