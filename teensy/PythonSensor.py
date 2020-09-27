import struct 
import serial   #first make sure that you have the serial library

PORT = 'COM7'  # Set this to whatever port is coming up in your device manager
BAUD = 9600    # This needs to be set to whatever the Teensy's baud rate is
VERBOSE = 0    # Keep this as 0 or your command prompt will be flooded with debug messages
TIMEOUT = 30   # Put this somewhere not too low, not way too high...


# Create an OBJECT of the Serial() Class called "serial_device".
# This object represents a serial connection that can read and write.
serial_device = serial.Serial()  
serial_device.port = PORT
serial_device.baudrate = BAUD
serial_device.timeout= TIMEOUT
print("Serial Parameter")


# Use the open() METHOD of the Serial() OBJECT to initiate the serial connection
serial_device.open()
data_in = 0
print("Beginning While Loop")

# Initiate an infinite loop where Python is constantly listening for new bytes of data over the Serial() Object.
while True:
        
    if serial_device.in_waiting > 0:
        data_in = serial_device.read(2)   #The argument for the read() method is the number of bytes to read.
        data_in = struct.unpack("<h", data_in)[0]
        #print(data_in)
    # do stuff with your data here
        if data_in == 12345:
                data_package = serial_device.read(4*128)  #Information from the arduino code
                k = 0
                m = 0
                left_data = [0]*128
                right_data = [0]*128
                for ndatapack in range(0, 128*2):
                     data_in = serial_device.read(2)
                     int_data = struct.unpack("<h", data_in)[0]
                     if (ndatapack%2)==0:
                         left_data[k] = data_package[ndatapack]
                         k=k+1
                     else:
                         right_data[m] = data_package[ndatapack]
                         m=m+1
                     print(left_data)
                     print(right_data)











                     
