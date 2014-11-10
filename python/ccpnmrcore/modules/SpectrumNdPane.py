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
from ccpncore.gui.Label import Label
from ccpn.lib import Spectrum as LibSpectrum
import numpy
import math
from functools import partial
import pyqtgraph as pg
from scipy import signal

class SpectrumNdPane(SpectrumPane):

  def __init__(self, *args, **kw):
    
    SpectrumPane.__init__(self, *args, **kw)

    self.plotItem.setAcceptDrops(True)
    
    self.setViewport(QtOpenGL.QGLWidget())
    self.setViewportUpdateMode(QtGui.QGraphicsView.FullViewportUpdate)
    self.crossHairShown = True
    self.fillToolBar()
    self.viewBox.menu = self.get2dContextMenu()
    self.viewBox.invertX()
    self.viewBox.invertY()
    self.showGrid(x=True, y=True)
    self.region = None
    self.colourIndex = 0
    self.spectrumUtilToolbar.setSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
    self.traceMarkers = []
    self.traceScale = 1e6
    self.traces = []
    self.phaseButtonShown = False

          
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
    elif event.modifiers() & QtCore.Qt.ControlModifier:
      if event.delta() > 0:
         self.increaseTraceScale()
      else:
        self.decreaseTraceScale()
    else:
      event.ignore

  def get2dContextMenu(self):

    self.contextMenu = Menu(self, isFloatWidget=True)
    self.contextMenu.addAction(self.hTraceAction)
    self.contextMenu.addAction(self.vTraceAction)
    self.removeTraces = self.contextMenu.addItem(text="Remove Traces", callback=self.clearTraceMarkers, shortcut="RT")
    self.crossHairAction = QtGui.QAction("Crosshair", self, triggered=self.toggleCrossHair,
                                         checkable=True)

    if self.crossHairShown == True:
      self.crossHairAction.setChecked(True)
    else:
      self.crossHairAction.setChecked(False)
    self.contextMenu.addAction(self.crossHairAction, isFloatWidget=True)
    self.contextMenu.addItem("Increase Trace Level", callback=self.increaseTraceScale)
    self.contextMenu.addItem("Decrease Trace Level", callback=self.decreaseTraceScale)

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
    spectrum.spectrumItem = spectrumItem

  def decreaseTraceScale(self):
    self.traceScale*=1.41
    for trace in self.traces:
      self.removeItem(trace.spectrumItemTrace)
      self.plotTrace(trace.spectrumItemTrace.dim,trace.spectrumItemTrace.position, traceMarker=trace)


  def increaseTraceScale(self):
    self.traceScale/=1.41
    for trace in self.traces:
      self.removeItem(trace.spectrumItemTrace)
      self.plotTrace(trace.spectrumItemTrace.dim,trace.spectrumItemTrace.position, traceMarker=trace)

  #
  # def updateTrace(self, xData, yData):
  #   for trace in self.traces:
  #     self.removeItem(trace)
  #     trace.newSpectrumItemTrace = pg.PlotDataItem(xData,yData)
  #     self.addItem(trace.SpectrumItemTrace)

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

  def addHTraceMarker(self):
    traceMarker = pg.InfiniteLine(angle=0, movable=True, pos=self.mousePoint)
    self.addItem(traceMarker)
    dim = 1
    self.traceMarkers.append(traceMarker)
    trace = self.plotTrace(dim, position=self.mousePoint.toTuple(), traceMarker=traceMarker)
    self.traces.append(trace)
    traceMarker.sigPositionChanged.connect(self.markerMoved)
    proxy = pg.SignalProxy(traceMarker.sigPositionChanged, slot=(self.markerMoved))
    if self.phaseButtonShown == False:
      print('showingbutton')
      self.phasingAction = QtGui.QAction("phasing", self, checkable=True)
      self.phasingAction.toggled.connect(self.togglePhasingBar)
      self.spectrumUtilToolbar.addAction(self.phasingAction)
      self.phaseButtonShown = True

  def addVTraceMarker(self):
    traceMarker = pg.InfiniteLine(angle=90, movable=True, pos=self.mousePoint)
    self.addItem(traceMarker)
    dim = 0
    self.traceMarkers.append(traceMarker)
    trace = self.plotTrace(dim, position=self.mousePoint.toTuple(), traceMarker=traceMarker)
    self.traces.append(trace)
    traceMarker.sigPositionChanged.connect(self.markerMoved)
    proxy = pg.SignalProxy(traceMarker.sigPositionChanged, slot=(self.markerMoved))
    if self.phaseButtonShown == False:
      self.phasingAction = QtGui.QAction("phasing", self, checkable=True)
      self.phasingAction.toggled.connect(self.togglePhasingBar)
      self.spectrumUtilToolbar.addAction(self.phasingAction)
      self.phaseButtonShown = True


  def markerMoved(self, traceMarker):
    self.removeItem(traceMarker.spectrumItemTrace)
    if traceMarker.angle== 0:
      dim = 1
      positions = [traceMarker.getXPos(),traceMarker.getYPos()]
    elif traceMarker.angle== 90:
      positions = [traceMarker.getXPos(),traceMarker.getYPos()]
      dim = 0
    self.plotTrace(dim=dim, position=positions, traceMarker=traceMarker)

  def phasingZeroOrder(self, value):
    for trace in self.traces:

      transformedData = signal.hilbert(trace.data)
      # print(transformedData)
      p0 = math.radians(value)
      # print('deg',value,'rad',p0)
      phasedData = (transformedData.real * math.cos(p0)) - (transformedData.imag * math.sin(p0))
      # print('npcos',numpy.cos(p0))
      # print(phasedData)
      # phasedData2 = numpy.real(phasedData)
      # print(phasedData2[0:9])
      self.removeItem(trace.spectrumItemTrace)
      self.plotTrace(trace.spectrumItemTrace.dim,trace.spectrumItemTrace.position, traceMarker=trace, data=phasedData)
    #   p0 = p0 * pi / 180.  # convert to radians
    #   p1 = p1 * pi / 180.
    #   size = data.shape[-1]
    #   apod = np.exp(1.0j * (p0 + (p1 * np.arange(size) / size))
    #               ).astype(data.dtype)
    # if inv:
    #     apod = 1 / apod
    # return apod * data

  def phasingFirstOrder(self):
    pass

  def plotTrace(self, dim, position=None, traceMarker=None, data=None):

    positions = []
    if position is None:
      position = self.mousePoint.toTuple()
    else:
      position = position
    for i in range(len(position)):
      positions.append(math.floor(LibSpectrum.getDimPointFromValue(self.current.spectrum, i, position[i])))

    spectrum = self.current.spectrum

    if dim == 0:
      if data is None:
        data = LibSpectrum.getSliceData(spectrum.ccpnSpectrum,position=positions, sliceDim=1)
      dataDimRef = self.current.spectrum.ccpnSpectrum.sortedDataDims()[1].findFirstDataDimRef()
      firstPoint = dataDimRef.pointToValue(0)
      pointCount = len(data)
      lastPoint = dataDimRef.pointToValue(pointCount)
      pointSpacing = (lastPoint-firstPoint)/pointCount
      positions2 = numpy.array([firstPoint + n*pointSpacing for n in range(pointCount)],dtype=numpy.float32)
      spectrumData = numpy.array([positions2,data], dtype=numpy.float32)
      data2 = (data/self.traceScale)
      data3 = numpy.array([x+position[0] for x in data2])
      traceMarker.spectrumItemTrace = pg.PlotDataItem(data3,positions2)
      traceMarker.spectrumItemTrace.dim = dim
      traceMarker.data = data
      traceMarker.spectrumItemTrace.position = position
      self.addItem(traceMarker.spectrumItemTrace)

    if dim == 1:
      dataDimRef = self.current.spectrum.ccpnSpectrum.sortedDataDims()[0].findFirstDataDimRef()
      if data is None:
        data = LibSpectrum.getSliceData(spectrum.ccpnSpectrum,position=positions, sliceDim=0)
      # print(data)
      firstPoint = dataDimRef.pointToValue(0)
      pointCount = len(data)
      lastPoint = dataDimRef.pointToValue(pointCount)
      pointSpacing = (lastPoint-firstPoint)/pointCount
      positions2 = numpy.array([firstPoint + n*pointSpacing for n in range(pointCount)],dtype=numpy.float32)
      # spectrumData = numpy.array([positions2,data], dtype=numpy.float32)
      data2 = (data/self.traceScale)*-1
      data3 = numpy.array([x+position[1] for x in data2])
      traceMarker.spectrumItemTrace = pg.PlotDataItem(positions2,data3)
      traceMarker.spectrumItemTrace.dim = dim
      traceMarker.data = data
      traceMarker.spectrumItemTrace.position = position
      self.addItem(traceMarker.spectrumItemTrace)

    return traceMarker

  def changeValue(self, label, value):

    floatValue = float(value)
    label.setText(str(floatValue))

  def changeSliderValue(self, slider, value):

    floatValue = float(value)
    slider.setValue(floatValue)

  def clearTraceMarkers(self):
    for item in self.traceMarkers:
      self.removeItem(item)
      self.removeItem(item.spectrumItemTrace)
    for item in self.traces:
      self.removeItem(item)
      self.removeItem(item)
    self.spectrumUtilToolbar.removeAction(self.phasingAction)
    self.phaseButtonShown = False
    self.traces = []

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
    self.hTraceAction = QtGui.QAction("H T", self, shortcut=QtGui.QKeySequence("H, T"), triggered=partial(self.addHTraceMarker))
    self.vTraceAction = QtGui.QAction("V T", self, shortcut=QtGui.QKeySequence("V, T"), triggered=partial(self.addVTraceMarker))
    self.spectrumUtilToolbar.addAction(self.hTraceAction)
    self.spectrumUtilToolbar.addAction(self.vTraceAction)



  def togglePhasingBar(self):
    if self.phasingAction.isChecked() == True:
      self.raisePhasingToolBar()
    if self.phasingAction.isChecked() == False:
      self.phasingToolBar.hide()

  def raisePhasingToolBar(self):
    self.phasingToolBar = QtGui.QToolBar()
    zeroPhaseSlider  = QtGui.QSlider(self)
    zeroPhaseSlider.setOrientation(QtCore.Qt.Horizontal)
    zeroPhaseSlider.setRange(-180.0, 180.0)
    zeroPhaseSlider.setValue(0)
    zeroPhaseSlider.setFixedWidth(350)
    zeroPhaseSlider.setTickInterval(0.1)
    zeroPhaseLabel = QtGui.QLineEdit(self)
    zeroPhaseLabel.setFixedWidth(50)
    zeroLabel = Label(self,text="P0")
    zeroLabel.setFixedWidth(30)
    self.phasingToolBar.addWidget(zeroLabel)
    self.phasingToolBar.addWidget(zeroPhaseSlider)
    zeroPhaseLabel.setText(str(zeroPhaseSlider.value()))
    zeroPhaseSlider.valueChanged.connect(partial(self.changeValue,zeroPhaseLabel))
    zeroPhaseLabel.textChanged.connect(partial(self.changeSliderValue,zeroPhaseSlider))
    zeroPhaseSlider.valueChanged.connect(self.phasingZeroOrder)
    self.phasingToolBar.addWidget(zeroPhaseLabel)
    firstPhaseSlider  = QtGui.QSlider(self)
    firstPhaseSlider.setFixedWidth(350)
    firstPhaseSlider.setOrientation(QtCore.Qt.Horizontal)
    firstPhaseSlider.setRange(-360.0, 360.0)
    firstPhaseSlider.setValue(0)
    firstPhaseSlider.setTickInterval(0.1)
    firstLabel = Label(self,text="P1")
    firstLabel.setFixedWidth(30)
    firstPhaseLabel = QtGui.QLineEdit(self)
    firstPhaseLabel.setFixedWidth(50)
    firstPhaseLabel.setText(str(firstPhaseSlider.value()))
    firstPhaseSlider.valueChanged.connect(partial(self.changeValue,firstPhaseLabel))
    firstPhaseLabel.textChanged.connect(partial(self.changeSliderValue,firstPhaseSlider))
    self.phasingToolBar.addWidget(firstLabel)
    self.phasingToolBar.addWidget(firstPhaseSlider)
    self.phasingToolBar.addWidget(firstPhaseLabel)
    self.dock.addWidget(self.phasingToolBar, 3, 0, 1, 11)

