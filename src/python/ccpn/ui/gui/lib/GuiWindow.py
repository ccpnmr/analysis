"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (https://www.ccpn.ac.uk) 2014 - 2022"
__credits__ = ("Ed Brooksbank, Joanna Fox, Victoria A Higman, Luca Mureddu, Eliza Płoskoń",
               "Timothy J Ragan, Brian O Smith, Gary S Thompson & Geerten W Vuister")
__licence__ = ("CCPN licence. See https://ccpn.ac.uk/software/licensing/")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, https://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2022-11-08 12:11:28 +0000 (Tue, November 08, 2022) $"
__version__ = "$Revision: 3.1.0 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from PyQt5 import QtCore
from functools import partial
from ccpn.core.lib import AssignmentLib
from ccpn.core.lib.peakUtils import estimateVolumes, updateHeight
from ccpn.core.lib.ContextManagers import undoBlockWithoutSideBar, notificationEchoBlocking
from ccpn.ui.gui import guiSettings
from ccpn.ui.gui.widgets.MessageDialog import showWarning, progressManager
from ccpn.ui.gui.popups.ShortcutsPopup import UserShortcuts
from ccpn.ui.gui.lib.SpectrumDisplay import navigateToCurrentPeakPosition, navigateToCurrentNmrResiduePosition
from ccpn.ui.gui.lib.Shortcuts import addShortCut
from ccpn.ui.gui.lib.mouseEvents import MouseModes, setCurrentMouseMode, getCurrentMouseMode, PICK
from ccpn.util.decorators import logCommand
from ccpn.util.Colour import colorSchemeTable
from ccpn.util.Logging import getLogger


_PEAKS = 1
_INTEGRALS = 2
_MULTIPLETS = 4
_INTEGRAL_PEAKS = 8
_MULTIPLET_PEAKS = 16


