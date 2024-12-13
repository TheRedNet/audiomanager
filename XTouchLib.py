import mido
from enum import Enum
import numpy as np

class XTouchColor(Enum):
    OFF = 0
    RED = 1
    GREEN = 2
    YELLOW = 3
    BLUE = 4
    MAGENTA = 5
    CYAN = 6
    WHITE = 7

class XTouchEncoderRing(Enum):
    DOT = 0
    PAN = 1
    WRAP = 2
    SPREAD = 3




class XTouch:
    __fader_db = [-70, -30, -10, 0, 10]
    __fader_pos = [-8192, -4464, 0, 4384, 8188]
    __sysex_prefix = [0xF0, 0x00, 0x00, 0x66, 0x15]
    __sysex_suffix = [0xF7]
    __sysex_color_command = [0x72]
    __sysex_display_command = [0x12]
    __max_pitchbend = 8188
    __min_pitchbend = -8192
    
    def __init__(self, fader_callback=None, encoder_callback=None, button_callback=None, touch_callback=None):
        try:
            input_name, output_name = self.__get_device_name()
        except OSError as e:
            raise e
        self.input = mido.open_input(input_name, callback=self.__midi_callback)
        self.output = mido.open_output(output_name)
        
        self.__display_colors = [0] * 8
        
        self.__fader_callback = fader_callback
        self.__encoder_callback = encoder_callback
        self.__button_callback = button_callback
        self.__touch_callback = touch_callback
        
        self.output.send(self.__display_hello_msg())

    def __del__(self):
        if self.input is not None:
            self.input.close()
        if self.output is not None:
            self.output.close()
    
    def __get_device_name(self):
        try:
            input_name = [name for name in mido.get_input_names() if "X-Touch-Ext" in name][0]
        except IndexError:
            raise OSError("No X-Touch-Ext input found")
        try:
            output_name = [name for name in mido.get_output_names() if "X-Touch-Ext" in name][0]
        except IndexError:
            raise OSError("No X-Touch-Ext output found")
        return input_name, output_name

    def __display_msg(self, dpstring, offset):
        prefix = self.__sysex_prefix + self.__sysex_display_command + [offset]
        suffix = self.__sysex_suffix
        dpbytes = [ord(c) for c in dpstring]
        msgbytearray = prefix + dpbytes + suffix
        return mido.Message.from_bytes(msgbytearray)

    def __display_color_msg(self):
        prefix = self.__sysex_prefix + self.__sysex_color_command
        suffix = self.__sysex_suffix
        color_bytes = [color for color in self.__display_colors]
        msgbytearray = prefix + color_bytes + suffix
        return mido.Message.from_bytes(msgbytearray)

    def __display_hello_msg(self):
        mackie_string = [ord(" ")] * 7 * 16
        msgbytearray = self.__sysex_prefix + self.__sysex_display_command + [0x00] + mackie_string + self.__sysex_suffix
        return mido.Message.from_bytes(msgbytearray)

    def display(self, text, channel, row):
        if 0 >= channel >= 7:
            raise IndexError("Channel must be between 0 and 7")
        if 0 >= row >= 1:
            raise IndexError("Row must be between 0 and 1")
        offset = channel * 7 + row*8*7
        self.output.send(self.__display_msg(text, offset))

    def display_color(self, color, channel):
        if 0 >= channel >= 7:
            raise IndexError("Channel must be between 0 and 7")
        if isinstance(color, XTouchColor):
            color = color.value
        else:
            if 0 >= color >= 7:
                raise ValueError("Color must be between 0 and 7 or an instance of XTouchColor")
        self.__display_colors[channel] = color
        self.output.send(self.__display_color_msg())
        
    def set_fader(self, channel, db=None, pos=None):
        if 0 >= channel >= 7:
            raise IndexError("Channel must be between 0 and 7")
        value=0
        if db is not None:
            if db < self.__fader_db[0] or db > self.__fader_db[-1]:
                raise ValueError(f"db value must be between {self.__fader_db} and {self.__fader_db[-1]}")
            value = np.interp(db, self.__fader_db, self.__fader_pos)
        elif pos is not None:
            if pos < self.__min_pitchbend or pos > self.__max_pitchbend:
                raise ValueError(f"pos value must be between {self.__min_pitchbend} and {self.__max_pitchbend}")
            value = pos

        self.output.send(mido.Message("pitchwheel", channel=channel, pitch=value))
    
    def __midi_callback(self, msg):
        if msg.type == "pitchwheel":
            if self.__fader_callback is not None:
                self.__fader_callback(msg.channel, np.interp(msg.pitch, self.__fader_pos, self.__fader_db), msg.pitch)
        elif msg.type == "control_change":
            if self.__encoder_callback is not None:
                ticks = msg.value % 64
                if msg.control > 64:
                    ticks = -ticks
                self.__encoder_callback(msg.control-16, ticks)
        elif msg.type == "note_on":
            if 0 <= msg.note <= 31:
                if msg.velocity == 127:
                    if self.__button_callback is not None:
                        self.__button_callback(msg.note, True)
                else:
                    if self.__button_callback is not None:
                        self.__button_callback(msg.note, False)
            elif 104 <= msg.note <= 111:
                if msg.velocity == 127:
                    if self.__touch_callback is not None:
                        self.__touch_callback(msg.note-104, True)
                else:
                    if self.__touch_callback is not None:
                        self.__touch_callback(msg.note-104, False)
        else:
            print(msg)
            
        def button_led(self, button, state, blink=False):
            if 0 >= button >= 31:
                raise IndexError("Button must be between 0 and 31")
            velocity = 0
            if state:
                velocity = 127
            if blink and state:
                velocity = 1
            self.output.send(mido.Message("note_on", note=button, velocity=color))
        
        def encoder_ring(self, encoder, value, mode = XTouchEncoderRing.DOT, light = False):
            if 0 >= encoder >= 7:
                raise IndexError("Encoder must be between 0 and 7")
            if isinstance(mode, XTouchEncoderRing):
                mode = mode.value
            else:
                if 0 >= mode >= 3:
                    raise ValueError("Mode must be between 0 and 3 or an instance of XTouchEncoderRing")
            if 0 >= value >= 15:
                raise ValueError("Value must be between 0 and 15")
            if light:
                mode += 4
            self.output.send(mido.Message("control_change", control=encoder+48, value=mode*16+value))
            
        def level_meter(self, channel, level):
            if 0 >= channel >= 7:
                raise IndexError("Channel must be between 0 and 7")
            if 0 >= level >= 13:
                raise ValueError("Level must be between 0 and 13")
                
            self.output.send(mido.Message("aftertouch", value=level+16*channel))
        
    
    
    
