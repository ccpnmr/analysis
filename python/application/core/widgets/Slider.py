__author__ = 'luca'

from PyQt4 import QtGui, QtCore
from application.core.widgets.Base import Base

class Slider(QtGui.QSlider, Base):
  def __init__(self, parent, startVal=0, endVal=100, value=None,
               direction='h', step=1, bigStep=None, callback=None,
               tracking=True, showNumber=True, tickInterval=None,
               tickPosition=None, listener=None, **kw):

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
