from XTouchLib import *
import logging
import voicemeeterlib as voicemeeter
from threading import Thread
import time
import XTouchVMinterface as xtvmi

logging.basicConfig(level=logging.INFO)

class App:
    def __init__(self, vm = voicemeeter.api("potato")):
        self.xt = XTouch(button_callback=self.button_callback, fader_callback=self.fader_callback, touch_callback=self.fader_touch_callback)
        self.running = True
        vm.event.pdirty = True
        vm.event.ldirty = True
        self.vm = vm
        
        self.levels = [0] * 16
        self.channel_mount_list = [3,4,5,6,7,9,10,11]
        
        self.fader_quick_touch = [0]*8
        self.fader_quick_touch_timeout = 0
        self.fader_quick_touch_wait = False
        
        self.vmint = xtvmi.VMInterfaceFunctions(self.vm)
        self.vmstate = xtvmi.VMInterfaceFunctions.VMState()
        self.vmstate.sync(self.vm)
        self.update_parameters()
        

        
    def close(self):
        self.running = False
        del self.xt
        
    
    def level_interpolation(self, db):
        if db == -200:
            return 0
        db = round(db, 0)
        db_list = [-200, -100, -50, -40, -35, -30, -25, -20, -15, -10, -5, 0, 5]
        for i in range(1,len(db_list)):
            if db > db_list[i-1] and db <= db_list[i]:
                return i
        return 13
    
    
    def update_levels(self):
        for i in range(8):
            level = self.level_interpolation(self.vmint.get_level(self.channel_mount_list[i]))
            channel = self.channel_mount_list[i]
            channel_name = f"{"i" if channel <= 7 else "o"}{str((channel%8)+1)}"
            self.xt.set_display_text(i,1, f"{str(level).ljust(2)} {channel_name}")
            if not level == 0:
                self.xt.set_level_meter(i, level)
                
    def update_parameters(self):
        for i in range(8):
            channel = self.channel_mount_list[i]
            params = self.vmint.get_channel_params(channel)
            self.xt.set_button_led(i, XTouchButton.MUTE, params.mute)
            if self.vmint.is_strip(channel):
                self.xt.set_button_led(i, XTouchButton.SOLO, params.solo)
            self.xt.set_fader(i, db=min(8,params.gain))

    def run(self):
        time_taken = 0
        while self.running:
            time_start = time.time()
            if self.vm.ldirty:
                self.update_levels()
            if self.vm.pdirty:
                self.update_parameters()
            if self.fader_quick_touch_wait:
                self.quick_touch_wait()
            self.xt.set_display_text(0, 0, f"T{(time_taken*1000):.1f}")
            time_taken = time.time()-time_start
            if time_taken < 0.1:
                time.sleep(0.1-time_taken)
            else:
                logging.warning(f"LAG: Time taken: {time_taken} seconds")

    
    def quick_touch_wait(self):
        if self.fader_quick_touch_timeout > time.time():
            return
        else:
            for i in range(8):
                if self.fader_quick_touch[i] == 3:
                    self.fader_quick_touch[i] = 0
                    self.xt.set_button_led(i, XTouchButton.SELECT, False)
            self.fader_quick_touch_wait = False
    
    def fader_touch_callback(self, channel, state, time_pressed):
        if ((time_pressed < 0.5 and state) or (time_pressed < 0.3 and not state)) and not self.fader_quick_touch_wait:
            qt_count = self.fader_quick_touch[channel]
            print(self.fader_quick_touch[channel])
            if qt_count == 0 and not state:
                self.fader_quick_touch[channel] = 1
            elif qt_count < 2:
                self.fader_quick_touch[channel] += 1
            elif qt_count == 2 and not state:
                self.fader_quick_touch_timeout = time.time() + 1.0
                vchannel = self.channel_mount_list[channel]
                params = self.vmint.get_channel_params(vchannel)
                params.gain = 0
                self.fader_quick_touch[channel] = 3
                self.xt.set_button_led(channel, XTouchButton.SELECT, 1)
                self.fader_quick_touch_wait = True
        elif 0 < self.fader_quick_touch[channel] < 3:
            print("reset")
            self.fader_quick_touch[channel] = 0
            
    
    def button_callback(self, channel, button, state, time_pressed):
        if button == XTouchButton.MUTE and state:
            channel = self.channel_mount_list[channel]
            params = self.vmint.get_channel_params(channel)
            params.mute = not params.mute
    
    def fader_callback(self, channel, db, position):
        if self.fader_quick_touch_timeout > time.time():
            return
        vchannel = self.channel_mount_list[channel]
        params = self.vmint.get_channel_params(vchannel)
        params.gain = max(-60,round(db,1))
        
        
with voicemeeter.api("potato") as vm:
    app = App(vm=vm)
    try:
        app.run()
    except Exception as e:
        logging.exception(e, exc_info=True)
        print("Exiting... Goodbye!")