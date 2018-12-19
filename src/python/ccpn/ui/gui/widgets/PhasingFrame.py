"""
Module Documentation here
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2017"
__credits__ = ("Wayne Boucher, Ed Brooksbank, Rasmus H Fogh, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license",
               "or ccpnmodel.ccpncore.memops.Credits.CcpnLicense for licence text")
__reference__ = ("For publications, please use reference from http://www.ccpn.ac.uk/v3-software/downloads/license",
                 "or ccpnmodel.ccpncore.memops.Credits.CcpNmrReference")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: CCPN $"
__dateModified__ = "$dateModified: 2017-07-07 16:32:54 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.b4 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from PyQt5 import QtWidgets
from ccpn.ui.gui.widgets.Entry import FloatEntry
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.PulldownList import PulldownList
from ccpn.ui.gui.widgets.Slider import Slider
from ccpn.ui.gui.widgets.Frame import Frame
from ccpn.ui.gui.widgets.DoubleSpinbox import DoubleSpinbox
from ccpn.ui.gui.widgets.Button import Button


directionTexts = ('horizontal', 'vertical')


class PhasingFrame(Frame):

    def __init__(self, parent=None,
                 includeDirection=True,
                 callback=None,
                 returnCallback=None,
                 directionCallback=None,
                 applyCallback=None, **kwds):

        super().__init__(parent, setLayout=True, **kwds)

        self.callback = callback
        self.returnCallback = returnCallback if returnCallback else self.doCallback
        self.directionCallback = directionCallback if directionCallback else self.doCallback
        self.applyCallback = applyCallback

        sliderDict = {
            'startVal'    : -180,
            'endVal'      : 180,
            'value'       : 0,
            'step'        : 1,
            'bigStep'     : 3,
            #'showNumber': True,
            'tickInterval': 30,
            'spinbox'     : True,
            }
        value = '%4d' % sliderDict['value']

        self.label0 = Label(self, text='ph0', grid=(0, 0))
        self.label0.setFixedWidth(30)
        # self.phLabel0 = Label(self, text=value, grid=(0, 1))
        # self.phLabel0.setFixedWidth(35)
        self.coarseSlider0 = Slider(self, callback=self.setCoarsePh0, grid=(0, 2), **sliderDict)
        # self.slider0.setFixedWidth(200)
        self.slider0 = DoubleSpinbox(self, grid=(0, 3), decimals=1, step=0.1, callback=self.setPh0)
        self.slider0.setRange(-180, 180)

        sliderDict = {
            'startVal'    : -360,
            'endVal'      : 360,
            'value'       : 0,
            'step'        : 1,
            #'showNumber': True,
            'tickInterval': 60,
            }
        value = '%4d' % sliderDict['value']

        self.label1 = Label(self, text='ph1', grid=(0, 4))
        self.label1.setFixedWidth(30)
        # self.phLabel1 = Label(self, text=value, grid=(0, 4))
        # self.phLabel1.setFixedWidth(35)
        self.coarseSlider1 = Slider(self, callback=self.setCoarsePh1, grid=(0, 5), **sliderDict)
        # self.slider1.setFixedWidth(200)
        self.slider1 = DoubleSpinbox(self, grid=(0, 6), decimals=1, step=0.1, callback=self.setPh1)
        self.slider1.setRange(-360, 360)

        self.PivotLabel = Label(self, text='pivot', grid=(0, 7))
        self.PivotLabel.setFixedWidth(35)
        self.pivotEntry = DoubleSpinbox(self, callback=lambda value: self._returnCallback(), decimals=3, step=0.1, grid=(0, 8))
        self.pivotEntry.setFixedWidth(60)

        self.pivotEntry.valueChanged.connect(self.setPivotValue)
        if includeDirection:
            self.directionList = PulldownList(self, texts=directionTexts,
                                              callback=None, grid=(0, 9))
            self.directionList.activated.connect(lambda text: self.directionCallback())
        else:
            self.directionList = None

        self.applyButton = Button(self, grid=(0, 10), text='Apply', callback=self._apply)
        self.applyButton.setEnabled(False)

        self.setSizePolicy(QtWidgets.QSizePolicy.Ignored, QtWidgets.QSizePolicy.Minimum)

        self.values = {'direction'      : directionTexts[0],
                       directionTexts[0]: {'ph0': 0.0, 'ph1': 0.0, 'pivot': 0.0},
                       directionTexts[1]: {'ph0': 0.0, 'ph1': 0.0, 'pivot': 0.0}
                       }
        self._pivotsSet = False

    @property
    def pivotsSet(self):
        return self._pivotsSet

    def setInitialPivots(self, pivotList):
        self._pivotsSet = True
        for dd, pivot in enumerate(pivotList):
            self.values[directionTexts[dd]]['pivot'] = pivot

    def _apply(self):
        if self.applyCallback:
            self.applyCallback(self.values)

    def updateValues(self):
        dd = self.getDirection()
        self.values['direction'] = directionTexts[dd]
        self.values[directionTexts[dd]] = {'ph0'  : float(self.slider0.value()),
                                           'ph1'  : float(self.slider1.value()),
                                           'pivot': float(self.pivotEntry.get())}

    def getDirection(self):
        return directionTexts.index(self.directionList.get()) if self.directionList else 0

    def getValues(self, direction):
        dir = directionTexts[direction]
        return (self.values[dir]['ph0'],
                self.values[dir]['ph1'],
                self.values[dir]['pivot'])

    def setCoarsePh0(self, value):
        # self.phLabel0.setText(str(value))
        self.slider0.setValue(value)
        # self.doCallback()

    def setCoarsePh1(self, value):
        # self.phLabel1.setText(str(value))
        self.slider1.setValue(value)
        # self.doCallback()

    def setPh0(self, value):
        # self.phLabel0.setText(str(value))
        self.coarseSlider0.setValue(value)
        self.updateValues()
        self.doCallback()

    def setPh1(self, value):
        # self.phLabel1.setText(str(value))
        self.coarseSlider1.setValue(value)
        self.updateValues()
        self.doCallback()

    def setPivotValue(self):
        self.updateValues()
        self.doCallback()

    def doCallback(self):
        if self.callback:
            self.callback()

    def _returnCallback(self):
        pass


if __name__ == '__main__':
    import os
    import sys
    from PyQt5 import QtGui, QtWidgets


    def myCallback(ph0, ph1, pivot, direction):
        print(ph0, ph1, pivot, direction)


    qtApp = QtWidgets.QApplication(['Test Phase Frame'])

    #QtCore.QCoreApplication.setApplicationName('TestPhasing')
    #QtCore.QCoreApplication.setApplicationVersion('0.1')

    widget = QtWidgets.QWidget()
    frame = PhasingFrame(widget, callback=myCallback)
    widget.show()
    widget.raise_()

    sys.exit(qtApp.exec_())
