import json
import os
from XTouchLibTypes import XTouchColor

class Config:
    def __init__(self, config_file='config.json'):
        self.config_file = config_file
        self.__settings = {
            "strips": [
                {"channel": 1 , "type": "input" , "name": "Input 1", "color": XTouchColor.GREEN.value},
                {"channel": 2 , "type": "input" , "name": "Input 2", "color": XTouchColor.GREEN.value},
                {"channel": 3 , "type": "input" , "name": "Input 3", "color": XTouchColor.GREEN.value},
                {"channel": 4 , "type": "input" , "name": "Input 4", "color": XTouchColor.GREEN.value},
                {"channel": 5 , "type": "input" , "name": "Input 5", "color": XTouchColor.GREEN.value},
                {"channel": 6 , "type": "input" , "name": "Input 6", "color": XTouchColor.GREEN.value},
                {"channel": 7 , "type": "input" , "name": "Input 7", "color": XTouchColor.GREEN.value},
                {"channel": 8 , "type": "input" , "name": "Input 8", "color": XTouchColor.GREEN.value},
                {"channel": 9 , "type": "output", "name": "Output1", "color": XTouchColor.RED  .value},
                {"channel": 10, "type": "output", "name": "Output2", "color": XTouchColor.RED  .value},
                {"channel": 11, "type": "output", "name": "Output3", "color": XTouchColor.RED  .value},
                {"channel": 12, "type": "output", "name": "Output4", "color": XTouchColor.RED  .value},
                {"channel": 13, "type": "output", "name": "Output5", "color": XTouchColor.RED  .value},
                {"channel": 14, "type": "output", "name": "Output6", "color": XTouchColor.RED  .value},
                {"channel": 15, "type": "output", "name": "Output7", "color": XTouchColor.RED  .value},
                {"channel": 16, "type": "output", "name": "Output8", "color": XTouchColor.RED  .value},
            ]
        }
        self.load_config()

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