"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (www.ccpn.ac.uk) 2014 - $Date: 2014-06-04 18:13:10 +0100 (Wed, 04 Jun 2014) $"
__credits__ = "Wayne Boucher, Rasmus H Fogh, Simon P Skinner, Geerten W Vuister"
__license__ = ("CCPN license. See www.ccpn.ac.uk/license"
              "or ccpncore.memops.Credits.CcpnLicense for license text")
__reference__ = ("For publications, please use reference from www.ccpn.ac.uk/license"
                " or ccpncore.memops.Credits.CcpNmrReference")

#=========================================================================================
# Last code modification:
#=========================================================================================
__author__ = "$Author: rhfogh $"
__date__ = "$Date: 2014-06-04 18:13:10 +0100 (Wed, 04 Jun 2014) $"
__version__ = "$Revision: 7686 $"

#=========================================================================================
# Start of code
#=========================================================================================
__author__ = 'simon'

import pyqtgraph as pg
import os
from functools import partial

from PyQt4 import QtGui, QtCore

from ccpn import Spectrum
from ccpncore.gui.Label import Label
from ccpncore.gui.PlotWidget import PlotWidget
from ccpncore.gui.Widget import Widget
from ccpncore.memops import Notifiers

from ccpnmrcore.gui.Axis import Axis
from ccpnmrcore.DropBase import DropBase

def sufficientlyDifferentWidth(region1, region2):
  
  w1 = abs(region1[1] - region1[0])
  w2 = abs(region2[1] - region2[0])
  d = abs(w1 - w2)
  
  return d > 1.0e-5 * max(w1, w2)
    
def scaleRegion(otherPreviousRegion, region, previousRegion):

  otherPreviousRegionWidth = abs(otherPreviousRegion[1] - otherPreviousRegion[0])
  regionWidth = abs(region[1] - region[0])
  previousRegionWidth = abs(previousRegion[1] - previousRegion[0])
  
  otherRegionWidth = otherPreviousRegionWidth * regionWidth / previousRegionWidth
  otherRegionPosition = 0.5 * (otherPreviousRegion[1] + otherPreviousRegion[0])
  
  return (otherRegionPosition - 0.5*otherRegionWidth, otherRegionPosition + 0.5*otherRegionWidth)
  
