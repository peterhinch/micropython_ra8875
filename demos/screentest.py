# screentest.py Test/demo of multiple screens for Pybboard RA8875 GUI

# Released under the MIT License (MIT). See LICENSE.
# Copyright (c) 2019-2020 Peter Hinch

# Updated for uasyncio V3

import uasyncio as asyncio
from math import pi

from micropython_ra8875.py.ugui import Screen
from micropython_ra8875.py.colors import *

from micropython_ra8875.widgets.knob import Knob
from micropython_ra8875.widgets.checkbox import Checkbox
from micropython_ra8875.widgets.led import LED
from micropython_ra8875.widgets.meter import Meter
from micropython_ra8875.widgets.dial import Dial
from micropython_ra8875.widgets.sliders import Slider

from micropython_ra8875.widgets.label import Label
from micropython_ra8875.widgets.buttons import Button, ButtonList, RadioButtons

from micropython_ra8875.fonts import font10, font14
from micropython_ra8875.driver.tft_local import setup

def to_string(val):
    return '{:3.1f}ohms'.format(val * 10)

# STANDARD BUTTONS

def quitbutton(x, y):
    def quit(button):
        Screen.shutdown()
    Button((x, y), height = 30, font = font14, callback = quit, fgcolor = RED,
           text = 'Quit', shape = RECTANGLE, width = 80)

def fwdbutton(x, y, cls_screen, text='Next'):
    def fwd(button):
        Screen.change(cls_screen)
    Button((x, y), height = 30, font = font14, callback = fwd, fgcolor = RED,
           text = text, shape = RECTANGLE, width = 80)

def backbutton(x, y):
    def back(button):
        Screen.back()
    Button((x, y), height = 30, font = font14, fontcolor = BLACK, callback = back,
           fgcolor = CYAN,  text = 'Back', shape = RECTANGLE, width = 80)

# SCREEN CREATION

# Demo of on_open and on_hide methods
class BackScreen(Screen):
    def __init__(self):
        super().__init__()
        Label((0, 0), font = font14, value = 'Ensure back refreshes properly')
        backbutton(390, 242)
        self.open_arg = 'Opening'
        self.hide_arg = 'Hiding'

    def on_open(self):
        print(self.open_arg)

    def on_hide(self):
        print(self.hide_arg)

class TaskScreen(Screen):
    def __init__(self):
        super().__init__()
        self.tasks = []  # Control cancellation explicitly
        Label((0, 0), font = font14, value = 'Green dial runs only')
        Label((0, 30), font = font14, value = 'when screen is visible')
        Label((0, 120), font = font14, value = "Yellow dial's value is")
        Label((0, 150), font = font14, value = 'computed continuously.')
        self.dial1 = Dial((350, 10), fgcolor = GREEN, border = 2, pointers = (0.9, 0.7))
        self.dial2 = Dial((350, 120), fgcolor = YELLOW, border = 2,  pointers = (0.9, 0.7))
        self.pause = False  # asyncio can't pause coros so handle at application level
        self.tasks.append(asyncio.create_task(self.maintask(self.dial1, True)))
        self.tasks.append(asyncio.create_task(self.maintask(self.dial2)))

        fwdbutton(0, 242, BackScreen)
        self.backbutton(390, 242)  # Special backbutton

    def on_open(self):
        print('Start green dial')
        self.pause = False

    def on_hide(self):
        print('Stop green dial')
        self.pause = True

    async def maintask(self, dial, can_pause=False):
        angle = 0
        await asyncio.sleep(0)
        while True:
            await asyncio.sleep_ms(200)
            if not (can_pause and self.pause):
                delta = 0.2
                angle += pi * 2 * delta / 10
                dial.value(angle)
                dial.value(angle /10, 1)

    def backbutton(self, x, y):
        def back(button):
            for task in self.tasks:
                task.cancel()
            self.tasks = []
            Screen.back()
        Button((x, y), height = 30, font = font14, fontcolor = BLACK, callback = back,
            fgcolor = CYAN,  text = 'Back', shape = RECTANGLE, width = 80)

class BaseScreen(Screen):
    def __init__(self):
        super().__init__()
        Label((0, 0), font = font14, value = 'Multiple screen demonstration.')
        fwdbutton(0, 242, KnobScreen, 'Knobs')
        fwdbutton(100, 242, SliderScreen, 'Sliders')
        fwdbutton(200, 242, AssortedScreen, 'Various')
        fwdbutton(0, 100, TaskScreen, 'Tasks')
        quitbutton(390, 242)