class GuiWindow():

    def __init__(self, application):
        self.application = application
        self.current = self.application.current

        self.pythonConsoleModule = None  # Python console module; defined upon first time Class initialisation. Either by toggleConsole or Restoring layouts

    def _setShortcuts(self):
        """
        Sets shortcuts for functions not specified in the main window menubar
        """
        # TODO:ED test that the shortcuts can be added to the modules
        # return

        context = QtCore.Qt.WidgetWithChildrenShortcut
        # addShortCut("c, h", self, self.toggleCrosshairAll, context=context)
        addShortCut("e, n", self, self.estimateNoise, context=context)
        addShortCut("g, s", self, self.toggleGridAll, context=context)
        addShortCut("Del", self, partial(self.deleteSelectedItems), context=context)
        addShortCut("Backspace", self, partial(self.deleteSelectedItems), context=context)
        addShortCut("m, k", self, self.createMark, context=context)
        addShortCut("m, c", self, self.clearMarks, context=context)
        addShortCut("m, x", self, partial(self.createMark, 0), context=context)
        addShortCut("m, y", self, partial(self.createMark, 1), context=context)
        addShortCut("m, z", self, partial(self.createMark, 2), context=context)
        addShortCut("m, w", self, partial(self.createMark, 3), context=context)
        addShortCut("p, m", self, self.createPeakAxisMarks, context=context)
        addShortCut("p, x", self, partial(self.createPeakAxisMarks, 0), context=context)
        addShortCut("p, y", self, partial(self.createPeakAxisMarks, 1), context=context)
        addShortCut("p, z", self, partial(self.createPeakAxisMarks, 2), context=context)
        addShortCut("p, w", self, partial(self.createPeakAxisMarks, 3), context=context)
        addShortCut("u, m", self, self.createMultipletAxisMarks, context=context)
        addShortCut("u, x", self, partial(self.createMultipletAxisMarks, 0), context=context)
        addShortCut("u, y", self, partial(self.createMultipletAxisMarks, 1), context=context)
        addShortCut("u, z", self, partial(self.createMultipletAxisMarks, 2), context=context)
        addShortCut("u, w", self, partial(self.createMultipletAxisMarks, 3), context=context)
        addShortCut("f, n", self, partial(navigateToCurrentNmrResiduePosition, self.application), context=context)
        addShortCut("f, p", self, partial(navigateToCurrentPeakPosition, self.application), context=context)
        addShortCut("c, a", self, partial(AssignmentLib.propagateAssignments, current=self.application.current), context=context)
        addShortCut("c, z", self, self._clearCurrentPeaks, context=context)
        addShortCut("c, o", self, self.setContourLevels, context=context)

        addShortCut("f, t", self, self.filterOnCurrentTable, context=context)
        addShortCut("t, u", self, partial(self.traceScaleUp, self), context=context)
        addShortCut("t, d", self, partial(self.traceScaleDown, self), context=context)
        addShortCut("t, h", self, partial(self.toggleHTrace, self), context=context)
        addShortCut("t, v", self, partial(self.toggleVTrace, self), context=context)
        addShortCut("t, a", self, self.newPhasingTrace, context=context)
        addShortCut("t, r", self, self.removePhasingTraces, context=context)
        addShortCut("p, v", self, self.setPhasingPivot, context=context)

        addShortCut("s, k", self, self.stackSpectra, context=context)
        addShortCut("l, a", self, partial(self.toggleLastAxisOnly, self), context=context)

        addShortCut("a, m", self, self.addMultiplet, context=context)
        addShortCut("c, c", self, self.newCollectionOfCurrentPeaks, context=context)
        addShortCut("i, 1", self, self.add1DIntegral, context=context)
        addShortCut("g, p", self, self.getCurrentPositionAndStrip, context=context)
        addShortCut("r, p", self, partial(self.refitCurrentPeaks, singularMode=True), context=context)
        addShortCut("r, g", self, partial(self.refitCurrentPeaks, singularMode=False), context=context)
        addShortCut("r, h", self, self.recalculateCurrentPeakHeights, context=context)
        addShortCut("Tab,Tab", self, self.moveToNextSpectrum, context=context)
        addShortCut("Tab, q", self, self.moveToPreviousSpectrum, context=context)
        addShortCut("Tab, a", self, self.showAllSpectra, context=context)
        addShortCut("Tab, z", self, self.hideAllSpectra, context=context)
        addShortCut("Tab, x", self, self.invertSelectedSpectra, context=context)
        addShortCut("m, m", self, self.switchMouseMode, context=context)
        addShortCut("s, e", self, self.snapCurrentPeaksToExtremum, context=context)

        addShortCut("z, s", self, self.storeZoom, context=context)
        addShortCut("z, r", self, self.restoreZoom, context=context)
        addShortCut("z, p", self, self.previousZoom, context=context)
        addShortCut("z, n", self, self.nextZoom, context=context)
        addShortCut("z, i", self, self.zoomIn, context=context)
        addShortCut("z, o", self, self.zoomOut, context=context)
        addShortCut("=", self, self.zoomIn, context=context)  # overrides openGL _panSpectrum
        addShortCut("+", self, self.zoomIn, context=context)
        addShortCut("-", self, self.zoomOut, context=context)

        # THESE REMOVE CONTROL FROM TABLES

        # addShortCut("Up", self, partial(self.panSpectrum, 'up'), context=context)
        # addShortCut("Down", self, partial(self.panSpectrum, 'down'), context=context)
        # addShortCut("Left", self, partial(self.panSpectrum, 'left'), context=context)
        # addShortCut("Right", self, partial(self.panSpectrum, 'right'), context=context)

        # addShortCut("Shift+Up", self, partial(self.movePeaks, 'up'), context=context)
        # addShortCut("Shift+Down", self, partial(self.movePeaks, 'down'), context=context)
        # addShortCut("Shift+Left", self, partial(self.movePeaks, 'left'), context=context)
        # addShortCut("Shift+Right", self, partial(self.movePeaks, 'right'), context=context)

        addShortCut("z, a", self, self.resetAllZoom, context=context)

        addShortCut("p, l", self, self.cycleSymbolLabelling, context=context)
        addShortCut("p, s", self, self.cyclePeakSymbols, context=context)
        # addShortCut("Space, Space", self, self.toggleConsole, context=context) # this is not needed here, already set on Menus!!
        # addShortCut("CTRL+a", self, self.selectAllPeaks, context=context)

        addShortCut("q, q", self, self._lowerContourBaseCallback, context=context)
        addShortCut("w, w", self, self._raiseContourBaseCallback, context=context)
        addShortCut("j, j", self, self.previousZPlane, context=context)
        addShortCut("k, k", self, self.nextZPlane, context=context)

    #     addShortCut("q, w, p, l", self, self.testLongShortcut, context=context)
    #
    # def testLongShortcut(self):
    #     print('>>>long')

    def _setUserShortcuts(self, preferences=None, mainWindow=None):

        # TODO:ED fix this circular link
        self.application._userShortcuts = UserShortcuts(mainWindow=mainWindow)  # set a new set of shortcuts

        context = QtCore.Qt.ApplicationShortcut
        userShortcuts = preferences.shortcuts
        for shortcut, function in userShortcuts.items():

            try:
                self.application._userShortcuts.addUserShortcut(shortcut, function)

                addShortCut("%s, %s" % (shortcut[0], shortcut[1]), self,
                            partial(UserShortcuts.runUserShortcut, self.application._userShortcuts, shortcut),
                            context)

            except:
                getLogger().warning('Error setting user shortcuts function')

            # if function.split('(')[0] == 'runMacro':
            #   QtWidgets.QShortcut(QtGui.QKeySequence("%s, %s" % (shortcut[0], shortcut[1])),
            #             self, partial(self.namespace['runMacro'], function.split('(')[1].split(')')[0]), context=context)
            #
            # else:
            #   stub = self.namespace.get(function.split('.')[0])
            #   try:
            #     QtWidgets.QShortcut(QtGui.QKeySequence("%s, %s" % (shortcut[0], shortcut[1])), self,
            #                     reduce(getattr, function.split('.')[1:], stub), context=context)
            #   except:
            #     getLogger().warning('Function cannot be found')

    def deassignPeaks(self):
        """Deassign all from selected peaks
        """
        if self.current.peaks:
            with undoBlockWithoutSideBar():
                for peak in self.current.peaks:
                    assignedDims = list(peak.dimensionNmrAtoms)
                    assignedDims = tuple([] for dd in assignedDims)
                    peak.dimensionNmrAtoms = assignedDims

    def deleteSelectedItems(self, parent=None):
        """Delete peaks/integrals/multiplets from the project
        """
        # show simple delete items popup
        from ccpn.ui.gui.popups.DeleteItems import DeleteItemsPopup

        foundSets = 0
        if self.current.peaks or self.current.multiplets or self.current.integrals:
            deleteItems = []
            if self.current.peaks:
                deleteItems.append(('Peaks', self.current.peaks, True))
                foundSets += _PEAKS
            if self.current.integrals:
                deleteItems.append(('Integrals', self.current.integrals, True))
                foundSets += _INTEGRALS
            if self.current.multiplets:
                deleteItems.append(('Multiplets', self.current.multiplets, True))
                foundSets += _MULTIPLETS

            # add integrals attached peaks
            attachedIntegrals = set()
            for peak in self.current.peaks:
                if peak.integral:
                    attachedIntegrals.add(peak.integral)
            attachedIntegrals = list(attachedIntegrals - set(self.current.integrals))

            if attachedIntegrals:
                deleteItems.append(('Additional Peak-Integrals', attachedIntegrals, False))
                foundSets += _INTEGRAL_PEAKS

            # add peaks attached multiplets
            attachedPeaks = set()
            for multiplet in self.current.multiplets:
                for peak in multiplet.peaks:
                    attachedPeaks.add(peak)
            attachedPeaks = list(attachedPeaks - set(self.current.peaks))

            if attachedPeaks:
                deleteItems.append(('Additional Multiplet-Peaks', attachedPeaks, False))
                foundSets += _MULTIPLET_PEAKS

            if foundSets & (_INTEGRAL_PEAKS | _MULTIPLET_PEAKS):
                # if there are additional peaks that have been missed then show popup - add more conditions?
                popup = DeleteItemsPopup(parent=self, mainWindow=self, items=deleteItems)
                popup.exec()

            else:
                # don't show the popup
                self.project.deleteObjects(*(obj for _name, itms, _check in deleteItems for obj in itms))

    # def deleteSelectedPeaks(self, parent=None):
    #
    #   # NBNB Moved here from Current
    #   # NBNB TODO: more general deletion
    #
    #   current = self.application.current
    #   peaks = current.peaks
    #   if peaks:
    #     n = len(peaks)
    #     title = 'Delete Peak%s' % ('' if n == 1 else 's')
    #     msg ='Delete %sselected peak%s?' % ('' if n == 1 else '%d ' % n, '' if n == 1 else 's')
    #     if MessageDialog.showYesNo(title, msg, parent):
    #       current.project.deleteObjects(*peaks)
    #
    # def deleteSelectedMultiplets(self, parent=None):
    #   current = self.application.current
    #   multiplets = current.multiplets
    #   if multiplets:
    #     n = len(multiplets)
    #     title = 'Delete Multiplet%s' % ('' if n == 1 else 's')
    #     msg ='Delete %sselected multiplet%s?' % ('' if n == 1 else '%d ' % n, '' if n == 1 else 's')
    #     if MessageDialog.showYesNo(title, msg, parent):
    #       current.project.deleteObjects(*multiplets)

    def _openCopySelectedPeaks(self):
        from ccpn.ui.gui.popups.CopyPeaksPopup import CopyPeaks

        popup = CopyPeaks(parent=self, mainWindow=self)
        peaks = self.current.peaks
        popup._selectPeaks(peaks)
        popup.exec_()

    def setPeakAliasing(self):
        """Set the aliasing for the currently selected peaks
        """
        if self.current.peaks:
            from ccpn.ui.gui.popups.SetPeakAliasing import SetPeakAliasingPopup

            popup = SetPeakAliasingPopup(parent=self, mainWindow=self, peaks=self.current.peaks)
            popup.exec_()

    def calibrateFromPeaks(self):
        """Calibrate the current strip from the selected peaks
        """
        if self.current.strip:
            self.current.strip.calibrateFromPeaks()

    def getCurrentPositionAndStrip(self):
        current = self.application.current
        # """
        # # this function is called as a shortcut macro ("w1") but
        # # with the code commented out that is pretty pointless.
        # # current.strip and current.cursorPosition are now set by
        # # clicking on a position in the strip so this commented
        # # out code is no longer useful, and this function might
        # # be more generally useful, so leave the brief version
        # current.strip = current.viewBox.parentObject().parent
        # cursorPosition = (current.viewBox.position.x(),
        #                   current.viewBox.position.y())
        # # if len(current.strip.axisOrder) > 2:
        # #   for axis in current.strip.orderedAxes[2:]:
        # #     position.append(axis.position)
        # # current.position = tuple(position)
        # current.cursorPosition = cursorPosition
        # """
        return current.strip, current.cursorPosition

    def _getPeaksParams(self, peaks):
        params = []
        for peak in peaks:
            params.append((peak.height, peak.position, peak.lineWidths))
        return params

    def _setPeaksParams(self, peaks, params):
        for n, peak in enumerate(peaks):
            height, position, lineWidths = params[n]
            peak.height = height
            peak.position = position
            peak.lineWidths = lineWidths

    def add1DIntegral(self, peak=None):
        """Peak: take self.application.currentPeak as default
        """

        from ccpn.core.lib.ContextManagers import undoBlock, notificationEchoBlocking, undoBlockWithoutSideBar

        with undoBlockWithoutSideBar():
            with notificationEchoBlocking():
                strip = self.application.current.strip
                peak = self.project.getByPid(peak) if isinstance(peak, str) else peak

                if strip is not None:
                    if strip.spectrumDisplay.is1D:
                        cursorPosition = self.application.current.cursorPosition
                        if cursorPosition is not None and len(cursorPosition) > 1:
                            limits = [cursorPosition[0], cursorPosition[0] + 0.01]

                            validViews = [sv for sv in strip.spectrumViews if sv.isDisplayed]
                            currentIntegrals = list(self.current.integrals)
                            for spectrumView in validViews:

                                if not spectrumView.spectrum.integralLists:
                                    spectrumView.spectrum.newIntegralList()

                                # stupid bug! mixing views and lists
                                validIntegralLists = [ilv.integralList for ilv in spectrumView.integralListViews if ilv.isDisplayed]

                                for integralList in validIntegralLists:

                                    # set the limits of the integral with a default baseline of 0.0
                                    integral = integralList.newIntegral(value=None, limits=[limits, ])
                                    integral.baseline = 0.0
                                    currentIntegrals.append(integral)
                                    if peak:
                                        integral.peak = peak
                                    else:
                                        if len(self.application.current.peaks) == 1:
                                            if self.application.current.peak.peakList.spectrum == integral.integralList.spectrum:
                                                integral.peak = self.application.current.peak
                            self.current.integrals = currentIntegrals

                else:
                    getLogger().warning('Current strip is not 1D')

    @logCommand('mainWindow.')
    def refitCurrentPeaks(self, singularMode=True):
        peaks = self.application.current.peaks
        if not peaks:
            return

        fitMethod = self.application.preferences.general.peakFittingMethod
        with undoBlockWithoutSideBar():
            AssignmentLib.refitPeaks(peaks, fitMethod=fitMethod, singularMode=singularMode)

    def recalculateCurrentPeakHeights(self):
        """
        Recalculates the peak height without changing the ppm position
        """
        getLogger().info('Recalculating peak height(s).')

        current = self.application.current
        peaks = current.peaks

        with undoBlockWithoutSideBar():
            with notificationEchoBlocking():
                list(map(lambda x: updateHeight(x), peaks))

        getLogger().info('Recalculating peak height(s) completed.')

    def estimateVolumes(self):
        """Estimate volumes of peaks selected by right-mouse menu
        If clicking on a selected peak then apply to all selected, otherwise apply to clicked peaks
        """
        current = self.application.current
        peaks = current.peaks
        clickedPeaks = current.strip._lastClickedObjects if current.strip else None

        # return if both the lists are empty
        if not (peaks or clickedPeaks):
            return

        with undoBlockWithoutSideBar():
            if (set(peaks or []) & set(clickedPeaks or [])):
                # if any of clickedPeaks are in current.peaks then apply to all selected
                estimateVolumes(peaks)
            else:
                estimateVolumes(clickedPeaks)

        # project = peaks[0].project
        # undo = project._undo
        #
        # project.newUndoPoint()
        # undo.increaseBlocking()
        #
        # currentParams = self._getPeaksParams(peaks)
        # try:
        #     AssignmentLib.refitPeaks(peaks)
        # finally:
        #     undo.decreaseBlocking()
        #     undo.newItem(self._setPeaksParams, self._setPeaksParams, undoArgs=[peaks, currentParams],
        #                  redoArgs=[peaks, self._getPeaksParams(peaks)])

    def reorderPeakListAxes(self):
        """Reorder axes of all peaks in peakList of first selected peak by right-mouse menu
        """
        current = self.application.current
        peaks = current.peaks
        clickedPeaks = current.strip._lastClickedObjects if current.strip else None

        # return if both the lists are empty
        if not (peaks or clickedPeaks):
            return

        with undoBlockWithoutSideBar():
            if set(clickedPeaks or []):
                from ccpn.ui.gui.popups.ReorderPeakListAxes import ReorderPeakListAxes as ReorderPeakListAxesPopup

                popup = ReorderPeakListAxesPopup(parent=self, mainWindow=self, peakList=clickedPeaks[0].peakList)
                popup.exec_()

    def selectAllPeaks(self, strip=None):
        """selects all peaks in the strip or current strip if any and if the spectrum is toggled on"""
        if strip is None:
            if self.application.current.strip:
                strip = self.application.current.strip
        if strip and not strip.isDeleted:
            spectra = [spectrumView.spectrum for spectrumView in strip.spectrumViews
                       if spectrumView.isDisplayed]
            listOfPeaks = [peakList.peaks for spectrum in spectra for peakList in spectrum.peakLists]

            self.application.current.peaks = [peak for peaks in listOfPeaks for peak in peaks]

    def addMultiplet(self):
        """add current peaks to a new multiplet"""
        strip = self.application.current.strip

        with undoBlockWithoutSideBar():
            if strip and strip.spectrumDisplay:
                spectra = [spectrumView.spectrum for spectrumView in
                           strip.spectrumViews if spectrumView.isDisplayed]
                for spectrum in spectra:
                    if len(spectrum.multipletLists) < 1:
                        multipletList = spectrum.newMultipletList()
                    else:
                        multipletList = spectrum.multipletLists[-1]
                    peaks = [peak for peakList in spectrum.peakLists for peak in peakList.peaks if
                             peak in self.application.current.peaks]
                    multiplet = multipletList.newMultiplet(peaks=peaks)
                    self.application.current.multiplet = multiplet

    def newCollectionOfCurrentPeaks(self):
        """add current peaks to a new collection"""
        from ccpn.util.Common import flattenLists
        from ccpn.core.lib.PeakCollectionLib import _getCollectionNameForAssignments, _getCollectionNameFromPeakPosition
        strip = self.application.current.strip
        with undoBlockWithoutSideBar():
            if strip and strip.spectrumDisplay:
                spectra = [spectrumView.spectrum for spectrumView in strip.spectrumViews if spectrumView.isDisplayed]
                peaks = [peak for peak in self.application.current.peaks if peak.spectrum in spectra]
                nmrAtoms = set(flattenLists([peak.assignedNmrAtoms for peak in peaks]))
                name = _getCollectionNameForAssignments(list(nmrAtoms)) # get a name from assigned peaks
                if not name:
                    name = _getCollectionNameFromPeakPosition(peaks[0]) # alternatively get a name from ppm position
                # we need to check if ordering is crucial here. For series is taking care by the SG where peaks belong.
                collection = self.application.project.newCollection(items=list(set(peaks)), name=name)
                self.application.current.collection = collection

    def traceScaleScale(self, window: 'GuiWindow', scale: float):
        """
        Changes the scale of a trace in all spectrum displays of the window.
        """
        # for spectrumDisplay in window.spectrumDisplays:

        if self.application.current.strip:
            spectrumDisplay = self.application.current.strip.spectrumDisplay

            if not spectrumDisplay.is1D:
                for strip in spectrumDisplay.strips:
                    _update = False
                    for spectrumView in strip.spectrumViews:
                        if spectrumView.traceScale is not None:
                            # may not have been initialised as no trace
                            spectrumView.traceScale *= scale
                            _update = True

                    if _update:
                        # spawn a redraw of the strip
                        strip._updatePivot()

    def traceScaleUp(self, window: 'GuiWindow', scale=1.4):
        """
        Doubles the scale for all traces in the specified window.
        """
        self.traceScaleScale(window, scale=scale)

    def traceScaleDown(self, window: 'GuiWindow', scale=(1.0 / 1.4)):
        """
        Halves the scale for all traces in the specified window.
        """
        self.traceScaleScale(window, scale=scale)

    def toggleHTrace(self, window: 'GuiWindow'):
        """
        Toggles whether horizontal traces are displayed in the specified window.
        """
        if self.application.current.strip:
            self.application.current.strip.spectrumDisplay.toggleHTrace()

    def toggleVTrace(self, window: 'GuiWindow'):
        """
        Toggles whether vertical traces are displayed in the specified window.
        """
        if self.application.current.strip:
            self.application.current.strip.spectrumDisplay.toggleVTrace()

    def toggleLastAxisOnly(self, window: 'GuiWindow'):
        """
        Toggles whether the axis is displayed in the last strip of the display
        """
        if self.application.current.strip:
            self.application.current.strip.toggleLastAxisOnly()

    def togglePhaseConsole(self, window: 'GuiWindow'):
        """
        Toggles whether the phasing console is displayed in the specified window.
        """
        for spectrumDisplay in window.spectrumDisplays:
            spectrumDisplay.togglePhaseConsole()

    def newPhasingTrace(self):
        strip = self.application.current.strip
        if strip:  # and (strip.spectrumDisplay.window is self):
            strip._newPhasingTrace()

    def stackSpectra(self):
        strip = self.application.current.strip
        if strip:  # and (strip.spectrumDisplay.window is self):
            strip._toggleStackPhaseFromShortCut()

    def setPhasingPivot(self):

        strip = self.application.current.strip
        if strip:  # and (strip.spectrumDisplay.window is self):
            strip._setPhasingPivot()

    def removePhasingTraces(self):
        """
        Removes all phasing traces from all strips.
        """
        strip = self.application.current.strip
        if strip:  # and (strip.spectrumDisplay.window is self):
            # strip.removePhasingTraces()
            for strip in strip.spectrumDisplay.strips:
                strip.removePhasingTraces()

    def _clearCurrentPeaks(self):
        """
        Sets current.peaks to an empty list.
        """
        # self.application.current.peaks = []
        self.application.current.clearPeaks()

    def filterOnCurrentTable(self):
        if hasattr(self.current, 'guiTable'):
            currentGuiTable = self.current.guiTable
            if currentGuiTable is not None:
                currentGuiTable.showSearchSettings()

    def setContourLevels(self):
        """
        Open the contour settings popup for the current strip
        """
        strip = self.application.current.strip
        if strip:
            strip.spectrumDisplay.adjustContours()

    # def toggleCrosshairAll(self):
    #     """
    #     Toggles whether crosshairs are displayed in all windows.
    #     """
    #     for window in self.project.windows:
    #         window.toggleCrosshair()

    def toggleCrosshair(self):
        """
        Toggles whether crosshairs are displayed in all spectrum displays
        """
        # toggle crosshairs for the spectrum displays in this window
        for spectrumDisplay in self.spectrumDisplays:
            spectrumDisplay.toggleCrosshair()

    def estimateNoise(self):
        """estimate the noise in the visible region of the current strip
        """
        strip = self.application.current.strip
        if strip:
            strip.estimateNoise()

    def createMark(self, axisIndex=None):
        """
        Creates a mark at the current cursor position in the current strip.
        """
        strip = self.application.current.strip
        if strip:
            strip._createMarkAtCursorPosition(axisIndex)

    def createPeakAxisMarks(self, axisIndex=None):
        """
        Creates marks at the selected peak positions.
        """
        strip = self.application.current.strip
        if strip:
            strip._markSelectedPeaks(axisIndex)

    def createMultipletAxisMarks(self, axisIndex=None):
        """
        Creates marks at the selected multiplet positions.
        """
        strip = self.application.current.strip
        if strip:
            strip._markSelectedMultiplets(axisIndex)

    @logCommand('mainWindow.')
    def clearMarks(self):
        """
        Clears all marks in all windows for the current task.
        """
        self.project.deleteObjects(*self.project.marks)

    def markPositions(self, axisCodes, chemicalShifts):
        """
        Create marks based on the axisCodes and adds annotations where appropriate.

        :param axisCodes: The axisCodes making a mark for
        :param chemicalShifts: A list or tuple of ChemicalShifts at whose values the marks should be made
        """
        project = self.application.project

        # colourDict = guiSettings.MARK_LINE_COLOUR_DICT  # maps atomName --> colour
        for ii, axisCode in enumerate(axisCodes):
            for chemicalShift in chemicalShifts[ii]:
                atomId = chemicalShift.nmrAtom.id
                atomName = chemicalShift.nmrAtom.name
                # TODO: the below fails, for example, if nmrAtom.name = 'Hn', can that happen?

                # colour = colourDict.get(atomName[:min(2,len(atomName))])
                colourMarks = guiSettings.getColours().get(guiSettings.MARKS_COLOURS)
                # colour = colourMarks[atomName[:min(2,len(atomName))]]
                colour = colourMarks.get(atomName[:min(2, len(atomName))])
                if not colour:
                    colour = colourMarks.get(guiSettings.DEFAULT)

                # exit if mark exists
                found = False
                for mm in project.marks:
                    if atomName in mm.labels and \
                            colour == mm.colour and \
                            abs(chemicalShift.value - mm.positions[0]) < 1e-6:
                        found = True
                        break
                if found:
                    continue

                # with logCommandBlock(get='self') as log:
                #     log('markPositions')
                with undoBlockWithoutSideBar():
                    # GWV 20181030: changed from atomName to id
                    if colour:
                        self.newMark(colour, [chemicalShift.value], [axisCode], labels=[atomId])
                    else:
                        # just use default mark colour rather than checking colourScheme
                        defaultColour = self.application.preferences.general.defaultMarksColour

                        try:
                            _prefsGeneral = self.application.preferences.general
                            defaultColour = _prefsGeneral.defaultMarksColour
                            if not defaultColour.startswith('#'):
                                colourList = colorSchemeTable[defaultColour] if defaultColour in colorSchemeTable else ['#FF0000']
                                _prefsGeneral._defaultMarksCount = _prefsGeneral._defaultMarksCount % len(colourList)
                                defaultColour = colourList[_prefsGeneral._defaultMarksCount]
                                _prefsGeneral._defaultMarksCount += 1
                        except:
                            defaultColour = '#FF0000'

                        try:
                            self.mainWindow.newMark(defaultColour, [chemicalShift.value], [atomId])
                        except Exception as es:
                            getLogger().warning('Error setting mark at position')
                            raise (es)

    def toggleGridAll(self):
        """
        Toggles grid display in all windows
        """
        for window in self.project.windows:
            window.toggleGrid()

    def toggleGrid(self):
        """
        toggle grid for the spectrum displays in this window.
        """
        for spectrumDisplay in self.spectrumDisplays:
            spectrumDisplay.toggleGrid()

    def toggleSideBandsAll(self):
        """
        Toggles sideBand display in all windows
        """
        for window in self.project.windows:
            window.toggleSideBands()

    def toggleSideBands(self):
        """
        toggle sideBands for the spectrum displays in this window.
        """
        for spectrumDisplay in self.spectrumDisplays:
            spectrumDisplay.toggleSideBands()

    def moveToNextSpectrum(self):
        """
        moves to next spectrum on the current strip, Toggling off the currently displayed spectrum.
        """
        if self.current.strip:
            self.current.strip._moveToNextSpectrumView()
        else:
            getLogger().warning('No current strip. Select a strip first.')

    def moveToPreviousSpectrum(self):
        """
        moves to next spectrum on the current strip, Toggling off the currently displayed spectrum.
        """
        if self.current.strip:
            self.current.strip._moveToPreviousSpectrumView()
        else:
            getLogger().warning('No current strip. Select a strip first.')

    def showAllSpectra(self):
        """
        shows all spectra in the spectrum display.
        """
        if self.current.strip:
            self.current.strip._showAllSpectrumViews(True)
        else:
            getLogger().warning('No current strip. Select a strip first.')

    def hideAllSpectra(self):
        """
        hides all spectra in the spectrum display.
        """
        if self.current.strip:
            self.current.strip._showAllSpectrumViews(False)
        else:
            getLogger().warning('No current strip. Select a strip first.')

    def invertSelectedSpectra(self):
        """
        invertes the selected spectra in the spectrum display. The toggled in will be hided and the hidden spectra will be displayed.
        """
        if self.current.strip:
            self.current.strip._invertSelectedSpectra()
        else:
            getLogger().warning('No current strip. Select a strip first.')

    @logCommand('mainWindow.')
    def snapCurrentPeaksToExtremum(self):
        """
        Snaps selected peaks. If more than one, pops up a Yes/No.
        Uses the minDropFactor from the preferences, and applies a parabolic fit to give first-estimate of lineWidths
        """
        peaks = list(self.current.peaks)
        if not peaks:
            return

        # get the default from the preferences
        minDropFactor = self.application.preferences.general.peakDropFactor
        searchBoxMode = self.application.preferences.general.searchBoxMode
        searchBoxDoFit = self.application.preferences.general.searchBoxDoFit
        fitMethod = self.application.preferences.general.peakFittingMethod

        with undoBlockWithoutSideBar():
            n = len(peaks)

            if n == 1:
                try:
                    peaks[0].snapToExtremum(halfBoxSearchWidth=4, halfBoxFitWidth=4,
                                            minDropFactor=minDropFactor, searchBoxMode=searchBoxMode, searchBoxDoFit=searchBoxDoFit, fitMethod=fitMethod)
                except Exception as es:
                    showWarning('Snap to Extremum', str(es))

            elif n > 1:
                # title = 'Snap Peak%s to extremum' % ('' if n == 1 else 's')
                # msg = 'Snap %sselected peak%s?' % ('' if n == 1 else '%d ' % n, '' if n == 1 else 's')
                # if MessageDialog.showYesNo(title, msg, self):

                with progressManager(self, 'Snapping peaks to extrema'):

                    try:
                        peaks.sort(key=lambda x: x.position[0] if x.position and None not in x.position else 0, reverse=False)  # reorder peaks by position
                        for peak in peaks:
                            peak.snapToExtremum(halfBoxSearchWidth=4, halfBoxFitWidth=4,
                                                minDropFactor=minDropFactor, searchBoxMode=searchBoxMode, searchBoxDoFit=searchBoxDoFit, fitMethod=fitMethod)

                    except Exception as es:
                        showWarning('Snap to Extremum', str(es))

            else:
                getLogger().warning('No selected peak/s. Select a peak first.')

    def storeZoom(self):
        """
        store the zoom of the currently selected strip
        """
        if self.current.strip:
            self.current.strip.spectrumDisplay._storeZoom()
        else:
            getLogger().warning('No current strip. Select a strip first.')

    def restoreZoom(self):
        """
        restore the zoom of the currently selected strip
        """
        if self.current.strip:
            self.current.strip.spectrumDisplay._restoreZoom()
        else:
            getLogger().warning('No current strip. Select a strip first.')

    def previousZoom(self):
        """
        change to the previous stored zoom
        """
        if self.current.strip:
            self.current.strip.spectrumDisplay._previousZoom()
        else:
            getLogger().warning('No current strip. Select a strip first.')

    def nextZoom(self):
        """
        change to the next stored zoom
        """
        if self.current.strip:
            self.current.strip.spectrumDisplay._nextZoom()
        else:
            getLogger().warning('No current strip. Select a strip first.')

    def zoomIn(self):
        """
        zoom in to the currently selected strip
        """
        if self.current.strip:
            self.current.strip.spectrumDisplay._zoomIn()
        else:
            getLogger().warning('No current strip. Select a strip first.')

    def zoomOut(self):
        """
        zoom out of the currently selected strip
        """
        if self.current.strip:
            self.current.strip.spectrumDisplay._zoomOut()
        else:
            getLogger().warning('No current strip. Select a strip first.')

    def panSpectrum(self, direction: str = 'up'):
        """
        Pan/Zoom the current strip with the cursor keys
        """
        if self.current.strip:
            self.current.strip._panSpectrum(direction)
        else:
            getLogger().warning('No current strip. Select a strip first.')

    def movePeaks(self, direction: str = 'up'):
        """
        Move the peaks in the current strip with the cursors
        """
        if self.current.strip:
            self.current.strip._movePeaks(direction)
        else:
            getLogger().warning('No current strip. Select a strip first.')

    def resetAllZoom(self):
        """
        zoom out of the currently selected strip
        """
        if self.current.strip:
            self.current.strip.spectrumDisplay._resetAllZooms()
        else:
            getLogger().warning('No current strip. Select a strip first.')

    def cycleSymbolLabelling(self):
        """
        restore the zoom of the currently selected strip to the top item of the queue
        """
        if self.current.strip:
            self.current.strip.spectrumDisplay._cycleSymbolLabelling()
        else:
            getLogger().warning('No current strip. Select a strip first.')

    def cyclePeakSymbols(self):
        """
        restore the zoom of the currently selected strip to the top item of the queue
        """
        if self.current.strip:
            self.current.strip.spectrumDisplay._cyclePeakSymbols()
        else:
            getLogger().warning('No current strip. Select a strip first.')

    def setMouseMode(self, mode):
        if mode in MouseModes:
            # self.mouseMode = mode
            setCurrentMouseMode(mode)
            for sd in self.project.spectrumDisplays:
                for strp in sd.strips:
                    strp.mouseModeAction.setChecked(mode == PICK)
            mouseModeText = ' Mouse Mode: '
            self.statusBar().showMessage(mouseModeText + mode)

    def switchMouseMode(self):
        # mode = self.mouseMode
        modesCount = len(MouseModes)
        mode = getCurrentMouseMode()
        if mode in MouseModes:
            i = MouseModes.index(mode)
            if i + 1 < modesCount:
                mode = MouseModes[i + 1]
                self.setMouseMode(mode)
            else:
                i = 0
                mode = MouseModes[i]
                self.setMouseMode(mode)

    def _findMenuAction(self, menubarText, menuText):
        # not sure if this function will be needed more widely or just in console context
        # CCPN internal: now also used in SequenceModule._closeModule
        # Should be stored in a dictionary upon initialisation!

        for menuBarAction in self._menuBar.actions():
            if menuBarAction.text() == menubarText:
                break
        else:
            return None

        for menuAction in menuBarAction.menu().actions():
            if menuAction.text() == menuText:
                return menuAction

        return None

    def toggleConsole(self):
        """

        - Opens a new pythonConsole module if none available.
        - Show/hide the pythonConsole module if already one available.
        """
        from ccpn.ui.gui.modules.PythonConsoleModule import PythonConsoleModule

        _justCreated = False
        if self.pythonConsoleModule is None:  # No pythonConsole module detected, so create one.
            self.moduleArea.addModule(PythonConsoleModule(self), 'bottom')
            _justCreated = True
        if self.pythonConsoleModule:
            if self.pythonConsoleModule.isHidden():
                self.pythonConsoleModule.show()
            else:
                if not _justCreated:
                    self.pythonConsoleModule.hide()

    def _lowerContourBaseCallback(self):
        """Callback to lower the contour level for the currently
        selected strip
        """
        if self.current.strip:
            self.current.strip.spectrumDisplay.lowerContourBase()
        else:
            getLogger().warning('No current strip. Select a strip first.')

    def _raiseContourBaseCallback(self):
        """Callback to increase the contour level for the currently
        selected strip
        """
        if self.current.strip:
            self.current.strip.spectrumDisplay.raiseContourBase()
        else:
            getLogger().warning('No current strip. Select a strip first.')

    def previousZPlane(self):
        """
        navigate to the previous Z plane for the currently selected strip
        """
        if self.current.strip:
            self.current.strip._changePlane(stripAxisIndex=2, planeIncrement=-1)
        else:
            getLogger().warning('No current strip. Select a strip first.')

    def nextZPlane(self):
        """
        navigate to the next Z plane for the currently selected strip
        """
        if self.current.strip:
            self.current.strip._changePlane(stripAxisIndex=2, planeIncrement=1)
        else:
            getLogger().warning('No current strip. Select a strip first.')

    @logCommand('mainWindow.')
    def markSelectedPeaks(self, axisIndex=None):
        """Mark the positions of all selected peaks
        """
        if self.current.strip:
            with undoBlockWithoutSideBar():
                for peak in self.current.peaks:
                    self.current.strip._createObjectMark(peak, axisIndex)

    @logCommand('mainWindow.')
    def markSelectedMultiplets(self, axisIndex=None):
        """Mark the positions of all selected multiplets
        """
        if self.current.strip:
            with undoBlockWithoutSideBar():
                for multiplet in self.current.multiplets:
                    self.current.strip._createObjectMark(multiplet, axisIndex)

    def makeStripPlot(self, includePeakLists=True, includeNmrChains=True, includeSpectrumTable=False):
        """Make a strip plot in the current spectrumDisplay
        """
        if self.current.strip and not self.current.strip.isDeleted:
            from ccpn.ui.gui.popups.StripPlotPopup import StripPlotPopup

            popup = StripPlotPopup(parent=self, mainWindow=self, spectrumDisplay=self.current.strip.spectrumDisplay,
                                   includePeakLists=includePeakLists, includeNmrChains=includeNmrChains, includeSpectrumTable=includeSpectrumTable)
            popup.exec_()
        else:
            showWarning('Make Strip Plot', 'No selected spectrumDisplay')
