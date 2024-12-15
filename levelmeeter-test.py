import customtkinter as ctk
import time
import voicemeeterlib
import numpy as np
from threading import Thread
from tkinter import Canvas

class App:
    def __init__(self, root, vm):
        self.root = root
        self.root.title("Level Meters")
        self.levels = [0] * 16
        self.delay = 0.05
        self.create_ui()
        self.running = True

        # Initialize Voicemeeter API

        self.vm = vm

        self.update_thread = Thread(target=self.update_levels)
        self.update_thread.start()

    def create_ui(self):
        self.canvas = Canvas(self.root, width=320, height=200, bg='white')
        self.canvas.grid(row=0, column=0, padx=5, pady=5, columnspan=16)

    def level_interpolation(self, db):
        level_list = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13]
        db_list = [-200, -100, -50, -40, -30, -20, -10, -5, -3, -1, 0, 1, 2]
        if db == -200:
            return 0
        return np.interp(db, db_list, level_list)

    def update_levels(self):
        try:
            while self.running:
                if self.vm.ldirty:
                    levels = [0] * 16
                    lnum = 0
                    for strip in self.vm.strip:
                        levels[lnum] = max(strip.levels.postfader)
                        lnum += 1
                    for bus in self.vm.bus:
                        levels[lnum] = max(bus.levels.all)
                        lnum += 1
                    self.levels = [min(13, max(0, self.level_interpolation(level))) for level in levels]
                    self.root.after(0, self.update_ui)
                    self.vm.clear_dirty()
                    self.delay = np.interp(max(levels), [-200, -100, 10], [0.2, 0.1, 0.01])
                time.sleep(self.delay)
        except KeyboardInterrupt:
            self.running = False
        except Exception as e:
            self.running = False
            time.sleep(1)
            raise e

    def update_ui(self):
        self.canvas.delete("all")
        bar_width = 15
        for i in range(16):
            lev = (int(np.interp(int(self.levels[i]), [0,1, 12,13], [0,1, 7,8])))
            height = 200 * lev/8
            x0 = i * (bar_width + 5)
            y0 = 200 - height
            x1 = x0 + bar_width
            y1 = 200
            
            if lev <= 4:
                color = "green"
            elif lev <= 7:
                color = "yellow"
            else:
                color = "red"

            self.canvas.create_rectangle(x0, y0, x1, y1, fill=color)
        print("Levels: " + " ".join(f"{level:.2f}" for level in self.levels))

    def on_closing(self):
        self.running = False
        self.vm.logout()  # Logout from Voicemeeter API
        print("Exiting... Goodbye!")
        self.root.destroy()

if __name__ == "__main__":
    KIND_ID = "potato"
    vm = voicemeeterlib.api(KIND_ID, ldirty=True, pdirty=True, ratelimit=100)
    vm.login()
    root = ctk.CTk()
    try:
        app = App(root, vm)
        root.protocol("WM_DELETE_WINDOW", app.on_closing)
    except Exception as e:
        vm.logout()
        time.sleep(1)
        print(e)
        print("Exiting... Initialization Error")
        quit()
    try:
        root.mainloop()
    except Exception as e:
        vm.logout()
        time.sleep(1)
        print(e)
        print("Exiting... Mainloop Error")
        quit()