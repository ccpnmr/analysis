"""
Module Documentation here
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2022"
__credits__ = ("Ed Brooksbank, Joanna Fox, Victoria A Higman, Luca Mureddu, Eliza Płoskoń",
               "Timothy J Ragan, Brian O Smith, Gary S Thompson & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2022-01-13 17:30:50 +0000 (Thu, January 13, 2022) $"
__version__ = "$Revision: 3.0.4 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from typing import List, Tuple, Sequence
from copy import deepcopy
from functools import partial

from PyQt5 import QtWidgets, QtCore, QtGui

from ccpn.core.Project import Project
from ccpn.core.Peak import Peak
from ccpn.core.PeakList import PeakList

from ccpn.core.lib.Notifiers import Notifier
from ccpn.core.lib.ContextManagers import undoStackBlocking, undoBlock, \
    notificationBlanking, undoBlockWithoutSideBar
from ccpn.ui.gui.guiSettings import getColours, CCPNGLWIDGET_HEXHIGHLIGHT, CCPNGLWIDGET_HEXFOREGROUND

from ccpn.util.Logging import getLogger
from ccpn.util.Constants import AXIS_MATCHATOMTYPE, AXIS_FULLATOMNAME, DOUBLEAXIS_FULLATOMNAME
from ccpn.util.decorators import logCommand
from ccpn.util.Colour import colorSchemeTable

from ccpn.ui.gui.guiSettings import GUISTRIP_PIVOT, ZPlaneNavigationModes
from ccpn.ui.gui.widgets.Frame import Frame
from ccpn.ui.gui.widgets.Widget import Widget
from ccpn.ui.gui.widgets.DropBase import DropBase
from ccpn.ui.gui.widgets import MessageDialog

from ccpn.ui.gui.lib.GuiNotifier import GuiNotifier
from ccpn.ui.gui.lib.OpenGL.CcpnOpenGLDefs import AXISXUNITS, AXISYUNITS, \
    SYMBOLTYPES, ANNOTATIONTYPES, SYMBOLSIZE, SYMBOLTHICKNESS, AXISASPECTRATIOS, AXISASPECTRATIOMODE, \
    BOTTOMAXIS, RIGHTAXIS, ALIASENABLED, ALIASSHADE, ALIASLABELSENABLED, CONTOURTHICKNESS, \
    PEAKLABELSENABLED, MULTIPLETLABELSENABLED

from ccpn.util.Constants import AXISUNIT_PPM, AXISUNIT_HZ, AXISUNIT_POINT


STRIPLABEL_ISPLUS = 'stripLabel_isPlus'
STRIP_MINIMUMWIDTH = 100
STRIP_MINIMUMHEIGHT = 150

DefaultMenu = 'DefaultMenu'
PeakMenu = 'PeakMenu'
IntegralMenu = 'IntegralMenu'
MultipletMenu = 'MultipletMenu'
AxisMenu = 'AxisMenu'
PhasingMenu = 'PhasingMenu'


class GuiStrip(Frame):
    # inherits NotifierBase

    optionsChanged = QtCore.pyqtSignal(dict)
    stripResized = QtCore.pyqtSignal(tuple)

    # MAXPEAKLABELTYPES = 6
    # MAXPEAKSYMBOLTYPES = 4

    def __init__(self, spectrumDisplay):
        """
        Basic graphics strip class; used in StripNd and Strip1d

        :param spectrumDisplay: spectrumDisplay instance

        This module inherits attributes from the Strip wrapper class:
        Use clone() method to make a copy
        """

        # For now, cannot set spectrumDisplay attribute as it is owned by the wrapper class
        # self.spectrumDisplay = spectrumDisplay
        self.mainWindow = self.spectrumDisplay.mainWindow
        self.application = self.mainWindow.application
        self.current = self.application.current

        super().__init__(parent=spectrumDisplay.stripFrame, setLayout=True, showBorder=False,
                         spacing=(0, 0), acceptDrops=True  #, hPolicy='expanding', vPolicy='expanding' ##'minimal'
                         )

        self.setMinimumWidth(STRIP_MINIMUMWIDTH)
        self.setMinimumHeight(STRIP_MINIMUMHEIGHT)

        # stripArrangement = getattr(self.spectrumDisplay, 'stripArrangement', None)
        # if stripArrangement == 'X':
        #     headerGrid = (0, 0)
        #     openGLGrid = (0, 1)
        #     stripToolBarGrid = (0, 2)
        # else:
        #     headerGrid = (0, 0)
        #     openGLGrid = (1, 0)
        #     stripToolBarGrid = (2, 0)

        headerGrid = (0, 0)
        headerSpan = (1, 5)
        openGLGrid = (1, 0)
        openGlSpan = (10, 5)
        stripToolBarGrid = (11, 0)
        stripToolBarSpan = (1, 5)

        if spectrumDisplay.is1D:
            from ccpn.ui.gui.widgets.GLWidgets import Gui1dWidget as CcpnGLWidget
        else:
            from ccpn.ui.gui.widgets.GLWidgets import GuiNdWidget as CcpnGLWidget

        self._CcpnGLWidget = CcpnGLWidget(strip=self, mainWindow=self.mainWindow)

        self.getLayout().addWidget(self._CcpnGLWidget, *openGLGrid, *openGlSpan)
        self._CcpnGLWidget.setSizePolicy(QtWidgets.QSizePolicy.Expanding,
                                         QtWidgets.QSizePolicy.Expanding)

        self.stripLabel = None
        self.header = None  #StripHeader(parent=self, mainWindow=self.mainWindow, strip=self,
        # grid=headerGrid, gridSpan=headerSpan, setLayout=True, spacing=(0, 0))

        # set the ID label in the new widget
        self._CcpnGLWidget.setStripID('.'.join(self.pid.split('.')))
        # self._CcpnGLWidget.setStripID('')

        # Widgets for toolbar; items will be added by GuiStripNd (e.g. the Z/A-plane boxes)
        # and GuiStrip1d; will be hidden for 2D's by GuiSpectrumView
        self._stripToolBarWidget = Widget(parent=self, setLayout=True,
                                          grid=stripToolBarGrid, gridSpan=stripToolBarSpan)
        self._stripToolBarWidget.getLayout().setSizeConstraint(QtWidgets.QLayout.SetFixedSize)

        self.viewStripMenu = None
        self.storedZooms = []
        # self.beingUpdated = False
        self.planeAxisBars = ()

        # need to keep track of mouse position because Qt shortcuts don't provide
        # the widget or the position of where the cursor is
        self.axisPositionDict = {}  # axisCode --> position

        self._contextMenuMode = DefaultMenu
        self._contextMenus = {DefaultMenu  : None,
                              PeakMenu     : None,
                              PhasingMenu  : None,
                              MultipletMenu: None,
                              IntegralMenu : None,
                              AxisMenu     : None
                              }

        self.navigateToPeakMenu = None  #set from context menu and in CcpnOpenGL rightClick
        self.navigateToCursorMenu = None  #set from context menu and in CcpnOpenGL rightClick
        self._isPhasingOn = False

        self._preferences = self.application.preferences.general

        # set symbolLabelling to the default from preferences or strip to the left
        settings = spectrumDisplay._getSettingsDict()
        if len(spectrumDisplay.strips) > 1:

            _firstStrip = spectrumDisplay.strips[0]

            # copy the values from the first strip
            self.symbolLabelling = min(_firstStrip.symbolLabelling, self.spectrumDisplay.MAXPEAKLABELTYPES - 1)
            self.symbolType = min(_firstStrip.symbolType, self.spectrumDisplay.MAXPEAKSYMBOLTYPES - 1)
            self.symbolSize = _firstStrip.symbolSize
            self.symbolThickness = _firstStrip.symbolThickness
            self.aliasEnabled = _firstStrip.aliasEnabled
            self.aliasShade = _firstStrip.aliasShade
            self.aliasLabelsEnabled = _firstStrip.aliasLabelsEnabled
            self.contourThickness = _firstStrip.contourThickness
            self.peakLabelsEnabled = _firstStrip.peakLabelsEnabled
            self.multipletLabelsEnabled = _firstStrip.multipletLabelsEnabled

            self.gridVisible = _firstStrip.gridVisible
            self.crosshairVisible = _firstStrip.crosshairVisible
            self.doubleCrosshairVisible = _firstStrip.doubleCrosshairVisible
            self.sideBandsVisible = _firstStrip.sideBandsVisible

            self.showSpectraOnPhasing = _firstStrip.showSpectraOnPhasing
            self._spectrumBordersVisible = _firstStrip._spectrumBordersVisible

            if spectrumDisplay.stripArrangement == 'Y':
                if self.spectrumDisplay.lastAxisOnly:
                    self.setAxesVisible(False, True)
                else:
                    self.setAxesVisible(True, True)
            elif spectrumDisplay.stripArrangement == 'X':
                if self.spectrumDisplay.lastAxisOnly:
                    self.setAxesVisible(True, False)
                else:
                    self.setAxesVisible(True, True)

            # set the axis units from the current settings
            # self.xUnits = _firstStrip.xUnits
            # self.yUnits = _firstStrip.yUnits
            # self._CcpnGLWidget._useLockedAspect = spectrumDisplay.strips[0]._CcpnGLWidget._useLockedAspect

        else:

            # get the values from the preferences
            self.gridVisible = self._preferences.showGrid
            self.crosshairVisible = self._preferences.showCrosshair
            self.doubleCrosshairVisible = self._preferences.showDoubleCrosshair
            self.sideBandsVisible = self._preferences.showSideBands

            self.showSpectraOnPhasing = self._preferences.showSpectraOnPhasing
            self._spectrumBordersVisible = self._preferences.showSpectrumBorder

            # get the values from the settings (check in case the number of states has changed)
            self.symbolLabelling = min(settings[ANNOTATIONTYPES], self.spectrumDisplay.MAXPEAKLABELTYPES - 1)
            self.symbolType = min(settings[SYMBOLTYPES], self.spectrumDisplay.MAXPEAKSYMBOLTYPES - 1)
            self.symbolSize = settings[SYMBOLSIZE]
            self.symbolThickness = settings[SYMBOLTHICKNESS]
            self.contourThickness = settings[CONTOURTHICKNESS]
            self.aliasEnabled = settings[ALIASENABLED]
            self.aliasShade = settings[ALIASSHADE]
            self.aliasLabelsEnabled = settings[ALIASLABELSENABLED]
            self.peakLabelsEnabled = settings[PEAKLABELSENABLED]
            self.multipletLabelsEnabled = settings[MULTIPLETLABELSENABLED]

            self.spectrumDisplay._setFloatingAxes(xUnits=settings[AXISXUNITS],
                                                  yUnits=settings[AXISYUNITS],
                                                  aspectRatioMode=settings[AXISASPECTRATIOMODE],
                                                  aspectRatios=settings[AXISASPECTRATIOS])

            self.setAxesVisible(True, True)

            # set the axis units from the current settings
            # self.xUnits = settings[AXISXUNITS]
            # self.yUnits = settings[AXISYUNITS]

        self._CcpnGLWidget._aspectRatioMode = settings[AXISASPECTRATIOMODE]
        self._CcpnGLWidget._aspectRatios = deepcopy(settings[AXISASPECTRATIOS])
        self._CcpnGLWidget._applyXLimit = self._preferences.zoomXLimitApply
        self._CcpnGLWidget._applyYLimit = self._preferences.zoomYLimitApply

        self._storedPhasingData = [[0.0, 0.0, 0.0], [0.0, 0.0, 0.0]]
        self.showActivePhaseTrace = True
        self.pivotLine = None
        self._lastClickedObjects = None
        self._newPosition = None

        self._hTraceActive = False
        self._vTraceActive = False
        self._newConsoleDirection = None

        # initialise the notifiers
        self.setStripNotifiers()

        # test aliasing notifiers
        # self._currentVisibleAliasingRange = {}
        # self._currentAliasingRange = {}

        # respond to values changed in the containing spectrumDisplay settings widget
        self.spectrumDisplay._spectrumDisplaySettings.symbolsChanged.connect(self._symbolsChangedInSettings)

    def resizeEvent(self, ev):
        super().resizeEvent(ev)
        # call subclass _resize event
        self._resize()
        self.stripResized.emit((self.width(), self.height()))

    def _resize(self):
        """Resize event to handle resizing of frames that overlay the OpenGL frame
        """
        # MUST BE SUBCLASSED
        raise NotImplementedError("Code error: function not implemented")

    def _selectCallback(self, widgets):
        # print('>>>select', widget1, widget2)
        # if the first widget is clicked then toggle the planeToolbar buttons
        if widgets[3].isVisible():
            widgets[3].hide()
            widgets[1].show()
        else:
            widgets[1].hide()
            widgets[3].show()
        self._resize()

    def _enterCallback(self, widget1, widget2):
        # print('>>>_enterCallback', widget1, widget2)
        pass

    def _leaveCallback(self, widget1, widget2):
        # print('>>>_leaveCallback', widget1, widget2)
        # widget2.hide()
        widget1.show()

    def setStripNotifiers(self):
        """Set the notifiers for the strip.
        """
        # GWV 20181127: moved to GuiMainWindow
        # GWV 20181127: moved to GuiMainWindow
        # notifier for highlighting the strip
        # self._stripNotifier = Notifier(self.current, [Notifier.CURRENT], 'strip', self._highlightCurrentStrip)

        # Notifier for updating the peaks
        self.setNotifier(self.project, [Notifier.CREATE, Notifier.DELETE, Notifier.CHANGE],
                         'Peak', self._updateDisplayedPeaks, onceOnly=True)

        self.setNotifier(self.project, [Notifier.CREATE, Notifier.DELETE, Notifier.RENAME],
                         'NmrAtom', self._updateDisplayedNmrAtoms, onceOnly=True)

        # Notifier for updating the integrals
        self.setNotifier(self.project, [Notifier.CREATE, Notifier.DELETE, Notifier.CHANGE],
                         'Integral', self._updateDisplayedIntegrals, onceOnly=True)

        # Notifier for updating the multiplets
        self.setNotifier(self.project, [Notifier.CREATE, Notifier.DELETE, Notifier.CHANGE],
                         'Multiplet', self._updateDisplayedMultiplets, onceOnly=True)

        # Notifier for change of stripLabel
        self.setNotifier(self.project, [Notifier.RENAME], 'Spectrum', self._updateSpectrumLabels)

        # # Notifier for change of stripLabel
        # self.setNotifier(self.project, [Notifier.RENAME], 'NmrResidue', self._updateStripLabel)

        # For now, all dropEvents are not strip specific, use spectrumDisplay's handling
        self.setGuiNotifier(self, [GuiNotifier.DROPEVENT], [DropBase.URLS, DropBase.PIDS],
                            self.spectrumDisplay._processDroppedItems)

    def viewRange(self):
        return self._CcpnGLWidget.viewRange()

    @property
    def gridVisible(self):
        """True if grid is visible.
        """
        return self._CcpnGLWidget._gridVisible

    @gridVisible.setter
    def gridVisible(self, visible):
        """set the grid visibility
        """
        if hasattr(self, 'gridAction'):
            self.gridAction.setChecked(visible)
        self._CcpnGLWidget._gridVisible = visible

        # spawn a redraw of the GL windows
        self._CcpnGLWidget.GLSignals.emitPaintEvent()

    # GWV 07/01/2022: removed
    # @property
    # def xUnits(self):
    #     """Current xUnits
    #     """
    #     return self._CcpnGLWidget._xUnits
    #
    # @xUnits.setter
    # def xUnits(self, units):
    #     """set the xUnits
    #     """
    #     self._CcpnGLWidget._xUnits = units
    #
    #     # spawn a redraw of the GL windows
    #     self._CcpnGLWidget.GLSignals.emitPaintEvent()
    #
    # @property
    # def yUnits(self):
    #     """Current yUnits
    #     """
    #     return self._CcpnGLWidget._yUnits
    #
    # @yUnits.setter
    # def yUnits(self, units):
    #     """set the yUnits
    #     """
    #     self._CcpnGLWidget._yUnits = units
    #
    #     # spawn a redraw of the GL windows
    #     self._CcpnGLWidget.GLSignals.emitPaintEvent()

    @property
    def sideBandsVisible(self):
        """True if sideBands are visible.
        """
        return self._CcpnGLWidget._sideBandsVisible

    @sideBandsVisible.setter
    def sideBandsVisible(self, visible):
        """set the sideBands visibility
        """
        if hasattr(self, 'sideBandsAction'):
            self.sideBandsAction.setChecked(visible)
        self._CcpnGLWidget._sideBandsVisible = visible

        # spawn a redraw of the GL windows
        self._CcpnGLWidget.GLSignals.emitPaintEvent()

    @property
    def spectrumBordersVisible(self):
        """True if spectrumBorders are visible.
        """
        return self._CcpnGLWidget._spectrumBordersVisible

    @spectrumBordersVisible.setter
    def spectrumBordersVisible(self, visible):
        """set the spectrumBorders visibility
        """
        if hasattr(self, 'spectrumBordersAction'):
            self.spectrumBordersAction.setChecked(visible)
        self._CcpnGLWidget._spectrumBordersVisible = visible

        # spawn a redraw of the GL windows
        self._CcpnGLWidget.GLSignals.emitPaintEvent()

    def toggleGrid(self):
        """Toggles whether grid is visible in the strip.
        """
        self.gridVisible = not self._CcpnGLWidget._gridVisible

    def toggleSideBands(self):
        """Toggles whether sideBands are visible in the strip.
        """
        self.sideBandsVisible = not self._CcpnGLWidget._sideBandsVisible

    @property
    def crosshairVisible(self):
        """True if crosshair is visible.
        """
        return self._CcpnGLWidget._crosshairVisible

    @crosshairVisible.setter
    def crosshairVisible(self, visible):
        """set the crosshairVisible visibility
        """
        if hasattr(self, 'crosshairAction'):
            self.crosshairAction.setChecked(visible)
        self._CcpnGLWidget._crosshairVisible = visible

        # spawn a redraw of the GL windows
        self._CcpnGLWidget.GLSignals.emitPaintEvent()

    def _toggleCrosshair(self):
        """Toggles whether crosshair is visible.
        """
        self.crosshairVisible = not self._CcpnGLWidget._crosshairVisible

    def _showCrosshair(self):
        """Displays crosshair in strip.
        """
        self.crosshairVisible = True

    def _hideCrosshair(self):
        """Hides crosshair in strip.
        """
        self.crosshairVisible = False

    def _crosshairCode(self, axisCode):
        """Determines what axisCodes are compatible as far as drawing crosshair is concerned
        TBD: the naive approach below should be improved
        """
        return axisCode  #if axisCode[0].isupper() else axisCode

    @property
    def doubleCrosshairVisible(self):
        """True if doubleCrosshair is visible.
        """
        return self._CcpnGLWidget._doubleCrosshairVisible

    @doubleCrosshairVisible.setter
    def doubleCrosshairVisible(self, visible):
        """set the doubleCrosshairVisible visibility
        """
        if hasattr(self, 'doubleCrosshairAction'):
            self.doubleCrosshairAction.setChecked(visible)
        self._CcpnGLWidget._doubleCrosshairVisible = visible

        # spawn a redraw of the GL windows
        self._CcpnGLWidget.GLSignals.emitPaintEvent()

    def _toggleDoubleCrosshair(self):
        """Toggles whether doubleCrosshair is visible.
        """
        self.doubleCrosshairVisible = not self._CcpnGLWidget._doubleCrosshairVisible

    # GWV; commented 24/12/21
    # @property
    # def pythonConsole(self):
    #     return self.mainWindow.pythonConsole

    def _showPeakOnPLTable(self):
        current = self.application.current
        peaks = current.peaks
        clickedPeaks = self._lastClickedObjects

        if not (peaks or clickedPeaks):
            return
        if len(peaks) == 1:
            peak = peaks[-1]
            peakTableModule = self.application.showPeakTable(peakList=peak.peakList)

    def setStackingMode(self, value):
        pass

    def getStackingMode(self):
        pass

    def _updateStripLabel(self, callbackDict):
        """Update the striplabel if it represented a NmrResidue that has changed its id.
        """
        # self.header.processNotifier(callbackDict)
        pass

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
                                   orderedSpectrumViews=self.getSpectrumViews())
        popup.exec_()
        popup._cleanupWidget()

    def makeStripPlot(self, includePeakLists=True, includeNmrChains=True, includeSpectrumTable=False):
        """Make a strip plot in the current spectrumDisplay
        """
        from ccpn.ui.gui.popups.StripPlotPopup import StripPlotPopup

        popup = StripPlotPopup(parent=self.mainWindow, mainWindow=self.mainWindow, spectrumDisplay=self.spectrumDisplay,
                               includePeakLists=includePeakLists, includeNmrChains=includeNmrChains, includeSpectrumTable=includeSpectrumTable)
        popup.exec_()
        popup._cleanupWidget()

    def calibrateFromPeaks(self):
        if self.current.peaks and len(self.current.peaks) > 1:

            if not (self._lastClickedObjects and isinstance(self._lastClickedObjects, Sequence)):
                MessageDialog.showMessage('Calibrate error', 'Select a single peak as the peak to calibrate to.')
                return
            else:
                if len(self._lastClickedObjects) > 1:
                    MessageDialog.showMessage('Too Many Peaks', 'Select a single peak as the peak to calibrate to.')
                    return

            # make sure that selected peaks are unique in each spectrum
            spectrumCount = {}
            for peak in self.current.peaks:
                if peak.peakList.spectrum in spectrumCount:
                    MessageDialog.showMessage('Too Many Peaks', 'Only select one peak in each spectrum')
                    break
                else:
                    spectrumCount[peak.peakList.spectrum] = peak

            else:
                # popup to calibrate from selected peaks in this display
                from ccpn.ui.gui.popups.CalibrateSpectraFromPeaksPopup import CalibrateSpectraFromPeaksPopupNd, CalibrateSpectraFromPeaksPopup1d

                if self.spectrumDisplay.is1D:
                    popup = CalibrateSpectraFromPeaksPopup1d(parent=self.mainWindow, mainWindow=self.mainWindow,
                                                             strip=self, spectrumCount=spectrumCount)
                else:
                    popup = CalibrateSpectraFromPeaksPopupNd(parent=self.mainWindow, mainWindow=self.mainWindow,
                                                             strip=self, spectrumCount=spectrumCount)

                popup.exec_()

        else:
            MessageDialog.showMessage('Not Enough Peaks', 'Select more than one peak, only one per spectrum')

    def close(self):
        self.deleteAllNotifiers()
        super().close()

    def _updateSpectrumLabels(self, data):
        """Callback when spectra have changed
        """
        self._CcpnGLWidget._processSpectrumNotifier(data)

    def _updateDisplayedPeaks(self, data):
        """Callback when peaks have changed
        """
        self._CcpnGLWidget._processPeakNotifier(data)

    def _updateDisplayedNmrAtoms(self, data):
        """Callback when nmrAtoms have changed
        """
        self._CcpnGLWidget._processNmrAtomNotifier(data)

    def _updateDisplayedMultiplets(self, data):
        """Callback when multiplets have changed
        """
        self._CcpnGLWidget._processMultipletNotifier(data)

    def refreshDevicePixelRatio(self):
        """Set the devicePixel ratio in the GL window
        """
        self._CcpnGLWidget.refreshDevicePixelRatio()

    def refresh(self):
        """Refresh the display for strip and redraw contours
        """
        self._CcpnGLWidget._updateVisibleSpectrumViews()

        # redraw the contours
        from ccpn.ui.gui.lib.OpenGL.CcpnOpenGL import GLNotifier

        GLSignals = GLNotifier(parent=self)

        for specNum, thisSpecView in enumerate(self.spectrumViews):
            thisSpecView.buildContours = True

        GLSignals.emitPaintEvent()

    def _checkMenuItems(self):
        """Update the menu check boxes from the strip
        Subclass if options needed, e.g. stackSpectra item
        """
        pass

    def _createMenuItemForNavigate(self, currentStrip, navigateAxes, navigatePos, showPos, strip, menuFunc, label, includeAxisCodes=True):
        from ccpn.ui.gui.lib.StripLib import navigateToPositionInStrip

        if includeAxisCodes:
            item = ', '.join([cc + ":" + str(x if isinstance(x, str) else round(x, 3)) for x, cc in zip(showPos, strip.axisCodes)])
        else:
            item = ', '.join([str(x if isinstance(x, str) else round(x, 3)) for x in showPos])

        text = '%s (%s)' % (strip.pid, item)
        toolTip = 'Show cursor in strip %s at %s position (%s)' % (str(strip.id), label, item)
        # if len(list(set(strip.axisCodes) & set(currentStrip.axisCodes))) > 0:
        menuFunc.addItem(text=text,
                         callback=partial(navigateToPositionInStrip, strip=strip,
                                          positions=navigatePos,
                                          axisCodes=navigateAxes, ),
                         toolTip=toolTip)
        # else:
        #     print('skipping axisCodes %s %s' % (strip.axisCodes, currentStrip.axisCodes))

    def _createCommonMenuItem(self, currentStrip, includeAxisCodes, label, menuFunc, perm, position, strip):
        showPos = []
        navigatePos = []
        navigateAxes = []
        for jj, ii in enumerate(perm):
            if ii is not None:
                showPos.append(position[ii])
                navigatePos.append(position[ii])
                navigateAxes.append(strip.axisCodes[jj])
            else:
                showPos.append(' - ')
        self._createMenuItemForNavigate(currentStrip, navigateAxes, navigatePos, showPos, strip, menuFunc, label,
                                        includeAxisCodes=includeAxisCodes)

    def _addItemsToNavigateMenu(self, position, axisCodes, label, menuFunc, includeAxisCodes=True):
        """Adds item to navigate to section of context menu.
        """
        from ccpn.core.lib.AxisCodeLib import getAxisCodeMatchIndices
        from itertools import product

        if not menuFunc:
            return

        menuFunc.clear()
        currentStrip = self

        if len(self.current.project.spectrumDisplays) > 0:
            menuFunc.setEnabled(True)

            # matchingItemAdded = False
            for spectrumDisplay in self.current.project.spectrumDisplays:
                for strip in spectrumDisplay.strips:

                    # add the opposite diagonals for matching axisCodes - always at the top of the list
                    if strip == currentStrip:

                        indices = getAxisCodeMatchIndices(strip.axisCodes, axisCodes, allMatches=False)
                        allIndices = getAxisCodeMatchIndices(strip.axisCodes, axisCodes, allMatches=True)
                        permutationList1 = [jj for jj in product(*(ii if ii else (None,) for ii in allIndices)) if len(set(jj)) == len(strip.axisCodes)]
                        for perm in permutationList1:

                            # skip any that match the original indexing
                            if any(ii != jj for ii, jj in zip(perm, indices)):
                                self._createCommonMenuItem(currentStrip, includeAxisCodes, label, menuFunc, perm, position, strip)
                        menuFunc.addSeparator()

                        # try:
                        #     # flip the first two axes, easy to do it here
                        #     flipAxisCodes = [strip.axisCodes[1], strip.axisCodes[0]] + list(strip.axisCodes[2:])
                        #
                        #     # get a list of all isotope code matches for each axis code in 'strip' matched to the flipped axes
                        #     perm = getAxisCodeMatchIndices(flipAxisCodes, axisCodes, allMatches=False)
                        #
                        #     self._createCommonMenuItem(currentStrip, includeAxisCodes, label, menuFunc, perm, position, strip)
                        #     menuFunc.addSeparator()
                        #     # matchingItemAdded = True
                        #
                        # except Exception as es:
                        #     # just skip if an error (but there shouldn't be any here)
                        #     pass

            # if not matchingItemAdded:
            #     print('>>> skipping menuitem')
            #     menuFunc.addItem(text='Skip matching isotopeCodes')
            #     menuFunc.addSeparator()

            for spectrumDisplay in self.current.project.spectrumDisplays:
                for strip in spectrumDisplay.strips:
                    if strip != currentStrip:

                        # get a list of all isotope code matches for each axis code in 'strip'
                        indices = getAxisCodeMatchIndices(strip.axisCodes, axisCodes, allMatches=True)

                        # generate a permutation list of the axis codes that have unique indices
                        # permutation list is list of tuples
                        # each element is list of indices to fetch from currentStrip and map to strip

                        # permutationList1 = [jj for jj in product(*(ii if ii else (None,) for ii in indices)) if len(set(jj)) == len(strip.axisCodes)]
                        permutationList1 = [jj for jj in product(*(ii if ii else (None,) for ii in indices))]  # if len(set(jj)) == len(strip.axisCodes)]

                        # print('>>>', strip.pid, indices)
                        for perm in permutationList1:
                            perm2 = [pp if pp is not None else -(cc + 1) for cc, pp in enumerate(perm)]
                            # print('>>>    ', perm, perm2)

                            if len(set(perm2)) == len(perm2):  # ignore None's
                                self._createCommonMenuItem(currentStrip, includeAxisCodes, label, menuFunc, perm, position, strip)

                        # menuFunc.addItem(text=' - ')

                        permutationList2 = [jj for jj in product(*(ii if ii else (None,) for ii in indices)) if len(set(jj)) == len(jj)]
                        if not permutationList2:

                            perm = list(getAxisCodeMatchIndices(strip.axisCodes, axisCodes, allMatches=False))

                            from collections import Counter
                            from itertools import product

                            maxIndexList = Counter(perm).most_common(1)
                            if maxIndexList:
                                index, maxCount = maxIndexList[0]
                                if index is not None:

                                    # iterate through all permutations of index/None
                                    combiList = [list(i) for i in product([None, index], repeat=maxCount)]
                                    indices = [ii for ii in range(len(perm)) if perm[ii] == index]

                                    # add all permutations except first (all unset)
                                    for combi in combiList[1:]:
                                        for ind, val in zip(indices, combi):
                                            perm[ind] = val

                                        self._createCommonMenuItem(currentStrip, includeAxisCodes, label, menuFunc, perm, position, strip)

                menuFunc.addSeparator()
        else:
            menuFunc.setEnabled(False)

    def _addItemsToNavigateToPeakMenu(self, peaks):
        """Adds item to navigate to peak position from context menu.
        """
        if peaks and self._navigateToPeakMenuSelected:
            self._addItemsToNavigateMenu(peaks[0].position, peaks[0].axisCodes, 'Peak', self._navigateToPeakMenuSelected, includeAxisCodes=True)

    def _addItemsToNavigateToCursorPosMenu(self):
        """Copied from old viewbox. This function apparently take the current cursorPosition
         and uses to pan a selected display from the list of spectrumViews or the current cursor position.
        """
        if self.navigateCursorMenu:
            position = [self.current.mouseMovedDict[AXIS_FULLATOMNAME][ax]
                        if ax in self.current.mouseMovedDict[AXIS_FULLATOMNAME] else None
                        for ax in self.axisCodes]
            if None in position:
                return

            self._addItemsToNavigateMenu(position, self.axisCodes, 'Cursor', self.navigateCursorMenu, includeAxisCodes=True)

    def markAxisIndices(self, indices=None):
        """Mark the X/Y/XY axisCodes by index
        """
        position = [self.current.mouseMovedDict[AXIS_FULLATOMNAME][ax] for ax in self.axisCodes]
        if indices is None:
            indices = tuple(range(len(self.axisCodes)))

        pos = [position[ii] for ii in indices]
        axes = [self.axisCodes[ii] for ii in indices]

        self._createMarkAtPosition(positions=pos, axisCodes=axes)

    def _addItemsToMenu(self, position, axisCodes, label, menuFunc):
        """Adds item to mark peak position from context menu.
        """
        from functools import partial

        if hasattr(self, 'markIn%sMenu' % label):
            menuFunc.clear()
            currentStrip = self

            if currentStrip:
                if len(self.current.project.spectrumDisplays) > 1:
                    menuFunc.setEnabled(True)
                    for spectrumDisplay in self.current.project.spectrumDisplays:
                        for strip in spectrumDisplay.strips:
                            if strip != currentStrip:
                                toolTip = 'Show cursor in strip %s at %s position %s' % (str(strip.id), label, str([round(x, 3) for x in position]))
                                if len(list(set(strip.axisCodes) & set(currentStrip.axisCodes))) <= 4:
                                    menuFunc.addItem(text=strip.pid,
                                                     callback=partial(self._createMarkAtPosition,
                                                                      positions=position,
                                                                      axisCodes=axisCodes),
                                                     toolTip=toolTip)
                        menuFunc.addSeparator()
                else:
                    menuFunc.setEnabled(False)

    def _addItemsToMarkInPeakMenu(self, peaks):
        """Adds item to mark peak position from context menu.
        """
        if peaks and hasattr(self, 'markInPeakMenu'):
            self._addItemsToMenu(peaks[0].position, peaks[0].axisCodes, 'Peak', self.markInPeakMenu)

    def _addItemsToMarkInCursorPosMenu(self):
        """Copied from old viewbox. This function apparently take the current cursorPosition
         and uses to pan a selected display from the list of spectrumViews or the current cursor position.
        """
        if hasattr(self, 'markInCursorMenu'):
            self._addItemsToMenu(self.current.cursorPosition, self.axisCodes, 'Cursor', self.markInCursorMenu)

    def _markSelectedPeaks(self, axisIndex=None):
        """Mark the positions of all selected peaks
        """
        with undoBlockWithoutSideBar():
            for peak in self.current.peaks:
                self._createObjectMark(peak, axisIndex)

    def _markSelectedMultiplets(self, axisIndex=None):
        """Mark the positions of all selected multiplets
        """
        with undoBlockWithoutSideBar():
            for multiplet in self.current.multiplets:
                self._createObjectMark(multiplet, axisIndex)

    def _addItemsToCopyAxisFromMenusMainView(self):
        """Setup the menu for the main view
        """
        # self._addItemsToCopyAxisFromMenus([self.copyAllAxisFromMenu, self.copyXAxisFromMenu, self.copyYAxisFromMenu],
        #                                    ['All', 'X', 'Y'])
        self._addItemsToCopyAxisFromMenus(((self.copyAllAxisFromMenu, 'All'),
                                           (self.copyXAxisFromMenu, 'X'),
                                           (self.copyYAxisFromMenu, 'Y')))

    def _addItemsToCopyAxisFromMenusAxes(self, viewPort, thisMenu, is1D):
        """Setup the menu for the axis views
        """
        from ccpn.ui.gui.lib.GuiStripContextMenus import _addCopyMenuItems

        copyAttribs, matchAttribs = _addCopyMenuItems(self, viewPort, thisMenu, is1D)

        self._addItemsToCopyAxisFromMenus(copyAttribs)
        for nm, ax in matchAttribs:
            self._addItemsToCopyAxisCodesFromMenus(ax, nm)

    def _addItemsToCopyAxisFromMenus(self, copyAttribs):  #, axisNames, axisIdList):
        """Copied from old viewbox. This function apparently take the current cursorPosition
         and uses to pan a selected display from the list of spectrumViews or the current cursor position.
        """
        # TODO needs clear documentation
        from functools import partial

        axisNames = tuple(nm[0] for nm in copyAttribs)
        axisIdList = tuple(nm[1] for nm in copyAttribs)

        for axisName, axisId in zip(axisNames, axisIdList):
            if axisName:
                axisName.clear()
                currentStrip = self.current.strip
                position = self.current.cursorPosition

                count = 0
                if currentStrip:
                    for spectrumDisplay in self.current.project.spectrumDisplays:
                        for strip in spectrumDisplay.strips:
                            if strip != currentStrip:
                                toolTip = 'Copy %s axis range from strip %s' % (str(axisId), str(strip.id))
                                if len(list(set(strip.axisCodes) & set(currentStrip.axisCodes))) <= 4:
                                    axisName.addItem(text=strip.pid,
                                                     callback=partial(self._copyAxisFromStrip,
                                                                      axisId=axisId, fromStrip=strip, ),
                                                     toolTip=toolTip)
                                    count += 1
                        axisName.addSeparator()

                axisName.setEnabled(True if count else False)

    def _addItemsToMarkAxesMenuAxesView(self, viewPort, thisMenu):
        """Setup the menu for the main view for marking axis codes
        """
        indices = {BOTTOMAXIS: (0,), RIGHTAXIS: (1,)}
        if viewPort in indices.keys():
            self._addItemsToMarkAxesMenuMainView(thisMenu, indices[viewPort])

    def _addItemsToMarkAxesMenuMainView(self, axisMenu=None, indices=None):
        """Setup the menu for the main view for marking axis codes
        """
        axisName = axisMenu if axisMenu else self.markAxesMenu
        position = [self.current.mouseMovedDict[AXIS_FULLATOMNAME][ax]
                    if ax in self.current.mouseMovedDict[AXIS_FULLATOMNAME] else None
                    for ax in self.axisCodes]
        if None in position:
            return

        row = 0
        if indices is None:
            # get the indices to add to the menu
            indices = tuple(range(len(self.axisCodes)))

            pos = [position[ii] for ii in indices]
            axes = [self.axisCodes[ii] for ii in indices]

            toolTip = 'Mark all axis codes'
            axisName.addItem(text='Mark All AxisCodes',
                             callback=partial(self._createMarkAtPosition, positions=pos, axisCodes=axes, ),
                             toolTip=toolTip)
            row += 1

        for ind in indices:
            pos = [position[ind], ]
            axes = [self.axisCodes[ind], ]

            toolTip = 'Mark %s axis code' % str(self.axisCodes[ind])
            axisName.addItem(text='Mark %s' % str(self.axisCodes[ind]),
                             callback=partial(self._createMarkAtPosition, positions=pos, axisCodes=axes, ),
                             toolTip=toolTip)
            row += 1

        if row:
            axisName.addSeparator()

    # def _addItemsToMarkAxesMenuXAxisView(self):
    #     """Setup the menu for the main view for marking axis codes
    #     """
    #     axisName = self.markAxesMenu
    #
    # def _addItemsToMarkAxesMenuYAxisView(self):
    #     """Setup the menu for the main view for marking axis codes
    #     """
    #     axisName = self.markAxesMenu

    def _addItemsToMatchAxisCodesFromMenusMainView(self):
        """Setup the menu for the main view
        """
        self._addItemsToCopyAxisCodesFromMenus(0, self.matchXAxisCodeToMenu)
        self._addItemsToCopyAxisCodesFromMenus(1, self.matchYAxisCodeToMenu)

    # def _addItemsToMatchAxisCodesFromMenusAxes(self):
    #     """Setup the menu for the axis views
    #     """
    #     self._addItemsToCopyAxisCodesFromMenus(0, [self.matchXAxisCodeToMenu2, self.matchYAxisCodeToMenu2])
    #     self._addItemsToCopyAxisCodesFromMenus(1, [self.matchXAxisCodeToMenu2, self.matchYAxisCodeToMenu2])

    def _addItemsToCopyAxisCodesFromMenus(self, axisIndex, axisName):  #, axisList):
        """Copied from old viewbox. This function apparently take the current cursorPosition
         and uses to pan a selected display from the list of spectrumViews or the current cursor position.
        """
        # TODO needs clear documentation
        from functools import partial
        from ccpn.core.lib.AxisCodeLib import getAxisCodeMatchIndices

        # axisList = (self.matchXAxisCodeToMenu2, self.matchYAxisCodeToMenu2)

        # if axisIndex not in range(len(axisList)):
        #     return

        # axisName = axisList[axisIndex]
        axisCode = self.axisCodes[axisIndex]

        if axisName:
            axisName.clear()
            currentStrip = self.current.strip
            position = self.current.cursorPosition

            count = 0
            if currentStrip:
                for spectrumDisplay in self.current.project.spectrumDisplays:
                    addSeparator = False
                    for strip in spectrumDisplay.strips:
                        if strip != currentStrip:

                            indices = getAxisCodeMatchIndices(strip.axisCodes, (axisCode,))

                            for ii, ind in enumerate(indices):
                                if ind is not None:

                                    toolTip = 'Copy %s axis range from strip %s' % (str(strip.axisCodes[ii]), str(strip.id))
                                    if len(list(set(strip.axisCodes) & set(currentStrip.axisCodes))) <= 4:
                                        axisName.addItem(text='%s from %s' % (str(strip.axisCodes[ii]), str(strip.pid)),
                                                         callback=partial(self._copyAxisCodeFromStrip,
                                                                          axisIndex=axisIndex, fromStrip=strip, fromAxisId=ii),
                                                         toolTip=toolTip)
                                        count += 1
                                        addSeparator = True

                    if addSeparator:
                        axisName.addSeparator()

            axisName.setEnabled(True if count else False)

    # def _enableNdAxisMenuItems(self, axisName, axisMenu):
    #
    #     from ccpn.ui.gui.lib.OpenGL.CcpnOpenGLDefs import BOTTOMAXIS, RIGHTAXIS, AXISCORNER
    #
    #     axisMenuItems = (self.copyAllAxisFromMenu2, self.copyXAxisFromMenu2, self.copyYAxisFromMenu2,
    #                      self.matchXAxisCodeToMenu2, self.matchYAxisCodeToMenu2)
    #     enabledList = {BOTTOMAXIS: (False, True, False, True, False),
    #                    RIGHTAXIS : (False, False, True, False, True),
    #                    AXISCORNER: (True, True, True, True, True)
    #                    }
    #     if axisName in enabledList:
    #         axisSelect = enabledList[axisName]
    #         for menuItem, select in zip(axisMenuItems, axisSelect):
    #             # only disable if already enabled
    #             if menuItem.isEnabled():
    #                 menuItem.setEnabled(select)
    #     else:
    #         getLogger().warning('Error selecting menu item')

    # def _enable1dAxisMenuItems(self, axisName):
    #
    #     from ccpn.ui.gui.lib.OpenGL.CcpnOpenGLDefs import BOTTOMAXIS, RIGHTAXIS, AXISCORNER
    #
    #     axisMenuItems = (self.copyAllAxisFromMenu2, self.copyXAxisFromMenu2, self.copyYAxisFromMenu2)
    #     enabledList = {BOTTOMAXIS: (False, True, False),
    #                    RIGHTAXIS : (False, False, True),
    #                    AXISCORNER: (True, True, True)
    #                    }
    #     if axisName in enabledList:
    #         axisSelect = enabledList[axisName]
    #         for menuItem, select in zip(axisMenuItems, axisSelect):
    #             # only disable if already enabled
    #             if menuItem.isEnabled():
    #                 menuItem.setEnabled(select)
    #     else:
    #         getLogger().warning('Error selecting menu item')

    def _updateDisplayedIntegrals(self, data):
        """Callback when integrals have changed.
        """
        self._CcpnGLWidget._processIntegralNotifier(data)

    def _highlightStrip(self, flag):
        """(un)highLight the strip depending on flag

        CCPNINTERNAL: used in GuiMainWindow
        """
        self._CcpnGLWidget.highlightCurrentStrip(flag)
        if self.stripLabel:
            self.stripLabel.setLabelColour(CCPNGLWIDGET_HEXHIGHLIGHT if flag else CCPNGLWIDGET_HEXFOREGROUND)
            self.stripLabel.setHighlighted(flag)

    def _attachZPlaneWidgets(self):
        """Attach the ZPlane widgets for the current strip into the spectrumDisplay axis frame
        """
        spec = self.spectrumDisplay
        if spec.is1D or len(spec.axisCodes) <= 2:
            return

        if spec.zPlaneNavigationMode == ZPlaneNavigationModes.PERSPECTRUMDISPLAY.label:
            # only need to change if showing the spectrumDisplay planeToolBar
            spec.zPlaneFrame.attachZPlaneWidgets(self)

    def _removeZPlaneWidgets(self):
        """Remove the ZPlane widgets for the curent strip from the spectrumDisplay axis frame
        """
        spec = self.spectrumDisplay
        if spec.is1D or len(spec.axisCodes) <= 2:
            return

        if spec.zPlaneFrame and spec.zPlaneNavigationMode == ZPlaneNavigationModes.PERSPECTRUMDISPLAY.label:
            spec.zPlaneFrame.removeZPlaneWidgets()

    def _newPhasingTrace(self):
        self._CcpnGLWidget.newTrace()

    def _setPhasingPivot(self):

        phasingFrame = self.spectrumDisplay.phasingFrame
        direction = phasingFrame.getDirection()
        # position = self.current.cursorPosition[0] if direction == 0 else self.current.cursorPosition[1]
        # position = self.current.positions[0] if direction == 0 else self.current.positions[1]

        position = None  #GWV; not sure what it should be
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
        self._CcpnGLWidget.clearStaticTraces()

    def _updatePivot(self):
        # this is called if pivot entry at bottom of display is updated and then "return" key used

        # update the static traces from the phasing console
        # redraw should update the display
        self._CcpnGLWidget.rescaleStaticTraces()

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

        # connect to the value in the GLwidget
        self.pivotLine.valuesChanged.connect(self._newPositionLineCallback)
        self.pivotLine.setValue(self._newPosition)
        phasingFrame.pivotEntry.valueChanged.connect(self._newPositionPivotCallback)

        # # make sure that all traces are clear
        # from ccpn.ui.gui.lib.OpenGL.CcpnOpenGL import GLNotifier
        #
        # GLSignals = GLNotifier(parent=self)
        if self.spectrumDisplay.is1D:
            self._CcpnGLWidget.GLSignals.emitEvent(triggers=[self._CcpnGLWidget.GLSignals.GLADD1DPHASING], display=self.spectrumDisplay)
        else:
            self._CcpnGLWidget.GLSignals.emitEvent(triggers=[self._CcpnGLWidget.GLSignals.GLCLEARPHASING], display=self.spectrumDisplay)

    def _newPositionLineCallback(self):
        if not self.isDeleted:
            phasingFrame = self.spectrumDisplay.phasingFrame
            self._newPosition = self.pivotLine.values  # [0]

            # disables feedback from the spinbox as event is spawned from the GLwidget
            phasingFrame.setPivotValue(self._newPosition)

            spectrumDisplay = self.spectrumDisplay
            for strip in spectrumDisplay.strips:
                if strip != self:
                    # set the pivotPosition in the other strips
                    strip._updatePivotLine(self._newPosition)

    def _updatePivotLine(self, newPosition):
        """Respond to changes in the other strips
        """
        if not self.isDeleted and self.pivotLine:
            self._newPosition = newPosition

            # don't emit a signal when changing - stops feedback loop
            self.pivotLine.setValue(newPosition, emitValuesChanged=False)

    def _newPositionPivotCallback(self, value):
        """Respond to change in value in the spinBox
        """
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
        self._CcpnGLWidget.GLSignals.emitEvent(triggers=[self._CcpnGLWidget.GLSignals.GLCLEARPHASING], display=self.spectrumDisplay)

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

        self._CcpnGLWidget.clearStaticTraces()

        # for spectrumView in self.spectrumViews:
        #     spectrumView._changedPhasingDirection()

    def _updatePhasing(self):
        if self.spectrumDisplay.phasingFrame.isVisible():
            colour = getColours()[GUISTRIP_PIVOT]
            self._CcpnGLWidget.setInfiniteLineColour(self.pivotLine, colour)
            self._CcpnGLWidget.rescaleStaticTraces()

    def _toggleShowActivePhaseTrace(self):
        """Toggles whether the active phasing trace is visible.
        """
        self.showActivePhaseTrace = not self.showActivePhaseTrace
        self._CcpnGLWidget.showActivePhaseTrace = self.showActivePhaseTrace

    def _toggleShowSpectraOnPhasing(self):
        """Toggles whether spectraOnPhasing is visible.
        """
        self.showSpectraOnPhasing = not self.showSpectraOnPhasing
        self._CcpnGLWidget.showSpectraOnPhasing = self.showSpectraOnPhasing

    def _showSpectraOnPhasing(self):
        """Displays spectraOnPhasing in strip.
        """
        self.showSpectraOnPhasing = True
        self._CcpnGLWidget.showSpectraOnPhasing = True

    def _hideSpectraOnPhasing(self):
        """Hides spectraOnPhasing in strip.
        """
        self.showSpectraOnPhasing = False
        self._CcpnGLWidget.showSpectraOnPhasing = False

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # symbolLabelling

    def _setSymbolLabelling(self):
        if self.spectrumViews:
            for sV in self.spectrumViews:

                for peakListView in sV.peakListViews:
                    # peakListView.buildSymbols = True
                    peakListView.buildLabels = True

            # spawn a redraw of the GL windows
            self._CcpnGLWidget.GLSignals.emitPaintEvent()

    @property
    def symbolLabelling(self):
        """Get the symbol labelling for the strip
        """
        return self._CcpnGLWidget._symbolLabelling

    @symbolLabelling.setter
    def symbolLabelling(self, value):
        """Set the symbol labelling for the strip
        """
        if not isinstance(value, int):
            raise TypeError('Error: symbolLabelling not an int')

        oldValue = self._CcpnGLWidget._symbolLabelling
        self._CcpnGLWidget._symbolLabelling = value if (value in range(self.spectrumDisplay.MAXPEAKLABELTYPES)) else 0
        if value != oldValue:
            self._setSymbolLabelling()
            if self.spectrumViews:
                self._emitSymbolChanged()

    def cycleSymbolLabelling(self):
        """Toggles whether peak labelling is minimal is visible in the strip.
        """
        self.symbolLabelling += 1

    def setSymbolLabelling(self, value):
        """Toggles whether peak labelling is minimal is visible in the strip.
        """
        self.symbolLabelling = value

    def _emitSymbolChanged(self):
        # spawn a redraw of the GL windows
        self._CcpnGLWidget.GLSignals._emitSymbolsChanged(source=None, strip=self,
                                                         symbolDict={SYMBOLTYPES           : self.symbolType,
                                                                     ANNOTATIONTYPES       : self.symbolLabelling,
                                                                     SYMBOLSIZE            : self.symbolSize,
                                                                     SYMBOLTHICKNESS       : self.symbolThickness,
                                                                     CONTOURTHICKNESS      : self.contourThickness,
                                                                     ALIASENABLED          : self.aliasEnabled,
                                                                     ALIASSHADE            : self.aliasShade,
                                                                     ALIASLABELSENABLED    : self.aliasLabelsEnabled,
                                                                     PEAKLABELSENABLED     : self.peakLabelsEnabled,
                                                                     MULTIPLETLABELSENABLED: self.multipletLabelsEnabled,
                                                                     })

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # symbolTypes

    def _setSymbolType(self):
        if self.spectrumViews:
            for sV in self.spectrumViews:

                for peakListView in sV.peakListViews:
                    peakListView.buildSymbols = True
                    peakListView.buildLabels = True

                for multipletListView in sV.multipletListViews:
                    multipletListView.buildSymbols = True
                    multipletListView.buildLabels = True

            # spawn a redraw of the GL windows
            self._CcpnGLWidget.GLSignals.emitPaintEvent()

    @property
    def symbolType(self):
        """Get the symbol type for the strip
        """
        return self._CcpnGLWidget._symbolType

    @symbolType.setter
    def symbolType(self, value):
        """Set the symbol type for the strip
        """
        if not isinstance(value, int):
            raise TypeError('Error: symbolType not an int')

        oldValue = self._CcpnGLWidget._symbolType
        self._CcpnGLWidget._symbolType = value if (value in range(self.spectrumDisplay.MAXPEAKSYMBOLTYPES)) else 0
        if value != oldValue:
            self._setSymbolType()
            if self.spectrumViews:
                self._emitSymbolChanged()

    def cyclePeakSymbols(self):
        """Cycle through peak symbol types.
        """
        self.symbolType += 1

    def setPeakSymbols(self, value):
        """set the peak symbol type.
        """
        self.symbolType = value

    def _setSymbolsPaintEvent(self):
        # prompt the GLwidgets to update
        self._CcpnGLWidget.GLSignals.emitEvent(triggers=[self._CcpnGLWidget.GLSignals.GLRESCALE,
                                                         self._CcpnGLWidget.GLSignals.GLALLPEAKS,
                                                         self._CcpnGLWidget.GLSignals.GLALLMULTIPLETS,
                                                         ])

    def _setContoursPaintEvent(self):
        # prompt the GLwidgets to update
        self._CcpnGLWidget.GLSignals.emitEvent(triggers=[self._CcpnGLWidget.GLSignals.GLALLCONTOURS,
                                                         ])

    def _symbolsChangedInSettings(self, aDict):
        """Respond to changes in the symbol values in the settings widget
        """
        _symbolType = aDict[SYMBOLTYPES]
        _annotationsType = aDict[ANNOTATIONTYPES]
        _symbolSize = aDict[SYMBOLSIZE]
        _symbolThickness = aDict[SYMBOLTHICKNESS]
        _aliasEnabled = aDict[ALIASENABLED]
        _aliasShade = aDict[ALIASSHADE]
        _aliasLabelsEnabled = aDict[ALIASLABELSENABLED]
        _peakLabelsEnabled = aDict[PEAKLABELSENABLED]
        _multipletLabelsEnabled = aDict[MULTIPLETLABELSENABLED]
        _contourThickness = aDict[CONTOURTHICKNESS]

        if self.isDeleted:
            return

        with self.spectrumDisplay._spectrumDisplaySettings.blockWidgetSignals():
            # update the current settings from the dict
            if _symbolType != self.symbolType:
                self.setPeakSymbols(_symbolType)

            elif _annotationsType != self.symbolLabelling:
                self.setSymbolLabelling(_annotationsType)

            elif _symbolSize != self.symbolSize:
                self.symbolSize = _symbolSize
                self._setSymbolsPaintEvent()

            elif _symbolThickness != self.symbolThickness:
                self.symbolThickness = _symbolThickness
                self._setSymbolsPaintEvent()

            elif _aliasEnabled != self.aliasEnabled:
                self.aliasEnabled = _aliasEnabled
                self._setSymbolsPaintEvent()

            elif _aliasShade != self.aliasShade:
                self.aliasShade = _aliasShade
                self._setSymbolsPaintEvent()

            elif _aliasLabelsEnabled != self.aliasLabelsEnabled:
                self.aliasLabelsEnabled = _aliasLabelsEnabled
                self._setSymbolsPaintEvent()

            elif _contourThickness != self.contourThickness:
                self.contourThickness = _contourThickness
                self._setContoursPaintEvent()

            elif _peakLabelsEnabled != self.peakLabelsEnabled:
                self.peakLabelsEnabled = _peakLabelsEnabled
                self._setSymbolsPaintEvent()

            elif _multipletLabelsEnabled != self.multipletLabelsEnabled:
                self.multipletLabelsEnabled = _multipletLabelsEnabled
                self._setSymbolsPaintEvent()

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # symbolSize

    @property
    def symbolSize(self):
        """Get the symbol size for the strip
        """
        return self._CcpnGLWidget._symbolSize

    @symbolSize.setter
    def symbolSize(self, value):
        """Set the symbol size for the strip
        """
        if not isinstance(value, (int, float)):
            raise TypeError('Error: symbolSize not an (int, float)')
        value = int(value)

        oldValue = self._CcpnGLWidget._symbolSize
        self._CcpnGLWidget._symbolSize = value if (value and value >= 0) else oldValue
        if value != oldValue:
            self._setSymbolLabelling()
            if self.spectrumViews:
                self._emitSymbolChanged()

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # symbolThickness

    @property
    def symbolThickness(self):
        """Get the symbol thickness for the strip
        """
        return self._CcpnGLWidget._symbolThickness

    @symbolThickness.setter
    def symbolThickness(self, value):
        """Set the symbol thickness for the strip
        """
        if not isinstance(value, (int, float)):
            raise TypeError('Error: symbolThickness not an (int, float)')
        value = int(value)

        oldValue = self._CcpnGLWidget._symbolThickness
        self._CcpnGLWidget._symbolThickness = value if (value and value >= 0) else oldValue
        if value != oldValue:
            self._setSymbolLabelling()
            if self.spectrumViews:
                self._emitSymbolChanged()

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # contourThickness

    @property
    def contourThickness(self):
        """Get the contour thickness for the strip
        """
        return self._CcpnGLWidget._contourThickness

    @contourThickness.setter
    def contourThickness(self, value):
        """Set the contour thickness for the strip
        """
        if not isinstance(value, (int, float)):
            raise TypeError('Error: contourThickness not an (int, float)')
        value = int(value)

        oldValue = self._CcpnGLWidget._contourThickness
        self._CcpnGLWidget._contourThickness = value if (value and value >= 0) else oldValue
        if value != oldValue:
            if self.spectrumViews:
                self._emitSymbolChanged()

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # aliasEnabled

    @property
    def aliasEnabled(self):
        """Get aliasEnabled for the strip
        """
        return self._CcpnGLWidget._aliasEnabled

    @aliasEnabled.setter
    def aliasEnabled(self, value):
        """Set aliasEnabled for the strip
        """
        if not isinstance(value, bool):
            raise TypeError('Error: aliasEnabled not a bool')

        oldValue = self._CcpnGLWidget._aliasEnabled
        self._CcpnGLWidget._aliasEnabled = value
        if value != oldValue:
            self._setSymbolLabelling()
            if self.spectrumViews:
                self._emitSymbolChanged()

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # aliasShade

    @property
    def aliasShade(self):
        """Get aliasShade for the strip
        """
        return self._CcpnGLWidget._aliasShade

    @aliasShade.setter
    def aliasShade(self, value):
        """Set aliasShade for the strip
        """
        if not isinstance(value, (int, float)):
            raise TypeError('Error: aliasShade not an (int, float)')

        oldValue = self._CcpnGLWidget._aliasShade
        self._CcpnGLWidget._aliasShade = value if (value and value >= 0) else oldValue
        if value != oldValue:
            self._setSymbolLabelling()
            if self.spectrumViews:
                self._emitSymbolChanged()

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # aliasLabelsEnabled

    @property
    def aliasLabelsEnabled(self):
        """Get aliasLabelsEnabled for the strip
        """
        return self._CcpnGLWidget._aliasLabelsEnabled

    @aliasLabelsEnabled.setter
    def aliasLabelsEnabled(self, value):
        """Set aliasLabelsEnabled for the strip
        """
        if not isinstance(value, bool):
            raise TypeError('Error: aliasLabelsEnabled not a bool')

        oldValue = self._CcpnGLWidget._aliasLabelsEnabled
        self._CcpnGLWidget._aliasLabelsEnabled = value
        if value != oldValue:
            self._setSymbolLabelling()
            if self.spectrumViews:
                self._emitSymbolChanged()

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # peakLabelsEnabled

    @property
    def peakLabelsEnabled(self):
        """Get peakLabelsEnabled for the strip
        """
        return self._CcpnGLWidget._peakLabelsEnabled

    @peakLabelsEnabled.setter
    def peakLabelsEnabled(self, value):
        """Set peakLabelsEnabled for the strip
        """
        if not isinstance(value, bool):
            raise TypeError('Error: peakLabelsEnabled not a bool')

        oldValue = self._CcpnGLWidget._peakLabelsEnabled
        self._CcpnGLWidget._peakLabelsEnabled = value
        if value != oldValue:
            self._setSymbolLabelling()
            if self.spectrumViews:
                self._emitSymbolChanged()

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # multipletLabelsEnabled

    @property
    def multipletLabelsEnabled(self):
        """Get multipletLabelsEnabled for the strip
        """
        return self._CcpnGLWidget._multipletLabelsEnabled

    @multipletLabelsEnabled.setter
    def multipletLabelsEnabled(self, value):
        """Set multipletLabelsEnabled for the strip
        """
        if not isinstance(value, bool):
            raise TypeError('Error: multipletLabelsEnabled not a bool')

        oldValue = self._CcpnGLWidget._multipletLabelsEnabled
        self._CcpnGLWidget._multipletLabelsEnabled = value
        if value != oldValue:
            self._setSymbolLabelling()
            if self.spectrumViews:
                self._emitSymbolChanged()

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def updateAxisRatios(self):
        # notify strips to update fixed/locked state

        try:
            # update settings - not very nice, using the settings signal for the minute :|
            self.spectrumDisplay._spectrumDisplaySettings.updateFromDefaults()
        except Exception as es:
            print(str(es))

    def setFixedAspectRatios(self, ratios):
        # update the ratios for the fixed mode
        self._CcpnGLWidget._lockedAspectRatios = ratios.copy()

    def setAspectRatioMode(self, mode):
        # update the aspect ratio mode
        self._CcpnGLWidget._aspectRatioMode = mode

    #-----------------------------------------------------------------------------------------
    # marks
    #-----------------------------------------------------------------------------------------

    def _createMarkAtPosition(self, positions, axisCodes):
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

        self.mainWindow.newMark(defaultColour, positions, axisCodes)

    def _copyAxisFromStrip(self, axisId, fromStrip):
        try:
            axisRange = fromStrip.viewRange()
            if axisId == 'X':
                # copy X axis from strip
                self.zoomX(*axisRange[0])

            elif axisId == 'Y':
                # copy Y axis from strip
                self.zoomY(*axisRange[1])

            elif axisId == 'All':
                # copy both axes from strip
                self.zoom(axisRange[0], axisRange[1])

        except Exception as es:
            getLogger().warning('Error copying axis %s from strip %s' % (str(axisId), str(fromStrip)))
            raise (es)

    def _copyAxisCodeFromStrip(self, axisIndex, fromStrip, fromAxisId):
        try:
            axisRange = fromStrip.orderedAxes[fromAxisId].region
            if axisIndex == 0:
                # copy X axis from strip
                self.zoomX(*axisRange)

            elif axisIndex == 1:
                # copy Y axis from strip
                self.zoomY(*axisRange)

        except Exception as es:
            getLogger().warning('Error copying axis %s from strip %s' % (str(fromStrip.axisCodes[fromAxisId]), str(fromStrip)))
            raise (es)

    def _createMarkAtCursorPosition(self, axisIndex=None):
        try:
            if self.isDeleted or self._flaggedForDelete:
                return

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

            # defaultColour = self._preferences.defaultMarksColour
            mouseDict = self.current.mouseMovedDict[AXIS_FULLATOMNAME]
            positions = [mouseDict[ax] for ax in self.axisCodes if ax in mouseDict]
            axisCodes = [ax for ax in self.axisCodes if ax in mouseDict]

            if axisIndex is not None:
                if (0 <= axisIndex < len(positions)):
                    positions = (positions[axisIndex],)
                    axisCodes = (axisCodes[axisIndex],)
                    self.mainWindow.newMark(defaultColour, positions, axisCodes)
            else:
                self.mainWindow.newMark(defaultColour, positions, axisCodes)

            # add the marks for the double cursor - needs to be enabled in preferences
            if self.doubleCrosshairVisible and self._CcpnGLWidget._matchingIsotopeCodes:
                mouseDict = self.current.mouseMovedDict[DOUBLEAXIS_FULLATOMNAME]
                positions = [mouseDict[ax] for ax in self.axisCodes[:2] if ax in mouseDict]
                axisCodes = [ax for ax in self.axisCodes[:2] if ax in mouseDict]

                if axisIndex is not None:

                    if (0 <= axisIndex < 2):
                        # get the reflected axisCode and position
                        doubleIndex = 1 - axisIndex
                        positions = (positions[doubleIndex],)
                        axisCodes = (axisCodes[doubleIndex],)
                        self.mainWindow.newMark(defaultColour, positions, axisCodes)
                else:
                    self.mainWindow.newMark(defaultColour, positions, axisCodes)

            # need new mark method of the form newMark(colour=colour, axisCode=position)

        except Exception as es:
            getLogger().warning('Error setting mark at current cursor position')
            raise (es)

    def getObjectsUnderMouse(self):
        """Get the selected objects currently under the mouse
        """
        return self._CcpnGLWidget.getObjectsUnderMouse()

    # GWV 24/12/21: not used and method does not return anything
    # def _showMousePosition(self, pos: QtCore.QPointF):
    #     """Displays mouse position for both axes by axis code.
    #     """
    #     if self.isDeleted:
    #         return
    #
    #     # position = self.viewBox.mapSceneToView(pos)
    #     try:
    #         # this only calls a single _wrapper function
    #         if self.spectrumDisplay.is1D:
    #             fmt = "%s: %.3f\n%s: %.4g"
    #         else:
    #             fmt = "%s: %.2f\n%s: %.2f"
    #     except:
    #         fmt = "%s: %.3f  %s: %.4g"

    def autoRange(self):
        self._CcpnGLWidget.autoRange()

    def zoom(self, xRegion: Tuple[float, float], yRegion: Tuple[float, float]):
        """Zooms strip to the specified region.
        """
        self._CcpnGLWidget.zoom(xRegion, yRegion)

    def zoomX(self, x1: float, x2: float):
        """
        Zooms x axis of strip to the specified region
        """
        self._CcpnGLWidget.zoomX(x1, x2)

    def zoomY(self, y1: float, y2: float):
        """Zooms y axis of strip to the specified region
        """
        self._CcpnGLWidget.zoomY(y1, y2)

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

    def _resetAllZoom(self):
        """
        Zooms x/y axes to maximum of data.
        """
        self._CcpnGLWidget.resetAllZoom()

    def _resetYZoom(self):
        """
        Zooms y axis to maximum of data.
        """
        self._CcpnGLWidget.resetYZoom()

    def _resetXZoom(self):
        """
        Zooms x axis to maximum value of data.
        """
        self._CcpnGLWidget.resetXZoom()

    def _storeZoom(self):
        """Adds current region to the zoom stack for the strip.
        """
        self._CcpnGLWidget.storeZoom()

    @property
    def zoomState(self):
        if self._CcpnGLWidget is not None:
            zoom = self._CcpnGLWidget.zoomState
            return zoom
        return []

    def restoreZoomFromState(self, zoomState):
        """
        Restore zoom from a saved state
        :param zoomState: list of Axis coordinate Left, Right, Bottom, Top
        """
        if zoomState is not None:
            if len(zoomState) == 4:
                # self._restoreZoom(zoomState=zoomState)
                axisL, axisR, axisB, axisT = zoomState[0], zoomState[1], zoomState[2], zoomState[3]

                self._CcpnGLWidget.setXRegion(axisL, axisR)
                self._CcpnGLWidget.setYRegion(axisT, axisB)

    def _restoreZoom(self, zoomState=None):
        """Restores last saved region to the zoom stack for the strip.
        """
        self._CcpnGLWidget.restoreZoom(zoomState)

    def _previousZoom(self):
        """Changes to the previous zoom for the strip.
        """
        self._CcpnGLWidget.previousZoom()

    def _nextZoom(self):
        """Changes to the next zoom for the strip.
        """
        self._CcpnGLWidget.nextZoom()

    def _setZoomPopup(self):
        from ccpn.ui.gui.popups.ZoomPopup import ZoomPopup

        popup = ZoomPopup(parent=self.mainWindow, mainWindow=self.mainWindow)
        popup.exec_()

    @logCommand(get='self')
    def resetZoom(self):
        self._CcpnGLWidget.resetZoom()

    def _zoomIn(self):
        """Zoom in to the strip.
        """
        self._CcpnGLWidget.zoomIn()

    def _zoomOut(self):
        """Zoom out of the strip.
        """
        self._CcpnGLWidget.zoomOut()

    def _panSpectrum(self, direction: str = 'up'):
        """Pan the spectrum with the cursor keys
        """
        self._CcpnGLWidget._panSpectrum(direction)

    def _movePeaks(self, direction: str = 'up'):
        """Move the peaks with the cursors
        """
        self._CcpnGLWidget._movePeaks(direction)

    def _resetRemoveStripAction(self):
        """Update interface when a strip is created or deleted.

          NB notifier is executed after deletion is final but before the wrapper is updated.
          len() > 1 check is correct also for delete
        """
        pass  # GWV: poor solution self.spectrumDisplay._resetRemoveStripAction()

    def setRightAxisVisible(self, axisVisible=False):
        """Set the visibility of the right axis
        """
        self._CcpnGLWidget.setRightAxisVisible(axisVisible=axisVisible)

    def setBottomAxisVisible(self, axisVisible=False):
        """Set the visibility of the bottom axis
        """
        self._CcpnGLWidget.setBottomAxisVisible(axisVisible=axisVisible)

    def getAxesVisible(self):
        """Get the visibility of strip axes
        """
        return self._CcpnGLWidget.getAxesVisible()

    def setAxesVisible(self, rightAxisVisible=True, bottomAxisVisible=False):
        """Set the visibility of strip axes
        """
        self._CcpnGLWidget.setAxesVisible(rightAxisVisible=rightAxisVisible,
                                          bottomAxisVisible=bottomAxisVisible)

    def getRightAxisWidth(self):
        """return the width of the right axis margin
        """
        return self._CcpnGLWidget.AXIS_MARGINRIGHT

    def getBottomAxisHeight(self):
        """return the height of the bottom axis margin
        """
        return self._CcpnGLWidget.AXIS_MARGINBOTTOM

    def _moveToNextSpectrumView(self):

        if not self.spectrumDisplay.isGrouped:

            # cycle through the spectrumViews
            spectrumViews = self.getSpectrumViews()
            countSpvs = len(spectrumViews)
            if countSpvs > 0:
                visibleSpectrumViews = [sv for sv in spectrumViews if sv.isDisplayed]
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

        else:
            # cycle through the spectrumGroups
            spectrumViews = self.getSpectrumViews()

            actions = self.spectrumDisplay.spectrumGroupToolBar.actions()
            if not actions:
                return

            visibleGroups = [(act, self.project.getByPid(act.objectName())) for act in actions if act.isChecked()]

            countSpvs = len(actions)

            if visibleGroups:

                # get the last group in the toolbar buttons
                lastAct, lastObj = visibleGroups[-1]
                nextInd = (actions.index(lastAct) + 1) % len(actions)
                nextAct, nextObj = actions[nextInd], self.project.getByPid(actions[nextInd].objectName())

                # uncheck/check the toolbar buttons
                for action, obj in visibleGroups:
                    action.setChecked(False)
                nextAct.setChecked(True)

                if nextObj:
                    # set the associated spectrumViews as visible
                    for specView in spectrumViews:
                        specView.setVisible(specView.spectrum in nextObj.spectra)

            elif actions:

                # nothing visible so set the first toolbar button
                currentGroup = self.project.getByPid(actions[0].objectName())
                if currentGroup:
                    for specView in spectrumViews:
                        specView.setVisible(specView.spectrum in currentGroup.spectra)
                actions[0].setChecked(True)

    def _moveToPreviousSpectrumView(self):

        if not self.spectrumDisplay.isGrouped:

            spectrumViews = self.getSpectrumViews()
            countSpvs = len(spectrumViews)
            if countSpvs > 0:
                visibleSpectrumViews = [sv for sv in spectrumViews if sv.isDisplayed]
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

        else:
            # cycle through the spectrumGroups
            spectrumViews = self.getSpectrumViews()

            actions = self.spectrumDisplay.spectrumGroupToolBar.actions()
            if not actions:
                return

            visibleGroups = [(act, self.project.getByPid(act.objectName())) for act in actions if act.isChecked()]

            countSpvs = len(actions)

            if visibleGroups:

                # get the first group in the toolbar buttons
                lastAct, lastObj = visibleGroups[0]
                nextInd = (actions.index(lastAct) - 1) % len(actions)
                nextAct, nextObj = actions[nextInd], self.project.getByPid(actions[nextInd].objectName())

                # uncheck/check the toolbar buttons
                for action, obj in visibleGroups:
                    action.setChecked(False)
                nextAct.setChecked(True)

                if nextObj:
                    # set the associated spectrumViews as visible
                    for specView in spectrumViews:
                        specView.setVisible(specView.spectrum in nextObj.spectra)

            elif actions:

                # nothing visible so set the last toolbar button
                currentGroup = self.project.getByPid(actions[-1].objectName())
                if currentGroup:
                    for specView in spectrumViews:
                        specView.setVisible(specView.spectrum in currentGroup.spectra)
                actions[-1].setChecked(True)

    def _showAllSpectrumViews(self, value: bool = True):

        # turn on/off all spectrumViews
        spectrumViews = self.getSpectrumViews()
        for sp in spectrumViews:
            sp.setVisible(value)

        if self.spectrumDisplay.isGrouped:
            # turn on/off all toolbar buttons
            actions = self.spectrumDisplay.spectrumGroupToolBar.actions()
            for action in actions:
                action.setChecked(value)

    # GWV 07/01/2022: removed
    # @property
    # def visibleSpectra(self):
    #     """List of spectra currently visible in the strip. Ordered as in the spectrumDisplay
    #     """
    #     return self.spectrumDisplay.visibleSpectra

    def _invertSelectedSpectra(self):

        if not self.spectrumDisplay.isGrouped:
            spectrumViews = self.getSpectrumViews()
            countSpvs = len(spectrumViews)
            if countSpvs > 0:

                visibleSpectrumViews = [sv.isDisplayed for sv in spectrumViews]
                if any(visibleSpectrumViews):
                    for sv in spectrumViews: sv.setVisible(not sv.isDisplayed)
                else:
                    self._showAllSpectrumViews(True)

        else:

            actions = self.spectrumDisplay.spectrumGroupToolBar.actions()
            spectra = set()
            for action in actions:

                # toggle the visibility of the toolbar buttons
                newVisible = not action.isChecked()
                action.setChecked(newVisible)
                obj = self.project.getByPid(action.objectName())

                if newVisible and obj:
                    for spec in obj.spectra:
                        spectra.add(spec)

            # set the visibility of the spectrumViews
            spectrumViews = self.getSpectrumViews()
            for specView in spectrumViews:
                specView.setVisible(specView.spectrum in spectra)

    def report(self):
        """Generate a drawing object that can be added to reports
        :return reportlab drawing object:
        """
        if self._CcpnGLWidget:
            # from ccpn.ui.gui.lib.OpenGL.CcpnOpenGLExport import GLExporter

            glReport = self._CcpnGLWidget.exportToSVG()
            if glReport:
                return glReport.report()

    # def axisRegionChanged(self, axis):
    #     """Notifier function: Update strips etc. for when axis position or width changes.
    #     """
    #     if self.isDeleted:
    #         return
    #
    #     self._setPlaneAxisWidgets(axis=axis)
    #
    #     # # can't remember why this is here
    #     # self.beingUpdated = False

    @logCommand(get='self')
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

        # with undoBlockWithoutSideBar():
        with undoStackBlocking() as _:  # Do not add to undo/redo stack
            with undoStackBlocking() as addUndoItem:
                # needs to be first as it uses currentOrdering
                addUndoItem(undo=partial(self._moveToStripLayout, newIndex, currentIndex))

            self._wrappedData.moveTo(newIndex)
            # reorder the strips in the layout
            self._moveToStripLayout(currentIndex, newIndex)

            # add undo item to reorder the strips in the layout
            with undoStackBlocking() as addUndoItem:
                addUndoItem(redo=partial(self._moveToStripLayout, currentIndex, newIndex))

    def _moveToStripLayout(self, currentIndex, newIndex):
        # management of Qt layout
        # TBD: need to soup up below with extra loop when have tiles
        spectrumDisplay = self.spectrumDisplay
        layout = spectrumDisplay.stripFrame.layout()
        if not layout:  # should always exist but play safe:
            return

        # remove old widgets - this needs to done otherwise the layout swap destroys all children, and remember minimum widths
        _oldWidgets = []
        minSizes = []
        while layout.count():
            wid = layout.takeAt(0).widget()
            _oldWidgets.append(wid)
            minSizes.append(wid.minimumSize())

        # get the new strip order
        _widgets = list(spectrumDisplay.orderedStrips)

        if len(_widgets) != len(spectrumDisplay.strips):
            raise RuntimeError('bad ordered stripCount')

        # remember necessary layout info and create a new layout - ensures clean for new widgets
        margins = layout.getContentsMargins()
        space = layout.spacing()
        QtWidgets.QWidget().setLayout(layout)
        layout = QtWidgets.QGridLayout()
        spectrumDisplay.stripFrame.setLayout(layout)
        layout.setContentsMargins(*margins)
        layout.setSpacing(space)

        # need to switch the tile positions for the moved strips

        # reinsert strips in new order - reset minimum widths
        if spectrumDisplay.stripArrangement == 'Y':

            # horizontal strip layout
            for m, widgStrip in enumerate(_widgets):

                tilePosition = widgStrip.tilePosition
                if True:  # tilePosition is None:
                    layout.addWidget(widgStrip, 0, m)
                    widgStrip.tilePosition = (0, m)
                # else:
                #     layout.addWidget(widgStrip, tilePosition[0], tilePosition[1])

                widgStrip.setMinimumWidth(minSizes[m].width())

        elif spectrumDisplay.stripArrangement == 'X':

            # vertical strip layout
            for m, widgStrip in enumerate(_widgets):

                tilePosition = widgStrip.tilePosition
                if True:  # tilePosition is None:
                    layout.addWidget(widgStrip, m, 0)
                    widgStrip.tilePosition = (0, m)
                # else:
                #     layout.addWidget(widgStrip, tilePosition[1], tilePosition[0])

                widgStrip.setMinimumHeight(minSizes[m].height())

        elif spectrumDisplay.stripArrangement == 'T':

            # NOTE:ED - Tiled plots not fully implemented yet
            getLogger().warning('Tiled plots not implemented for spectrumDisplay: %s' % str(spectrumDisplay.pid))

        else:
            getLogger().warning('Strip direction is not defined for spectrumDisplay: %s' % str(spectrumDisplay.pid))

        # rebuild the axes for strips
        spectrumDisplay.showAxes(stretchValue=True, widths=False)

    def navigateToPosition(self, positions:List[float],
                           axisCodes:List[str] = None,
                           widths:List[float] = None):
        """Navigate to positions, optionally setting widths of this Strip
        """
        from ccpn.ui.gui.lib.StripLib import navigateToPositionInStrip

        navigateToPositionInStrip(self, positions, axisCodes, widths)

    def navigateToPeak(self, peak, widths:List[float] = None):
        """Navigate to peak.position, optionally setting widths of this Strip
        """
        if peak:
            self.navigateToPosition(peak.position, peak.axisCodes, widths=widths)
        else:
            MessageDialog.showMessage('No Peak', 'Select a peak first')

    def _raiseContextMenu(self, event: QtGui.QMouseEvent):
        """
        Raise the context menu
        """

        position = event.screenPos()
        self.viewStripMenu.exec_(QtCore.QPoint(int(position.x()),
                                               int(position.y())))
        self.contextMenuPosition = self.current.cursorPosition

    def _updateVisibility(self):
        """Update visibility list in the OpenGL
        """
        self._CcpnGLWidget.updateVisibleSpectrumViews()

    def firstVisibleSpectrum(self):
        """return the first visible spectrum in the strip, or the first if none are visible.
        """
        return self._CcpnGLWidget._firstVisible

    def _toggleStackPhaseFromShortCut(self):
        """Not implemented, to be overwritten by subclasses
        """
        pass

    def mainViewSize(self):
        """Return the width/height for the mainView of the OpenGL widget
        """
        return self._CcpnGLWidget.mainViewSize()

    #-----------------------------------------------------------------------------------------
    # Peak-related stuff
    #-----------------------------------------------------------------------------------------

    @logCommand(get='self')
    def createPeak(self, ppmPositions: List[float]) -> Tuple[Tuple[Peak, ...], Tuple[PeakList, ...]]:
        """Create peak at position for all spectra currently displayed in strip.
        """
        result = []
        peakLists = []

        with undoBlockWithoutSideBar():
            # create the axisDict for this spectrum
            axisDict = {axis: ppm for axis, ppm in zip(self.axisCodes, ppmPositions)}

            # loop through the visible spectra
            for spectrumView in (v for v in self.spectrumViews if v.isDisplayed):

                spectrum = spectrumView.spectrum
                # get the list of visible peakLists
                validPeakListViews = [pp for pp in spectrumView.peakListViews if pp.isDisplayed]
                if not validPeakListViews:
                    continue

                for thisPeakListView in validPeakListViews:
                    peakList = thisPeakListView.peakList

                    # pick the peak in this peakList
                    pk = spectrum.createPeak(peakList, **axisDict)
                    if pk:
                        result.append(pk)
                        peakLists.append(peakList)

            # set the current peaks
            self.current.peaks = result

        return tuple(result), tuple(peakLists)

    @logCommand(get='self')
    def pickPeaks(self, regions: List[Tuple[float,float]]) -> list:
        """Peak-pick in regions for all spectra currently displayed in the strip.
        :param regions: a list of (minVal,maxVal) tuples in display order
        :return a list of Peak instances
        """
        from ccpn.core.lib.SpectrumLib import _pickPeaksByRegion

        _displayedSpectra = self._displayedSpectra
        if len(_displayedSpectra) == 0:
            getLogger().warning('%s pickPeaks: no visible spectra' % self)
            return []

        result = []
        with undoBlockWithoutSideBar():

            # loop through the visible spectra
            for _displayedSpectrum in _displayedSpectra:
                spectrum = _displayedSpectrum.spectrum
                spectrumView = _displayedSpectrum.spectrumView

                _checkOutside = _displayedSpectrum.checkForRegionsOutsideLimits(regions)
                _skip = any(_checkOutside)
                if _skip:
                    getLogger().debug('Strip.pickPeaks: skipping %s; outside region %r' % (spectrum, regions))
                    continue

                # get the list of visible peakLists
                validPeakListViews = [pp for pp in spectrumView.peakListViews if pp.isDisplayed]
                if not validPeakListViews:
                    continue

                # get parameters to apply to peak picker
                _sliceTuples = _displayedSpectrum.getSliceTuples(regions)
                positiveThreshold = spectrum.positiveContourBase if spectrumView.displayPositiveContours else None
                negativeThreshold = spectrum.negativeContourBase if spectrumView.displayNegativeContours else None

                for thisPeakListView in validPeakListViews:
                    peakList = thisPeakListView.peakList
                    # pick the peaks in this peakList
                    newPeaks = _pickPeaksByRegion(spectrum = spectrum,
                                                  sliceTuples=_sliceTuples,
                                                  peakList=peakList,
                                                  positiveThreshold=positiveThreshold,
                                                  negativeThreshold=negativeThreshold,
                                                  )
                    if newPeaks is not None and len(newPeaks) > 0:
                        result.extend(newPeaks)

        self.current.peaks = result
        return result

    #-----------------------------------------------------------------------------------------
    # strip Axis-related stuff
    #-----------------------------------------------------------------------------------------

    def getAxisPosition(self, axisIndex):
        return self._CcpnGLWidget.getAxisPosition(axisIndex)

    def setAxisPosition(self, axisIndex, position, rescale=True, update=True):
        """Set the axis position of the strip
        if rescale is False, the symbols, etc., must explicitly be refreshed
        """
        self._CcpnGLWidget.setAxisPosition(axisIndex, position, rescale=rescale, update=update)

    def getAxisWidth(self, axisIndex):
        return self._CcpnGLWidget.getAxisWidth(axisIndex)

    def setAxisWidth(self, axisIndex, width, rescale=True, update=True):
        """Set the axis width of the strip, centred on the axis position
        if rescale is False, the symbols, etc., must explicitly be refreshed
        """
        self._CcpnGLWidget.setAxisWidth(axisIndex, width, rescale=rescale, update=update)

    def getAxisRegion(self, axisIndex):
        """Return the region currently displayed in the strip as tuple(min, max) for given axis.
        axisIndex is the screen axis; X is 0, Y is 1
        """
        return self._CcpnGLWidget.getAxisRegion(axisIndex)

    def setAxisRegion(self, axisIndex, width, rescale=True, update=True):
        """Set the axis region for the strip.
        if rescale is False, the symbols, etc., must explicitly be refreshed
        """
        self._CcpnGLWidget.setAxisRegion(axisIndex, width, rescale=rescale, update=update)

    def getAxisRegions(self) -> Tuple[Tuple, ...]:
        """Return a tuple if tuples for the regions ((min, max), ...)
        Visible direction of axes is not preserved
        """
        regions = []
        for axis, position, width in zip(self.orderedAxes, self.positions, self.widths):
            regions.append((position - width / 2.0, position + width / 2.0))

        return tuple(regions)

    def _setAxisPositionAndWidth(self, stripAxisIndex: int, position:float, width:float = None,
                                       refresh=True):
        """Change the position of axis defined by stripAxisIndex
        :param stripAxisIndex: an index, defining an Z, A, ... plane; i.e. >= 2
        :param position: the new position (in axis units; i.e. ppm, Hz, points)
        :param width: (optional) the width of the plane
        :param refresh: call openGL refresh
        """

        if stripAxisIndex < 0 or stripAxisIndex >= self.spectrumDisplay.dimensionCount:
            raise ValueError('%s._setAxisPositionAndWidth: invalid stripAxisIndex "%s"' %
                             (self.__class__.__name__, stripAxisIndex))
        _axis = self.orderedAxes[stripAxisIndex]

        if len(self._displayedSpectra) == 0:
            return

        # unfortunately, we need a spectrum with right dimensionality to do axis unit conversions
        # (for now). Take the first eligible one
        found = False
        sv = None
        for sv in self.spectrumViews:
            if sv.spectrum.dimensionCount == self.spectrumDisplay.dimensionCount:
                found = True
                break
        if not found or sv is None:
            raise RuntimeError('%s._setPositionAndWidth: no appropriate spectrum found for this display to do conversions' %
                               self.__class__.__name__
                               )
        _specDim = sv.spectrumDimensions[stripAxisIndex]

        _axis._incrementByUnit = self._minAxisIncrementByUnit[stripAxisIndex]
        _axis._minLimitByUnit = self._minAxisLimitsByUnit[stripAxisIndex]
        _axis._maxLimitByUnit = self._maxAxisLimitsByUnit[stripAxisIndex]
        position = max(_axis._minLimitByUnit, position)
        position = min(_axis._maxLimitByUnit, position)

        # for now: Axis.position and Axis.width are maintained in ppm; so conversion
        # depending on Axis.unit is required.
        if _axis.unit == AXISUNIT_PPM:
            _axis.position = position
            _axis._positionByUnit = position
            if width is not None:
                _axis.width = width
                _axis._widthByUnit = width

        elif _axis.unit == AXISUNIT_POINT:
            # change to ppm
            _axis.position = _specDim.pointToPpm(position)
            _axis._positionByUnit = position
            if width is not None:
                _axis.width = width * _specDim.ppmPerPoint
                _axis._widthByUnit = width

        elif _axis.unit == AXISUNIT_HZ:
            # change to ppm by scaling by spectrometerFrequencies
            _axis.position = position / _specDim.spectrometerFrequency
            _axis._positionByUnit = position
            if width is not None:
                _axis.width = width / _specDim.spectrometerFrequency
                _axis._widthByUnit = width

        else:
            getLogger().debug(f'Axis {_axis.unit} not found')
            return

        self._updatePlaneToolBarWidgets(stripAxisIndex)
        if refresh:
            self.refresh()

    def _initAxesValues(self,   spectrumView):
        """Initialiase the strip.axes using a spectrumView instance
        CCPNINTERNAL: used from _newSpectrumDisplay
        """
        from ccpn.util.Constants import AXISUNIT_NUMBER, AXISUNIT_POINT, AXISUNIT_PPM

        spectrum = spectrumView.spectrum
        axes = self.orderedAxes

        if spectrum.dimensionCount == 1:
            # 1D spectrum
            ppmLimits, valueLimits = spectrum.get1Dlimits()

            axes[0].region = ppmLimits
            axes[0]._positionByUnit = axes[0].position
            axes[0]._widthByUnit = axes[0].width

            axes[1].region = valueLimits
            axes[1].unit = AXISUNIT_NUMBER

        else:
            # nD
            for _axis, _specDim, dimIndex in zip(axes,
                                                 spectrumView.spectrumDimensions,
                                                 spectrumView.dimensionIndices
                                                 ):
                if _axis._index < 2:
                    # The X,Y axis of the strip
                    if spectrum.isTimeDomains[dimIndex] or spectrum.isSampledDomains[dimIndex]:
                        _axis.unit = AXISUNIT_POINT
                        self._setAxisPositionAndWidth(_axis._index,
                                                      position = float(_specDim.pointCount/2)+0.5,
                                                      width = float(_specDim.pointCount),
                                                      refresh = False
                        )
                    else:
                        _axis.unit = AXISUNIT_PPM
                        limits = _specDim.aliasingLimits
                        self._setAxisPositionAndWidth(_axis._index,
                                                      position = 0.5*(limits[0] + limits[1]),  # The centre
                                                      width = max(limits) - min(limits),
                                                      refresh = False
                        )

                else:
                    # A strip Z,A,... "plane-axis"
                    if spectrum.isTimeDomains[dimIndex] or spectrum.isSampledDomains[dimIndex]:
                        _axis.unit = AXISUNIT_POINT
                        self._setAxisPositionAndWidth(_axis._index,
                                                      position = 1.0,
                                                      width = 1.0,
                                                      refresh = False
                        )
                    else:
                        _axis.unit = AXISUNIT_PPM
                        limits = _specDim.spectrumLimits
                        self._setAxisPositionAndWidth(_axis._index,
                                                      position = 0.5*(limits[0] + limits[1]),  # The centre
                                                      width = _specDim.ppmPerPoint,
                                                      refresh = False
                        )
        # init the GL
        self._CcpnGLWidget.initialiseAxes(strip=self)

    #-----------------------------------------------------------------------------------------
    # Subclassed in nD
    #-----------------------------------------------------------------------------------------

    def _updatePlaneAxes(self):
        """A Convenience method to update plane-axis values.
        It uses the _changePlane() method; also updates the plane widgets
        """
        # Only implemented for nD
        pass

    def _changePlane(self, stripAxisIndex: int, planeIncrement:int, planeCount = None,
                           refresh:bool = True
                     ):
        """Change the position of plane-axis defined by stripAxisIndex by increment (in points)
        :param stripAxisIndex: an index, defining an Z, A, ... plane; i.e. >= 2
        :param planeIncrement: an integer defining number of planes to increment.
                               The actual ppm increment (for axis in ppm units) will be
                               the minimum ppm increment along stripAxisIndex.
        :param planeCount: the number of planes to display
        :param refresh: optionally refresh strip after setting values
        """
        # Only implemented for nD
        pass


