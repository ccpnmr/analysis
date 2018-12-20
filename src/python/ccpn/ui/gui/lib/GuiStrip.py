"""
Module Documentation here
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
__modifiedBy__ = "$modifiedBy: Wayne Boucher $"
__dateModified__ = "$dateModified: 2017-07-07 16:32:44 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.b4 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

import typing

import pyqtgraph as pg
from PyQt5 import QtWidgets, QtCore, QtGui

from ccpn.core.Project import Project
from ccpn.core.lib.Notifiers import Notifier, NotifierBase

from ccpn.ui.gui.guiSettings import getColours, GUISTRIP_PIVOT
from ccpn.ui.gui.widgets.PlaneToolbar import _StripLabel, StripHeader
from ccpn.ui.gui.widgets.Frame import Frame
from ccpn.ui.gui.widgets.Widget import Widget
from ccpn.ui.gui.lib.GuiNotifier import GuiNotifier
from ccpn.ui.gui.widgets.DropBase import DropBase
from ccpn.ui.gui.widgets import MessageDialog
from ccpn.util.Logging import getLogger
from ccpn.util.Constants import AXIS_MATCHATOMTYPE, AXIS_FULLATOMNAME
from functools import partial
from ccpn.ui.gui.lib.OpenGL.CcpnOpenGLDefs import AXISXUNITS, AXISYUNITS, AXISLOCKASPECTRATIO
from ccpn.core.lib.ContextManagers import logCommandBlock, undoStackBlocking


STRIPLABEL_ISPLUS = 'stripLabel_isPlus'

DefaultMenu = 'DefaultMenu'
PeakMenu = 'PeakMenu'
IntegralMenu = 'IntegralMenu'
MultipletMenu = 'MultipletMenu'
PhasingMenu = 'PhasingMenu'


class GuiStrip(Frame):
    # inherits NotifierBase

    def __init__(self, spectrumDisplay, useOpenGL=False):
        """
        Basic strip class; used in StripNd and Strip1d

        :param spectrumDisplay: spectrumDisplay instance

        This module inherits attributes from the Strip wrapper class:
        Use clone() method to make a copy
        """

        # For now, cannot set spectrumDisplay attribute as it is owned by the wrapper class
        # self.spectrumDisplay = spectrumDisplay
        self.mainWindow = self.spectrumDisplay.mainWindow
        self.application = self.mainWindow.application
        self.current = self.application.current

        getLogger().debug('GuiStrip>>> spectrumDisplay: %s' % self.spectrumDisplay)
        super().__init__(parent=spectrumDisplay.stripFrame, setLayout=True,
                         acceptDrops=True  #, hPolicy='expanding', vPolicy='expanding' ##'minimal'
                         )

        self.setMinimumWidth(50)
        self.setMinimumHeight(150)

        self.layout().setSpacing(0)
        self.header = StripHeader(parent=self, mainWindow=self.mainWindow,
                                  grid=(0, 0), gridSpan=(1, 2), setLayout=True, spacing=(0, 0))

        self._useCcpnGL = True
        # TODO: ED comment out the block below to return to normal
        if self._useCcpnGL:
            # self.plotWidget.hide()

            if spectrumDisplay.is1D:
                from ccpn.ui.gui.widgets.GLWidgets import Gui1dWidget as CcpnGLWidget
            else:
                from ccpn.ui.gui.widgets.GLWidgets import GuiNdWidget as CcpnGLWidget

            self._CcpnGLWidget = CcpnGLWidget(strip=self, mainWindow=self.mainWindow)
            self.getLayout().addWidget(self._CcpnGLWidget, 1, 0)  # (3,0) if not hiding plotWidget
            self._CcpnGLWidget.setSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding,
                                             QtWidgets.QSizePolicy.MinimumExpanding)

            # set the ID label in the new widget
            self._CcpnGLWidget.setStripID('.'.join(self.id.split('.')))
            self._CcpnGLWidget.gridVisible = self.application.preferences.general.showGrid

        # Widgets for toolbar; items will be added by GuiStripNd (eg. the Z/A-plane boxes)
        # and GuiStrip1d; will be hidden for 2D's by GuiSpectrumView
        self._stripToolBarWidget = Widget(parent=self, setLayout=True,
                                          hPolicy='expanding',
                                          grid=(2, 0), spacing=(5, 5))

        self.viewStripMenu = None  # = self.plotItem.vb
        self._showCrossHair()
        self.storedZooms = []
        self.beingUpdated = False

        # need to keep track of mouse position because Qt shortcuts don't provide
        # the widget or the position of where the cursor is
        self.axisPositionDict = {}  # axisCode --> position

        self._contextMenuMode = DefaultMenu
        self._contextMenus = {DefaultMenu  : None,
                              PeakMenu     : None,
                              PhasingMenu  : None,
                              MultipletMenu: None,
                              IntegralMenu : None
                              }

        self.navigateToPeakMenu = None  #set from context menu and in CcpnOpenGL rightClick
        self.navigateToCursorMenu = None  #set from context menu and in CcpnOpenGL rightClick
        self._isPhasingOn = False

        # set peakLabelling to the default from preferences or strip to the left
        settings = spectrumDisplay.getSettings()
        if len(spectrumDisplay.strips) > 1:
            self.peakLabelling = spectrumDisplay.strips[0].peakLabelling
            self.symbolType = spectrumDisplay.strips[0].symbolType
            self.symbolSize = spectrumDisplay.strips[0].symbolSize
            self.symbolThickness = spectrumDisplay.strips[0].symbolThickness
            self.gridVisible = spectrumDisplay.strips[0].gridVisible
            self.crosshairVisible = spectrumDisplay.strips[0].crosshairVisible
            self.showSpectraOnPhasing = spectrumDisplay.strips[0].showSpectraOnPhasing

            try:
                self._CcpnGLWidget._axisLocked = spectrumDisplay.strips[0]._CcpnGLWidget._axisLocked
            except Exception as es:
                getLogger().debugGL('OpenGL widget not instantiated')

        else:
            self.peakLabelling = self.application.preferences.general.annotationType
            self.symbolType = self.application.preferences.general.symbolType
            if spectrumDisplay.is1D:
                self.symbolSize = self.application.preferences.general.symbolSize1d
            else:
                self.symbolSize = self.application.preferences.general.symbolSizeNd
            self.symbolThickness = self.application.preferences.general.symbolThickness
            self.gridVisible = self.application.preferences.general.showGrid
            self.crosshairVisible = self.application.preferences.general.showCrosshair
            self.showSpectraOnPhasing = self.application.preferences.general.showSpectraOnPhasing

        self._storedPhasingData = [[0.0, 0.0, 0.0], [0.0, 0.0, 0.0]]

        try:
            self._CcpnGLWidget.gridVisible = self.application.preferences.general.showGrid
            # set the axis units from the current settings
            self._CcpnGLWidget.xUnits = settings[AXISXUNITS]
            self._CcpnGLWidget.yUnits = settings[AXISYUNITS]
            self._CcpnGLWidget.axisLocked = settings[AXISLOCKASPECTRATIO]
        except Exception as es:
            getLogger().debugGL('OpenGL widget not instantiated')

        # initialise the notifiers
        self.setStripNotifiers()

    def setStripNotifiers(self):
        """Set the notifiers for the strip.
        """
        # GWV 20181127: moved to GuiMainWindow
        # notifier for highlighting the strip
        # self._stripNotifier = Notifier(self.current, [Notifier.CURRENT], 'strip', self._highlightCurrentStrip)

        # Notifier for updating the peaks
        self.setNotifier(self.project, [Notifier.CREATE, Notifier.DELETE, Notifier.CHANGE],
                         'Peak', self._updateDisplayedPeaks, onceOnly=True)

        # Notifier for updating the integrals
        self.setNotifier(self.project, [Notifier.CREATE, Notifier.DELETE, Notifier.CHANGE],
                         'Integral', self._updateDisplayedIntegrals, onceOnly=True)

        # Notifier for updating the multiplets
        self.setNotifier(self.project, [Notifier.CREATE, Notifier.DELETE, Notifier.CHANGE],
                         'Multiplet', self._updateDisplayedMultiplets, onceOnly=True)

        # Notifier for change of stripLabel
        self.setNotifier(self.project, [Notifier.RENAME], 'NmrResidue', self._updateStripLabel)

        # For now, all dropEvents are not strip specific, use spectrumDisplay's handling
        self.setGuiNotifier(self, [GuiNotifier.DROPEVENT], [DropBase.URLS, DropBase.PIDS],
                            self.spectrumDisplay._processDroppedItems)
        self.setGuiNotifier(self, [GuiNotifier.DRAGMOVEEVENT], [DropBase.URLS, DropBase.PIDS],
                            self.spectrumDisplay._processDragEnterEvent)

    def viewRange(self):
        return self._CcpnGLWidget.viewRange()

    @property
    def gridIsVisible(self):
        """True if grid is visible.
        """
        try:
            return self._CcpnGLWidget.gridVisible
        except Exception as es:
            getLogger().debugGL('OpenGL widget not instantiated')

    @property
    def crossHairIsVisible(self):
        """True if crosshair is visible.
        """
        try:
            return self._CcpnGLWidget.crossHairVisible
        except Exception as es:
            getLogger().debugGL('OpenGL widget not instantiated')

    @property
    def pythonConsole(self):
        return self.mainWindow.pythonConsole

    def _openCopySelectedPeaks(self):
        from ccpn.ui.gui.popups.CopyPeaksPopup import CopyPeaks

        popup = CopyPeaks(parent=self.mainWindow, mainWindow=self.mainWindow)
        peaks = self.current.peaks
        popup._selectPeaks(peaks)
        popup.exec()
        popup.raise_()

    def _updateStripLabel(self, callbackDict):
        """Update the striplabel if it represented a NmrResidue that has changed its id.
        """
        text = self.header.getLabelText(position='c')
        if callbackDict['oldPid'] == text:
            self.header.setLabelText(position='c', text=callbackDict['object'].pid)

    def createMark(self):
        """Sets the marks at current position
        """
        self.spectrumDisplay.mainWindow.createMark()

    def clearMarks(self):
        """Sets the marks at current position
        """
        self.spectrumDisplay.mainWindow.clearMarks()

    def estimateNoise(self):
        """Estimate noise in the current region
        """
        from ccpn.ui.gui.popups.EstimateNoisePopup import EstimateNoisePopup

        popup = EstimateNoisePopup(parent=self.mainWindow, mainWindow=self.mainWindow, strip=self,
                                   orderedSpectrumViews=self.spectrumDisplay.orderedSpectrumViews(self.spectrumViews))
        popup.exec_()
        popup._cleanupWidget()

    def makeStripPlot(self):
        """Make a strip plot in the current spectrumDisplay
        """
        from ccpn.ui.gui.popups.StripPlotPopup import StripPlotPopup

        popup = StripPlotPopup(parent=self.mainWindow, mainWindow=self.mainWindow, spectrumDisplay=self.spectrumDisplay,
                               includePeakLists=True, includeNmrChains=True, includeSpectrumTable=False)
        popup.exec_()
        popup._cleanupWidget()

    def close(self):
        self.deleteAllNotifiers()
        super().close()

    # GWV 20181127: changed implementation to use deleteAllNotifiers in close() method
    # def _unregisterStrip(self):
    #     """Unregister all notifiers
    #     """
    #     self._stripNotifier.unRegister()
    #     self._peakNotifier.unRegister()
    #     self._integralNotifier.unRegister()
    #     self._multipletNotifier.unRegister()
    #     self._stripLabelNotifier.unRegister()
    #     self._droppedNotifier.unRegister()
    #     self._moveEventNotifier.unRegister()

    def _updateDisplayedPeaks(self, data):
        """Callback when peaks have changed
        """
        self._CcpnGLWidget._processPeakNotifier(data)

    def _updateDisplayedMultiplets(self, data):
        """Callback when multiplets have changed
        """
        self._CcpnGLWidget._processMultipletNotifier(data)

    def _checkMenuItems(self):
        """Update the menu check boxes from the strip
        Subclass if options needed, e.g. stackSpectra item
        """
        pass

    def _addItemsToNavigateToPeakMenu(self):
        """Adds item to navigate to peak position from context menu.
        """
        # TODO, merge the two menu (cursor and peak) in one single menu to avoid code duplication. Issues: when tried, only one menu at the time worked!
        from functools import partial
        from ccpn.ui.gui.lib.Strip import navigateToPositionInStrip

        if self.navigateToPeakMenu:
            self.navigateToPeakMenu.clear()
            currentStrip = self.current.strip
            position = self.current.cursorPosition
            if currentStrip:
                if self.current.peak:
                    if len(self.current.project.spectrumDisplays) > 1:
                        self.navigateToPeakMenu.setEnabled(True)
                        for spectrumDisplay in self.current.project.spectrumDisplays:
                            for strip in spectrumDisplay.strips:
                                if strip != currentStrip:
                                    toolTip = 'Show cursor in strip %s at Peak position %s' % (str(strip.id), str([round(x, 3) for x in position]))
                                    if len(list(set(strip.axisCodes) & set(currentStrip.axisCodes))) <= 2:
                                        self.navigateToPeakMenu.addItem(text=strip.pid,
                                                                        callback=partial(navigateToPositionInStrip, strip=strip,
                                                                                         positions=self.current.peak.position,
                                                                                         axisCodes=self.current.peak.axisCodes),
                                                                        toolTip=toolTip)
                                self.navigateToPeakMenu.addSeparator()
                    else:
                        self.navigateToPeakMenu.setEnabled(False)

    def _addItemsToNavigateToCursorPosMenu(self):
        """Copied from old viewbox. This function apparently take the current cursorPosition
         and uses to pan a selected display from the list of spectrumViews or the current cursor position.
        """
        # TODO needs clear documentation
        from functools import partial
        from ccpn.ui.gui.lib.Strip import navigateToPositionInStrip

        if self.navigateCursorMenu:
            self.navigateCursorMenu.clear()
            currentStrip = self.current.strip
            position = self.current.cursorPosition
            if currentStrip:
                if len(self.current.project.spectrumDisplays) > 1:
                    self.navigateCursorMenu.setEnabled(True)
                    for spectrumDisplay in self.current.project.spectrumDisplays:
                        for strip in spectrumDisplay.strips:
                            if strip != currentStrip:
                                toolTip = 'Show cursor in strip %s at Cursor position %s' % (str(strip.id), str([round(x, 3) for x in position]))
                                if len(list(set(strip.axisCodes) & set(currentStrip.axisCodes))) <= 2:
                                    self.navigateCursorMenu.addItem(text=strip.pid,
                                                                    callback=partial(navigateToPositionInStrip, strip=strip,
                                                                                     positions=position, axisCodes=currentStrip.axisCodes, ),
                                                                    toolTip=toolTip)
                            self.navigateCursorMenu.addSeparator()
                else:
                    self.navigateCursorMenu.setEnabled(False)

    def _updateDisplayedIntegrals(self, data):
        """Callback when integrals have changed.
        """
        self._CcpnGLWidget._processIntegralNotifier(data)

    def _highlightStrip(self, flag):
        """(un)highLight the strip depending on flag

        CCPNINTERNAL: used in GuiMainWindow
        """
        self._CcpnGLWidget.highlightCurrentStrip(flag)

    # GWV 20181127: moved to a single notifier in GuiMainWindow
    # def _highlightCurrentStrip(self, data):
    #     "Callback to highlight the axes of current strip"
    #     # self.plotWidget.highlightAxes(self is self.current.strip)
    #     pass
    #
    #     try:
    #         # Only do something in case of the old and new current strip
    #         previousStrip = data[Notifier.PREVIOUSVALUE]
    #         if self is previousStrip:
    #             self._CcpnGLWidget.highlightCurrentStrip(False)
    #         elif self is self.current.strip:
    #             self._CcpnGLWidget.highlightCurrentStrip(True)
    #
    #         # # spawn a redraw of the GL windows
    #         # from ccpn.util.CcpnOpenGL import GLNotifier
    #         # GLSignals = GLNotifier(parent=None)
    #         # GLSignals.emitPaintEvent()
    #
    #     except Exception as es:
    #         getLogger().debugGL('OpenGL widget not instantiated', strip=self, error=es)

    def _newPhasingTrace(self):
        try:
            self._CcpnGLWidget.newTrace()
        except Exception as es:
            getLogger().debugGL('OpenGL widget not instantiated')

    def _setPhasingPivot(self):

        phasingFrame = self.spectrumDisplay.phasingFrame
        direction = phasingFrame.getDirection()
        # position = self.current.cursorPosition[0] if direction == 0 else self.current.cursorPosition[1]
        # position = self.current.positions[0] if direction == 0 else self.current.positions[1]

        mouseMovedDict = self.current.mouseMovedDict
        if direction == 0:
            for mm in mouseMovedDict[AXIS_MATCHATOMTYPE].keys():
                if mm[0] == self.axisCodes[0][0]:
                    position = mouseMovedDict[AXIS_MATCHATOMTYPE][mm]
        else:
            for mm in mouseMovedDict[AXIS_MATCHATOMTYPE].keys():
                if mm[0] == self.axisCodes[1][0]:
                    position = mouseMovedDict[AXIS_MATCHATOMTYPE][mm]

        phasingFrame.pivotEntry.set(position)
        self._updatePivot()

    def removePhasingTraces(self):
        try:
            self._CcpnGLWidget.clearStaticTraces()
        except:
            getLogger().debugGL('OpenGL widget not instantiated')

    def _updatePivot(self):
        # this is called if pivot entry at bottom of display is updated and then "return" key used

        # update the static traces from the phasing console
        # redraw should update the display
        try:
            self._CcpnGLWidget.rescaleStaticTraces()
        except:
            getLogger().debugGL('OpenGL widget not instantiated')

    def setTraceScale(self, traceScale):
        for spectrumView in self.spectrumViews:
            spectrumView.traceScale = traceScale

    @property
    def contextMenuMode(self):
        return self._contextMenuMode

    @contextMenuMode.getter
    def contextMenuMode(self):
        return self._contextMenuMode

    @contextMenuMode.setter
    def contextMenuMode(self, mode):
        self._contextMenuMode = mode

    def turnOnPhasing(self):

        phasingFrame = self.spectrumDisplay.phasingFrame
        # self.hPhasingPivot.setVisible(True)
        # self.vPhasingPivot.setVisible(True)

        # change menu
        self._isPhasingOn = True
        self.viewStripMenu = self._phasingMenu

        if self.spectrumDisplay.is1D:

            self._hTraceActive = True
            self._vTraceActive = False
            self._newConsoleDirection = 0
        else:
            # TODO:ED remember trace direction
            self._hTraceActive = self.spectrumDisplay.hTraceAction  # self.hTraceAction.isChecked()
            self._vTraceActive = self.spectrumDisplay.vTraceAction  # self.vTraceAction.isChecked()

            # set to the first active or the remembered phasingDirection
            self._newConsoleDirection = phasingFrame.getDirection()
            if self._hTraceActive:
                self._newConsoleDirection = 0
                phasingFrame.directionList.setIndex(0)
            elif self._vTraceActive:
                self._newConsoleDirection = 1
                phasingFrame.directionList.setIndex(1)

        # for spectrumView in self.spectrumViews:
        #     spectrumView._turnOnPhasing()

        # # make sure that all traces are clear
        # from ccpn.util.CcpnOpenGL import GLNotifier
        # GLSignals = GLNotifier(parent=self)
        # if self.spectrumDisplay.is1D:
        #   GLSignals.emitEvent(triggers=[GLNotifier.GLADD1DPHASING], display=self.spectrumDisplay)
        # else:
        #   GLSignals.emitEvent(triggers=[GLNotifier.GLCLEARPHASING], display=self.spectrumDisplay)

        vals = self.spectrumDisplay.phasingFrame.getValues(self._newConsoleDirection)
        self.spectrumDisplay.phasingFrame.slider0.setValue(vals[0])
        self.spectrumDisplay.phasingFrame.slider1.setValue(vals[1])
        self.spectrumDisplay.phasingFrame.pivotEntry.set(vals[2])

        # TODO:ED remember direction
        self._newPosition = phasingFrame.pivotEntry.get()
        self.pivotLine = self._CcpnGLWidget.addInfiniteLine(colour='highlight', movable=True, lineStyle='dashed', lineWidth=2.0)

        if not self.pivotLine:
            getLogger().warning('no infiniteLine')
            return

        if self._newConsoleDirection == 0:
            self.pivotLine.orientation = ('v')

            # self.hTraceAction.setChecked(True)
            # self.vTraceAction.setChecked(False)
            if not self.spectrumDisplay.is1D:
                self.hTraceAction.setChecked(True)
                self.vTraceAction.setChecked(False)
                self._CcpnGLWidget.updateHTrace = True
                self._CcpnGLWidget.updateVTrace = False
        else:
            self.pivotLine.orientation = ('h')
            # self.hTraceAction.setChecked(False)
            # self.vTraceAction.setChecked(True)
            if not self.spectrumDisplay.is1D:
                self.hTraceAction.setChecked(False)
                self.vTraceAction.setChecked(True)
                self._CcpnGLWidget.updateHTrace = False
                self._CcpnGLWidget.updateVTrace = True

        self.pivotLine.valuesChanged.connect(self._newPositionLineCallback)
        self.pivotLine.setValue(self._newPosition)
        phasingFrame.pivotEntry.valueChanged.connect(self._newPositionPivotCallback)

        # make sure that all traces are clear
        from ccpn.ui.gui.lib.OpenGL.CcpnOpenGL import GLNotifier

        GLSignals = GLNotifier(parent=self)
        if self.spectrumDisplay.is1D:
            GLSignals.emitEvent(triggers=[GLNotifier.GLADD1DPHASING], display=self.spectrumDisplay)
        else:
            GLSignals.emitEvent(triggers=[GLNotifier.GLCLEARPHASING], display=self.spectrumDisplay)

    def _newPositionLineCallback(self):
        if not self.isDeleted:
            phasingFrame = self.spectrumDisplay.phasingFrame
            self._newPosition = self.pivotLine.values  # [0]
            phasingFrame.pivotEntry.setValue(self._newPosition)

    def _newPositionPivotCallback(self, value):
        self._newPosition = value
        self.pivotLine.setValue(value)

    def turnOffPhasing(self):
        phasingFrame = self.spectrumDisplay.phasingFrame

        # self.hPhasingPivot.setVisible(False)
        # self.vPhasingPivot.setVisible(False)

        # change menu
        self._isPhasingOn = False
        # for spectrumView in self.spectrumViews:
        #     spectrumView._turnOffPhasing()

        # make sure that all traces are clear
        from ccpn.ui.gui.lib.OpenGL.CcpnOpenGL import GLNotifier

        GLSignals = GLNotifier(parent=self)
        GLSignals.emitEvent(triggers=[GLNotifier.GLCLEARPHASING], display=self.spectrumDisplay)

        self._CcpnGLWidget.removeInfiniteLine(self.pivotLine)
        self.pivotLine.valuesChanged.disconnect(self._newPositionLineCallback)
        phasingFrame.pivotEntry.valueChanged.disconnect(self._newPositionPivotCallback)

        if self.spectrumDisplay.is1D:
            self._CcpnGLWidget.updateHTrace = False
            self._CcpnGLWidget.updateVTrace = False
        else:
            # TODO:ED remember trace direction
            self.hTraceAction.setChecked(False)  #self._hTraceActive)
            self.vTraceAction.setChecked(False)  #self._vTraceActive)
            self._CcpnGLWidget.updateHTrace = False  #self._hTraceActive
            self._CcpnGLWidget.updateVTrace = False  #self._vTraceActive

    def _changedPhasingDirection(self):

        phasingFrame = self.spectrumDisplay.phasingFrame
        direction = phasingFrame.getDirection()

        if not phasingFrame.isVisible():
            return

        if direction == 0:
            self.pivotLine.orientation = ('v')
            self.hTraceAction.setChecked(True)
            self.vTraceAction.setChecked(False)
            self._CcpnGLWidget.updateHTrace = True
            self._CcpnGLWidget.updateVTrace = False
        else:
            self.pivotLine.orientation = ('h')
            self.hTraceAction.setChecked(False)
            self.vTraceAction.setChecked(True)
            self._CcpnGLWidget.updateHTrace = False
            self._CcpnGLWidget.updateVTrace = True

        vals = phasingFrame.getValues(direction)
        # phasingFrame.slider0.setValue(self.spectrumDisplay._storedPhasingData[direction][0])
        # phasingFrame.slider1.setValue(self.spectrumDisplay._storedPhasingData[direction][1])
        # phasingFrame.pivotEntry.set(self.spectrumDisplay._storedPhasingData[direction][2])
        phasingFrame.slider0.setValue(vals[0])
        phasingFrame.slider1.setValue(vals[1])
        phasingFrame.pivotEntry.set(vals[2])

        try:
            self._CcpnGLWidget.clearStaticTraces()
        except:
            getLogger().debugGL('OpenGL widget not instantiated')

        # for spectrumView in self.spectrumViews:
        #     spectrumView._changedPhasingDirection()

    def _updatePhasing(self):
        try:
            if self.spectrumDisplay.phasingFrame.isVisible():
                colour = getColours()[GUISTRIP_PIVOT]
                self._CcpnGLWidget.setInfiniteLineColour(self.pivotLine, colour)
                self._CcpnGLWidget.rescaleStaticTraces()
        except:
            getLogger().debugGL('OpenGL widget not instantiated', spectrumDisplay=self.spectrumDisplay, strip=self)

    def _toggleCrossHair(self):
        """Toggles whether crosshair is visible.
        """
        try:
            self.crosshairVisible = not self.crosshairVisible
            self._CcpnGLWidget.crossHairVisible = self.crosshairVisible
        except:
            getLogger().debugGL('OpenGL widget not instantiated')

    def _showCrossHair(self):
        """Displays crosshair in strip.
        """
        try:
            self.crosshairVisible = True
            self._CcpnGLWidget.crossHairVisible = True
        except:
            getLogger().debugGL('OpenGL widget not instantiated')

    def _hideCrossHair(self):
        """Hides crosshair in strip.
        """
        try:
            self.crosshairVisible = False
            self._CcpnGLWidget.crossHairVisible = False
        except:
            getLogger().debugGL('OpenGL widget not instantiated')

    def _toggleShowSpectraOnPhasing(self):
        """Toggles whether spectraOnPhasing is visible.
        """
        try:
            self.showSpectraOnPhasing = not self.showSpectraOnPhasing
            self._CcpnGLWidget.showSpectraOnPhasing = self.showSpectraOnPhasing
        except:
            getLogger().debugGL('OpenGL widget not instantiated')

    def _showSpectraOnPhasing(self):
        """Displays spectraOnPhasing in strip.
        """
        try:
            self.showSpectraOnPhasing = True
            self._CcpnGLWidget.showSpectraOnPhasing = True
        except:
            getLogger().debugGL('OpenGL widget not instantiated')

    def _hideSpectraOnPhasing(self):
        """Hides spectraOnPhasing in strip.
        """
        try:
            self.showSpectraOnPhasing = False
            self._CcpnGLWidget.showSpectraOnPhasing = False
        except:
            getLogger().debugGL('OpenGL widget not instantiated')

    def toggleGrid(self):
        """Toggles whether grid is visible in the strip.
        """
        try:
            self.gridVisible = not self.gridVisible
            self._CcpnGLWidget.gridVisible = self.gridVisible
        except:
            getLogger().debugGL('OpenGL widget not instantiated')

    def cyclePeakLabelling(self):
        """Toggles whether peak labelling is minimal is visible in the strip.
        """
        self.peakLabelling += 1
        if self.peakLabelling > 2:
            self.peakLabelling = 0

        if self.spectrumViews:
            for sV in self.spectrumViews:

                for peakListView in sV.peakListViews:
                    # peakListView.buildSymbols = True
                    peakListView.buildLabels = True

            # spawn a redraw of the GL windows
            from ccpn.ui.gui.lib.OpenGL.CcpnOpenGL import GLNotifier

            GLSignals = GLNotifier(parent=None)
            GLSignals.emitPaintEvent()

    def cyclePeakSymbols(self):
        """Cycle through peak symbol types.
        """
        self.symbolType += 1
        if self.symbolType > 2:
            self.symbolType = 0

        if self.spectrumViews:
            for sV in self.spectrumViews:

                for peakListView in sV.peakListViews:
                    peakListView.buildSymbols = True
                    peakListView.buildLabels = True

                for multipletListView in sV.multipletListViews:
                    multipletListView.buildSymbols = True
                    multipletListView.buildLabels = True

            # spawn a redraw of the GL windows
            from ccpn.ui.gui.lib.OpenGL.CcpnOpenGL import GLNotifier

            GLSignals = GLNotifier(parent=None)
            GLSignals.emitPaintEvent()

    def _crosshairCode(self, axisCode):
        """Determines what axisCodes are compatible as far as drawing crosshair is concerned
        TBD: the naive approach below should be improved
        """
        return axisCode  #if axisCode[0].isupper() else axisCode

    def _createMarkAtCursorPosition(self):
        try:
            # colourDict = guiSettings.MARK_LINE_COLOUR_DICT  # maps atomName --> colour

            positions = [self.current.mouseMovedDict[AXIS_FULLATOMNAME][ax] for ax in self.axisCodes]
            defaultColour = self.application.preferences.general.defaultMarksColour
            self._project.newMark(defaultColour, positions, self.axisCodes)

        except Exception as es:
            getLogger().warning('Error setting mark at current cursor position')
            raise (es)

    # # TODO: remove apiRuler (when notifier at bottom of module gets rid of it)
    # def _initRulers(self):
    #
    #     for mark in self._project.marks:
    #         apiMark = mark._wrappedData
    #         for apiRuler in apiMark.rulers:
    #             self.plotWidget._addRulerLine(apiRuler)

    def _showMousePosition(self, pos: QtCore.QPointF):
        """Displays mouse position for both axes by axis code.
        """
        if self.isDeleted:
            return

        # position = self.viewBox.mapSceneToView(pos)
        try:
            # this only calls a single _wrapper function
            if self.orderedAxes[1] and self.orderedAxes[1].code == 'intensity':
                format = "%s: %.3f\n%s: %.4g"
            else:
                format = "%s: %.2f\n%s: %.2f"
        except:
            format = "%s: %.3f  %s: %.4g"

    def zoom(self, xRegion: typing.Tuple[float, float], yRegion: typing.Tuple[float, float]):
        """Zooms strip to the specified region.
        """
        try:
            self._CcpnGLWidget.zoom(xRegion, yRegion)
        except:
            getLogger().debugGL('OpenGL widget not instantiated')

    def zoomX(self, x1: float, x2: float):
        """
        Zooms x axis of strip to the specified region
        """
        padding = self.application.preferences.general.stripRegionPadding
        self.viewBox.setXRange(x1, x2, padding=padding)

    def zoomY(self, y1: float, y2: float):
        """Zooms y axis of strip to the specified region
        """
        padding = self.application.preferences.general.stripRegionPadding
        self.viewBox.setYRange(y1, y2, padding=padding)

    # def showZoomPopup(self):
    #     """
    #     Creates and displays a popup for zooming to a region in the strip.
    #     """
    #     zoomPopup = QtWidgets.QDialog()
    #
    #     Label(zoomPopup, text='x1', grid=(0, 0))
    #     x1LineEdit = FloatLineEdit(zoomPopup, grid=(0, 1))
    #     Label(zoomPopup, text='x2', grid=(0, 2))
    #     x2LineEdit = FloatLineEdit(zoomPopup, grid=(0, 3))
    #     Label(zoomPopup, text='y1', grid=(1, 0))
    #     y1LineEdit = FloatLineEdit(zoomPopup, grid=(1, 1))
    #     Label(zoomPopup, text='y2', grid=(1, 2))
    #     y2LineEdit = FloatLineEdit(zoomPopup, grid=(1, 3))
    #
    #     def _zoomTo():
    #         x1 = x1LineEdit.get()
    #         y1 = y1LineEdit.get()
    #         x2 = x2LineEdit.get()
    #         y2 = y2LineEdit.get()
    #         if None in (x1, y1, x2, y2):
    #             getLogger().warning('Zoom: must specify region completely')
    #             return
    #         self.zoomToRegion(xRegion=(x1, x2), yRegion=(y1, y2))
    #         zoomPopup.close()
    #
    #     Button(zoomPopup, text='OK', callback=_zoomTo, grid=(2, 0), gridSpan=(1, 2))
    #     Button(zoomPopup, text='Cancel', callback=zoomPopup.close, grid=(2, 2), gridSpan=(1, 2))
    #
    #     zoomPopup.exec_()

    # TODO. Set limit range properly for each case: 1D/nD, flipped axis
    # def setZoomLimits(self, xLimits, yLimits, factor=5):
    #   '''
    #
    #   :param xLimits: List [min, max], e.g ppm [0,15]
    #   :param yLimits:  List [min, max]  eg. intensities [-300,2500]
    #   :param factor:
    #   :return: Limits the viewBox from zooming in too deeply(crashing the program) to zooming out too far.
    #   '''
    #   ratio = (abs(xLimits[0] - xLimits[1])/abs(yLimits[0] - yLimits[1]))/factor
    #   if max(yLimits)>max(xLimits):
    #     self.viewBox.setLimits(xMin=-abs(min(xLimits)) * factor,
    #                            xMax=max(xLimits) * factor,
    #                            yMin=-abs(min(yLimits)) * factor,
    #                            yMax=max(yLimits) * factor,
    #                            minXRange=((max(xLimits) - min(xLimits))/max(xLimits)) * ratio,
    #                            maxXRange=max(xLimits) * factor,
    #                            minYRange=(((max(yLimits) - min(yLimits))/max(yLimits))),
    #                            maxYRange=max(yLimits) * factor
    #                            )
    #   else:
    #     self.viewBox.setLimits(xMin=-abs(min(xLimits)) * factor,
    #                            xMax=max(xLimits) * factor,
    #                            yMin=-abs(min(yLimits)) * factor,
    #                            yMax=max(yLimits) * factor,
    #                            minXRange=((max(xLimits) - min(xLimits))/max(xLimits)),
    #                            maxXRange=max(xLimits) * factor,
    #                            minYRange=(((max(yLimits) - min(yLimits))/max(yLimits)))*ratio,
    #                            maxYRange=max(yLimits) * factor
    #                            )

    # def removeZoomLimits(self):
    #   self.viewBox.setLimits(xMin=None,
    #                          xMax=None,
    #                          yMin=None,
    #                          yMax=None,
    #                          # Zoom Limits
    #                          minXRange=None,
    #                          maxXRange=None,
    #                          minYRange=None,
    #                          maxYRange=None
    #                          )

    def _storeZoom(self):
        """Adds current region to the zoom stack for the strip.
        """
        try:
            self._CcpnGLWidget.storeZoom()
        except:
            getLogger().debugGL('OpenGL widget not instantiated')

    def _restoreZoom(self):
        """Restores last saved region to the zoom stack for the strip.
        """
        try:
            self._CcpnGLWidget.restoreZoom()
        except:
            getLogger().debugGL('OpenGL widget not instantiated')

    def _setZoomPopup(self):
        from ccpn.ui.gui.popups.ZoomPopup import ZoomPopup

        popup = ZoomPopup(parent=self.mainWindow, mainWindow=self.mainWindow)
        popup.exec_()

    def resetZoom(self):
        try:
            self._CcpnGLWidget.resetZoom()
            self.pythonConsole.writeConsoleCommand("strip.resetZoom()", strip=self)
            getLogger().info("strip = application.getByGid('%s')\nstrip.resetZoom()" % self.pid)
        except:
            getLogger().debugGL('OpenGL widget not instantiated')

    def _zoomIn(self):
        """Zoom in to the strip.
        """
        try:
            self._CcpnGLWidget.zoomIn()
        except:
            getLogger().debugGL('OpenGL widget not instantiated')

    def _zoomOut(self):
        """Zoom out of the strip.
        """
        try:
            self._CcpnGLWidget.zoomOut()
        except:
            getLogger().debugGL('OpenGL widget not instantiated')

    def _resetRemoveStripAction(self):
        """Update interface when a strip is created or deleted.

          NB notifier is executed after deletion is final but before the wrapper is updated.
          len() > 1 check is correct also for delete
        """
        pass  # GWV: poor soultion self.spectrumDisplay._resetRemoveStripAction()

    def _moveToNextSpectrumView(self):
        # spectrumViews = self.orderedSpectrumViews()
        spectrumViews = self.spectrumDisplay.orderedSpectrumViews(self.spectrumViews)
        countSpvs = len(spectrumViews)
        if countSpvs > 0:
            visibleSpectrumViews = [i for i in spectrumViews if i.isVisible()]
            if len(visibleSpectrumViews) > 0:
                currentIndex = spectrumViews.index(visibleSpectrumViews[-1])
                if countSpvs > currentIndex + 1:
                    for visibleSpectrumView in visibleSpectrumViews:
                        visibleSpectrumView.setVisible(False)
                    spectrumViews[currentIndex + 1].setVisible(True)
                elif countSpvs == currentIndex + 1:  #starts again from the first
                    for visibleSpectrumView in visibleSpectrumViews:
                        visibleSpectrumView.setVisible(False)
                    spectrumViews[0].setVisible(True)
            else:
                spectrumViews[-1].setVisible(True)  #starts the loop again if none is selected
        else:
            MessageDialog.showWarning('Unable to select spectrum', 'Select a SpectrumDisplay with active spectra first')

    def _moveToPreviousSpectrumView(self):
        # spectrumViews = self.orderedSpectrumViews()
        spectrumViews = self.spectrumDisplay.orderedSpectrumViews(self.spectrumViews)
        countSpvs = len(spectrumViews)
        if countSpvs > 0:
            visibleSpectrumViews = [i for i in spectrumViews if i.isVisible()]
            if len(visibleSpectrumViews) > 0:
                currentIndex = spectrumViews.index(visibleSpectrumViews[0])
                # if countSpvs > currentIndex + 1:
                for visibleSpectrumView in visibleSpectrumViews:
                    visibleSpectrumView.setVisible(False)
                spectrumViews[currentIndex - 1].setVisible(True)
            else:
                spectrumViews[-1].setVisible(True)  # starts the loop again if none is selected

        else:
            MessageDialog.showWarning('Unable to select spectrum', 'Select a SpectrumDisplay with active spectra first')

    def _showAllSpectrumViews(self, value: bool = True):
        # spectrumViews = self.orderedSpectrumViews()
        spectrumViews = self.spectrumDisplay.orderedSpectrumViews(self.spectrumViews)
        for sp in spectrumViews:
            sp.setVisible(value)

    def _invertSelectedSpectra(self):
        # spectrumViews = self.orderedSpectrumViews()
        spectrumViews = self.spectrumDisplay.orderedSpectrumViews(self.spectrumViews)
        countSpvs = len(spectrumViews)
        if countSpvs > 0:

            visibleSpectrumViews = [i.isVisible() for i in spectrumViews]
            if any(visibleSpectrumViews):
                changeState = [i.setVisible(not i.isVisible()) for i in spectrumViews]
            else:
                self._showAllSpectrumViews(True)

    def report(self):
        """Generate a drawing object that can be added to reports
        :return reportlab drawing object:
        """
        if self._CcpnGLWidget:
            # from ccpn.ui.gui.lib.OpenGL.CcpnOpenGLExport import GLExporter

            glReport = self._CcpnGLWidget.exportToSVG()
            if glReport:
                return glReport.report()

    def axisRegionChanged(self, axis):
        """Notifier function: Update strips etc. for when axis position or width changes.
        """
        # axis = data[Notifier.OBJECT]
        strip = self  #axis.strip
        if not strip: return

        position = axis.position
        width = axis.width

        index = strip.axisOrder.index(axis.code)
        if not strip.beingUpdated and index > 1:
            strip.beingUpdated = True

            if len(strip.axisOrder) > 2:
                n = index - 2
                if n >= 0:
                    planeLabel = strip.planeToolbar.planeLabels[n]
                    planeSize = planeLabel.singleStep()
                    planeLabel.setValue(position)
                    strip.planeToolbar.planeCounts[n].setValue(width / planeSize)

        strip.beingUpdated = False

    def moveTo(self, newIndex: int):
        """Move strip to index newIndex in orderedStrips.
        """
        currentIndex = self._wrappedData.index
        if currentIndex == newIndex:
            return

        # get the current order
        stripCount = self.spectrumDisplay.stripCount

        if newIndex >= stripCount:
            # Put strip at the right, which means newIndex should be stripCount - 1
            if newIndex > stripCount:
                # warning
                raise TypeError("Attempt to copy strip to position %s in display with only %s strips"
                                % (newIndex, stripCount))
            newIndex = stripCount - 1

        with logCommandBlock(get='self') as log:
            log('moveTo')

            with undoStackBlocking() as addUndoItem:
                # needs to be first as it uses currentOrdering
                addUndoItem(undo=partial(self._resetStripLayout, newIndex, currentIndex))

            self._wrappedData.moveTo(newIndex)
            # reorder the strips in the layout
            self._resetStripLayout(currentIndex, newIndex)

            # add undo item to reorder the strips in the layout
            with undoStackBlocking() as addUndoItem:
                addUndoItem(redo=partial(self._resetStripLayout, currentIndex, newIndex))

    def _resetStripLayout(self, currentIndex, newIndex):
        # management of Qt layout
        # TBD: need to soup up below with extra loop when have tiles
        spectrumDisplay = self.spectrumDisplay
        layout = spectrumDisplay.stripFrame.layout()
        if not layout:  # should always exist but play safe:
            return

        for r in range(layout.rowCount()):
            items = []
            if spectrumDisplay.stripDirection == 'Y':
                if currentIndex < newIndex:
                    for n in range(currentIndex, newIndex + 1):
                        item = layout.itemAtPosition(r, n)
                        items.append(item)
                        layout.removeItem(item)
                    items = items[1:] + [items[0]]
                    for m, item in enumerate(items):
                        layout.addItem(item, r, m + currentIndex, )
                else:
                    for n in range(newIndex, currentIndex + 1):
                        item = layout.itemAtPosition(r, n)
                        items.append(item)
                        layout.removeItem(item)
                    items = [items[-1]] + items[:-1]
                    for m, item in enumerate(items):
                        layout.addItem(item, r, m + newIndex, )

            elif spectrumDisplay.stripDirection == 'X':
                if currentIndex < newIndex:
                    for n in range(currentIndex, newIndex + 1):
                        item = layout.itemAtPosition(n, 0)
                        items.append(item)
                        layout.removeItem(item)
                    items = items[1:] + [items[0]]
                    for m, item in enumerate(items):
                        layout.addItem(item, m + currentIndex, 0)
                else:
                    for n in range(newIndex, currentIndex + 1):
                        item = layout.itemAtPosition(n, 0)
                        items.append(item)
                        layout.removeItem(item)
                    items = [items[-1]] + items[:-1]
                    for m, item in enumerate(items):
                        layout.addItem(item, m + newIndex, 0)

        # rebuild the axes for each strip
        self.spectrumDisplay.showAxes(stretchValue=True, widths=False)

    def navigateToPosition(self, positions: typing.List[float],
                           axisCodes: typing.List[str] = None,
                           widths: typing.List[float] = None):
        from ccpn.ui.gui.lib.Strip import navigateToPositionInStrip

        navigateToPositionInStrip(self, positions, axisCodes, widths)

    def navigateToPeak(self, peak, widths: typing.List[float] = None):

        if peak:
            self.navigateToPosition(peak.position, peak.axisCodes)
        else:
            MessageDialog.showMessage('No Peak', 'Select a peak first')

    def _raiseContextMenu(self, event: QtGui.QMouseEvent):
        """
        Raise the context menu
        """

        position = event.screenPos()
        self.viewStripMenu.popup(QtCore.QPoint(int(position.x()),
                                               int(position.y())))
        self.contextMenuPosition = self.current.cursorPosition

    def _updateVisibility(self):
        """Update visibility list in the OpenGL
        """
        self._CcpnGLWidget.updateVisibleSpectrumViews()


