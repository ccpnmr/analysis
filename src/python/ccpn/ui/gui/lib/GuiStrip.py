"""
Module Documentation here
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

from ccpn.core.Peak import Peak
from ccpn.core.PeakList import PeakList
from ccpn.core.Project import Project
from ccpn.core.lib.Notifiers import Notifier, NotifierBase

from ccpn.ui.gui.guiSettings import getColours, GUISTRIP_PIVOT
from ccpn.ui.gui.guiSettings import textFontSmall
from ccpn.ui.gui.widgets.Button import Button
from ccpn.ui.gui.widgets.PlotWidget import PlotWidget
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.LineEdit import FloatLineEdit
from ccpn.ui.gui.widgets.Widget import Widget
from ccpn.ui.gui.widgets.PlaneToolbar import _StripLabel, StripHeader
from ccpn.ui.gui.widgets.Frame import Frame
from ccpn.ui.gui.widgets.Widget import Widget
from ccpn.ui.gui.lib.GuiNotifier import GuiNotifier
from ccpn.ui.gui.widgets.DropBase import DropBase
from ccpn.ui.gui.widgets import MessageDialog

from ccpn.ui.gui import guiSettings

from ccpn.util import Ticks
from ccpnmodel.ccpncore.api.ccpnmr.gui.Task import Ruler as ApiRuler
from ccpn.util.Logging import getLogger
from ccpn.util.Constants import AXIS_MATCHATOMTYPE, AXIS_FULLATOMNAME
from ccpn.util import Common as commonUtil
from typing import Tuple, List, Any
from functools import partial
from ccpn.ui.gui.lib.OpenGL.CcpnOpenGLDefs import AXISXUNITS, AXISYUNITS, AXISLOCKASPECTRATIO


STRIPLABEL_ISPLUS = 'stripLabel_isPlus'

DefaultMenu = 'DefaultMenu'
PeakMenu = 'PeakMenu'
IntegralMenu = 'IntegralMenu'
MultipletMenu = 'MultipletMenu'
PhasingMenu = 'PhasingMenu'


class GuiStrip(NotifierBase, Frame):

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

        # it appears to be required to explicitly set these, otherwise
        # the Widget will not fill all available space
        ###self.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        # The strip is responsive on restore to the contentMargins set here
        # self.setContentsMargins(5, 0, 5, 0)
        # self.setContentsMargins(10, 10, 10, 10)
        self.setMinimumWidth(50)
        self.setMinimumHeight(150)
        # self.layout().setSizeConstraint(QtWidgets.QLayout.SetNoConstraint)

        self.layout().setSpacing(0)

        self.header = StripHeader(parent=self, mainWindow=self.mainWindow,
                                  grid=(0, 0), gridSpan=(1, 2), setLayout=True, spacing=(0, 0))

        # self.plotWidget = PlotWidget(self, useOpenGL=useOpenGL)
        # self.plotWidget.setSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.MinimumExpanding)

        #showDoubleCrosshair = self.application.preferences.general.doubleCrossHair)
        # GWV: plotWidget appears not to be responsive to contentsMargins
        # self.plotWidget.setContentsMargins(10, 30, 10, 30)
        # self.getLayout().addWidget(self.plotWidget, 1, 0)
        # self.layout().setHorizontalSpacing(0)
        # self.layout().setVerticalSpacing(0)
        # self.plotWidget.showGrid(x=True, y=True, alpha=None)

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

        # self.plotWidgetOverlay = pg.PlotWidget(self, useOpenGL=useOpenGL)  #    make a copy
        # self.plotWidgetOverlay.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        # self.plotWidgetOverlay.resize(200, 200)
        # self.plotWidgetOverlay.setWindowFlags(QtCore.Qt.FramelessWindowHint)
        # self.plotWidgetOverlay.setAttribute(QtCore.Qt.WA_TranslucentBackground, True)
        # self.plotWidgetOverlay.showGrid(x=True, y=True, alpha=None)

        # Widgets for toolbar; items will be added by GuiStripNd (eg. the Z/A-plane boxes)
        # and GuiStrip1d; will be hidden for 2D's by GuiSpectrumView
        self._stripToolBarWidget = Widget(parent=self, setLayout=True,
                                          hPolicy='expanding',
                                          grid=(2, 0), spacing=(5, 5))

        # Widgets for _stripIdLabel and _stripLabel
        # self._labelWidget = Frame(parent=self, setLayout=True,
        #                            hPolicy='expanding', vAlign='center',
        # grid=(0, 0), spacing=(0,0))
        # self._labelWidget.layout().setHorizontalSpacing(0)
        # self._labelWidget.layout().setVerticalSpacing(0)
        # self._labelWidget.setFixedHeight(32)

        # display and pid
        #TODO:GEERTEN correct once pid has been reviewed
        # self._stripIdLabel = Label(parent=self._labelWidget,
        #                            text='.'.join(self.id.split('.')), margins=[0,0,0,0], spacing=(0,0),
        #                            grid=(0,0), gridSpan=(1,1), hAlign='left', vAlign='top', hPolicy='minimum')
        # self._stripIdLabel.setFont(textFontSmall)
        # TODO:ED check - have moved the label to the top-left corner
        # self.plotWidget.stripIDLabel.setText('.'.join(self.id.split('.')))

        # Displays a draggable label for the strip
        #TODO:GEERTEN reinsert a notifier for update in case this displays a nmrResidue
        # self._stripLabel = _StripLabel(parent=self._labelWidget,
        #                                text='', spacing=(0,0),
        #                                grid=(0,1), hAlign='c')    #, hAlign='left', vAlign='top', hPolicy='minimum')
        #
        # self._stripLabel.setSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum)
        # self._stripLabel.setFont(textFontSmall)
        #
        # self._stripResidueId = _StripLabel(parent=self._labelWidget,
        #                                text='', spacing=(0,0),
        #                                grid=(0,0), hAlign='l')
        # self._stripResidueId.setSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum)
        # self._stripResidueId.setFont(textFontSmall)
        # self._stripResidueId.hide()
        #
        # self._stripResidueDir = _StripLabel(parent=self._labelWidget,
        #                                text='', spacing=(0,0),
        #                                grid=(0,2), hAlign='r')
        # self._stripResidueDir.setSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum)
        # self._stripResidueDir.setFont(textFontSmall)
        # self._stripResidueDir.hide()

        # self._labelWidget.layout().setAlignment(QtCore.Qt.AlignTop)

        # Strip needs access to plotWidget's items and info #TODO: get rid of this
        # self.plotItem = self.plotWidget.plotItem
        self.viewStripMenu = None         # = self.plotItem.vb

        self._showCrossHair()
        # callbacks
        ###self.plotWidget.scene().sigMouseMoved.connect(self._mouseMoved)
        # self.plotWidget.scene().sigMouseMoved.connect(self._showMousePosition)  # update mouse cursors
        self.storedZooms = []

        self.beingUpdated = False
        # self.xPreviousRegion, self.yPreviousRegion = self.viewRange()

        # need to keep track of mouse position because Qt shortcuts don't provide
        # the widget or the position of where the cursor is
        self.axisPositionDict = {}  # axisCode --> position

        self._contextMenuMode = DefaultMenu

        self._contextMenus = {DefaultMenu: None,
                              PeakMenu: None,
                              PhasingMenu: None,
                              MultipletMenu: None,
                              IntegralMenu: None
                              }

        self.navigateToPeakMenu = None  #set from context menu and in CcpnOpenGL rightClick
        self.navigateToCursorMenu = None  #set from context menu and in CcpnOpenGL rightClick
        # self._initRulers()
        self._isPhasingOn = False
        # self.hPhasingPivot = pg.InfiniteLine(angle=90, movable=True)
        # self.hPhasingPivot.setVisible(False)
        # self.plotWidget.addItem(self.hPhasingPivot)
        # self.hPhasingPivot.sigPositionChanged.connect(lambda phasingPivot: self._movedPivot())
        # self.haveSetHPhasingPivot = False

        # self.vPhasingPivot = pg.InfiniteLine(angle=0, movable=True)
        # self.vPhasingPivot.setVisible(False)
        # self.plotWidget.addItem(self.vPhasingPivot)
        # self.vPhasingPivot.sigPositionChanged.connect(lambda phasingPivot: self._movedPivot())
        # self.haveSetVPhasingPivot = False

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
        self.setGuiNotifier(self,[GuiNotifier.DROPEVENT], [DropBase.URLS, DropBase.PIDS],
                            self.spectrumDisplay._processDroppedItems)
        self.setGuiNotifier(self,[GuiNotifier.DRAGMOVEEVENT], [DropBase.URLS, DropBase.PIDS],
                            self.spectrumDisplay._processDragEnterEvent)

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
                # self._CcpnGLWidget._updateHTrace = spectrumDisplay.strips[0]._CcpnGLWidget._updateHTrace
                # self._CcpnGLWidget._updateVTrace = spectrumDisplay.strips[0]._CcpnGLWidget._updateVTrace
                # self.hTraceAction.setChecked(self._CcpnGLWidget._updateHTrace)
                # self.vTraceAction.setChecked(self._CcpnGLWidget._updateVTrace)

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

        # self.plotWidget.grid.setVisible(self.application.preferences.general.showGrid)

        self._storedPhasingData = [[0.0, 0.0, 0.0], [0.0, 0.0, 0.0]]

        try:
            self._CcpnGLWidget.gridVisible = self.application.preferences.general.showGrid
            # set the axis units from the current settings
            self._CcpnGLWidget.xUnits = settings[AXISXUNITS]
            self._CcpnGLWidget.yUnits = settings[AXISYUNITS]
            self._CcpnGLWidget.axisLocked = settings[AXISLOCKASPECTRATIO]
        except Exception as es:
            getLogger().debugGL('OpenGL widget not instantiated')

        # self._stripToolBarWidget.setSizePolicy(QtWidgets.QSizePolicy.Ignored, QtWidgets.QSizePolicy.Preferred)
        # self._labelWidget.setSizePolicy(QtWidgets.QSizePolicy.Ignored, QtWidgets.QSizePolicy.Ignored)
        # self._stripLabel.setSizePolicy(QtWidgets.QSizePolicy.Ignored, QtWidgets.QSizePolicy.Ignored)

        # self.show()

    # def mouseMoveEvent(self, a0: QtGui.QMouseEvent):
    #     print('>>>mouseMove')

    def viewRange(self):
        return self._CcpnGLWidget.viewRange()

    @property
    def gridIsVisible(self):
        "True if grid is visible"

        try:
            return self._CcpnGLWidget.gridVisible
        except Exception as es:
            getLogger().debugGL('OpenGL widget not instantiated')

        # return self.plotWidget.grid.isVisible()

    @property
    def crossHairIsVisible(self):
        "True if crosshair is visible"

        try:
            return self._CcpnGLWidget.crossHairVisible
        except Exception as es:
            getLogger().debugGL('OpenGL widget not instantiated')

        # return self.plotWidget.crossHair1.isVisible()

    # @property
    # def mouseMode(self):
    #   """Get the mouseMode from the mainWindow"""
    #   return self.application.ui.mainWindow.mouseMode

    @property
    def pythonConsole(self):
        return self.mainWindow.pythonConsole

    # def getStripLabel(self):
    #   """Return the stripLabel widget"""
    #   return self._stripLabel
    #
    # def setStripLabelText(self, text: str):
    #   """set the text of the _stripLabel"""
    #   if text is not None:
    #     self._stripLabel.setText(text)
    #
    # def getStripLabelText(self) -> str:
    #   """return the text of the _stripLabel"""
    #   return self._stripLabel.text()
    #
    # def showStripLabel(self, doShow: bool=True):
    #   """show / hide the _stripLabel"""
    #   self._stripLabel.setVisible(doShow)
    #
    # def hideStripLabel(self):
    #   "Hide the _stripLabel; convienience"
    #   self._stripLabel.setVisible(False)

    def _openCopySelectedPeaks(self):
        from ccpn.ui.gui.popups.CopyPeaksPopup import CopyPeaks

        popup = CopyPeaks(parent=self.mainWindow, mainWindow=self.mainWindow)
        peaks = self.current.peaks
        popup._selectPeaks(peaks)
        popup.exec()
        popup.raise_()

    def _updateStripLabel(self, callbackDict):
        "Update the striplabel if it represented a NmrResidue that has changed its id"
        # text = self.getStripLabelText()

        text = self.header.getLabelText(position='c')
        if callbackDict['oldPid'] == text:
            self.header.setLabelText(position='c', text=callbackDict['object'].pid)

            # self.setStripLabelText(callbackDict['object'].pid)

        # try:
        #   self._CcpnGLWidget.setStripID(callbackDict['object'].pid)
        # except Exception as es:
        #   getLogger().debugGL('OpenGL widget not instantiated', strip=self, error=es)

    # def setStripLabelisPlus(self, isPlus: bool):
    #   """set the isPlus attribute of the _stripResidueId"""
    #   self._stripLabel._isPlus = isPlus
    #
    # def getStripResidueId(self):
    #   """Return the stripResidueId widget"""
    #   return self._stripResidueId
    #
    # def setStripResidueIdText(self, text: str):
    #   """set the text of the _stripResidueId"""
    #   if text is not None:
    #     self._stripResidueId.setText(text)
    #
    # def getStripResidueIdText(self) -> str:
    #   """return the text of the _stripResidueId"""
    #   return self._stripResidueId.text()
    #
    # def showStripResidueId(self, doShow: bool=True):
    #   """show / hide the _stripResidueId"""
    #   self._stripResidueId.setVisible(doShow)
    #   if doShow:
    #     self._labelWidget.setFixedHeight(32)
    #   else:
    #     self._labelWidget.setFixedHeight(32)
    #
    # def hideStripResidueId(self):
    #   "Hide the _stripResidueId; convienience"
    #   self._stripResidueId.setVisible(False)
    #   self._labelWidget.setFixedHeight(32)
    #
    # def getStripResidueDir(self):
    #   """Return the stripResidueDir widget"""
    #   return self._stripResidueDir
    #
    # def setStripResidueDirText(self, text: str):
    #   """set the text of the _stripResidueDir"""
    #   if text is not None:
    #     self._stripResidueDir.setText(text)
    #
    # def getStripResidueDirText(self) -> str:
    #   """return the text of the _stripResidueDir"""
    #   return self._stripResidueDir.text()
    #
    # def showStripResidueDir(self, doShow: bool=True):
    #   """show / hide the _stripResidueDir"""
    #   self._stripResidueDir.setVisible(doShow)
    #   if doShow:
    #     self._labelWidget.setFixedHeight(32)
    #   else:
    #     self._labelWidget.setFixedHeight(32)
    #
    # def hideStripResidueDir(self):
    #   "Hide the _stripResidueDir; convienience"
    #   self._stripResidueDir.setVisible(False)
    #   self._labelWidget.setFixedHeight(32)

    def createMark(self):
        """
        Sets the marks at current position
        """
        self.spectrumDisplay.mainWindow.createMark()

    def clearMarks(self):
        """
        Sets the marks at current position
        """
        self.spectrumDisplay.mainWindow.clearMarks()

    def estimateNoise(self):
        """
        Estimate noise in the current region
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
        ''' Adds item to navigate to peak position from context menu'''
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
        ''' Copied from old viewbox. This function apparently take the current cursorPosition
         and uses to pan a selected display from the list of spectrumViews or the current cursor position
        TODO needs clear documentation'''
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
        """Callback when integrals have changed
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

    # def _printToFile(self, printer):
    #     # CCPN INTERNAL - called in printToFile method of GuiMainWindow
    #
    #     for spectrumView in self.spectrumViews:
    #         spectrumView._printToFile(printer)
    #
    #     # print box
    #
    #     # print ticks and grid line
    #     viewRegion = self.plotWidget.viewRange()
    #     v1, v0 = viewRegion[0]  # TBD: relies on axes being backwards
    #     w1, w0 = viewRegion[1]  # TBD: relies on axes being backwards, which is not true in 1D
    #     xMajorTicks, xMinorTicks, xMajorFormat = Ticks.findTicks((v0, v1))
    #     yMajorTicks, yMinorTicks, yMajorFormat = Ticks.findTicks((w0, w1))
    #
    #     xScale = (printer.x1 - printer.x0) / (v1 - v0)
    #     xOffset = printer.x0 - xScale * v0
    #     yScale = (printer.y1 - printer.y0) / (w1 - w0)
    #     yOffset = printer.y0 - yScale * w0
    #     xMajorText = [xMajorFormat % tick for tick in xMajorTicks]
    #     xMajorTicks = [tick * xScale + xOffset for tick in xMajorTicks]
    #     xMinorTicks = [tick * xScale + xOffset for tick in xMinorTicks]
    #     yMajorText = [xMajorFormat % tick for tick in yMajorTicks]
    #     yMajorTicks = [tick * yScale + yOffset for tick in yMajorTicks]
    #     yMinorTicks = [tick * yScale + yOffset for tick in yMinorTicks]
    #
    #     xTickHeight = yTickHeight = max(printer.y1 - printer.y0, printer.x1 - printer.x0) * 0.01
    #
    #     for tick in xMinorTicks:
    #         printer.writeLine(tick, printer.y0, tick, printer.y0 + 0.5 * xTickHeight)
    #
    #     fontsize = 10
    #     for n, tick in enumerate(xMajorTicks):
    #         if self.plotWidget.grid.isVisible():
    #             printer.writeLine(tick, printer.y0, tick, printer.y1, colour='#888888')
    #         printer.writeLine(tick, printer.y0, tick, printer.y0 + xTickHeight)
    #         text = xMajorText[n]
    #         printer.writeText(text, tick - 0.5 * len(text) * fontsize * 0.7, printer.y0 + xTickHeight + 1.5 * fontsize)
    #
    #     # output backwards for y
    #     for tick in yMinorTicks:
    #         printer.writeLine(printer.x0, printer.y1 - tick, printer.x0 + 0.5 * yTickHeight, printer.y1 - tick)
    #
    #     for n, tick in enumerate(yMajorTicks):
    #         if self.plotWidget.grid.isVisible():
    #             printer.writeLine(printer.x0, printer.y1 - tick, printer.x1, printer.y1 - tick, colour='#888888')
    #         printer.writeLine(printer.x0, printer.y1 - tick, printer.x0 + yTickHeight, printer.y1 - tick)
    #         text = yMajorText[n]
    #         printer.writeText(text, printer.x0 + yTickHeight + 0.5 * fontsize * 0.7, printer.y1 - tick + 0.5 * fontsize)

    def _newPhasingTrace(self):

        try:
            self._CcpnGLWidget.newTrace()
        except Exception as es:
            getLogger().debugGL('OpenGL widget not instantiated')

        return

        for spectrumView in self.spectrumViews:
            spectrumView._newPhasingTrace()

    """
    def newHPhasingTrace(self):
      
      for spectrumView in self.spectrumViews:
        spectrumView.newHPhasingTrace(self.mousePosition[1])
        
    def newVPhasingTrace(self):
      
      for spectrumView in self.spectrumViews:
        spectrumView.newVPhasingTrace(self.mousePosition[0])
    """

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

        #     return
        #     for spectrumView in self.spectrumViews:
        #         spectrumView.removePhasingTraces()
        #
        # """
        # def togglePhasingPivot(self):
        #
        #   self.hPhasingPivot.setPos(self.mousePosition[0])
        #   self.hPhasingPivot.setVisible(not self.hPhasingPivot.isVisible())
        # """

    def _updatePivot(self):  # this is called if pivot entry at bottom of display is updated and then "return" key used

        # update the static traces from the phasing console
        # redraw should update the display
        try:
            self._CcpnGLWidget.rescaleStaticTraces()
        except:
            getLogger().debugGL('OpenGL widget not instantiated')

        # return
        #
        # phasingFrame = self.spectrumDisplay.phasingFrame
        # position = phasingFrame.pivotEntry.get()
        # direction = phasingFrame.getDirection()
        # if direction == 0:
        #     self.hPhasingPivot.setPos(position)
        # else:
        #     self.vPhasingPivot.setPos(position)
        # self._updatePhasing()

    # def _movedPivot(self):  # this is called if pivot on screen is dragged
    #
    #     phasingFrame = self.spectrumDisplay.phasingFrame
    #     direction = phasingFrame.getDirection()
    #     if direction == 0:
    #         position = self.hPhasingPivot.getXPos()
    #     else:
    #         position = self.vPhasingPivot.getYPos()
    #
    #     phasingFrame.pivotEntry.set(position)
    #     self._updatePhasing()

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

            # TODO:ED don't need as menu will change
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

        # phasingFrame.setDirection(1-direction)
        # self.spectrumDisplay._storedPhasingData[1-direction] = [phasingFrame.slider0.value(),
        #                                                         phasingFrame.slider1.value(),
        #                                                         phasingFrame.pivotEntry.get()]

        if not phasingFrame.isVisible():
            return

        # if direction == 0:
        #     self.hPhasingPivot.setVisible(True)
        #     self.vPhasingPivot.setVisible(False)
        #     # self.pivotLine.orientation = ('v')
        # else:
        #     self.hPhasingPivot.setVisible(False)
        #     self.vPhasingPivot.setVisible(True)
        #     # self.pivotLine.orientation = ('h')

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

        # update the static traces from the phasing console
        # redraw should update the display
        try:
            if self.spectrumDisplay.phasingFrame.isVisible():
                colour = getColours()[GUISTRIP_PIVOT]
                self._CcpnGLWidget.setInfiniteLineColour(self.pivotLine, colour)
                self._CcpnGLWidget.rescaleStaticTraces()
        except:
            getLogger().debugGL('OpenGL widget not instantiated', spectrumDisplay=self.spectrumDisplay, strip=self)

        # return
        #
        # # TODO:GEERTEN: Fix  (not yet picked-up!; why? - ED: old code, return statement above)
        # colour = getColours()[GUISTRIP_PIVOT]
        # self.hPhasingPivot.setPen({'color': colour})
        # self.vPhasingPivot.setPen({'color': colour})
        # for spectrumView in self.spectrumViews:
        #     spectrumView.setPivotColour(colour)
        #     spectrumView._updatePhasing()

    # def _updateXRegion(self, viewBox):
    #     # this is called when the viewBox is changed on the screen via the mouse
    #     # this code is complicated because need to keep viewBox region and axis region in sync
    #     # and there can be different viewBoxes with the same axis
    #
    #     if not self._finaliseDone: return
    #
    #     assert viewBox is self.viewBox, 'viewBox = %s, self.viewBox = %s' % (viewBox, self.viewBox)
    #
    #     self._updateX()
    #     self._updatePhasing()
    #
    # def _updateYRegion(self, viewBox):
    #     # this is called when the viewBox is changed on the screen via the mouse
    #     # this code is complicated because need to keep viewBox region and axis region in sync
    #     # and there can be different viewBoxes with the same axis
    #
    #     if not self._finaliseDone: return
    #
    #     assert viewBox is self.viewBox, 'viewBox = %s, self.viewBox = %s' % (viewBox, self.viewBox)
    #
    #     self._updateY()
    #     self._updatePhasing()

    # def _updateX(self):
    #
    #     def _widthsChangedEnough(r1, r2, tol=1e-5):
    #         r1 = sorted(r1)
    #         r2 = sorted(r2)
    #         minDiff = abs(r1[0] - r2[0])
    #         maxDiff = abs(r1[1] - r2[1])
    #         return (minDiff > tol) or (maxDiff > tol)
    #
    #     if not self._finaliseDone: return
    #
    #     # this only wants to get the scaling of the modified strip and not the actual values
    #
    #     xRange = list(self.viewBox.viewRange()[0])
    #     for strip in self.spectrumDisplay.strips:
    #         if strip is not self:
    #             stripXRange = list(strip.viewBox.viewRange()[0])
    #             if _widthsChangedEnough(stripXRange, xRange):
    #                 # TODO:ED check whether the strip has a range set yet
    #                 diff = (xRange[1] - xRange[0]) / 2.0
    #                 mid = (stripXRange[1] + stripXRange[0]) / 2.0
    #                 xRange = (mid - diff, mid + diff)
    #
    #                 strip.viewBox.setXRange(*xRange, padding=0)

    # def _updateY(self):
    #
    #     def _widthsChangedEnough(r1, r2, tol=1e-5):
    #         r1 = sorted(r1)
    #         r2 = sorted(r2)
    #         minDiff = abs(r1[0] - r2[0])
    #         maxDiff = abs(r1[1] - r2[1])
    #         return (minDiff > tol) or (maxDiff > tol)
    #
    #     if not self._finaliseDone: return
    #
    #     yRange = list(self.viewBox.viewRange()[1])
    #     for strip in self.spectrumDisplay.strips:
    #         if strip is not self:
    #             stripYRange = list(strip.viewBox.viewRange()[1])
    #             if _widthsChangedEnough(stripYRange, yRange):
    #                 strip.viewBox.setYRange(*yRange, padding=0)

    def _toggleCrossHair(self):
        " Toggles whether crosshair is visible"
        # self.plotWidget.crossHair1.toggle()
        # if self.spectrumViews and self.spectrumViews[0].spectrum.showDoubleCrosshair:
        #     self.plotWidget.crossHair2.toggle()

        try:
            self.crosshairVisible = not self.crosshairVisible
            self._CcpnGLWidget.crossHairVisible = self.crosshairVisible
        except:
            getLogger().debugGL('OpenGL widget not instantiated')

    def _showCrossHair(self):
        "Displays crosshair in strip"
        # self.plotWidget.crossHair1.show()
        # if self.spectrumViews and self.spectrumViews[0].spectrum.showDoubleCrosshair:
        #   self.plotWidget.crossHair2.show()

        try:
            self.crosshairVisible = True
            self._CcpnGLWidget.crossHairVisible = True
        except:
            getLogger().debugGL('OpenGL widget not instantiated')

    def _hideCrossHair(self):
        "Hides crosshair in strip."
        # self.plotWidget.crossHair1.hide()
        # if self.spectrumViews and self.spectrumViews[0].spectrum.showDoubleCrosshair:
        #   self.plotWidget.crossHair2.hide()

        try:
            self.crosshairVisible = False
            self._CcpnGLWidget.crossHairVisible = False
        except:
            getLogger().debugGL('OpenGL widget not instantiated')

    def _toggleShowSpectraOnPhasing(self):
        " Toggles whether spectraOnPhasing is visible"
        try:
            self.showSpectraOnPhasing = not self.showSpectraOnPhasing
            self._CcpnGLWidget.showSpectraOnPhasing = self.showSpectraOnPhasing
        except:
            getLogger().debugGL('OpenGL widget not instantiated')

    def _showSpectraOnPhasing(self):
        "Displays spectraOnPhasing in strip"
        try:
            self.showSpectraOnPhasing = True
            self._CcpnGLWidget.showSpectraOnPhasing = True
        except:
            getLogger().debugGL('OpenGL widget not instantiated')

    def _hideSpectraOnPhasing(self):
        "Hides spectraOnPhasing in strip."
        try:
            self.showSpectraOnPhasing = False
            self._CcpnGLWidget.showSpectraOnPhasing = False
        except:
            getLogger().debugGL('OpenGL widget not instantiated')

    def toggleGrid(self):
        "Toggles whether grid is visible in the strip."
        # self.plotWidget.toggleGrid()

        try:
            self.gridVisible = not self.gridVisible
            self._CcpnGLWidget.gridVisible = self.gridVisible
        except:
            getLogger().debugGL('OpenGL widget not instantiated')

    def cyclePeakLabelling(self):
        """Toggles whether peak labelling is minimal is visible in the strip
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
        """Cycle through peak symbol types
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
        # determines what axisCodes are compatible as far as drawing crosshair is concerned
        # TBD: the naive approach below should be improved
        return axisCode  #if axisCode[0].isupper() else axisCode

    def _createMarkAtCursorPosition(self):
        try:
            # colourDict = guiSettings.MARK_LINE_COLOUR_DICT  # maps atomName --> colour

            positions = [self.current.mouseMovedDict[AXIS_FULLATOMNAME][ax] for ax in self.axisCodes]
            defaultColour = self.application.preferences.general.defaultMarksColour
            self._project.newMark(defaultColour, positions, self.axisCodes)

        except Exception as es:
            getLogger().warning('Error setting mark at current cursor position')
            raise(es)

    # # TODO: remove apiRuler (when notifier at bottom of module gets rid of it)
    # def _initRulers(self):
    #
    #     for mark in self._project.marks:
    #         apiMark = mark._wrappedData
    #         for apiRuler in apiMark.rulers:
    #             self.plotWidget._addRulerLine(apiRuler)

    def _showMousePosition(self, pos: QtCore.QPointF):
        """
        Displays mouse position for both axes by axis code.
        """
        if not self._finaliseDone: return

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

        # self._cursorLabel.setText(format %
        #   (self.axisOrder[0], position.x(), self.axisOrder[1], position.y())
        # )

        # self.plotWidget.mouseLabel.setText(format %
        #                                    (self.axisOrder[0], position.x(), self.axisOrder[1], position.y())
        #                                    )
        # self.plotWidget.mouseLabel.setPos(position.x(), position.y())
        # self.plotWidget.mouseLabel.show()

    def zoom(self, xRegion: typing.Tuple[float, float], yRegion: typing.Tuple[float, float]):
        """Zooms strip to the specified region
        """
        try:
            self._CcpnGLWidget.zoom(xRegion, yRegion)
        except:
            getLogger().debugGL('OpenGL widget not instantiated')

    # def zoomToRegion(self, xRegion: typing.Tuple[float, float], yRegion: typing.Tuple[float, float]):
    #     """
    #     Zooms strip to the specified region
    #     """
    #     if not self._finaliseDone: return
    #     padding = self.application.preferences.general.stripRegionPadding
    #     self.viewBox.setXRange(*xRegion, padding=padding)
    #     self.viewBox.setYRange(*yRegion, padding=padding)

    def zoomX(self, x1: float, x2: float):
        """
        Zooms x axis of strip to the specified region
        """
        if not self._finaliseDone: return

        padding = self.application.preferences.general.stripRegionPadding
        self.viewBox.setXRange(x1, x2, padding=padding)

    def zoomY(self, y1: float, y2: float):
        """
        Zooms y axis of strip to the specified region
        """
        if not self._finaliseDone: return
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
        """
        Adds current region to the zoom stack for the strip.
        """
        # self.storedZooms.append(self.viewBox.viewRange())

        try:
            self._CcpnGLWidget.storeZoom()
        except:
            getLogger().debugGL('OpenGL widget not instantiated')

    def _restoreZoom(self):
        """
        Restores last saved region to the zoom stack for the strip.
        """
        # if not self._finaliseDone: return

        # if len(self.storedZooms) != 0:
        #     restoredZoom = self.storedZooms.pop()
        #     padding = self.application.preferences.general.stripRegionPadding
        #     self.plotWidget.setXRange(restoredZoom[0][0], restoredZoom[0][1], padding=padding)
        #     self.plotWidget.setYRange(restoredZoom[1][0], restoredZoom[1][1], padding=padding)
        # else:
        #     self.resetZoom()

        try:
            self._CcpnGLWidget.restoreZoom()
        except:
            getLogger().debugGL('OpenGL widget not instantiated')

    # def resetZoom(self):
    #   """
    #   Zooms both axis of strip to the specified region
    #   """
    #   padding = self.application.preferences.general.stripRegionPadding
    #   self.viewBox.autoRange(padding=padding)

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
        """
        zoom in to the strip.
        """
        # if not self._finaliseDone: return

        # zoomPercent = -self.application.preferences.general.zoomPercent / 100.0
        # padding = self.application.preferences.general.stripRegionPadding
        # currentRange = self.viewBox.viewRange()
        # l = currentRange[0][0]
        # r = currentRange[0][1]
        # b = currentRange[1][0]
        # t = currentRange[1][1]
        # dx = (r - l) / 2.0
        # dy = (t - b) / 2.0
        # nl = l - zoomPercent * dx
        # nr = r + zoomPercent * dx
        # nt = t + zoomPercent * dy
        # nb = b - zoomPercent * dy
        # self.plotWidget.setXRange(nl, nr, padding=padding)
        # self.plotWidget.setYRange(nb, nt, padding=padding)

        try:
            self._CcpnGLWidget.zoomIn()
        except:
            getLogger().debugGL('OpenGL widget not instantiated')

    def _zoomOut(self):
        """
        zoom out of the strip.
        """
        # if not self._finaliseDone: return

        # zoomPercent = +self.application.preferences.general.zoomPercent / 100.0
        # padding = self.application.preferences.general.stripRegionPadding
        # currentRange = self.viewBox.viewRange()
        # l = currentRange[0][0]
        # r = currentRange[0][1]
        # b = currentRange[1][0]
        # t = currentRange[1][1]
        # dx = (r - l) / 2.0
        # dy = (t - b) / 2.0
        # nl = l - zoomPercent * dx
        # nr = r + zoomPercent * dx
        # nt = t + zoomPercent * dy
        # nb = b - zoomPercent * dy
        # self.plotWidget.setXRange(nl, nr, padding=padding)
        # self.plotWidget.setYRange(nb, nt, padding=padding)

        try:
            self._CcpnGLWidget.zoomOut()
        except:
            getLogger().debugGL('OpenGL widget not instantiated')

    # def showPeaks(self, peakList: PeakList, peaks: typing.List[Peak] = None):
    #     ###from ccpn.ui.gui.modules.spectrumItems.GuiPeakListView import GuiPeakListView
    #     # NBNB TBD 1) we should not always display all peak lists together
    #     # NBNB TBD 2) This should not be called for each strip
    #
    #     # Redundant but still removing
    #
    #     return

    # if not peaks:
    #     peaks = peakList.peaks
    #
    # peakListView = self._findPeakListView(peakList)
    # if not peakListView:
    #     return
    #
    # peaks = [peak for peak in peaks if self.peakIsInPlane(peak) or self.peakIsInFlankingPlane(peak)]
    # self.spectrumDisplay.showPeaks(peakListView, peaks)

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
        """
        Generate a drawing object that can be added to reports
        :return reportlab drawing object:
        """
        if self._CcpnGLWidget:
            # from ccpn.ui.gui.lib.OpenGL.CcpnOpenGLExport import GLExporter

            glReport = self._CcpnGLWidget.exportToSVG()
            if glReport:
                return glReport.report()

    def axisRegionChanged(self, axis):
        """Notifier function: Update strips etc. for when axis position or width changes
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
        """Move strip to index newIndex in orderedStrips
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

        _undo = self.project._undo
        self._startCommandEchoBlock('moveTo', newIndex)
        try:
            # management of API objects

            if _undo is not None:
                _undo._newItem(undoPartial=partial(self.spectrumDisplay.showAxes))

            self._wrappedData.moveTo(newIndex)

            if _undo is not None:
                _undo.newItem(self._resetStripLayout, self._resetStripLayout,
                              undoArgs=(newIndex, currentIndex), redoArgs=(currentIndex, newIndex))
                _undo._newItem(redoPartial=partial(self.spectrumDisplay.showAxes))

        finally:
            self._endCommandEchoBlock()

        # reorder the strips in the layout
        self._resetStripLayout(currentIndex, newIndex)

        # # rebuild the axes for each strip
        # self.spectrumDisplay.showAxes()

        return

        # from ccpn.core.lib.ContextManagers import logCommandManager, blockUndoItems
        # from functools import partial
        #
        # with logCommandManager(get='self') as log:
        #     log('moveTo')
        #
        #     with blockUndoItems() as addUndoItem:
        #         # needs to be first as it uses currentOrdering
        #         addUndoItem(undo=partial(self.spectrumDisplay.showAxes))
        #
        #     self.moveStrip(newIndex)
        #
        #     # reorder the strips ordering class
        #     strips = self.spectrumDisplay.strips
        #     order = list(self.spectrumDisplay._stripOrdering.getOrder())
        #     ind = strips.index(self)
        #     val = order.pop(ind)
        #     order.insert(newIndex, val)
        #     self.spectrumDisplay._stripOrdering.setOrder(tuple(order))
        #
        #     # add undo item to reorder the strips in the layout
        #     with blockUndoItems() as addUndoItem:
        #         addUndoItem(undo=partial(self._resetStripLayout, newIndex, currentIndex),
        #                  redo=partial(self._resetStripLayout, currentIndex, newIndex))
        #         addUndoItem(redo=partial(self.spectrumDisplay.showAxes))
        #
        #     if _undo is not None:
        #         _undo.decreaseBlocking()
        #         # _undo.newItem(newStrip.delete, newStrip._unDelete)
        #         _undo.newItem(self.spectrumDisplay.removeStrip, self.spectrumDisplay._unDelete,
        #                       undoArgs=(newStrip,), redoArgs=(newStrip,))
        #
        # # reorder the strips in the layout
        # self._resetStripLayout(currentIndex, newIndex)
        #
        # # rebuild the axes for each strip
        # self.spectrumDisplay.showAxes()

    def deleteStrip(self):
        """Overrides normal delete"""
        # currentStripItem = self._getWidgetFromLayout()
        # self.setParent(None)

        # ccpnStrip = self._wrappedData
        # n = len(ccpnStrip.spectrumDisplay.strips)
        n = self.spectrumDisplay.stripCount
        if n > 1:
            spectrumDisplay = self.spectrumDisplay
            layout = spectrumDisplay.stripFrame.layout()

            if layout:  # should always be the case but play safe

                self._removeFromLayout()  # adds nothing to the undo stack, so add it below

                _undo = self.project._undo
                if _undo is not None:
                    _undo.newItem(self._restoreToLayout, self._removeFromLayout)

                # save the deleted api object
                self._storeStripDelete()
                # self._unDeleteCall, self._unDeleteArgs = self._recoverApiObject(self)

                # # reorder the strips ordering class
                # strips = spectrumDisplay.strips
                # # order = list(spectrumDisplay._stripOrdering.getOrder())
                # order = list(spectrumDisplay.stripOrder)
                # ind = strips.index(self)
                # val = order.pop(ind)
                # order = [o if o < val else (o - 1) for o in order]

                # delete the strip
                self._delete()
                # ccpnStrip.delete()

                # spectrumDisplay._stripOrdering.setOrder(tuple(order))
                # spectrumDisplay.stripOrder = order

            self.current.strip = spectrumDisplay.strips[-1]
        else:
            raise ValueError("The last strip in a display cannot be deleted")

    def _unDelete(self):
        """Overrides normal delete"""
        # currentStripItem = self._getWidgetFromLayout()
        # self.setParent(None)

        # recover the deleted apiStrip
        self._storeStripUnDelete()
        # self._unDeleteCall(*self._unDeleteArgs)

        # ccpnStrip = self._wrappedData
        # n = len(ccpnStrip.spectrumDisplay.strips)
        n = self.spectrumDisplay.stripCount

        if n > 1:
            spectrumDisplay = self.spectrumDisplay
            layout = spectrumDisplay.stripFrame.layout()

            if layout:  # should always be the case but play safe

                self._restoreToLayout()  # adds nothing to the undo stack, so add it below

                _undo = self.project._undo
                if _undo is not None:
                    _undo.newItem(self._removeFromLayout, self._restoreToLayout)

            self.current.strip = spectrumDisplay.strips[-1]

        else:
            raise ValueError("The last strip in a display cannot be deleted")

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

    def _removeFromLayout(self):
        """Remove the current strip from the layout and store in the temporary area for undoing
        (contained in mainWindow)
        CCPN Internal
        """
        spectrumDisplay = self.spectrumDisplay
        index = self.stripIndex()

        layout = spectrumDisplay.stripFrame.layout()
        n = layout.count()

        if n > 1 and layout:
            _undo = self.project._undo
            if _undo is not None:
                _undo.increaseBlocking()

            currentIndex = index

            # clear the layout and rebuild
            self._widgets = []
            while layout.count():
                self._widgets.append(layout.takeAt(0).widget())
            self._widgets.remove(self)

            if spectrumDisplay.stripDirection == 'Y':
                for m, widgStrip in enumerate(self._widgets):  # build layout again
                    layout.addWidget(widgStrip, 0, m)
                    layout.setColumnStretch(m, 1)
                    layout.setColumnStretch(m + 1, 0)
            elif spectrumDisplay.stripDirection == 'X':
                for m, widgStrip in enumerate(self._widgets):  # build layout again
                    layout.addWidget(widgStrip, m, 0)
                layout.setColumnStretch(0, 1)

            # move to widget store
            self.mainWindow._UndoWidgetStorage.layout().addWidget(self)
            # self.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents, True)

            _undo = self.project._undo
            if _undo is not None:
                _undo.decreaseBlocking()

            # store the old information
            self._storeStripDeleteDict(currentIndex)

            # rebuild the axes for each strip
            self.spectrumDisplay.showAxes()

        else:
            raise ValueError("The last strip in a display cannot be deleted")

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

    def _restoreToLayout(self):
        """Restore the current strip to the layout from the temporary undo area
        (currently contained in mainWindow)
        CCPN Internal
        """
        # ccpnStrip = self._wrappedData
        spectrumDisplay = self.spectrumDisplay
        layout = spectrumDisplay.stripFrame.layout()

        if layout:
            from ccpn.core.lib.ContextManagers import undoBlock

            with undoBlock():
                # retrieve the old index from storageDict
                currentIndex = self._getStripDeleteDict()

                self.mainWindow._UndoWidgetStorage.layout().removeWidget(self)
                # self.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents, False)

                # clear the layout and rebuild
                self._widgets = []
                while layout.count():
                    self._widgets.append(layout.takeAt(0).widget())
                self._widgets.insert(currentIndex, self)

                if spectrumDisplay.stripDirection == 'Y':
                    for m, widgStrip in enumerate(self._widgets):  # build layout again
                        layout.addWidget(widgStrip, 0, m)
                        layout.setColumnStretch(m, 1)
                elif spectrumDisplay.stripDirection == 'X':
                    for m, widgStrip in enumerate(self._widgets):  # build layout again
                        layout.addWidget(widgStrip, m, 0)
                    layout.setColumnStretch(0, 1)

                # put ccpnStrip back into strips using the api
                # if self not in ccpnStrip.spectrumDisplay.strips:
                if self not in self.spectrumDisplay.strips:
                    for order, cStrip in enumerate(self._widgets):
                        # cStrip._wrappedData.__dict__['index'] = order  # this is the api creation of orderedStrips
                        cStrip._setStripIndex(order)

            # rebuild the axes for each strip
            self.spectrumDisplay.showAxes()

    def _raiseContextMenu(self, event: QtGui.QMouseEvent):
        """
        Raise the context menu
        """

        position = event.screenPos()
        self.viewStripMenu.popup(QtCore.QPoint(int(position.x()),
                                             int(position.y())))
        self.contextMenuPosition = self.current.cursorPosition

    # def peakPickPosition(self, inPosition) -> Tuple[Peak]:
    #     """
    #     Pick peak at position for all spectra currently displayed in strip
    #     """
    #     _preferences = self.application.preferences.general
    #
    #     result = []
    #     peakLists = []
    #
    #     self._startCommandEchoBlock('peakPickPosition', inPosition)  #Dict)
    #     self._project.blankNotification()
    #     try:
    #         for spectrumView in self.spectrumViews:
    #
    #             # check whether there any peakLists attached to the spectrumView - could be peakLists or integralLists
    #             numPeakLists = [pp for pp in spectrumView.peakListViews if isinstance(pp.peakList, PeakList)]
    #             if not numPeakLists:  # this can happen if no peakLists, so create one
    #                 # if not spectrumView.peakListViews:    # this can happen if no peakLists, so create one
    #                 self._project.unblankNotification()  # need this otherwise SideBar does not get updated
    #                 spectrumView.spectrum.newPeakList()
    #                 self._project.blankNotification()
    #
    #             validPeakListViews = [pp for pp in spectrumView.peakListViews if isinstance(pp.peakList, PeakList)
    #                                   and pp.isVisible()
    #                                   and spectrumView.isVisible()]
    #             for thisPeakListView in validPeakListViews:
    #                 # find the first visible peakList
    #                 peakList = thisPeakListView.peakList
    #
    #                 # for peakListView in spectrumView.peakListViews:
    #                 # find the first visible peakList
    #                 # if not peakListView.isVisible() or not spectrumView.isVisible():
    #                 #   continue
    #
    #                 # peakList = peakListView.peakList
    #
    #                 # if isinstance(peakList, PeakList):
    #                 peak = peakList.newPeak()
    #
    #                 # change dict to position
    #                 # position = [0.0] * len(peak.axisCodes)
    #                 # for n, axis in enumerate(peak.axisCodes):
    #                 #   if _preferences.matchAxisCode == 0:  # default - match atom type
    #                 #     for ax in positionDict.keys():
    #                 #       if ax and axis and ax[0] == axis[0]:
    #                 #         position[n] = positionDict[ax]
    #                 #         break
    #                 #
    #                 #   elif _preferences.matchAxisCode == 1:  # match full code
    #                 #     if axis in positionDict.keys():
    #                 #       position[n] = positionDict[axis]
    #
    #                 position = inPosition
    #                 if spectrumView.spectrum.dimensionCount > 1:
    #                     # sortedSelectedRegion =[list(sorted(x)) for x in selectedRegion]
    #                     spectrumAxisCodes = spectrumView.spectrum.axisCodes
    #                     stripAxisCodes = self.axisCodes
    #                     position = [0] * spectrumView.spectrum.dimensionCount
    #
    #                     remapIndices = commonUtil._axisCodeMapIndices(stripAxisCodes, spectrumAxisCodes)
    #                     if remapIndices:
    #                         for n, axisCode in enumerate(spectrumAxisCodes):
    #                             # idx = stripAxisCodes.index(axisCode)
    #
    #                             idx = remapIndices[n]
    #                             # sortedSpectrumRegion[n] = sortedSelectedRegion[idx]
    #                             position[n] = inPosition[idx]
    #                     else:
    #                         position = inPosition
    #
    #                 if peak.peakList.spectrum.dimensionCount == 1:
    #                     if len(position) > 1:
    #                         peak.position = (position[0],)
    #                         peak.height = position[1]
    #                 else:
    #                     peak.position = position
    #                     # note, the height below is not derived from any fitting
    #                     # but is a weighted average of the values at the neighbouring grid points
    #                     peak.height = spectrumView.spectrum.getPositionValue(peak.pointPosition)
    #                 result.append(peak)
    #                 peakLists.append(peakList)
    #
    #     except Exception as es:
    #         pass
    #
    #     finally:
    #         self._endCommandEchoBlock()
    #         self._project.unblankNotification()
    #
    #     for peak in result:
    #         peak._finaliseAction('create')
    #
    #     return tuple(result), tuple(peakLists)

    # def peakPickRegion(self, selectedRegion: List[List[float]]) -> Tuple[Peak]:
    #     """Peak pick all spectra currently displayed in strip in selectedRegion """
    #
    #     result = []
    #
    #     project = self.project
    #     minDropfactor = self.application.preferences.general.peakDropFactor
    #
    #     self._startCommandEchoBlock('peakPickRegion', selectedRegion)
    #     self._project.blankNotification()
    #     try:
    #
    #         for spectrumView in self.spectrumViews:
    #
    #             numPeakLists = [pp for pp in spectrumView.peakListViews if isinstance(pp.peakList, PeakList)]
    #             if not numPeakLists:  # this can happen if no peakLists, so create one
    #                 self._project.unblankNotification()  # need this otherwise SideBar does not get updated
    #                 spectrumView.spectrum.newPeakList()
    #                 self._project.blankNotification()
    #
    #             validPeakListViews = [pp for pp in spectrumView.peakListViews if isinstance(pp.peakList, PeakList)
    #                                   and pp.isVisible()
    #                                   and spectrumView.isVisible()]
    #             # if numPeakLists:
    #             for thisPeakListView in validPeakListViews:
    #                 # find the first visible peakList
    #                 peakList = thisPeakListView.peakList
    #
    #                 # peakList = spectrumView.spectrum.peakLists[0]
    #
    #                 if spectrumView.spectrum.dimensionCount > 1:
    #                     sortedSelectedRegion = [list(sorted(x)) for x in selectedRegion]
    #                     spectrumAxisCodes = spectrumView.spectrum.axisCodes
    #                     stripAxisCodes = self.axisCodes
    #                     sortedSpectrumRegion = [0] * spectrumView.spectrum.dimensionCount
    #
    #                     remapIndices = commonUtil._axisCodeMapIndices(stripAxisCodes, spectrumAxisCodes)
    #                     if remapIndices:
    #                         for n, axisCode in enumerate(spectrumAxisCodes):
    #                             # idx = stripAxisCodes.index(axisCode)
    #                             idx = remapIndices[n]
    #                             sortedSpectrumRegion[n] = sortedSelectedRegion[idx]
    #                     else:
    #                         sortedSpectrumRegion = sortedSelectedRegion
    #
    #                     newPeaks = peakList.pickPeaksNd(sortedSpectrumRegion,
    #                                                     doPos=spectrumView.displayPositiveContours,
    #                                                     doNeg=spectrumView.displayNegativeContours,
    #                                                     fitMethod='gaussian', minDropfactor=minDropfactor)
    #                 else:
    #                     # 1D's
    #                     # NBNB This is a change - valuea are now rounded to three decimal places. RHF April 2017
    #                     newPeaks = peakList.pickPeaks1d(selectedRegion[0], sorted(selectedRegion[1]), size=minDropfactor * 100)
    #                     # y0 = startPosition.y()
    #                     # y1 = endPosition.y()
    #                     # y0, y1 = min(y0, y1), max(y0, y1)
    #                     # newPeaks = peakList.pickPeaks1d([startPosition.x(), endPosition.x()], [y0, y1])
    #
    #                 result.extend(newPeaks)
    #                 # break
    #
    #             # # Add the new peaks to selection
    #             # for peak in newPeaks:
    #             #   # peak.isSelected = True
    #             #   self.current.addPeak(peak)
    #
    #             # for window in project.windows:
    #             #   for spectrumDisplay in window.spectrumDisplays:
    #             #     for strip in spectrumDisplay.strips:
    #             #       spectra = [spectrumView.spectrum for spectrumView in strip.spectrumViews]
    #             #       if peakList.spectrum in spectra:
    #             #               strip.showPeaks(peakList)
    #
    #     finally:
    #         self._endCommandEchoBlock()
    #         self._project.unblankNotification()
    #
    #     for peak in result:
    #         peak._finaliseAction('create')
    #     #
    #     return tuple(result)


