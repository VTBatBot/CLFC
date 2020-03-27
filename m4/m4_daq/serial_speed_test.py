"""
Performs a single run, plotting the data and showing timing info
"""

import matplotlib.pyplot as plt
import serial
import time

def start_run(s):
    """
    Initiates a run
    """
    s.write([0x10])

def wait_for_run(s):
    """
    Blocks until the run is complete
    """
    waiting = True
    while waiting:
        s.write([0x20])
        
        r = s.read(1)
        if r == b'\x01':
            waiting = False

def get_data(s, ch):
    """
    Retreives and pre-processes data from a channel
    """
    s.write([0x30 | ch])
    
    num_pages = s.read(1)[0]
    raw_data = s.read(num_pages * 8192)
    return [3.3/4096 * ((y << 8) | x) for x, y in zip(raw_data[::2], raw_data[1::2])]

s = serial.Serial('COM7')

start = time.time_ns()

start_run(s)
wait_for_run(s)

dump = time.time_ns()

left = get_data(s, ch=0)
right = get_data(s, ch=1)

end = time.time_ns()

print('Start to run completion:', dump - start)
print('Start to data retreival:', end - start)

plt.plot(left)
plt.plot(right)
plt.ylabel('Amplitude (V)')
plt.xlabel('Sample #')
plt.show()
