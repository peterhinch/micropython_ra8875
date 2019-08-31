# dialog.py Extension to ugui providing the DialogBox class

# Released under the MIT License (MIT). See LICENSE.
# Copyright (c) 2019 Peter Hinch

from micropython_ra8875.ugui import Aperture, Screen
from micropython_ra8875.driver.tft import TFT
from micropython_ra8875.support.constants import *
from micropython_ra8875.widgets.label import Label
from micropython_ra8875.widgets.buttons import Button

class DialogBox(Aperture):
    def __init__(self, font, *, elements, location=(20, 20), label=None,
                 bgcolor=DARKGREEN, buttonwidth=25, closebutton=True):
        height = 150
        spacing = 20
        buttonwidth = max(max([TFT.get_stringsize(x[0], font)[0] for x in elements]) + 4, buttonwidth)
        buttonheight = max(TFT.get_stringsize('x', font)[1], 25)
        nelements = len(elements)
        width = spacing + (buttonwidth + spacing) * nelements
        if label is not None:
            width = max(width, TFT.get_stringsize(label, font)[0] + 2 * spacing)
        super().__init__(location, height, width, bgcolor = bgcolor)
        x = self.location[0] + spacing # Coordinates relative to physical display
        gap = 0
        if nelements > 1:
            gap = ((width - 2 * spacing) - nelements * buttonwidth) // (nelements - 1)
        y = self.location[1] + self.height - buttonheight - 10
        if label is not None:
            Label((x, self.location[1] + 50), font = font, bgcolor = bgcolor, value = label)
        for text, color in elements:
            Button((x, y), height = buttonheight, width = buttonwidth, font = font, fontcolor = BLACK, fgcolor = color,
                text = text, shape = RECTANGLE,
                callback = self.back, args = (text,))
            x += buttonwidth + gap
        if closebutton:
            x, y = TFT.get_stringsize('X', font)
            size = max(x, y, 25)
            Button((self.location[0] + width - (size + 1), self.location[1] + 1), height = size, width = size, font = font,
                fgcolor = RED,  text = 'X', shape = RECTANGLE,
                callback = self.back, args = ('Close',))

    def back(self, button, text):
        Aperture.value(text)
        Screen.back()
