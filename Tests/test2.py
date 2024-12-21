import mido
import numpy as np
print(mido.get_input_names())
import random
from threading import Thread
import time

# get the input which contains "X-Touch-Ext"
try:
    input_name = [name for name in mido.get_input_names() if "X-Touch-Ext" in name][0]
except IndexError:
    print("No X-Touch-Ext input found")
    exit()
print(input_name)
# get the output which contains "X-Touch-Ext"
try:
    output_name = [name for name in mido.get_output_names() if "X-Touch-Ext" in name][0]
except IndexError:
    print("No X-Touch-Ext output found")
    exit()
#input = mido.open_input(input_name)

output = mido.open_output(output_name)
input = mido.open_input(input_name)

def display_msg(dpstring, offset):
    prefix = [0xF0, 0x00, 0x00, 0x66, 0x15, 0x12, offset]
    suffix = [0xF7]
    for i in range(7-len(dpstring)):
        dpstring += " "
    dpbytes = [ord(c) for c in dpstring]
    msgbytearray = prefix + dpbytes + suffix
    return mido.Message.from_bytes(msgbytearray)




fader_db = [-70, -30, -10, 0, 10]
fader_pos = [-8192, -4464, 0, 4384, 8188]

level_meter_db = [-60, -30, -10, 10]
#map to 1-12
level_meter_pos = [1, 2, 6, 14]

#reset X-Touch
reset_msg = mido.Message.from_hex("F0 00 00 66 15 63 F7")
print(reset_msg.hex())
output.send(reset_msg)


display_color_msg = mido.Message.from_hex("F0 00 00 66 15 72 01 01 02 03 04 05 06 07 F7")
print(display_color_msg.hex())
output.send(display_color_msg)

sysex_prefix = [0xF0, 0x00, 0x00, 0x66, 0x15, 0x12, 0x00]
sysex_suffix = [0xF7]

mackie_string = [ord(" ")] * 7 * 16
msgbytearray = sysex_prefix + mackie_string + sysex_suffix

display_hello_msg = mido.Message.from_bytes(msgbytearray)
print(display_hello_msg.hex())
output.send(display_hello_msg)

sysex_general_prefix = [0xF0, 0x00, 0x00, 0x66, 0x15]
sysex_general_suffix = [0xF7]

#for i in range(0, 7):
#    channel_meter_mode = mido.Message.from_bytes(sysex_general_prefix + [0x20, i] + [0b00000001<<i] + sysex_general_suffix)
#    print(channel_meter_mode)
#    output.send(channel_meter_mode)

position = [0, 0, 0, 0, 0, 0, 0, 0]
state = [0] * 32

run_level_meeter = True 

def random_level_meter():
    while run_level_meeter:
        print_string = ""
        for i in range(8):
            level_meter = random.randint(1, 13)
            if level_meter == 13: level_meter = 14
            output.send(mido.Message("aftertouch",value=level_meter+16*i))
            #print(f"Level Meter: {level_meter}")
        time.sleep(0.5)



level_meter_thread = Thread(target=random_level_meter)
level_meter_thread.start()


with input:
    for msg in input:
        if msg.type == "pitchwheel":
            output.send(msg)
            in_db = np.interp(msg.pitch, fader_pos, fader_db)
            print(f"Pitch: {msg.pitch} dB: {in_db}")
            # level meter
            level_meter = int(np.interp(in_db, level_meter_db, level_meter_pos)) + (16*msg.channel)
            output.send(mido.Message("aftertouch",value=level_meter))
            displaymsgdb = f"{in_db:.1f}dB"
            displaymsg = display_msg(displaymsgdb, (msg.channel*7)+8*7 ) 
            output.send(displaymsg)
        elif msg.type == "control_change":
            if 16 <= msg.control <= 23:
                channel = msg.control - 16 - 1
                if channel == -1:
                    channel = 7
                ticks = msg.value % 64
                if msg.value > 64:
                    ticks = -ticks
                position[channel] += ticks
                position[channel] = max(0, min(127, position[channel]))
                

                output.send(mido.Message("control_change",control=channel+48,value=position[channel]))
                print(f"Channel: {channel} Position: {position[channel]} Value: ")
                displaymsg = display_msg(f"{channel} {position[channel]}", channel*7)
                output.send(displaymsg)
        elif msg.type == "note_on" and msg.velocity > 0 and msg.note == 31:
            color_array = [1, 2, 3, 4, 5, 6, 7,8]
            for i in range(8):
                rng_color = random.randint(1, 7)
                color_array[i] = rng_color
            prefix = [0xF0, 0x00, 0x00, 0x66, 0x15, 0x72]
            suffix = [0xF7]
            msgbytearray = prefix + color_array + suffix
            display_color_msg = mido.Message.from_bytes(msgbytearray)
            print(display_color_msg.hex())
            output.send(display_color_msg)
        elif msg.type == "note_on" and 0 <= msg.note <= 31:
            if msg.velocity == 127:
                output.send(mido.Message("note_on",note=msg.note,velocity=1))
            else:
                state[msg.note] = (state[msg.note] + 1) % 3
                if state[msg.note] == 1:
                    output.send(mido.Message("note_on",note=msg.note,velocity=127))
                elif state[msg.note] == 2:
                    output.send(mido.Message("note_on",note=msg.note,velocity=1))
                else:
                    output.send(mido.Message("note_on",note=msg.note,velocity=0))

                
                
            

        else:
            print(msg)



                
            
