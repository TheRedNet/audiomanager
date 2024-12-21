import pyaudio
import time
# List all audio devices
time_list = []
for i in range(50):
    start_time = time.time()
    p = pyaudio.PyAudio()
    init_time = time.time() - start_time
    p.get_device_count()
    count_time = time.time() - start_time - init_time
    p.terminate()
    term_time = time.time() - start_time - init_time - count_time
    time_list.append((init_time, count_time, term_time))
    print(f"Init: {init_time}, Count: {count_time}, Term: {term_time}")

max_init = max([t[0] for t in time_list])
max_count = max([t[1] for t in time_list])
max_term = max([t[2] for t in time_list])
avg_init = sum([t[0] for t in time_list]) / len(time_list)
avg_count = sum([t[1] for t in time_list]) / len(time_list)
avg_term = sum([t[2] for t in time_list]) / len(time_list)
print(f"Max Init: {max_init}, Max Count: {max_count}, Max Term: {max_term}")
print(f"Avg Init: {avg_init}, Avg Count: {avg_count}, Avg Term: {avg_term}")