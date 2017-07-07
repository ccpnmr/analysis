"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2017"
__credits__ = ("Wayne Boucher, Ed Brooksbank, Rasmus H Fogh, Luca Mureddu, Timothy J Ragan"
               "Simon P Skinner & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license"
               "or ccpnmodel.ccpncore.memops.Credits.CcpnLicense for licence text")
__reference__ = ("For publications, please use reference from http://www.ccpn.ac.uk/v3-software/downloads/license"
               "or ccpnmodel.ccpncore.memops.Credits.CcpNmrReference")

#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: CCPN $"
__dateModified__ = "$dateModified: 2017-04-07 11:41:06 +0100 (Fri, April 07, 2017) $"
__version__ = "$Revision: 3.0.b1 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"

__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from ccpn.ui.gui.widgets.Entry import FloatEntry
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.PulldownList import PulldownList
from ccpn.ui.gui.widgets.Slider import Slider
from ccpn.ui.gui.widgets.Frame import Frame

directionTexts = ('Horizontal', 'Vertical')

class PhasingFrame(Frame):

  def __init__(self, parent=None, includeDirection=True, callback=None, returnCallback=None, directionCallback=None, **kw):

    Frame.__init__(self, parent, setLayout=True, **kw)
    
    self.callback = callback
    self.returnCallback = returnCallback if returnCallback else self.doCallback
    self.directionCallback = directionCallback if directionCallback else self.doCallback

    sliderDict = {
      'startVal': -180,
      'endVal': 180,
      'value': 0,
      'step':1,
      'bigStep':3,
      #'showNumber': True,
      'tickInterval': 30,
      'spinbox':True,
    }
    value = '%4d' % sliderDict['value']
    
    self.label0 = Label(self, text='ph0', grid=(0,0))
    self.label0.setFixedWidth(30)
    self.phLabel0 = Label(self, text=value, grid=(0, 1))
    self.phLabel0.setFixedWidth(35)
    self.slider0 = Slider(self, callback=self.setPh0, grid=(0, 2), **sliderDict)
    self.slider0.setFixedWidth(200)

    sliderDict = {
      'startVal': -360,
      'endVal': 360,
      'value': 0,
      'step':1,
      #'showNumber': True,
      'tickInterval': 60,
    }
    value = '%4d' % sliderDict['value']
    
    self.label1 = Label(self, text='ph1', grid=(0,3))
    self.label1.setFixedWidth(30)
    self.phLabel1 = Label(self, text=value, grid=(0, 4))
    self.phLabel1.setFixedWidth(35)
    self.slider1 = Slider(self, callback=self.setPh1, grid=(0, 5), **sliderDict)
    self.slider1.setFixedWidth(200)

    self.PivotLabel = Label(self, text='pivot', grid=(0,6))
    self.PivotLabel.setFixedWidth(35)
    self.pivotEntry = FloatEntry(self, callback=lambda value: self.returnCallback(), decimals=2, grid=(0,7))
    self.pivotEntry.setFixedWidth(60)
    
    if includeDirection:
      self.directionList = PulldownList(self, texts=directionTexts,
                                        callback=lambda text: self.directionCallback(), grid=(0,8))
    else:
      self.directionList = None
      
  def getDirection(self):
    
    return directionTexts.index(self.directionList.get()) if self.directionList else 0
    
  def setPh0(self, value):
    self.phLabel0.setText(str(value))
    self.doCallback()
    
  def setPh1(self, value):
    self.phLabel1.setText(str(value))
    self.doCallback()
    
  def doCallback(self):
    if self.callback:
      self.callback()
 
if __name__ == '__main__':

  import os
  import sys
  from PyQt4 import QtGui

  def myCallback(ph0, ph1, pivot, direction):
    print(ph0, ph1, pivot, direction)
    
  qtApp = QtGui.QApplication(['Test Phase Frame'])

  #QtCore.QCoreApplication.setApplicationName('TestPhasing')
  #QtCore.QCoreApplication.setApplicationVersion('0.1')

  widget = QtGui.QWidget()
  frame = PhasingFrame(widget, callback=myCallback)
  widget.show()
  widget.raise_()
  
  sys.exit(qtApp.exec_())
 
