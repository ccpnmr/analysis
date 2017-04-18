"""
This module implements the Button class

"""

#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (www.ccpn.ac.uk) 2014 - $Date$"
__credits__ = "Wayne Boucher, Rasmus H Fogh, Simon Skinner, Geerten Vuister"
__license__ = ("CCPN license. See www.ccpn.ac.uk/license"
              "or ccpnmodel.ccpncore.memops.Credits.CcpnLicense for license text")
__reference__ = ("For publications, please use reference from www.ccpn.ac.uk/license"
                " or ccpnmodel.ccpncore.memops.Credits.CcpNmrReference")

#=========================================================================================
# Last code modification:
#=========================================================================================
__author__ = "$Author: Geerten Vuister $"
__date__ = "$Date: 2017-04-18 15:19:30 +0100 (Tue, April 18, 2017) $"

#=========================================================================================
# Start of code
#=========================================================================================
from PyQt4 import QtCore, QtGui

from ccpn.ui.gui.widgets.Base import Base
from ccpn.ui.gui.widgets.Icon import Icon
from ccpn.framework.Translation import translator

CHECKED = QtCore.Qt.Checked
UNCHECKED = QtCore.Qt.Unchecked

class Button(QtGui.QPushButton, Base):

  def __init__(self, parent, text='', callback=None, icon=None, toggle=None, **kw):

    #text = translator.translate(text): not needed as it calls setText which does the work

    QtGui.QPushButton.__init__(self, parent)
    Base.__init__(self, **kw)

    self.setText(text)

    if icon: # filename or pixmap
      self.setIcon(Icon(icon))
      self.setIconSize(QtCore.QSize(22,22))
    if toggle is not None:
      self.setCheckable(True)
      self.setSelected(toggle)

    self._callback = None
    self.setCallback(callback)

  def setSelected(self, selected):

    if self.isCheckable():
      if selected:
        self.setChecked(CHECKED)
      else:
        self.setChecked(UNCHECKED)

  def setCallback(self, callback):
    "Sets callback; disconnects if callback=None"
    if self._callback is not None:
      self.disconnect(self, QtCore.SIGNAL('clicked()'), self._callback)
    if callback:
      self.connect(self, QtCore.SIGNAL('clicked()'), callback)
      # self.clicked.connect doesn't work with lambda, yet...
    self._callback = callback

  def setText(self, text):
    "Set the text of the button, applying the translator first"
    self._text = translator.translate(text)
    QtGui.QPushButton.setText(self, self._text)

  def getText(self):
    "Get the text of the button"
    return self._text


if __name__ == '__main__':

  from ccpn.ui.gui.widgets.Application import TestApplication

  app = TestApplication()

  window = QtGui.QWidget()

  def click():
    print("Clicked")

  b1 = Button(window, text='Click Me', callback=click,
             tipText='Click for action',
             grid=(0, 0))

  b2 = Button(window, text='I am inactive', callback=click,
             tipText='Cannot click',
             grid=(0, 1))

  b2.setEnabled(False)

  b3 = Button(window, text='I am green', callback=click,
             tipText='Mmm, green', bgColor='#80FF80',
             grid=(0, 2))

  b4 = Button(window, icon='icons/system-help.png', callback=click,
             tipText='A toggled icon button', toggle=True,
             grid=(0, 3))

  window.show()
  window.raise_()

  app.start()


