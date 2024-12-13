import XTouchLib
from XTouchLib import XTouchColor as XTColor

xt = XTouchLib.XTouch()

# This will display "Hello World" on the first row of the first channel
for i in range(8):
    xt.display("Hello", i, 0)
    xt.display("World", i, 1)

# This will display the colors of the first 8 channels
for i in range(8):
    xt.display_color(i, i)

