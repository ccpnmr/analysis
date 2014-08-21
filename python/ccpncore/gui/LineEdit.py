__author__ = 'simon'
from PySide import QtGui

from ccpncore.gui.Base import Base

class LineEdit(QtGui.QLineEdit, Base):

  def __init__(self, parent, text='', textColor=None, **kw):

    QtGui.QLineEdit.__init__(self, text, parent)
    Base.__init__(self, **kw)

    if textColor:
      self.setStyleSheet('QLabel {color: %s;}' % textColor)

  def get(self):

    return self.text()

  def set(self, text=''):

    self.setText(self.translate(text))