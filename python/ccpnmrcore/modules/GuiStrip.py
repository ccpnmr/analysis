__author__ = 'simon'

import pyqtgraph as pg
import os
from functools import partial

from PySide import QtGui, QtCore

from ccpn import Spectrum
from ccpncore.gui.Label import Label
from ccpncore.gui.PlotWidget import PlotWidget
from ccpncore.gui.Widget import Widget
from ccpncore.memops import Notifiers

from ccpnmrcore.gui.Axis import Axis
from ccpnmrcore.DropBase import DropBase


class GuiStrip(DropBase, Widget): # DropBase needs to be first, else the drop events are not processed

  sigClicked = QtCore.Signal(object, object)

  def __init__(self):
    self.stripFrame = self._parent.stripFrame
    self.guiSpectrumDisplay = self._parent  # NBNB TBD is it worth keeping both?


    Widget.__init__(self)
    DropBase.__init__(self, self._parent._appBase, self.dropCallback)
    self.plotWidget = PlotWidget(self.stripFrame, appBase=self._parent._appBase,
                      dropCallback=self.dropCallback, grid=(0, self.guiSpectrumDisplay.stripCount-1))
    # self.plotWidget = PlotWidget(self.stripFrame, appBase=self._parent._appBase,
    #           dropCallback=self.dropCallback, grid=(0, self.guiSpectrumDisplay.stripCount-1)) #, gridSpan=(1, 1))


    if self._parent._appBase.preferences.general.colourScheme == 'light':
      self.background = 'w'
      self.foreground = 'k'
    else:
      self.background = 'k'
      self.foreground = 'w'
    pg.setConfigOption('background', self.background)
    pg.setConfigOption('foreground', self.foreground)
    self.plotWidget.setBackground(self.background)
    # self.setAcceptDrops(True)
    # self.plotWidget.setAcceptDrops(True)
    self._appBase = self.guiSpectrumDisplay._appBase
    # self.setForegroundBrush(foreground)

    self.plotItem = self.plotWidget.plotItem
    self.plotItem.setMenuEnabled(enableMenu=True, enableViewBoxMenu=False)
    # self.plotItem.setAcceptDrops(True)
    self.axes = self.plotItem.axes
    self.viewBox = self.plotItem.vb
    # self.xRegion = self.orderedAxes[0].region
    # self.yRegion = self.orderedAxes[1].region
    self.viewBox.setXRange(*self.orderedAxes[0].region)
    self.viewBox.setYRange(*self.orderedAxes[1].region)
    self.xAxis = Axis(self.plotWidget, orientation='top', pen=self.foreground,
                      viewBox=self.viewBox, axisCode=self.orderedAxes[0].code)
    self.yAxis = Axis(self.plotWidget, orientation='left', pen=self.foreground,
                      viewBox=self.viewBox, axisCode=self.orderedAxes[1].code)
    self.gridShown = True
    self.viewBox.sigStateChanged.connect(self.moveAxisCodeLabels)
    self.viewBox.sigRangeChanged.connect(self.updateRegion)
    self.grid = pg.GridItem(pen=self.foreground)
    # self.plotWidget.addItem(self.grid)
    # self.setMinimumWidth(200)
    self.createCrossHair()
    proxy = pg.SignalProxy(self.plotWidget.scene().sigMouseMoved, rateLimit=60, slot=self.mouseMoved)
    self.plotWidget.scene().sigMouseMoved.connect(self.mouseMoved)
    self.plotWidget.scene().sigMouseMoved.connect(self.showMousePosition)
    self.storedZooms = []
    self.addSpinSystemLabel()
    
    self.eventOriginator = None
    Notifiers.registerNotify(self.axisRegionUpdated, 'ccpnmr.gui.Task.Axis', 'setPosition')
    Notifiers.registerNotify(self.axisRegionUpdated, 'ccpnmr.gui.Task.Axis', 'setWidth')

  # def addAStrip(self):
  #
  #   newStrip = self.strips[0].clone()
  #   print(newStrip.pid)

  def updateRegion(self, event):
    # this is called when the viewBox is changed on the screen via the mouse
    if self.eventOriginator:
      return
    self.eventOriginator = self
    
    xRegion = self.viewBox.viewRange()[0]
    yRegion = self.viewBox.viewRange()[1]
    self.orderedAxes[0].region = xRegion
    self.orderedAxes[1].region = yRegion
    #for spectrumView in self.spectrumViews:
    #  spectrumView.update()
    #self.update()
    
    self.eventOriginator = None

  def axisRegionUpdated(self, apiAxis):
    # this is called when the api region (position and/or width) is changed
    
    if self.eventOriginator:
      return
    self.eventOriginator = self
    
    xRegion = self.orderedAxes[0].region
    yRegion = self.orderedAxes[1].region
    self.viewBox.setXRange(*xRegion)
    self.viewBox.setYRange(*yRegion)
    #for spectrumView in self.spectrumViews:
    #  spectrumView.update()
    #self.update()
    
    self.eventOriginator = None

  def addSpinSystemLabel(self):
    self.spinSystemLabel = Label(self.stripFrame, grid=(1, self.guiSpectrumDisplay.stripCount-1),
                                 hAlign='center', dragDrop=True, pid=self.pid)
    self.spinSystemLabel.setText("Spin systems shown here")
    self.spinSystemLabel.setFixedHeight(30)
    # self.spinSystemLabel.pid = self.pid
    # print(self.pid)lo



  def moveAxisCodeLabels(self):
    self.xAxis.textItem.setPos(self.viewBox.boundingRect().bottomLeft())
    self.yAxis.textItem.setPos(self.viewBox.boundingRect().topRight())

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
    position = self.viewBox.mapSceneToView(pos).toTuple()
    self.guiSpectrumDisplay.positionBox.setText("X: %.3f  Y: %.3f" % position)

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
      self.guiSpectrumDisplay.copyStrip(dropObject, newIndex=0)
      # print(dropObject._parent)
      # print('dropObject',dropObject)
      dropObject.delete()
      dropObject.clone()
      # # print(newStrip)
      # print('strip cloned')
    # else:
    #   print('not a spectrum')

