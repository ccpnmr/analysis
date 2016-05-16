"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (www.ccpn.ac.uk) 2014 - $Date$"
__credits__ = "Wayne Boucher, Rasmus H Fogh, Simon P Skinner, Geerten W Vuister"
__license__ = ("CCPN license. See www.ccpn.ac.uk/license"
              "or ccpnmodel.ccpncore.memops.Credits.CcpnLicense for license text")
__reference__ = ("For publications, please use reference from www.ccpn.ac.uk/license"
                " or ccpnmodel.ccpncore.memops.Credits.CcpNmrReference")

#=========================================================================================
# Last code modification:
#=========================================================================================
__author__ = "$Author$"
__date__ = "$Date$"
__version__ = "$Revision$"

#=========================================================================================
# Start of code
#=========================================================================================
from PyQt4 import QtGui,QtCore
import pyqtgraph as pg
from pyqtgraph.Point import Point
import sys
import json
import numpy as np
class SpectrumWidget:

  def __init__(self):

    pg.setConfigOption('background', 'w')
    pg.setConfigOption('foreground', 'k')
    # if self.useOpenGL:
    #   pg.setConfigOption('useOpenGL', 'True')
    # self.viewBox = CustomViewBox()
    self.xAxis = pg.AxisItem(orientation='top')
    self.yAxis = pg.AxisItem(orientation='left')
    self.widget = pg.PlotWidget(
      enableMenu=False, axisItems={
        'bottom':self.xAxis, 'right': self.yAxis})
    # shortcutFile=open('/Users/simon/PycharmProjects/CCPN_V3/trunk/ccpnv3/shortcuts.json', 'r')
    # self.shortcuts = json.load(shortcutFile)
    # # self.createShortcuts()
    #
    # self.createCrossHair()
    ## connect cross hair (mouseMoved) and mouseClick events to QtGraphicsScene

    ## setup axes for display

    self.widget.plotItem.axes['left']['item'].hide()
    self.widget.plotItem.axes['right']['item'].show()
    # orientation left to put text on left of axis and same for top
    self.widget.plotItem.axes['right']['item'].orientation = 'left'
    self.widget.plotItem.axes['bottom']['item'].orientation = 'top'


    self.vLine = pg.InfiniteLine(angle=90)
    self.hLine = pg.InfiniteLine(angle=0)
    self.widget.addItem(self.vLine)
    self.widget.addItem(self.hLine)

    self.widget.scene().sigMouseMoved.connect(self.mouseMoved)



  def mouseMoved(self, event):
    position = event
    if self.widget.sceneBoundingRect().contains(position):
        mousePoint = self.widget.vb.mapSceneToView(position)
        self.vLine.setPos(mousePoint.x())
        self.hLine.setPos(mousePoint.y())


class CustomViewBox(pg.ViewBox):

  def __init__(self, *args, **kwds):
        pg.ViewBox.__init__(self, *args, **kwds)
        self.setMenuDisabled()


  def mouseClickEvent(self, event):

    if event.button() == QtCore.Qt.LeftButton and not event.modifiers():
      event.accept()
      print("Left Click Event")

    elif (event.button() == QtCore.Qt.LeftButton) and (
              event.modifiers() & QtCore.Qt.ControlModifier) and not (
    event.modifiers() & QtCore.Qt.ShiftModifier):
      position = event.scenePos()
      mousePoint = self.mapSceneToView(position)
      print(mousePoint)

    elif (event.button() == QtCore.Qt.LeftButton) and (
              event.modifiers() & QtCore.Qt.ShiftModifier) and not (
    event.modifiers() & QtCore.Qt.ControlModifier):
      print('Add Select')

    elif event.button() == QtCore.Qt.MiddleButton and not event.modifiers():
      event.accept()
      print('Pick and Assign')

    elif event.button() == QtCore.Qt.RightButton and not event.modifiers():
      event.accept()
      print('Context Menu to be activated here')

    if event.double():
      event.accept()
      print("Double Click event")



  def mouseDragEvent(self, event, axis=None):

    if event.button() == QtCore.Qt.LeftButton and not event.modifiers():
      pg.ViewBox.mouseDragEvent(self, event)


    elif (event.button() == QtCore.Qt.RightButton) and (
              event.modifiers() & QtCore.Qt.ShiftModifier) and not (
              event.modifiers() & QtCore.Qt.ControlModifier):
      print("RightDrag + Shift")

      if event.isFinish():
        position = event.pos()
        ## draw rectangle around highlighted area - not tied to axes yet,
        ## probably needs to be
        ax = QtCore.QRectF(Point(event.buttonDownPos(event.button())),
                           Point(position))
        self.showAxRect(ax)

      else:
        self.updateScaleBox(event.buttonDownPos(), event.pos())

      event.accept()

    elif (event.button() == QtCore.Qt.LeftButton) and (
              event.modifiers() & QtCore.Qt.ControlModifier) and (
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

    elif (event.button() == QtCore.Qt.LeftButton) and (
              event.modifiers() & QtCore.Qt.ShiftModifier) and not (
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
    ## above events remove pan abilities from plot window,
    ## need to re-implement them without changing mouseMode
    else:
      event.ignore()


###For testing
if __name__ == '__main__':

  def testMain():
    app = QtGui.QApplication(sys.argv)
    w = QtGui.QWidget()
    layout = QtGui.QGridLayout()
    widget=SpectrumWidget().widget
    layout.addWidget(widget)
    xdata = []
    ydata = []
    numPoints = 4096
    for i in range(numPoints):
       xdata.append(-3+(20/numPoints*i))
       ydata.append(1e4/np.random.random())

    spectrumXData = np.array(xdata)
    spectrumYData = np.array(ydata)
    widget.plot(spectrumXData,spectrumYData)
    w.setLayout(layout)
    w.show()
    sys.exit(app.exec_())

  testMain()
