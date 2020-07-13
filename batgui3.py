#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jun 23 12:33:23 2020

@author: devan
"""



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
        super().__init__()
        
        #constants
        self.width = 800 #width of the window
        self.height = 400 #height of the window
        self.N = 10000 #number of data points
        self.fs = 400000 # sampling frequency
        self.lowcut = 20000 # low end of passed frequency range
        self.highcut = 100000 # high end of passed frequency range
        self.T = 1 / fs; #sampling interval
        self.beginTime = 0 #start time of sampling
        self.stopTime = 0.025 #stop time of sampling
        
         # strings for labels
        self.nString = 'N: '
        self.tString = 't: '
        self.fsString = 'Fs: '
        self.fpsString = 'fps: '
        
        # variables
        self.i = 0
        self.Type = 'sg'
        self.file = '20181111_121401467.txt'
        self.useUpload = False
        self.startTime = 0
        self.endTime = 0
        self.fps = 0.0
        self.timeArray = np.arange(self.beginTime, self.stopTime, self.T); #array of sample time points
        
        #timer for automatic execution
        self.timer = QtCore.QTimer()
        self.timer.setInterval(500) #in ms
        #self.timer.timeout.connect(self.fpsUpdate)
        self.timer.start()
        
        
        self.resize(self.width, self.height)
        self.layout = QtGui.QGridLayout()
        self.setLayout(self.layout)
        self.addWidgets(self.layout)
        self.sgBtn.toggle()
        
        
    def addWidgets(self, layout):
        #create buttons and other widgets
        self.sgBtn = QtGui.QRadioButton('Spectrogram')
        self.smBtn = QtGui.QRadioButton('Spectrum')
        self.ogBtn = QtGui.QRadioButton('Oscillogram')
        self.startBtn = QtGui.QPushButton('Start/Stop')
        self.uploadBtn = QtGui.QPushButton('Upload Waveform')
        #self.iterationInput = QtGui.QLineEdit('Enter number of iterations')
        self.iterationSelect = QtGui.QComboBox(self)
        self.iterationSelect.addItems(['1','2','3','4','5'])
        
       
        
        #labels
        self.iterationLabel = QtGui.QLabel(self.nString)
        self.durationLabel = QtGui.QLabel(self.tString)
        self.rateLabel = QtGui.QLabel(self.fsString)
        self.fpsLabel = QtGui.QLabel(self.fpsString)
        
        
        
        # create plots
        self.leftPlot = pg.PlotWidget()
        self.rightPlot = pg.PlotWidget()
        self.leftPlot.setFixedWidth(400)
        self.rightPlot.setFixedWidth(400)
        
        ## Add widgets to the layout in their proper positions
        # left a gap on column 3
        layout.addWidget(self.startBtn, 3, 2)
        layout.addWidget(self.uploadBtn, 3, 1)
        #layout.addWidget(self.iterationInput, 3, 1)
        layout.addWidget(self.iterationSelect, 2, 6)
        layout.addWidget(self.sgBtn, 2, 4)
        layout.addWidget(self.smBtn, 3, 4)
        layout.addWidget(self.ogBtn, 4, 4)
        layout.addWidget(self.iterationLabel, 2, 5)
        layout.addWidget(self.durationLabel, 3, 5)
        layout.addWidget(self.rateLabel, 4, 5)
        layout.addWidget(self.fpsLabel, 4, 6)
        self.layout.addWidget(self.leftPlot, 1, 1, 1, 2)
        self.layout.addWidget(self.rightPlot, 1, 3, 1, 4)
        
        # Connect buttons to methods
        self.startBtn.clicked.connect(self.run)
        self.uploadBtn.clicked.connect(self.waveformUpload)
        self.sgBtn.toggled.connect(self.plotSelection)
        self.smBtn.toggled.connect(self.plotSelection)
        self.ogBtn.toggled.connect(self.plotSelection)
        
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
        Plot.clear()
        Time = Time[20:]
        amp = self.butter_bandpass_filter(amp, lowcut, highcut, fs)
        amp = amp[20:]
        Plot.plot(x=Time, y=amp)
        Plot.setLabel('bottom', 'Time [s]')
        if side=='left':
            Plot.setLabel('left', 'Amplitude')
        
    def ft(self, amp, rate, setSize):
        xf = np.linspace(0.0, 1.0/(2.0*rate), setSize//2)
        freq = np.abs(np.fft.rfft(amp))
        yf = freq[N//20:N//4] #from 20kHz to 100kHz
        xf = xf[N//20:N//4]
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
        
        #color mapping
        pos = np.array([0., 1., 0.5, 0.25, 0.75])
        color = np.array([[0,255,255,255], [255,255,0,255], [0,0,0,255], (0, 0, 255, 255), (255, 0, 0, 255)], dtype=np.ubyte)
        #color = np.array([[128,0,128,255], [255,255,0,255], [0,255,255,255], (0,255,0,255), (0,0,255,255)], dtype=np.ubyte)
        cmap = pg.ColorMap(pos, color)
        lut = cmap.getLookupTable(0.0, 1.0, 256)
        self.img.setLookupTable(lut)
        self.img.setLevels([-50,40])
        
        #scipy spectrogram returns 129x44 array of data
        rows = 52
        columns = 44
        self.img_array = np.zeros((rows, columns))
        
        #scale the axes
        yscale = 1.0/(columns/200)#scale is wrong
        xscale = 0.025/rows
        self.img.scale(xscale, yscale)
        
        data = np.array(data)
        f, t, Sxx = spectrogram(data, rate)
        self.img_array = Sxx[13:65]
        self.img.setImage(self.img_array, autoLevels=True)
        
        Plot.setLabel('bottom', 'Time [s]')
        if side == 'left':
            Plot.setLabel('left', 'Frequency [kHz]')
        
    def run(self):
        #self.labels()
        self.startTime = time.time()
        self.jStr = self.iterationSelect.currentText()
        self.j = int(self.jStr)
        self.i = self.j
        #self.i += 1
        if self.useUpload == False:
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
        if self.sgBtn.isChecked():
            tSg = time.time()
            self.build_sg(self.leftPlot, lamp, fs, 'left')
            self.build_sg(self.rightPlot, ramp, fs, 'right')
            print("Spectrogram: {}".format(time.time() - tSg))
        elif self.smBtn.isChecked():
            tSm = time.time()
            self.build_sm(self.leftPlot, lamp, fs, N, 'left')
            self.build_sm(self.rightPlot, ramp, fs, N, 'right')
            print("Spectrum: {}".format(time.time() - tSm))
        elif self.ogBtn.isChecked():
            tOg = time.time()
            self.build_og(self.leftPlot, self.timeArray, lamp, 'left')
            self.build_og(self.rightPlot, self.timeArray, ramp, 'right')
            print("Oscillogram: {}".format(time.time() - tOg))
        self.useUpload = False
        self.endTime = time.time()
        self.tTotal = self.endTime - self.startTime
        print("Total: {}".format(self.tTotal))
        self.fps = 1/self.tTotal
        self.labels()
        self.fpsUpdate() #temporary
        self.startTime = self.endTime
        
        
    def plotSelection(self):
        lamp, ramp = self.amplitude(self.file)
        if self.sgBtn.isChecked():
            self.build_sg(self.leftPlot, lamp, fs, 'left')
            self.build_sg(self.rightPlot, ramp, fs, 'right')
        if self.smBtn.isChecked():
            self.build_sm(self.leftPlot, lamp, fs, N, 'left')
            self.build_sm(self.rightPlot, ramp, fs, N, 'right')
        if self.ogBtn.isChecked():
            self.build_og(self.leftPlot, self.timeArray, lamp, 'left')
            self.build_og(self.rightPlot, self.timeArray, ramp, 'right')
            
    def waveformUpload(self):
        filepath = QtGui.QFileDialog.getOpenFileName(self, 'Open file', 
                                                     '/home/devan/Coding/MuellerLab/BatBotGUI',
                                                     "Text Files (*.txt)") #change filepath for Jetson
        self.file = filepath[0]
        self.useUpload = True
        
    def labels(self):
        self.nString = 'N: {}'.format(self.iterationSelect.currentText())
        self.tString = 't: {:.4f}'.format(self.tTotal)
        self.fsString = 'Fs: {}'.format(str(self.fs))
        self.iterationLabel.setText(self.nString)
        self.durationLabel.setText(self.tString)
        self.rateLabel.setText(self.fsString)
        
    def fpsUpdate(self):
        self.fpsString = 'fps: {:.2f}'.format(self.fps)
        self.fpsLabel.setText(self.fpsString)
  



if __name__ == '__main__':
    app = QtGui.QApplication([])
    w = Window()
    w.show()
    app.exec_()
    