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
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2017-04-07 11:40:43 +0100 (Fri, April 07, 2017) $"
__version__ = "$Revision: 3.0.b1 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: luca $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from PyQt4 import QtGui, QtCore
from ccpn.ui.gui.widgets.Base import Base
from ccpn.ui.gui.widgets.Spinbox import Spinbox

class Slider(QtGui.QSlider, Base):
  def __init__(self, parent, startVal=0, endVal=100, value=None,
               direction='h', step=1, bigStep=None, callback=None,
               tracking=True, showNumber=True, tickInterval=None,
               tickPosition=None, listener=None, spinbox=False, **kw):

    QtGui.QSlider.__init__(self, parent)
    Base.__init__(self, **kw)

    self.callback = callback

    if value is None:
      value = startVal


    if not bigStep:
      bigStep = step

    if tickInterval:
      if not tickPosition:
        if 'h' in direction.lower():
          tickPosition = self.TicksBelow
        else:
          tickPosition = self.TicksRight

      self.setTickInterval(tickInterval)
      self.setTickPosition(tickPosition)


    self.showNumber = showNumber
    self.setRange(startVal, endVal)
    self.setStep(step, bigStep)
    self.set(value)
    self.fontMetric = QtGui.QFontMetricsF(self.font())

    if 'h' in direction.lower():
      self.setOrientation(QtCore.Qt.Horizontal)
    else:
      self.setOrientation(QtCore.Qt.Vertical)

    # Callback continuously (True)
    # Or only at intervals (False)
    self.setTracking(tracking)


    if showNumber and not tracking:
      self.connect(self, QtCore.SIGNAL('sliderMoved(int)'), self._redraw)

    if showNumber:
      self.connect(self, QtCore.SIGNAL('sliderReleased()'), self.update)

    self.connect(self, QtCore.SIGNAL('valueChanged(int)'), self._callback)

    if listener:
      if isinstance(listener, (set, list, tuple)):
        for signal in listener:
          signal.connect(self.setValue)

      else:
        listener.connect(self.setValue)



  def setRange(self, startVal, endVal):

    startVal = int(startVal)
    endVal = int(endVal)

    assert startVal != endVal

    if startVal > endVal:
      self.setInvertedAppearance(True)
      startVal, endVal = endVal, startVal
    else:
      self.setInvertedAppearance(False)

    value = self.get()

    if startVal <= value <= endVal:
      callback = self.callback
      self.callback = None
      QtGui.QSlider.setRange(self, startVal, endVal)
      self.callback = callback

    else:
      QtGui.QSlider.setRange(self, startVal, endVal)

  def setStep(self, step, bigStep=None):

    self.setSingleStep(step)

    if bigStep:
      self.setPageStep(bigStep)

  def set(self, value, doCallback=True):

    if not doCallback:
      callback = self.callback
      self.callback = None
      self.setValue(int(value))
      self.callback = callback

    else:
      self.setValue(int(value))

  def get(self):

    return self.value()

  def _callback(self, callback):

    if self.callback:
      self.callback(self.value())

  def disable(self):

    self.setDisabled(True)

  def enable(self):

    self.setEnabled(True)

  def setState(self, state):

    self.setEnabled(state)





class SliderSpinBox(QtGui.QWidget, Base):
  def __init__(self,parent, startVal=0, endVal=100, value=None, step=1, bigStep=5, **kw):
    QtGui.QWidget.__init__(self, parent)
    Base.__init__(self, **kw)

    if value is None:
      value = startVal

    if not bigStep:
      bigStep = step

    slider = Slider(self, value=value, startVal=startVal, endVal=endVal, bigStep=bigStep, grid=(0, 1))
    self.spinBox = Spinbox(self, value=value, min=startVal, max=endVal, grid=(0, 0))
    slider.valueChanged.connect(self.spinBox.setValue)
    self.spinBox.valueChanged.connect(slider.setValue)

  def getValue(self):
    return self.spinBox.value()

  def set(self, value):
    self.spinBox.setValue(value)


if __name__ == '__main__':
  from ccpn.ui.gui.widgets.Application import TestApplication
  from ccpn.ui.gui.widgets.BasePopup import BasePopup
  app = TestApplication()
  popup = BasePopup(title='Test slider')
  popup.setSize(250, 50)
  slider = SliderSpinBox(parent=popup, startVal=0, endVal=100, value=5)
  app.start()
