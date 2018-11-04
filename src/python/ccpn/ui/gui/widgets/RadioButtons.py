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
__dateModified__ = "$dateModified: 2017-07-07 16:32:55 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.b3 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Luca Mureddu $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from PyQt5 import QtGui, QtWidgets, QtCore
from ccpn.ui.gui.widgets.Base import Base
from ccpn.ui.gui.widgets.RadioButton import RadioButton


CHECKED = QtCore.Qt.Checked
UNCHECKED = QtCore.Qt.Unchecked

class RadioButtons(QtWidgets.QWidget, Base):

  def __init__(self, parent, texts=None, selectedInd=None, exclusive=True,
               callback=None, direction='h', tipTexts=None,  **kwds):

    super().__init__(parent)
    Base._init(self, setLayout = True, **kwds)

    if texts is None:
      texts = []

    self.texts = texts
    direction = direction.lower()
    buttonGroup = self.buttonGroup = QtWidgets.QButtonGroup(self)
    self.isExclusive = exclusive
    buttonGroup.setExclusive(self.isExclusive)

    if not tipTexts:
      tipTexts = [None] * len(texts)

    self.radioButtons = []
    self.setButtons(texts, selectedInd, direction, tipTexts)
    # for i, text in enumerate(texts):
    #   if 'h' in direction:
    #     grid = (0, i)
    #   else:
    #     grid = (i, 0)
    #   button = RadioButton(self, text, tipText=tipTexts[i], grid=grid, hAlign='l')
    #   self.radioButtons.append(button)
    #
    #   buttonGroup.addButton(button)
    #   buttonGroup.setId(button, i)
    #
    # if selectedInd is not None:
    #   self.radioButtons[selectedInd].setChecked(True)

    # buttonGroup.connect(buttonGroup, QtCore.SIGNAL('buttonClicked(int)'), self._callback)
    buttonGroup.buttonClicked.connect(self._callback)

    self.setCallback(callback)

  def setButtons(self, texts=None, selectedInd=None, direction='h', tipTexts=None):
    """Change the buttons in the button group
    """
    # clear the original buttons
    selected = self.getSelectedText()

    for btn in self.radioButtons:
      self.buttonGroup.removeButton(btn)
      btn.deleteLater()
    self.radioButtons = []

    # rebuild the button list
    for i, text in enumerate(texts):
      if 'h' in direction:
        grid = (0, i)
      else:
        grid = (i, 0)
      button = RadioButton(self, text, tipText=tipTexts[i], grid=grid, hAlign='l')
      self.radioButtons.append(button)

      self.buttonGroup.addButton(button)
      self.buttonGroup.setId(button, i)

    self.texts = texts
    if selectedInd is not None:
      self.radioButtons[selectedInd].setChecked(True)
    elif selected and selected in self.texts:
      self.set(selected)
    else:
      self.radioButtons[0].setChecked(True)

  def getRadioButton(self, text):
    for rb in self.radioButtons:
      if rb.text() == text:
        return rb

  def get(self):

    return self.texts[self.getIndex()]

  def getIndex(self):

    return self.radioButtons.index(self.buttonGroup.checkedButton())

  @property
  def isChecked(self):

    return self.buttonGroup.checkedButton() is not None

  def set(self, text):

    i = self.texts.index(text)
    self.setIndex(i)

  def getSelectedText(self):
    for radioButton in self.radioButtons:
      if radioButton.isChecked():
        name = radioButton.text()
        if name:
          return name

  def setIndex(self, i):

    self.radioButtons[i].setChecked(True)

  def deselectAll(self):
    self.buttonGroup.setExclusive(False)
    for i in self.radioButtons:
      i.setChecked(False)
    self.buttonGroup.setExclusive(self.isExclusive)

  def setCallback(self, callback):

    self.callback = callback

  def _callback(self, button):

    if self.callback and button:
      # button = self.buttonGroup.buttons[ind]
      self.callback()


if __name__ == '__main__':
  from ccpn.ui.gui.widgets.Application import TestApplication
  from ccpn.ui.gui.widgets.BasePopup import BasePopup

  from ccpn.ui.gui.popups.Dialog import CcpnDialog

  def testCallback():
    print('TEST')

  app = TestApplication()
  popup = CcpnDialog(windowTitle='Test radioButtons', setLayout=True)

  buttonGroup = QtWidgets.QButtonGroup(popup)
  # radioButtons = RadioButtons(parent=popup,
  #              callback=testCallback, grid=(0, 0))
  for i in range(10):
    button = RadioButton(popup, text='TEST', grid=(i, 0),
                         callback=None)  # partial(self.assignSelect
    buttonGroup.addButton(button)


  popup.raise_()
  popup.exec()

  app.start()
