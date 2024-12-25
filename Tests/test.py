import mido
import time
import math
from threading import Thread, Lock

print(mido.get_input_names())

# get the input which contains "X-Touch-Ext"
try:
    input_name = [name for name in mido.get_input_names() if "X-Touch-Ext" in name][0]
except IndexError:
    print("No X-Touch-Ext input found")
    exit()
print(input_name)
# get the output which contains "X-Touch-Ext"
try:
    output_name = [name for name in mido.get_output_names() if "X-Touch-Ext" in name][0]
except IndexError:
    print("No X-Touch-Ext output found")
    exit()

class MidiController:
    def __init__(self, input_name, output_name):
        self.input = mido.open_input(input_name)
        self.output = mido.open_output(output_name)
        self.animate = False
        self.iteration = 0.0
        self.sineinvertion = False
        self.sinexstretch = 0.7
        self.mutex = Lock()
        self.p = Thread(target=self.SendMidi)
        self.p.start()
        self.input.callback = self.Callback
    
    def calculate_sine(self, iteration, sineinvertion, sinexstretch, i):
        sine = int(8100 * math.sin(iteration + (i * sinexstretch)))
        if sineinvertion:
            sine = -sine
        return sine

    def SendMidi(self):
        loc_iteration = 0
        loc_animate = False
        #lcd displays
        lcd_sysx_hex_start = [0x00, 0x20, 0x32, 0x42, 0x4c]
        lcd_sysx_hex_end = []
        lcd_channel = 0x01
        lcd_cc_hex = 0b00000000
        lcd_character_string = "Hello World111"
        lcd_character_string_hex = [ord(c) for c in lcd_character_string]
        lcd_full_string_hex = lcd_sysx_hex_start + [lcd_channel] + [lcd_cc_hex] + lcd_character_string_hex + lcd_sysx_hex_end
        
        for b in lcd_full_string_hex:
            print(hex(b))
        
        # list to tuple
        data_tuple = tuple(lcd_full_string_hex)
        print(data_tuple)
        lcd_full_string = mido.Message("sysex", data=data_tuple)
        print(lcd_full_string.hex())
        self.output.send(lcd_full_string)

        while True:
            with self.mutex:
                iteration = self.iteration
                animate = self.animate
                sineinvertion = self.sineinvertion
                sinexstretch = self.sinexstretch

            if loc_animate != animate:
                if animate:
                    self.output.send(mido.Message("note_on", note=7, velocity=30))
                else:
                    self.output.send(mido.Message("note_on", note=7, velocity=0))
                loc_animate = animate
                print("sanimate: ", loc_animate)
            if not animate:
                time.sleep(1.0)
            if loc_iteration != iteration:
                if not animate:
                    pass  
                for i in range(8):
                    sine = self.calculate_sine(iteration, sineinvertion, sinexstretch, i)
                    self.output.send(mido.Message("pitchwheel", channel=i, pitch=sine))
                loc_iteration = iteration
                for i in range(8):
                    level = 12
                    channel = i
                    pressure = level + (channel * 16)     
                    self.output.send(mido.Message("aftertouch", channel=0, value=pressure))
                print("siteration: ", loc_iteration)
            
            time.sleep(0.05)

    def Callback(self, msg):
        print(msg)
        if msg.type == "note_on":
            if msg.note == 7 and msg.velocity == 127:
                with self.mutex:
                    self.animate = not self.animate
                print("mlanimate: ", self.animate)
            if msg.note == 39 and msg.velocity == 127:
                with self.mutex:
                    self.sinexstretch = 0.7
        if msg.type == "pitchwheel":
            if self.animate:
                with self.mutex:
                    self.iteration = math.asin(max(-1, min(1, msg.pitch / 8100))) - (msg.channel * self.sinexstretch)
                    print("mliteration: ", self.iteration)
        if msg.type == "control_change":
            if msg.control == 23:
                ticks = msg.value % 64
                if msg.value > 64:
                    ticks = -ticks
                with self.mutex:
                    self.sinexstretch += ticks * 0.05
                    self.sinexstretch = round(self.sinexstretch, 2)
                print("sinexstretch: ", self.sinexstretch) 

mc = MidiController(input_name, output_name)
while True:
    time.sleep(1)
    pass
