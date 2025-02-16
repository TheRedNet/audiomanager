from XTouchLib import *
import logging
import voicemeeterlib as voicemeeter
from threading import Thread
import time
import XTouchVMinterface as xtvmi
import XtouchVMconfig as xtcfg
import mido
import islocked
from enum import Enum

def level_interpolation(db):
    if db == -200:
        return 0
    db = round(db, 0)
    db_list = [-200, -100, -50, -40, -35, -30, -25, -20, -15, -10, -5, 0, 5]
    for i in range(1,len(db_list)):
        if db_list[i - 1] < db <= db_list[i]:
            return i
    return 13

class Mode(Enum):
    MAINMENU = 1
    SELECTCHANNEL = 2

class AppState:
    def __init__(self, vm = voicemeeter.api("potato"), xtouch: XTouch = XTouch()):
        self.xt = xtouch
        self.vm = vm
        self.xtvmi = xtvmi.VMInterfaceFunctions(self.vm)
        # shared state for all menus
        self.mode = Mode.MAINMENU
        
        # shared state for main menu
        self.mounted_channels = [3,4,5,6,7,9,10,11]
        
        # shared state for select channel menu
        self.selected_channel = 0
        
    
    
    
# This is the base class for all menus
class Menu:
    def __init__(self, appstate: AppState):
        pass
    
    def __del__(self):
        pass
    
    # This is the main loop of the menu called by the app every 0.1 seconds
    def main_loop(self):
        pass
    
    # XTouch callbacks
    def button_callback(self, channel: int, button: XTouchButton, state: bool, time: float):
        pass
    
    def fader_callback(self, channel: int, db: float, pos: int):
        pass
    
    def touch_callback(self, channel: int, state: bool, time: float):
        pass
    
    def encoder_callback(self, channel: int, ticks: int):
        pass
    # End of XTouch callbacks
    
    
    


class MainMenu:
    def __init__(self, appstate: AppState):
        pass
    
    def __del__(self):
        pass
    
    
    def main_loop(self):
        pass
    
    # XTouch callbacks
    def button_callback(self, channel: int, button: XTouchButton, state: bool, time: float):
        pass
    
    def fader_callback(self, channel: int, db: float, pos: int):
        pass
    
    def touch_callback(self, channel: int, state: bool, time: float):
        pass
    
    def encoder_callback(self, channel: int, ticks: int):
        pass
    # End of XTouch callbacks
    
    
    
class SelectChannelMenu:
    def __init__(self, appstate: AppState):
        self.apps = appstate
    
    def __del__(self):
        pass
    
    
    def main_loop(self):
        pass
    
    # XTouch callbacks
    def button_callback(self, channel: int, button: XTouchButton, state: bool, time: float):
        pass
    
    def fader_callback(self, channel: int, db: float, pos: int):
        pass
    
    def touch_callback(self, channel: int, state: bool, time: float):
        pass
    
    def encoder_callback(self, channel: int, ticks: int):
        pass
    # End of XTouch callbacks


class App:
    def __init__(self, appstate: AppState):
        pass