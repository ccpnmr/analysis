from PySide import QtGui,QtCore
import pyqtgraph as pg
import numpy as np
from pyqtgraph.Point import Point
import pyqtgraph.console
import sys


class SpectrumWidget:

  def __init__(self):

    pg.setConfigOption('background', 'w')
    pg.setConfigOption('foreground', 'k')
    self.widget = pg.PlotWidget()
    self.createCrossHair()
    self.viewBox = self.widget.plotItem.vb
    self.widget.scene().sigMouseMoved.connect(self.mouseMoved)


  def createCrossHair(self):
    self.vLine = pg.InfiniteLine(angle=90)
    self.hLine = pg.InfiniteLine(angle=0)
    self.widget.addItem(self.vLine)
    self.widget.addItem(self.hLine)

  def mouseMoved(self, event):
    position = event  ## using signal proxy turns original arguments into a tuple
    if self.widget.sceneBoundingRect().contains(position):
        mousePoint = self.viewBox.mapSceneToView(position)
        self.vLine.setPos(mousePoint.x())
        self.hLine.setPos(mousePoint.y())



###For testing
if __name__ == '__main__':

  app = QtGui.QApplication(sys.argv)
  w = QtGui.QWidget()
  layout = QtGui.QGridLayout()
  spectrumWidget = SpectrumWidget()
  widget=spectrumWidget.widget
  layout.addWidget(widget)
  w.setLayout(layout)
  w.show()
  sys.exit(app.exec_())

