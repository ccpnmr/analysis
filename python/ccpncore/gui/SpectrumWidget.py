from PySide import QtGui,QtCore
import pyqtgraph as pg
import numpy as np
from pyqtgraph.Point import Point
import pyqtgraph.console
import sys
import pprint

class SpectrumWidget:

  def __init__(self):

    pg.setConfigOption('background', 'w')
    pg.setConfigOption('foreground', 'k')
    # if self.useOpenGL:
    #   pg.setConfigOption('useOpenGL', 'True')
    self.widget = pg.PlotWidget()
    self.createCrossHair()
    self.viewBox = self.widget.plotItem.vb
    self.viewBox.setMenuDisabled()
    self.widget.scene().sigMouseMoved.connect(self.mouseMoved)
    self.widget.scene().sigMouseClicked.connect(self.mouseClicked)

    # self.widget.scene().sigMouseClicked.connect(self.mouseDragged)
    self.widget.plotItem.axes['left']['item'].hide()
    self.widget.plotItem.axes['right']['item'].show()
    self.widget.plotItem.axes['right']['item'].orientation = 'left'
    self.widget.plotItem.axes['bottom']['item'].orientation = 'top'
    self.viewBox.mouseDragEvent = self.newMouseDragEvent


  def createCrossHair(self):
    self.vLine = pg.InfiniteLine(angle=90)
    self.hLine = pg.InfiniteLine(angle=0)
    self.widget.addItem(self.vLine)
    self.widget.addItem(self.hLine)

  def mouseMoved(self, event):
    position = event
    if self.widget.sceneBoundingRect().contains(position):
        mousePoint = self.viewBox.mapSceneToView(position)
        self.vLine.setPos(mousePoint.x())
        self.hLine.setPos(mousePoint.y())


  def mouseClicked(self, event):

    if event.button() == QtCore.Qt.LeftButton and not event.modifiers():
      event.accept()
      print("leftclick")

    elif (event.button() == QtCore.Qt.LeftButton) and (event.modifiers() & QtCore.Qt.ControlModifier):
      position = event.scenePos()  ## using signal proxy turns original arguments into a tuple
      mousePoint = self.viewBox.mapSceneToView(position)
      print(mousePoint)

    elif (event.button() == QtCore.Qt.LeftButton) and (event.modifiers() & QtCore.Qt.ShiftModifier):
      print('Add Select')

    elif event.button() == QtCore.Qt.MiddleButton and not event.modifiers():
      event.accept()
      print('Pick and Assign')

    elif event.button() == QtCore.Qt.RightButton and not event.modifiers():
      event.accept()
      print('Context Menu to be activated here')



  def newMouseDragEvent(self, event):
    if (event.button() == QtCore.Qt.RightButton) and (event.modifiers() & QtCore.Qt.ShiftModifier) and not (
              event.modifiers() & QtCore.Qt.ControlModifier):
      print("RightDrag + Shift")
      if event.isStart():
        position = event.buttonDownPos()
        print("start ",position)

      elif event.isFinish():
        position = event.pos()
        print("end ",position)

      event.accept()

    elif (event.button() == QtCore.Qt.LeftButton) and (event.modifiers()
                                                       & QtCore.Qt.ControlModifier) and (
              event.modifiers() & QtCore.Qt.ShiftModifier):
        # Pick in area
      print('LeftDrag + Control + Shift')
      if event.isStart():
        position = event.buttonDownPos()
        print("start ",position)
      elif event.isFinish():
        position = event.pos()
        print("end ",position)
      event.accept()

    elif (event.button() == QtCore.Qt.LeftButton) and (event.modifiers() & QtCore.Qt.ShiftModifier) and not (
              event.modifiers() & QtCore.Qt.ControlModifier):
       # Add select area
      print('LeftDrag + Shift')
      if event.isStart():
        position = event.buttonDownPos()
        print("start ",position)
      elif event.isFinish():
        position = event.pos()
        print("end ",position)

      event.accept()


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

