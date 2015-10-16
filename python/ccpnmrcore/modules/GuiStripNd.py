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
from functools import partial
import pyqtgraph as pg

from ccpn import Project

from ccpn.lib._wrapper import Spectrum as LibSpectrum

from ccpncore.api.ccpnmr.gui.Task import Axis as ApiAxis
from ccpncore.api.ccpnmr.gui.Task import StripSpectrumView as ApiStripSpectrumView

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
    
    self.haveSetupZWidgets = False
    
    ###self.plotWidget.plotItem.setAcceptDrops(True)
    ###self.viewportWidget = QtOpenGL.QGLWidget()
    ###self.plotWidget.setViewport(self.viewportWidget)
    ###self.guiSpectrumDisplay.viewportDict[self.viewportWidget] = self
    ###self.plotWidget.setViewportUpdateMode(QtGui.QGraphicsView.FullViewportUpdate)
    self.viewBox.menu = self.get2dContextMenu()
    self.viewBox.invertX()
    self.viewBox.invertY()
    ###self.region = guiSpectrumDisplay.defaultRegion()
    self.planeLabel = None
    self.axesSwapped = False
    self.colourIndex = 0
    # print(guiSpectrumDisplay)
    # self.fillToolBar()
    # self.addSpinSystemLabel()
    self.addPlaneToolbar()

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
    self.hTraceAction = self.contextMenu.addItem("H Trace", checked=False, checkable=True)
    self.vTraceAction = self.contextMenu.addItem("V Trace", checked=False, checkable=True)
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
    resetZoomAction = self.contextMenu.addAction("Reset Zoom", self.resetZoom)
    resetZoomIcon = Icon('iconsNew/zoom-full')
    resetZoomAction.setIcon(resetZoomIcon)
    resetZoomAction.setToolTip('Reset Zoom')



    ###if self.crossHairShown == True:
    ###  self.crossHairAction.setChecked(True)
    ###else:
    ###  self.crossHairAction.setChecked(False)
    self.crossHairAction.setChecked(self.vLine.isVisible())

    if self.grid.isVisible():
      self.gridAction.setChecked(True)
    else:
      self.gridAction.setChecked(False)
    # self.contextMenu.addAction(self.crossHairAction, isFloatWidget=True)
    return self.contextMenu

  def resetZoom(self):
    x = []
    y = []
    for spectrumView in self.spectrumViews:
      xIndex = spectrumView.spectrum.axisCodes.index(self.axisCodes[0])
      yIndex = spectrumView.spectrum.axisCodes.index(self.axisCodes[1])
      x.append(spectrumView.spectrum.spectrumLimits[xIndex])
      y.append(spectrumView.spectrum.spectrumLimits[yIndex])

    xArray = numpy.array(x).flatten()
    yArray = numpy.array(y).flatten()

    self.zoomToRegion([min(xArray), max(xArray), min(yArray), max(yArray)])


  def updateRegion(self, viewBox):
    # this is called when the viewBox is changed on the screen via the mouse
    
    GuiStrip.updateRegion(self, viewBox)
    self.updateTraces()
    
  def updateTraces(self):
    
    updateHTrace = self.hTraceAction.isChecked()
    updateVTrace = self.vTraceAction.isChecked()
    for spectrumView in self.spectrumViews:
      spectrumView.updateTrace(self.mousePosition, self.mousePixel, updateHTrace, updateVTrace)
    
  def toggleHTrace(self):
    self.hTraceAction.setChecked(not self.hTraceAction.isChecked())
    self.updateTraces()

  def toggleVTrace(self):
    self.vTraceAction.setChecked(not self.vTraceAction.isChecked())
    self.updateTraces()

  def mouseMoved(self, positionPixel):

    GuiStrip.mouseMoved(self, positionPixel)
    self.updateTraces()
    
  def setZWidgets(self):
          
    for n, zAxis in enumerate(self.orderedAxes[2:]):
      minZPlaneSize = None
      minAliasedFrequency = maxAliasedFrequency = None
      for spectrumView in self.spectrumViews:
        # spectrum = spectrumView.spectrum
        # zDim = spectrum.axisCodes.index(zAxis.code)

        position, width, totalPointCount, minFrequency, maxFrequency, dataDim = (
          spectrumView._getSpectrumViewParams(n+2))
      
        # minFrequency = spectrum.minAliasedFrequencies[zDim]
        # TBD: the below does not work for pseudo-ND data sets
        # if minFrequency is None:
        #   totalPointCount = spectrum.totalPointCounts[zDim]
        #   minFrequency = spectrum.getDimValueFromPoint(zDim, totalPointCount-1.0)
        if minAliasedFrequency is None or minFrequency < minAliasedFrequency:
          minAliasedFrequency = minFrequency

        # maxFrequency = spectrumView.spectrum.maxAliasedFrequencies[zDim]
        # TBD: the below does not work for pseudo-ND data sets
        # if maxFrequency is None:
        #   maxFrequency = spectrum.getDimValueFromPoint(zDim, 0.0)
        if maxAliasedFrequency is None or maxFrequency < maxAliasedFrequency:
          maxAliasedFrequency = maxFrequency

        # NBNB 1) we should use the region width for the step size. 2) the width is the same in all cases
        # zPlaneSize = spectrumView._apiSpectrumView.spectrumView.orderedDataDims[n].getDefaultPlaneSize()
        # zPlaneSize = spectrumView.zPlaneSize()
        minZPlaneSize = width
        # if zPlaneSize is not None:
        #   if minZPlaneSize is None or zPlaneSize < minZPlaneSize:
        #     minZPlaneSize = zPlaneSize
          
      if minZPlaneSize is None:
        minZPlaneSize = 1.0 # arbitrary
      
      planeLabel = self.planeToolbar.planeLabels[n]
      
      planeLabel.setSingleStep(minZPlaneSize)
    
      if minAliasedFrequency is not None:
        planeLabel.setMinimum(minAliasedFrequency)
      
      if maxAliasedFrequency is not None:
        planeLabel.setMaximum(maxAliasedFrequency)

      planeLabel.setValue(zAxis.position)
    
      if not self.haveSetupZWidgets:
        # have to set this up here, otherwise the callback is called too soon and messes up the position
        planeLabel.valueChanged.connect(partial(self.setZPlanePosition, n))
    
    self.haveSetupZWidgets = True
      
  def changeZPlane(self, n=0, planeCount=None, position=None):
    
    zAxis = self.orderedAxes[n+2]
    planeLabel = self.planeToolbar.planeLabels[n]
    planeSize = planeLabel.singleStep()

    if planeCount:
      delta = planeSize * planeCount
      zAxis.position += delta
      #planeLabel.setValue(zAxis.position)
    elif position is not None: # should always be the case
      zAxis.position = position
      #planeLabel.setValue(zAxis.position)

      # else:
      #   print('position is outside spectrum bounds')

  def changePlaneCount(self, n=0, value=1):
    zAxis = self.orderedAxes[n+2]
    zAxis.width*=value

  def nextZPlane(self, n=0):

    self.changeZPlane(n, planeCount=-1) # -1 because ppm units are backwards

  def prevZPlane(self, n=0):

    self.changeZPlane(n, planeCount=1) # -1 because ppm units are backwards

  def addPlaneToolbar(self):

    callbacks = [self.prevZPlane, self.nextZPlane, self.setZPlanePosition, self.setPlaneCount]

    self.planeToolbar = PlaneToolbar(self, grid=(1, self.guiSpectrumDisplay.orderedStrips.index(self)),
                                     hAlign='center', vAlign='c', callbacks=callbacks)
    self.planeToolbar.setMinimumWidth(250)

  def blankCallback(self):
    pass

  def setZPlanePosition(self, n, value):
    planeLabel = self.planeToolbar.planeLabels[n]
    if planeLabel.minimum() <= planeLabel.value() <= planeLabel.maximum():
      self.changeZPlane(n, position=value)

  def setPlaneCount(self, n=0, value=1):

    planeCount = self.planeToolbar.planeCounts[n]
    self.changePlaneCount(value=(value/planeCount.oldValue))
    planeCount.oldValue = value

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
      
    peaks = [peak for peak in peaks if self.peakIsInPlane(peak)]
    self.stripFrame.guiSpectrumDisplay.showPeaks(peakListView, peaks)

def _spectrumViewCreated(project:Project, apiStripSpectrumView:ApiStripSpectrumView):
  strip = project._data2Obj[apiStripSpectrumView.strip]
  if isinstance(strip, GuiStripNd) and not strip.haveSetupZWidgets:
    strip.setZWidgets()

# Add notifier functions to Project
Project._setupNotifier(_spectrumViewCreated, ApiStripSpectrumView, 'postInit')

         