
from PyQt4 import QtGui, QtCore

from ccpncore.gui.Base import Base
from ccpncore.util.Translation import translator



class RadioButton(QtGui.QRadioButton, Base):

  def __init__(self, parent, text='', textColor=None, textSize=None, callback=None, **kw):

    text = translator.translate(text)

    QtGui.QRadioButton.__init__(self, text, parent)
    Base.__init__(self,  **kw)
    if textColor:
      self.setStyleSheet('QRadioButton {color: %s; font-size: 12pt;}' % textColor)
    # if textSize :
    #   self.setStyleSheet('QRadioButton {font-size: %s;}' % textSize)
    if callback:
      self.setCallback(callback)

  def get(self):

    return self.text()

  def set(self, text=''):

    if len(text) > 0:
      text = translator.translate(text)

    self.setText(text)

  def setCallback(self, callback):
    #
    # if self.callback:
    #   self.disconnect(self, QtCore.SIGNAL('clicked()'), self.callback)

    if callback:
      self.connect(self, QtCore.SIGNAL('clicked()'), callback)
      # self.clicked.connect doesn't work with lambda, yet...