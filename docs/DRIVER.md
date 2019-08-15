# RA8875 device driver

This driver provides MicroPython access to a subset of the capabilities of the
RA8875 chip. The subset was chosen to be close to the minimum functionality
required to support the touch GUI display. The `ra8875.py` driver provides an
`RA8875` class. This is usable for applications other than the GUI and could
readily be extended to support additional primitives provided by the chip.

The GUI subclasses `RA8875` to provide a `TFT` class. This handles 'greying
out' of disabled widgets by modifying the colors passed to the superclass
methods. For convenience `TFT` is documented here.

The RA8875 documentation is not the world's best and the chip has bugs. The
driver was written by referring to a number of sources, notably the Adafruit
libraries; data values for display control registers were copied from their
code. Accordingly the use of their displays is highly recommended: other units
may not be electrically compatible with the driver. See
[references](./DRIVER.md#4-references) for details of the supported hardware
and for the sources of information used.

###### [GUI docs](./GUI.md)

# 1. The TFT class

Where `color` is specified this is an `(r, g, b)` tuple where r, g and b are in
range 0 to 255 inclusive.

Constructor. This takes the following mandatory arguments.  
 1. `spi` An initialised SPI bus instance.
 2. `pincs` An initialised `Pin` instance defined for output with initial value
 of 1. Used for chip select.
 3. `pinrst` An initialised `Pin` instance defined for output with initial value
 of 1. Used to perform a hardware reset.
 4. `width` Display width and height. Supported values are 480x272 and 800x480.
 5. `height`
 6. `loop` An event loop instance or `None`. In the latter case the touch panel
 `uasyncio` task will not be run, so the touch panel will be inoperative.

Methods.
 1. `desaturate` Arg `value=None`. If a `bool` is passed, defines whether
 greying-out is done by dimming (`False`) or desaturating (`True`) objects. By
 default the current status is returned.
 2. `dim` Arg `factor=None` If a numeric value is passed, sets the amount of
 dimming to be used if this option is selected. A typical value is 2, meaning
 that the brightness of colors is halved. Returns the current factor.
 3. `usegrey` Arg `val`. Set current greyed-out status. If `True` is passed,
 subsequent pixels will be rendered with the specified `color` modified to the
 current greyed-out style. If `False` is passed they will be rendered normally.
 Note that `desaturate` and `dim` methods set the grey style. They only affect
 rendering when the greyed- out status is set via `usegrey`.
 4. `draw_rectangle` Args `x1, y1, x2, y2, color` Draw a rectangle.
 5. `fill_rectangle` Args `x1, y1, x2, y2, color` Draw a filled rectangle.
 6. `draw_clipped_rectangle` Args `x1, y1, x2, y2, color` Draw a clipped
 rectangle.
 7. `fill_clipped_rectangle` Args `x1, y1, x2, y2, color` Draw a filled clipped
 rectangle.
 8. `draw_circle` Args `x, y, radius, color` Draw a circle.
 9. `fill_circle` Args `x, y, radius, color` Draw a filled circle.
 10. `draw_vline` Args `x, y, l, color` Draw a vertical line length `l`.
 11. `draw_hline` Args `x, y, l, color` Draw a horizontal line length `l`.
 12. `draw_line` Args `x1, y1, x2, y2, color` Draw a line from `x1, y1` to
 `x2, y2`.
 13. `text_style` Arg `style=None`. If `None` is passed, return the current
 text style. See below for definition of text style.
 14. `print_string` Args `s, x, y` Print string `s` at location `x, y` in the
 current style. This method is rudimentary and does not handle control chars or
 newlines.

### Text style

This is a `(fgcolor, bgcolor, font)` tuple where `fgcolor` and `bgcolor` are
foreground and background colors as `(r, g, b)` tuples. `font` is the name of
an imported Python font.

# 2. The RA8875 class

Colors are specified as (r, g, b) tuples. They are converted to 16 bit RGB565
values by the `RA8875.to_rgb565` static method.

Constructor. This takes the following mandatory arguments.  
 1. `spi` An initialised SPI bus instance.
 2. `pincs` An initialised `Pin` instance defined for output with initial value
 of 1. Used for chip select.
 3. `pinrst` An initialised `Pin` instance defined for output with initial value
 of 1. Used to perform a hardware reset.
 4. `width` Display width and height. Supported values are 480x272 and 800x480.
 5. `height`
 6. `loop=None` An event loop instance or `None`.

If `loop` is supplied the constructor launches a `._dotouch` asynchronous
method which handles the touch panel. If `None` is passed this will not be run:
the touch panel will be inoperative.

Display methods required for GUI:  
 1. `clr_scr` No args. Clear screen (all pixels off).
 2. `draw_rectangle` Args `x1, y1, x2, y2, color` Draw a rectangle.
 3. `fill_rectangle` Args `x1, y1, x2, y2, color` Draw a filled rectangle.
 4. `draw_clipped_rectangle` Args `x1, y1, x2, y2, color` Draw a clipped
 rectangle.
 5. `fill_clipped_rectangle` Args `x1, y1, x2, y2, color` Draw a filled clipped
 rectangle.
 6. `draw_circle` Args `x, y, radius, color` Draw a circle.
 7. `fill_circle` Args `x, y, radius, color` Draw a filled circle.
 8. `draw_vline` Args `x, y, l, color` Draw a vertical line length `l`.
 9. `draw_hline` Args `x, y, l, color` Draw a horizontal line length `l`.
 10. `draw_line` Args `x1, y1, x2, y2, color` Draw a line from `x1, y1` to
 `x2, y2`.
 11. `draw_glyph` Args `mv, x, y, rows, cols, fgcolor, bgcolor` The `mv` arg is
 a `memoryview` into a `bytes` object holding a glyph bitmap. The bitmap uses
 one bit per pixel as a horizontally mapped array. It is rendered at `x, y` and
 the glyph is organised as `rows, cols`. Rendering uses the supplied foreground
 and background colors.

Touchpanel (TP) methods required by GUI:  
 1. `ready` No args. Returns `True` if TP data is available.
 2. `touched` No args. Returns `True` if TP is currently being touched.
 3. `get_touch` No args. Return touch panel data `x, y` as screen coordinates.
 Caller should check `ready` before calling. The returned coordinates will be
 raw values unless `calibrate` has been called, when they will be adjusted.

Additional methods:  
 1. `calibrate` Args `xmin, ymin, xmax, ymax` Apply user-specified calibration
 values to future touchpanel readings. See below.
 2. `width` No args. Return display width in pixels.
 3. `height` No args. Return display height in pixels.
 4. `draw_pixel` Args `x, y, color` draw a single pixel.


### Calibration

The user runs `cal.py` to determine the reported coordinates of the top left
and bottom right of the display. The code in `tft_local.py` is modified to call
`.calibrate` with those values.

This ensures that the GUI acquires corrected coordinates from the touch panel.

# 3. Chip limitations

The RA8875 touch interface has an unexpected behaviour. A single brief touch
always appears as at least two touch events with different coordinates. The
last of these seems to be the correct one (subject to calibration). The driver
makes no attempt to mitigate this. The setting of the debounce bit had no
evident effect on this behaviour.

The RA8875 claims to provide a means of reading back the contents of the frame
buffer. This seems broken. I removed functionality which aimed to support it as
the outcome was not deterministic.

# 4. References

[CircuitPython library](https://github.com/adafruit/Adafruit_CircuitPython_RA8875)
written by Melissa LeBlanc-Williams for Adafruit Industries.
[Arduino library](https://github.com/adafruit/Adafruit_RA8875) written by
Limor Fried/Ladyada for Adafruit Industries.
[Datasheet](https://cdn-shop.adafruit.com/datasheets/RA8875_DS_V19_Eng.pdf)
[App note](https://cdn-shop.adafruit.com/datasheets/ra8875+app+note.pdf)

[This driver](https://github.com/sumotoy/RA8875/blob/0.70/RA8875.cpp) by Max Mc
Costa.

Supported hardware

[Controller board](https://www.adafruit.com/product/1590)  
[4.3 inch display](https://www.adafruit.com/product/1591)  
[7 inch display](https://www.adafruit.com/product/2354)