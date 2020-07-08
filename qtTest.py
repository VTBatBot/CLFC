#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jun 23 12:33:23 2020

@author: devan
"""


# =============================================================================
# from pyqtgraph.Qt import QtGui, QtCore
# import numpy as np
# import pyqtgraph as pg
# from pyqtgraph.ptime import time
# import serial
# 
# app = QtGui.QApplication([])
# 
# p = pg.plot()
# p.setWindowTitle('live plot from serial')
# curve = p.plot()
# 
# data = [0]
# raw=serial.Serial('COM9', 115200)
# 
# 
# def update():
#     global curve, data
#     line = raw.readline()
#     if ("hand" in line):
#        line=line.split(":")
#        if len(line)==8:
#             data.append(float(line[4]))
#             xdata = np.array(data, dtype='float64')
#             curve.setData(xdata)
#             app.processEvents()
# 
# timer = QtCore.QTimer()
# timer.timeout.connect(update)
# timer.start(0)
# 
# if __name__ == '__main__':
#     import sys
#     if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
#         QtGui.QApplication.instance().exec_()
# =============================================================================

# =============================================================================
# from pyqtgraph.Qt import QtGui  # (the example applies equally well to PySide)
# import pyqtgraph as pg
# 
# ## Always start by initializing Qt (only once per application)
# app = QtGui.QApplication([])
# 
# ## Define a top-level widget to hold everything
# w = QtGui.QWidget()
# 
# ## Create some widgets to be placed inside
# btn = QtGui.QPushButton('press me')
# text = QtGui.QLineEdit('enter text')
# listw = QtGui.QListWidget()
# plot = pg.PlotWidget()
# 
# ## Create a grid layout to manage the widgets size and position
# layout = QtGui.QGridLayout()
# w.setLayout(layout)
# 
# ## Add widgets to the layout in their proper positions
# layout.addWidget(btn, 0, 0)   # button goes in upper-left
# layout.addWidget(text, 1, 0)   # text edit goes in middle-left
# layout.addWidget(listw, 2, 0)  # list widget goes in bottom-left
# layout.addWidget(plot, 0, 1, 3, 1)  # plot goes on right side, spanning 3 rows
# 
# ## Display the widget as a new window
# w.show()
# 
# ## Start the Qt event loop
# app.exec_()
# =============================================================================

# =============================================================================
# import sys
# import random
# from pyqtgraph.Qt import QtCore, QtWidgets, QtGui
# 
# class MyWidget(QtWidgets.QWidget):
#     def __init__(self):
#         super().__init__()
#         self.hello = ['Hello', "Goodbye"]
#         self.button = QtWidgets.QPushButton('Click me!')
#         self.text = QtWidgets.QLabel('Hello World!')
#         self.text.setAlignment(QtCore.Qt.AlignCenter)
#         
#         self.layout = QtWidgets.QVBoxLayout()
#         self.layout.addWidget(self.text)
#         self.layout.addWidget(self.button)
#         self.setLayout(self.layout)
#         
#         self.button.clicked.connect(self.magic)
#         
#     def magic(self):
#         self.text.setText(random.choice(self.hello))
#         
# if __name__ == "__main__":
#     app = QtWidgets.QApplication([sys])
#     widget = MyWidget()
#     widget.resize(800, 400)
#     widget.show()
#     
#     sys.exit(app.exec_())
# =============================================================================

from pyqtgraph.Qt import QtGui, QtCore
import pyqtgraph as pg
import numpy as np
from scipy.signal import spectrogram, butter, lfilter
import time


N = 10000 #number of data points per set
fs = 400000 # sampling frequency
lowcut = 20000 # low end of passed frequency range
highcut = 100000 # high end of passed frequency range

class Window(QtGui.QWidget):
    def __init__(self):
        self.width = 800 #width of the window
        self.height = 400 #height of the window
        super().__init__()
        self.resize(self.width, self.height)
        self.layout = QtGui.QGridLayout()
        self.setLayout(self.layout)
        self.addWidgets(self.layout)
        self.i = 0
        self.Type = 'sg'
        self.file = '20181111_121401467.txt'
        
    def addWidgets(self, layout):
        #create buttons and other widgets
        self.sgBtn = QtGui.QRadioButton('Spectrogram')
        self.smBtn = QtGui.QRadioButton('Spectrum')
        self.ogBtn = QtGui.QRadioButton('Oscillogram')
        self.startBtn = QtGui.QPushButton('Start/Stop')
        self.uploadBtn = QtGui.QPushButton('Upload Waveform')
        self.iterationInput = QtGui.QLineEdit('Enter number of iterations')
        self.iterationLabel = QtGui.QLabel('N: ')
        self.durationLabel = QtGui.QLabel('t: ')
        self.rateLabel = QtGui.QLabel('Fs: ')
        
        # create plots
        self.leftPlot = pg.PlotWidget()
        self.rightPlot = pg.PlotWidget()
        self.leftPlot.setFixedWidth(400)
        self.rightPlot.setFixedWidth(400)
        
        ## Add widgets to the layout in their proper positions
        layout.addWidget(self.startBtn, 3, 2)
        layout.addWidget(self.uploadBtn, 3, 0)
        layout.addWidget(self.iterationInput, 3, 1)
        layout.addWidget(self.sgBtn, 2, 3)
        layout.addWidget(self.smBtn, 3, 3)
        layout.addWidget(self.ogBtn, 4, 3)
        layout.addWidget(self.iterationLabel, 2, 4)
        layout.addWidget(self.durationLabel, 3, 4)
        layout.addWidget(self.rateLabel, 4, 4)
        self.layout.addWidget(self.leftPlot, 1, 0, 1, 2)
        self.layout.addWidget(self.rightPlot, 1, 2, 1, 3)
        
        # Connect buttons to methods
        self.startBtn.clicked.connect(self.run)
        
        self.sgBtn.toggled.connect(lambda:self.plotSelection('sg'))
        self.smBtn.toggled.connect(lambda:self.plotSelection('sm'))
        self.ogBtn.toggled.connect(lambda:self.plotSelection('og'))
                
    def amplitude(self, filename):
        self.data = []
        self.ldata = []
        self.rdata = []
        file = open(filename, newline='\n')
        for _ in file:
            i = int(_.strip())
            j = (((i - 0) * (1.65 - (-1.65))) / (4095-0))
            self.data.append(j)
        self.lavg = sum(self.data[0:N])/len(self.data)//2
        self.ravg = sum(self.data[N:])/len(self.data)//2
        for _ in range(len(self.data)//2):
            self.ldata.append(self.data[_] - self.lavg)
        for _ in range(len(self.data)//2, len(self.data)):
            self.rdata.append(self.data[_] - self.ravg)
        return self.ldata, self.rdata
    
    def butter_bandpass(self, lowcut, highcut, fs, order=5):
        nyq = 0.5 * fs
        low = lowcut / nyq
        high = highcut / nyq
        b, a = butter(order, [low, high], btype='band')
        return b, a
    
    def butter_bandpass_filter(self, data, lowcut, highcut, fs, order=5):
        b, a = self.butter_bandpass(lowcut, highcut, fs, order=order)
        y = lfilter(b, a, data)
        return y
    
    def build_og(self, Plot, Time, amp, side='left'):
        Time = Time[20:]
        amp = self.butter_bandpass_filter(amp, lowcut, highcut, fs)
        amp = amp[20:]
        Plot.plot(x=Time, y=amp)
        Plot.setLabel('bottom', 'Time [s]')
        if side=='left':
            Plot.setLabel('left', 'Amplitude')
        
    def ft(self, rate, setSize, amp):
        xf = np.linspace(0.0, 1.0/(2.0*rate), setSize//2)
        freq = np.abs(np.fft.rfft(amp))
        yf = freq[N//20:N//4] #from 20kHz to 100kHz
        xf = xf[N//20:N//4]
        base_dB = max(yf)
        dB = []
        for v in yf:
            dB.append(10*np.log10(v/base_dB)) #convert to dB scale
        return xf, dB
    
    def build_sm(self, Plot, rate, setSize, amp, side='left'):
        xf, yf = self.ft(rate, setSize, amp)
        Plot.plot(x=xf, y=yf)
        Plot.setLabel('bottom', 'Frequency')
        if side == 'left':
            Plot.set_ylabel('Amplitude')
    
    def build_sg(self, Plot, data, rate, side='left'):
        self.img = pg.ImageItem() #spectrogram is an image
        Plot.addItem(self.img) #add sg to widget
        
        #color mapping
        pos = np.array([0., 1., 0.5, 0.25, 0.75])
        color = np.array([[0,255,255,255], [255,255,0,255], [0,0,0,255], (0, 0, 255, 255), (255, 0, 0, 255)], dtype=np.ubyte)
        cmap = pg.ColorMap(pos, color)
        lut = cmap.getLookupTable(0.0, 1.0, 256)
        self.img.setLookupTable(lut)
        self.img.setLevels([-50,40])
        
        #scipy spectrogram returns 129x44 array of data
        self.img_array = np.zeros((129, 44))
        
        #scale the axes
        yscale = 1.0/(self.img_array.shape[1]/100000)
        xscale = 0.025/129
        self.img.scale(xscale, yscale)
        
        
    def run(self):
        tTotal = time.time()
        self.i += 1
        if self.i >= 4:
            self.i = 0
        if self.i == 0:
            self.file = '20181111_121401467.txt'
        elif self.i == 1:
            self.file = '20181111_121329107.txt'
        elif self.i == 2:
            self.file = '20181111_121335497.txt'
        elif self.i == 3:
            self.file = '20181111_121335587.txt'
        tAmp = time.time()
        lamp, ramp = self.amplitude(self.file)
        print("Amplitude: {}".format(time.time() - tAmp))
        if self.Type == 'sg':
            tSg = time.time()
            self.build_sg(self.leftPlot, lamp, fs, 'left')
            self.build_sg(self.rightPlot, ramp, fs, 'right')
            print("Spectrogram: {}".format(time.time() - tSg))
        elif self.Type == 'sm':
            tSm = time.time()
            lxf, lyf = self.ft(fs, N, lamp)
            rxf, ryf = self.ft(fs, N, ramp)
            self.build_sm(self.leftPlot, lxf, lyf, 'left')
            self.build_sm(self.rightPlot, rxf, ryf, 'right')
            print("Spectrum: {}".format(time.time() - tSm))
        elif self.Type == 'og':
            tOg = time.time()
            self.build_og(self.leftPlot, timeArray, lamp, 'left')
            self.build_og(self.rightPlot, timeArray, ramp, 'right')
            print("Oscillogram: {}".format(time.time() - tOg))
        tDraw = time.time()
        #canvas.draw()
        print("canvas.draw(): {}".format(time.time() - tDraw))
        print("Total: {}".format(time.time() - tTotal))
        
    def plotSelection(self, Type):
        lamp, ramp = self.amplitude(self.file)
        if Type == 'sg':
            self.build_sg(self.leftPlot, lamp, fs, 'left')
            self.build_sg(self.rightPlot, ramp, fs, 'right')
        if Type == 'sm':
            lxf, lyf = self.ft(fs, N, lamp)
            rxf, ryf = self.ft(fs, N, ramp)
            self.build_sm(self.leftPlot, lxf, lyf, 'left')
            self.build_sm(self.rightPlot, rxf, ryf, 'right')
        if Type == 'og':
            self.build_og(self.leftPlot, timeArray, lamp, 'left')
            self.build_og(self.rightPlot, timeArray, ramp, 'right')
        #canvas.draw()
            
    def waveformUpload(self):
        #filepath = filedialog.askopenfilename(initialdir='Coding/MuellerLab/BatBotGUI/', title='Select Waveform', filetypes=(("txt files","*.txt"),("all files","*.*")))
        filepath = QtGui.QFileDialog.getOpenFileName(self, 'Open file', '/Coding',"Text Files (*.txt *.*)")
        file = filepath
        print(file)
        return file

class SpectrogramWidget(pg.PlotWidget):
    def __init__(self):
        super().__init__()
        self.img = pg.ImageItem() 
        self.addItem(self.img)
        
        #color mapping
        pos = np.array([0., 1., 0.5, 0.25, 0.75])
        color = np.array([[0,255,255,255], [255,255,0,255], [0,0,0,255], (0, 0, 255, 255), (255, 0, 0, 255)], dtype=np.ubyte)
        cmap = pg.ColorMap(pos, color)
        lut = cmap.getLookupTable(0.0, 1.0, 256)
        self.img.setLookupTable(lut)
        self.img.setLevels([-50,40])
        
        #scipy spectrogram returns 129x44 array of data
        self.img_array = np.zeros((129, 44))
        
        #scale the axes
        yscale = 1.0/(self.img_array.shape[1]/100000)
        xscale = 0.025/129
        self.img.scale(xscale, yscale)
        self.setFixedWidth(400)
        
    def update(self, filename):
        data = []
        ldata = []
        file = open(filename, newline='\n')
        for _ in file:
            i = int(_.strip())
            #map values from 12 bit range to 3.3V
            j = (((i - 0) * (1.65 - (-1.65))) / (4095-0))
            data.append(j)
        #N=10000, only first half of 20000 is one ear
        lavg = sum(data[0:N])/len(data)//2
        for _ in range(len(data)//2):
            ldata.append(data[_] - lavg) #center data on 0
        ldata = np.array(ldata)
        
        #get spectrogram data in Sxx
        f, t, Sxx = spectrogram(ldata, fs)
        self.img_array = Sxx
        self.img.setImage(self.img_array, autoLevels=False)
        
        
N = 10000 #number of data points
fs = 400000 # sampling frequency
lowcut = 20000 # low end of passed frequency range
highcut = 100000 # high end of passed frequency range
T = 1 / fs; #sampling interval
beginTime = 0 #start time of sampling
endTime = 0.025 #end time of sampling
timeArray = np.arange(beginTime, endTime, T); #array of sample time points
windowWidth = 800 #width of the window
windowHeight = 400 #height of the window


if __name__ == '__main__':
    app = QtGui.QApplication([])
    w = Window()
    
# =============================================================================
#     lsg = SpectrogramWidget()
#     rsg = SpectrogramWidget()
#     w.layout.addWidget(lsg, 1, 0, 1, 2)
#     w.layout.addWidget(rsg, 1, 2, 1, 3)
#     lsg.update('20181111_121329107.txt')
#     rsg.update('20181111_121335497.txt')
# =============================================================================
    
    #connect start/stop button to updating spectrogram
    #w.startBtn.clicked.connect(lambda x:lsg.update('20181111_121335497.txt'))
    
    w.show()
    app.exec_()
    