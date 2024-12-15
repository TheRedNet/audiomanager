import logging

import voicemeeterlib
import time
import numpy as np

logging.basicConfig(level=logging.INFO)


#class App:
#    def __init__(self, vm):
#        self.vm = vm
#        # register your app as event observer
#        self.levels = [0] * 16
#        self.vm.observer.add(self)
#
#    def __str__(self):
#        return type(self).__name__
#
#    # define an 'on_update' callback function to receive event updates
#    def on_update(self, event):
#        logging.info(f"Event: {event}")
#        if event == "pdirty":
#            print("pdirty!")
#        elif event == "mdirty":
#            print("mdirty!")
#        elif event == "ldirty":
#            lnum = 0
#            for bus in self.vm.bus:
#                if bus.levels.isdirty:
#                    self.levels[lnum] = max(bus.levels.all)
#                lnum += 1
#            for strip in self.vm.strip:
#                if strip.levels.isdirty:
#                    self.levels[lnum] = max(strip.levels.postfader)
#                lnum += 1
#            logging.info(f"Levels: {self.levels}")
#        elif event == "midi":
#            current = self.vm.midi.current
#            print(f"Value of midi button {current} is {self.vm.midi.get(current)}")
class App:
    def __init__(self):
        self.levels = [] * 16
        self.delay = 0.05
        KIND_ID = "potato"
        vm = voicemeeterlib.api(KIND_ID, ldirty=True, pdirty=True, ratelimit=100)
        vm.login()
        self.undirty_skips = 0
        try:
            while True:
                if vm.ldirty:
                    self.update_levels(vm)
                    print(self.level_message())
                    vm.clear_dirty()
                    self.delay = np.interp(max(self.levels), [-200, -100, 10], [0.2, 0.1, 0.01])
                time.sleep(self.delay)
        except KeyboardInterrupt:
            vm.logout()
        except Exception as e:
            vm.logout()
            time.sleep(1)
            raise e
    def update_levels(self, vm):
        levels = [0] * 16
        lnum = 0
        for strip in vm.strip:
            levels[lnum] = max(strip.levels.postfader)
            lnum += 1
        for bus in vm.bus:
            levels[lnum] = max(bus.levels.all)
            lnum += 1
        self.levels = levels
        
    def level_message(self):
        fullstring = "Strip: "
        for i in range(len(self.levels)):
            string = " " * 6
            string = string[:6-len(str(self.levels[i]))] + str(self.levels[i])
            fullstring += " " + string
            if i == 7:
                fullstring += " Bus: "
        fullstring += f" Delay: {self.delay:.3f}s"
        return fullstring
        

        



if __name__ == "__main__":
    App()