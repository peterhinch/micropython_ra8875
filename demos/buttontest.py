# buttontest.py Test/demo of pushbutton classes for Pyboard RA8875 GUI

# Released under the MIT License (MIT). See LICENSE.
# Copyright (c) 2019 Peter Hinch

from micropython_ra8875.py.ugui import Screen
from micropython_ra8875.py.colors import *

from micropython_ra8875.widgets.buttons import Button, ButtonList, RadioButtons
from micropython_ra8875.widgets.checkbox import Checkbox
from micropython_ra8875.widgets.label import Label
from micropython_ra8875.widgets.pad import Pad

from micropython_ra8875.fonts import font10, font14
from micropython_ra8875.driver.tft_local import setup

class ButtonScreen(Screen):
    def __init__(self):
        super().__init__()
# These tables contain args that differ between members of a set of related buttons
        table = [
            {'fgcolor' : GREEN, 'text' : 'Yes', 'args' : ('Oui', 2), 'fontcolor' : (0, 0, 0)},
            {'fgcolor' : RED, 'text' : 'No', 'args' : ('Non', 2)},
            {'fgcolor' : BLUE, 'text' : '???', 'args' : ('Que?', 2)},  # 'fill': False to see effect
            {'fgcolor' : GREY, 'text' : 'Rats', 'args' : ('Rats', 2)},
        ]
# Highlight buttons: only tabulate data that varies
        table_highlight = [
            {'text' : 'P', 'args' : ('p', 2)},
            {'text' : 'Q', 'args' : ('q', 2)},
            {'text' : 'R', 'args' : ('r', 2)},
            {'text' : 'S', 'args' : ('s', 2)},
        ]
# A Buttonset with two entries
        table_buttonset = [
            {'fgcolor' : GREEN, 'shape' : CLIPPED_RECT, 'text' : 'Start', 'args' : ('Live', 2)},
            {'fgcolor' : RED, 'shape' : CLIPPED_RECT, 'text' : 'Stop', 'args' : ('Die', 2)},
        ]

        table_radiobuttons = [
            {'text' : '1', 'args' : ('1', 3)},
            {'text' : '2', 'args' : ('2', 3)},
            {'text' : '3', 'args' : ('3', 3)},
            {'text' : '4', 'args' : ('4', 3)},
        ]

        labels = { 'width' : 70,
                'fontcolor' : WHITE,
                'border' : 2,
                'fgcolor' : RED,
                'bgcolor' : (0, 40, 0),
                'font' : font14,
                }

# Uncomment this line to see 'skeleton' style greying-out:
#        Screen.tft.grey_color()

# Labels
        self.lstlbl = []
        for n in range(5):
            self.lstlbl.append(Label((390, 40 * n), **labels))

        self.lst_en_dis = []  # Controls affected by disable button.
# Button assortment
        x = 0
        for t in table:
            self.lst_en_dis.append(Button((x, 0), font = font14, shape = CIRCLE,
                                          callback = self.callback, **t))
            x += 70

# Highlighting buttons
        x = 0
        for t in table_highlight:
            self.lst_en_dis.append(Button((x, 60), fgcolor = CYAN, shape = CIRCLE, fontcolor = BLACK,
                   litcolor = WHITE, font = font14, callback = self.callback, **t))
            x += 70
# Pad
        lbl_pad = Label((0, 200), value = 'touch me', fontcolor = WHITE, border = 2,
                        fgcolor = RED, bgcolor = DARKGREEN, font = font14)
        pad = Pad((0, 200), width = lbl_pad.width, height = lbl_pad.height, onrelease = False,
                  callback = lambda _: lbl_pad.value('Short'),
                  lp_callback = lambda _: lbl_pad.value('Long'))
        self.lst_en_dis.append(pad)

# Start/Stop toggle
        self.bs = ButtonList(self.callback)
        self.bs0 = None
        for t in table_buttonset: # Buttons overlay each other at same location
            button = self.bs.add_button((0, 240), font = font14, fontcolor = BLACK, height = 30, **t)
            if self.bs0 is None: # Save for reset button callback
                self.bs0 = button
        self.lst_en_dis.append(self.bs)

# Radio buttons
        x = 0
        self.rb = RadioButtons(BLUE, self.callback) # color of selected button
        self.rb0 = None
        for t in table_radiobuttons:
            button = self.rb.add_button((x, 140), font = font14, fontcolor = WHITE,
                                fgcolor = (0, 0, 90), height = 40, width = 40, **t)
            if self.rb0 is None: # Save for reset button callback
                self.rb0 = button
            x += 60
        self.lst_en_dis.append(self.rb)
# Checkbox
        self.cb1 = Checkbox((340, 0), callback = self.cbcb, args = (0,))
        self.cb2 = Checkbox((340, 40), fillcolor = RED, callback = self.cbcb, args = (1,))
        self.lst_en_dis.extend([self.cb1, self.cb2])
# Reset button
        self.lbl_reset = Label((200, 210), font = font10, value = 'Reset also responds to long press')
        self.btn_reset = Button((300, 240), font = font14, height = 30, width = 80,
                                fgcolor = BLUE, shape = RECTANGLE, text = 'Reset', fill = True,
                                callback = self.cbreset, args = (4,), onrelease = False,
                                lp_callback = self.callback, lp_args = ('long', 4))
# Quit
        self.btn_quit = Button((390, 240), font = font14, height = 30, width = 80,
                               fgcolor = RED, shape = RECTANGLE, text = 'Quit',
                               callback = self.quit)
# Enable/Disable toggle 
        self.bs_en = ButtonList(self.cb_en_dis)
        self.bs_en.add_button((200, 240), font = font14, fontcolor = BLACK, height = 30, width = 90,
                              fgcolor = GREEN, shape = RECTANGLE, text = 'Disable', args = (True,))
        self.bs_en.add_button((200, 240), font = font14, fontcolor = BLACK, height = 30, width = 90,
                              fgcolor = RED, shape = RECTANGLE, text = 'Enable', args = (False,))

    def callback(self, button, arg, idx_label):
        self.lstlbl[idx_label].value(arg)

    def quit(self, button):
        Screen.shutdown()

    def cbcb(self, checkbox, idx_label):
        if checkbox.value():
            self.lstlbl[idx_label].value('True')
        else:
            self.lstlbl[idx_label].value('False')

    def cbreset(self, button, idx_label):
        self.cb1.value(False)
        self.cb2.value(False)
        self.bs.value(self.bs0)
        self.rb.value(self.rb0)
        self.lstlbl[idx_label].value('Short')

    def cb_en_dis(self, button, disable):
        for item in self.lst_en_dis:
            item.greyed_out(disable)

def test():
    print('Testing TFT...')
    setup()
    Screen.change(ButtonScreen)

test()
