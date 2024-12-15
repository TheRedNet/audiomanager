import customtkinter as ctk
import time
import voicemeeterlib
import numpy as np
from threading import Thread
from tkinter import Canvas

class App:
    def __init__(self, root, vm):
        self.canvas_height = 500
        self.bar_count = 16
        self.bar_width = 35
        self.bar_spacing = 10
        self.top_margin = 20
        self.section_devider_width = 3
        
        self.root = root
        self.root.title("Level Meters")
        self.levels = [-200] * 16
        self.delay = 0.05
        self.running = True
        
        # Decay
        self.decay_list = [0] * 16
        self.prev_levels = [0] * 16
        self.decay_speed = 100
        self.real_levels = [0] * 16

        # Initialize Voicemeeter API

        self.vm = vm

        self.create_ui()
        self.root.after(0, self.update_levels)
        self.root.after(1000, self.decay)

    def set_decay_speed(self, speed):
        self.decay_speed = int(speed)
        self.decay_label.configure(text=f"Decay Speed (ms): {self.decay_speed}")
        
    def decay(self):
        print(self.decay_list)
        for i in range(16):
            if self.decay_list[i] < 13:
                self.decay_list[i] += 1
        self.root.after(int(self.decay_speed), self.decay)
    
    def create_ui(self):
        self.canvas = Canvas(self.root, width=(self.bar_count*(self.bar_spacing+self.bar_width)+2*self.bar_spacing), height=self.canvas_height+self.top_margin+18, bg='black', highlightthickness=0)
        self.canvas.grid(row=0, column=0, padx=0, pady=0, columnspan=16)
        self.decay_slider = ctk.CTkSlider(self.root, from_=50, to=1000, command=self.set_decay_speed)
        self.decay_slider.set(100)
        self.decay_slider.grid(row=2, column=0, padx=0, pady=0, columnspan=16)
        self.decay_label = ctk.CTkLabel(self.root, text=f"Decay Speed (ms): {self.decay_speed}") 
        self.decay_label.grid(row=1, column=0, padx=0, pady=0, columnspan=16)
        

    def level_interpolation(self, db):
        if db == -200:
            return 0
        db = round(db, 0)
        db_list = [-200, -60, -50, -40, -35, -30, -25, -20, -15, -10, -5, 0, 5]
        for i in range(1,len(db_list)):
            if db > db_list[i-1] and db <= db_list[i]:
                return i
        return 13

    def update_levels(self):
        if self.vm.ldirty:
            levels = [0] * 16
            lnum = 0
            for strip in self.vm.strip:
                levels[lnum] = max(strip.levels.postfader)
                lnum += 1
            for bus in self.vm.bus:
                levels[lnum] = max(bus.levels.all)
                lnum += 1
            
            
            for i in range(16):
                if self.level_interpolation(levels[i]) > self.level_interpolation(self.prev_levels[i])-self.decay_list[i]:
                    self.decay_list[i] = 0
                    self.levels[i] = levels[i]
            self.prev_levels = self.levels
            self.real_levels = levels
            self.update_ui()
            self.vm.clear_dirty()
            self.delay = np.interp(max(levels), [-200, -100, 10], [0.3, 0.2, 0.05])
        self.root.after(int(self.delay*1000), self.update_levels)
        #time.sleep(0.3)
        

    def update_ui(self):
        sections = 8
        self.canvas.delete("all")
        bar_width = self.bar_width
        extra_space = self.bar_spacing
        for i in range(16):
            lev = (int(np.interp(int(min(13, max(0, self.level_interpolation(self.levels[i])-self.decay_list[i]))), [0,1, 12,13], [0,1, sections-1, sections])))
            height = self.canvas_height * lev/sections
            if i == 8:
                extra_space += self.bar_spacing
            x0 = i * (bar_width + self.bar_spacing) + extra_space
            y0 = self.canvas_height - height + self.top_margin
            x1 = x0 + bar_width
            y1 = self.canvas_height + self.top_margin
            
            if lev <= 4:
                color = "green"
            elif lev <= 7:
                color = "yellow"
            else:
                color = "red"
            self.canvas.create_rectangle(x0, y0, x1, y1, fill=color, outline=color)
            
            if lev > 7:
                h = self.canvas_height * 7/sections
                y = self.canvas_height - h + self.top_margin
                self.canvas.create_rectangle(x0, y, x1, y1, fill="yellow", outline="yellow")
            if lev > 4:
                h = self.canvas_height * 4/sections
                y = self.canvas_height - h + self.top_margin
                self.canvas.create_rectangle(x0, y, x1, y1, fill="green", outline="green")
            
            
            self.canvas.create_text(x0 + bar_width/2, y1+1, text=f"{i}", anchor="n", fill="white")
            self.canvas.create_text(x0 + bar_width/2, y1-15, text=f"{lev}", anchor="n", fill="black")
            if lev == 0:
                self.canvas.create_text(x0 + bar_width/2, y0-2, text=f"{self.levels[i]:.1f}", anchor="s", fill="white")
            else:
                self.canvas.create_text(x0 + bar_width/2, y0+12+self.section_devider_width, text=f"{self.real_levels[i]:.1f}", anchor="s", fill="black")
        for i in range(1, sections):
            y = self.canvas_height * i/sections + self.top_margin - self.section_devider_width/2
            self.canvas.create_line(0, y, self.bar_count*(self.bar_spacing+self.bar_width)+2*self.bar_spacing, y, fill="black", width=self.section_devider_width)
        x = 8 * (bar_width + self.bar_spacing) + self.bar_spacing
        self.canvas.create_line(x, 5, x, self.canvas_height+self.top_margin+10, fill="white")
        #print("Levels: " + " ".join(f"{level:.1f}" for level in self.levels))

    def on_closing(self):
        self.running = False
        self.vm.logout()  # Logout from Voicemeeter API
        print("Exiting... Goodbye!")
        self.root.destroy()
        print("Exiting... Root Destroyed")
        quit()

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
    #vm.logout()