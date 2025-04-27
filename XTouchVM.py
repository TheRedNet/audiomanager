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


class Mode(Enum):
    """Enumeration for XTouch modes."""
    CHANNELS = 0
    MATRIX = 1

def level_interpolation(db):
    if db == -200:
        return 0
    db = round(db, 0)
    db_list = [-200, -100, -50, -40, -35, -30, -25, -20, -15, -10, -5, 0, 5]
    for i in range(1,len(db_list)):
        if db_list[i - 1] < db <= db_list[i]:
            return i
    return 13

class Scheduler:
    def __init__(self):
        self.tasks = []
    
    def run_due(self):
        for task, due, identifier in self.tasks:
            if time.time() > due:
                task()
                self.tasks.remove((task, due, identifier))
    
    def add_task(self, task, wait, identifier="all"):
        self.tasks.append((task, time.time() + wait, identifier))
    
    def cancel_task(self, identifier):
        self.tasks = [task for task in self.tasks if task[2] != identifier]
    
    def clear(self):
        self.tasks = []

class MatrixMode:
    def __init__(self, xtouch: XTouch, vm = voicemeeter.api("potato")):
        self.terminate = False
        self.xt = xtouch
        self.vm = vm
        
        


class App:
    def __init__(self, vme = voicemeeter.api("potato")):
        self.xt = XTouch()
        self.running = True
        vme.event.pdirty = True
        vme.event.ldirty = True
        self.vm = vme
        
        self.invoke_full_refresh = False
        self.scheduler = Scheduler()
        self.levels = [0] * 16
        self.channel_mount_list_list_default = [[3,4,5,6,7,9,10,12],[8,9,10,11,12,13,14,15],[0,1,2,3,4,5,6,7]]
        self.channel_mount_list_list_names = ["Home","Outputs","Inputs"]
        self.channel_mount_list_list = [list.copy() for list in self.channel_mount_list_list_default]
        self.channel_mount_list_index = 0
        self.channel_mount_list = self.channel_mount_list_list[0]
        
        self.shortcut_mode = 0
        self.shortcut_text_default = "Mode"
        self.shortcut_text = self.shortcut_text_default
        
        self.denoiser_text_default = "Dnoiser"
        self.denoiser_text = self.denoiser_text_default
        
        self.vmint = xtvmi.VMInterfaceFunctions(self.vm)
        self.vmstate = xtvmi.VMInterfaceFunctions.VMState()
        self.slockd = self.ScreenLockDetector(xtouch=self.xt)
        self.set_callbacks()
        self.config = xtcfg.Config()
        self.vmstate.sync(self.vm)
        self.update_parameters()
        self.update_displays()
        

    def set_callbacks(self):
        self.xt.change_callback(direct_midi_hook_callback=self.slockd.direct_midi_hook,
                                button_callback=self.button_callback,
                                fader_callback=self.fader_callback,
                                touch_callback=self.fader_touch_callback,
                                encoder_callback=self.encoder_callback,
                                encoder_press_callback=self.encoder_press_callback)

    def close(self):
        self.running = False
        self.xt.close()
        time.sleep(0.1)
        del self.xt

    def update_displays(self):
        self.xt.set_display_text(0, 0, self.channel_mount_list_list_names[self.channel_mount_list_index])
        self.xt.set_display_text(2, 0, self.shortcut_text)
        if self.channel_mount_list_index == 0:
            self.xt.set_display_text(1, 0, self.denoiser_text)
        else:
            self.xt.set_display_text(1, 0, " ")
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
        any_solos = False
        for i in range(8):
            channel = self.channel_mount_list[i]
            params = self.vmint.get_channel_params(channel)
            self.xt.set_button_led(i, XTouchButton.MUTE, params.mute)
            if self.vmint.is_strip(channel):
                self.xt.set_button_led(i, XTouchButton.SOLO, params.solo)
                if params.solo:
                    any_solos = True
            self.xt.set_fader(i, db=min(8,params.gain))
        if any_solos:
            for i in range(8):
                channel = self.channel_mount_list[i]
                if self.vmint.is_strip(channel):
                    params = self.vmint.get_channel_params(channel)
                    if not params.solo and not params.mute:
                        self.xt.set_button_led(i, XTouchButton.MUTE, XTouchButtonLED.BLINK)
        self.update_encoder_rings()

    def full_refresh(self):
        self.update_parameters()
        self.update_displays()
        self.update_levels()
        self.update_encoder_rings()
        self.invoke_full_refresh = False
        
    def run(self):
        time_taken = 0
        while self.running:
            time_start = time.time()
            if self.invoke_full_refresh:
                self.full_refresh()
            else:
                if self.vm.ldirty:
                    self.update_levels()
                if self.vm.pdirty:
                    self.update_parameters()
            self.scheduler.run_due()
            time_taken = time.time()-time_start
            if time_taken < 0.1:
                time.sleep(0.1-time_taken)
            else:
                logging.warning(f"LAG: Time taken: {time_taken} seconds")
    
    
    def shortcut_functions(self):
        '''
        shortcut functions changing multiple parameters at once
        '''
        def vr_mode(self: App):
            self.vm.strip[0].mute = True
            self.vm.strip[1].mute = False
            self.vm.bus[4].mute = False
            self.vm.bus[2].mute = True
            self.vm.bus[3].mute = True
        
        def desktop_mode(self: App):
            self.vm.strip[0].mute = False
            self.vm.strip[1].mute = True
            self.vm.bus[4].mute = True
            self.vm.bus[2].mute = False
            self.vm.bus[3].mute = False
        return [
            ("DESKTOP", desktop_mode),
            ("VR", vr_mode),
            ]
    
    def shortcut_callback(self):
        self.shortcut_mode += 1
        if self.shortcut_mode >= len(self.shortcut_functions()):
            self.shortcut_mode = 0
        self.shortcut_functions()[self.shortcut_mode][1](self)
        self.shortcut_text = self.shortcut_functions()[self.shortcut_mode][0]
        def reset_shortcut_text():
            self.shortcut_text = self.shortcut_text_default
            self.update_displays()
        self.scheduler.cancel_task("reset_shortcut_text")
        self.scheduler.add_task(reset_shortcut_text, 10, "reset_shortcut_text")
    
    def update_encoder_rings(self):
        #channel 1 encoder ring
        if self.channel_mount_list_index == 0:
            self.xt.set_encoder_ring(channel=0, value=0, mode=XTouchEncoderRing.WRAP)
        elif self.channel_mount_list_index == 2:
            self.xt.set_encoder_ring(channel=0, value=1, mode=XTouchEncoderRing.PAN)
        elif self.channel_mount_list_index == 1:
            self.xt.set_encoder_ring(channel=0, value=11, mode=XTouchEncoderRing.PAN)
        
        #channel 2 encoder ring
        self.xt.set_encoder_ring(channel=1, value=int(self.vm.strip[4].denoiser.knob) + 1, mode=XTouchEncoderRing.WRAP, light=False)
        
        #channel 3 encoder ring
        self.xt.set_encoder_ring(channel=2, value=0, mode=XTouchEncoderRing.WRAP, light=(not self.shortcut_mode == 0))
    
    def encoder_callback(self, channel, ticks):
        if channel == 0:
            self.channel_mount_list_index -= ticks
            self.channel_mount_list_index = self.channel_mount_list_index % len(self.channel_mount_list_list)
            self.channel_mount_list = self.channel_mount_list_list[self.channel_mount_list_index]
            self.invoke_full_refresh = True
        elif channel == 1:
            if self.channel_mount_list_index == 0:
                nv = self.vm.strip[4].denoiser.knob - ticks
                self.vm.strip[4].denoiser.knob = min(10, max(0, nv))
                self.denoiser_text = f"{self.vm.strip[4].denoiser.knob}".rjust(7)
                self.invoke_full_refresh = True
                self.scheduler.cancel_task("reset_denoiser_text")
                def reset_denoiser_text():
                    self.denoiser_text = self.denoiser_text_default
                    self.update_displays()
                self.scheduler.add_task(reset_denoiser_text, 5, "reset_denoiser_text")
        elif 6 <= channel <= 7:
            vchannel = self.channel_mount_list[channel]
            new_channel = (vchannel - ticks) % 16
            self.channel_mount_list[channel] = new_channel
            self.invoke_full_refresh = True
            
        
    def encoder_press_callback(self, channel, state, time_pressed):
        if state and channel == 0:
            self.channel_mount_list_index = 0
            self.channel_mount_list = self.channel_mount_list_list[self.channel_mount_list_index]
            self.invoke_full_refresh = True
        if state and channel == 2:
            self.shortcut_callback()
            self.invoke_full_refresh = True
        if state and channel == 7:
            self.channel_mount_list[channel] = self.channel_mount_list_list_default[self.channel_mount_list_index][channel]
            self.invoke_full_refresh = True
        if state and channel == 6:
            if not self.channel_mount_list[channel] == self.channel_mount_list_list_default[self.channel_mount_list_index][channel]:
                self.channel_mount_list[channel] = self.channel_mount_list_list_default[self.channel_mount_list_index][channel]
            else:
                self.channel_mount_list[channel] += 1
            self.invoke_full_refresh = True
    
    def fader_touch_callback(self, channel, state, time_pressed):
        if state:
            self.xt.set_display_text(channel, 1, f"{self.vmint.get_channel_params(self.channel_mount_list[channel]).gain:.1f}dB".rjust(7))
        else:
            self.update_displays()


    def button_callback(self, channel: int, button: XTouchButton, state: bool, time_pressed: float):
        if state:
            if button == XTouchButton.MUTE:
                channel = self.channel_mount_list[channel]
                params = self.vmint.get_channel_params(channel)
                params.mute = not params.mute
            elif button == XTouchButton.SOLO:
                channel = self.channel_mount_list[channel]
                if self.vmint.is_strip(channel):
                    params = self.vmint.get_channel_params(channel)
                    params.solo = not params.solo



    def fader_callback(self, channel, db, position):
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

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    with voicemeeter.api("potato") as vm:
        app = App(vme=vm)
        try:
            app.run()
        except Exception as e:
            logging.exception(e, exc_info=True)
            print("Exiting... Goodbye!")