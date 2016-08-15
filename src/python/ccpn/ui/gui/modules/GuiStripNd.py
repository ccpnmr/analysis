"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (www.ccpn.ac.uk) 2014 - $Date$"
__credits__ = "Wayne Boucher, Rasmus H Fogh, Simon P Skinner, Geerten W Vuister"
__license__ = ("CCPN license. See www.ccpn.ac.uk/license"
              "or ccpnmodel.ccpncore.memops.Credits.CcpnLicense for license text")
__reference__ = ("For publications, please use reference from www.ccpn.ac.uk/license"
                " or ccpnmodel.ccpncore.memops.Credits.CcpNmrReference")

#=========================================================================================
# Last code modification:
#=========================================================================================
__author__ = "$Author$"
__date__ = "$Date$"
__version__ = "$Revision$"

#=========================================================================================
# Start of code
#=========================================================================================
__author__ = 'simon'

#from PyQt4 import QtGui, QtCore, QtOpenGL
from PyQt4 import QtGui, QtCore

# import math
import numpy
from functools import partial
# import pyqtgraph as pg

# from ccpn.core.Project import Project
from ccpn.core.PeakList import PeakList
# from ccpn.core.Peak import Peak

# from ccpnmodel.ccpncore.api.ccpnmr.gui.Task import Axis as ApiAxis
# from ccpnmodel.ccpncore.api.ccpnmr.gui.Task import StripSpectrumView as ApiStripSpectrumView

# from ccpn.ui.gui.widgets.Button import Button
# from ccpn.ui.gui.widgets.DoubleSpinbox import DoubleSpinbox
from ccpn.ui.gui.widgets.Icon import Icon
from ccpn.ui.gui.widgets.Menu import Menu
from ccpn.ui.gui.widgets.PlaneToolbar import PlaneToolbar

# from ccpn.ui.gui.widgets.Spinbox import Spinbox

import typing

from ccpn.ui.gui.modules.GuiStrip import GuiStrip

# from ccpn.ui.gui.modules.spectrumItems.GuiPeakListView import GuiPeakListView