# Notifiers:
def _updateDisplayedMarks(data):
    """Callback when marks have changed - Create, Change, Delete; defined above
    """
    from ccpn.ui.gui.lib.OpenGL.CcpnOpenGL import GLNotifier

    GLSignals = GLNotifier(parent=None)
    GLSignals.emitEvent(triggers=[GLNotifier.GLMARKS])


def _updateSelectedPeaks(data):
    """Callback when peaks have changed
    """
    from ccpn.ui.gui.lib.OpenGL.CcpnOpenGL import GLNotifier

    GLSignals = GLNotifier(parent=None)
    GLSignals.emitEvent(triggers=[GLNotifier.GLHIGHLIGHTPEAKS], targets=data[Notifier.OBJECT].peaks)


def _updateSelectedIntegrals(data):
    """Callback when integrals have changed
    """
    from ccpn.ui.gui.lib.OpenGL.CcpnOpenGL import GLNotifier

    GLSignals = GLNotifier(parent=None)
    GLSignals.emitEvent(triggers=[GLNotifier.GLHIGHLIGHTINTEGRALS], targets=data[Notifier.OBJECT].integrals)


def _updateSelectedMultiplets(data):
    """Callback when multiplets have changed
    """
    from ccpn.ui.gui.lib.OpenGL.CcpnOpenGL import GLNotifier

    GLSignals = GLNotifier(parent=None)
    GLSignals.emitEvent(triggers=[GLNotifier.GLHIGHLIGHTMULTIPLETS], targets=data[Notifier.OBJECT].multiplets)


