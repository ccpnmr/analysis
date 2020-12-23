"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2020"
__credits__ = ("Ed Brooksbank, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2020-10-23 18:39:16 +0100 (Fri, October 23, 2020) $"
__version__ = "$Revision: 3.0.1 $"
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

    MAXPEAKLABELTYPES = 6
    MAXPEAKSYMBOLTYPES = 4

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

    # def showPeaks(self, peakListView, peaks):
    #     """
    #     Displays specified peaks in all strips of the display using peakListView
    #     """
    #
    #     # NB should not be imported at top of file to avoid potential cyclic imports
    #     from ccpn.ui.gui.lib import GuiPeakListView
    #
    #     viewBox = peakListView.spectrumView.strip.viewBox
    #     activePeakItemDict = self.activePeakItemDict
    #     peakItemDict = activePeakItemDict.setdefault(peakListView, {})
    #     inactivePeakItemDict = self.inactivePeakItemDict
    #     inactivePeakItems = inactivePeakItemDict.setdefault(peakListView, set())
    #     ##inactivePeakItems = self.inactivePeakItems
    #     existingApiPeaks = set(peakItemDict.keys())
    #     unusedApiPeaks = existingApiPeaks - set([peak._wrappedData for peak in peaks])
    #     for apiPeak in unusedApiPeaks:
    #         peakItem = peakItemDict.pop(apiPeak)
    #         #viewBox.removeItem(peakItem)
    #         inactivePeakItems.add(peakItem)
    #         peakItem.setVisible(False)
    #     for peak in peaks:
    #         apiPeak = peak._wrappedData
    #         if apiPeak in existingApiPeaks:
    #             continue
    #         if inactivePeakItems:
    #             peakItem = inactivePeakItems.pop()
    #             peakItem.setupPeakItem(peakListView, peak)
    #             #viewBox.addItem(peakItem)
    #             peakItem.setVisible(True)
    #         else:
    #             peakItem = GuiPeakListView.Peak1d(peak, peakListView)
    #         peakItemDict[apiPeak] = peakItem

    def _fillToolBar(self):
        """
        Adds specific icons for 1d spectra to the spectrum utility toolbar.
        """
        tb = self.spectrumUtilToolBar
        self._spectrumUtilActions = {}

        toolBarItemsFor1d = [
            #  action name,        icon,                 tooltip,                                   active, callback

            ('increaseStripWidth', 'icons/range-expand', 'Increase the width of strips in display', True, self.increaseStripSize),
            ('decreaseStripWidth', 'icons/range-contract', 'Decrease the width of strips in display', True, self.decreaseStripSize),
            ('maximiseZoom', 'icons/zoom-full', 'Maximise Zoom (ZA)', True, self._resetAllZooms),

            ('maximiseHeight', 'icons/zoom-best-fit-1d', 'Maximise Height', True, self._resetYZooms),
            ('maximiseWidth', 'icons/zoom-full-1d', 'Maximise Width', True, self._resetXZooms),

            ('storeZoom', 'icons/zoom-store', 'Store Zoom (ZS)', True, self._storeZoom),
            ('restoreZoom', 'icons/zoom-restore', 'Restore Zoom (ZR)', True, self._restoreZoom),
            ('undoZoom', 'icons/zoom-undo', 'Previous Zoom (ZP)', True, self._previousZoom),
            ('redoZoom', 'icons/zoom-redo', 'Next Zoom (ZN)', True, self._nextZoom),
            # ('addStrip', 'icons/plus', 'Duplicate the rightmost strip', True, self.addStrip),
            # ('removeStrip', 'icons/minus', 'Remove the current strip', True, self.removeCurrentStrip),
            ]

        # create the actions from the lists
        for aName, icon, tooltip, active, callback in toolBarItemsFor1d:
            action = tb.addAction(tooltip, callback)
            if icon is not None:
                ic = Icon(icon)
                action.setIcon(ic)
            self._spectrumUtilActions[aName] = action

    def processSpectra(self, pids: Sequence[str], event):
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

    def raiseContourBase(self):
        """
        Increases contour base level for all spectra visible in the display.
        """
        # Currently not implemented
        pass

    def lowerContourBase(self):
        """
        Decreases contour base level for all spectra visible in the display.
        """
        # Currently not implemented
        pass

    def setVisibleAxes(self):
        # skip for 1D for the minute
        pass

    def _highlightAxes(self, strip, state):
        """Highlight the last row axis if strip
        """
        pass

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
