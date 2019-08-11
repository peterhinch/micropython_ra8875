# Sample Images

These are based on the 4.3 inch display.

# Puhbuttons

![Buttons](./buttons.JPG)

# Vertical sliders

![Vertical sliders](./vert_sliders2.JPG)

# Horizontal sliders

![Horizontal sliders](./horiz_slider.JPG)

# Rotary controls and displays

![Dials](./dials.JPG)

# Modal Dialog Box

![Dialog box](./dialog.JPG)

# Plot Module

These images are of a proof-of-concept of using the Pyboard to generate a sine
wave and using the ADC's to read the response of the network under test.

## Control Panel

![Control](./nan.JPG)

## Bode Plot (Cartesian graph)

![Bode](./bode.JPG)

## Nyquist Plot (Polar graph)

![Nyquist](./nyquist.JPG)

To anyone interested in this project this was a lash-up with the network (a two
pole passive filter) wired between a DAC output and an ADC input. A serious
solution would require I/O electronics which I have designed but not implemented
to date. The dynamic range could be substantially improved: 60dB was my target.
As it stands the phase measurements are dubious when the amplitude is more than
40dB down. An auto-ranging amplifier is required.

Note to any MicroPython developers. Would that the firmware supported concurrent
synchronous reading of two ADC's. This would enable phase to be read from an
arbitrary pair of incoming signals. Phase measurements were only possible
because the signal is of a known frequency, constant for the duration of each
reading.
