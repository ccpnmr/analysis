import os

from PySide import QtCore, QtGui, QtOpenGL
from ccpncore.gui import ViewBox

from pyqtgraph.dockarea import Dock

from collections import OrderedDict

from ccpncore.lib.memops.Implementation.Project import loadDataSource

import pyqtgraph as pg
# this allows combining of OpenGL and ordinary Qt drawing
# the pre-calculated OpenGL is done in the drawPre() function
# then the Qt scene is drawn (presumably it's in the "Item" layer)
# then the on-the-fly Qt is drone in the drawPost() function
# both drawPre() and drawPost() are called from the scene code
# most drawing happens automatically because of Qt
# only the OpenGL needs to be called explicitly

# abstract class: subclass needs to implement addSpectrum()

SPECTRUM_COLOURS = OrderedDict([('#FF0000','red'),
                                ('#00FFFF','cyan'),
                                ('#FF8000','orange'),
                                ('#0080FF','manganese blue'),
                                ('#FFFF00','yellow'),
                                ('#0000FF','blue'),
                                ('#80FF00','chartreuse'),
                                ('#8000FF','purple'),
                                ('#00FF00','green'),
                                ('#FF00FF','magenta'),
                                ('#00FF80','spring green'),
                                ('#FF0080','deep pink')])

class SpectrumPane(pg.PlotWidget):
  
  def __init__(self, project=None, parent=None, spectraVar=None, region=None, dimMapping=None, current=None, title=None, **kw):

    pg.setConfigOptions(background='w')
    pg.setConfigOptions(foreground='k')

    pg.PlotWidget.__init__(self, parent, viewBox=ViewBox.ViewBox(), axes=None, enableMenu=True,
                           background='w', foreground='k')
    self.axes = self.plotItem.axes
    self.plotItem.setMenuEnabled(enableMenu=True, enableViewBoxMenu=False)
    self.title = title
    self.parent = parent
    self.project = project
    self.viewBox = self.plotItem.vb
    self.viewBox.parent = self
    self.viewBox.current = current
    self.xAxis = pg.AxisItem(orientation='top')
    self.yAxis = pg.AxisItem(orientation='right')
    self.axes['left']['item'].hide()
    self.axes['right']['item'].show()
    self.axes['bottom']['item'].orientation = 'bottom'
    self.setAcceptDrops(True)
    self.crossHair = self.createCrossHair()
    self.viewBox.invertX()
    self.scene().sigMouseMoved.connect(self.mouseMoved)
    self.dock = Dock(name=self.title, size=(1100, 1300))
    # self.dock.setStyleSheet("border: 1px solid #44a")

    self.spectrumToolbar = QtGui.QToolBar()
    spectrumToolBarColor = QtGui.QColor(214,215,213)
    palette = QtGui.QPalette(self.spectrumToolbar.palette())
    palette.setColor(QtGui.QPalette.Button,spectrumToolBarColor)
    # self.spectrumToolbar.setSizePolicy(QtGui.QSizePolicy.Fixed,QtGui.QSizePolicy.Fixed)
    self.dock.addWidget(self.spectrumToolbar, 0, 0, 2, 7)
    self.spectrumUtilToolbar = QtGui.QToolBar()
    self.spectrumUtilToolbar.setSizePolicy(QtGui.QSizePolicy.Fixed,QtGui.QSizePolicy.Fixed)
    self.dock.addWidget(self.spectrumUtilToolbar, 0, 7, 2, 3)
    self.spectrumIndex = 1
    self.viewBox.current = current
    self.positionBox = QtGui.QLabel()
    self.dock.addWidget(self.positionBox, 0, 10, 2, 1)
    # self.positionBox.setSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
    self.scene().sigMouseMoved.connect(self.showMousePosition)
    self.dock.addWidget(self, 2, 0, 1, 11)

    if spectraVar is None:
      spectraVar = []


    self.setSpectra(spectraVar, region, dimMapping)

  def clicked(self, spectrum):
    self.current.spectrum = spectrum.parent
    self.current.spectra.append(spectrum.parent)
    self.parent.pythonConsole.write('current.spectrum='+str(self.current.spectrum)+'\n')
    self.parent.statusBar().showMessage('current.spectrum='+str(self.current.spectrum.pid))

  def createCrossHair(self):
    self.vLine = pg.InfiniteLine(angle=90, movable=False)
    self.hLine = pg.InfiniteLine(angle=0, movable=False)
    self.addItem(self.vLine, ignoreBounds=True)
    self.addItem(self.hLine, ignoreBounds=True)

  def mouseMoved(self, event):
    position = event
    if self.sceneBoundingRect().contains(position):
        mousePoint = self.viewBox.mapSceneToView(position)
        self.vLine.setPos(mousePoint.x())
        self.hLine.setPos(mousePoint.y())

  def addSpectra(self, spectra):
    for spectrum in spectra:
      self.addSpectrum(spectrum)

  def showMousePosition(self, pos):

    position = self.viewBox.mapSceneToView(pos).toTuple()
    self.positionBox.setText("X: %.3f  I: %.2E" % position)


  def zoomToRegion(self, region):
    self.setXRange(region[0],region[1])
    self.setYRange(region[2],region[3])

  def zoomX(self, region):
    self.setXRange(region[0],region[1])

  def zoomY(self, region):
    self.setYRange(region[0],region[1])

  def zoomAll(self):
    self.autoRange()


  ##### functions used externally #####

  def clearSpectra(self):
    
    self.spectrumItems = []
    self.region = None
    self.dimMapping = None
        
  def addSpectrum(self, spectrumVar, region=None, dimMapping=None):

    raise Exception('should be implemented in subclass')

  def setSpectra(self, spectraVar, region=None, dimMapping=None):

    self.clearSpectra()
    for spectrumVar in spectraVar:
      self.addSpectrum(spectrumVar, region, dimMapping)

  def showMousePosition(self, pos):

    position = self.viewBox.mapSceneToView(pos).toTuple()
    self.positionBox.setText("X: %.3f  I: %.2E" % position)

  def dragEnterEvent(self, event):
    event.accept()

  def dropEvent(self,event):
    event.accept()
    if isinstance(self.parent, QtGui.QGraphicsScene):
      event.ignore()
      return

    if event.mimeData().urls():

      filePaths = [url.path() for url in event.mimeData().urls()]
      print(filePaths)
      print(len(filePaths))
      if len(filePaths) == 1:
        for dirpath, dirnames, filenames in os.walk(filePaths[0]):
          if dirpath.endswith('memops') and 'Implementation' in dirnames:
            self.parent.openProject(filePaths[0])
            self.addSpectra(self.project.spectra)

        else:
          self.parent.loadSpectra(filePaths[0])

    else:
      data = (event.mimeData().retrieveData('application/x-qabstractitemmodeldatalist', str))
      pidData = str(data.data(),encoding='utf-8')
      WHITESPACE_AND_NULL = ['\x01', '\x00', '\n','\x1e','\x02','\x03','\x04']
      pidData2 = [s for s in pidData if s not in WHITESPACE_AND_NULL]
      actualPid = ''.join(map(str, pidData2))
      spectrum = self.project.getById(actualPid)
      print(actualPid, spectrum)
      spectrum = self.addSpectrum(spectrum)
      self.current.spectrum = spectrum
      self.current.pane = self





  
  