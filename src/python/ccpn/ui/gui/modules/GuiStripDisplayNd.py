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
from PyQt4 import QtCore, QtGui

from ccpn.core.Project import Project
from ccpn.core.Peak import Peak


from ccpnmodel.ccpncore.api.ccpnmr.gui.Task import FreeStrip as ApiFreeStrip
from ccpnmodel.ccpncore.api.ccpnmr.gui.Task import BoundDisplay as ApiBoundDisplay

from ccpn.ui.gui.widgets.Icon import Icon

import typing

from ccpn.ui.gui.modules.GuiSpectrumDisplay import GuiSpectrumDisplay
from ccpn.ui.gui.modules.spectrumItems import GuiPeakListView

class GuiStripDisplayNd(GuiSpectrumDisplay):

  def __init__(self):

    # below are so we can reuse PeakItems and only create them as needed
    self.activePeakItemDict = {}  # maps peakListView to apiPeak to peakItem for peaks which are being displayed
    # cannot use (wrapper) peak as key because project._data2Obj dict invalidates mapping before deleted callback is called
    # TBD: this might change so that we can use wrapper peak (which would make nicer code in showPeaks and deletedPeak below)
    ###self.inactivePeakItems = set() # contains unused peakItems
    self.inactivePeakItemDict = {}  # maps peakListView to apiPeak to set of peaks which are not being displayed
    
    GuiSpectrumDisplay.__init__(self)

    self.isGrouped = False
    
    self.spectrumActionDict = {}  # apiDataSource --> toolbar action (i.e. button)

    self._fillToolBar()
    self.setAcceptDrops(True)

  def addStrip(self) -> 'GuiStripNd':
    """
    Creates a new strip by duplicating the first strip in the display.
    """
    newStrip = self.strips[0].clone()
    if self._appBase.ui.mainWindow is not None:
      mainWindow = self._appBase.ui.mainWindow
    else:
      mainWindow = self._appBase._mainWindow
    mainWindow.pythonConsole.writeConsoleCommand(
        "strip.clone()", strip=self.strips[0].clone())
    self.project._logger.info("strip = project.getByPid('%s')\nstrip.clone()" % self.strips[0].pid)
    return newStrip

  def showSpinSystemLabel(self):
    """NBNB do we still need this?"""
    self.spinSystemSideLabel.show()

  def hideSpinSystemLabel(self):
    """NBNB do we still need this?"""
    self.hideSystemSideLabel.show()

  def _fillToolBar(self):
    """
    Adds specific icons for Nd spectra to the spectrum utility toolbar.
    """
    GuiSpectrumDisplay._fillToolBar(self)
    
    spectrumUtilToolBar = self.spectrumUtilToolBar
    
    plusOneAction = spectrumUtilToolBar.addAction("+1", self.addContourLevel)
    plusOneIcon = Icon('icons/contour-add')
    plusOneAction.setIcon(plusOneIcon)
    plusOneAction.setToolTip('Add One Level')
    minusOneAction = spectrumUtilToolBar.addAction("+1", self.removeContourLevel)
    minusOneIcon = Icon('icons/contour-remove')
    minusOneAction.setIcon(minusOneIcon)
    minusOneAction.setToolTip('Remove One Level ')
    upBy2Action = spectrumUtilToolBar.addAction("*1.4", self.raiseContourBase)
    upBy2Icon = Icon('icons/contour-base-up')
    upBy2Action.setIcon(upBy2Icon)
    upBy2Action.setToolTip('Raise Contour Base Level')
    downBy2Action = spectrumUtilToolBar.addAction("/1.4", self.lowerContourBase)
    downBy2Icon = Icon('icons/contour-base-down')
    downBy2Action.setIcon(downBy2Icon)
    downBy2Action.setToolTip('Lower Contour Base Level')
    storeZoomAction = spectrumUtilToolBar.addAction("Store Zoom", self._storeZoom)
    storeZoomIcon = Icon('icons/zoom-store')
    storeZoomAction.setIcon(storeZoomIcon)
    storeZoomAction.setToolTip('Store Zoom')
    restoreZoomAction = spectrumUtilToolBar.addAction("Restore Zoom", self._restoreZoom)
    restoreZoomIcon = Icon('icons/zoom-restore')
    restoreZoomAction.setIcon(restoreZoomIcon)
    restoreZoomAction.setToolTip('Restore Zoom')

  def raiseContourBase(self):
    """
    Increases contour base level for all spectra visible in the display.
    """
    for spectrumView in self.spectrumViews:
      if spectrumView.isVisible():
        apiDataSource = spectrumView._wrappedData.spectrumView.dataSource
        apiDataSource.positiveContourBase *= apiDataSource.positiveContourFactor
        apiDataSource.negativeContourBase *= apiDataSource.negativeContourFactor
        spectrumView.update()
        spectrum = spectrumView.spectrum
        if self._appBase.ui.mainWindow is not None:
          mainWindow = self._appBase.ui.mainWindow
        else:
          mainWindow = self._appBase._mainWindow
        mainWindow.pythonConsole.writeConsoleCommand(
        "spectrum.positiveContourBase = %s" % spectrum.positiveContourBase, spectrum=spectrum)
        mainWindow.pythonConsole.writeConsoleCommand(
        "spectrum.negativeContourBase = %s" % spectrum.negativeContourBase, spectrum=spectrum)
        self.project._logger.info("spectrum = project.getByPid(%s)" % spectrum.pid)
        self.project._logger.info("spectrum.positiveContourBase = %s" % spectrum.positiveContourBase)
        self.project._logger.info("spectrum.negativeContourBase = %s" % spectrum.negativeContourBase)

  def lowerContourBase(self):
    """
    Decreases contour base level for all spectra visible in the display.
    """
    for spectrumView in self.spectrumViews:
      if spectrumView.isVisible():
        apiDataSource = spectrumView._wrappedData.spectrumView.dataSource
        apiDataSource.positiveContourBase /= apiDataSource.positiveContourFactor
        apiDataSource.negativeContourBase /= apiDataSource.negativeContourFactor
        spectrumView.update()
        spectrum = spectrumView.spectrum
        if self._appBase.ui.mainWindow is not None:
          mainWindow = self._appBase.ui.mainWindow
        else:
          mainWindow = self._appBase._mainWindow
        mainWindow.pythonConsole.writeConsoleCommand(
        "spectrum.positiveContourBase = %s" % spectrum.positiveContourBase, spectrum=spectrum)
        mainWindow.pythonConsole.writeConsoleCommand(
        "spectrum.negativeContourBase = %s" % spectrum.negativeContourBase, spectrum=spectrum)
        self.project._logger.info("spectrum = project.getByPid(%s)" % spectrum.pid)
        self.project._logger.info("spectrum.positiveContourBase = %s" % spectrum.positiveContourBase)
        self.project._logger.info("spectrum.negativeContourBase = %s" % spectrum.negativeContourBase)

  def addContourLevel(self):
    """
    Increases number of contours by 1 for all spectra visible in the display.
    """
    for spectrumView in self.spectrumViews:
      if spectrumView.isVisible():
        apiDataSource = spectrumView._wrappedData.spectrumView.dataSource
        apiDataSource.positiveContourCount += 1
        apiDataSource.negativeContourCount += 1
        spectrum = spectrumView.spectrum
        if self._appBase.ui.mainWindow is not None:
          mainWindow = self._appBase.ui.mainWindow
        else:
          mainWindow = self._appBase._mainWindow
        mainWindow.pythonConsole.writeConsoleCommand(
        "spectrum.positiveContourCount = %s" % spectrum.positiveContourCount, spectrum=spectrum)
        mainWindow.pythonConsole.writeConsoleCommand(
        "spectrum.negativeContourCount = %s" % spectrum.negativeContourCount, spectrum=spectrum)
        self.project._logger.info("spectrum = project.getByPid(%s)" % spectrum.pid)
        self.project._logger.info("spectrum.positiveContourCount = %s" % spectrum.positiveContourCount)
        self.project._logger.info("spectrum.negativeContourCount = %s" % spectrum.negativeContourCount)

  def removeContourLevel(self):
    """
    Decreases number of contours by 1 for all spectra visible in the display.
    """
    for spectrumView in self.spectrumViews:
      if spectrumView.isVisible():
        apiDataSource = spectrumView._wrappedData.spectrumView.dataSource
        if apiDataSource.positiveContourCount > 0:
          apiDataSource.positiveContourCount -= 1
        if apiDataSource.negativeContourCount > 0:
          apiDataSource.negativeContourCount -= 1
        spectrum = spectrumView.spectrum
        if self._appBase.ui.mainWindow is not None:
          mainWindow = self._appBase.ui.mainWindow
        else:
          mainWindow = self._appBase._mainWindow
        mainWindow.pythonConsole.writeConsoleCommand(
        "spectrum.positiveContourCount = %s" % spectrum.positiveContourCount, spectrum=spectrum)
        mainWindow.pythonConsole.writeConsoleCommand(
        "spectrum.negativeContourCount = %s" % spectrum.negativeContourCount, spectrum=spectrum)
        self.project._logger.info("spectrum = project.getByPid(%s)" % spectrum.pid)
        self.project._logger.info("spectrum.positiveContourCount = %s" % spectrum.positiveContourCount)
        self.project._logger.info("spectrum.negativeContourCount = %s" % spectrum.negativeContourCount)
    
  def showPeaks(self, peakListView:GuiPeakListView.GuiPeakListView, peaks:typing.List[Peak]):
    """
    Displays specified peaks in all strips of the display using peakListView
    """
    viewBox = peakListView.spectrumView.strip.viewBox
    activePeakItemDict = self.activePeakItemDict
    peakItemDict = activePeakItemDict.setdefault(peakListView, {})
    inactivePeakItemDict = self.inactivePeakItemDict
    inactivePeakItems = inactivePeakItemDict.setdefault(peakListView, set())
    ##inactivePeakItems = self.inactivePeakItems
    existingApiPeaks = set(peakItemDict.keys())
    unusedApiPeaks = existingApiPeaks - set([peak._wrappedData for peak in peaks])
    for apiPeak in unusedApiPeaks:
      peakItem = peakItemDict.pop(apiPeak)
      #viewBox.removeItem(peakItem)
      inactivePeakItems.add(peakItem)
      peakItem.setVisible(False)
    for peak in peaks:
      apiPeak = peak._wrappedData
      if apiPeak in existingApiPeaks:
        continue
      if inactivePeakItems:
        peakItem = inactivePeakItems.pop()
        peakItem.setupPeakItem(peakListView, peak)
        #viewBox.addItem(peakItem)
        peakItem.setVisible(True)
      else:
        peakItem = GuiPeakListView.PeakNd(peakListView, peak)
      peakItemDict[apiPeak] = peakItem

# Functions for notifiers

# We are not currently using Free strips
#
# # Could be changed to wrapper level, but would be triggered much more often. Leave  as is.
# def _changedFreeStripAxisOrdering(project:Project, apiStrip:ApiFreeStrip):
#   """Used (and works) for either BoundDisplay of FreeStrip"""
#   project._data2Obj[apiStrip]._setZWidgets()

def _changedBoundDisplayAxisOrdering(project:Project, apiDisplay:ApiBoundDisplay):
  """Used (and works) for either BoundDisplay of FreeStrip"""
  for strip in project._data2Obj[apiDisplay].strips:
    strip._setZWidgets()
