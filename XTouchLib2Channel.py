import mido
from enum import Enum
from typing import Callable, List
import numpy as np

class XTouchColor(Enum):
    """Enumeration for XTouch colors."""
    OFF = 0
    RED = 1
    GREEN = 2
    YELLOW = 3
    BLUE = 4
    MAGENTA = 5
    CYAN = 6
    WHITE = 7

class XTouchEncoderRing(Enum):
    """Enumeration for XTouch encoder ring modes."""
    DOT = 0
    PAN = 1
    WRAP = 2
    SPREAD = 3

class XTouchButtonLED(Enum):
    """Enumeration for XTouch button LEDs."""
    OFF = 0
    ON = 1
    BLINK = 2

class XTutils:
    fader_db = [-70, -60, -30, -10, 0, 8]
    fader_pos = [-8192, -7700, -4340, 245, 4720, 8188]
    sysex_prefix = [0x00, 0x00, 0x66, 0x15]
    sysex_color_command = [0x72]
    sysex_display_command = [0x12]
    max_pitchbend = 8188
    min_pitchbend = -8192

    def text_display_message(self, text: str, offset: int = 0):
        """Create a sysex message for displaying text on the XTouch display."""
        if offset < 0 or offset > 112:
            raise ValueError("Offset must be between 0 and 112")
        if len(text) > 112 - offset:
            raise ValueError("Text is too long")
        bytes = self.sysex_prefix + self.sysex_display_command + [offset] + [ord(c) for c in text]
        return mido.Message('sysex', data=bytes)
    
    def fader_pos_to_db(self, pos: int):
        """Convert XTouch fader position to dB value."""
        if self.min_pitchbend <= pos <= self.max_pitchbend:
            raise ValueError("Fader position out of range")
        return np.interp(pos, self.fader_pos, self.fader_db)
    
    def fader_db_to_pos(self, db: float):
        """Convert dB value to XTouch fader position."""
        if db < -70 or db > 8:
            raise ValueError("dB value out of range")
        return np.interp(db, self.fader_db, self.fader_pos)
    
    def color_message(self, colors: List[int]):
        """Create a sysex message for setting the color of a channel."""
        if len(colors) != 8:
            raise ValueError("Colors must be a list of 8 integers")
        bytes = self.sysex_prefix + self.sysex_color_command + colors
        return mido.Message('sysex', data=bytes)


