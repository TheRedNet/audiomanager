import voicemeeterlib
import pyaudio
import time
from threading import Thread
import mido
import logging
import tkinter as tk
from tkinter import scrolledtext
import pystray
from pystray import MenuItem as item
from PIL import Image, ImageDraw, ImageFont
import coloredlogs
import re
import os
from win11toast import toast


# Set to True to restart the script after closing the tray icon
reboot = False
# Configure logging to write to a file
logging.basicConfig(level=logging.INFO, 
                    format='[%(asctime)s][%(levelname)s][%(name)s] %(message)s', 
                    filename='logfile.log',
                    filemode='w'
                    )
coloredlogs.install(level='INFO', fmt='[%(asctime)s][%(levelname)s][%(name)s] %(message)s')

class Notificator:
    def __init__(self):
        self.logger = logging.getLogger(__class__.__name__)
        self.logger.info("Initializing...")

    def show_notification_thread(self, title, message):
        self.logger.debug(f"Showing notification: {title} - {message}")
        toast(title, message, duration="short")
        self.logger.debug("Notification shown.")
        
    def notification(self, title, message):
        notification_thread = Thread(target=self.show_notification_thread, args=(title, message))
        notification_thread.start()
        

class VoicemeeterHandler:
    def __init__(self, api_type):
        self.logger = logging.getLogger(__class__.__name__)
        self.logger.info("Initializing...")
        self.vm = voicemeeterlib.api(api_type)

    def connect(self):
        self.logger.info("Connecting to Voicemeeter...")
        self.vm.login()
        
    def disconnect(self):
        self.logger.info("Disconnecting from Voicemeeter...")
        self.vm.logout()
    
    def restart(self):
        self.logger.info("Restarting Voicemeeter...")
        self.vm.command.restart()
        

class FantomMidiHandler:
    def __init__(self):
        self.logger = logging.getLogger("FANTOM-08 MIDI Handler")
        self.logger.info("Initializing...")
        self.notify = Notificator()
        self.fantom_device = None
        self.fantom_output = None
        self.running = False
        self.inport = None
        self.outport = None
        self.current_program = 0
        self.current_bank_msb = 0
        self.current_bank_lsb = 0
        
    def is_running(self):
        return self.running
            
    def find_fantom(self):
        for port in mido.get_input_names():
            if 'FANTOM-06' in port and all(keyword not in port for keyword in ['MIDI', 'DAW']):
                return port
        return None
    
    def find_loop_output(self):
        for port in mido.get_output_names():
            if 'FANTOM filterd' in port:
                return port
        return None
    
    def check_fantom_devices(self):
        if self.running:
            return False
        self.fantom_device = self.find_fantom()
        self.fantom_output = self.find_loop_output()
        if self.fantom_device is None:
            self.logger.info("Fantom device not found. Please connect the Fantom to the computer.")
            return False
        if self.fantom_output is None:
            self.logger.info("Fantom loopmidi output not found. Please create a loopmidi port named 'FANTOM filterd'.")
            return False
        self.notify.notification("Fantom Connected", "Fantom device connected.")
        self.handle_midi()
        return True

    def check_if_fantom_disconnected(self):
        if self.find_fantom() is None and self.running:
            self.logger.info("Fantom device disconnected.")
            self.notify.notification("Fantom Disconnected", "Fantom device disconnected.")
            self.stop()
            return True
        return False
    
    def stop(self):
        if self.running:
            self.logger.info("Stopping...")
            self.running = False
            if self.inport:
                self.inport.close()
                self.inport = None
            if self.outport:
                self.outport.close()
                self.outport = None
    
    def handle_midi(self):
        if self.running:
            return
        self.running = True
        fantom_output = self.fantom_output
        if not fantom_output:
            self.logger.info("Fantom output port not set.")
            return
        
        try:
            self.outport = mido.open_output(fantom_output)
        except Exception as e:
            self.logger.error(f"Error opening MIDI output port: {e}")
            return
        
        self.current_program = 10880.001
        whitelisted_programs = [10880.001]
        whitelisted_types = ['note_on', 'note_off', 'control_change']
        
        def forward_midi(msg):
            if self.current_program in whitelisted_programs:
                self.outport.send(msg)
        
        def message_callback(msg):
            
            if msg.type == 'control_change':
                if msg.control == 0:  # Bank Select MSB
                    self.current_bank_msb = msg.value
                elif msg.control == 32:  # Bank Select LSB
                    self.current_bank_lsb = msg.value
            elif msg.type == 'program_change':
                
                prog = (msg.program + 1) / 1000.0
                
                
                self.current_program = (self.current_bank_msb << 7) + self.current_bank_lsb + prog
                self.logger.info(f"Current program: {self.current_program}")
            if msg.type in whitelisted_types:
                forward_midi(msg)
            self.logger.debug(f"MIDI Message: {msg}")
        
        try:
            self.inport = mido.open_input(self.fantom_device, callback=message_callback)
        except Exception as e:
            self.logger.error(f"Error opening MIDI input port: {e}")
        self.logger.info("FANTOM device connected.")




