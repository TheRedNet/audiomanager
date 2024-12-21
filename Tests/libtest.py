import Tests.XTouchLibOld as XTouchLibOld
from Tests.XTouchLibOld import XTouchColor as XTColor
from Tests.XTouchLibOld import XTouchButton as XTButton
from Tests.XTouchLibOld import XTouchEncoderRing as XTEncoder
import time
import logging
import numpy as np

logging.basicConfig(level=logging.DEBUG)

xt = XTouchLibOld.XTouch

fader_db = [-70, -30, -10, 0, 8]
fader_posl = [-8192, -4464, 0, 4384, 8188]
fader_pos = 0
time_start = time.time()

def fader_callback(channel, db, pos):
    print(f"Channel {channel} Fader: {db:.1f}dB Position: {pos:.1f}")
    xt.set_display(f"{db:.1f}dB", channel, 0)
    xt.set_display(f"{pos:.1f}", channel, 1)
    xt.set_fader(channel, pos=pos)

def encoder_callback(channel, ticks):
    global fader_pos
    if channel == 6:
        ticks = ticks * 10
    elif channel == 7:
        ticks = ticks * 100
    print(f"Channel {channel} Encoder: {ticks}")
    if fader_pos + ticks > 8188:
        fader_pos = 8188
    elif fader_pos + ticks < -8192:
        fader_pos = -8192
    else:
        fader_pos += ticks
    for i in range(8):
        xt.set_display(f"{fader_pos:.1f}", i, 1)
        xt.set_fader(i, pos=fader_pos)
        xt.set_display(f"{np.interp(fader_pos,  fader_posl, fader_db):.1f}", channel, 0)

def encoder_press_callback(channel, value):
    print(f"Channel {channel} Encoder Press: {value}")
    if value:
        global fader_pos
        if fader_pos < 0:
            for i in range(8):
                xt.set_fader(i, pos=8000)
        else:
            for i in range(8):
                xt.set_fader(i, pos=-8000)
    else:
        for i in range(8):
            xt.set_fader(i, pos=fader_pos)
    
def button_callback(channel, button, value):
    #light up level meter
    global time_start
    if value:
        time_start = time.time()
        xt.set_button_led(channel,button, True, True)
        level = int((channel + 7)*(1))
        xt.set_level_meter(channel, level)
        print(f"Level Meter: {level}")
    else:
        print(f"Time: {time.time()-time_start}")
        xt.set_button_led(channel,button, False)
    print(f"Channel {channel} Button: {value}")

xt = XTouchLibOld.XTouch(fader_callback=fader_callback, encoder_callback=encoder_callback, encoder_press_callback=encoder_press_callback, button_callback=button_callback)



# This will display "Hello World" on the first row of the first channel
for i in range(8):
    xt.set_display("Hello", i, 0)
    xt.set_display("World", i, 1)

# This will display the colors of the first 8 channels
for i in range(8):
    xt.set_display_color(i, i)


while True:
    xt.set_level_meter(7, 13)
    time.sleep(0.14)
    pass