# Notifiers:
def _updateDisplayedMarks(data):
    """Callback when marks have changed - Create, Change, Delete; defined above.
    """
    from ccpn.ui.gui.lib.OpenGL.CcpnOpenGL import GLNotifier

    GLSignals = GLNotifier(parent=None)
    GLSignals.emitEvent(triggers=[GLNotifier.GLMARKS])


def _updateSelectedPeaks(data):
    """Callback when peaks have changed.
    """
    from ccpn.ui.gui.lib.OpenGL.CcpnOpenGL import GLNotifier

    GLSignals = GLNotifier(parent=None)
    GLSignals.emitEvent(triggers=[GLNotifier.GLHIGHLIGHTPEAKS], targets=data[Notifier.OBJECT].peaks)


def _updateSelectedIntegrals(data):
    """Callback when integrals have changed.
    """
    from ccpn.ui.gui.lib.OpenGL.CcpnOpenGL import GLNotifier

    GLSignals = GLNotifier(parent=None)
    GLSignals.emitEvent(triggers=[GLNotifier.GLHIGHLIGHTINTEGRALS], targets=data[Notifier.OBJECT].integrals)


def _updateSelectedMultiplets(data):
    """Callback when multiplets have changed.
    """
    from ccpn.ui.gui.lib.OpenGL.CcpnOpenGL import GLNotifier

    GLSignals = GLNotifier(parent=None)
    GLSignals.emitEvent(triggers=[GLNotifier.GLHIGHLIGHTMULTIPLETS], targets=data[Notifier.OBJECT].multiplets)


