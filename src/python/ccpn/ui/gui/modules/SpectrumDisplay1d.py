"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2017"
__credits__ = ("Wayne Boucher, Ed Brooksbank, Rasmus H Fogh, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license",
               "or ccpnmodel.ccpncore.memops.Credits.CcpnLicense for licence text")
__reference__ = ("For publications, please use reference from http://www.ccpn.ac.uk/v3-software/downloads/license",
               "or ccpnmodel.ccpncore.memops.Credits.CcpNmrReference")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: CCPN $"
__dateModified__ = "$dateModified: 2017-07-07 16:32:45 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.b3 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from typing import Sequence

from ccpn.ui.gui.lib.GuiSpectrumDisplay import GuiSpectrumDisplay
from ccpn.ui.gui.widgets.Icon import Icon
from ccpn.ui.gui.popups.SpectrumPropertiesPopup import SpectrumDisplayPropertiesPopup1d


class SpectrumDisplay1d(GuiSpectrumDisplay):

  def __init__(self, mainWindow, name):
    # if not apiSpectrumDisplay1d.strips:
    #   apiSpectrumDisplay1d.newStrip1d()

    GuiSpectrumDisplay.__init__(self, mainWindow=mainWindow, name=name, useScrollArea=True)
    self._fillToolBar()
    # self.addSpinSystemSideLabel()
    self.setAcceptDrops(True)
    self.isGrouped = False
    self.spectrumActionDict = {}
    self.activePeakItemDict = {}  # maps peakListView to apiPeak to peakItem for peaks which are being displayed
    # cannot use (wrapper) peak as key because project._data2Obj dict invalidates mapping before deleted callback is called
    # TBD: this might change so that we can use wrapper peak (which would make nicer code in showPeaks and deletedPeak below)
    ###self.inactivePeakItems = set() # contains unused peakItems
    self.inactivePeakItemDict = {}  # maps peakListView to apiPeak to set of peaks which are not being displayed

    # store the list of ordered spectrumViews
    self._orderedSpectrumViews = None

  def showPeaks(self, peakListView, peaks):
    """
    Displays specified peaks in all strips of the display using peakListView
    """

    # NB should not be imported at top of file to avoid potential cyclic imports
    from ccpn.ui.gui.lib import GuiPeakListView

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
        peakItem = GuiPeakListView.Peak1d(peak, peakListView)
      peakItemDict[apiPeak] = peakItem


  def _fillToolBar(self):
    """
    Adds specific icons for 1d spectra to the spectrum utility toolbar.
    """
    spectrumUtilToolBar = self.spectrumUtilToolBar
    #spectrumUtilToolBar.setIconSize(QtCore.QSize(64, 64)) # set in constructor

    # GWV: removed: GuiSpectrumDisplay._fillToolBar(self)
    #TODO: See Nd case on how to do this better

    # Disable add and remove strips, as they're broken
    ###spectrumUtilToolBar.removeAction(spectrumUtilToolBar.actions()[0])
    ###spectrumUtilToolBar.removeAction(spectrumUtilToolBar.actions()[0])
    # spectrumUtilToolBar.actions()[0].setDisabled(True)

    # Why does asking for the icon size fix it?  I don't know, but it does!

    # ('Increase Strip Width', 'icons/range-expand', 'Increase the width of strips in display', True, self.increaseStripWidth),
    # ('Decrease Strip Width', 'icons/range-contract', 'Decrease the width of strips in display', True, self.decreaseStripWidth),
    increaseStripWidthAction = spectrumUtilToolBar.addAction("Increase Strip Width", self.increaseStripWidth)
    increaseStripWidthIcon = Icon('icons/range-expand')
    increaseStripWidthAction.setIcon(increaseStripWidthIcon)
    decreaseStripWidthAction = spectrumUtilToolBar.addAction("Decrease Strip Width", self.decreaseStripWidth)
    decreaseStripWidthIcon = Icon('icons/range-contract')
    decreaseStripWidthAction.setIcon(decreaseStripWidthIcon)

    autoScaleAction = spectrumUtilToolBar.addAction("AutoScale", self.resetYZooms)
    autoScaleActionIcon = Icon('icons/zoom-best-fit-1d')
    # autoScaleActionIcon.actualSize(QtCore.QSize(10, 10))
    autoScaleAction.setIcon(autoScaleActionIcon)
    # autoScaleAction.setText("AutoScale")
    fullZoomAction = spectrumUtilToolBar.addAction("Full", self.resetXZooms)
    fullZoomIcon = Icon('icons/zoom-full-1d')
    fullZoomAction.setIcon(fullZoomIcon)
    storeZoomAction = spectrumUtilToolBar.addAction("Store Zoom", self._storeZoom)
    storeZoomIcon = Icon('icons/zoom-store')
    storeZoomAction.setIcon(storeZoomIcon)
    storeZoomAction.setToolTip('Store Zoom')
    restoreZoomAction = spectrumUtilToolBar.addAction("Restore Zoom", self._restoreZoom)
    restoreZoomIcon = Icon('icons/zoom-restore')
    restoreZoomAction.setIcon(restoreZoomIcon)
    restoreZoomAction.setToolTip('Restore Zoom')



  def processSpectra(self, pids:Sequence[str], event):
    """Display spectra defined by list of Pid strings"""
    for ss in pids:
      print('processing Spectrum', ss)
    print(self.parent())

  def _updatePlotColour(self, spectrum):
    apiDataSource = spectrum._wrappedData
    action = self.spectrumActionDict.get(apiDataSource)
    if action:
      for strip in self.strips:
        for spectrumView in strip.spectrumViews:
          if spectrumView.spectrum is spectrum:
            spectrumView.plot.setPen(apiDataSource.sliceColour)

  def adjustContours(self):
    # insert popup to modify contours
    popup = SpectrumDisplayPropertiesPopup1d(parent=self.mainWindow, mainWindow=self.mainWindow,
                                             orderedSpectrumViews=self.orderedSpectrumViews(self.spectrumViews))
    popup.exec_()
    popup.raise_()


# Functions for notifiers

# def _updateSpectrumPlotColour(project:Project, apiDataSource:ApiDataSource):
#   getDataObj = project._data2Obj.get
#   spectrum = getDataObj(apiDataSource)
#
#   for task in project.tasks:
#     if task.status == 'active':
#       for spectrumDisplay in task.spectrumDisplays:
#         if spectrumDisplay.is1D:
#           spectrumDisplay._updatePlotColour(spectrum)
#
# def _updateSpectrumViewPlotColour(project:Project, apiSpectrumView:ApiSpectrumView):
#   getDataObj = project._data2Obj.get
#   spectrum = getDataObj(apiSpectrumView.dataSource)
#   if spectrum:
#     spectrumDisplay = getDataObj(apiSpectrumView.spectrumDisplay)
#     if spectrumDisplay.is1D:
#       spectrumDisplay._updatePlotColour(spectrum)

