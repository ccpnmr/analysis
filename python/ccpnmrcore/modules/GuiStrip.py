__author__ = 'simon'

import pyqtgraph as pg

import os

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
    self.axes = self.plotItem.axes
    self.plotItem.setMenuEnabled(enableMenu=True, enableViewBoxMenu=False)
    self.viewBox = self.plotItem.vb
    # self.viewBox.parent = self
    # self.viewBox.current = self.current
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
    # self.scene().sigMouseHover.connect(self.setCurrentPane)
    self.storedZooms = []
    self.spectrumItems = []
    # if spectraVar is None:
    #   spectraVar = []
    print(self)
    guiSpectrumDisplay.addWidget(self, 1, 0)
    # self.setSpectra(spectraVar)


  def createCrossHair(self):
    self.vLine = pg.InfiniteLine(angle=90, movable=False, pen='w')
    self.hLine = pg.InfiniteLine(angle=0, movable=False, pen='w')
    self.addItem(self.vLine, ignoreBounds=True, )
    self.addItem(self.hLine, ignoreBounds=True)


  def mouseMoved(self, event):
    position = event
    if self.sceneBoundingRect().contains(position):
        self.mousePoint = self.viewBox.mapSceneToView(position)
        self.vLine.setPos(self.mousePoint.x())
        self.hLine.setPos(self.mousePoint.y())
    return self.mousePoint

  def storeZoom(self):
    self.storedZooms.append(self.viewBox.viewRange())

  def restoreZoom(self):
    if len(self.storedZooms) != 0:
      restoredZoom = self.storedZooms.pop()
      self.setXRange(restoredZoom[0][0], restoredZoom[0][1])
      self.setYRange(restoredZoom[1][0], restoredZoom[1][1])


  def zoomYAll(self):
    y2 = self.viewBox.childrenBoundingRect().top()
    y1 = y2 + self.viewBox.childrenBoundingRect().height()
    self.viewBox.setYRange(y2,y1)

  def zoomXAll(self):
    x2 = self.viewBox.childrenBoundingRect().left()
    x1 = x2 + self.viewBox.childrenBoundingRect().width()
    self.viewBox.setXRange(x2,x1)



  def showSpectrum(self, guiSpectrumView):
    raise Exception('should be implemented in subclass')

  def dragEnterEvent(self, event):
    event.accept()

  def dropEvent(self,event):
    event.accept()
    # self.current.pane = self
    if isinstance(self.parent, QtGui.QGraphicsScene):
      event.ignore()
      return

    if event.mimeData().urls():
      # event.accept()
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
      # event.accept()
      data = (event.mimeData().retrieveData('application/x-qabstractitemmodeldatalist', str))
      #data = event.mimeData().text()
      print('RECEIVED mimeData: "%s"' % data)

      pidData = str(data.data(),encoding='utf-8')
      WHITESPACE_AND_NULL = ['\x01', '\x00', '\n','\x1e','\x02','\x03','\x04','\x0e','\x12', '\x0c', '\x05', '\x10', '\x14']
      pidData2 = [s for s in pidData if s not in WHITESPACE_AND_NULL]
      actualPid = ''.join(map(str, pidData2))
      # print(list(actualPid))


      spectrum = self.getObject(actualPid)
      # print(spectrum)
      self.guiSpectrumDisplay.addSpectrum(spectrum)