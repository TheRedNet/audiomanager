import mido
from enum import Enum
from typing import Callable
import numpy as np
import logging

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

class XTouchButton(Enum):
    """Enumeration for XTouch buttons."""
    REC = 0
    SOLO = 1
    MUTE = 2
    SELECT = 3

class XTouch:
    """Class to interact with the XTouch device."""
    __fader_db = [-70, -30, -10, 0, 8]
    __fader_pos = [-8192, -4464, 0, 4384, 8188]
    __sysex_prefix = [0xF0, 0x00, 0x00, 0x66, 0x15]
    __sysex_suffix = [0xF7]
    __sysex_color_command = [0x72]
    __sysex_display_command = [0x12]
    __sysex_device_query = [0x00]
    __max_pitchbend = 8188
    __min_pitchbend = -8192
    def __init__(self, fader_callback: Callable[[int, float, int], None] = None, encoder_callback: Callable[[int, int], None] = None, encoder_press_callback: Callable[[int, bool], None] = None, button_callback: Callable[[int, XTouchButton, bool], None] = None, touch_callback: Callable[[int, bool], None] = None):
    
        """
        Initialize the XTouch device.

        :param fader_callback: Callback function for fader events.
        :param encoder_callback: Callback function for encoder events.
        :param encoder_press_callback: Callback function for encoder press events.
        :param button_callback: Callback function for button events.
        :param touch_callback: Callback function for touch events.
        """
        try:
            input_name, output_name = self.__get_device_name()
        except OSError as e:
            raise e
        self.input = mido.open_input(input_name, callback=self.__midi_callback)
        self.output = mido.open_output(output_name)
        
        self.logger = logging.getLogger("XTouch Library")
        
        self.__display_colors = [0] * 8
        
        self.__fader_callback = fader_callback
        self.__encoder_callback = encoder_callback
        self.__encoder_press_callback = encoder_press_callback
        self.__button_callback = button_callback
        self.__touch_callback = touch_callback
        
        #self.output.send(mido.Message.from_bytes(self.__sysex_prefix + self.__sysex_device_query + self.__sysex_suffix))
        self.output.send(self.__display_hello_msg())

    def change_callback(self, fader_callback: Callable[[int, float, int], None] = None, encoder_callback: Callable[[int, int], None] = None, encoder_press_callback: Callable[[int, bool], None] = None, button_callback: Callable[[int, XTouchButton, bool], None] = None, touch_callback: Callable[[int, bool], None] = None):
        """
        Change the callback functions for the XTouch device.

        :param fader_callback: Callback function for fader events.
        :param encoder_callback: Callback function for encoder events.
        :param encoder_press_callback: Callback function for encoder press events.
        :param button_callback: Callback function for button events.
        :param touch_callback: Callback function for touch events.
        """
        was_set = False
        if fader_callback is None or callable(fader_callback):
            self.__fader_callback = fader_callback
            was_set = True
        if encoder_callback is None or callable(encoder_callback):
            self.__encoder_callback = encoder_callback
            was_set = True
        if encoder_press_callback is None or callable(encoder_press_callback):
            self.__encoder_press_callback = encoder_press_callback
            was_set = True
        if button_callback is None or callable(button_callback):
            self.__button_callback = button_callback
            was_set = True
        if touch_callback is None or callable(touch_callback):
            self.__touch_callback = touch_callback
            was_set = True
        if not was_set:
            raise ValueError("No valid callback functions provided")
        

    def __del__(self):
        """Clean up the XTouch device."""
        if self.input is not None:
            self.input.close()
        if self.output is not None:
            self.output.close()
    
    def __get_device_name(self):
        """
        Get the input and output device names for the XTouch device.

        :return: Tuple containing input and output device names.
        :raises OSError: If no XTouch device is found.
        """
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
        """
        Create a SysEx message to display text on the XTouch device.

        :param dpstring: The text to display.
        :param offset: The offset for the display.
        :return: SysEx message.
        """
        prefix = self.__sysex_prefix + self.__sysex_display_command + [offset]
        suffix = self.__sysex_suffix
        dpbytes = [ord(c) for c in dpstring]
        msgbytearray = prefix + dpbytes + suffix
        return mido.Message.from_bytes(msgbytearray)

    def __display_color_msg(self):
        """
        Create a SysEx message to set the display colors on the XTouch device.

        :return: SysEx message.
        """
        prefix = self.__sysex_prefix + self.__sysex_color_command
        suffix = self.__sysex_suffix
        color_bytes = [color for color in self.__display_colors]
        msgbytearray = prefix + color_bytes + suffix
        return mido.Message.from_bytes(msgbytearray)

    def __display_hello_msg(self):
        """
        Create a SysEx message to display a hello message on the XTouch device.

        :return: SysEx message.
        """
        mackie_string = [ord(" ")] * 7 * 16
        msgbytearray = self.__sysex_prefix + self.__sysex_display_command + [0x00] + mackie_string + self.__sysex_suffix
        return mido.Message.from_bytes(msgbytearray)

    def set_display(self, text, channel, row):
        """
        Display text on the XTouch device.

        :param text: The text to display.
        :param channel: The channel to display the text on.
        :param row: The row to display the text on.
        :raises IndexError: If the channel or row is out of range.
        """
        if not (0 <= channel <= 7):
            raise IndexError("Channel must be between 0 and 7")
        if not (0 <= row <= 1):
            raise IndexError("Row must be between 0 and 1")
        offset = channel * 7 + row * 8 * 7
        self.output.send(self.__display_msg(text, offset))
        
    def set_raw_display(self, text, offset):
        """
        Display text on the XTouch device at a specific offset.

        :param text: The text to display.
        :param offset: The offset to display the text at.
        """
        if len(text) + offset > 112:
            raise IndexError("Text and offset exceed display length of 112 characters")
        self.output.send(self.__display_msg(text, offset))

    def set_display_color(self, color, channel):
        """
        Set the display color on the XTouch device.

        :param color: The color to set.
        :param channel: The channel to set the color on.
        :raises IndexError: If the channel is out of range.
        :raises ValueError: If the color is out of range.
        """
        if not (0 <= channel <= 7):
            raise IndexError("Channel must be between 0 and 7")
        if isinstance(color, XTouchColor):
            color = color.value
        else:
            if not (0 <= color <= 7):
                raise ValueError("Color must be between 0 and 7 or an instance of XTouchColor")
        self.__display_colors[channel] = color
        self.output.send(self.__display_color_msg())
        
    def set_raw_display_color(self, colors: list):
        if len(colors) != 8:
            raise ValueError("Color list must be of length 8")
        if all(isinstance(c, XTouchColor) for c in colors):
            colors = [c.value for c in colors]
        elif not all((0 <= c <= 7 and isinstance(c, int)) for c in colors):
            raise ValueError("Colors must be between 0 and 7 or instances of XTouchColor")
        self.__display_colors = colors
        self.output.send(self.__display_color_msg())
        
    def set_fader(self, channel, db=None, pos=None):
        """
        Set the fader position on the XTouch device.

        :param channel: The channel to set the fader on.
        :param db: The dB value to set the fader to.
        :param pos: The position value to set the fader to.
        :raises IndexError: If the channel is out of range.
        :raises ValueError: If the dB or position value is out of range.
        """
        if not (0 <= channel <= 7):
            raise IndexError("Channel must be between 0 and 7")
        value = 0
        if db is not None:
            if db < self.__fader_db[0] or db > self.__fader_db[-1]:
                raise ValueError(f"db value must be between {self.__fader_db[0]} and {self.__fader_db[-1]}")
            value = np.interp(db, self.__fader_db, self.__fader_pos)
        elif pos is not None:
            if pos < self.__min_pitchbend or pos > self.__max_pitchbend:
                raise ValueError(f"pos value must be between {self.__min_pitchbend} and {self.__max_pitchbend}")
            value = pos

        self.output.send(mido.Message("pitchwheel", channel=channel, pitch=value))
    
    def __generate_response_code(self, challenge_code):
        """
        Generate a response code for the given challenge code.

        :param challenge_code: The challenge code.
        :return: The response code.
        """
        r = [0] * 4
        c = challenge_code
        r[0] = 0x7F & (c[0] + (c[1] ^ 0x0A) - c[3])
        r[1] = 0x7F & ((c[2] >> 4) ^ (c[0] + c[3]))
        r[2] = 0x7F & (c[3] - (c[2] << 2) ^ (c[0] | c[1]))
        r[3] = 0x7F & (c[1] - c[2] + (0xF0 ^ (c[3] << 4)))
        return r

    def __handle_sysex_handshake(self, msg):
        """
        Handle the SysEx handshake process.

        :param msg: The SysEx message.
        :raises ConnectionError: If the handshake fails.
        """
        # Handshake Procedure:
        # 1. Host sends 0x00
        # 2. Device responds with 0x01 7 bytes serial number and 4 bytes challenge code
        # 3. Host responds with 0x02 7 bytes serial number and 4 bytes response code
        # 4. Device now has two options: 0x03 to accept or 0x04 to reject both with 7 bytes serial number
        sysex_host_query_connection = 0x1  # 7 bytes serial number and 4 bytes challenge code sent by device
        sysex_host_query_response = 0x2  # 7 bytes serial number and 4 bytes response code sent by host
        sysex_host_accept = 0x3  # 7 bytes serial number sent by device
        sysex_host_reject = 0x4  # 7 bytes serial number sent by device
        sysex_version_query = 0x13  # 0x00 as parameter sent by host
        sysex_version_response = 0x14  # 5 bytes version by device
        sysex_command_byte = 4
        print(hex(msg.data[sysex_command_byte]))
        print(msg.data)
        if msg.data[sysex_command_byte] == sysex_host_query_connection:
            print("Handshake response sent")
            response = self.__sysex_prefix + [sysex_host_query_response] + list(msg.data[5:12]) + list(self.__generate_response_code(list(msg.data[12:16]))) + self.__sysex_suffix
            print("Responding with: ", (mido.Message.from_bytes(response)).hex())
            self.output.send(mido.Message.from_bytes(response))
            self.output.send(mido.Message.from_bytes(self.__sysex_prefix + [sysex_version_query] + [0x00] + self.__sysex_suffix))
        elif msg.data[sysex_command_byte] == sysex_host_accept:
            self.logger.info("Handshake successful")
            print("Handshake successful")
            self.output.send(mido.Message.from_bytes(self.__sysex_prefix + [sysex_version_query] + [0x00] + self.__sysex_suffix))
        elif msg.data[sysex_command_byte] == sysex_host_reject:
            self.logger.error("Handshake failed")
            print("Handshake failed")
            self.input.close()
            self.output.close()
            raise ConnectionError("Handshake failed")
        elif msg.data[sysex_command_byte] == sysex_version_response:
            # v.v.v.v.v
            vstring = f"{msg.data[5]}.{msg.data[6]}.{msg.data[7]}.{msg.data[8]}.{msg.data[9]}"
            self.logger.info(f"X-Touch Device version: {vstring}")

    def __midi_callback(self, msg: mido.Message):
        """
        Handle incoming MIDI messages.

        :param msg: The MIDI message.
        """
        try:
            if msg.type == "pitchwheel":
                if self.__fader_callback is not None:
                    self.__fader_callback(msg.channel, np.interp(msg.pitch, self.__fader_pos, self.__fader_db), msg.pitch)
            elif msg.type == "control_change":
                if self.__encoder_callback is not None:
                    ticks = msg.value % 64
                    if msg.value < 64:
                        ticks = -ticks
                    self.__encoder_callback(msg.control - 16, ticks)
            elif msg.type == "note_on":
                if 0 <= msg.note <= 31:
                    button = None
                    if msg.note <= 7:
                        button = XTouchButton.REC
                    elif 8 <= msg.note <= 15:
                        button = XTouchButton.SOLO
                    elif 16 <= msg.note <= 23:
                        button = XTouchButton.MUTE
                    elif 24 <= msg.note <= 31:
                        button = XTouchButton.SELECT
                    channel = msg.note % 8
                    if msg.velocity == 127:
                        if self.__button_callback is not None:
                            self.__button_callback(channel, button, True)
                    else:
                        if self.__button_callback is not None:
                            self.__button_callback(channel, button, False)
                elif 32 <= msg.note <= 39:
                    if msg.velocity == 127:
                        if self.__encoder_press_callback is not None:
                            self.__encoder_press_callback(msg.note - 32, True)
                    else:
                        if self.__encoder_press_callback is not None:
                            self.__encoder_press_callback(msg.note - 32, False)
                elif 104 <= msg.note <= 111:
                    if msg.velocity == 127:
                        if self.__touch_callback is not None:
                            self.__touch_callback(msg.note - 104, True)
                    else:
                        if self.__touch_callback is not None:
                            self.__touch_callback(msg.note - 104, False)
            elif msg.type == "sysex":
                print(msg.hex())
                if 0 <= msg.data[4] <= 4 or msg.data[4] == 0x13 or msg.data[4] == 0x14:
                    self.__handle_sysex_handshake(msg)
            else:
                print(msg)
        except Exception as e:
            logging.error(e, exc_info=True)

    def set_button_led(self, channel, button, state, blink=False):
        """
        Set the LED state for a button on the XTouch device.

        :param channel: The channel of the button.
        :param button: The button to set the LED for.
        :param state: The state of the LED (True for on, False for off).
        :param blink: Whether the LED should blink.
        :raises TypeError: If state or blink is not a boolean.
        :raises IndexError: If the channel is out of range.
        :raises ValueError: If the button is out of range.
        """
        if not isinstance(state, bool):
            raise TypeError("State must be a boolean")
        if not isinstance(blink, bool):
            raise TypeError("Blink must be a boolean")
        if not (0 <= channel <= 7):
            raise IndexError("Channel must be between 0 and 7")
        if isinstance(button, XTouchButton):
            button = button.value
        else:
            if not (0 <= button <= 3):
                raise ValueError("Button must be between 0 and 3 or an instance of XTouchButton")
        velocity = 0
        if state:
            velocity = 127
        if blink and state:
            velocity = 1
        int_button = button * 8 + channel
        self.output.send(mido.Message("note_on", note=int_button, velocity=velocity))

    def set_encoder_ring(self, channel, value, mode: XTouchEncoderRing, light=False):
        """
        Set the encoder ring mode and value on the XTouch device.

        :param channel: The channel of the encoder to set.
        :param value: The value to set the encoder to.
        :param mode: The mode to set the encoder to.
        :param light: Whether the encoder should be lit.
        :raises IndexError: If the encoder is out of range.
        :raises ValueError: If the mode or value is out of range.
        """
        if not (0 <= channel <= 7):
            raise IndexError("Encoder must be between 0 and 7")
        if isinstance(mode, XTouchEncoderRing):
            mode = mode.value
        else:
            if not (0 <= mode <= 3):
                raise ValueError("Mode must be between 0 and 3 or an instance of XTouchEncoderRing")
        if not (0 <= value <= 15):
            raise ValueError("Value must be between 0 and 15")
        if light:
            mode += 4
        self.output.send(mido.Message("control_change", control=channel + 48, value=mode * 16 + value))

    def set_level_meter(self, channel, level):
        """
        Set the level meter value on the XTouch device.

        :param channel: The channel to set the level meter for.
        :param level: The level to set the meter to.
        :raises IndexError: If the channel is out of range.
        :raises ValueError: If the level is out of range.
        """
        if not (0 <= channel <= 7):
            raise IndexError("Channel must be between 0 and 7")
        if not (0 <= level <= 13):
            raise ValueError("Level must be between 0 and 13")
        if level == 13:
            level = 14
        self.output.send(mido.Message("aftertouch", value=level + 16 * channel))