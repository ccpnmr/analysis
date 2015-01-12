__author__ = 'simon'

import pyqtgraph as pg

import os
from functools import partial

from PySide import QtGui, QtCore

from ccpncore.gui import ViewBox

from ccpnmrcore.Base import Base as GuiBase

from ccpnmrcore.gui.Axis import Axis




class GuiStrip(pg.PlotWidget, GuiBase):

  sigClicked = QtCore.Signal(object, object)

  def __init__(self, guiSpectrumDisplay, apiStrip, **kw):
    self.guiSpectrumDisplay = guiSpectrumDisplay
    # self.strip = strip
    background = 'k'
    foreground = 'w'

    pg.setConfigOptions(background=background)
    pg.setConfigOptions(foreground=foreground)
    pg.PlotWidget.__init__(self, viewBox=ViewBox.ViewBox(), axes=None, enableMenu=True,
                           background=background, foreground=foreground)

    GuiBase.__init__(self, guiSpectrumDisplay.appBase)
    self.current = guiSpectrumDisplay.appBase.current
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
    self.grid = pg.GridItem()
    self.addItem(self.grid)
    self.setAcceptDrops(True)
    self.crossHair = self.createCrossHair()
    self.scene().sigMouseMoved.connect(self.mouseMoved)
    self.scene().sigMouseHover.connect(self.setCurrentPane)
    self.scene().sigMouseMoved.connect(self.showMousePosition)
    self.storedZooms = []
    self.spectrumItems = []
    guiSpectrumDisplay.addWidget(self, 1, 0, 1, 10)

  def createCrossHair(self):
    self.vLine = pg.InfiniteLine(angle=90, movable=False, pen='w')
    self.hLine = pg.InfiniteLine(angle=0, movable=False, pen='w')
    self.addItem(self.vLine, ignoreBounds=True, )
    self.addItem(self.hLine, ignoreBounds=True)


  def setCurrentPane(self):
    self.current.pane = self

  def toggleCrossHair(self):
    if self.crossHairShown ==True:
      self.hideCrossHair()
    else:
      self.showCrossHair()
      self.crossHairShown = True

  def showCrossHair(self):
      self.vLine.show()
      self.hLine.show()
      self.crossHairAction.setChecked(True)
      self.crossHairShown = True

  def hideCrossHair(self):
    self.vLine.hide()
    self.hLine.hide()
    self.crossHairAction.setChecked(False)
    self.crossHairShown = False

  def toggleGrid(self):
    if self.grid.isVisible() == True:
      self.grid.hide()
    else:
      self.grid.show()

  def mouseMoved(self, event):
    position = event
    if self.sceneBoundingRect().contains(position):
        self.mousePoint = self.viewBox.mapSceneToView(position)
        self.vLine.setPos(self.mousePoint.x())
        self.hLine.setPos(self.mousePoint.y())
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

  def dragEnterEvent(self, event):
    event.accept()

  def dropEvent(self,event):
    event.accept()
    if isinstance(self.parent, QtGui.QGraphicsScene):
      event.ignore()
      return

    if event.mimeData().urls():
      filePaths = [url.path() for url in event.mimeData().urls()]
      if len(filePaths) == 1:
        for dirpath, dirnames, filenames in os.walk(filePaths[0]):
          if dirpath.endswith('memops') and 'Implementation' in dirnames:
            self.appBase.openProject(filePaths[0])
            self.addSpectra(self.project.spectra)

        else:
          print(filePaths[0])
          self.appBase.mainWindow.loadSpectra(filePaths[0])


      elif len(filePaths) > 1:
        [self.appBase.mainWindow.loadSpectra(filePath) for filePath in filePaths]


    else:
      data = (event.mimeData().retrieveData('application/x-qabstractitemmodeldatalist', str))
      print('RECEIVED mimeData: "%s"' % data)
      pidData = str(data.data(),encoding='utf-8')
      WHITESPACE_AND_NULL = ['\x01', '\x00', '\n','\x1e','\x02','\x03','\x04','\x0e','\x12', '\x0c', '\x05', '\x10', '\x14']
      pidData2 = [s for s in pidData if s not in WHITESPACE_AND_NULL]
      actualPid = ''.join(map(str, pidData2))
      spectrum = self.getObject(actualPid)
      self.guiSpectrumDisplay.addSpectrum(spectrum)