class KnobScreen(Screen):
    def __init__(self):
        super().__init__()
        backbutton(390, 242)
        fwdbutton(0, 242, BackScreen)
        labels = { 'width' : 70,
            'fontcolor' : WHITE,
            'border' : 2,
            'fgcolor' : RED,
            'bgcolor' : (0, 40, 0),
            }

        lstlbl = []
        for n in range(2):
            lstlbl.append(Label((120, 120 + 40 * n), font = font10, **labels))
        lbl_1 = Label((120, 120), font = font10, **labels)
        lbl_2 = Label((120, 160), font = font10, **labels)
        meter1 = Meter((320, 0), font=font10, legends=('0','5','10'), barcolor = YELLOW, fgcolor = GREEN, bgcolor=BLACK)
        dial1 = Dial((120, 0), fgcolor = YELLOW, border = 2, pointers = (0.9, 0.7))
        Knob((0, 0), fgcolor = GREEN, bgcolor=(0, 0, 80), color = (168,63,63), border = 2,
            cb_end = self.callback, cbe_args = ['Knob1'], cb_move = self.knob_moved, cbm_args = [dial1, 0, lbl_1, meter1])
        Knob((0, 120), fgcolor = WHITE, border = 2, cb_move = self.knob_moved, cbm_args = [dial1, 1, lbl_2],
            cb_end = self.callback, cbe_args = ['Knob2'], arc = pi * 1.5)

    def callback(self, knob, control_name):
        print('{} returned {}'.format(control_name, knob.value()))

    def knob_moved(self, knob, dial, pointer, label, meter=None):
        val = knob.value() # range 0..1
        dial.value(2 * (val - 0.5) * pi, pointer)
        label.value('{:3.1f}'.format(val))
        if meter is not None:
            meter.value(val)

class SliderScreen(Screen):
    def __init__(self):
        super().__init__()
# Common args for the labels
        labels = { 'width' : 75,
                'fontcolor' : WHITE,
                'border' : 2,
                'fgcolor' : RED,
                'bgcolor' : (0, 40, 0),
                }
# Common arguments for all three sliders
        table = {'fontcolor' : WHITE,
                'legends' : ('0', '5', '10'),
                }
        backbutton(390, 242)
        fwdbutton(0, 242, BackScreen)
        self.lstlbl = []
        for n in range(3):
            self.lstlbl.append(Label((80 * n, 215), font = font10, **labels))
        y = 5
        self.slave1 = Slider((80, y), font = font10,
            fgcolor = GREEN, cb_end = self.callback, cbe_args = ('Slave1',), cb_move = self.slave_moved, cbm_args = (1,), **table)
        self.slave2 = Slider((160, y), font = font10,
            fgcolor = GREEN, cb_end = self.callback, cbe_args = ('Slave2',), cb_move = self.slave_moved, cbm_args = (2,), **table)
        master = Slider((0, y), font = font10,
            fgcolor = YELLOW, cb_end = self.callback, cbe_args = ('Master',), cb_move = self.master_moved, 
            cbm_args = (0,), value=0.5, border = 2, **table)

# cb_end occurs when user stops touching the control
    def callback(self, slider, device):
        print('{} returned {}'.format(device, slider.value()))

    def master_moved(self, slider, idx_label):
        val = slider.value()
        self.slave1.value(val)
        self.slave2.value(val)
        self.lstlbl[idx_label].value(to_string(val))

# Either slave has had its slider moved (by user or by having value altered)
    def slave_moved(self, slider, idx_label):
        val = slider.value()
        self.lstlbl[idx_label].value(to_string(val))

class AssortedScreen(Screen):
    def __init__(self):
        super().__init__()
        labels = { 'width' : 70,
                'fontcolor' : WHITE,
                'border' : 2,
                'fgcolor' : RED,
                'bgcolor' : (0, 40, 0),
                'font' : font14,
                }
        radiobuttons = [
            {'text' : '1', 'args' : ['1']},
            {'text' : '2', 'args' : ['2']},
            {'text' : '3', 'args' : ['3']},
            {'text' : '4', 'args' : ['4']},
        ]
        buttonlist = [
            {'fgcolor' : GREEN, 'shape' : CLIPPED_RECT, 'text' : 'Start', 'args' : ['Live']},
            {'fgcolor' : RED, 'shape' : CLIPPED_RECT, 'text' : 'Stop', 'args' : ['Die']},
        ]

        backbutton(390, 242)
        fwdbutton(0, 242, BackScreen)
        lstlbl = []
        for n in range(4):
            lstlbl.append(Label((350, 40 * n), **labels))
        self.led = LED((440, 0), border = 2)
        Checkbox((300, 0), callback = self.cbcb, args = [lstlbl[0], False])
        Checkbox((300, 40), fillcolor = RED, callback = self.cbcb, args = [lstlbl[1], True])

# On/Off toggle
        x = 1
        bs = ButtonList(self.callback)
        bs0 = None
        for t in buttonlist: # Buttons overlay each other at same location
            t['args'].append(lstlbl[2])
            button = bs.add_button((x, 120), font = font14, height=30, fontcolor = BLACK, **t)
            if bs0 is None:
                bs0 = button
# Radio buttons
        x = 1
        rb = RadioButtons(BLUE, self.callback) # color of selected button
        for t in radiobuttons:
            t['args'].append(lstlbl[3])
            button = rb.add_button((x, 180), font = font14, fontcolor = WHITE,
                                fgcolor = (0, 0, 90), height = 40, width = 40, **t)
            x += 60

    def callback(self, button, arg, label): # Callback for radio button
        label.value(arg)

    def cbcb(self, checkbox, label, test): # Callback for checkbox
        if test:
            self.led.value(checkbox.value())
        else:
            color = RED if checkbox.value() else YELLOW
            self.led.color(color)
        if checkbox.value():
            label.value('True')
        else:
            label.value('False')

def test():
    print('Test TFT panel...')
    setup()
    Screen.change(BaseScreen)                                          # Run it!

test()