class AudioDeviceMonitor:
    def __init__(self, fantom_handler=FantomMidiHandler, voicemeeter_handler=VoicemeeterHandler):
        self.logger = logging.getLogger(__class__.__name__)
        self.logger.info("Initializing...")
        self.notify = Notificator()
        pii = pyaudio.PyAudio()
        self.previous_devices = pii.get_device_count()
        pii.terminate()
        self.running = False
        self.fantom_handler = fantom_handler
        self.vm_handler = voicemeeter_handler
        self.change_in_previous_check = False

    def get_device_count(self):
        return self.p.get_device_count()

            
    def monitor_devices(self):
        while self.running:
            self.logger.debug("Checking audio devices...")
            start_time = time.time()
            p = pyaudio.PyAudio()
            current_devices = p.get_device_count()
            p.terminate()
            end_time = time.time()
            wait_time = 10
            self.logger.debug(f"Current audio devices: {current_devices} (Time taken: {end_time - start_time:.4f}s)")
            if current_devices != self.previous_devices:
                self.logger.info("Audio device change detected!")
                
                if current_devices > self.previous_devices:
                    self.logger.info(f"New device connected.{current_devices} > {self.previous_devices}")
                    was_fantom = self.fantom_handler.check_fantom_devices()
                    if not self.change_in_previous_check and not was_fantom:
                        self.notify.notification("Audio Device Change", "New audio device connected.")
                    self.vm_handler.restart()
                    
                elif current_devices < self.previous_devices:
                    self.logger.info(f"Device disconnected.{current_devices} > {self.previous_devices}")
                    was_fantom = self.fantom_handler.check_if_fantom_disconnected()
                    if not self.change_in_previous_check and not was_fantom:
                        self.notify.notification("Audio Device Change", "Audio device disconnected.")
                        
                    
                
                self.previous_devices = current_devices
                self.change_in_previous_check = True
                wait_time = 10
            else:
                if self.change_in_previous_check:
                    self.change_in_previous_check = False
            
            frequency = 1
            while self.running and wait_time > 0:
                if wait_time % 5 == 0 and not self.change_in_previous_check:
                    if self.fantom_handler.is_running():
                        self.fantom_handler.check_if_fantom_disconnected()
                
                
                time.sleep(frequency)
                wait_time -= frequency

    def start_monitoring(self):
        self.logger.info("Starting monitoring thread...")
        self.running = True
        self.monitor_thread = Thread(target=self.monitor_devices)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()

    def stop_monitoring(self):
        self.logger.info("Stopping monitoring thread...")
        self.running = False
        if hasattr(self, 'monitor_thread'):
            self.monitor_thread.join()




