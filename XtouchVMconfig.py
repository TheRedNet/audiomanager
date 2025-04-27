import json
import os
import logging
from XTouchLibTypes import XTouchColor

def type_string_generator(channel):
        return f"{"Physical" if channel%8 < 5 else "Virtual"}{"Input" if channel < 8 else "Output"}{(channel%8)+1}"

class Config:
    def __init__(self, config_file='config.json'):
        self.logger = logging.getLogger(__name__)
        self.config_file = config_file
        self.__settings = {
            "channels": {
                0:{"type": "input" , "name": "WaveMIC", "color": XTouchColor.GREEN.value},
                1:{"type": "input" , "name": "RiftMIC", "color": XTouchColor.GREEN.value},
                2:{"type": "input" , "name": "Input 3", "color": XTouchColor.GREEN.value},
                3:{"type": "input" , "name": "FANTOM", "color": XTouchColor.RED.value},
                4:{"type": "input" , "name": "Discord", "color": XTouchColor.BLUE.value},
                5:{"type": "input" , "name": "System", "color": XTouchColor.MAGENTA.value},
                6:{"type": "input" , "name": "Spotify", "color": XTouchColor.GREEN.value},
                7:{"type": "input" , "name": "FireFox", "color": XTouchColor.YELLOW.value},
                8:{"type": "output", "name": "V Mic", "color": XTouchColor.WHITE.value},
                9:{"type": "output", "name": "Speaker", "color": XTouchColor.WHITE.value},
                10:{"type": "output", "name": "BTHead", "color": XTouchColor.WHITE.value},
                11:{"type": "output", "name": "WaveOut", "color": XTouchColor.WHITE.value},
                12:{"type": "output", "name": "Oculus", "color": XTouchColor.WHITE.value},
                13:{"type": "output", "name": "Output6", "color": XTouchColor.WHITE.value},
                14:{"type": "output", "name": "Visual", "color": XTouchColor.WHITE.value},
                15:{"type": "output", "name": "Record", "color": XTouchColor.WHITE.value},
            }
        }
        self.generate_default_config()
        self.load_config()

    
    
    def generate_default_config(self):
        for i in range(1, 16):
            self.__settings["channels"][i] = {
                "type": type_string_generator(i),
                "name": f"Input {i+1}" if i <= 7 else f"Output{i-7}",
                "color": XTouchColor.GREEN.value if i <= 7 else XTouchColor.RED.value
            }
    
    def load_config(self):
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r') as file:
                json_settings = json.load(file)
                settings = {}
                parse_error = False
                config_update = False
                if "channels" in json_settings:
                    settings["channels"] = {}
                    for i in range(16):
                        if str(i) in json_settings["channels"]:
                            settings["channels"][i] = {}
                            # Check if the channel is a dictionary and has the required keys
                            if "type" in json_settings["channels"][str(i)]:
                                if json_settings["channels"][str(i)]["type"] != type_string_generator(i):
                                    self.logger.info(f"Outdated type in config file for channel {i}. Expected {type_string_generator(i)}, got {json_settings['channels'][str(i)]['type']}. Type will be updated.")
                                    config_update = True
                                settings["channels"][i]["type"] = type_string_generator(i)
                            else:
                                self.logger.error(f"Invalid config file format: Missing type for channel {i}.")
                                parse_error = True
                                break
                            if "name" in json_settings["channels"][str(i)]:
                                if len(json_settings["channels"][str(i)]["name"]) > 7:
                                    self.logger.warning(f"Name too long in config file for channel {i}. The name will not fit on the XTouch.")
                                settings["channels"][i]["name"] = json_settings["channels"][str(i)]["name"]
                            else:
                                self.logger.error(f"Invalid config file format: Missing name for channel {i}.")
                                parse_error = True
                                break
                            if "color" in json_settings["channels"][str(i)]:
                                if isinstance(json_settings["channels"][str(i)]["color"], int):
                                    if json_settings["channels"][str(i)]["color"] in range(0, 8):
                                        settings["channels"][i]["color"] = json_settings["channels"][str(i)]["color"]
                                    else:
                                        self.logger.error(f"Invalid config file format: Color value out of range for channel {i}. Expected 0-7, got {json_settings['channels'][str(i)]['color']}.")
                                        parse_error = True
                                        break
                                else:
                                    self.logger.error(f"Invalid config file format: Color value not an integer for channel {i}. Expected int, got {type(json_settings['channels'][str(i)]['color'])}.")
                                    parse_error = True
                                    break
                            else:
                                self.logger.error(f"Invalid config file format: Missing color for channel {i}.")
                                parse_error = True
                                break
                                    
                        else:
                            self.logger.error(f"Invalid config file format: Missing channel {i} in \"channels\" key: {self.config_file}")
                            parse_error = True
                            break
                else:
                    self.logger.error(f"Invalid config file format: {self.config_file}. 'channels' key not found.")
                    parse_error = True
                if not parse_error:
                    self.__settings = settings
                    if config_update:
                        self.logger.info("Saving updated config file.")
                        self.save_config()
        else:
            self.save_config()

    def save_config(self):
        with open(self.config_file, 'w') as file:
            json.dump(self.__settings, file, indent=4)

    @property
    def settings(self):
        return self.__settings
    
    @settings.setter
    def settings(self, value):
        self.__settings = value
        #self.save_config()


# Example usage
if __name__ == "__main__":
    config = Config()
    print(config.settings)
    config.settings["volume"] = 75
    config.save_config()