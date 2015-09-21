"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (www.ccpn.ac.uk) 2014 - $Date: 2014-06-04 18:13:10 +0100 (Wed, 04 Jun 2014) $"
__credits__ = "Wayne Boucher, Rasmus H Fogh, Simon P Skinner, Geerten W Vuister"
__license__ = ("CCPN license. See www.ccpn.ac.uk/license"
              "or ccpncore.memops.Credits.CcpnLicense for license text")
__reference__ = ("For publications, please use reference from www.ccpn.ac.uk/license"
                " or ccpncore.memops.Credits.CcpNmrReference")

#=========================================================================================
# Last code modification:
#=========================================================================================
__author__ = "$Author: rhfogh $"
__date__ = "$Date: 2014-06-04 18:13:10 +0100 (Wed, 04 Jun 2014) $"
__version__ = "$Revision: 7686 $"

#=========================================================================================
# Start of code
#=========================================================================================
from PyQt4 import QtGui

from ccpncore.gui.Label import Label
from ccpncore.gui.Slider import Slider
from ccpncore.gui.Frame import Frame

class PhasingFrame(Frame):

  def __init__(self, parent=None, callback=None, **kw):

    Frame.__init__(self, parent, **kw)
    
    self.callback = callback

    sliderDict = {
      'startVal': 0,
      'endVal': 360,
      'value': 0,
      #'showNumber': True,
      'tickInterval': 90,
    }
    value = '%4d' % sliderDict['value']
    
    label = Label(self, text='ph0', grid=(0,0))
    self.phLabel0 = Label(self, text=value, grid=(0, 1))
    self.slider0 = Slider(self, callback=self.setPh0, grid=(0, 2), **sliderDict)
    
    label = Label(self, text='ph1', grid=(0,3))
    self.phLabel1 = Label(self, text=value, grid=(0, 4))
    self.slider1 = Slider(self, callback=self.setPh1, grid=(0, 5), **sliderDict)
 
  def setPh0(self, value):
    self.phLabel0.setText(str(value))
    self.doCallback()
    
  def setPh1(self, value):
    self.phLabel1.setText(str(value))
    self.doCallback()
    
  def doCallback(self):
    if self.callback:
      self.callback(self.slider0.value(), self.slider1.value())
 
if __name__ == '__main__':

  import os
  import sys

  qtApp = QtGui.QApplication(['Test Phase Frame'])

  #QtCore.QCoreApplication.setApplicationName('TestPhasing')
  #QtCore.QCoreApplication.setApplicationVersion('0.1')

  widget = QtGui.QWidget()
  frame = PhaseFrame(widget)
  widget.show()
  widget.raise_()
  
  sys.exit(qtApp.exec_())
 