#=========================================================================================
# Notifiers:
#=========================================================================================

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

# def _axisRegionChanged(cDict):
#     """Notifier function: Update strips etc. for when axis position or width changes.
#     """
#     axis = cDict[Notifier.OBJECT]
#     strip = axis.strip
#
#     position = axis.position
#     width = axis.width
#     region = (position - width / 2., position + width / 2.)
#
#     index = strip.axisOrder.index(axis.code)
#     if not strip.beingUpdated:
#
#         strip.beingUpdated = True
#
#         try:
#             if index == 0:
#                 # X axis
#                 padding = strip.application.preferences.general.stripRegionPadding
#                 strip.viewBox.setXRange(*region, padding=padding)
#             elif index == 1:
#                 # Y axis
#                 padding = strip.application.preferences.general.stripRegionPadding
#                 strip.viewBox.setYRange(*region, padding=padding)
#             else:
#
#                 if len(strip.axisOrder) > 2:
#                     n = index - 2
#                     if n >= 0:
#
#                         if strip.planeAxisBars and n < len(strip.planeAxisBars):
#                             # strip.planeAxisBars[n].setPosition(ppmPosition, ppmWidth)
#                             strip.planeAxisBars[n].updatePosition()
#
#                         # planeLabel = strip.planeToolbar.planeLabels[n]
#                         # planeSize = planeLabel.singleStep()
#                         # planeLabel.setValue(position)
#                         # strip.planeToolbar.planeCounts[n].setValue(width / planeSize)
#
#         finally:
#             strip.beingUpdated = False

# NB The following two notifiers could be replaced by wrapper notifiers on
# Mark, 'change'. But it would be rather more clumsy, so leave it as it is.

# def _rulerCreated(project: Project, apiRuler: ApiRuler):
#     """Notifier function for creating rulers"""
#     for strip in project.strips:
#         strip.plotWidget._addRulerLine(apiRuler)


# def _rulerDeleted(project: Project, apiRuler: ApiRuler):
#     """Notifier function for deleting rulers"""
#     for strip in project.strips:
#         strip.plotWidget._removeRulerLine(apiRuler)
