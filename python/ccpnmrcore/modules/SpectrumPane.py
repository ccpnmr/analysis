import operator

from PySide import QtCore, QtGui, QtOpenGL
from ccpncore.gui import ViewBox

from pyqtgraph.dockarea import Dock


import pyqtgraph as pg
# this allows combining of OpenGL and ordinary Qt drawing
# the pre-calculated OpenGL is done in the drawPre() function
# then the Qt scene is drawn (presumably it's in the "Item" layer)
# then the on-the-fly Qt is drone in the drawPost() function
# both drawPre() and drawPost() are called from the scene code
# most drawing happens automatically because of Qt
# only the OpenGL needs to be called explicitly

# abstract class: subclass needs to implement addSpectrum()
class SpectrumPane(pg.PlotWidget):
  
  def __init__(self, project=None, parent=None, spectraVar=None, region=None, dimMapping=None, current=None, title=None, **kw):

    pg.setConfigOptions(background='w')
    pg.setConfigOptions(foreground='k')
    pg.PlotWidget.__init__(self, parent, viewBox=ViewBox.ViewBox(), axes=None, enableMenu=False, background='w', foreground='k')
    self.axes = self.plotItem.axes
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
    self.dragEnterEvent = self.dragEnterEvent
    self.setAcceptDrops(True)
    self.dropEvent = self.dropEvent
    self.crossHair = self.createCrossHair()
    self.scene().sigMouseMoved.connect(self.mouseMoved)

    if spectraVar is None:
      spectraVar = []


    self.setSpectra(spectraVar, region, dimMapping)

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
    self.positionBox.setText("X: %.3f  I: %.2E" % position)


  def zoomToRegion(self, region):
    self.widget.setXRange(region[0],region[1])
    self.widget.setYRange(region[2],region[3])

  def zoomX(self, region):
    self.widget.setXRange(region[0],region[1])

  def zoomY(self, region):
    self.widget.setYRange(region[0],region[1])

  def zoomAll(self):
    self.widget.autoRange()

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

  ##### functions called from SpectrumScene #####
    
  # can be overridden (so implemented) in subclass
  # meant for OpenGL drawing
  def showMousePosition(self, pos):

    position = self.viewBox.mapSceneToView(pos).toTuple()
    self.positionBox.setText("X: %.3f  I: %.2E" % position)

  def dragEnterEvent(self, event):
    event.accept()

  def dropEvent(self, event):
    event.accept()

  def drawPre(self, painter, rect):

    pass

  # can be overridden (so implemented) in subclass
  # meant for on-the-fly (so not scene-related) Qt drawing
  def drawPost(self, painter, rect):

    pass



  
  