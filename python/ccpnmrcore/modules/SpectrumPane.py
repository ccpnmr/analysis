import os

from collections import OrderedDict

from PySide import QtCore, QtGui, QtOpenGL

import pyqtgraph as pg
from pyqtgraph.dockarea import Dock

from ccpncore.gui import ViewBox

from ccpnmrcore.Base import Base

# abstract class: subclass needs to implement addSpectrum()

SPECTRUM_COLOURS = OrderedDict([('#ff0000','red'),
                                ('#00ffff','cyan'),
                                ('#ff8000','orange'),
                                ('#0080ff','manganese blue'),
                                ('#ffff00','yellow'),
                                ('#0000ff','blue'),
                                ('#80ff00','chartreuse'),
                                ('#8000ff','purple'),
                                ('#00ff00','green'),
                                ('#ff00ff','magenta'),
                                ('#00FF80','spring green'),
                                ('#FF0080','deep pink')])

class SpectrumPane(pg.PlotWidget, Base):
  
  def __init__(self, project=None, parent=None, spectraVar=None, current=None, title=None, pid=None, preferences=None, **kw):

    if preferences.general.colourScheme == 'light':

      self.background = pg.setConfigOptions(background='w')
      self.foreground = pg.setConfigOptions(foreground='k')
      pg.PlotWidget.__init__(self, parent, viewBox=ViewBox.ViewBox(), axes=None, enableMenu=True,
                           background='w', foreground='k')
    elif preferences.general.colourScheme == 'dark':
      self.background = self.background = pg.setConfigOptions(background='k')
      self.foreground = pg.setConfigOptions(foreground='w')
      pg.PlotWidget.__init__(self, parent, viewBox=ViewBox.ViewBox(), axes=None, enableMenu=True,
                           background='k', foreground='w')

    # pg.PlotWidget.__init__(self, parent, viewBox=ViewBox.ViewBox(), axes=None, enableMenu=True,
    #                        background='w', foreground='k')
    Base.__init__(self,project=project, **kw)
    self.axes = self.plotItem.axes
    self.plotItem.setMenuEnabled(enableMenu=True, enableViewBoxMenu=False)
    self.title = title
    self.parent = parent
    self.project = project
    self.pid = pid
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
    self.scene().sigMouseMoved.connect(self.mouseMoved)
    # print('parent',parent)
    if parent is None:
      self.dock = Dock(name=self.title, size=(1100,1300))
    elif isinstance(parent, Dock):
      self.dock = parent
    else:
      self.dock = None
    self.spectrumToolbar = QtGui.QToolBar()
    self.spectrumUtilToolbar = QtGui.QToolBar()
    # self.spectrumToolbar.setSizePolicy(QtGui.QSizePolicy.Fixed,QtGui.QSizePolicy.Fixed)
    spectrumToolBarColor = QtGui.QColor(214,215,213)
    palette = QtGui.QPalette(self.spectrumToolbar.palette())
    palette.setColor(QtGui.QPalette.Button,spectrumToolBarColor)
    #self.spectrumToolbar.setSizePolicy(QtGui.QSizePolicy.Expanding,QtGui.QSizePolicy.Expanding)
    if self.dock:
      self.dock.addWidget(self.spectrumToolbar, 0, 0, 2, 9)
    self.spectrumIndex = 1
    self.viewBox.current = current
    self.positionBox = QtGui.QLabel()
    if self.dock:
      self.dock.addWidget(self.positionBox, 0, 10, 2, 1)
    self.scene().sigMouseMoved.connect(self.showMousePosition)
    if self.dock:
      self.dock.addWidget(self, 2, 0, 1, 11)

    if spectraVar is None:
      spectraVar = []

    self.setSpectra(spectraVar)

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
    
  def showMousePosition(self, pos):

    position = self.viewBox.mapSceneToView(pos).toTuple()
    self.positionBox.setText("X: %.3f  Y: %.3f" % position)


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
        
  def addSpectrum(self, spectrumVar, dimMapping=None):

    raise Exception('should be implemented in subclass')

  def addSpectra(self, spectrumVars):
    for spectrumVar in spectrumVars:
      self.addSpectrum(spectrumVar)

  def setSpectra(self, spectraVar):

    self.clearSpectra()
    for spectrumVar in spectraVar:
      self.addSpectrum(spectrumVar)

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
          print(filePaths[0])
          self.parent.loadSpectra(filePaths[0])
      elif len(filePaths) > 1:
        [self.parent.loadSpectra(filePath) for filePath in filePaths]


    else:
      data = (event.mimeData().retrieveData('application/x-qabstractitemmodeldatalist', str))
      pidData = str(data.data(),encoding='utf-8')
      WHITESPACE_AND_NULL = ['\x01', '\x00', '\n','\x1e','\x02','\x03','\x04','\x0e']
      pidData2 = [s for s in pidData if s not in WHITESPACE_AND_NULL]
      actualPid = ''.join(map(str, pidData2))
      spectrum = self.getObject(actualPid)
      self.addSpectrum(spectrum)
      self.current.spectrum = spectrum
      self.current.pane = self





  
  
