"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (www.ccpn.ac.uk) 2014 - $Date: 2014-06-04 18:13:10 +0100 (Wed, 04 Jun 2014) $"
__credits__ = "Wayne Boucher, Rasmus H Fogh, Simon P Skinner, Geerten W Vuister"
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
__author__ = 'simon'

#from PyQt4 import QtGui, QtCore, QtOpenGL
from PyQt4 import QtGui, QtCore

import math
import numpy
import pyqtgraph as pg

from ccpn.lib.wrapper import Spectrum as LibSpectrum

from ccpncore.memops import Notifiers

from ccpncore.gui.Button import Button
from ccpncore.gui.DoubleSpinbox import DoubleSpinbox
from ccpncore.gui.Icon import Icon
from ccpncore.gui.Menu import Menu
from ccpncore.gui.Spinbox import Spinbox

from ccpnmrcore.gui.PlaneToolbar import PlaneToolbar
from ccpnmrcore.modules.GuiStrip import GuiStrip
###from ccpnmrcore.modules.spectrumItems.GuiPeakListView import PeakNd

class GuiStripNd(GuiStrip):

  def __init__(self):
    GuiStrip.__init__(self, useOpenGL=True)

    # the scene knows which items are in it but they are stored as a list and the below give fast access from API object to QGraphicsItem
    ###self.peakLayerDict = {}  # peakList --> peakLayer
    self.peakListViewDict = {}  # peakList --> peakListView

    ###self.plotWidget.plotItem.setAcceptDrops(True)
    ###self.viewportWidget = QtOpenGL.QGLWidget()
    ###self.plotWidget.setViewport(self.viewportWidget)
    ###self.guiSpectrumDisplay.viewportDict[self.viewportWidget] = self
    ###self.plotWidget.setViewportUpdateMode(QtGui.QGraphicsView.FullViewportUpdate)
    self.viewBox.menu = self.get2dContextMenu()
    self.viewBox.invertX()
    self.viewBox.invertY()
    self.traceMarkers = []
    self.traceScale = 1e6
    self.traces = []
    ###self.region = guiSpectrumDisplay.defaultRegion()
    self.planeLabel = None
    self.axesSwapped = False
    self.colourIndex = 0
    # print(guiSpectrumDisplay)
    # self.fillToolBar()
    # self.addSpinSystemLabel()
    self.addPlaneToolbar()
    ###self.setShortcuts()
    # for spectrumView in self.spectrumViews:
    # #   newSpectrumView = spectrumView
    #   #if spectrumView not in self.plotWidget.scene().items():
    #     # newItem = spectrumView
    #     #self.plotWidget.scene().addItem(spectrumView)
    #   if spectrumView is not None:
    #     # Check is necessary as spectrumView may be None during project loading
    #     spectrumView.addSpectrumItem(self)

    ###Notifiers.registerNotify(self.newPeak, 'ccp.nmr.Nmr.Peak', '__init__')

    
  # def setupAxes(self):
  #   GuiStrip.setupAxes(self)
  #   for func in ('setPosition', 'setWidth'):
  #     Notifiers.registerNotify(self.axisRegionChanged, 'ccpnmr.gui.Task.Axis', func)


  def mouseDragEvent(self, event):
    if event.button() == QtCore.Qt.RightButton:
        pass
    else:
        self.viewBox.mouseDragEvent(self, event)


  def get2dContextMenu(self):

    self.contextMenu = Menu('', self, isFloatWidget=True)
    # self.contextMenu.addAction(self.hTraceAction)
    # self.contextMenu.addAction(self.vTraceAction)
    self.crossHairAction = self.contextMenu.addItem("Crosshair", callback=self.toggleCrossHair, checkable=True)
    self.gridAction = self.contextMenu.addItem("Grid", callback=self.toggleGrid, checkable=True)
    plusOneAction = self.contextMenu.addAction("Add Contour Level", self.guiSpectrumDisplay.addOne)
    plusOneIcon = Icon('iconsNew/contour-add')
    plusOneAction.setIcon(plusOneIcon)
    plusOneAction.setToolTip('Add One Level')
    minusOneAction = self.contextMenu.addAction("Remove Contour Level", self.guiSpectrumDisplay.subtractOne)
    minusOneIcon = Icon('iconsNew/contour-remove')
    minusOneAction.setIcon(minusOneIcon)
    minusOneAction.setToolTip('Remove One Level ')
    upBy2Action = self.contextMenu.addAction("Raise Base Level", self.guiSpectrumDisplay.upBy2)
    upBy2Icon = Icon('iconsNew/contour-base-up')
    upBy2Action.setIcon(upBy2Icon)
    upBy2Action.setToolTip('Raise Contour Base Level')
    downBy2Action = self.contextMenu.addAction("Lower Base Level", self.guiSpectrumDisplay.downBy2)
    downBy2Icon = Icon('iconsNew/contour-base-down')
    downBy2Action.setIcon(downBy2Icon)
    downBy2Action.setToolTip('Lower Contour Base Level')
    storeZoomAction = self.contextMenu.addAction("Store Zoom", self.guiSpectrumDisplay.storeZoom)
    storeZoomIcon = Icon('iconsNew/zoom-store')
    storeZoomAction.setIcon(storeZoomIcon)
    storeZoomAction.setToolTip('Store Zoom')
    restoreZoomAction = self.contextMenu.addAction("Restore Zoom", self.guiSpectrumDisplay.restoreZoom)
    restoreZoomIcon = Icon('iconsNew/zoom-restore')
    restoreZoomAction.setIcon(restoreZoomIcon)
    restoreZoomAction.setToolTip('Restore Zoom')


    ###if self.crossHairShown == True:
    ###  self.crossHairAction.setChecked(True)
    ###else:
    ###  self.crossHairAction.setChecked(False)

    if self.grid.isVisible():
      self.gridAction.setChecked(True)
    else:
      self.gridAction.setChecked(False)
    # self.contextMenu.addAction(self.crossHairAction, isFloatWidget=True)
    return self.contextMenu


  def changeZPlane(self, planeCount=None, position=None):

    zAxis = self.orderedAxes[2]
    smallest = None
    minima = []
    maxima = []
    #take smallest inter-plane distance
    for spectrumItem in self.spectrumViews:
      index = spectrumItem.spectrum.axisCodes.index(zAxis.code)
      minima.append(spectrumItem.spectrum.spectrumLimits[index][0])
      maxima.append(spectrumItem.spectrum.spectrumLimits[index][1])
      zPlaneSize = spectrumItem.zPlaneSize()
      if zPlaneSize is not None:
        if smallest is None or zPlaneSize < smallest:
          smallest = zPlaneSize
    if smallest is None:
      smallest = 1.0 # arbitrary

    if planeCount:
      delta = smallest * planeCount
      zAxis.position = zAxis.position+delta
    elif position:
      if min(minima) < position <= max(maxima):
        zAxis.position = position
        self.planeToolbar.planeLabel.setValue(zAxis.position)
      else:
        print('position is outside spectrum bounds')


  def changePlaneThickness(self, value):
    zAxis = self.orderedAxes[2]
    zAxis.width*=value

  def nextZPlane(self):

    self.changeZPlane(planeCount=-1) # -1 because ppm units are backwards

  def prevZPlane(self):

    self.changeZPlane(planeCount=1) # -1 because ppm units are backwards

  def addPlaneToolbar(self):


    callbacks = [self.prevZPlane, self.nextZPlane, self.setZPlanePosition, self.changePlaneThickness]

    self.planeToolbar = PlaneToolbar(self, grid=(1, self.guiSpectrumDisplay.orderedStrips.index(self)),
                                     hAlign='center', vAlign='c', callbacks=callbacks)

  def setZPlanePosition(self, value):
    if self.planeToolbar.planeLabel.minimum() <= self.planeToolbar.planeLabel.value() <= self.planeToolbar.planeLabel.maximum():
      self.changeZPlane(position=value)

  def setPlaneThickness(self, value):

    self.changePlaneThickness((value/self.planeThicknessValue))
    self.planeThicknessValue = value

  def _findPeakListView(self, peakList):
    
    peakListView = self.peakListViewDict.get(peakList)
    if peakListView:
      return peakListView
      
    for spectrumView in self.spectrumViews:
      for peakListView in spectrumView.peakListViews:
        if peakList is peakListView.peakList:
          self.peakListViewDict[peakList] = peakListView
          return peakListView
            
    return None
    
  def showPeaks(self, peakList, peaks=None):
    ###from ccpnmrcore.modules.spectrumItems.GuiPeakListView import GuiPeakListView
    # NBNB TBD 1) we should not always display all peak lists together
    # NBNB TBD 2) This should not be called for each strip
    
    if not peaks:
      peaks = peakList.peaks
         
    peakListView = self._findPeakListView(peakList)
    if not peakListView:
      return
  
      # for spectrumView in self.spectrumViews:
      #   spectrumView._connectPeakLayerVisibility(peakLayer)
        ###spectrumView.visibilityAction.toggled.connect(peakLayer.setVisible)
      
    #rectItem = QtGui.QGraphicsRectItem(5, 120, 2, 10, peakLayer, self.plotWidget.scene())
    ##color = QtGui.QColor('red')
    #rectItem.setBrush(QtGui.QBrush(color))
    #rectItem.setFlag(QtGui.QGraphicsItem.ItemIsMovable)
    #rectItem.setFlag(QtGui.QGraphicsItem.ItemIsSelectable)
    ##lineItem = QtGui.QGraphicsLineItem(5, 120, 7, 130, peakLayer, self.plotWidget.scene())
    ##pen = QtGui.QPen()
    ##pen.setWidth(0.1)
    ##pen.setBrush(color)
    ##lineItem.setPen(pen)
    ##lineItem.setFlag(QtGui.QGraphicsItem.ItemIsSelectable)
    
    peaks = [peak for peak in peaks if self.peakIsInPlane(peak)]
    self.stripFrame.guiSpectrumDisplay.showPeaks(peakListView, peaks)

    ###for peak in peaks:
    ###  if peak not in self.peakItemDict:
    ###    peakItem = PeakNd(self, peak, peakLayer)
    ###    self.peakItemDict[peak] = peakItem
        
     # peakItem = PeakNd(self, peak)
    ###self.plotWidget.addItem(peakLayer)
     # self.plotWidget.addItem((peakItem.annotation))
     
  def peakIsInPlane(self, peak):

    if len(self.orderedAxes) > 2:
      zDim = self.spectrumViews[0].dimensionOrdering[2] - 1
      zPlaneSize = self.spectrumViews[0].zPlaneSize()
      zPosition = peak.position[zDim]

      zRegion = self.orderedAxes[2].region
      if zRegion[0]-zPlaneSize <= zPosition <= zRegion[1]+zPlaneSize:
        return True
      else:
        return False
    else:
      return True
    
  """
  def newPeak(self, apiPeak):
    peak = self._appBase.project._data2Obj[apiPeak]
    if None in peak.position:
      return
    peakList = peak.parent
    self.showPeaks(peakList)
"""
      
  # def axisRegionChanged(self, apiAxis):
  #
  #   # TBD: other axes
  #   apiStripAxis = self._wrappedData.findFirstStripAxis(axis=apiAxis)
  #   if apiStripAxis is None:
  #     return
  #   axis = self._appBase.project._data2Obj[apiStripAxis]
  #   if len(self.orderedAxes) >= 3 and axis in self.orderedAxes[2:]:
  #     peakLists = self.peakLayerDict.keys()
  #     for peakList in peakLists:
  #       peakLayer = self.peakLayerDict[peakList]
  #       peaks = [peak for peak in peakList.peaks if self.peakIsInPlane(peak)]
  #       self.stripFrame.guiSpectrumDisplay.showPeaks(peakLayer, peaks)

  def addHTraceMarker(self):
    traceMarker = pg.InfiniteLine(angle=0, movable=True, pos=self.mousePoint)
    self._appBase.current.traceMarker = traceMarker
    self.plotWidget.addItem(traceMarker)
    traceMarker.axis = self.orderedAxes[0]
    traceMarker.positionAxis = self.orderedAxes[1]
    self.traceMarkers.append(traceMarker)
    trace = self.plotTrace(position=self.mousePoint, traceMarker=traceMarker)
    self.traces.append(trace)
    traceMarker.sigPositionChanged.connect(self.markerMoved)
    proxy = pg.SignalProxy(traceMarker.sigPositionChanged, slot=(self.markerMoved))

  def addVTraceMarker(self):
    traceMarker = pg.InfiniteLine(angle=90, movable=True, pos=self.mousePoint)
    self._appBase.current.traceMarker = traceMarker
    self.addItem(traceMarker)
    traceMarker.axis = self.yAxis
    traceMarker.positionAxis = self.xAxis
    self.traceMarkers.append(traceMarker)
    trace = self.plotTrace(position=self.mousePoint.toTuple(), traceMarker=traceMarker)
    self.traces.append(trace)
    traceMarker.sigPositionChanged.connect(self.markerMoved)
    proxy = pg.SignalProxy(traceMarker.sigPositionChanged, slot=(self.markerMoved))

  def plotTrace(self, position=None, traceMarker=None, phasedData=None):

    positions = []
    if position is None:
      position = [self.mousePoint.x(),self.mousePoint.y()]

    else:
      position = [position.x(), position.y()]
      if self.axesSwapped == True:
        position.reverse()
    if len(self.orderedAxes) > 2:
      zDims = set(range(self._appBase.current.spectrum.dimensionCount)) - {self.orderedAxes[0].mappedDim, self.orderedAxes[1].mappedDim}
      zDims = set(range(len(self.orderedAxes))) - {self.orderedAxes[0].mappedDim, self.orderedAxes[1].mappedDim}
      zDim = zDims.pop()
      position.append(int(self.region[zDim][0]))


    dimensionCount = len(self.orderedAxes)
    ppmRegion = dimensionCount * [None]
    pointCounts = self.spectrumViews[0].spectrum.pointCounts
    for dim in range(dimensionCount):
      # if dim in (self._appBase.current.spectrum.spectrumItem.xDim, self._appBase.current.spectrum.spectrumItem.yDim):
      region = self.plotWidget.viewRange()[dim]
      # else:
      #   n = position[dim]
      #   region = n
      ppmRegion[dim] = region
    pntRegion = []
    for dim in range(dimensionCount):
        pnt = LibSpectrum.getDimPointFromValue(self.spectrumViews[0].spectrum, dim, ppmRegion[dim])
        pntRegion.append(math.floor(pnt[0]))
    spectrum = self.spectrumViews[0].spectrum
    dataDimRef = spectrum.apiDataSource.sortedDataDims()[traceMarker.axis.mappedDim].findFirstDataDimRef()
    data = LibSpectrum.getSliceData(spectrum.apiDataSource,position=pntRegion, sliceDim=traceMarker.axis.mappedDim)
    firstPoint = dataDimRef.pointToValue(0)
    pointCount = len(data)
    lastPoint = dataDimRef.pointToValue(pointCount)
    pointSpacing = (lastPoint-firstPoint)/pointCount
    positions2 = numpy.array([firstPoint + n*pointSpacing for n in range(pointCount)],dtype=numpy.float32)
    # positions2 = positions2[::-1]
    if phasedData is not None:
      data2 = (numpy.array(phasedData)/self.traceScale)*-1
    else:
      data2 = (data/self.traceScale)*-1
    if traceMarker.angle == 0:
      data3 = numpy.array([x+ppmRegion[traceMarker.positionAxis.mappedDim] for x in data2])
      traceMarker.spectrumItemTrace = pg.PlotDataItem(positions2, data3)
    else:
      # positions2 = positions2[::-1]
      data3 = numpy.array([x+ppmRegion[traceMarker.positionAxis.mappedDim] for x in data2])
      traceMarker.spectrumItemTrace = pg.PlotDataItem(data3,positions2)
    traceMarker.spectrumItemTrace.dim = traceMarker.axis.mappedDim
    traceMarker.data = data
    traceMarker.spectrumItemTrace.position = position
    self.addItem(traceMarker.spectrumItemTrace)


    return traceMarker

         