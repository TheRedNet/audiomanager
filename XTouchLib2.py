from XTouchLib2Channel import *
import mido

class XTouch:
    def __init__(self):
        
        self.__input_name, self.__output_name = self.__get_device_name()
        self.__midi_in = mido.open_input(self.__input_name)
        self.__midi_out = mido.open_output(self.__output_name)
        self.__channels = [Channel(i, self.__color_callback, self.__midi_out_callback) for i in range(8)]
    
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
    
    def __color_callback(self):
        colors = [channel.display_color for channel in self.__channels]
        self.__midi_out.send(XTutils.color_message(colors))
    
    def __midi_out_callback(self, msg: mido.Message):
        self.__midi_out.send(msg)
    
    @property
    def channels(self):
        return self.__channels
    
    @channels.setter
    def channels(self, value):
        if not isinstance(value, List[Channel]):
            raise ValueError("Channels must be a list of Channel objects")
        if len(value) != 8:
            raise ValueError("Channels must be a list of length 8")
        self.__channels = value