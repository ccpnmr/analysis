__author__ = 'simon'

import pyqtgraph as pg
import os
from functools import partial
from PySide import QtGui, QtCore
from ccpn import Spectrum
from ccpncore.gui import ViewBox
from ccpnmrcore.DropBase import DropBase
from ccpnmrcore.gui.Axis import Axis

class GuiStrip(DropBase, pg.PlotWidget): # DropBase needs to be first, else the drop events are not processed

  sigClicked = QtCore.Signal(object, object)

  def __init__(self):
    # self.stripFrame = self._parent.stripFrame
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

    #
    # self.plotItem.setParentItem(self.dock.stripFrame)
    # pg.setConfigOption('background', background)
    # pg.setConfigOption('foreground', foreground)
    self.setBackground(background)
    # self.setForegroundBrush(foreground)
    # print(dir(self))
    self.current = self._appBase.current
    self.axes = self.plotItem.axes
    self.plotItem.setMenuEnabled(enableMenu=True, enableViewBoxMenu=False)
    self.viewBox = self.plotItem.vb
    self.xAxis = Axis(self, orientation='top')
    self.yAxis = Axis(self, orientation='left')
    self.gridShown = True
    self.axes['left']['item'].hide()
    self.axes['right']['item'].show()
    self.axes['bottom']['item'].orientation = 'top'
    self.axes['right']['item'].orientation = 'left'
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
    # self.plotItem.resizeEvent = self.resizeEvent
    self.setAcceptDrops(True)
    self.createCrossHair()
    self.scene().sigMouseMoved.connect(self.mouseMoved)
    # self.scene().sigMouseHover.connect(self.setCurrentPane)
    self.scene().sigMouseMoved.connect(self.showMousePosition)
    # self.current.pane = self.guiSpectrumDisplay
    self.storedZooms = []
    self.spectrumItems = []
    self.guiSpectrumDisplay.dock.addWidget(self, 1, 1, 1, 3)


    # layout = self.stripFrame.layout()
    # if not layout:
    #   layout = QtGui.QGridLayout(self.stripFrame)
    #   layout.setContentsMargins(0, 0, 0, 0)
    #   self.stripFrame.setLayout(layout)
    #
    # # print(self.stripFrame.width())
    #
    #
    # n = len(self.guiSpectrumDisplay.apiSpectrumDisplay.strips)-1
    # layout.setColumnStretch(n, 1)
    # layout.setSpacing(1)
    # layout.addWidget(self, 0, n)
    # # self.scene().sigMouseClicked.connect(self.setCurrentPane)
    #
    # self.guiSpectrumDisplay.guiStrips.append(self)


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
    self.guiSpectrumDisplay.hLines.append(self.hLine)
    self.guiSpectrumDisplay.vLines.append(self.vLine)

  def toggleCrossHair(self):
    if self.crossHairShown:
      self.hideCrossHair()
    else:
      self.showCrossHair()

  def showCrossHair(self):
      for vLine in self.guiSpectrumDisplay.vLines:
        vLine.show()
      for hLine in self.guiSpectrumDisplay.hLines:
        hLine.show()
      self.crossHairAction.setChecked(True)
      self.crossHairShown = True

  def hideCrossHair(self):
    for vLine in self.guiSpectrumDisplay.vLines:
        vLine.hide()
    for hLine in self.guiSpectrumDisplay.hLines:
        hLine.hide()
    self.crossHairAction.setChecked(False)
    self.crossHairShown = False

  def toggleGrid(self):
    if self.grid.isVisible():
      self.grid.hide()
    else:
      self.grid.show()

  def setCurrentPane(self):
    self.guiSpectrumDisplay.currentStrip = self
    self._appBase.mainWindow.pythonConsole.write('current.pane = '+str(self.guiSpectrumDisplay.name()))
    self._appBase.current.pane = self.guiSpectrumDisplay
    # for strip in self.guiSpectrumDisplay.guiStrips:
      # strip.hideCrossHair()
    self.guiSpectrumDisplay.currentStrip.showCrossHair()

  # def mouseMoved(self, event):
  #   position = event
  #   if self.sceneBoundingRect().contains(position):
  #       self.mousePoint = self.viewBox.mapSceneToView(position)
  #       self.vLine.setPos(self.mousePoint.x())
  #       self.hLine.setPos(self.mousePoint.y())
  #   return self.mousePoint

  def mouseMoved(self, event):
    position = event
    if self.sceneBoundingRect().contains(position):
        self.mousePoint = self.viewBox.mapSceneToView(position)
        for vLine in self.guiSpectrumDisplay.vLines:
          vLine.setPos(self.mousePoint.x())
        for hLine in self.guiSpectrumDisplay.hLines:
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
      self.guiSpectrumDisplay.addSpectrum(dropObject)
