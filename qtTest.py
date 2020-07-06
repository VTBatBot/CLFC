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
        self.addButtons(self.layout)
        
    def addButtons(self, layout):
        # buttons and other widgets
        self.sgBtn = QtGui.QRadioButton('Spectrogram')
        self.smBtn = QtGui.QRadioButton('Spectrum')
        self.ogBtn = QtGui.QRadioButton('Oscillogram')
        self.startBtn = QtGui.QPushButton('Start/Stop')
        self.uploadBtn = QtGui.QPushButton('Upload Waveform')
        self.iterationInput = QtGui.QLineEdit('Enter number of iterations')
        self.iterationLabel = QtGui.QLabel('N: ')
        self.durationLabel = QtGui.QLabel('t: ')
        self.rateLabel = QtGui.QLabel('Fs: ')
        
        
        
        ## Add widgets to the layout in their proper positions
        layout.addWidget(self.startBtn, 3, 2)
        layout.addWidget(self.uploadBtn, 3, 0)   # text edit goes in middle-left
        layout.addWidget(self.iterationInput, 3, 1)  # list widget goes in bottom-left
        layout.addWidget(self.sgBtn, 2, 3)
        layout.addWidget(self.smBtn, 3, 3)
        layout.addWidget(self.ogBtn, 4, 3)
        layout.addWidget(self.iterationLabel, 2, 4)
        layout.addWidget(self.durationLabel, 3, 4)
        layout.addWidget(self.rateLabel, 4, 4)
        
        #lsg = SpectrogramWidget()
        #rsg = SpectrogramWidget()
        #layout.addWidget(lsg, 1, 0, 1, 2)

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
        

if __name__ == '__main__':
    app = QtGui.QApplication([])
    w = Window()
    lsg = SpectrogramWidget()
    w.layout.addWidget(lsg, 1, 0, 1, 2)
    lsg.update('20181111_121329107.txt')
    
    #connect start/stop button to updating spectrogram
    w.startBtn.clicked.connect(lambda x:lsg.update('20181111_121335497.txt'))
    w.show()
    app.exec_()
    