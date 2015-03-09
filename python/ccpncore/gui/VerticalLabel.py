__author__ = 'simon'

from PyQt4 import QtGui, QtCore
from ccpncore.gui.Base import Base

class VerticalLabel(QtGui.QWidget, Base):

    def __init__(self, parent, text, **kwargs):
      QtGui.QWidget.__init__(self, parent)
      self.text = text
      self.setText(text)
      self.height = parent.height()
      Base.__init__(self, **kwargs)

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.setPen(QtCore.Qt.black)
        painter.translate(20, 200)
        painter.rotate(-90)
        painter.drawText(0, 0, self.text)
        painter.end()

    def setText(self, text):
      self.text = text
      self.repaint()