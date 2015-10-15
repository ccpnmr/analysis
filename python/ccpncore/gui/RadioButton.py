
from PyQt4 import QtGui, QtCore

from ccpncore.gui.Base import Base



class RadioButton(QtGui.QRadioButton, Base):

  def __init__(self, parent, text='',textColor=None, textSize=None, **kw):

    QtGui.QRadioButton.__init__(self, text, parent)
    Base.__init__(self,  **kw)
    if textColor:
      self.setStyleSheet('QRadioButton {color: %s; font-size: 12pt;}' % textColor)
    # if textSize :
    #   self.setStyleSheet('QRadioButton {font-size: %s;}' % textSize)

  def get(self):

    return self.text()

  def set(self, text=''):

    self.setText(self.translate(text))