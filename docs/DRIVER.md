# RA8875 device driver

This driver provides MicroPython access to a subset of the capabilities of the
RA8875 chip. The subset was chosen to be close to the minimum functionality
required to support the touch GUI display. The `ra8875.py` driver provides an
`RA8875` class.

The GUI subclasses `RA8875` to provide a `TFT` class. This handles 'greying
out' of disabled widgets by modifying the colors passed to the superclass
methods.

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
 rendering when the greyed- out status is set.
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
 12. `draw_line` Args `x1, y1, x2, y2, color` Draw a line from (x1, y1) to
 (x2, y2).
 13. `text_style` Arg `style=None`. If `None` is passed, return the current
 text style. See below for definition of text style.
 14. `print_string` Args `s, x, y` Print string `s` at location `x, y` in the
 current style. This method is rudimentary and does not handle control chars or
 newlines.

## 1.1 Text style

This is a `(fgcolor, bgcolor, font)` tuple where `fgcolor` and `bgcolor` are
foreground and background colors as `(r, g, b` tuples. `font` is the name of an
imported Python font.

# 2. The RA8875 class

Colors are specified as (r, g, b) tuples. They are converted to 16 bit RGB565
values by the RA8875 `to_rgb565` static method.

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
method which handles the touch panel. If `None` is passed this will not be run,
so the touch panel will be inoperative.

Display methods required for GUI:  
 1. `clr_scr` Clear screen (all pixels off).
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
 10. `draw_line` Args `x1, y1, x2, y2, color` Draw a line from (x1, y1) to
 (x2, y2).
 11. `save_region` Args `mv, x1, y1, x2, y2` Copy pixels from the defined
 region in the RA8875 frame buffer into a user supplied buffer. `mv` is a
 memoryview into a bytearray which must have sufficient capacity to hold 2
 bytes per pixel. See note below.
 12. `restore_region` Args `mv, x1, y1, x2, y2`. Draw the contents of the user
 supplied buffer at a region defined by the supplied coordinates. These may
 differ from those used for the save, but the aspect ratio must be unchanged.
 13. `draw_glyph` Args `mv, x, y, rows, cols, fgcolor, bgcolor` The `mv` arg is
 a `memoryview` into a `bytes` object holding a glyph bitmap. This is a one bit
 horizontally mapped array. It is rendered at `x, y` and the glyph is organised
 as `rows, cols`. Rendering uses the supplied foreground and background colors.

Touchpanel (TP) methods required by GUI:  
 1. `ready` No args. Returns `True` if TP data is available.
 2. `touched` No args. Returns `True` if TP is currently being touched.
 3. `get_touch` No args. Return touch panel data `x, y` as screen coordinates.
 Caller should check `ready` before calling. The returned coordinates will be
 raw values unless `calibrate` has been called, when they will be adjusted.

Additional methods:  
 1. `calibrate` Args `xmin, ymin, xmax, ymax` Apply user-specified calibration
 values to future touchpanel readings. User-modified code in `tft_local.py`
 suppies the reported raw values for the top leftmost and bottom rightmost
 pixels.
 2. `width` No args. Return display width in pixels.
 3. `height` No args. Return display height in pixels.
 4. `draw_pixel` Args `x, y, color` draw a single pixel.
 5. `get_pixel` Args `x, y` Return the RGB565 value of a pixel.

Note that the `save_region` method is not guaranteed to work reliably: in my
testing the chip does not return deterministic data. It seems to work well
enough for the `Meter` control, but the `Slider` controls did not work well
and have been rewritten to avoid using this feature.
