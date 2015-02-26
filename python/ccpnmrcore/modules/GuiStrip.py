__author__ = 'simon'

import pyqtgraph as pg
import os
from functools import partial

from PySide import QtGui, QtCore

from ccpn import Spectrum
from ccpncore.gui.Label import Label
from ccpncore.gui import ViewBox

from ccpnmrcore.gui.Axis import Axis
from ccpnmrcore.DropBase import DropBase


import copy

class GuiStrip(DropBase, pg.PlotWidget): # DropBase needs to be first, else the drop events are not processed

  sigClicked = QtCore.Signal(object, object)

  def __init__(self):
    self.stripFrame = self._parent.stripFrame
    self.guiSpectrumDisplay = self._parent  # NBNB TBD is it worth keeping both?
    # self.apiStrip = apiStrip
    #
    # apiStrip.guiStrip = self  # runtime only


    pg.PlotWidget.__init__(self, viewBox=ViewBox.ViewBox(), axes=None, enableMenu=True)

    DropBase.__init__(self, self._parent._appBase, self.dropCallback)
    # if self.appBase.preferences.general.colourScheme == 'light':
    #   background = 'w'
    #   foreground = 'k'
    #   print(background)
    # else:
    background = 'k'
    foreground = 'w'
    # self.plotItem.setParentItem(self.dock.stripFrame)
    # pg.setConfigOption('background', background)
    # pg.setConfigOption('foreground', foreground)
    self.setBackground(background)
    # self.setAcceptDrops(True)
    # self.setForegroundBrush(foreground)
    # print(dir(self))
    self.current = self._appBase.current
    # self.plotItem.setAcceptDrops(True)
    self.axes = self.plotItem.axes
    self.plotItem.setMenuEnabled(enableMenu=True, enableViewBoxMenu=False)
    self.viewBox = self.plotItem.vb
    self.xAxis = Axis(self, orientation='top')
    self.yAxis = Axis(self, orientation='left')
    self.gridShown = True
    self.axes['left']['item'].hide()
    self.axes['right']['item'].show()
    # self.axes['bottom']['item'].orientation = 'top'
    # self.axes['right']['item'].orientation = 'left'
    self.axes['bottom']['item'].setPen(pg.functions.mkPen('w'))
    self.axes['right']['item'].setPen(pg.functions.mkPen('w'))
    self.textItem = pg.TextItem(text='Hn', color=(255, 255, 255))
    self.textItem.setPos(self.viewBox.boundingRect().bottomLeft())
    self.textItem2 = pg.TextItem(text='Nh', color=(255, 255, 255))
    self.textItem2.setPos(self.viewBox.boundingRect().topRight())
    self.viewBox.sigStateChanged.connect(self.moveAxisCodeLabels)
    self.scene().addItem(self.textItem)
    self.scene().addItem(self.textItem2)
    self.grid = pg.GridItem()
    self.addItem(self.grid)
    self.setMinimumWidth(200)
    # self.plotItem.resizeEvent = self.resizeEvent
    print('layout', self.plotItem.layout)
    self.plotItem.layout = QtGui.QGridLayout()
    print('layout', self.plotItem.layout)
    self.createCrossHair()
    proxy = pg.SignalProxy(self.scene().sigMouseMoved, rateLimit=60, slot=self.mouseMoved)
    self.scene().sigMouseMoved.connect(self.mouseMoved)
    self.scene().sigMouseMoved.connect(self.showMousePosition)
    self.storedZooms = []
    self.stripCount = 0
    self.stripFrame.layout().addWidget(self, 0, len(self._parent.strips))
    # self.addSpinSystemLabel()
    # print(self.spinSystemLabel)

  def addSpinSystemLabel(self):
    self.spinSystemLabel = Label(self, hAlign='center', dragDrop=True)
    self.spinSystemLabel.setText("Spin systems shown here")
    self.spinSystemLabel.setFixedHeight(30)
    self.spinSystemLabel.pid = self.pid
    self._parent.stripNumber+=1
    self.plotItem.layout.addItem(self.spinSystemLabel, 4, 0)
    # self.layout().addWidget(self.spinSystemLabel)

  def moveAxisCodeLabels(self):
    self.textItem.setPos(self.viewBox.boundingRect().bottomLeft())
    self.textItem2.setPos(self.viewBox.boundingRect().topRight())

  def hideCrossHairs(self):
    for strip in self.guiSpectrumDisplay.guiStrips:
      strip.hideCrossHair()

  def createCrossHair(self):
    self.vLine = pg.InfiniteLine(angle=90, movable=False, pen='w')
    self.hLine = pg.InfiniteLine(angle=0, movable=False, pen='w')
    self.addItem(self.vLine, ignoreBounds=True)
    self.addItem(self.hLine, ignoreBounds=True)
    self._appBase.hLines.append(self.hLine)
    self._appBase.vLines.append(self.vLine)

  def toggleCrossHair(self):
    if self.crossHairShown:
      self.hideCrossHair()
    else:
      self.showCrossHair()

  def showCrossHair(self):
      for vLine in self._appBase.vLines:
        vLine.show()
      for hLine in self._appBase.hLines:
        hLine.show()
      self.crossHairAction.setChecked(True)
      self.crossHairShown = True

  def hideCrossHair(self):
    for vLine in self._appBase.vLines:
        vLine.hide()
    for hLine in self._appBase.hLines:
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
    if self.sceneBoundingRect().contains(position):
        self.mousePoint = self.viewBox.mapSceneToView(position)
        for vLine in self._appBase.vLines:
          vLine.setPos(self.mousePoint.x())
        for hLine in self._appBase.hLines:
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

    # if isinstance(dropObject, Strip):