class GuiStripNd(GuiStrip):

  def __init__(self):
    GuiStrip.__init__(self, useOpenGL=True)

    # the scene knows which items are in it but they are stored as a list and the below give fast access from API object to QGraphicsItem
    ###self.peakLayerDict = {}  # peakList --> peakLayer
    ###self.peakListViewDict = {}  # peakList --> peakListView
    
    self.haveSetupZWidgets = False
    self.viewBox.menu = self._get2dContextMenu()
    self.viewBox.invertX()
    self.viewBox.invertY()
    ###self.region = guiSpectrumDisplay.defaultRegion()
    self.planeLabel = None
    self.axesSwapped = False
    self._addPlaneToolbar()
    if self._appBase.ui.mainWindow is not None:
      self.pythonConsole = self._appBase.ui.mainWindow.pythonConsole
    else:
      self.pythonConsole = self._appBase._mainWindow.pythonConsole
    self.logger = self._project._logger
    self.mouseDragEvent = self._mouseDragEvent
    self.updateRegion = self._updateRegion

  def _mouseDragEvent(self, event):
    """
    Re-implemented mouse event to enable smooth panning.
    """
    if event.button() == QtCore.Qt.RightButton:
      pass
    else:
      self.viewBox.mouseDragEvent(self, event)

  def _get2dContextMenu(self) -> Menu:
    """
    Creates and returns the Nd context menu
    """
    self.contextMenu = Menu('', self, isFloatWidget=True)
    self.toolbarAction = self.contextMenu.addItem("Toolbar", callback=self.guiSpectrumDisplay.toggleToolbar, checkable=True)
    self.crossHairAction = self.contextMenu.addItem("Crosshair", callback=self._toggleCrossHair, checkable=True)
    self.hTraceAction = self.contextMenu.addItem("H Trace", checked=False, checkable=True)
    self.vTraceAction = self.contextMenu.addItem("V Trace", checked=False, checkable=True)
    self.gridAction = self.contextMenu.addItem("Grid", callback=self.toggleGrid, checkable=True)
    plusOneAction = self.contextMenu.addAction("Add Contour Level", self.guiSpectrumDisplay.addContourLevel)
    plusOneIcon = Icon('icons/contour-add')
    plusOneAction.setIcon(plusOneIcon)
    plusOneAction.setToolTip('Add One Level')
    minusOneAction = self.contextMenu.addAction("Remove Contour Level", self.guiSpectrumDisplay.removeContourLevel)
    minusOneIcon = Icon('icons/contour-remove')
    minusOneAction.setIcon(minusOneIcon)
    minusOneAction.setToolTip('Remove One Level ')
    upBy2Action = self.contextMenu.addAction("Raise Base Level", self.guiSpectrumDisplay.raiseContourBase)
    upBy2Icon = Icon('icons/contour-base-up')
    upBy2Action.setIcon(upBy2Icon)
    upBy2Action.setToolTip('Raise Contour Base Level')
    downBy2Action = self.contextMenu.addAction("Lower Base Level", self.guiSpectrumDisplay.lowerContourBase)
    downBy2Icon = Icon('icons/contour-base-down')
    downBy2Action.setIcon(downBy2Icon)
    downBy2Action.setToolTip('Lower Contour Base Level')
    storeZoomAction = self.contextMenu.addAction("Store Zoom", self.guiSpectrumDisplay._storeZoom)
    storeZoomIcon = Icon('icons/zoom-store')
    storeZoomAction.setIcon(storeZoomIcon)
    storeZoomAction.setToolTip('Store Zoom')
    restoreZoomAction = self.contextMenu.addAction("Restore Zoom", self.guiSpectrumDisplay._restoreZoom)
    restoreZoomIcon = Icon('icons/zoom-restore')
    restoreZoomAction.setIcon(restoreZoomIcon)
    restoreZoomAction.setToolTip('Restore Zoom')
    resetZoomAction = self.contextMenu.addAction("Reset Zoom", self.resetZoom)
    resetZoomIcon = Icon('icons/zoom-full')
    resetZoomAction.setIcon(resetZoomIcon)
    resetZoomAction.setToolTip('Reset Zoom')
    printAction = self.contextMenu.addAction("Print to File...", lambda: self.spectrumDisplay.window.printToFile(self.spectrumDisplay))
    printIcon = Icon('icons/print')
    printAction.setIcon(printIcon)
    printAction.setToolTip('Print Spectrum Display to File')

    self.contextMenu.navigateToMenu = self.contextMenu.addMenu('Navigate To')

    # self.navigateToMenu = self.contextMenu.addMenu('Navigate To')
    # self.spectrumDisplays = self.getSpectrumDisplays()
    # for spectrumDisplay in self.spectrumDisplays:
    #   spectrumDisplayAction = self.navigateToMenu.addAction(spectrumDisplay.pid)
    #   receiver = lambda spectrumDisplay=spectrumDisplay.pid: self.navigateTo(spectrumDisplay)
    #   self.connect(spectrumDisplayAction, QtCore.SIGNAL('triggered()'), receiver)
    #   self.navigateToMenu.addAction(spectrumDisplay)



    self.crossHairAction.setChecked(self.vLine.isVisible())

    if self.grid.isVisible():
      self.gridAction.setChecked(True)
    else:
      self.gridAction.setChecked(False)
    # self.contextMenu.addAction(self.crossHairAction, isFloatWidget=True)
    return self.contextMenu

  def resetZoom(self, axis=None):
    """
    Resets zoom of strip axes to limits of maxima and minima of the limits of the displayed spectra.
    """
    x = []
    y = []
    for spectrumView in self.spectrumViews:

      # Get spectrum dimension index matching display X and Y
      # without using axis codes, as they may not match
      spectrumIndices = spectrumView._displayOrderSpectrumDimensionIndices
      spectrumLimits = spectrumView.spectrum.spectrumLimits
      x.append(spectrumLimits[spectrumIndices[0]])
      y.append(spectrumLimits[spectrumIndices[1]])
      # xIndex = spectrumView.spectrum.axisCodes.index(self.axisCodes[0])
      # yIndex = spectrumView.spectrum.axisCodes.index(self.axisCodes[1])
      # x.append(spectrumView.spectrum.spectrumLimits[xIndex])
      # y.append(spectrumView.spectrum.spectrumLimits[yIndex])

    xArray = numpy.array(x).flatten()
    yArray = numpy.array(y).flatten()

    zoomXArray = ([min(xArray), max(xArray)])
    zoomYArray = ([min(yArray), max(yArray)])
    self.zoomToRegion(zoomXArray, zoomYArray)
    self.pythonConsole.writeConsoleCommand("strip.resetZoom()", strip=self)
    self.logger.info("strip = application.getByGid('%s')\nstrip.resetZoom()" % self.pid)
    return zoomXArray, zoomYArray

  def resetAxisRange(self, axis):
    if not axis:
      return

    positionArray = []

    for spectrumView in self.spectrumViews:

      # Get spectrum dimension index matching display X or Y
      # without using axis codes, as they may not match
      spectrumIndices = spectrumView._displayOrderSpectrumDimensionIndices
      spectrumLimits = spectrumView.spectrum.spectrumLimits
      positionArray.append(spectrumLimits[spectrumIndices[axis]])

    zoomArray = ([min(positionArray), max(positionArray)])
    if axis == 0:
      self.zoomX(*zoomArray)
    elif axis == 1:
      self.zoomY(*zoomArray)


  def _updateRegion(self, viewBox):
    # this is called when the viewBox is changed on the screen via the mouse

    GuiStrip._updateRegion(self, viewBox)
    self._updateTraces()

  def _updateTraces(self):

    if self.mousePosition:
      updateHTrace = self.hTraceAction.isChecked()
      updateVTrace = self.vTraceAction.isChecked()
      for spectrumView in self.spectrumViews:
        spectrumView._updateTrace(self.mousePosition, self.mousePixel, updateHTrace, updateVTrace)

  def toggleHorizontalTrace(self):
    """
    Toggles whether or not horizontal trace is displayed.
    """
    self.hTraceAction.setChecked(not self.hTraceAction.isChecked())
    self._updateTraces()

  def toggleVerticalTrace(self):
    """
    Toggles whether or not vertical trace is displayed.
    """
    self.vTraceAction.setChecked(not self.vTraceAction.isChecked())
    self._updateTraces()

  def _mouseMoved(self, positionPixel):

    GuiStrip._mouseMoved(self, positionPixel)
    self._updateTraces()

  def _setZWidgets(self):
    """
    # CCPN INTERNAL - called in _changedBoundDisplayAxisOrdering function of GuiStripDisplayNd.py
    Sets values for the widgets in the plane toolbar.
    """

    for n, zAxis in enumerate(self.orderedAxes[2:]):
      minZPlaneSize = None
      minAliasedFrequency = maxAliasedFrequency = None
      for spectrumView in self.spectrumViews:
        # spectrum = spectrumView.spectrum
        # zDim = spectrum.axisCodes.index(zAxis.code)

        # position, width, totalPointCount, minFrequency, maxFrequency, dataDim = (
        #   spectrumView._getSpectrumViewParams(n+2))
        viewParams = spectrumView._getSpectrumViewParams(n+2)

        minFrequency = viewParams.minAliasedFrequency
        if minFrequency is not None:
         if minAliasedFrequency is None or minFrequency < minAliasedFrequency:
           minAliasedFrequency = minFrequency

        maxFrequency = viewParams.maxAliasedFrequency
        if maxFrequency is not None:
          if maxAliasedFrequency is None or maxFrequency < maxAliasedFrequency:
            maxAliasedFrequency = maxFrequency

        width = viewParams.valuePerPoint
        if minZPlaneSize is None or width < minZPlaneSize:
          minZPlaneSize = width

      if minZPlaneSize is None:
        minZPlaneSize = 1.0 # arbitrary
      else:
        # Necessary, otherwise it does not know what width it should have
        zAxis.width = minZPlaneSize

      planeLabel = self.planeToolbar.planeLabels[n]

      planeLabel.setSingleStep(minZPlaneSize)

      # have to do the following in order: maximum, value, minimum
      # otherwise Qt will set bogus value to guarantee that minimum <= value <= maximum

      if maxAliasedFrequency is not None:
        planeLabel.setMaximum(maxAliasedFrequency)

      planeLabel.setValue(zAxis.position)

      if minAliasedFrequency is not None:
        planeLabel.setMinimum(minAliasedFrequency)

      if not self.haveSetupZWidgets:
        # have to set this up here, otherwise the callback is called too soon and messes up the position
        planeLabel.editingFinished.connect(partial(self._setZPlanePosition, n, planeLabel.value()))

    self.haveSetupZWidgets = True

  def changeZPlane(self, n:int=0, planeCount:int=None, position:float=None):
    """
    Changes the position of the z axis of the strip by number of planes or a ppm position, depending
    on which is specified.
    """

    zAxis = self.orderedAxes[n+2]
    planeLabel = self.planeToolbar.planeLabels[n]
    planeSize = planeLabel.singleStep()

    # below is hack to prevent initial setting of value to 99.99 when dragging spectrum onto blank display
    if planeLabel.minimum() == 0 and planeLabel.value() == 99.99 and planeLabel.maximum() == 99.99:
      return

    if planeCount:
      delta = planeSize * planeCount
      position = zAxis.position + delta
      if planeLabel.minimum() <= position <= planeLabel.maximum():
        zAxis.position = position
      #planeLabel.setValue(zAxis.position)
    elif position is not None: # should always be the case
      if planeLabel.minimum() <= position <= planeLabel.maximum():
        zAxis.position = position
        self.pythonConsole.writeConsoleCommand("strip.changeZPlane(position=%f)" % position, strip=self)
        self.logger.info("strip = application.getByGid('%s')\nstrip.changeZPlane(position=%f)" % (self.pid, position))
        #planeLabel.setValue(zAxis.position)

      # else:
      #   print('position is outside spectrum bounds')

  def _changePlaneCount(self, n:int=0, value:int=1):
    """
    Changes the number of planes displayed simultaneously.
    """
    zAxis = self.orderedAxes[n+2]
    planeLabel = self.planeToolbar.planeLabels[n]
    zAxis.width = value * planeLabel.singleStep()

  def nextZPlane(self, n:int=0):
    """
    Increases z ppm position by one plane
    """
    self.changeZPlane(n, planeCount=-1) # -1 because ppm units are backwards
    self.pythonConsole.writeConsoleCommand("strip.nextZPlane()", strip=self)
    self.logger.info("strip = application.getByGid('%s')\nstrip.nextZPlane()" % self.pid)

  def prevZPlane(self, n:int=0):
    """
    Decreases z ppm position by one plane
    """
    self.changeZPlane(n, planeCount=1) # -1 because ppm units are backwards
    self.pythonConsole.writeConsoleCommand("strip.prevZPlane()", strip=self)
    self.logger.info("strip = application.getByGid('%s')\nstrip.prevZPlane()" % self.pid)

  def _addPlaneToolbar(self):
    """
    Adds the plane toolbar to the strip.
    """
    callbacks = [self.prevZPlane, self.nextZPlane, self._setZPlanePosition, self._changePlaneCount]

    self.planeToolbar = PlaneToolbar(self, grid=(1, self.guiSpectrumDisplay.orderedStrips.index(self)),
                                     hAlign='center', vAlign='c', callbacks=callbacks)
    self.planeToolbar.setMinimumWidth(250)

  def _setZPlanePosition(self, n:int, value:float):
    """
    Sets the value of the z plane position box if the specified value is within the displayable limits.
    """
    planeLabel = self.planeToolbar.planeLabels[n]
    #if planeLabel.valueChanged():
    #  value = planeLabel.value()
    # 8/3/2016 Rasmus Fogh. Fixed untested (obvious bug)
    # if planeLabel.minimum() <= planeLabel.value() <= planeLabel.maximum():

    # not sure the check below is needed since presumably Qt guarantees this
    if planeLabel.minimum() <= value <= planeLabel.maximum():
      self.changeZPlane(n, position=value)

  # def setPlaneCount(self, n:int=0, value:int=1):
  #   """
  #   Sets the number of planes to be displayed simultaneously.
  #   """
  #   planeCount = self.planeToolbar.planeCounts[n]
  #   self.changePlaneCount(value=(value/planeCount.oldValue))
  #   planeCount.oldValue = value

  def _findPeakListView(self, peakList:PeakList):
    
    #peakListView = self.peakListViewDict.get(peakList)
    #if peakListView:
    #  return peakListView
      
    for spectrumView in self.spectrumViews:
      for peakListView in spectrumView.peakListViews:
        if peakList is peakListView.peakList:
          #self.peakListViewDict[peakList] = peakListView
          return peakListView
            
    return None
