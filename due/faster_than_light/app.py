import sys
import time
from pyqtgraph.Qt import QtCore, QtGui
import numpy as np
import pyqtgraph as pg
import time, threading, sys
import serial

DURATION = 3

SERIAL_PORT = 'COM5'

class SerialReader(threading.Thread):
    def __init__(self, port, chunkSize=1024, chunks=5000):
        threading.Thread.__init__(self)
        # circular buffer for storing serial data until it is
        # fetched by the GUI
        self.buffer = np.zeros(chunks*chunkSize, dtype=np.uint16)
       
        self.chunks = chunks        # number of chunks to store in the buffer
        self.chunkSize = chunkSize  # size of a single chunk (items, not bytes)
        self.ptr = 0                # pointer to most (recently collected buffer index) + 1
        self.port = port            # serial port handle
        self.sps = 0.0              # holds the average sample acquisition rate
        self.exitFlag = False
        self.exitMutex = threading.Lock()
        self.dataMutex = threading.Lock()
       
    def run(self):
        exitMutex = self.exitMutex
        dataMutex = self.dataMutex
        buffer = self.buffer
        port = self.port
        count = 0
        sps = None
        lastUpdate = pg.ptime.time()
       
        while True:
            # see whether an exit was requested
            with exitMutex:
                if self.exitFlag:
                    break
           
            # read one full chunk from the serial port
            data = port.read(self.chunkSize*2)
            # convert data to 16bit int numpy array
            data = np.frombuffer(data, dtype=np.uint16)
           
            # keep track of the acquisition rate in samples-per-second
            count += self.chunkSize
            now = pg.ptime.time()
            dt = now-lastUpdate
            if dt > 1.0:
                # sps is an exponential average of the running sample rate measurement
                if sps is None:
                    sps = count / dt
                else:
                    sps = sps * 0.9 + (count / dt) * 0.1
                count = 0
                lastUpdate = now
               
            # write the new chunk into the circular buffer
            # and update the buffer pointer
            with dataMutex:
                buffer[self.ptr:self.ptr+self.chunkSize] = data
                self.ptr = (self.ptr + self.chunkSize) % buffer.shape[0]
                if sps is not None:
                    self.sps = sps
               
               
    def get(self, num, downsample=1):
        with self.dataMutex:  # lock the buffer and copy the requested data out
            ptr = self.ptr
            if ptr-num < 0:
                data = np.empty(num, dtype=np.uint16)
                data[:num-ptr] = self.buffer[ptr-num:]
                data[num-ptr:] = self.buffer[:ptr]
            else:
                data = self.buffer[self.ptr-num:self.ptr].copy()
            rate = self.sps

        rate = max(rate, 1)
       
        data = data.astype(np.float32) * (3.3 / 2**12)
        if downsample > 1:  # if downsampling is requested, average N samples together
            data = data.reshape(num//downsample,downsample).mean(axis=1)
            num = data.shape[0]
            return np.linspace(0, (num-1)/rate*downsample, num), data, rate
        else:
            return np.linspace(0, (num-1)/rate, num), data, rate
   
    def exit(self):
        """ Instruct the serial thread to exit."""
        with self.exitMutex:
            self.exitFlag = True

class App(QtGui.QMainWindow):
    def __init__(self, parent=None):
        super(App, self).__init__(parent)

        #### Create Gui Elements ###########
        self.mainbox = QtGui.QWidget()
        self.setCentralWidget(self.mainbox)
        self.mainbox.setLayout(QtGui.QVBoxLayout())

        self.canvas = pg.GraphicsLayoutWidget()
        self.mainbox.layout().addWidget(self.canvas)

        #  line plot
        self.plot = self.canvas.addPlot()
        self.h2 = self.plot.plot(pen='y')

        self.plot.setLabel('left', 'Voltage (V)')
        self.plot.setLabel('bottom', 'Time (s)')

        # Add grid
        self.plot.showGrid(x = True, y = True, alpha = 0.3)  

        # Add x-axis labels
        ticks = []
        num = int(DURATION*1024/1.535)
        for t in np.arange(0, DURATION, 0.5):
            ticks.append((num * (DURATION-t)/DURATION, '{:.02}'.format(t)))
        self.plot.getAxis('bottom').setTicks([ticks])

        # Start reading from serial
        self._update()

    def _update(self):
        num = int(DURATION*1024/1.535)
        t, v, r = thread.get(1000*num, downsample=1000)
        self.h2.setData(v)

        QtCore.QTimer.singleShot(1, self._update)

if __name__ == '__main__':
    s = serial.Serial(SERIAL_PORT)
               
    thread = SerialReader(s)
    thread.start()

    app = QtGui.QApplication(sys.argv)
    thisapp = App()
    thisapp.show()
    sys.exit(app.exec_())
