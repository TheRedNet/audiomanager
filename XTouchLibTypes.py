from enum import Enum

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

class XTouchButtonLED(Enum):
    """Enumeration for XTouch button LEDs."""
    OFF = 0
    ON = 1
    BLINK = 2
    
class XTouchStateUnchecked:
    def __init__(self, no_init=False):
        if no_init:
            return
        self.display_colors = [7] * 8
        self.display_text = " " * 112
        self.button_leds = [[0] * 4 for _ in range(8)]
        self.encoder_rings = [(0,0,False)] * 8
        self.faders = [-8192] * 8

    def __eq__(self, other):
        return self.display_colors == other.display_colors and self.display_text == other.display_text and self.button_leds == other.button_leds and self.encoder_rings == other.encoder_rings and self.faders == other.faders

    def copy(self):
        """
        Create a copy of the XTouch state.
        :return: Copy of the XTouch state.
        """
        state = XTouchStateUnchecked(no_init=True)
        state.display_colors = self.display_colors.copy()
        state.display_text = self.display_text
        state.button_leds = [buttons.copy() for buttons in self.button_leds]
        state.encoder_rings = self.encoder_rings.copy()
        state.faders = self.faders.copy()
        return state

class XTouchState:
    def __init__(self, initial_state: XTouchStateUnchecked = XTouchStateUnchecked()):
        self.__display_colors = initial_state.display_colors
        self.__diplay_text = initial_state.display_text
        self.__button_leds = initial_state.button_leds
        self.__encoder_rings = initial_state.encoder_rings
        self.__faders = initial_state.faders
        


    def __eq__(self, other):
        return self.__display_colors == other.display_colors and self.__diplay_text == other.display_text and self.__button_leds == other.button_leds and self.__encoder_rings == other.encoder_rings and self.__faders == other.faders
    
    def copy(self):
        """
        Create a copy of the XTouch state.
        :return: Copy of the XTouch state.
        """
        state = XTouchState()
        state.display_colors = self.display_colors.copy()
        state.display_text = self.display_text
        state.button_leds = self.button_leds.copy()
        state.encoder_rings = self.encoder_rings.copy()
        state.faders = self.faders.copy()
        return state
    
    @property
    def display_text(self):
        return self.__diplay_text
    @display_text.setter
    def display_text(self, text: str):
        if len(text) > 112:
            raise ValueError("Display text cannot be longer than 112 characters")
        if any(ord(c) > 127 for c in text):
            raise ValueError("Display text must be ASCII")
        self.__diplay_text = text
    @property
    def display_colors(self):
        return self.__display_colors
    @display_colors.setter
    def display_colors(self, colors: list):
        if len(colors) != 8:
            raise ValueError("Color list must be of length 8")
        if any(color not in range(8) for color in colors):
            raise ValueError("Invalid color value")
        self.__display_colors = colors
    @property
    def button_leds(self):
        return self.__button_leds
    @button_leds.setter
    def button_leds(self, button_leds: list):
        if len(button_leds) != 8:
            raise ValueError("Button LED list must be of length 8")
        if any(len(leds) != 4 for leds in button_leds):
            raise ValueError("Each button LED list must be of length 4")
        if any(led not in range(3) for leds in button_leds for led in leds):
            raise ValueError("Invalid LED value")
        self.__button_leds = button_leds
    @property
    def encoder_rings(self):
        return self.__encoder_rings
    @encoder_rings.setter
    def encoder_rings(self, encoder_rings: list):
        if len(encoder_rings) != 8:
            raise ValueError("Encoder ring list must be of length 8")
        if any(len(ring) != 3 for ring in encoder_rings):
            raise ValueError("Each encoder ring list must be of length 3")
        if any(ring[0] not in range(4) for ring in encoder_rings):
            raise ValueError("Invalid encoder ring mode")
        if any(ring[1] not in range(16) for ring in encoder_rings):
            raise ValueError("Invalid encoder ring value")
        if any(ring[2] not in [True, False] for ring in encoder_rings):
            raise ValueError("Invalid encoder ring LED value")
        self.__encoder_rings = encoder_rings

    @property
    def faders(self):
        return self.__faders
    @faders.setter
    def faders(self, faders: list):
        if len(faders) != 8:
            raise ValueError("Fader list must be of length 8")
        if any(fader not in range(-8192, 8188) for fader in faders):
            raise ValueError("Invalid fader value")
        self.__faders = faders
