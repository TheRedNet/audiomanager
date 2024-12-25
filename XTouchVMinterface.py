import voicemeeterlib as voicemeeter


    

class VMInterfaceFunctions:
    def __init__(self, vm = voicemeeter.api("potato")):
        self.vm = vm
        
    def get_level(self, channel):
        if 0 <= channel <= 7:
            return max(self.vm.strip[channel].levels.postfader)
        elif 8 <= channel <= 15:
            return max(self.vm.bus[channel-8].levels.all)
        else:
            raise IndexError(f"Channel out of range (0-15): {channel}")
        
    def get_channel_params(self, channel):
        if 0 <= channel <= 7:
            return self.vm.strip[channel]
        elif 8 <= channel <= 15:
            return self.vm.bus[channel-8]
        else:
            raise IndexError(f"Channel out of range (0-15): {channel}")
    
    def is_strip(self, channel):
        return 0 <= channel <= 7
    
    
        
    class VMState:
        def __init__(self):
            self.mutes = [False] * 16
            self.solos = [False] * 8
            self.gains = [0] * 16

        def sync(self, vm = voicemeeter.api("potato")):
            for i in range(8):
                self.mutes[i] = vm.strip[i].mute
                self.gains[i] = vm.strip[i].gain
                o = i+8
                self.mutes[o] = vm.bus[i].mute
                self.gains[o] = vm.bus[i].gain
            for i in range(8):
                self.solos[i] = vm.strip[i].solo
