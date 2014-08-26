import operator

from PySide import QtCore, QtGui, QtOpenGL

from ccpnmrcore.modules.SpectrumPane import SpectrumPane

from ccpnmrcore.modules.spectrumPane.SpectrumNdItem import SpectrumNdItem

class SpectrumNdPane(SpectrumPane):

  def __init__(self, *args, **kw):
    
    SpectrumPane.__init__(self, *args, **kw)

    self.plotItem.setAcceptDrops(True)
    
    self.setViewport(QtOpenGL.QGLWidget())
    self.setViewportUpdateMode(QtGui.QGraphicsView.FullViewportUpdate)
    self.viewBox.invertX()
    self.viewBox.invertY()
    self.fillToolBar()
    self.showGrid(x=True, y=True)
    self.region = None
          
  ##### functions used externally #####

  # overrides superclass function
  def wheelEvent(self, event, axis=None):
    if event.modifiers() & QtCore.Qt.ShiftModifier:
      if event.delta() > 0:
        self.current.spectrum.spectrumItem.raiseBaseLevel()
      else:
        self.current.spectrum.spectrumItem.lowerBaseLevel()
    elif not event.modifiers():
      QtGui.QGraphicsView.wheelEvent(self, event)
      sc = 1.001 ** event.delta()
      #self.scale *= sc
      #self.updateMatrix()
      self.scale(sc, sc)
    else:
      event.ignore



  def clearSpectra(self):
    
    SpectrumPane.clearSpectra(self)    
    self.region = None
    
  # implements superclass function
  def addSpectrum(self, spectrumVar, dimMapping=None):
    
    spectrum = self.getObject(spectrumVar)
    if spectrum.dimensionCount < 1:
      # TBD: logger message
      return
      
    # TBD: check if dimensions make sense
      
    spectrumItem = SpectrumNdItem(self, spectrum, dimMapping, self.region)
    self.scene().addItem(spectrumItem)
    spectrum.spectrumItem = spectrumItem

  def upBy8(self):
    newLevels = []
    for level in self.current.spectrum.spectrumItem.levels:
      newLevels.append(level*8)
    self.current.spectrum.spectrumItem.levels = tuple(newLevels)

  def upBy2(self):
    newLevels = []
    for level in self.current.spectrum.spectrumItem.levels:
      newLevels.append(level*2)
    self.current.spectrum.spectrumItem.levels = tuple(newLevels)

  def downBy8(self):
    newLevels = []
    for level in self.current.spectrum.spectrumItem.levels:
      newLevels.append(level/8)
    self.current.spectrum.spectrumItem.levels = tuple(newLevels)

  def downBy2(self):
    newLevels = []
    for level in self.current.spectrum.spectrumItem.levels:
      newLevels.append(level/2)
    self.current.spectrum.spectrumItem.levels = tuple(newLevels)

  def addOne(self):
    self.current.spectrum.spectrumItem.numberOfLevels +=1
    self.current.spectrum.spectrumItem.levels = self.current.spectrum.spectrumItem.getLevels()

  def subtractOne(self):
    self.current.spectrum.spectrumItem.numberOfLevels -=1
    self.current.spectrum.spectrumItem.levels = self.current.spectrum.spectrumItem.getLevels()

  def fillToolBar(self):
    self.spectrumUtilToolbar.addAction("+1", self.addOne)
    self.spectrumUtilToolbar.addAction("-1", self.subtractOne)
    self.spectrumUtilToolbar.addAction("*2", self.upBy2)
    self.spectrumUtilToolbar.addAction("/2", self.downBy2)
    self.spectrumUtilToolbar.addAction("*8", self.upBy8)
    self.spectrumUtilToolbar.addAction("/8", self.downBy8)
    self.spectrumUtilToolbar.addAction("Store Zoom", self.storeZoom)
    self.spectrumUtilToolbar.addAction("Restore Zoom", self.restoreZoom)

