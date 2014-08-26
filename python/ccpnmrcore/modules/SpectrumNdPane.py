import operator

from PySide import QtCore, QtGui, QtOpenGL

from ccpnmrcore.modules.SpectrumPane import SpectrumPane, SPECTRUM_COLOURS

from ccpnmrcore.modules.spectrumPane.SpectrumNdItem import SpectrumNdItem

from functools import partial

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
    self.colourIndex = 0

          
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
    self.posColors = list(SPECTRUM_COLOURS.keys())[self.colourIndex]
    self.negColors = list(SPECTRUM_COLOURS.keys())[self.colourIndex+1]
    spectrumItem = SpectrumNdItem(self, spectrum, dimMapping, self.region, self.posColors, self.negColors)
    newItem = self.scene().addItem(spectrumItem)
    self.mainWindow.pythonConsole.write("current.pane.addSpectrum(%s)\n" % (spectrum))
    spectrumItem.name = spectrum.name
    if self.colourIndex != len(SPECTRUM_COLOURS) - 2:
      self.colourIndex +=2
    else:
      self.colourIndex = 0

    if self.spectrumIndex < 10:
      shortcutKey = "s,"+str(self.spectrumIndex)
      self.spectrumIndex+=1
    else:
      shortcutKey = None

    print(newItem)
    newAction = self.spectrumToolbar.addAction(spectrumItem.name, QtGui.QToolButton)
    newAction.setCheckable(True)
    newAction.setChecked(True)
    newAction.setShortcut(QtGui.QKeySequence(shortcutKey))

    newAction.toggled.connect(spectrumItem.setVisible)
    self.spectrumToolbar.addAction(newAction)
    self.spectrumItems.append(spectrumItem)
    self.current.spectrum = spectrum

    # spectrumItem.posColors =
    spectrum.spectrumItem = spectrumItem

  def upBy2(self):
    self.current.spectrum.spectrumItem.baseLevel*=1.4
    self.current.spectrum.spectrumItem.levels = self.current.spectrum.spectrumItem.getLevels()

  def downBy2(self):
    self.current.spectrum.spectrumItem.baseLevel/=1.4
    self.current.spectrum.spectrumItem.levels = self.current.spectrum.spectrumItem.getLevels()

  def addOne(self):
    self.current.spectrum.spectrumItem.numberOfLevels +=1
    self.current.spectrum.spectrumItem.levels = self.current.spectrum.spectrumItem.getLevels()

  def subtractOne(self):
    self.current.spectrum.spectrumItem.numberOfLevels -=1
    self.current.spectrum.spectrumItem.levels = self.current.spectrum.spectrumItem.getLevels()

  def fillToolBar(self):
    self.spectrumUtilToolbar.addAction("+1", self.addOne)
    self.spectrumUtilToolbar.addAction("-1", self.subtractOne)
    self.spectrumUtilToolbar.addAction("*1.4", self.upBy2)
    self.spectrumUtilToolbar.addAction("/1.4", self.downBy2)
    self.spectrumUtilToolbar.addAction("Store Zoom", self.storeZoom)
    self.spectrumUtilToolbar.addAction("Restore Zoom", self.restoreZoom)

