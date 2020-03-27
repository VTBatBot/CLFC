import matplotlib.pyplot as plt
from datetime import datetime
import serial
import serial.tools.list_ports
import struct
import time
import math
import os

# COM port of Arduino Due; leave None for cross-platform auto-detection
DDG_PORT = 'COM5'

# Number of runs between plot updates. Plotting almost doubles the
# duration of each run, so keep this large
PLOT_INTERVAL = 1

# Number of milliseconds for each run, used to add artificial delays after runs.
# Set to 0 to achieve the maximum collection rate
RUN_DURATION = 0

class DDG:
    """
    Interface to an Arduino Due running DAQ DAQ Goose

    Bare minimum example (collect a single run):

        ddg = DDG()
        left, right = ddg.collect_data()
        plt.plot(left)
        plt.plot(right)
        plt.show()

    """
        
    FIRMWARE_VERSION = (0, 2)
    
    def __init__(self, port=None):
        """
        Connect to a device

        :param port: optional, COM port of Arduino Due
        """
        
        # Try to deduce the serial port
        #if not port:
        #    port = self.guess_port()

        # Connect to the device
        self.ser = serial.Serial(port)

        # Attempt to reset the device
        self.reset()
        
        # Handshake with the device and get its version
        version = self.get_version()
        if version != self.FIRMWARE_VERSION:
            raise Exception('The Due is running an incompatible firware version '
                            f'(expected {self.FIRMWARE_VERSION}, got {version})')

        print(f'Connected to Due on {port}')

    @staticmethod
    def guess_port():
        """
        Discover any locally connected Arduino Dues

        :return: COM port name of discovered Due
        """
        
        # Try to detect any Arduino Dues by USB IDs
        available_ports = serial.tools.list_ports.comports()
        possible_ports = [port.device for port in available_ports \
                          if (port.vid == 9025 and port.pid == 62)]

        # Yell at the user if no Due was found
        if not any(possible_ports):
            # Warn them if they are using the wrong port
            prog_port_connected = any(1 for port in available_ports \
                                      if (port.vid == 9025 and port.pid == 61))
            if prog_port_connected:
                raise Exception('Connected to the wrong Due port: use the outer (native) port')
                
            raise Exception('Due not found: verify that it is properly connected')

        return possible_ports[0]

    @staticmethod
    def create_packet(op, body=None):
        body_len = len(body) if body else 0
        packet = bytearray(5 + body_len)

        packet[0:5] = struct.pack('<BI', op, body_len)
        if body:
            packet[5:] = body

        return packet

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

    def read_header(self, expected_opcode=None, expected_len=None):
        """
        Read a packet header from serial; throws when expected values are
        different than actual

        :param expected_opcode: optional, opcode of packet to receive
        :para expected_len: optional, length of packet to receive
        """
        
        op, resp_len = struct.unpack('<BI', self.ser.read(size=5))
        if (expected_opcode is not None and op != expected_opcode) or \
           (expected_len is not None and resp_len != expected_len):
            raise Exception('Unexpected packet! Reset the Due')

        return resp_len

    def read_body(self, resp_len):
        """
        Read a fixed number of bytes from serial
        """
        
        return bytearray(self.ser.read(size=resp_len))

    def read(self, expected_opcode=None, expected_len=None):
        """
        Read a packet header and body; throws when expected values are
        different than actual

        :param expected_opcode: optional, opcode of packet to receive
        :param expected_len, optional, length of packet to receive
        """
        
        return self.read_body(self.read_header(expected_opcode, expected_len))

    def get_version(self):
        """
        Get the firmware version

        :return: firmware version major and minor
        """
        
        self.write(self.create_packet(0))
        resp = self.read(expected_opcode=0x80, expected_len=2)
        return struct.unpack('<BB', resp)

    def collect_data(self, dynamic=False, dynamic_delayed=False):
        """
        Perform a full data collection run

        :param dynamic: ears should be moved before data collection
        :param dynamic_delayed: add a slight delay before dynamic data collection
        :return: collected data split into separate channels
        """

        opcode = 2
            
        ddg.write(ddg.create_packet(opcode))
        ddg.read(expected_opcode=0x80|opcode, expected_len=0)

        # Wait for collection to finish and read in data
        raw_data = ddg.read(expected_opcode=0x82, expected_len=2*45000)

        # The two channels are interleaved and split across two little endian bytes;
        # we need to join the bytes and split the two channels
        joined_data = [(3.3/4095 * ((y << 8) | x)) for x, y in zip(raw_data[::2], raw_data[1::2])]
        return joined_data
    

if __name__ == '__main__':
    # Connect to Arduino Due
    ddg = DDG(port=DDG_PORT)
    
    print('-' * 60)

    print('Enter name of file: ', end='')
    file_name = input()

    print('-' * 60)    
    print(f'Saving to {os.path.abspath(file_name)}')
    print('-' * 60)

    data = ddg.collect_data()

    with open(file_name, 'w') as f:
        for data_point in data:
            f.write('{}\n'.format(data_point))

    print('Done!')
    
    """
    # Loop data collection indefinitely; press Ctrl-C and close the plot
    # to stop elegantly
    while True:
        try:
            run_start = time.time_ns()

            # Collect data
            


            # Periodically plot an incoming signal
        

            # Clear previous lines (for speed)
            ax1.lines = []

            # Plot
            ax1.plot(left)

            # Show the plot without blocking (there's no separate UI
            # thread)
            plt.show(block=False)
            plt.pause(0.001)

        except KeyboardInterrupt:
            print('Interrupted')
            break
    """
