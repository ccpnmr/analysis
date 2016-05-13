"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (www.ccpn.ac.uk) 2014 - $Date$"
__credits__ = "Wayne Boucher, Rasmus H Fogh, Simon P Skinner, Geerten W Vuister"
__license__ = ("CCPN license. See www.ccpn.ac.uk/license"
              "or ccpncore.memops.Credits.CcpnLicense for license text")
__reference__ = ("For publications, please use reference from www.ccpn.ac.uk/license"
                " or ccpncore.memops.Credits.CcpNmrReference")

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

# from ccpn import Project
from ccpn import PeakList
# from ccpn import Peak

# from ccpncore.api.ccpnmr.gui.Task import Axis as ApiAxis
# from ccpncore.api.ccpnmr.gui.Task import StripSpectrumView as ApiStripSpectrumView

# from ccpn.ui.gui.widgets.Button import Button
# from ccpn.ui.gui.widgets.DoubleSpinbox import DoubleSpinbox
from ccpn.ui.gui.widgets.Icon import Icon
from ccpn.ui.gui.widgets.Menu import Menu
# from ccpn.ui.gui.widgets.Spinbox import Spinbox

import typing

from ccpn.ui.gui.base.PlaneToolbar import PlaneToolbar
from ccpn.ui.gui.modules.GuiStrip import GuiStrip

# from ccpn.ui.gui.modules.spectrumItems.GuiPeakListView import GuiPeakListView

