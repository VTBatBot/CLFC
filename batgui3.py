#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jun 23 12:33:23 2020

@author: devan
"""


import os
from pyqtgraph.Qt import QtGui, QtCore
from PyQt5.QtCore import Qt
import pyqtgraph as pg
import numpy as np
from scipy.signal import spectrogram, butter, lfilter
import time
import colormaps as cm
from enum import Enum

os.environ['DISPLAY']=':0' # fixes display error with launch on startup

class SizePolicy(Enum):
    FIX = QtGui.QSizePolicy.Fixed
    MIN = QtGui.QSizePolicy.Minimum
    MAX = QtGui.QSizePolicy.Maximum
    PREF = QtGui.QSizePolicy.Preferred
    EXPAND = QtGui.QSizePolicy.Expanding
    MINEXPAND = QtGui.QSizePolicy.MinimumExpanding
    IGNORED =QtGui.QSizePolicy.Ignored

class Align(Enum):
    CENTER = QtCore.Qt.AlignCenter
    LEFT = QtCore.Qt.AlignLeft
    RIGHT = QtCore.Qt.AlignRight
    
class Window(QtGui.QWidget): 
    def __init__(self):
        super().__init__()
        pg.setConfigOptions(imageAxisOrder='row-major') 
            # flips image correct way
        
        ## constants
        self.width = 800        # width of the window
        self.height = 430       # height of the window
        self.plotWidth = 390    # width of each plot
        self.N = 10000          # number of data points
        self.fs = 400e3         # sampling frequency in Hz
        self.lowcut = 20e3      # low end of passed frequency range
        self.highcut = 100e3    # high end of passed frequency range
        self.T = 1 / self.fs;   # sampling interval
        self.beginTime = 0      # start time of sampling
        self.stopTime = 0.025   # stop time of sampling
        
        ## strings for labels
        self.nString = 'N: '
        self.tString = 't: '
        self.fsString = 'Fs: '
        self.fpsString = 'fps: '
        self.nMaxString = 'Nmax: '
        
        ## variables
        self.file = '20181111_121335587.txt'
        self.useUpload = False
        self.startTime = 0
        self.endTime = 0
        self.fps = 0.0
        self.tPassed = 0
        self.timeArray = np.arange(self.beginTime, self.stopTime, self.T); 
            # array of sample time points
        self.n = 0
            
        
        
        ## Widgets
        self.sgBtn = QtGui.QRadioButton('Spectrogram')
        self.smBtn = QtGui.QRadioButton('Spectrum')
        self.ogBtn = QtGui.QRadioButton('Oscillogram')
        self.startBtn = QtGui.QPushButton('Start/Stop')
        self.startBtn.setFixedWidth(self.plotWidth//3)
        self.uploadBtn = QtGui.QPushButton('Upload Waveform')
        self.uploadBtn.setFixedWidth(self.plotWidth//3)
        self.iterationInput = QtGui.QLineEdit('N iterations')
        
        ## Connect buttons to methods
        self.startBtn.clicked.connect(self.run)
        self.uploadBtn.clicked.connect(self.waveformUpload)
        self.sgBtn.toggled.connect(self.plotSelection)
        self.smBtn.toggled.connect(self.plotSelection)
        self.ogBtn.toggled.connect(self.plotSelection)
        
        ## rectangle - not working yet
        self.scene = QtGui.QGraphicsScene(self)
        self.view = QtGui.QGraphicsView(self.scene)
        self.statusRect = QtGui.QGraphicsRectItem(QtCore.QRectF(0,0,800,20))
        self.scene.addItem(self.statusRect)
        
            #(left, top, width, height)
        #self.iterationSelect = QtGui.QComboBox(self)
        #self.iterationSelect.addItems(['5','10','50','100','500','inf'])
        
        ## labels
        self.iterationLabel = QtGui.QLabel(self.nString)
        self.durationLabel = QtGui.QLabel(self.tString)
        self.rateLabel = QtGui.QLabel(self.fsString)
        self.fpsLabel = QtGui.QLabel(self.fpsString)
        self.nMaxLabel = QtGui.QLabel(self.nMaxString)
        
        ## create plots
        self.leftPlot = pg.PlotWidget()
        self.rightPlot = pg.PlotWidget()
        self.leftPlot.setFixedWidth(self.plotWidth)
        self.rightPlot.setFixedWidth(self.plotWidth)
        
        #timer for automatic execution
        self.timer = QtCore.QTimer()
        self.timer.setInterval(500) #in ms
        #self.timer.timeout.connect(self.fpsUpdate)
        self.timer.start()
        
        ## create the layout
        self.resize(self.width, self.height)
        self.layout = QtGui.QGridLayout()
        self.setLayout(self.layout)
        self.addWidgets(self.layout)
        # window starts with sgBtn toggled so spectrogram appears
        self.sgBtn.toggle()
        self.labels()
        
        
        
        
    def addWidgets(self, layout):
        MIN = SizePolicy.MIN.value
        
        self.iterationInput.setSizePolicy(MIN, MIN)
        self.view.setSizePolicy(MIN,MIN)
        
        #self.sgBtn.setSizePolicy(MIN, MIN) |
        #self.smBtn.setSizePolicy(MIN, MIN) # dont seem to change anything
        #self.ogBtn.setSizePolicy(MIN, MIN) |

        
        
        ## Alignments
        left = Align.LEFT.value
        right = Align.RIGHT.value
        
        ## Add widgets to the layout in their proper positions
        #iterationLayout = QtGui.QGridLayout()
        #layout.addLayout(iterationLayout, 2, 6)
        # left a gap on column 1, 3, 5
        layout.addWidget(self.startBtn, 4, 2)
        layout.addWidget(self.uploadBtn, 4, 0)
        layout.addWidget(self.iterationInput, 3, 8)
        #layout.addWidget(self.iterationSelect, 2, 8)
        layout.addWidget(self.sgBtn, 3, 4, 1, 1, alignment=left)
        layout.addWidget(self.smBtn, 4, 4, 1, 1, alignment=left)
        layout.addWidget(self.ogBtn, 5, 4, 1, 1, alignment=left)
        layout.addWidget(self.iterationLabel, 3, 6, alignment=left)
        layout.addWidget(self.nMaxLabel, 3, 7, alignment=right)
        layout.addWidget(self.durationLabel, 4, 6)
        #self.durationLabel.setHorizontalStretch(3)
        layout.addWidget(self.rateLabel, 5, 6)
        layout.addWidget(self.fpsLabel, 5, 8)
        layout.addWidget(self.leftPlot, 1, 0, 1, 5)
        layout.addWidget(self.rightPlot, 1, 5, 1, 5)
        #layout.addWidget(self.view, 2, 0, 1, 20) #the view is too big
        
        
        
        
        #layout.setContentsMargins(5, 0, 5, 5)
        #print(layout.spacing())
        
        
    def amplitude(self, filename):
        self.data = []
        self.ldata = []
        self.rdata = []
        file = open(filename, newline='\n')
        for _ in file:
            i = int(_.strip())
            j = (((i - 0) * (1.65 - (-1.65))) / (4095-0))
            self.data.append(j)
        self.lavg = sum(self.data[0:self.N])/len(self.data)//2
        self.ravg = sum(self.data[self.N:])/len(self.data)//2
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
        Plot.clear()
        Time = Time[20:]
        amp = self.butter_bandpass_filter(amp, self.lowcut, 
                                          self.highcut, self.fs)
        amp = amp[20:]
        Plot.plot(x=Time, y=amp)
        Plot.setLabel('bottom', 'Time [s]')
        if side=='left':
            Plot.setLabel('left', 'Amplitude')
        
    def ft(self, amp, rate, setSize):
        xf = np.linspace(0.0, 1.0/(2.0*rate), setSize//2)
        freq = np.abs(np.fft.rfft(amp))
        yf = freq[self.N//20:self.N//4] #from 20kHz to 100kHz
        xf = xf[self.N//20:self.N//4]
        base_dB = max(yf)
        dB = []
        for v in yf:
            dB.append(10*np.log10(v/base_dB)) #convert to dB scale
        return xf, dB
    
    def build_sm(self, Plot, amp, rate, setSize, side='left'):
        Plot.clear()
        xf, yf = self.ft(amp, rate, setSize)
        xf = xf[10:]
        yf = yf[10:]
        Plot.plot(x=xf, y=yf)
        Plot.setLabel('bottom', 'Frequency')
        if side == 'left':
            Plot.setLabel('left', 'Amplitude')
    
    def build_sg(self, Plot, data, rate, side='left'):
        Plot.clear()
        self.img = pg.ImageItem() #spectrogram is an image
        Plot.addItem(self.img) #add sg to widget
        
        ## color mapping
        step = 1/63
        #pos = np.linspace(0, 1, 63)
        pos = np.arange(0.0, 1.0, step)
        color = cm.jet #63x4 array of rgba values
        
        cmap = pg.ColorMap(pos, color)

        lut = cmap.getLookupTable(0.0, 1.0, 256)
        self.img.setLookupTable(lut)
        
        ## creating the spectrogram
        data = np.array(data)
        # nperseg & noverlap estimated by looking at spectrogram
        # most efficient nperseg & nfft values are powers of 2
        # spectrogram returns to Sxx as (frequency x time)
        ## Change values for limit freq range ##
        f, t, Sxx = spectrogram(data, rate, 'blackman',
                                nperseg=256, noverlap=220, nfft=512)
                                #'blackman', nperseg=512, noverlap=400)
                                
        # necessary for image to appear correctly, estimated
        Sxx = Sxx * 5e8
        
        ## cutting the frequency range to 20kHz-100kHz
        fRes = (f[1] - f[0])/2
        fLowcut = self.binarySearch(f, self.lowcut, fRes)
        fHighcut = self.binarySearch(f, self.highcut, fRes)
        #Sxx = Sxx[fLowcut:fHighcut]
        #f = f[fLowcut:fHighcut]
        
        ## empty array for the image
        rows = len(f)
        columns = len(t)
        self.img_array = np.zeros((rows, columns))
        
        ## scale the axes
        yscale = 100/columns # scale is wrong
        xscale = 25/rows
        self.img.scale(xscale, yscale)
        
        
        self.img_array = Sxx
        self.img.setImage(self.img_array, autoLevels=False, levels=(-10,60))
            #level values are estimated from appearance
        
        Plot.setLabel('bottom', 'Time [ms]')
        if side == 'left':
            Plot.setLabel('left', 'Frequency [kHz]')
        
    def run(self):
        self.running = True
        #self.labels()
        startTime = time.time()
        jStr = self.iterationInput.text()
        try:
            self.j = int(jStr)
        except ValueError:
            self.j = 0
        self.i = 0
        while self.n < self.j:
            tStart = time.time()
            if self.useUpload == False:
                if self.i > 3:
                    self.i = 0
                if self.i == 0:
                    self.file = '20181111_121401467.txt'
                elif self.i == 1:
                    self.file = '20181111_121329107.txt'
                elif self.i == 2:
                    self.file = '20181111_121335497.txt'
                elif self.i == 3:
                    self.file = '20181111_121335587.txt'
            self.i += 1
            self.n += 1
            #tAmp = time.time()
            lamp, ramp = self.amplitude(self.file) # if useUpload True, file is
                # set in the waveformUpload function
                
            #print("Amplitude: {}".format(time.time() - tAmp))
            if self.sgBtn.isChecked():
                #tSg = time.time()
                self.build_sg(self.leftPlot, lamp, self.fs, 'left')
                self.build_sg(self.rightPlot, ramp, self.fs, 'right')
                #print("Spectrogram: {}".format(time.time() - tSg))
            elif self.smBtn.isChecked():
                #tSm = time.time()
                self.build_sm(self.leftPlot, lamp, self.fs, self.N, 'left')
                self.build_sm(self.rightPlot, ramp, self.fs, self.N, 'right')
                #print("Spectrum: {}".format(time.time() - tSm))
            elif self.ogBtn.isChecked():
                #tOg = time.time()
                self.build_og(self.leftPlot, self.timeArray, lamp, 'left')
                self.build_og(self.rightPlot, self.timeArray, ramp, 'right')
                #print("Oscillogram: {}".format(time.time() - tOg))
            self.tPassed = time.time() - startTime
            tOnce = time.time() - tStart
            self.labels()
            self.fps = 1/tOnce
            self.fpsUpdate() #temporary
            app.processEvents()
        self.n = 0
        self.useUpload = False
        endTime = time.time()
        self.tTotal = endTime - startTime
        print("Total: {}".format(self.tTotal))
        startTime = endTime
        self.running = False
        
    def sampleRun(self):
        jStr = self.iterationInput.text()
        try:
            self.j = int(jStr)
        except ValueError:
            self.j = 0
        self.i = 0
        n = 0
        while n < self.j:
            tStart = time.time()
            if self.useUpload == False:
                if self.i > 3:
                    self.i = 0
                if self.i == 0:
                    self.file = '20181111_121401467.txt'
                elif self.i == 1:
                    self.file = '20181111_121329107.txt'
                elif self.i == 2:
                    self.file = '20181111_121335497.txt'
                elif self.i == 3:
                    self.file = '20181111_121335587.txt'
            self.i += 1
            n += 1
            #tAmp = time.time()
            lamp, ramp = self.amplitude(self.file) # if useUpload True, file is
                # set in the waveformUpload function
            Plot = self.leftPlot
            amp = lamp
            Time = self.timeArray
            Plot.clear()
            #Time = Time[20:]
            amp = self.butter_bandpass_filter(amp, self.lowcut, 
                                              self.highcut, self.fs)
            #amp = amp[20:]
            Plot.plot(x=Time, y=amp)
            Plot.setLabel('bottom', 'Time [s]')
            Plot.setLabel('left', 'Amplitude')
            app.processEvents()
            self.labels()
        
    def plotSelection(self):
        lamp, ramp = self.amplitude(self.file)
        if self.sgBtn.isChecked():
            self.build_sg(self.leftPlot, lamp, self.fs, 'left')
            self.build_sg(self.rightPlot, ramp, self.fs, 'right')
        if self.smBtn.isChecked():
            self.build_sm(self.leftPlot, lamp, self.fs, self.N, 'left')
            self.build_sm(self.rightPlot, ramp, self.fs, self.N, 'right')
        if self.ogBtn.isChecked():
            self.build_og(self.leftPlot, self.timeArray, lamp, 'left')
            self.build_og(self.rightPlot, self.timeArray, ramp, 'right')
            
    def waveformUpload(self):
        filepath = QtGui.QFileDialog.getOpenFileName(self, 'Open file', 
                                                     '/home/devan/BatBot',
                                                     "Text Files (*.txt)") #change filepath for Jetson
        self.file = filepath[0]
        self.useUpload = True
        
    def labels(self):
        self.nString = 'N: {}'.format(self.n)
        minutes = self.tPassed//60
        sec = self.tPassed % 60
        self.tString = 't: {m:.0f} min {sec:.2f} sec'.format(m=minutes,sec=sec)
        self.fsString = 'Fs: {:.0f} kHz'.format(self.fs/1000)
        self.iterationLabel.setText(self.nString)
        self.durationLabel.setText(self.tString)
        self.rateLabel.setText(self.fsString)
        
    def fpsUpdate(self):
        self.fpsString = 'fps: {:.1f}'.format(self.fps)
        self.fpsLabel.setText(self.fpsString)
        
    def binarySearch(self, data, target, res):
        first = 0
        last = len(data) - 1
        index = -1
        while (first <= last) and (index == -1):
            mid = (first+last)//2
            if data[mid] >= target - res and data[mid] <= target + res:
                index = mid
            else: 
                if target < data[mid]:
                    last = mid - 1
                else: 
                    first = mid + 1
        return index


if __name__ == '__main__':
    app = QtGui.QApplication([])
    w = Window()
    w.show()
    import sys
    if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        QtGui.QApplication.instance().exec_()
    