def _axisRegionChanged(cDict):
    """Notifier function: Update strips etc. for when axis position or width changes"""

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
                # One of the Z axes
                # strip._updateTraces()
                # for spectrumView in strip.spectrumViews:
                #     spectrumView.update()
                #     if spectrumView.isVisible():
                #         for peakListView in spectrumView.peakListViews:
                #             if peakListView.isVisible():
                #                 peakList = peakListView.peakList
                #                 peaks = [peak for peak in peakList.peaks if strip.peakIsInPlane(peak) or strip.peakIsInFlankingPlane(peak)]
                #                 strip.spectrumDisplay.showPeaks(peakListView, peaks)

                if len(strip.axisOrder) > 2:
                    n = index - 2
                    if n >= 0:
                        planeLabel = strip.planeToolbar.planeLabels[n]
                        planeSize = planeLabel.singleStep()
                        planeLabel.setValue(position)
                        strip.planeToolbar.planeCounts[n].setValue(width / planeSize)

            # if index >= 2:
            #     spectrumDisplay = strip.spectrumDisplay
            #     if hasattr(spectrumDisplay, 'activePeakItemDict'):  # ND display
            #         activePeakItemDict = spectrumDisplay.activePeakItemDict
            #         for spectrumView in strip.spectrumViews:
            #             for peakListView in spectrumView.peakListViews:
            #                 peakItemDict = activePeakItemDict.get(peakListView, {})
            #                 for peakItem in peakItemDict.values():
            #                     peakItem._stripRegionUpdated()

        finally:
            strip.beingUpdated = False

    # if index == 1:  # ASSUMES that only do H phasing
    #     strip._updatePhasing()


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
    """Set up graphical parameters for completed strips - for notifiers"""
    strip = project._data2Obj[apiStrip]

    # orderedAxes = strip.orderedAxes
    # padding = strip.application.preferences.general.stripRegionPadding
    #
    # strip.viewBox.setXRange(*orderedAxes[0].region, padding=padding)
    # strip.viewBox.setYRange(*orderedAxes[1].region, padding=padding)
    # strip.plotWidget._initTextItems()
    # strip.viewBox.sigStateChanged.connect(strip.plotWidget._moveAxisCodeLabels)
    #
    # # signal for communicating zoom across strips
    # strip.viewBox.sigXRangeChanged.connect(strip._updateXRegion)
    # strip.viewBox.sigYRangeChanged.connect(strip._updateYRegion)

    try:
        strip._CcpnGLWidget.initialiseAxes(strip=strip)
        # strip._CcpnGLWidget._resetAxisRange()
    except:
        getLogger().debugGL('OpenGL widget not instantiated')
