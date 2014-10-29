"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (www.ccpn.ac.uk) 2014 - $Date: 2014-06-04 18:13:10 +0100 (Wed, 04 Jun 2014) $"
__credits__ = "Wayne Boucher, Rasmus H Fogh, Simon Skinner, Geerten Vuister"
__license__ = ("CCPN license. See www.ccpn.ac.uk/license"
              "or ccpncore.memops.Credits.CcpnLicense for license text")
__reference__ = ("For publications, please use reference from www.ccpn.ac.uk/license"
                " or ccpncore.memops.Credits.CcpNmrReference")

#=========================================================================================
# Last code modification:
#=========================================================================================
__author__ = "$Author: rhfogh $"
__date__ = "$Date: 2014-06-04 18:13:10 +0100 (Wed, 04 Jun 2014) $"
__version__ = "$Revision: 7686 $"

#=========================================================================================
# Start of code
#=========================================================================================
import operator

from PySide import QtCore, QtGui, QtOpenGL

from ccpnmrcore.modules.SpectrumPane import SpectrumPane, SPECTRUM_COLOURS
from ccpncore.gui.Action import Action
from ccpnmrcore.modules.spectrumPane.SpectrumNdItem import SpectrumNdItem
from ccpnmrcore.modules.spectrumPane.Spectrum1dItem import Spectrum1dItem
from ccpncore.gui.Menu import Menu
from ccpncore.gui.Icon import Icon
from ccpn.lib import Spectrum as LibSpectrum
import numpy
from functools import partial
import pyqtgraph as pg

