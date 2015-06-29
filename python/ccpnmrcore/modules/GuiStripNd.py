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
from ccpncore.gui.Font import Font
from ccpncore.gui.Icon import Icon
from ccpncore.gui.Label import Label
from ccpncore.gui.LineEdit import LineEdit
from ccpncore.gui.Menu import Menu
from ccpncore.gui.ToolBar import ToolBar
from ccpncore.util import Colour

from ccpnmrcore.modules.GuiStrip import GuiStrip
###from ccpnmrcore.modules.spectrumItems.GuiPeakListView import PeakNd

class GuiStripNd(GuiStrip):

  def __init__(self):
    GuiStrip.__init__(self, useOpenGL=True)

    # the scene knows which items are in it but they are stored as a list and the below give fast access from API object to QGraphicsItem
    self.peakLayerDict = {}  # peakList --> peakLayer

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
    self.addSpinSystemLabel()
    self.addPlaneToolbar()
    ###self.setShortcuts()
    for spectrumView in self.spectrumViews:
    #   newSpectrumView = spectrumView
      #if spectrumView not in self.plotWidget.scene().items():
        # newItem = spectrumView
        #self.plotWidget.scene().addItem(spectrumView)
      if spectrumView is not None:
        # Check is necessary as spectrumView may be None during project loading
        spectrumView.addSpectrumItem(self)

    ###Notifiers.registerNotify(self.newPeak, 'ccp.nmr.Nmr.Peak', '__init__')

    
  def setupAxes(self):
    GuiStrip.setupAxes(self)
    for func in ('setPosition', 'setWidth'):
      Notifiers.registerNotify(self.axisRegionChanged, 'ccpnmr.gui.Task.Axis', func)


  def mouseDragEvent(self, event):
    if event.button() == QtCore.Qt.RightButton:
        print(event)
    else:
        self.viewBox.mouseDragEvent(self, event)


  def get2dContextMenu(self):

    self.contextMenu = Menu('', self, isFloatWidget=True)
    # self.contextMenu.addAction(self.hTraceAction)
    # self.contextMenu.addAction(self.vTraceAction)
    self.crossHairAction = self.contextMenu.addItem("Crosshair", callback=self.toggleCrossHair, checkable=True)
    self.gridAction = self.contextMenu.addItem("Grid", callback=self.toggleGrid, checkable=True)

    if self.crossHairShown == True:
      self.crossHairAction.setChecked(True)
    else:
      self.crossHairAction.setChecked(False)

    if self.grid.isVisible():
      self.gridAction.setChecked(True)
    else:
      self.gridAction.setChecked(False)
    # self.contextMenu.addAction(self.crossHairAction, isFloatWidget=True)
    return self.contextMenu


  def changeZPlane(self, planeCount=None, position=None):

    zAxis = self.orderedAxes[2]
    print(zAxis)
    smallest = None
    #take smallest inter-plane distance
    for spectrumItem in self.spectrumViews:
      zPlaneSize = spectrumItem.zPlaneSize()
      if zPlaneSize is not None:
        if smallest is None or zPlaneSize < smallest:
          smallest = zPlaneSize
    if smallest is None:
      smallest = 1.0 # arbitrary
    #
    if planeCount:
      delta = smallest * planeCount
      zAxis.position = zAxis.position+delta
    elif position:
      zAxis.position = position
    self.planeLabel.setText('%.3f' % zAxis.position)

  def nextZPlane(self):

    self.changeZPlane(planeCount=-1) # -1 because ppm units are backwards

  def prevZPlane(self):

    self.changeZPlane(planeCount=1) # -1 because ppm units are backwards

  # def fillToolBar(self):
  #   spectrumUtilToolBar =  self.guiSpectrumDisplay.spectrumUtilToolBar
  #   plusOneAction = spectrumUtilToolBar.addAction("+1", self.addOne)
  #   plusOneIcon = Icon('icons/contourAdd')
  #   plusOneAction.setIcon(plusOneIcon)
  #   plusOneAction.setToolTip('Add One Level')
  #   minusOneAction = spectrumUtilToolBar.addAction("+1", self.subtractOne)
  #   minusOneIcon = Icon('icons/contourRemove')
  #   minusOneAction.setIcon(minusOneIcon)
  #   minusOneAction.setToolTip('Remove One Level ')
  #   upBy2Action = spectrumUtilToolBar.addAction("*1.4", self.upBy2)
  #   upBy2Icon = Icon('icons/contourBaseUp')
  #   upBy2Action.setIcon(upBy2Icon)
  #   upBy2Action.setToolTip('Raise Contour Base Level')
  #   downBy2Action = spectrumUtilToolBar.addAction("*1.4", self.downBy2)
  #   downBy2Icon = Icon('icons/contourBaseDown')
  #   downBy2Action.setIcon(downBy2Icon)
  #   downBy2Action.setToolTip('Lower Contour Base Level')
  #   storeZoomAction = spectrumUtilToolBar.addAction("Store Zoom", self.storeZoom)
  #   storeZoomIcon = Icon('icons/zoom-store')
  #   storeZoomAction.setIcon(storeZoomIcon)
  #   storeZoomAction.setToolTip('Store Zoom')
  #   restoreZoomAction = spectrumUtilToolBar.addAction("Restore Zoom", self.restoreZoom)
  #   restoreZoomIcon = Icon('icons/zoom-restore')
  #   restoreZoomAction.setIcon(restoreZoomIcon)
  #   restoreZoomAction.setToolTip('Restore Zoom')
  #
  # def upBy2(self):
  #   for spectrumItem in self.spectrumItems:
  #     spectrumItem.baseLevel*=1.4
  #     spectrumItem.levels = spectrumItem.getLevels()
  #
  # def downBy2(self):
  #   for spectrumItem in self.spectrumItems:
  #     spectrumItem.baseLevel/=1.4
  #     spectrumItem.levels = spectrumItem.getLevels()
  #
  # def addOne(self):
  #   self._appBase.current.spectrum.spectrumItem.numberOfLevels +=1
  #   self._appBase.current.spectrum.spectrumItem.levels = self._appBase.current.spectrum.spectrumItem.getLevels()
  #
  #
  # def subtractOne(self):
  #   self._appBase.current.spectrum.spectrumItem.numberOfLevels -=1
  #   self._appBase.current.spectrum.spectrumItem.levels = self._appBase.current.spectrum.spectrumItem.getLevels()

  def addPlaneToolbar(self):

    # if self._parent.spectrumViews[0]
    if len(self.orderedAxes) > 2:
      for i in range(len(self.orderedAxes)-2):
        self.planeToolbar = ToolBar(self.stripFrame, grid=(1+i, self.guiSpectrumDisplay.orderedStrips.index(self)), hAlign='center')
        self.planeToolbar.setMinimumWidth(200)
        # self.spinSystemLabel = Label(self)
        # self.spinSystemLabel.setMaximumWidth(1150)
        # self.spinSystemLabel.setScaledContents(True)
        prevPlaneButton = Button(self,'<', callback=self.prevZPlane)
        prevPlaneButton.setFixedWidth(19)
        prevPlaneButton.setFixedHeight(19)
        prevPlaneButton.setStyleSheet("""
        QPushButton {background-color: #535a83;
                    border: 1px solid;
                    border-color: #182548;
                    color: #bec4f3;}
        QPushButton::clicked {
        color: #122043;
        background-color: #e4e15b;

        """)
        prevPlaneButton.setFont(Font(size=14, bold=True))
        self.planeLabel = LineEdit(self)
        self.planeLabel.setFixedHeight(19)
        self.planeLabel.setText('%.3f' % self.positions[2])
        self.planeLabel.setStyleSheet("""QLineEdit {
        background-color: #f7ffff;
        color: #122043;
        margin: 0px 4px 4px 4px;
        border: 1px solid #182548;
        }
        QLineEdit::selected {
        background-color: #e4e15b;
        color: #e4e15b;
        """ )
        self.planeLabel.setAlignment(QtCore.Qt.AlignCenter)
        self.planeLabel.setFont(Font(normal=True))
        # self.axisCodeLabel = Label(self, text=spectrum.axisCodes[spectrumItem.dimMapping[2]])
        # self.planeLabel.textChanged.connect(self.changeZPlane)
        nextPlaneButton = Button(self,'>', callback=self.nextZPlane)
        nextPlaneButton.setFixedWidth(19)
        nextPlaneButton.setFixedHeight(19)
        nextPlaneButton.setStyleSheet("""
        QPushButton {background-color: #535a83;
                    border: 1px solid;
                    border-color: #182548;
                    color: #bec4f3;
                    }
        QPushButton::clicked {
        color: #122043;
        background-color: #e4e15b;

        """)
        nextPlaneButton.setFont(Font(size=14, bold=True))
        self.planeToolbar.setContentsMargins(0,0,0,0)
        self.planeToolbar.addWidget(prevPlaneButton)
        self.planeToolbar.addWidget(self.planeLabel)
        self.planeToolbar.addWidget(nextPlaneButton)

  def showPeaks(self, peakList, peaks=None):
    from ccpnmrcore.modules.spectrumItems.GuiPeakListView import GuiPeakListView
    
    if not peaks:
      peaks = peakList.peaks
      
    peakLayer = self.peakLayerDict.get(peakList)
    if not peakLayer:
      peakLayer = GuiPeakListView(self.plotWidget.scene(), self, peakList)
      self.viewBox.addItem(peakLayer)
      self.peakLayerDict[peakList] = peakLayer
      for spectrumView in self.spectrumViews:
        spectrumView.visibilityAction.toggled.connect(peakLayer.setVisible)
      
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
    self.stripFrame.guiSpectrumDisplay.showPeaks(peakLayer, peaks)
    
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
    
  def newPeak(self, apiPeak):
    peak = self._appBase.project._data2Obj[apiPeak]
    if None in peak.position:
      return
    peakList = peak.parent
    self.showPeaks(peakList)
  
  def axisRegionChanged(self, apiAxis):
    
    # TBD: other axes
    print(apiAxis)
    apiStripAxis = self._wrappedData.findFirstStripAxis(axis=apiAxis)
    if apiStripAxis is None:
      return
    axis = self._appBase.project._data2Obj[apiStripAxis]
    if len(self.orderedAxes) >= 3 and axis in self.orderedAxes[2:]:
      peakLists = self.peakLayerDict.keys()
      for peakList in peakLists:
        peakLayer = self.peakLayerDict[peakList]
        peaks = [peak for peak in peakList.peaks if self.peakIsInPlane(peak)]
        self.stripFrame.guiSpectrumDisplay.showPeaks(peakLayer, peaks)

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
        print(pnt)
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

         