def _axisRegionChanged(cDict):
    """Notifier function: Update strips etc. for when axis position or width changes.
    """
    axis = cDict[Notifier.OBJECT]
    strip = axis.strip

    position = axis.position
    width = axis.width
    region = (position - width / 2., position + width / 2.)

    index = strip.axisOrder.index(axis.code)
    if not strip.beingUpdated:

        strip.beingUpdated = True

        try:
            if index == 0:
                # X axis
                padding = strip.application.preferences.general.stripRegionPadding
                strip.viewBox.setXRange(*region, padding=padding)
            elif index == 1:
                # Y axis
                padding = strip.application.preferences.general.stripRegionPadding
                strip.viewBox.setYRange(*region, padding=padding)
            else:

                if len(strip.axisOrder) > 2:
                    n = index - 2
                    if n >= 0:
                        planeLabel = strip.planeToolbar.planeLabels[n]
                        planeSize = planeLabel.singleStep()
                        planeLabel.setValue(position)
                        strip.planeToolbar.planeCounts[n].setValue(width / planeSize)

        finally:
            strip.beingUpdated = False


# NB The following two notifiers could be replaced by wrapper notifiers on
# Mark, 'change'. But it would be rather more clumsy, so leave it as it is.

# NBNB TODO code uses API object. REFACTOR

# def _rulerCreated(project: Project, apiRuler: ApiRuler):
#     """Notifier function for creating rulers"""
#     for strip in project.strips:
#         strip.plotWidget._addRulerLine(apiRuler)


# def _rulerDeleted(project: Project, apiRuler: ApiRuler):
#     """Notifier function for deleting rulers"""
#     for strip in project.strips:
#         strip.plotWidget._removeRulerLine(apiRuler)


# Add notifier functions to Project


# NB This notifier must be implemented as an API postInit notifier,
# As it relies on Axs that are not yet created when 'created' notifiers are executed
def _setupGuiStrip(project: Project, apiStrip):
    """Set up graphical parameters for completed strips - for notifiers.
    """
    strip = project._data2Obj[apiStrip]
    try:
        strip._CcpnGLWidget.initialiseAxes(strip=strip)
        # strip._CcpnGLWidget._resetAxisRange()
    except:
        getLogger().debugGL('OpenGL widget not instantiated')
