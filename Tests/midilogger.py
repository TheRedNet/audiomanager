import mido

# get the input which contains "X-Touch"
try:
    input_name = [name for name in mido.get_input_names() if "X-Touch" in name][0]
except IndexError:
    print("No X-Touch input found")
    exit()
print(input_name)

with mido.open_input(input_name) as inport:
    for msg in inport:
        print(msg)