"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2019"
__credits__ = ("Ed Brooksbank, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: CCPN $"
__dateModified__ = "$dateModified: 2017-07-07 16:32:45 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.b5 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from PyQt5 import QtCore
from ccpn.core.lib import AssignmentLib
from ccpn.core.IntegralList import IntegralList
from ccpn.ui.gui.widgets import MessageDialog
from ccpn.ui.gui.lib.SpectrumDisplay import navigateToCurrentPeakPosition, navigateToCurrentNmrResiduePosition
from ccpn.ui.gui import guiSettings
from ccpn.util.Logging import getLogger
from functools import partial
from ccpn.ui.gui.lib.Shortcuts import addShortCut
from ccpn.ui.gui.popups.ShortcutsPopup import UserShortcuts
from ccpn.ui.gui.widgets.MessageDialog import progressManager
from ccpn.ui.gui.lib.mouseEvents import MouseModes, setCurrentMouseMode, getCurrentMouseMode
from ccpn.util.decorators import logCommand
from ccpn.core.lib.ContextManagers import undoBlock


#TODO:WAYNE: incorporate most functionality in GuiMainWindow. See also MainMenu
# For readability there should be a class
# _MainWindowShortCuts which (Only!) has the shortcut definitions and the callbacks to initiate them.
# The latter should all be private methods!


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
        addShortCut("c, h", self, self.toggleCrosshairAll, context=context)
        addShortCut("c, d", self, self.toggleDoubleCrosshairAll, context=context)
        addShortCut("e, n", self, self.estimateNoise, context=context)
        addShortCut("g, s", self, self.toggleGridAll, context=context)
        addShortCut("Del", self, partial(self.deleteSelectedItems), context=context)
        addShortCut("m, k", self, self.createMark, context=context)
        addShortCut("m, c", self, self.clearMarks, context=context)
        addShortCut("f, n", self, partial(navigateToCurrentNmrResiduePosition, self.application), context=context)
        addShortCut("f, p", self, partial(navigateToCurrentPeakPosition, self.application), context=context)
        addShortCut("c, a", self, partial(AssignmentLib.propagateAssignments, current=self.application.current), context=context)
        addShortCut("c, z", self, self._clearCurrentPeaks, context=context)
        addShortCut("t, u", self, partial(self.traceScaleUp, self), context=context)
        addShortCut("t, d", self, partial(self.traceScaleDown, self), context=context)
        addShortCut("t, h", self, partial(self.toggleHTrace, self), context=context)
        addShortCut("t, v", self, partial(self.toggleVTrace, self), context=context)
        addShortCut("l, a", self, partial(self.toggleLastAxisOnly, self), context=context)
        addShortCut("p, v", self, self.setPhasingPivot, context=context)
        addShortCut("t, r", self, self.removePhasingTraces, context=context)
        addShortCut("a, m", self, self.addMultiplet, context=context)
        addShortCut("t, a", self, self.newPhasingTrace, context=context)
        addShortCut("i, 1", self, self.add1DIntegral, context=context)
        addShortCut("w, 1", self, self.getCurrentPositionAndStrip, context=context)
        addShortCut("r, p", self, partial(self.refitCurrentPeaks, singularMode=True), context=context)
        addShortCut("r, g", self, partial(self.refitCurrentPeaks, singularMode=False), context=context)
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
        addShortCut("z, a", self, self.resetAllZoom, context=context)
        addShortCut("p, l", self, self.cyclePeakLabelling, context=context)
        addShortCut("p, s", self, self.cyclePeakSymbols, context=context)
        # addShortCut("Space, Space", self, self.toggleConsole, context=context) # this is not needed here, already set on Menus!!
        addShortCut("CTRL+a", self, self.selectAllPeaks, context=context)

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

    def deleteSelectedItems(self, parent=None):
        """Delete peaks/integrals/multiplets from the project
        """
        # show simple delete items popup
        from ccpn.ui.gui.popups.DeleteItems import DeleteItemsPopup

        if self.current.peaks or self.current.multiplets or self.current.integrals:
            deleteItems = []
            if self.current.peaks:
                deleteItems.append(('Peaks', self.current.peaks))
            if self.current.integrals:
                deleteItems.append(('Integrals', self.current.integrals))
            if self.current.multiplets:
                deleteItems.append(('Multiplets', self.current.multiplets))

            # add integrals attached peaks
            attachedIntegrals = set()
            for peak in self.current.peaks:
                if peak.integral:
                    attachedIntegrals.add(peak.integral)
            attachedIntegrals = list(attachedIntegrals - set(self.current.integrals))

            if attachedIntegrals:
                deleteItems.append(('Integrals attached to Peaks', attachedIntegrals))

            # add peaks attached multiplets
            attachedPeaks = set()
            for multiplet in self.current.multiplets:
                for peak in multiplet.peaks:
                    attachedPeaks.add(peak)
            attachedPeaks = list(attachedPeaks - set(self.current.peaks))

            if attachedPeaks:
                deleteItems.append(('Peaks attached to Multiplets', attachedPeaks))

            popup = DeleteItemsPopup(parent=self, mainWindow=self, items=deleteItems)
            popup.exec_()

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

    def setPeakAliasing(self):
        """Set the aliasing for the currently selected peaks
        """
        if self.current.peaks:
            from ccpn.ui.gui.popups.SetPeakAliasing import SetPeakAliasingPopup

            popup = SetPeakAliasingPopup(parent=self, mainWindow=self, items=self.current.peaks)
            popup.exec_()

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
        strip = self.application.current.strip
        peak = self.project.getByPid(peak) if isinstance(peak, str) else peak

        if strip is not None:
            if strip.spectrumDisplay.is1D:
                cursorPosition = self.application.current.cursorPosition
                if cursorPosition is not None:
                    limits = [cursorPosition[0], cursorPosition[0] + 0.005]

                    validViews = [sv for sv in strip.spectrumViews if sv.isVisible()]

                    # with logCommandBlock(get='self') as log:
                    #     if peak:
                    #         log('add1DIntegral', peak=repr(peak.pid))
                    #     else:
                    #         log('add1DIntegral')

                    with undoBlock():
                        currentIntegrals = list(self.current.integrals)
                        for spectrumView in validViews:

                            if not spectrumView.spectrum.integralLists:
                                spectrumView.spectrum.newIntegralList()

                            validIntegralLists = [il.integralList for il in spectrumView.integralListViews]

                            if len(
                                    validIntegralLists) > 1:  # make a integralView always visible if there is only one and are creating a new integral
                                validIntegralLists = [il for il in validIntegralLists if il.isVisible()]

                            if len(validIntegralLists) == 1:
                                for il in spectrumView.peakListViews:
                                    if isinstance(il.peakList, IntegralList):
                                        il.setVisible(True)

                            for integralList in validIntegralLists:
                                integral = integralList.newIntegral(value=None, limits=[limits, ])
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

    def refitCurrentPeaks(self, singularMode=True):
        peaks = self.application.current.peaks
        if not peaks:
            return

        with undoBlock():
            AssignmentLib.refitPeaks(peaks, singularMode=singularMode)

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

    def selectAllPeaks(self):
        '''selects all peaks in the current strip if the spectrum is toggled on'''
        if self.application.current.strip:
            if self.application.current.strip.spectrumDisplay:
                spectra = [spectrumView.spectrum for spectrumView in
                           self.application.current.strip.spectrumDisplay.spectrumViews if spectrumView.isVisible()]
                peakLists = [peakList.peaks for spectrum in spectra for peakList in spectrum.peakLists]
                self.application.current.peaks = [peak for peakList in peakLists for peak in peakList]

    def addMultiplet(self):
        """add current peaks to a new multiplet"""
        strip = self.application.current.strip

        with undoBlock():
            if strip and strip.spectrumDisplay:
                spectra = [spectrumView.spectrum for spectrumView in
                           strip.spectrumDisplay.spectrumViews if spectrumView.isVisible()]
                for spectrum in spectra:
                    if len(spectrum.multipletLists) < 1:
                        multipletList = spectrum.newMultipletList()
                    else:
                        multipletList = spectrum.multipletLists[-1]
                    peaks = [peak for peakList in spectrum.peakLists for peak in peakList.peaks if
                             peak in self.application.current.peaks]
                    multiplet = multipletList.newMultiplet(peaks=peaks)
                    self.application.current.multiplet = multiplet

    def traceScaleScale(self, window: 'GuiWindow', scale: float):
        """
        Changes the scale of a trace in all spectrum displays of the window.
        """
        # for spectrumDisplay in window.spectrumDisplays:

        if self.application.current.strip:
            spectrumDisplay = self.application.current.strip.spectrumDisplay

            if not spectrumDisplay.is1D:
                for strip in spectrumDisplay.strips:
                    for spectrumView in strip.spectrumViews:
                        spectrumView.traceScale *= scale

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
        if strip:               # and (strip.spectrumDisplay.window is self):
            strip._newPhasingTrace()

    def setPhasingPivot(self):

        strip = self.application.current.strip
        if strip:               # and (strip.spectrumDisplay.window is self):
            strip._setPhasingPivot()

    def removePhasingTraces(self):
        """
        Removes all phasing traces from all strips.
        """
        strip = self.application.current.strip
        if strip:               # and (strip.spectrumDisplay.window is self):
            # strip.removePhasingTraces()
            for strip in strip.spectrumDisplay.strips:
                strip.removePhasingTraces()

    def _clearCurrentPeaks(self):
        """
        Sets current.peaks to an empty list.
        """
        # self.application.current.peaks = []
        self.application.current.clearPeaks()

    def toggleCrosshairAll(self):
        """
        Toggles whether crosshairs are displayed in all windows.
        """
        for window in self.project.windows:
            window.toggleCrosshair()

    def toggleCrosshair(self):
        """
        Toggles whether crosshairs are displayed in all spectrum displays
        """
        # toggle crosshairs for the spectrum displays in this window
        for spectrumDisplay in self.spectrumDisplays:
            spectrumDisplay.toggleCrosshair()

    def toggleDoubleCrosshairAll(self):
        """
        Toggles whether double crosshairs are displayed in all windows.
        """
        self.application.preferences.general.showDoubleCrosshair = not self.application.preferences.general.showDoubleCrosshair

        # repaint all windows
        from ccpn.ui.gui.lib.OpenGL.CcpnOpenGL import GLNotifier

        GLSignals = GLNotifier(parent=self)
        GLSignals.emitPaintEvent()

    def estimateNoise(self):
        """estimate the noise in the visible region of the current strip
        """
        strip = self.application.current.strip
        if strip:
            strip.estimateNoise()

    def createMark(self):
        """
        Creates a mark at the current cursor position in the current strip.
        """
        strip = self.application.current.strip
        if strip:
            strip._createMarkAtCursorPosition()

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
                with undoBlock():
                    # GWV 20181030: changed from atomName to id
                    if colour:
                        project.newMark(colour, [chemicalShift.value], [axisCode], labels=[atomId])
                    else:
                        # just use gray rather than checking colourScheme
                        defaultColour = self.application.preferences.general.defaultMarksColour
                        project.newMark(defaultColour, [chemicalShift.value], [atomId])

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

    def snapCurrentPeaksToExtremum(self, parent=None):
        """
           Snaps selected peaks. If more then one, pops up a Yes/No.
        """
        peaks = self.current.peaks
        n = len(peaks)
        # self.application.project.blankNotification()
        if n == 1:
            peaks[0].snapToExtremum(halfBoxSearchWidth=3, halfBoxFitWidth=10)
        elif n > 1:
            title = 'Snap Peak%s to extremum' % ('' if n == 1 else 's')
            msg = 'Snap %sselected peak%s?' % ('' if n == 1 else '%d ' % n, '' if n == 1 else 's')
            if MessageDialog.showYesNo(title, msg, parent):
                with progressManager(self, 'Snapping peaks to extrema'):
                    for peak in peaks:
                        peak.snapToExtremum(halfBoxSearchWidth=3, halfBoxFitWidth=10)
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

    def resetAllZoom(self):
        """
        zoom out of the currently selected strip
        """
        if self.current.strip:
            self.current.strip.spectrumDisplay._resetAllZooms()
        else:
            getLogger().warning('No current strip. Select a strip first.')

    def cyclePeakLabelling(self):
        """
        restore the zoom of the currently selected strip to the top item of the queue
        """
        if self.current.strip:
            self.current.strip.spectrumDisplay._cyclePeakLabelling()
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
        - Closes the  pythonConsole module if already one available.

        """
        # NB. The  pythonConsole module is only a container for the IpythonConsole Widget,
        #     which is always present in the application and never gets destroyed until the project is closed.
        #     The pythonConsole module instead is created and closed all the time this function is called.
        #     Destroying the module has been the most stable way of handle this toggling feature. Hiding,moving or any other
        #     kind, has created many bugs in the past, including misbehaviour on tempAreas, containers QT errors etc.

        from ccpn.ui.gui.modules.PythonConsoleModule import PythonConsoleModule

        if self.pythonConsoleModule is None:  # No pythonConsole module detected, so create one.
            self.moduleArea.addModule(PythonConsoleModule(self), 'bottom')

        else:  # just close it!
            self.pythonConsoleModule._closeModule()