class SpectrumNdPane(SpectrumPane):

  def __init__(self, *args, **kw):
    
    SpectrumPane.__init__(self, *args, **kw)

    self.plotItem.setAcceptDrops(True)
    
    self.setViewport(QtOpenGL.QGLWidget())
    self.setViewportUpdateMode(QtGui.QGraphicsView.FullViewportUpdate)
    self.crossHairShown = True
    self.viewBox.menu = self.get2dContextMenu()
    self.viewBox.invertX()
    self.viewBox.invertY()
    self.fillToolBar()
    self.showGrid(x=True, y=True)
    self.region = None
    self.colourIndex = 0
    self.spectrumUtilToolbar.setSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
    self.traceMarkers = []

          
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

  def get2dContextMenu(self):

    self.contextMenu = Menu(self, isFloatWidget=True)
    self.contextMenu.addItem("H Trace", callback=partial(self.addTraceMarker,'horizontal'))
    self.contextMenu.addItem("V Trace", callback=partial(self.addTraceMarker,'vertical'))
    self.removeTraces = self.contextMenu.addItem("Remove Traces", callback=self.clearTraceMarkers)
    self.crossHairAction = QtGui.QAction("Crosshair", self, triggered=self.toggleCrossHair,
                                         checkable=True)

    if self.crossHairShown == True:
      self.crossHairAction.setChecked(True)
    else:
      self.crossHairAction.setChecked(False)
    self.contextMenu.addAction(self.crossHairAction, isFloatWidget=True)
    return self.contextMenu



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
    spectrum.spectrumItem = spectrumItem
    if self.colourIndex != len(SPECTRUM_COLOURS) - 2:
      self.colourIndex +=2
    else:
      self.colourIndex = 0

    if self.spectrumIndex < 10:
      shortcutKey = "s,"+str(self.spectrumIndex)
      self.spectrumIndex+=1
    else:
      shortcutKey = None

    pix=QtGui.QPixmap(60,10)
    # pix2=QtGui.QPixmap(30,10)
    # pix.scaled(60,20)
    # pix.setSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Fixed)
    pix.fill(QtGui.QColor(self.posColors))
    spectrumItem.newAction = self.spectrumToolbar.addAction(spectrumItem.name, QtGui.QToolButton)
    newIcon = QtGui.QIcon(pix)
    # newIcon.actualSize(QtCore.QSize(80,60))
    spectrumItem.newAction.setIcon(newIcon)
    spectrumItem.newAction.setCheckable(True)
    spectrumItem.newAction.setChecked(True)
    spectrumItem.newAction.setShortcut(QtGui.QKeySequence(shortcutKey))

    spectrumItem.newAction.toggled.connect(spectrumItem.setVisible)
    self.spectrumToolbar.addAction(spectrumItem.newAction)
    spectrumItem.widget = self.spectrumToolbar.widgetForAction(spectrumItem.newAction)
    spectrumItem.widget.clicked.connect(partial(self.clickedNd, spectrum))
    spectrumItem.widget.setFixedSize(60,30)
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

  def addTraceMarker(self, orientation):
    if orientation == 'horizontal':
      traceMarker = pg.InfiniteLine(angle=0, movable=True, pos=self.mousePoint)
      self.addItem(traceMarker)
      dim = 0
    if orientation == 'vertical':
      traceMarker = pg.InfiniteLine(angle=90, movable=True, pos=self.mousePoint)
      self.addItem(traceMarker)
      dim=1
    self.traceMarkers.append(traceMarker)
    self.phasingModule = self.mainWindow.addSpectrum1dPane()
    self.plotTrace(dim, position=self.mousePoint.toTuple(), module=self.phasingModule)
    traceMarker.sigPositionChanged.connect(partial(self.markerMoved,self.phasingModule))


  def plotTrace(self, dim, position=None, module=None):
    positions = []
    if position is None:
      position = self.mousePoint.toTuple()
    else:
      position = position
    i = 0
    for pos in position:
      dataDimRef = self.current.spectrum.ccpnSpectrum.sortedDataDims()[i].findFirstDataDimRef()
      positions.append(dataDimRef.valueToPoint(int(position[i])))
      i+=1
    spectrum = self.current.spectrum
    dataDimRef = self.current.spectrum.ccpnSpectrum.sortedDataDims()[dim].findFirstDataDimRef()
    firstPoint = dataDimRef.pointToValue(0)
    pointCount = spectrum.ccpnSpectrum.sortedDataDims()[dim].numPoints
    lastPoint = dataDimRef.pointToValue(pointCount)
    pointSpacing = (lastPoint-firstPoint)/pointCount
    position = numpy.array([firstPoint + n*pointSpacing for n in range(pointCount)],numpy.float32)
    data = LibSpectrum.getSliceData(spectrum.ccpnSpectrum,position=positions, sliceDim=dim)
    spectrumData = numpy.array([position,data], numpy.float32)
    spectrumItem = Spectrum1dItem(self,spectrum, spectralData=spectrumData)
    spectrumItem.plot = module.plotItem.plot(spectrumData[0],spectrumData[1])


  def clearTraceMarkers(self):
    for item in self.traceMarkers:
      self.removeItem(item)

  def markerMoved(self, module, traceMarker):
    positions = [traceMarker.getXPos(),traceMarker.getYPos()]
    module.plotItem.clear()
    self.plotTrace(dim=0, position=positions, module=module)



  def fillToolBar(self):
    plusOneAction = self.spectrumUtilToolbar.addAction("+1", self.addOne)
    plusOneIcon = Icon('icons/contourAdd')
    plusOneAction.setIcon(plusOneIcon)
    plusOneAction.setToolTip('Add One Level')
    minusOneAction = self.spectrumUtilToolbar.addAction("+1", self.subtractOne)
    minusOneIcon = Icon('icons/contourRemove')
    minusOneAction.setIcon(minusOneIcon)
    minusOneAction.setToolTip('Remove One Level ')
    upBy2Action = self.spectrumUtilToolbar.addAction("*1.4", self.upBy2)
    upBy2Icon = Icon('icons/contourBaseUp')
    upBy2Action.setIcon(upBy2Icon)
    upBy2Action.setToolTip('Raise Contour Base Level')
    downBy2Action = self.spectrumUtilToolbar.addAction("*1.4", self.downBy2)
    downBy2Icon = Icon('icons/contourBaseDown')
    downBy2Action.setIcon(downBy2Icon)
    downBy2Action.setToolTip('Lower Contour Base Level')
    storeZoomAction = self.spectrumUtilToolbar.addAction("Store Zoom", self.storeZoom)
    storeZoomIcon = Icon('icons/zoom-store')
    storeZoomAction.setIcon(storeZoomIcon)
    storeZoomAction.setToolTip('Store Zoom')
    restoreZoomAction = self.spectrumUtilToolbar.addAction("Restore Zoom", self.restoreZoom)
    restoreZoomIcon = Icon('icons/zoom-restore')
    restoreZoomAction.setIcon(restoreZoomIcon)
    restoreZoomAction.setToolTip('Restore Zoom')


