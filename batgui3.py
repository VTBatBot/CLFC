#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jun 23 12:33:23 2020

@author: devan
"""


import os
from PyQt5 import QtGui, QtCore
from PyQt5.QtCore import Qt
import pyqtgraph as pg
import numpy as np
from scipy.signal import spectrogram, butter, lfilter
import time
import colormaps as cm
from enum import Enum
import sip

os.environ['DISPLAY']=':0' # fixes display error with launch on startup

class SizePolicy(Enum):
    FIX = QtGui.QSizePolicy.Fixed
    MIN = QtGui.QSizePolicy.Minimum
    MAX = QtGui.QSizePolicy.Maximum
    PREF = QtGui.QSizePolicy.Preferred
    EXPAND = QtGui.QSizePolicy.Expanding
    MINEXPAND = QtGui.QSizePolicy.MinimumExpanding

class Align(Enum):
    CENTER = QtCore.Qt.AlignCenter
    LEFT = QtCore.Qt.AlignLeft
    RIGHT = QtCore.Qt.AlignRight
    
    
class Window(QtGui.QWidget): 
    def __init__(self):
        super().__init__()
        pg.setConfigOptions(imageAxisOrder='row-major') 
            # flips image correct way
            
        self.setWindowIcon(QtGui.QIcon('VT_BIST_LOGO.ico'))
        self.setWindowTitle('BatBot')
        
        ## constants
        self.width = 800        # width of the window
        self.height = 430       # height of the window
        self.plotWidth = 390    # width of each plot
        self.N = int(10e3)           # number of data points
        self.fs = int(400e3)         # sampling frequency in Hz
        #self.T = 1 / self.fs;   # sampling interval
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
        #self.startTime = 0
        #self.endTime = 0
        self.fps = 0.0          # frames per second
        self.tPassed = 0
        # array of sample time points
        self.timeArray = np.linspace(self.beginTime, self.stopTime, self.fs); 
        self.n = 0
        self.sigWindow = 'blackman'     # default signal window
        self.lowcut = 20e3      # low end of passed frequency range
        self.highcut = 100e3    # high end of passed frequency range
        self.nperseg = 256      # number of freq points per time segment
        self.noverlap = self.nperseg//5 # overlap of time segments
        self.nfft = self.nperseg       # not really sure
        
        ## create plots
        self.leftPlot = pg.PlotWidget()     # widget to display plots
        self.rightPlot = pg.PlotWidget()
        self.leftPlot.setEnabled(False)     # disables plot interaction
        self.rightPlot.setEnabled(False)
        self.leftPlot.setFixedWidth(self.plotWidth)
        self.rightPlot.setFixedWidth(self.plotWidth)
        
# =============================================================================
#         #timer for automatic execution
#         self.timer = QtCore.QTimer()
#         self.timer.setInterval(500) #in ms
#         #self.timer.timeout.connect(self.fpsUpdate)
#         self.timer.start()
# =============================================================================
        
        ## create the main grid layout
        self.resize(self.width, self.height)
        self.mainLayout = QtGui.QGridLayout()
        self.setLayout(self.mainLayout)
        
        ## add plots
        self.mainLayout.addWidget(self.leftPlot, 0, 0)
        self.mainLayout.addWidget(self.rightPlot, 0, 1)
        
        self.displayInfo() # create the info display
        # window starts with sgBtn toggled so spectrogram appears
        self.sgBtn.toggle()
        self.labels() # self defined method
        
    def displayInfo(self):
        ## delete settings widgets if they exist
        try:
            self.mainLayout.removeWidget(self.settingsWidget)
            sip.delete(self.settingsWidget)
            self.settingsWidget = None
        except AttributeError:
            pass
        
        ## creates the information display
        # groups all the information into one widget
        self.infoWidget = QtGui.QWidget()
        self.mainLayout.addWidget(self.infoWidget, 1, 0, 1, 2)
        self.infoLayout =  QtGui.QGridLayout()
        self.infoWidget.setLayout(self.infoLayout)
        #self.infoWidget.setStyleSheet('margin:0;'\
        #                             'background-color:none')
            # removes borders for all contained items
        #self.infoWidget.setFlat(True)
        
        ## Widgets
        # spectrogram toggle
        self.sgBtn = QtGui.QRadioButton('Spectrogram')
        self.sgBtn.toggled.connect(self.plotSelection)
        
        # spectrum toggle
        self.smBtn = QtGui.QRadioButton('Spectrum')
        self.smBtn.toggled.connect(self.plotSelection)
        
        # oscillogram toggle
        self.ogBtn = QtGui.QRadioButton('Oscillogram')
        self.ogBtn.toggled.connect(self.plotSelection)
        
        # Start/Stop button
        self.startBtn = QtGui.QPushButton('Start/Stop')
        self.startBtn.setFixedWidth(self.plotWidth//4)
        self.startBtn.setStyleSheet("background-color: green")
        self.startBtn.clicked.connect(self.run)
        self.startBtn.setCheckable(True)
        
        # upload waveform button
        self.uploadBtn = QtGui.QPushButton('Upload Waveform')
        self.uploadBtn.setFixedWidth(3*self.plotWidth//10)
        self.uploadBtn.clicked.connect(self.waveformUpload)
        
        # blank input for number of echoes
        self.iterationInput = QtGui.QLineEdit('N_echoes')
        MIN = SizePolicy.MIN.value
        self.iterationInput.setSizePolicy(MIN, MIN)
        
        # button for the settings menu
        self.menuBtn = QtGui.QPushButton('Settings')
        self.menuBtn.clicked.connect(self.displaySettings)
        
        
        ## Labels
        self.iterationLabel = QtGui.QLabel(self.nString)
        self.durationLabel = QtGui.QLabel(self.tString)
        #self.durationLabel.setHorizontalStretch(3)
        self.rateLabel = QtGui.QLabel(self.fsString)
        self.fpsLabel = QtGui.QLabel(self.fpsString)
        self.nMaxLabel = QtGui.QLabel(self.nMaxString)
        
        #self.sgBtn.setSizePolicy(MIN, MIN) |
        #self.smBtn.setSizePolicy(MIN, MIN) # dont seem to change anything
        #self.ogBtn.setSizePolicy(MIN, MIN) |
        
        ## Alignments
        left = Align.LEFT.value
        right = Align.RIGHT.value
        
        ## Add widgets to the layout in their proper positions
        # left a gap on column 1, 3, 5
        self.infoLayout.addWidget(self.uploadBtn, 4, 0)
        self.infoLayout.addWidget(self.startBtn, 4, 2)
        self.infoLayout.setColumnMinimumWidth(3, 20)
        self.infoLayout.addWidget(self.sgBtn, 3, 4, 1, 1, alignment=left)
        self.infoLayout.addWidget(self.smBtn, 4, 4, 1, 1, alignment=left)
        self.infoLayout.addWidget(self.ogBtn, 5, 4, 1, 1, alignment=left)
        self.infoLayout.setColumnMinimumWidth(5, 20)
        self.infoLayout.addWidget(self.iterationLabel, 3, 6, alignment=left)
        self.infoLayout.addWidget(self.durationLabel, 4, 6)
        self.infoLayout.addWidget(self.rateLabel, 5, 6)
        self.infoLayout.addWidget(self.nMaxLabel, 3, 7, alignment=right)
        self.infoLayout.addWidget(self.iterationInput, 3, 8)
        self.infoLayout.addWidget(self.fpsLabel, 4, 8)
        self.infoLayout.addWidget(self.menuBtn, 5, 8)
        
        #self.infoLayout.setContentsMargins(5, 0, 5, 5)
        
        
    def displaySettings(self):
        ## remove information widgets
        self.mainLayout.removeWidget(self.infoWidget)
        sip.delete(self.infoWidget)
        self.infoWidget = None
        
        # save all current data for reversion
        self.quicksave()
        
        ## widget for grouping items w/ grid layout
        self.settingsWidget = QtGui.QWidget()
        self.mainLayout.addWidget(self.settingsWidget, 1, 0, 1, 2)
        self.settingsLayout = QtGui.QGridLayout()
        self.settingsWidget.setLayout(self.settingsLayout)
        
        # revert changes button
        revertBtn = QtGui.QPushButton('Revert')
        revertBtn.clicked.connect(self.revert)
        
        # return to information display
        closeBtn = QtGui.QPushButton('Close')
        closeBtn.clicked.connect(self.displayInfo)
        
        # dropdown box for signal windows
        self.windowSelect = QtGui.QComboBox()
        self.windowSelect.addItems(['blackman','hamming',
                              'hann','bartlett','flattop','parzen',
                              'bohman','blackmanharris','nuttall',
                              'barthann','boxcar','triang'])
        self.windowSelect.currentTextChanged.connect(self.saveSettings)
        windowLabel = QtGui.QLabel('Window:')
        
        # dropdown box for length of window (powers of 2)
        self.lengthSelect = QtGui.QComboBox()
        self.lengthSelect.addItems(['128','256','512','1024','2048',
                                    '4096','8192'])
        self.lengthSelect.setCurrentText('256')
        self.lengthSelect.currentTextChanged.connect(self.saveSettings)
        self.lengthLabel = QtGui.QLabel("Length:")
        
        # slider for adjusting overlap (as % of window length)
        self.noverlapSlider = QtGui.QSlider(orientation=2) # 2=vertical
        self.noverlapSlider.setRange(20, 99)
        #self.noverlapSlider.setSingleStep(int(self.nperseg/10)) #unknown
        self.noverlapSlider.setPageStep(10)
        self.noverlapSlider.setSliderPosition(100*self.noverlap/self.nperseg)
        self.noverlapSlider.valueChanged.connect(self.saveSettings)
# =============================================================================
#         self.noverlapSlider.setStyleSheet(
# "QSlider::groove:horizontal {"\
# "background: qlineargradient("\
# "x1:0, y1:0, x2:0, y2:1, stop:0 #B1B1B1, stop:1 #c4c4c4);"\
# "border: 1px solid; border-radius: 4px; height: 10px; margin: 0px;}\n"
# 
# "QSlider::sub-page:horizontal {"\
# "background: qlineargradient("\
# "x1: 0, y1: 0, x2: 0, y2: 1,stop: 0 #66e, stop: 1 #bbf);"\
# "background: qlineargradient("\
# "x1: 0, y1: 0.2, x2: 1, y2: 1,stop: 0 #bbf, stop: 1 #55f);"\
# "border: 1px solid #777; height: 10px; border-radius: 4px;}"
# 
# "QSlider::add-page:horizontal {" \
# "background: #fff;" \
# "border: 1px solid #777;" \
# "height: 10px;" \
# "border-radius: 4px;}"
# 
# "QSlider::handle:horizontal {"\
# "background: qlineargradient(x1:0, y1:0, x2:1, y2:1,"\
# "    stop:0 #eee, stop:1 #ccc);"\
# "border: 1px solid #777;"\
# "width: 18px;"\
# "margin-top: -3px;"\
# "margin-bottom: -3px;"\
# "border-radius: 4px;}"
# "")
# =============================================================================
        noverlapDisp = self.noverlapSlider.sliderPosition()
        self.noverlapLabel = QtGui.QLabel('overlap: {}%'.format(str(noverlapDisp)))
        
        # slider for high-pass cutoff frequency
        self.highcutSlider = QtGui.QSlider(orientation=1) # 1==horizontal
        self.highcutSlider.setRange(0, 200)
        #self.highcutSlider.setValue(self.highcut)
        self.highcutSlider.setSliderPosition(self.highcut*1e-3)
        self.highcutSlider.valueChanged.connect(self.saveSettings) #implement
        #self.highcutSlider.setSingleStep(1)
        self.highcutLabel = QtGui.QLabel('High-pass Cutoff: {} kHz'.format(str(self.highcut*1e-3)))
        
        # slider for low-pass cutoff frequency
        self.lowcutSlider = QtGui.QSlider(orientation=1) # 1==horizontal
        self.lowcutSlider.setRange(0, 200)
        #self.lowcutSlider.setValue(20)
        self.lowcutSlider.setSliderPosition(self.lowcut*1e-3)
        self.lowcutSlider.valueChanged.connect(self.saveSettings) #implement
        #self.lowcutSlider.setSingleStep(1)
        self.lowcutLabel = QtGui.QLabel('Low-pass Cutoff: {} kHz'.format(str(self.lowcut*1e-3)))
        
        CENTER = Align.CENTER.value
        self.settingsLayout.addWidget(windowLabel, 1, 0)
        self.settingsLayout.addWidget(self.windowSelect, 1, 1)
        self.settingsLayout.addWidget(self.lengthLabel, 2, 0)
        self.settingsLayout.addWidget(self.lengthSelect, 2, 1)
        self.settingsLayout.addWidget(self.noverlapLabel, 0, 2, CENTER)
        self.settingsLayout.addWidget(self.noverlapSlider, 1, 2, 3, 1, CENTER)
        #self.settingsLayout.setRowMinimumHeight(1, 50)
        self.settingsLayout.addWidget(self.highcutLabel, 0, 3)
        self.settingsLayout.addWidget(self.highcutSlider, 1, 3)
        self.settingsLayout.addWidget(self.lowcutLabel, 2, 3)
        self.settingsLayout.addWidget(self.lowcutSlider, 3, 3)
        self.settingsLayout.addWidget(revertBtn, 0, 4)
        self.settingsLayout.addWidget(closeBtn, 1, 4)
        
        
    def saveSettings(self):
        self.sigWindow = self.windowSelect.currentText()
        self.nperseg = int(self.lengthSelect.currentText())
        #print(self.nperseg)
        self.noverlap = (self.noverlapSlider.sliderPosition()/100)*self.nperseg
        #print(self.noverlap)
        self.nfft = self.nperseg # can be changed
        noverlapDisp = self.noverlapSlider.sliderPosition()
        self.noverlapLabel.setText('noverlap: {}%'.format(str(noverlapDisp)))
        self.highcut = self.highcutSlider.sliderPosition()*1e3
        highcutDisp = str(self.highcut*1e-3)
        self.highcutLabel.setText('High-pass Cutoff: {} kHz'.format(highcutDisp))
        self.lowcut = self.lowcutSlider.sliderPosition()*1e3
        lowcutDisp = str(self.lowcut*1e-3)
        self.lowcutLabel.setText('Low-pass Cutoff: {} kHz'.format(lowcutDisp))
        self.plotSelection('sg')
        
    def quicksave(self):
        self.saveData = [self.sigWindow, self.nperseg, self.noverlap,
                         self.lowcut, self.highcut]
        
    def revert(self):
        self.sigWindow = self.saveData[0]
        self.windowSelect.setCurrentText(self.sigWindow)
        self.nperseg = self.saveData[1]
        self.lengthSelect.setCurrentText(str(self.nperseg))
        self.noverlap = self.saveData[2]
        self.noverlapSlider.setSliderPosition(100*self.noverlap/self.nperseg)
        self.nfft = self.nperseg
        self.lowcut = self.saveData[3]
        self.lowcutSlider.setSliderPosition(self.lowcut)
        self.highcut = self.saveData[4]
        self.highcutSlider.setSliderPosition(self.highcut)
        
        self.plotSelection('sg')
        
        
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
        Plot.setLabel('bottom', 'Time', units='s')
        if side=='left':
            Plot.setLabel('left', 'Amplitude')
    
    def ft(self, lamp, ramp):
        lfreq = np.abs(np.fft.rfft(lamp))
        rfreq = np.abs(np.fft.rfft(ramp))
        lyf = lfreq[1:] #first data point is 0 and offsets rest of data
        ryf = rfreq[1:]
        yf = np.concatenate((lyf, ryf))
        base_dB = max(yf)
        ldB = []
        rdB = []
        for v in lyf:
            ldB.append(10*np.log10(v/base_dB)) #convert to dB scale
        for v in ryf:
            rdB.append(10*np.log10(v/base_dB)) #convert to dB scale
        return ldB, rdB
        
    def build_sm(self, leftPlot, rightPlot, lamp, ramp):
        leftPlot.clear()
        rightPlot.clear()
        lyf, ryf = self.ft(lamp, ramp)
        xf = np.linspace(0.0, self.fs//2, self.N//2)
        #xf = xf[self.N//20:self.N//4]
        #yf = freq[self.N//20:self.N//4] #from 20kHz to 100kHz
        leftPlot.plot(x=xf, y=lyf)
        rightPlot.plot(x=xf, y=ryf)
        leftPlot.setLabel('bottom', 'Frequency', units='Hz')
        rightPlot.setLabel('bottom', 'Frequency', units='Hz')
        leftPlot.setLabel('left', 'Amplitude', units='dB')
        #rows = len(lyf)
        #columns = len(xf)
        #yscale = 1
        #xscale = 200/columns
        #xaxis = pg.AxisItem('bottom', text='Frequency', units='Hz')
        #xaxis.setRange(0, 200e3)
        #leftPlot.setAxisItems({'bottom': xaxis})
        #leftPlot.scale(xscale, yscale)
        #rightPlot.scale(xscale, yscale)
            
    def build_sg(self, leftPlot, rightPlot, ldata, rdata):
        leftPlot.clear()
        rightPlot.clear()
        ldata = np.array(ldata)
        rdata = np.array(rdata)
        
        ## creating the spectrogram
        # most efficient nperseg & nfft values are powers of 2
        # spectrogram returns to Sxx as (frequency x time)
        f, t, lSxx = spectrogram(ldata, self.fs, self.sigWindow,
                                nperseg=self.nperseg, 
                                noverlap=self.noverlap,
                                nfft=self.nfft)
        f, t, rSxx = spectrogram(rdata, self.fs, self.sigWindow,
                                nperseg=self.nperseg, 
                                noverlap=self.noverlap,
                                nfft=self.nfft)
        
        lImg = pg.ImageItem() #spectrogram is an image
        rImg = pg.ImageItem()
        leftPlot.addItem(lImg) #add sg to widget
        rightPlot.addItem(rImg)
        
        ## color mapping
        nColors = 63
        #pos = np.linspace(0, 1, nColors)
        pos = np.logspace(-3, 0, nColors)
        color = cm.jet #63x4 array of rgba values
        
        cmap = pg.ColorMap(pos, color)

        lut = cmap.getLookupTable(0.0, 1.0, 256)
        lImg.setLookupTable(lut)
        rImg.setLookupTable(lut)
        
        
        #Sxx = Sxx * 1e10
        
        ## cutting the frequency range to 20kHz-100kHz
        fRes = (f[1] - f[0])/2
        fLowcut = self.binarySearch(f, self.lowcut, fRes)
        fHighcut = self.binarySearch(f, self.highcut, fRes)
        lSxx = lSxx[fLowcut:fHighcut]
        rSxx = rSxx[fLowcut:fHighcut]
        f = f[fLowcut:fHighcut]
        
        print(np.shape(rSxx))
        #print(len(t))
        
        ## empty array for the image
        rows = len(f)
        columns = len(t)
        self.lImg_array = np.zeros((rows, columns))
        self.rImg_array = np.zeros((rows, columns))
        
        ## scale the axes
        yscale = (max(f)-min(f))*1e-3 /rows # scale is wrong
        xscale = max(t)/columns
        lImg.scale(xscale, yscale)
        rImg.scale(xscale, yscale)
        
        ## Attempts to fix yAxis
        yAxis = pg.AxisItem('left')
        yAxis.setRange(self.lowcut*1e-3, self.highcut*1e-3)
        leftPlot.setAxisItems({'left': yAxis})
        #leftPlot.setRange(yRange=(20,100))
        #leftPlot.getAxis('left').setRange(20,100)
        #leftPlot.getAxis('left').linkToView(None)
        #leftPlot.setTransformOriginPoint(QtCore.QPointF(0, 200))
        
        
        
        self.lImg_array = lSxx
        self.rImg_array = rSxx
        
        ## normalize together
        Sxx = np.concatenate([lSxx,rSxx])
        Min = Sxx.min()
        Max = Sxx.max()
        lImg.setImage(self.lImg_array, autoLevels=False, levels=(Min, Max))
            #level values are estimated from appearance
        rImg.setImage(self.rImg_array, autoLevels=False, levels=(Min, Max))
        
        #leftPlot.setLimits(xMin=0, xMax=t[-1], yMin=0, yMax=f[-1])
        #rightPlot.setLimits(xMin=0, xMax=t[-1], yMin=0, yMax=f[-1])
        
        leftPlot.setLabel('bottom', 'Time', units='s')
        rightPlot.setLabel('bottom', 'Time', units='s')
        leftPlot.setLabel('left', 'Frequency', units='kHz')
            
    def run(self):
        #startTime = time.time()
        self.startBtn.setStyleSheet("background-color: red")
        jStr = self.iterationInput.text()
        try:
            self.j = int(jStr)
        except ValueError:
            self.j = 'inf'
        basepath = '/home/devan/Coding/MuellerLab/BatBotGUI/Data'
            #/home/devan/BatBot/Data #for Jetson
        data = []
        with os.scandir(basepath) as entries:
            for entry in entries:
                if entry.is_file():
                    data.append(entry.path)
        while self.startBtn.isChecked():
            if self.j != 'inf':
                # self.n initialized in __init__
                if self.n >= self.j:
                    break
            tStart = time.time()
            if self.useUpload == False:
                self.file = data[self.n]
            #tAmp = time.time()
            lamp, ramp = self.amplitude(self.file) # if useUpload True, file is
                # set in the waveformUpload function
            #print("Amplitude: {}".format(time.time() - tAmp))
            if self.sgBtn.isChecked():
                #tSg = time.time()
                self.build_sg(self.leftPlot, self.rightPlot, lamp, ramp)
                #print("Spectrogram: {}".format(time.time() - tSg))
            elif self.smBtn.isChecked():
                #tSm = time.time()
                self.build_sm(self.leftPlot, self.rightPlot, lamp, ramp)
                #print("Spectrum: {}".format(time.time() - tSm))
            elif self.ogBtn.isChecked():
                #tOg = time.time()
                self.build_og(self.leftPlot, self.timeArray, lamp, 'left')
                self.build_og(self.rightPlot, self.timeArray, ramp, 'right')
                #print("Oscillogram: {}".format(time.time() - tOg))
            #self.tPassed = time.time() - startTime
            tOnce = time.time() - tStart
            self.fps = 1/tOnce
            self.labels()
            #self.fpsUpdate() #temporary
            self.n += 1
            app.processEvents()
        self.n = 0
        self.useUpload = False
        #endTime = time.time()
        #self.tTotal = endTime - startTime
        #print("Total: {}".format(self.tTotal))
        #startTime = endTime
        self.startBtn.setStyleSheet("background-color: green")
        self.startBtn.setChecked(False)
        
        
    def plotSelection(self, plot=None):
        lamp, ramp = self.amplitude(self.file)
        if plot == 'sg':
            self.build_sg(self.leftPlot, self.rightPlot, lamp, ramp)
        elif self.sgBtn.isChecked():
            self.build_sg(self.leftPlot, self.rightPlot, lamp, ramp)
        elif self.smBtn.isChecked():
            self.build_sm(self.leftPlot, self.rightPlot, lamp, ramp)
        elif self.ogBtn.isChecked():
            self.build_og(self.leftPlot, self.timeArray, lamp, 'left')
            self.build_og(self.rightPlot, self.timeArray, ramp, 'right')
            
    def waveformUpload(self):
        filepath = QtGui.QFileDialog.getOpenFileName(self, 'Open file', 
                                                     '/home/devan/BatBot/Data',
                                                     "Text Files (*.txt)") #Jetson filepath
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
        self.fpsString = 'fps: {:.1f} Hz'.format(self.fps)
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
    #w.showMaximized() #for Jetson
    import sys
    if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        QtGui.QApplication.instance().exec_()
    
