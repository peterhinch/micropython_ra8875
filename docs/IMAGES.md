# Sample Images

These are based on the 4.3 inch display. Color rendition in these images is not
particularly good: in practice colors are clear and vibrant.

###### [GUI docs](./GUI.md)

# Puhbuttons

![Buttons](./buttons.JPG)

# Vertical sliders

![Vertical sliders](./vert_sliders2.JPG)

# Horizontal sliders

![Horizontal sliders](./horiz_slider.JPG)

Widget colors can change dynamically.

![Horizontal sliders](./horiz_slider_2.JPG)

# Rotary controls, dropdown lists and listboxes

![Dials](./dials.JPG)

# Text boxes: word wrap and tab stops

![Wrap](./textbox_wrap.JPG)

![Tabs](./textbox_tab.JPG)

These support scrolling programmatically or via touch.

# Vector display

![Vectors](./vector.JPG)

Vectors (as a `complex`) may be shown in "compass" or "clock" styles. Length
and angle change as the vector alters. The color of any vector can be changed
dynamically in uer code.

# Scale

![Scale](./scale.JPG)

The `Scale` control can accurately display variables having a wide range of
values. The scale moves within a window so that the current value aligns with
the fixed pointer. The scale color can change dynamically (in the lower
instance).

# Modal Dialog Box

![Dialog box](./dialog.JPG)

# Plot Module

These images were a proof-of-concept of using the Pyboard to generate a sine
wave and using the ADC's to read the response of the network under test.

## Control Panel

![Control](./nan.JPG)

## Bode Plot (Cartesian graph)

![Bode](./bode.JPG)

## Nyquist Plot (Polar graph)

![Nyquist](./nyquist.JPG)

The above plots were from a proof of concept for my
[electrical network analyser](https://forum.micropython.org/viewtopic.php?f=5&t=4159).
Plotting these graphs used a lash-up with the network (a two pole passive
filter) wired between a DAC output and an ADC input. The real instrument
benefits from a variable gain amplifier for much improved dynamic range. The
ADC `read_timed_multi` method now enables gain and phase to be measured much
more accurately and at higher signal frequencies.