class GuiStripNd(GuiStrip):

  def __init__(self):
    GuiStrip.__init__(self, useOpenGL=True)

    # the scene knows which items are in it but they are stored as a list and the below give fast access from API object to QGraphicsItem
    ###self.peakLayerDict = {}  # peakList --> peakLayer
    ###self.peakListViewDict = {}  # peakList --> peakListView
    
    self.haveSetupZWidgets = False
    self.viewBox.menu = self.get2dContextMenu()
    self.viewBox.invertX()
    self.viewBox.invertY()
    ###self.region = guiSpectrumDisplay.defaultRegion()
    self.planeLabel = None
    self.axesSwapped = False
    self.addPlaneToolbar()
    self.pythonConsole = self._appBase.mainWindow.pythonConsole
    self.logger = self._project._logger

  def mouseDragEvent(self, event):
    """
    Re-implemented mouse event to enable smooth panning.
    """
    if event.button() == QtCore.Qt.RightButton:
      pass
    else:
      self.viewBox.mouseDragEvent(self, event)

  def get2dContextMenu(self) -> Menu:
    """
    Creates and returns the Nd context menu
    """
    self.contextMenu = Menu('', self, isFloatWidget=True)
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
    printAction = self.contextMenu.addAction("Print to File...", lambda: self.spectrumDisplay.window.printToFile(self.spectrumDisplay))
    printIcon = Icon('iconsNew/print')
    printAction.setIcon(printIcon)
    printAction.setToolTip('Print Spectrum Display to File')

    self.crossHairAction.setChecked(self.vLine.isVisible())

    if self.grid.isVisible():
      self.gridAction.setChecked(True)
    else:
      self.gridAction.setChecked(False)
    # self.contextMenu.addAction(self.crossHairAction, isFloatWidget=True)
    return self.contextMenu

  def resetZoom(self):
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

    zoomArray = ([min(xArray), max(xArray), min(yArray), max(yArray)])
    self.zoomToRegion(zoomArray)
    self.pythonConsole.writeConsoleCommand("strip.resetZoom()", strip=self)
    self.logger.info("strip = project.getByPid('%s')\nstrip.resetZoom()" % self.pid)
    return zoomArray


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
    """
    Toggles whether or not horizontal trace is displayed.
    """
    self.hTraceAction.setChecked(not self.hTraceAction.isChecked())
    self.updateTraces()

  def toggleVTrace(self):
    """
    Toggles whether or not vertical trace is displayed.
    """
    self.vTraceAction.setChecked(not self.vTraceAction.isChecked())
    self.updateTraces()

  def mouseMoved(self, positionPixel):

    GuiStrip.mouseMoved(self, positionPixel)
    self.updateTraces()

  def setZWidgets(self):
    """
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

      if minAliasedFrequency is not None:
        planeLabel.setMinimum(minAliasedFrequency)

      if maxAliasedFrequency is not None:
        planeLabel.setMaximum(maxAliasedFrequency)

      planeLabel.setValue(zAxis.position)

      if not self.haveSetupZWidgets:
        # have to set this up here, otherwise the callback is called too soon and messes up the position
        planeLabel.editingFinished.connect(partial(self.setZPlanePosition, n, planeLabel.value()))

    self.haveSetupZWidgets = True

  def changeZPlane(self, n:int=0, planeCount:int=None, position:float=None):
    """
    Changes the position of the z axis of the strip by number of planes or a ppm position, depending
    on which is specified.
    """

    zAxis = self.orderedAxes[n+2]
    planeLabel = self.planeToolbar.planeLabels[n]
    planeSize = planeLabel.singleStep()

    if planeCount:
      delta = planeSize * planeCount
      zAxis.position += delta
      #planeLabel.setValue(zAxis.position)
    elif position is not None: # should always be the case
      zAxis.position = position
      self.pythonConsole.writeConsoleCommand("strip.changeZPlane(position=%f)" % position, strip=self)
      self.logger.info("strip = project.getByPid('%s')\nstrip.changeZPlane(position=%f)" % (self.pid, position))
      #planeLabel.setValue(zAxis.position)

      # else:
      #   print('position is outside spectrum bounds')

  def changePlaneCount(self, n:int=0, value:int=1):
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
    self.logger.info("strip = project.getByPid('%s')\nstrip.nextZPlane()" % self.pid)

  def prevZPlane(self, n:int=0):
    """
    Decreases z ppm position by one plane
    """
    self.changeZPlane(n, planeCount=1) # -1 because ppm units are backwards
    self.pythonConsole.writeConsoleCommand("strip.prevZPlane()", strip=self)
    self.logger.info("strip = project.getByPid('%s')\nstrip.prevZPlane()" % self.pid)

  def addPlaneToolbar(self):
    """
    Adds the plane toolbar to the strip.
    """
    callbacks = [self.prevZPlane, self.nextZPlane, self.setZPlanePosition, self.changePlaneCount]

    self.planeToolbar = PlaneToolbar(self, grid=(1, self.guiSpectrumDisplay.orderedStrips.index(self)),
                                     hAlign='center', vAlign='c', callbacks=callbacks)
    self.planeToolbar.setMinimumWidth(250)

  def blankCallback(self):
    pass

  def setZPlanePosition(self, n:int, value:float):
    """
    Sets the value of the z plane position box if the specified value is within the displayable limits.
    """
    planeLabel = self.planeToolbar.planeLabels[n]
    if planeLabel.valueChanged:
      value = planeLabel.value()
    # 8/3/2016 Rasmus Fogh. Fixed untested (obvious bug)
    # if planeLabel.minimum() <= planeLabel.value() <= planeLabel.maximum():
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
        
  # def showPeaks(self, peakList:PeakList, peaks:typing.List[Peak]=None):
  #   ###from ccpn.ui.gui.modules.spectrumItems.GuiPeakListView import GuiPeakListView
  #   # NBNB TBD 1) we should not always display all peak lists together
  #   # NBNB TBD 2) This should not be called for each strip
  #
  #   if not peaks:
  #     peaks = peakList.peaks
  #
  #   peakListView = self._findPeakListView(peakList)
  #   if not peakListView:
  #     return
  #
  #   peaks = [peak for peak in peaks if self.peakIsInPlane(peak)]
  #   self.stripFrame.guiSpectrumDisplay.showPeaks(peakListView, peaks)

# Notifiers

# Add notifier functions to Project
# def _spectrumViewCreated(project:Project, apiStripSpectrumView:ApiStripSpectrumView):
#   strip = project._data2Obj[apiStripSpectrumView.strip]
#   if isinstance(strip, GuiStripNd) and not strip.haveSetupZWidgets:
#     strip.setZWidgets()
#
# # Add notifier functions to Project
# Project._setupApiNotifier(_spectrumViewCreated, ApiStripSpectrumView, 'postInit')

         