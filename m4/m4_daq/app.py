import matplotlib.pyplot as plt
from datetime import datetime
import numpy as np
import serial
import serial.tools.list_ports
import struct
import time
import math
import os

# COM port of the M4; leave None for cross-platform auto-detection
PORT = None

# Number of runs between plot updates. Plotting almost doubles the
# duration of each run, so keep this large
PLOT_INTERVAL = 1

class BatBot:
    """
    Bare minimum example (collect a single run):

        bb = BatBot()
        left, right = bb.collect_data()
        plt.plot(left)
        plt.plot(right)
        plt.show()

    """
        
    FIRMWARE_VERSION = (0, 2)
    
    def __init__(self, port=None):
        """
        Connect to a device

        :param port: optional, COM port of M4
        """
        
        # Try to deduce the serial port
        if not port:
            port = self.guess_port()

        # Connect to the device
        self.ser = serial.Serial(port)

        # Attempt to reset the device
        self.reset()

        print(f'Connected to M4 on {port}')

    @staticmethod
    def guess_port():
        """
        Discover any locally connected M4s

        :return: COM port name of discovered M4
        """
        
        VID = 0x239a
        PID = 0x8031

        # Try to detect any M4s by USB IDs
        available_ports = serial.tools.list_ports.comports()
        possible_ports = [port.device for port in available_ports \
                          if (port.vid == VID and port.pid == PID)]

        # Yell at the user if no M4 was found
        if not any(possible_ports):
            raise Exception('M4 not found: verify that it is properly connected')

        return possible_ports[0]

    def reset(self):
        """
        Trigger a hardware reset using the serial's DTR; highly
        dependent on hardware configuration
        """
        
        self.ser.setDTR(False)
        time.sleep(1)
        self.ser.flushInput()
        self.ser.setDTR(True)

    def write(self, packet):
        self.ser.write(packet)

    def read(self, length):
        return self.ser.read(length)

    def _start_run(self):
        self.write([0x10])

    def _wait_for_run_to_complete(self):
        while True:
            self.write([0x20])

            if self.read(1) == b'\x01':
                return

    def _get_data(self, ch):
        self.write([0x30 | ch])
        
        num_pages = self.read(1)[0]
        raw_data = self.read(num_pages * 8192)
        return [((y << 8) | x) for x, y in zip(raw_data[::2], raw_data[1::2])]

    def collect_data(self):
        """
        Perform a full data collection run

        :return: collected data split into separate channels
        """

        self._start_run()

        self._wait_for_run_to_complete()

        left_ch = self._get_data(ch=0)
        right_ch = self._get_data(ch=1)

        return (left_ch, right_ch)
        
if __name__ == '__main__':
    # Connect to M4
    bb = BatBot(port=PORT)
    
    print('-' * 60)

    # Ask for name of output folder
    print('Enter name of folder: ', end='')
    folder_name = input()

    print('-' * 60)    
    print(f'Saving to {os.path.abspath(folder_name)}')
    print('-' * 60)
    
    # Create a subplot for each channel
    f, (ax1, ax2) = plt.subplots(1, 2, sharey=True)
    ax1.set_xlim([0, 10000])
    ax1.set_ylim([0, 4096])
    ax2.set_xlim([0, 10000])
    ax2.set_ylim([0, 4096])

    num_runs = 0
    trial_start = datetime.now()

    # Loop data collection indefinitely; press Ctrl-C and close the plot
    # to stop elegantly
    while True:
        try:
            run_start = time.time_ns()

            # Collect data
            left, right = bb.collect_data()

            # Create output folder and file
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S%f')[:-3]
            output_folder = folder_name + '/'
            output_filename = timestamp + '.txt'
            output_path = output_folder + output_filename
            if not os.path.exists(output_folder):
                os.makedirs(output_folder)

            # Write output
            with open(output_path, 'w') as f:
                for data in left + right:
                    f.write('{}\n'.format(data))

            num_runs += 1

            # Periodically plot an incoming signal
            if num_runs % PLOT_INTERVAL == 0:
                elapsed = datetime.now() - trial_start

                # Leave a status message
                ax1.set_title('{} runs - {}'.format(num_runs, str(elapsed)[:-7]))
                ax2.set_title('{} runs/min'.format(int(num_runs/max(elapsed.seconds,1)*60)))

                # Clear previous lines (for speed)
                ax1.lines = ax2.lines = []

                # Plot
                ax1.plot(left)
                ax2.plot(right)

                # Show the plot without blocking (there's no separate UI
                # thread)
                plt.show(block=False)
                plt.pause(0.001)

        except KeyboardInterrupt:
            print('Interrupted')
            break

    print('-' * 60)

    elapsed = datetime.now() - trial_start
    print(f'{num_runs} runs took {elapsed}')
