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
__dateModified__ = "$dateModified: 2020-10-23 18:39:17 +0100 (Fri, October 23, 2020) $"
__version__ = "$Revision: 3.0.1 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Geerten/CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

import typing

from ccpn.core.Peak import Peak
from ccpn.core.Project import Project
from ccpn.ui.gui.lib import GuiPeakListView
from ccpn.ui.gui.lib.GuiSpectrumDisplay import GuiSpectrumDisplay
from ccpn.ui.gui.widgets.Icon import Icon
from ccpnmodel.ccpncore.api.ccpnmr.gui.Task import BoundDisplay as ApiBoundDisplay
from ccpn.ui.gui.popups.SpectrumPropertiesPopup import SpectrumDisplayPropertiesPopupNd
from ccpn.core.lib.ContextManagers import undoBlockWithoutSideBar

from ccpn.util.decorators import logCommand

from ccpn.util.Logging import getLogger


class SpectrumDisplayNd(GuiSpectrumDisplay):

    MAXPEAKLABELTYPES = 6
    MAXPEAKSYMBOLTYPES = 4

    def __init__(self, mainWindow, name):
        """
        spectrum display object for Nd spectra

        :param mainWindow: MainWindow instance
        :param name: Title-bar name for the Module

        This module inherits attributes from the SpectralDisplay wrapper class (see GuiSpectrumDislay)
        """

        # below are so we can reuse PeakItems and only create them as needed
        self.activePeakItemDict = {}  # maps peakListView to apiPeak to peakItem for peaks which are being displayed
        # cannot use (wrapper) peak as key because project._data2Obj dict invalidates mapping before deleted callback is called
        # TBD: this might change so that we can use wrapper peak (which would make nicer code in showPeaks and deletedPeak below)
        ###self.inactivePeakItems = set() # contains unused peakItems
        self.inactivePeakItemDict = {}  # maps peakListView to apiPeak to set of peaks which are not being displayed

        GuiSpectrumDisplay.__init__(self, mainWindow=mainWindow, name=name, useScrollArea=True)
        # .mainWindow, .current and .application are set by GuiSpectrumDisplay
        # .project is set by the wrapper

        # self.isGrouped = False

        #TODO: have SpectrumToolbar own and maintain this
        self.spectrumActionDict = {}  # apiDataSource --> toolbar action (i.e. button); used in SpectrumToolBar

        # store the list of ordered spectrumViews
        self._orderedSpectrumViews = None

        self._fillToolBar()
        #self.setAcceptDrops(True)

    def _fillToolBar(self):
        """
        Adds specific icons for Nd spectra to the spectrum utility toolbar.
        """
        tb = self.spectrumUtilToolBar
        self._spectrumUtilActions = {}

        toolBarItemsForNd = [
            #  action name,        icon,                  tooltip,                                     active, callback

            ('raiseBase', 'icons/contour-base-up', 'Raise Contour Base Level (Shift + Mouse Wheel)', True, self.raiseContourBase),
            ('lowerBase', 'icons/contour-base-down', 'Lower Contour Base Level (Shift + Mouse Wheel)', True, self.lowerContourBase),
            ('increaseTraceScale', 'icons/tracescale-up', 'Increase scale of 1D traces in display (TU)', True, self.increaseTraceScale),
            ('decreaseTraceScale', 'icons/tracescale-down', 'Decrease scale of 1D traces in display (TD)', True, self.decreaseTraceScale),
            ('addStrip', 'icons/plus', 'Duplicate the rightmost strip', True, self.addStrip),
            ('removeStrip', 'icons/minus', 'Remove the current strip', True, self.removeCurrentStrip),
            ('increaseStripWidth', 'icons/range-expand', 'Increase the width of strips in display', True, self.increaseStripSize),
            ('decreaseStripWidth', 'icons/range-contract', 'Decrease the width of strips in display', True, self.decreaseStripSize),
            ('maximiseZoom', 'icons/zoom-full', 'Maximise Zoom (ZA)', True, self._resetAllZooms),
            ('storeZoom', 'icons/zoom-store', 'Store Zoom (ZS)', True, self._storeZoom),
            ('restoreZoom', 'icons/zoom-restore', 'Restore Zoom (ZR)', True, self._restoreZoom),
            ('undoZoom', 'icons/zoom-undo', 'Previous Zoom (ZP)', True, self._previousZoom),
            ('redoZoom', 'icons/zoom-redo', 'Next Zoom (ZN)', True, self._nextZoom),
            ]

        # create the actions from the lists
        for aName, icon, tooltip, active, callback in toolBarItemsForNd:
            action = tb.addAction(tooltip, callback)
            if icon is not None:
                ic = Icon(icon)
                action.setIcon(ic)
            self._spectrumUtilActions[aName] = action

    def _rebuildContours(self):
        from ccpn.ui.gui.lib.OpenGL.CcpnOpenGL import GLNotifier

        GLSignals = GLNotifier(parent=self)

        for specViews in self.spectrumViews:
            specViews.buildContoursOnly = True

        # repaint
        GLSignals.emitPaintEvent()

    def raiseContourBase(self):
        """
        Increases contour base level for all spectra visible in the display.
        """
        modifiedSpectra = set()
        with undoBlockWithoutSideBar():
            for spectrumView in self.spectrumViews:
                if spectrumView.isVisible():
                    spectrum = spectrumView.spectrum

                    # only increase once - duh
                    if spectrum in modifiedSpectra:
                        continue

                    modifiedSpectra.add(spectrum)

                    if spectrum.positiveContourBase == spectrumView.positiveContourBase:
                        # We want to set the base for ALL spectra
                        # and to ensure that any private settings are overridden for this display
                        # setting to None forces the spectrumVIew to access the spectrum attributes
                        spectrumView.positiveContourBase = None
                        spectrumView.positiveContourFactor = None
                        spectrum.positiveContourBase *= spectrum.positiveContourFactor
                    else:
                        # Display has custom contour base - change that one only
                        spectrumView.positiveContourBase *= spectrumView.positiveContourFactor

                    if spectrum.negativeContourBase == spectrumView.negativeContourBase:
                        # We want to set the base for ALL spectra
                        # and to ensure that any private settings are overridden for this display
                        spectrumView.negativeContourBase = None
                        spectrumView.negativeContourFactor = None
                        spectrum.negativeContourBase *= spectrum.negativeContourFactor
                    else:
                        # Display has custom contour base - change that one only
                        spectrumView.negativeContourBase *= spectrumView.negativeContourFactor

                    # spectrumView.rebuildContours()
                    # spectrumView.update()

                    mainWindow = self.mainWindow
                    mainWindow.pythonConsole.writeConsoleCommand(
                            "spectrum.positiveContourBase = %s" % spectrum.positiveContourBase, spectrum=spectrum)
                    mainWindow.pythonConsole.writeConsoleCommand(
                            "spectrum.negativeContourBase = %s" % spectrum.negativeContourBase, spectrum=spectrum)
                    getLogger().info("spectrum = project.getByPid(%s)" % spectrum.pid)
                    getLogger().info("spectrum.positiveContourBase = %s" % spectrum.positiveContourBase)
                    getLogger().info("spectrum.negativeContourBase = %s" % spectrum.negativeContourBase)

            # self._rebuildContours()

    def lowerContourBase(self):
        """
        Decreases contour base level for all spectra visible in the display.
        """
        modifiedSpectra = set()
        with undoBlockWithoutSideBar():
            for spectrumView in self.spectrumViews:
                if spectrumView.isVisible():
                    spectrum = spectrumView.spectrum

                    # only increase once - duh
                    if spectrum in modifiedSpectra:
                        continue

                    modifiedSpectra.add(spectrum)

                    if spectrum.positiveContourBase == spectrumView.positiveContourBase:
                        # We want to set the base for ALL spectra
                        # and to ensure that any private settings are overridden for this display
                        spectrumView.positiveContourBase = None
                        spectrumView.positiveContourFactor = None
                        spectrum.positiveContourBase /= spectrum.positiveContourFactor
                    else:
                        # Display has custom contour base - change that one only
                        spectrumView.positiveContourBase /= spectrumView.positiveContourFactor

                    if spectrum.negativeContourBase == spectrumView.negativeContourBase:
                        # We want to set the base for ALL spectra
                        # and to ensure that any private settings are overridden for this display
                        spectrumView.negativeContourBase = None
                        spectrumView.negativeContourFactor = None
                        spectrum.negativeContourBase /= spectrum.negativeContourFactor
                    else:
                        # Display has custom contour base - change that one only
                        spectrumView.negativeContourBase /= spectrumView.negativeContourFactor

                    # spectrumView.rebuildContours()
                    # spectrumView.update()

                    mainWindow = self.mainWindow
                    mainWindow.pythonConsole.writeConsoleCommand(
                            "spectrum.positiveContourBase = %s" % spectrum.positiveContourBase, spectrum=spectrum)
                    mainWindow.pythonConsole.writeConsoleCommand(
                            "spectrum.negativeContourBase = %s" % spectrum.negativeContourBase, spectrum=spectrum)
                    getLogger().info("spectrum = project.getByPid(%s)" % spectrum.pid)
                    getLogger().info("spectrum.positiveContourBase = %s" % spectrum.positiveContourBase)
                    getLogger().info("spectrum.negativeContourBase = %s" % spectrum.negativeContourBase)

            # self._rebuildContours()

    def addContourLevel(self):
        """
        Increases number of contours by 1 for all spectra visible in the display.
        """
        modifiedSpectra = set()
        with undoBlockWithoutSideBar():
            for spectrumView in self.spectrumViews:
                if spectrumView.isVisible():
                    spectrum = spectrumView.spectrum

                    # only increase once - duh
                    if spectrum in modifiedSpectra:
                        continue

                    modifiedSpectra.add(spectrum)

                    if spectrum.positiveContourCount == spectrumView.positiveContourCount:
                        # We want to set the base for ALL spectra
                        # and to ensure that any private settings are overridden for this display
                        spectrumView.positiveContourCount = None
                        spectrum.positiveContourCount += 1
                    else:
                        # Display has custom contour count - change that one only
                        spectrumView.positiveContourCount += 1

                    if spectrum.negativeContourCount == spectrumView.negativeContourCount:
                        # We want to set the base for ALL spectra
                        # and to ensure that any private settings are overridden for this display
                        spectrumView.negativeContourCount = None
                        spectrum.negativeContourCount += 1
                    else:
                        # Display has custom contour count - change that one only
                        spectrumView.negativeContourCount += 1

                    # spectrumView.rebuildContours()
                    # spectrumView.update()

                    mainWindow = self.mainWindow
                    mainWindow.pythonConsole.writeConsoleCommand(
                            "spectrum.positiveContourCount = %s" % spectrum.positiveContourCount, spectrum=spectrum)
                    mainWindow.pythonConsole.writeConsoleCommand(
                            "spectrum.negativeContourCount = %s" % spectrum.negativeContourCount, spectrum=spectrum)
                    getLogger().info("spectrum = project.getByPid(%s)" % spectrum.pid)
                    getLogger().info("spectrum.positiveContourCount = %s" % spectrum.positiveContourCount)
                    getLogger().info("spectrum.negativeContourCount = %s" % spectrum.negativeContourCount)

            # self._rebuildContours()

    def removeContourLevel(self):
        """
        Decreases number of contours by 1 for all spectra visible in the display.
        """
        modifiedSpectra = set()
        with undoBlockWithoutSideBar():
            for spectrumView in self.spectrumViews:
                if spectrumView.isVisible():
                    spectrum = spectrumView.spectrum

                    # only increase once - duh
                    if spectrum in modifiedSpectra:
                        continue

                    modifiedSpectra.add(spectrum)

                    if spectrum.positiveContourCount == spectrumView.positiveContourCount:
                        # We want to set the base for ALL spectra
                        # and to ensure that any private settings are overridden for this display
                        spectrumView.positiveContourCount = None
                        if spectrum.positiveContourCount:
                            spectrum.positiveContourCount -= 1
                    else:
                        # Display has custom contour count - change that one only
                        if spectrumView.positiveContourCount:
                            spectrumView.positiveContourCount -= 1

                    if spectrum.negativeContourCount == spectrumView.negativeContourCount:
                        # We want to set the base for ALL spectra
                        # and to ensure that any private settings are overridden for this display
                        spectrumView.negativeContourCount = None
                        if spectrum.negativeContourCount:
                            spectrum.negativeContourCount -= 1
                    else:
                        # Display has custom contour count - change that one only
                        if spectrumView.negativeContourCount:
                            spectrumView.negativeContourCount -= 1

                    # spectrumView.rebuildContours()
                    # spectrumView.update()

                    mainWindow = self.mainWindow
                    mainWindow.pythonConsole.writeConsoleCommand(
                            "spectrum.positiveContourCount = %s" % spectrum.positiveContourCount, spectrum=spectrum)
                    mainWindow.pythonConsole.writeConsoleCommand(
                            "spectrum.negativeContourCount = %s" % spectrum.negativeContourCount, spectrum=spectrum)
                    getLogger().info("spectrum = project.getByPid(%s)" % spectrum.pid)
                    getLogger().info("spectrum.positiveContourCount = %s" % spectrum.positiveContourCount)
                    getLogger().info("spectrum.negativeContourCount = %s" % spectrum.negativeContourCount)
                # mainWindow = self.mainWindow
                # mainWindow.pythonConsole.writeConsoleCommand(
                #         "spectrum.positiveContourCount = %s" % spectrum.positiveContourCount, spectrum=spectrum)
                # mainWindow.pythonConsole.writeConsoleCommand(
                #         "spectrum.negativeContourCount = %s" % spectrum.negativeContourCount, spectrum=spectrum)
                # getLogger().info("spectrum = project.getByPid(%s)" % spectrum.pid)
                # getLogger().info("spectrum.positiveContourCount = %s" % spectrum.positiveContourCount)
                # getLogger().info("spectrum.negativeContourCount = %s" % spectrum.negativeContourCount)

            # self._rebuildContours()

    def updateTraces(self):
        for strip in self.strips:
            strip._updateTraces()

    def adjustContours(self):
        # insert popup to modify contours
        popup = SpectrumDisplayPropertiesPopupNd(parent=self.mainWindow, mainWindow=self.mainWindow,
                                                 orderedSpectrumViews=self.orderedSpectrumViews(self.spectrumViews))
        popup.exec_()

    # def showPeaks(self, peakListView: GuiPeakListView.GuiPeakListView, peaks: typing.List[Peak]):
    #     """
    #     Displays specified peaks in all strips of the display using peakListView
    #     """
    #
    #     # viewBox = peakListView.spectrumView.strip.viewBox
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
    #             peakItem = GuiPeakListView.PeakNd(peakListView, peak)
    #         peakItemDict[apiPeak] = peakItem


# Functions for notifiers

# We are not currently using Free strips
#
# # Could be changed to wrapper level, but would be triggered much more often. Leave  as is.
# def _changedFreeStripAxisOrdering(project:Project, apiStrip:ApiFreeStrip):
#   """Used (and works) for either BoundDisplay of FreeStrip"""
#   project._data2Obj[apiStrip]._setZWidgets()

def _changedBoundDisplayAxisOrdering(project: Project, apiDisplay: ApiBoundDisplay):
    """Used (and works) for either BoundDisplay of FreeStrip"""
    for strip in project._data2Obj[apiDisplay].strips:
        strip._setZWidgets()
