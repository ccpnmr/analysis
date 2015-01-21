__author__ = 'simon'

from PySide import QtGui, QtCore


class VerticalLabel(QtGui.QWidget):

    def __init__(self, parent, text):
      self.text = text
      self.height = parent.height()
      QtGui.QWidget.__init__(self, parent)

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