class GuiStrip(DropBase, Widget): # DropBase needs to be first, else the drop events are not processed

  sigClicked = QtCore.Signal(object, object)

  def __init__(self):
    
    self.stripFrame = self._parent.stripFrame
    self.guiSpectrumDisplay = self._parent  # NBNB TBD is it worth keeping both?

    Widget.__init__(self)
    DropBase.__init__(self, self._parent._appBase, self.dropCallback)

    self.plotWidget = PlotWidget(self.stripFrame, appBase=self._parent._appBase,
              dropCallback=self.dropCallback)#, gridSpan=(1, 1))
    self.stripFrame.layout().addWidget(self.plotWidget, 0, self.guiSpectrumDisplay.orderedStrips.index(self))

    if self._parent._appBase.preferences.general.colourScheme == 'light':
      self.background = 'w'
      self.foreground = 'k'
    else:
      self.background = 'k'
      self.foreground = 'w'
    pg.setConfigOption('background', self.background)
    pg.setConfigOption('foreground', self.foreground)
    self.plotWidget.setBackground(self.background)
    self.plotWidget.plotItem.axes['top']['item']
    self._appBase = self.guiSpectrumDisplay._appBase

    self.plotItem = self.plotWidget.plotItem
    self.plotItem.setMenuEnabled(enableMenu=True, enableViewBoxMenu=False)
    self.viewBox = self.plotItem.vb
    self.viewBox.setXRange(*self.orderedAxes[0].region)
    self.viewBox.setYRange(*self.orderedAxes[1].region)
    self.xAxis = Axis(self.plotWidget, orientation='top', pen=self.foreground,
                      viewBox=self.viewBox, axisCode=self.orderedAxes[0].code)
    self.yAxis = Axis(self.plotWidget, orientation='left', pen=self.foreground,
                      viewBox=self.viewBox, axisCode=self.orderedAxes[1].code)
    self.gridShown = True
    self.textItem = pg.TextItem(text=self.pid, color='w')
    self.textItem.setPos(self.viewBox.boundingRect().topLeft())
    self.plotWidget.scene().addItem(self.textItem)
    self.viewBox.sigStateChanged.connect(self.moveAxisCodeLabels)
    self.viewBox.sigRangeChanged.connect(self.updateRegion)
    ###proxy = pg.SignalProxy(self.viewBox.sigRangeChanged, rateLimit=10, slot=self.updateRegion)
    self.grid = pg.GridItem()
    self.plotWidget.addItem(self.grid)
    self.setMinimumWidth(200)
    self.createCrossHair()
    proxy2 = pg.SignalProxy(self.plotWidget.scene().sigMouseMoved, rateLimit=60, slot=self.mouseMoved)
    self.plotWidget.scene().sigMouseMoved.connect(self.mouseMoved)
    self.plotWidget.scene().sigMouseMoved.connect(self.showMousePosition)
    self.storedZooms = []
    
    self.beingUpdated = False
    self.xPreviousRegion, self.yPreviousRegion = self.viewBox.viewRange()
    
    Notifiers.registerNotify(self.axisRegionUpdated, 'ccpnmr.gui.Task.Axis', 'setPosition')
    Notifiers.registerNotify(self.axisRegionUpdated, 'ccpnmr.gui.Task.Axis', 'setWidth')

  def addStrip(self):

    self.strips[0].clone()

  def updateRegion(self, viewBox):
    # this is called when the viewBox is changed on the screen via the mouse
    
    # this code is complicated because need to keep viewBox region and axis region in sync
    # and there can be different viewBoxes with the same axis

    assert viewBox is self.viewBox, 'viewBox = %s, self.viewBox = %s' % (viewBox, self.viewBox)
    
    if self.beingUpdated:
      return
    
    self.beingUpdated = True
    
    try:
      
      xPreviousRegion = self.xPreviousRegion
      yPreviousRegion = self.yPreviousRegion
      xRegion, yRegion = viewBox.viewRange()
    
      xIsChanged = sufficientlyDifferentWidth(xRegion, xPreviousRegion) if xPreviousRegion else True
      yIsChanged = sufficientlyDifferentWidth(yRegion, yPreviousRegion) if yPreviousRegion else True
      
      spectrumDisplay = self.guiSpectrumDisplay
      if xIsChanged and yIsChanged and spectrumDisplay.stripDirection is not None:
        for otherStrip in spectrumDisplay.strips:
          if otherStrip is self:
            continue
          otherStrip.beingUpdated = True
          xOtherPreviousRegion, yOtherPreviousRegion = otherStrip.xPreviousRegion, otherStrip.yPreviousRegion
          if spectrumDisplay.stripDirection == 'Y':
            # x axis needs updating, y axis happens automatically below
            xOtherRegion = scaleRegion(xOtherPreviousRegion, yRegion, yPreviousRegion)
            otherStrip.viewBox.setXRange(*xOtherRegion)
            otherStrip.viewBox.setYRange(*yRegion)
            otherStrip.orderedAxes[0].region = otherStrip.xPreviousRegion = xOtherRegion
            otherStrip.yPreviousRegion = yRegion
          else: # spectrumDisplay.stripDirection == 'X'
            # y axis needs updating, x axis happens automatically below
            yOtherRegion = scaleRegion(yOtherPreviousRegion, xRegion, xPreviousRegion)
            otherStrip.viewBox.setYRange(*yOtherRegion)
            otherStrip.viewBox.setXRange(*xRegion)
            otherStrip.orderedAxes[1].region = otherStrip.yPreviousRegion = yOtherRegion
            otherStrip.xPreviousRegion = xRegion
    
      self.orderedAxes[0].region = self.xPreviousRegion = xRegion
      self.orderedAxes[1].region = self.yPreviousRegion = yRegion    
              
    finally:
      
      self.beingUpdated = False
      if xIsChanged and yIsChanged and spectrumDisplay.stripDirection is not None:
        for otherStrip in self.guiSpectrumDisplay.strips:
          if otherStrip is self:
            continue
          otherStrip.beingUpdated = False

  def axisRegionUpdated(self, apiAxis):
    # this is called when the api region (position and/or width) is changed
    
    xAxis, yAxis = self.orderedAxes[:2]
    if apiAxis not in (xAxis._wrappedData, yAxis._wrappedData):
      return
      
    if self.beingUpdated:
      return
      
    self.beingUpdated = True
        
    try:
      xRegion = xAxis.region
      yRegion = yAxis.region
      self.viewBox.setXRange(*xRegion)
      self.viewBox.setYRange(*yRegion)
    finally:
      self.beingUpdated = False

  def addSpinSystemLabel(self):
    self.spinSystemLabel = Label(self.stripFrame, grid=(1, self.guiSpectrumDisplay.orderedStrips.index(self)),
                                 hAlign='center', dragDrop=True, pid=self.pid)
    self.spinSystemLabel.setText("Spin systems shown here")
    self.spinSystemLabel.setFixedHeight(30)
    # self.spinSystemLabel.pid = self.pid
    # print(self.pid)lo



  def moveAxisCodeLabels(self):
    self.xAxis.textItem.setPos(self.viewBox.boundingRect().bottomLeft())
    self.yAxis.textItem.setPos(self.viewBox.boundingRect().topRight())
    self.textItem.setPos(self.viewBox.boundingRect().topLeft())

  def hideCrossHairs(self):
    for strip in self.guiSpectrumDisplay.guiStrips:
      strip.hideCrossHair()

  def createCrossHair(self):
    self.vLine = pg.InfiniteLine(angle=90, movable=False, pen=self.foreground)
    self.hLine = pg.InfiniteLine(angle=0, movable=False, pen=self.foreground)
    self.plotWidget.addItem(self.vLine, ignoreBounds=True)
    self.plotWidget.addItem(self.hLine, ignoreBounds=True)
    self.guiSpectrumDisplay._appBase.hLines.append(self.hLine)
    self.guiSpectrumDisplay._appBase.vLines.append(self.vLine)

  def toggleCrossHair(self):
    if self.crossHairShown:
      self.hideCrossHair()
    else:
      self.showCrossHair()

  def showCrossHair(self):
      for vLine in self.guiSpectrumDisplay._appBase.vLines:
        vLine.show()
      for hLine in self.guiSpectrumDisplay._appBase.hLines:
        hLine.show()
      self.crossHairAction.setChecked(True)
      self.crossHairShown = True

  def hideCrossHair(self):
    for vLine in self.guiSpectrumDisplay._appBase.vLines:
        vLine.hide()
    for hLine in self.guiSpectrumDisplay._appBase.hLines:
        hLine.hide()
    self.crossHairAction.setChecked(False)
    self.crossHairShown = False

  def toggleGrid(self):
    if self.grid.isVisible():
      self.grid.hide()
    else:
      self.grid.show()

  def mouseMoved(self, event):
    position = event
    if self.plotWidget.sceneBoundingRect().contains(position):
        self.mousePoint = self.viewBox.mapSceneToView(position)
        for vLine in self.guiSpectrumDisplay._appBase.vLines:
          vLine.setPos(self.mousePoint.x())
        for hLine in self.guiSpectrumDisplay._appBase.hLines:
          hLine.setPos(self.mousePoint.y())
    return self.mousePoint

  def showMousePosition(self, pos):
    position = self.viewBox.mapSceneToView(pos)
    self.guiSpectrumDisplay.positionBox.setText("X: %.3f  Y: %.3f" % (position.x(), position.y()))

  def zoomToRegion(self, region):
    self.setXRange(region[0],region[1])
    self.setYRange(region[2],region[3])

  def zoomX(self, region):
    self.setXRange(region[0],region[1])

  def zoomY(self, region):
    self.setYRange(region[0],region[1])

  def zoomAll(self):
    self.autoRange()

  def zoomTo(self, x1, x2, y1, y2):
    self.zoomToRegion([float(x1.text()),float(x2.text()),float(y1.text()),float(y2.text())])
    self.zoomPopup.close()

  def raiseZoomPopup(self):
    self.zoomPopup = QtGui.QDialog()
    layout = QtGui.QGridLayout()
    layout.addWidget(QtGui.QLabel(text='x1'), 0, 0)
    x1 = QtGui.QLineEdit()
    layout.addWidget(x1, 0, 1, 1, 1)
    layout.addWidget(QtGui.QLabel(text='x2'), 0, 2)
    x2 = QtGui.QLineEdit()
    layout.addWidget(x2, 0, 3, 1, 1)
    layout.addWidget(QtGui.QLabel(text='y1'), 1, 0,)
    y1 = QtGui.QLineEdit()
    layout.addWidget(y1, 1, 1, 1, 1)
    layout.addWidget(QtGui.QLabel(text='y2'), 1, 2)
    y2 = QtGui.QLineEdit()
    layout.addWidget(y2, 1, 3, 1, 1)
    okButton = QtGui.QPushButton(text="OK")
    okButton.clicked.connect(partial(self.zoomTo,x1,x2,y1,y2))
    cancelButton = QtGui.QPushButton(text='Cancel')
    layout.addWidget(okButton,2, 1)
    layout.addWidget(cancelButton, 2, 3)
    cancelButton.clicked.connect(self.zoomPopup.close)
    self.zoomPopup.setLayout(layout)
    self.zoomPopup.exec_()

  def storeZoom(self):
    self.storedZooms.append(self.viewBox.viewRange())

  def restoreZoom(self):
    if len(self.storedZooms) != 0:
      restoredZoom = self.storedZooms.pop()
      self.setXRange(restoredZoom[0][0], restoredZoom[0][1])
      self.setYRange(restoredZoom[1][0], restoredZoom[1][1])

  def showSpectrum(self, guiSpectrumView):
    raise Exception('should be implemented in subclass')

  def dropCallback(self, dropObject):

    if isinstance(dropObject, Spectrum):
      self.displaySpectrum(dropObject)

    else:
      if self._parent.assignmentDirection == 'i-1':

        self.guiSpectrumDisplay.stripFrame.setLayoutDirection(QtCore.Qt.RightToLeft)
        self.guiSpectrumDisplay.copyStrip(dropObject, newIndex=0)

      else:
        print('i+1')
        self.guiSpectrumDisplay.stripFrame.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.guiSpectrumDisplay.copyStrip(dropObject)

    # self.guiSpectrumDisplay.regridStrips()