class Channel:

    def __init__(self, channel: int, color_callback: Callable[[None],None], midi_out_callback: Callable[[mido.Message],None]):
        self.__channel: int = channel
        
        self.__midi_send = midi_out_callback
        self.__color_callback = color_callback
        
        # Actual state variables
        self.__display_text_list = [" "*7]*2
        self.__display_color: int = XTouchColor.WHITE.value
        self.__fader_pos: int = 0
        self.__encoder_pos: int = 0
        self.__encoder_mode: int = XTouchEncoderRing.DOT.value
        self.__encoder_led: int = 0
        self.__button_leds = [XTouchButtonLED.OFF.value]*4


    
    @property
    def channel(self):
        """The channel number of the strip."""
        return self.__channel
    
    @property
    def display_color(self):
        return self.__display_color
    
    @display_color.setter
    def display_color(self, color: XTouchColor|int):
        old_color = self.__display_color
        if isinstance(color, XTouchColor):
            self.__display_color = color.value
        elif isinstance(color, int):
            self.__display_color = color
        else:
            raise ValueError("Invalid color type")
        if old_color != self.__display_color:
            self.__color_callback()
    
    @property
    def display_text(self):
        return self.__display_text_list
    
    @display_text.setter
    def display_text(self, text_list: List[str]):
        if not isinstance(text_list, List[str]):
            raise ValueError("Text list must be a list of strings")
        if len(text_list) != 2:
            raise ValueError("Text list must be of length 2")
        i=0
        for t in text_list:
            if len(t) > 7:
                raise ValueError(f"Text cannot be longer than 7 characters line:{i} text:{t}")
            if any(ord(c) > 127 for c in t):
                raise ValueError(f"Text must be ASCII line:{i} text:{t}")
            if t != self.__display_text_list[i]:
                self.__display_text_list[i] = t
                self.__midi_send(XTutils.text_display_message(t, ( self.__channel*7 + i*7*8 )))
            i+=1
    
    @property
    def fader(self):
        return self.__fader_pos
    
    @fader.setter
    def fader(self, pos: int):
        if not isinstance(pos, int):
            raise ValueError("Fader position must be an integer")
        if pos < -8192 or pos > 8188:
            raise ValueError("Fader position out of range")
        if pos != self.__fader_pos:
            self.__fader_pos = pos
            self.__midi_send(mido.Message('pitchwheel', channel=self.__channel, pitch=pos))
    
    @property
    def fader_db(self):
        return XTutils.fader_pos_to_db(self.__fader_pos)
    
    @fader_db.setter
    def fader_db(self, db: float):
        if not isinstance(db, float):
            raise ValueError("Fader dB value must be a float")
        pos = XTutils.fader_db_to_pos(db)
        self.fader = int(pos)
        
    def __button_setter_factory(self, button: int):
        def button_setter(state: XTouchButtonLED|int|bool):
            if isinstance(state, XTouchButtonLED):
                state = state.value
            elif isinstance(state, bool):
                state = int(state)
            elif not (0 <= state <= 2):
                raise ValueError("State must be between 0 and 2 or an instance of XTouchButtonLED or bool")
            
            if state != self.__button_leds[button]:
                # nice one liner to set the button led velocity
                # if state is 0 velocity is 0, if state is 1 velocity is 127, if state is 2 velocity is 1 (for blinking)
                velocity = 1 if state == 2 else state*127
                int_button = button * 8 + self.__channel
                self.__button_leds[button] = state
                self.__midi_send(mido.Message('control_change', channel=self.__channel, control=int_button, value=velocity))
        return button_setter
    
    def __button_getter_factory(self, button: int):
        def button_getter():
            return self.__button_leds[button]
        return button_getter
    
    rec_button = property(__button_getter_factory(0), __button_setter_factory(0), None, "The record button state")
    solo_button = property(__button_getter_factory(1), __button_setter_factory(1), None, "The solo button state")
    mute_button = property(__button_getter_factory(2), __button_setter_factory(2), None, "The mute button state")
    select_button = property(__button_getter_factory(3), __button_setter_factory(3), None, "The select button state")
    
    
    def __update_encoder(self):
        self.__midi_send(mido.Message('control_change', control=self.__channel + 48, value=self.__encoder_pos + self.__encoder_mode*16 + self.__encoder_led*64))
    
    @property
    def encoder_mode(self):
        return self.__encoder_mode
    
    @encoder_mode.setter
    def encoder_mode(self, mode: XTouchEncoderRing|int):
        if isinstance(mode, XTouchEncoderRing):
            mode = mode.value
        elif not (0 <= mode <= 3):
            raise ValueError("Encoder mode must be between 0 and 3 or an instance of XTouchEncoderRing")
        if mode != self.__encoder_mode:
            self.__encoder_mode = mode
            self.__update_encoder()
    
    @property
    def encoder_pos(self):
        return self.__encoder_pos
    
    @encoder_pos.setter
    def encoder_pos(self, pos: int):
        if not isinstance(pos, int):
            raise ValueError("Encoder position must be an integer")
        if not 0 <= pos <= 11:
            raise ValueError("Encoder position must be between 0 and 11")
        if pos != self.__encoder_pos:
            self.__encoder_pos = pos
            self.__update_encoder()
    
    @property
    def encoder_led(self):
        return self.__encoder_led
    
    @encoder_led.setter
    def encoder_led(self, led: int|bool):
        if isinstance(led, bool):
            led = int(led)
        elif not (((led == 0) or (led == 1)) and isinstance(led, int)):
            raise ValueError("Encoder LED must be between 0 or 1 or an instance of bool")

        if led != self.__encoder_led:
            self.__encoder_led = led
            self.__update_encoder()
    
    def level_meter_impulse(self, level: int):
        if not isinstance(level, int):
            raise ValueError("Level must be an integer")
        if not 0 <= level <= 13:
            raise ValueError("Level must be between 0 and 13")
        
        level = 14 if level == 13 else level
        self.__midi_send(mido.Message("aftertouch", value=level + 16*self.__channel))
        
        
    
    
    