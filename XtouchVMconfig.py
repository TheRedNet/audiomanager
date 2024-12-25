import json
import os
from XTouchLibTypes import XTouchColor

class Config:
    def __init__(self, config_file='config.json'):
        self.config_file = config_file
        self.__settings = {
            "channels": {
                0:{"type": "input" , "name": "Input 1", "color": XTouchColor.GREEN.value},
                1:{"type": "input" , "name": "Input 2", "color": XTouchColor.GREEN.value},
                2:{"type": "input" , "name": "Input 3", "color": XTouchColor.GREEN.value},
                3:{"type": "input" , "name": "FANTOM", "color": XTouchColor.RED.value},
                4:{"type": "input" , "name": "Discord", "color": XTouchColor.BLUE.value},
                5:{"type": "input" , "name": "System", "color": XTouchColor.MAGENTA.value},
                6:{"type": "input" , "name": "Spotify", "color": XTouchColor.GREEN.value},
                7:{"type": "input" , "name": "FireFox", "color": XTouchColor.YELLOW.value},
                8:{"type": "output", "name": "Output1", "color": XTouchColor.WHITE.value},
                9:{"type": "output", "name": "Speaker", "color": XTouchColor.WHITE.value},
                10:{"type": "output", "name": "BTHead", "color": XTouchColor.WHITE.value},
                11:{"type": "output", "name": "WaveOut", "color": XTouchColor.WHITE.value},
                12:{"type": "output", "name": "Oculus", "color": XTouchColor.WHITE.value},
                13:{"type": "output", "name": "Output6", "color": XTouchColor.WHITE.value},
                14:{"type": "output", "name": "Output7", "color": XTouchColor.WHITE.value},
                15:{"type": "output", "name": "Output8", "color": XTouchColor.WHITE.value},
            }
        }
        #self.generate_default_config()
        #self.load_config()

    def generate_default_config(self):
        for i in range(1, 16):
            self.__settings["channels"][i] = {
                "type": "input" if i <= 7 else "output",
                "name": f"Input {i+1}" if i <= 7 else f"Output{i-7}",
                "color": XTouchColor.GREEN.value if i <= 7 else XTouchColor.RED.value
            }
    
    def load_config(self):
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r') as file:
                self.__settings = json.load(file)
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