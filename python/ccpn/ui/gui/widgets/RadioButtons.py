__author__ = 'luca'


from PyQt4 import QtGui, QtCore

from ccpn.ui.gui.widgets.Base import Base

from ccpn.ui.gui.widgets.RadioButton import RadioButton


CHECKED = QtCore.Qt.Checked
UNCHECKED = QtCore.Qt.Unchecked

class RadioButtons(QtGui.QWidget):

  def __init__(self, parent, texts=None, selectedInd=None,
               callback=None, direction='h', tipTexts=None,  **kw):


    QtGui.QWidget.__init__(self, parent)
    # Base.__init__(self, **kw)

    if texts is None:
      texts = []

    self.texts = texts
    direction = direction.lower()
    buttonGroup = self.buttonGroup = QtGui.QButtonGroup(self)
    buttonGroup.setExclusive(True)

    if not tipTexts:
      tipTexts = [None] * len(texts)

    self.radioButtons = []
    for i, text in enumerate(texts):
      if 'h' in direction:
        grid = (0, i)
      else:
        grid = (i, 0)

      button = RadioButton(self, text, tipText=tipTexts[i], grid=grid)

      self.radioButtons.append(button)

      buttonGroup.addButton(button)
      buttonGroup.setId(button, i)

    if selectedInd is not None:
      self.radioButtons[selectedInd].setChecked(True)

    buttonGroup.connect(buttonGroup, QtCore.SIGNAL('buttonClicked(int)'), self._callback)

    self.setCallback(callback)

  def get(self):

    return self.texts[self.getIndex()]

  def getIndex(self):

    return self.radioButtons.index(self.buttonGroup.checkedButton())

  def set(self, text):

    i = self.texts.index(text)
    self.setIndex(i)

  def setIndex(self, i):

    self.radioButtons[i].setChecked(True)

  def setCallback(self, callback):

    self.callback = callback

  def _callback(self, ind):

    if self.callback and ind >= 0:
      button = self.buttonGroup.buttons()[ind]
      self.callback()
