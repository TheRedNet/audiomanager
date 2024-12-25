from XTouchLib import *
import logging
import voicemeeterlib as voicemeeter
from threading import Thread
import time
import XTouchVMinterface as xtvmi
import XtouchVMconfig as xtcfg
import mido
import islocked

logging.basicConfig(level=logging.INFO)


def level_interpolation(db):
    if db == -200:
        return 0
    db = round(db, 0)
    db_list = [-200, -100, -50, -40, -35, -30, -25, -20, -15, -10, -5, 0, 5]
    for i in range(1,len(db_list)):
        if db_list[i - 1] < db <= db_list[i]:
            return i
    return 13


class App:
    def __init__(self, vm = voicemeeter.api("potato")):
        self.xt = XTouch()
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
        self.slockd = self.ScreenLockDetector(xtouch=self.xt)
        self.xt.change_callback(direct_midi_hook_callback=self.slockd.direct_midi_hook,
                                button_callback=self.button_callback,
                                fader_callback=self.fader_callback,
                                touch_callback=self.fader_touch_callback)
        self.config = xtcfg.Config()
        self.vmstate.sync(self.vm)
        self.update_parameters()
        self.update_displays()
        


        
    def close(self):
        self.running = False
        del self.xt

    def update_displays(self):
        colors = [0] * 8
        for i in range(8):
            chanconfig = self.config.settings["channels"][self.channel_mount_list[i]]
            colors[i] = chanconfig["color"]
            self.xt.set_display_text(i, 1, chanconfig["name"])
        self.xt.set_raw_display_color(colors)
    
    def update_levels(self):
        for i in range(8):
            level = level_interpolation(self.vmint.get_level(self.channel_mount_list[i]))
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
        if state:
            self.xt.set_display_text(channel, 1, f"{self.vmint.get_channel_params(self.channel_mount_list[channel]).gain:.1f}dB".rjust(7))
        else:
            self.update_displays()

            
    
    def button_callback(self, channel: int, button: XTouchButton, state: bool, time_pressed: float):
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
        self.xt.set_display_text(channel, 1, f"{params.gain:.1f}dB".rjust(7))





    class ScreenLockDetector:
        def __init__(self, xtouch: XTouch):
            self.next_check = time.time()
            self.locked = False
            self.note_count = 0
            self.xt = xtouch
            self.xtstate_backup = self.xt.state
            self.message_is_displayed = False
            
        def direct_midi_hook(self, msg: mido.Message):
            if time.time() > self.next_check:
                if islocked.islocked():
                    self.locked = True
                    self.next_check = time.time() + 1
                else:
                    self.locked = False
                    self.next_check = time.time() + 1
                    if self.message_is_displayed:
                        self.xt.state = self.xtstate_backup
                        self.message_is_displayed = False
            if msg.type == "note_on":
                prev_note_count = self.note_count
                if msg.velocity == 0:
                    self.note_count -= 1
                else:
                    self.note_count += 1
                if self.locked:
                    if self.message_is_displayed and self.note_count == 0:
                        self.xt.state = self.xtstate_backup
                        self.message_is_displayed = False
                    elif not self.message_is_displayed and self.note_count > 0:
                        self.xtstate_backup = self.xt.state
                        self.xt.set_raw_display_color([XTouchColor.RED]*8)
                        self.xt.set_raw_display_text(0, ("SCREEN SYSTEM "*4+"LOCKED SPERRE "*4))
                        self.message_is_displayed = True
            return self.locked

        
with voicemeeter.api("potato") as vm:
    app = App(vm=vm)
    try:
        app.run()
    except Exception as e:
        logging.exception(e, exc_info=True)
        print("Exiting... Goodbye!")