class LogWindow:
    def __init__(self, root):
        self.logger = logging.getLogger(__class__.__name__)
        self.logger.info("Initializing...")
        self.root = root
        self.root.title("Log Window")
        self.text_area = scrolledtext.ScrolledText(root, wrap=tk.WORD, width=150, height=50)
        self.text_area.pack()
        self.log_level_var = tk.StringVar(value='INFO')
        self.log_level_menu = tk.OptionMenu(root, self.log_level_var, 'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL', command=self.change_log_level)
        self.log_level_menu.pack()
        self.auto_scroll_var = tk.BooleanVar(value=True)
        self.auto_scroll_check = tk.Checkbutton(root, text="Auto Scroll", variable=self.auto_scroll_var)
        self.auto_scroll_check.pack()
        self.line_count = 0
        self.update_log()
        self.closed = True

    def change_log_level(self, level):
        logging.getLogger().setLevel(level)
        coloredlogs.set_level(level)

    def update_log(self):
        try:
            with open('logfile.log', 'r') as f:
                f.seek(self.line_count)
                lines = f.readlines()
                for line in lines:
                    self.apply_coloredlogs(line)
                self.line_count = f.tell()
                if self.auto_scroll_var.get():
                    self.text_area.yview(tk.END)
        except FileNotFoundError:
            print("Log file not found.")
        except Exception as e:
            print(f"Error reading log file: {e}")
        self.root.after(1, self.update_log)

    def apply_coloredlogs(self, line):
        color_map = {
            'DEBUG': 'purple',
            'INFO': 'black',
            'WARNING': 'yellow',
            'ERROR': 'red',
            'CRITICAL': 'dark_red'
        }

        # Extract the log level from the line
        split_line = line.split(']')
        if len(split_line) < 3:
            return
        level = split_line[1].strip('[').strip()

        # Insert the line into the text area
        self.text_area.insert(tk.END, line , level)

        # Configure the tag for the log level
        self.text_area.tag_config(level, foreground=color_map.get(level, 'black'))
        #print(f"Inserted line with level {level} and color {color_map.get(level, 'black')}")  # Debug print
        
        
class TrayIcon:
    def __init__(self):
        self.logger = logging.getLogger(__class__.__name__)
        self.logger.info("Initializing...")
        self.icon = pystray.Icon("AudioManager")
        self.icon.menu = pystray.Menu(item('Log Window', self.show_log_window, default=True),item("Restart", self.on_restart), item('Exit', self.on_exit))
        self.icon.icon = self.create_image()
        self.icon.title = "Audio Manager"
        self.reboot = False
        self.exit = False
        self.lwh = None

    def on_restart(self, icon, item):
        self.logger.info("Restarting...")
        self.reboot = True
        self.on_exit(icon, item)
        
    
    def create_image(self):
        width = 64
        height = 64
        image = Image.new('RGB', (width, height), (30, 30, 30))
        dc = ImageDraw.Draw(image)
        font = ImageFont.truetype("arial", 50)  # Use a larger font size
        text = "AM"
        bbox = dc.textbbox((0, 0), text, font=font)
        textwidth = bbox[2] - bbox[0]
        textheight = bbox[3] - bbox[1]
        x = (width - textwidth) // 2
        y = (height - textheight) // 2
        dc.text((x, y), text, fill="red", font=font)
        return image

    def on_exit(self, icon, item):
        self.exit = True
        icon.stop()
        self.close_log_window()

    def show_log_window(self, icon, item):
        if self.lwh is None:
            self.logger.info("Creating log window...")
            root = tk.Tk()
            self.lwh = LogWindow(root)
            self.lwh.closed = False
            root.protocol("WM_DELETE_WINDOW", self.on_close_log_window)
            root.mainloop()
        else:
            self.close_log_window()
    
    def on_close_log_window(self):
        self.lwh.closed = True
        self.lwh.root.destroy()
        self.lwh = None
    
    def close_log_window(self):
        if self.lwh:
            self.lwh.root.destroy()
            self.lwh = None
    
    def run(self):
        self.icon.run()


def main():
    logger = logging.getLogger("Main")
    logger.info("Starting...")
    vmh = VoicemeeterHandler('potato')
    vmh.connect()
    fantom_handler = FantomMidiHandler()
    monitor = AudioDeviceMonitor(fantom_handler, vmh)
    monitor.start_monitoring()
    fantom_handler.check_fantom_devices()
    tray_icon = TrayIcon()    

    def exit():
        logger.info("Stopping...")
        monitor.stop_monitoring()
        tray_icon.icon.stop()
        vmh.disconnect()
        fantom_handler.stop()
        tray_icon.close_log_window()
        logger.info("Stopped.")
    
    # Keep the main thread running
    try:
        tray_icon.run()
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt detected.")
    if not tray_icon.exit:
        logger.info("Tray icon closed")
    reboot = tray_icon.reboot
    exit()
    return reboot
    
    

# Main
if __name__ == "__main__":
    reboot = main()
    if reboot:
        os.system('.\\Scripts\\python.exe audiomanager.py')
