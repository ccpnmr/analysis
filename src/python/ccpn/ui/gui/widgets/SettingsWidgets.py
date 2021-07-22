"""
Module Documentation here
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2021"
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
__dateModified__ = "$dateModified: 2021-07-20 21:57:03 +0100 (Tue, July 20, 2021) $"
__version__ = "$Revision: 3.0.4 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from PyQt5 import QtWidgets
from PyQt5.QtCore import pyqtSignal, pyqtSlot
from ccpn.ui.gui.widgets.CompoundWidgets import ListCompoundWidget
from ccpn.ui.gui.widgets.Widget import Widget
from ccpn.ui.gui.widgets.Button import Button
from ccpn.ui.gui.widgets.RadioButtons import RadioButtons
from ccpn.ui.gui.widgets.Spacer import Spacer
from ccpn.ui.gui.widgets.CheckBox import CheckBox
from ccpn.ui.gui.widgets.CheckBoxes import CheckBoxes
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.Frame import Frame
from ccpn.ui.gui.widgets.Font import getTextDimensionsFromFont, getFontHeight
from ccpn.ui.gui.widgets.CompoundWidgets import CheckBoxCompoundWidget, DoubleSpinBoxCompoundWidget
from ccpn.ui.gui.widgets.DoubleSpinbox import ScientificDoubleSpinBox
from ccpn.ui.gui.widgets.Slider import Slider
from ccpn.ui.gui.guiSettings import getColours, DIVIDER, SOFTDIVIDER, ZPlaneNavigationModes
from ccpn.ui.gui.widgets.HLine import HLine
from ccpn.ui.gui.widgets.PulldownListsForObjects import NmrChainPulldown, SpectrumDisplayPulldown, ChemicalShiftListPulldown
from ccpn.core.lib.Notifiers import Notifier
from ccpn.ui._implementation.SpectrumView import SpectrumView
from functools import partial
from ccpn.ui.gui.lib.OpenGL.CcpnOpenGLNotifier import GLNotifier
from ccpn.ui.gui.lib.OpenGL.CcpnOpenGLDefs import AXISXUNITS, AXISYUNITS, \
    SYMBOLTYPES, SYMBOLSIZE, SYMBOLTHICKNESS, ANNOTATIONTYPES, AXISASPECTRATIOS, \
    AXISASPECTRATIOMODE, ALIASENABLED, ALIASSHADE, ALIASLABELSENABLED, CONTOURTHICKNESS
from ccpn.ui.gui.widgets.Spinbox import Spinbox
from ccpn.core.lib.AxisCodeLib import getAxisCodeMatchIndices
from ccpn.ui.gui.widgets.Base import SignalBlocking
from ccpn.core.Chain import Chain
from ccpn.core.RestraintList import RestraintList


ALL = '<all>'

STRIPPLOT_PEAKS = 'peaks'
STRIPPLOT_NMRRESIDUES = 'nmrResidues'
STRIPPLOT_NMRCHAINS = 'nmrChains'
STRIPPLOT_NMRATOMSFROMPEAKS = 'nmrAtomsPeaks'
NO_STRIP = 'noStrip'
LineEditsMinimumWidth = 195


class SpectrumDisplaySettings(Widget, SignalBlocking):
    # signal for parentWidgets to respond to changes in the widget
    settingsChanged = pyqtSignal(dict)
    symbolsChanged = pyqtSignal(dict)
    stripArrangementChanged = pyqtSignal(int)
    zPlaneNavigationModeChanged = pyqtSignal(int)

    def __init__(self, parent=None,
                 mainWindow=None,
                 spectrumDisplay=None,
                 callback=None, returnCallback=None, applyCallback=None,
                 xAxisUnits=0, xTexts=[], showXAxis=True,
                 yAxisUnits=0, yTexts=[], showYAxis=True,
                 symbolType=0, annotationType=0, symbolSize=0, symbolThickness=0,
                 aliasEnabled=False, aliasShade=0,
                 aliasLabelsEnabled=False,
                 stripArrangement=0,
                 _baseAspectRatioAxisCode='H', _aspectRatios={},
                 _aspectRatioMode=0, contourThickness=0, zPlaneNavigationMode=0,
                 **kwds):
        super().__init__(parent, setLayout=True, **kwds)

        self._parent = parent
        self._spectrumDisplay = spectrumDisplay

        # Derive application, project, and current from mainWindow
        self.mainWindow = mainWindow
        if mainWindow:
            self.application = mainWindow.application
            self.project = mainWindow.application.project
            self.current = mainWindow.application.current
            self.preferences = mainWindow.application.preferences
        else:
            self.application = None
            self.project = None
            self.current = None
            self.preferences = None

        # store callbacks
        self.callback = callback
        self.returnCallback = returnCallback if returnCallback else self.doCallback
        self.applyCallback = applyCallback

        # set up the widgets
        self._setWidgets(parent, _aspectRatios.keys(), _baseAspectRatioAxisCode, showXAxis, showYAxis, xTexts, yTexts)

        # populate the widgets
        self._populateWidgets(_aspectRatioMode, _aspectRatios, annotationType, stripArrangement,
                              symbolSize, symbolThickness, symbolType, xAxisUnits, yAxisUnits,
                              aliasEnabled, aliasShade, aliasLabelsEnabled,
                              contourThickness, zPlaneNavigationMode)

        # connect to the lock/symbol/ratio changed pyqtSignals
        self._GLSignals = GLNotifier(parent=self._parent)
        self._GLSignals.glAxisLockChanged.connect(self._lockAspectRatioChangedInDisplay)
        self._GLSignals.glSymbolsChanged.connect(self._symbolsChangedInDisplay)
        self._GLSignals.glXAxisChanged.connect(self._aspectRatioChangedInDisplay)
        self._GLSignals.glYAxisChanged.connect(self._aspectRatioChangedInDisplay)

    def _setWidgets(self, parent, aspectCodes, baseAspectCode, showXAxis, showYAxis, xTexts, yTexts):
        """Set up the widgets for the module
        """
        # insert widgets into the parent widget
        row = 0
        self.xAxisUnits = Label(parent, text="X-axis units", grid=(row, 0))
        self.xAxisUnitsData = RadioButtons(parent, texts=xTexts,
                                           objectNames=[f'xUnitsSDS_{text}' for text in xTexts],
                                           objectName='xUnitsSDS',
                                           # selectedInd=xAxisUnits,
                                           callback=self._settingsChanged,
                                           direction='h',
                                           grid=(row, 1), gridSpan=(1, 3), hAlign='l',
                                           tipTexts=None,
                                           )
        self.xAxisUnits.setVisible(showXAxis)
        self.xAxisUnitsData.setVisible(showXAxis)

        row += 1
        self.yAxisUnits = Label(parent, text="Y-axis units", grid=(row, 0))
        self.yAxisUnitsData = RadioButtons(parent, texts=yTexts,
                                           objectNames=[f'yUnitsSDS_{text}' for text in xTexts],
                                           objectName='yUnitsSDS',
                                           # selectedInd=yAxisUnits,
                                           callback=self._settingsChanged,
                                           direction='h',
                                           grid=(row, 1), gridSpan=(1, 3), hAlign='l',
                                           tipTexts=None)
        self.yAxisUnits.setVisible(showYAxis)
        self.yAxisUnitsData.setVisible(showYAxis)

        row += 1
        HLine(parent, grid=(row, 0), gridSpan=(1, 5), colour=getColours()[DIVIDER], height=15)

        row += 1
        _height = getFontHeight(size='VLARGE') or 24
        self.stripArrangementLabel = Label(parent, text="Strip Arrangement", grid=(row, 0))
        self.stripArrangementButtons = RadioButtons(parent, texts=['    ', '    ', '    '],
                                                    objectNames=['stripSDS_Row', 'stripSDS_Column', 'stripSDS_Tile'],
                                                    objectName='stripSDS',
                                                    # selectedInd=stripArrangement,
                                                    direction='horizontal',
                                                    grid=(row, 1), gridSpan=(1, 3), hAlign='l',
                                                    tipTexts=None,
                                                    icons=[('icons/strip-row', (_height, _height)),
                                                           ('icons/strip-column', (_height, _height)),
                                                           ('icons/strip-tile', (_height, _height))
                                                           ],
                                                    )
        # NOTE:ED - temporarily disable/hide the Tile button
        self.stripArrangementButtons.radioButtons[2].setEnabled(False)
        self.stripArrangementButtons.radioButtons[2].setVisible(False)
        self.stripArrangementButtons.setCallback(self._stripArrangementChanged)

        if self._spectrumDisplay.is1D:
            # not currently required for 1D
            self.stripArrangementLabel.setVisible(False)
            self.stripArrangementButtons.setVisible(False)
            self.stripArrangementButtons.setEnabled(False)

        row += 1
        self.zPlaneNavigationModeLabel = Label(parent, text="zPlane Navigation Mode", grid=(row, 0))
        self.zPlaneNavigationModeData = RadioButtons(parent, texts=[val.description for val in ZPlaneNavigationModes],
                                                     objectNames=[f'zPlaneSDS_{val.label}' for val in ZPlaneNavigationModes],
                                                     objectName='zPlaneSDS',
                                                     callback=self._zPlaneNavigationModeChanged,
                                                     direction='h',
                                                     grid=(row, 1), hAlign='l', gridSpan=(1, 2),
                                                     tipTexts=('Tools are located at the bottom of the spectrumDisplay,\nand will operate on the last strip selected in that spectrumDisplay',
                                                               'Tools are located at the bottom of each strip',
                                                               'Tools are displayed in the upper-left corner of each strip display'),
                                                     )
        self.zPlaneNavigationModeLabel.setToolTip('Select where the zPlane navigation tools are located')

        if len(self._spectrumDisplay.axisCodes) < 3:
            self.zPlaneNavigationModeLabel.setVisible(False)
            self.zPlaneNavigationModeData.setVisible(False)
            self.zPlaneNavigationModeData.setEnabled(False)

        row += 1
        HLine(parent, grid=(row, 0), gridSpan=(1, 5), colour=getColours()[DIVIDER], height=15)

        row += 1
        Label(parent, text="Aspect Ratio", grid=(row, 0))

        row += 1
        self.useAspectRatioModeLabel = Label(parent, text="Mode", hAlign='r', grid=(row, 0))
        self.useAspectRatioModeButtons = RadioButtons(parent, texts=['Free', 'Locked', 'Fixed'],
                                                      objectNames=['armSDS_Free', 'armSDS_Locked', 'armSDS_Fixed'],
                                                      objectName='armSDS',
                                                      # selectedInd=_aspectRatioMode,
                                                      callback=self._aspectRatioModeChanged,
                                                      direction='horizontal',
                                                      grid=(row, 1), gridSpan=(1, 3), hAlign='l',
                                                      tipTexts=None,
                                                      )

        row += 1
        Label(parent, text='Current values:', hAlign='r', grid=(row, 0))
        Label(parent, text='Fixed', grid=(row, 1))
        Label(parent, text='Screen', grid=(row, 2))

        row += 1
        self.aspectLabel = {}
        self.aspectData = {}
        self.aspectScreen = {}
        self.aspectLabelFrame = Frame(parent, setLayout=True, showBorder=False, grid=(row, 0))
        self.aspectDataFrame = Frame(parent, setLayout=True, showBorder=False, grid=(row, 1))
        self.aspectScreenFrame = Frame(parent, setLayout=True, showBorder=False, grid=(row, 2))
        self._removeWidget(self.aspectLabelFrame)
        self._removeWidget(self.aspectDataFrame)
        self._removeWidget(self.aspectScreenFrame)
        for ii, aspect in enumerate(sorted(aspectCodes)):
            # aspectValue = _aspectRatios[aspect]
            self.aspectLabel[aspect] = Label(self.aspectLabelFrame, text=aspect, grid=(ii, 0), hAlign='r')

            self.aspectData[aspect] = ScientificDoubleSpinBox(self.aspectDataFrame, min=0.01, grid=(ii, 0), hAlign='l', decimals=2,
                                                              objectName=f'aspectSDS_{aspect}')
            # self.aspectData[aspect].setValue(aspectValue)
            self.aspectData[aspect].setMinimumWidth(LineEditsMinimumWidth)
            if aspect[0] == baseAspectCode[0]:
                self.aspectData[aspect].setEnabled(False)
            else:
                self.aspectData[aspect].setEnabled(True)
                self.aspectData[aspect].valueChanged.connect(partial(self._settingsChangeAspect, aspect))

            self.aspectScreen[aspect] = Label(self.aspectScreenFrame, text=aspect, grid=(ii, 0), hAlign='l')
            # self.aspectScreen[aspect].setText(self.aspectData[aspect].textFromValue(aspectValue))

        row += 1
        _buttonFrame = Frame(parent, setLayout=True, grid=(row, 1), gridSpan=(1, 3), hAlign='l')
        self.setFromDefaultsButton = Button(_buttonFrame, text='Defaults', grid=(0, 0), callback=self.updateFromDefaults)
        self.setFromScreenButton = Button(_buttonFrame, text='Set from screen', grid=(0, 1), callback=self._setAspectFromScreen)

        row += 1
        HLine(parent, grid=(row, 0), gridSpan=(1, 5), colour=getColours()[DIVIDER], height=15)

        row += 1
        self.contourThicknessLabel = Label(parent, text="Contour thickness (pixel)", grid=(row, 0))
        self.contourThicknessData = Spinbox(parent, step=1,
                                            min=1, max=20, grid=(row, 1), hAlign='l', objectName='SDS_contour')
        self.contourThicknessData.setMinimumWidth(LineEditsMinimumWidth)
        self.contourThicknessData.valueChanged.connect(self._symbolsChanged)

        row += 1
        HLine(parent, grid=(row, 0), gridSpan=(1, 5), colour=getColours()[DIVIDER], height=15)

        row += 1
        Label(parent, text="Peaks", hAlign='l', grid=(row, 0))

        if self._spectrumDisplay.MAXPEAKLABELTYPES:
            row += 1
            _texts = ['Short', 'Full', 'Pid', 'Minimal', 'Id', 'Annotation']
            _names = ['annSDS_Short', 'annSDS_Full', 'annSDS_Pid', 'annSDS_Minimal', 'annSDS_Id', 'annSDS_Annotation']
            _texts = _texts[:self._spectrumDisplay.MAXPEAKLABELTYPES]
            _names = _names[:self._spectrumDisplay.MAXPEAKLABELTYPES]

            self.annotationsLabel = Label(parent, text="Label", hAlign='r', grid=(row, 0))
            self.annotationsData = RadioButtons(parent, texts=_texts,
                                                objectNames=_names,
                                                objectName='annSDS',
                                                # selectedInd=annotationType,
                                                callback=self._symbolsChanged,
                                                direction='horizontal',
                                                grid=(row, 1), gridSpan=(1, 3), hAlign='l',
                                                tipTexts=None,
                                                )

        if self._spectrumDisplay.MAXPEAKSYMBOLTYPES:
            # if not self._spectrumDisplay.is1D:
            row += 1
            _texts = ['Cross', 'lineWidths', 'Filled lineWidths', 'Plus']
            _names = ['symSDS_Cross', 'symSDS_lineWidths', 'symSDS_Filled lineWidths', 'symSDS_Plus']
            _texts = _texts[:self._spectrumDisplay.MAXPEAKSYMBOLTYPES]
            _names = _names[:self._spectrumDisplay.MAXPEAKSYMBOLTYPES]

            self.symbolsLabel = Label(parent, text="Symbol",  hAlign='r', grid=(row, 0))
            self.symbol = RadioButtons(parent, texts=_texts,
                                       objectNames=_names,
                                       objectName='symSDS',
                                       # selectedInd=symbolType,
                                       callback=self._symbolsChanged,
                                       direction='h',
                                       grid=(row, 1), gridSpan=(1, 3), hAlign='l',
                                       tipTexts=None,
                                       )

            if self._spectrumDisplay.is1D:
                self.symbol.radioButtons[1].setEnabled(False)
                self.symbol.radioButtons[2].setEnabled(False)
                self.symbol.radioButtons[1].setVisible(False)
                self.symbol.radioButtons[2].setVisible(False)

        row += 1
        self.symbolSizePixelLabel = Label(parent, text="Size (pixel)", hAlign='r', grid=(row, 0))
        self.symbolSizePixelData = Spinbox(parent, step=1,
                                           min=2, max=50, grid=(row, 1), hAlign='l', objectName='SDS_symbolSize')
        self.symbolSizePixelData.setMinimumWidth(LineEditsMinimumWidth)
        # self.symbolSizePixelData.setValue(int(symbolSize))
        self.symbolSizePixelData.valueChanged.connect(self._symbolsChanged)

        row += 1
        self.symbolThicknessLabel = Label(parent, text="Thickness (pixel)", hAlign='r', grid=(row, 0))
        self.symbolThicknessData = Spinbox(parent, step=1,
                                           min=1, max=20, grid=(row, 1), hAlign='l', objectName='SDS_symbolThickness')
        self.symbolThicknessData.setMinimumWidth(LineEditsMinimumWidth)
        # self.symbolThicknessData.setValue(int(symbolThickness))
        self.symbolThicknessData.valueChanged.connect(self._symbolsChanged)

        row += 1
        HLine(parent, grid=(row, 0), gridSpan=(1, 5), colour=getColours()[DIVIDER], height=15)

        row += 1
        Label(parent, text="Aliased Peaks", hAlign='l', grid=(row, 0))

        row += 1
        self.aliasEnabledLabel = Label(parent, text="Show peaks", hAlign='r', grid=(row, 0))
        self.aliasEnabledData = CheckBox(parent,
                                         # checked=aliasEnabled,
                                         grid=(row, 1), objectName='SDS_aliasEnabled')
        self.aliasEnabledData.clicked.connect(self._symbolsChanged)

        row += 1
        self.aliasLabelsEnabledLabel = Label(parent, text="Show labels", hAlign='r', grid=(row, 0))
        self.aliasLabelsEnabledData = CheckBox(parent,
                                               # checked=aliasLabelsEnabled,
                                               grid=(row, 1), objectName='SDS_aliasLabelsEnabled')
        self.aliasLabelsEnabledData.clicked.connect(self._symbolsChanged)

        row += 1
        self.aliasShadeLabel = Label(parent, text="Opacity", hAlign='r', grid=(row, 0))
        _sliderBox = Frame(parent, setLayout=True, grid=(row, 1), hAlign='l')
        self.aliasShadeData = Slider(_sliderBox, grid=(0, 1), hAlign='l', objectName='SDS_aliasShade')
        Label(_sliderBox, text="0", grid=(0, 0), hAlign='l')
        Label(_sliderBox, text="100%", grid=(0, 2), hAlign='l')
        self.aliasShadeData.setMinimumWidth(LineEditsMinimumWidth)
        # self.aliasShadeData.set(aliasShade)
        self.aliasShadeData.valueChanged.connect(self._symbolsChanged)

        row += 1
        self._spacer = Spacer(parent, 5, 5,
                              QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding,
                              grid=(row, 4), gridSpan=(1, 1))
        self._parent.setContentsMargins(5, 5, 5, 5)

    def _populateWidgets(self, aspectRatioMode, aspectRatios, annotationType, stripArrangement,
                         symbolSize, symbolThickness, symbolType, xAxisUnits, yAxisUnits,
                         aliasEnabled, aliasShade, aliasLabelsEnabled,
                         contourThickness, zPlaneNavigationMode):
        """Populate the widgets
        """
        with self.blockWidgetSignals():

            # put the values into the correct widgets

            self._setAxesUnits(xAxisUnits, yAxisUnits)


            self.useAspectRatioModeButtons.setIndex(aspectRatioMode)
            for ii, aspect in enumerate(sorted(aspectRatios.keys())):
                aspectValue = aspectRatios[aspect]
                self.aspectData[aspect].setValue(aspectValue)
                self.aspectScreen[aspect].setText(self.aspectData[aspect].textFromValue(aspectValue))

            if self._spectrumDisplay.MAXPEAKLABELTYPES:
                self.annotationsData.setIndex(annotationType)
            if self._spectrumDisplay.MAXPEAKSYMBOLTYPES:
                self.symbol.setIndex(symbolType)

            self.symbolSizePixelData.setValue(int(symbolSize))
            self.symbolThicknessData.setValue(int(symbolThickness))
            self.contourThicknessData.setValue(int(contourThickness))

            self.stripArrangementButtons.setIndex(stripArrangement)
            self.aliasEnabledData.set(aliasEnabled)
            self.aliasShadeData.set(aliasShade)
            self.aliasLabelsEnabledData.set(aliasLabelsEnabled)
            self.aliasLabelsEnabledData.setEnabled(aliasEnabled)
            self.aliasShadeData.setEnabled(aliasEnabled)
            self.zPlaneNavigationModeData.setIndex(zPlaneNavigationMode)

    def _setAxesUnits(self, xAxisUnits, yAxisUnits):
        """Set the unit's checkboxes
        CCPNINTERNAL: used in GuiSpectrumDisplay
        """
        if xAxisUnits is not None:
            self.xAxisUnitsData.setIndex(xAxisUnits)
        if yAxisUnits is not None:
            self.yAxisUnitsData.setIndex(yAxisUnits)

    def getValues(self):
        """Return a dict containing the current settings
        """
        aspectRatios = {}
        for axis, data in self.aspectData.items():
            aspectRatios[axis] = data.get()

        # NOTE:ED - should really use an intermediate data structure here

        return {AXISXUNITS         : self.xAxisUnitsData.getIndex(),
                AXISYUNITS         : self.yAxisUnitsData.getIndex(),
                AXISASPECTRATIOMODE: self.useAspectRatioModeButtons.getIndex(),
                AXISASPECTRATIOS   : aspectRatios,
                SYMBOLTYPES        : self.symbol.getIndex(),  # if not self._spectrumDisplay.is1D else 0,
                ANNOTATIONTYPES    : self.annotationsData.getIndex(),  # if not self._spectrumDisplay.is1D else 0,
                SYMBOLSIZE         : int(self.symbolSizePixelData.text()),
                SYMBOLTHICKNESS    : int(self.symbolThicknessData.text()),
                CONTOURTHICKNESS   : int(self.contourThicknessData.text()),
                ALIASENABLED       : self.aliasEnabledData.isChecked(),
                ALIASSHADE         : int(self.aliasShadeData.get()),
                ALIASLABELSENABLED : self.aliasLabelsEnabledData.isChecked(),
                }

    def _aspectRatioModeChanged(self):
        """Set the current aspect ratio mode
        """
        self._updateLockedSettings()
        self._settingsChanged()

    def _updateLockedSettings(self, always=False):
        if self.useAspectRatioModeButtons.getIndex() == 2 or always:
            with self.aspectScreenFrame.blockWidgetSignals():
                for aspect, data in self.aspectData.items():
                    if aspect in self.aspectScreen:
                        self.aspectScreen[aspect].setText(data.text())

    def _settingsChangeAspect(self, *args):
        """Set the aspect ratio for the axes
        """
        self._updateLockedSettings()
        self._settingsChanged()

    def _setAspectFromScreen(self, *args):
        with self.aspectDataFrame.blockWidgetSignals():
            for aspect, label in self.aspectScreen.items():
                if aspect in self.aspectData:
                    self.aspectData[aspect].setValue(self.aspectData[aspect].valueFromText(label.text()))

        self._settingsChanged()

    def setStripArrangementButtons(self, value):
        """Update the state of the stripArrangement radioButtons
        """
        self.blockSignals(True)
        self.stripArrangementButtons.setIndex(value)
        self.blockSignals(False)

    def setZPlaneButtons(self, value):
        """Update the state of the zPlaneNavigation radioButtons
        """
        self.blockSignals(True)
        labels = [val.label for val in ZPlaneNavigationModes]
        if value in labels:
            self.zPlaneNavigationModeData.setIndex(labels.index(value))
        self.blockSignals(False)

    def updateFromDefaults(self, *args):
        """Update the defaults from preferences
        """
        with self.aspectDataFrame.blockWidgetSignals():
            for aspect, label in self.aspectScreen.items():
                if aspect in self.preferences.general.aspectRatios:
                    value = self.preferences.general.aspectRatios[aspect]
                    self.aspectData[aspect].setValue(value)

        self.blockSignals(True)
        self.useAspectRatioModeButtons.setIndex(int(self.preferences.general.aspectRatioMode))
        self._updateLockedSettings()
        self.xAxisUnitsData.setIndex(self.preferences.general.xAxisUnits)
        self.yAxisUnitsData.setIndex(self.preferences.general.yAxisUnits)
        self.blockSignals(False)

        self._settingsChanged()

    @pyqtSlot()
    def _settingsChanged(self):
        """Handle changing the X axis units
        """
        self.settingsChanged.emit(self.getValues())

    @pyqtSlot(dict)
    def _lockAspectRatioChangedInDisplay(self, aDict):
        """Respond to an external change in the lock status of a strip
        """
        if aDict[GLNotifier.GLSPECTRUMDISPLAY] == self._spectrumDisplay:
            self.blockSignals(True)

            self.useAspectRatioModeButtons.setIndex(aDict[GLNotifier.GLVALUES][0])
            self._updateLockedSettings()

            self.blockSignals(False)

    @pyqtSlot(dict)
    def _aspectRatioChangedInDisplay(self, aDict):
        """Respond to an external change in the aspect ratio of a strip
        """
        if aDict[GLNotifier.GLSPECTRUMDISPLAY] == self._spectrumDisplay:
            _aspectRatios = aDict[GLNotifier.GLAXISVALUES][GLNotifier.GLASPECTRATIOS]
            if not _aspectRatios:
                return

            self.blockSignals(True)

            for aspect in sorted(_aspectRatios.keys()):
                aspectValue = _aspectRatios[aspect]
                if aspect in self.aspectScreen and aspect in self.aspectData:
                    self.aspectScreen[aspect].setText(self.aspectData[aspect].textFromValue(aspectValue))

            self.blockSignals(False)

    @pyqtSlot()
    def _symbolsChanged(self):
        """Handle changing the symbols
        """
        self.symbolsChanged.emit(self.getValues())

        _enabled = self.aliasEnabledData.get()
        self.aliasLabelsEnabledData.setEnabled(_enabled)
        self.aliasShadeData.setEnabled(_enabled)

    @pyqtSlot(dict)
    def _symbolsChangedInDisplay(self, aDict):
        """Respond to an external change in symbol settings
        """
        if aDict[GLNotifier.GLSPECTRUMDISPLAY] == self._spectrumDisplay:
            values = aDict[GLNotifier.GLVALUES]
            self.blockSignals(True)

            # if not self._spectrumDisplay.is1D:
            # only update if Nd
            self.symbol.setIndex(values[SYMBOLTYPES])
            self.annotationsData.setIndex(values[ANNOTATIONTYPES])
            self.symbolSizePixelData.set(values[SYMBOLSIZE])
            self.symbolThicknessData.set(values[SYMBOLTHICKNESS])
            self.contourThicknessData.set(values[CONTOURTHICKNESS])
            self.aliasEnabledData.set(values[ALIASENABLED])
            self.aliasShadeData.set(values[ALIASSHADE])
            self.aliasLabelsEnabledData.set(values[ALIASLABELSENABLED])

            _enabled = self.aliasEnabledData.get()
            self.aliasLabelsEnabledData.setEnabled(_enabled)
            self.aliasShadeData.setEnabled(_enabled)

            self.mainWindow.statusBar().showMessage("Cycle Symbol Labelling: %s " % self.annotationsData.get())

            self.blockSignals(False)

    def _stripArrangementChanged(self):
        """Emit a signal if the strip arrangement buttons have been pressed
        """
        self.stripArrangementChanged.emit(self.stripArrangementButtons.getIndex())

    def _zPlaneNavigationModeChanged(self):
        """Emit a signal if the zPlane navigation buttons have been pressed
        """
        self.zPlaneNavigationModeChanged.emit(self.zPlaneNavigationModeData.getIndex())

    def doCallback(self):
        """Handle the user callback
        """
        if self.callback:
            self.callback()

    def _returnCallback(self):
        """Handle the return from widget callback
        """
        pass

    def updateRatiosInDisplay(self, ratios):
        """Manually update the settings in the display
        """
        with self.aspectScreenFrame.blockWidgetSignals():
            for aspect in sorted(ratios.keys()):
                aspectValue = ratios[aspect]
                if aspect in self.aspectScreen and aspect in self.aspectData:
                    self.aspectData[aspect].setText(aspectValue)


class _commonSettings():
    """
    Not to be used as a stand-alone class
    """

    # separated from settings widgets below, but only one seems to use it now

    def _getSpectraFromDisplays(self, displays):
        """Get the list of active spectra from the spectrumDisplays
        """
        if not self.application or not displays or len(displays) > 1:
            return 0, None, None, None

        from ccpn.core.lib.AxisCodeLib import getAxisCodeMatch, getAxisCodeMatchIndices

        validSpectrumViews = {}

        # loop through all the selected displays/spectrumViews that are visible
        for dp in displays:

            # ignore undefined displays
            if not dp or dp.is1D:
                continue

            if dp.strips:
                for sv in dp.strips[0].spectrumViews:

                    if not (sv.isDeleted or sv._flaggedForDelete):
                        if sv.spectrum not in validSpectrumViews:
                            validSpectrumViews[sv.spectrum] = sv.isVisible()
                        else:
                            validSpectrumViews[sv.spectrum] = validSpectrumViews[sv.spectrum] or sv.isVisible()

        if validSpectrumViews:
            maxLen = 0
            refAxisCodes = None

            # need a list of all unique axisCodes in the spectra in the selected spectrumDisplays
            from ccpn.util.OrderedSet import OrderedSet

            # have to assume that there is only one display it this point
            activeDisplay = displays[0]

            # get list of unique axisCodes
            visibleAxisCodes = {}
            spectrumIndices = {}
            for spectrum, visible in validSpectrumViews.items():

                indices = getAxisCodeMatchIndices(spectrum.axisCodes, activeDisplay.axisCodes)
                spectrumIndices[spectrum] = indices
                for ii, axis in enumerate(spectrum.axisCodes):
                    ind = indices[ii]
                    if ind is not None:
                        if ind in visibleAxisCodes:
                            visibleAxisCodes[ind].add(axis)
                        else:
                            visibleAxisCodes[ind] = OrderedSet([axis])

            ll = len(activeDisplay.axisCodes)
            axisLabels = [None] * ll
            for ii in range(ll):
                axisLabels[ii] = ', '.join(visibleAxisCodes[ii])

            return ll, axisLabels, spectrumIndices, validSpectrumViews

            # from ccpn.util.OrderedSet import OrderedSet
            #
            # # get list of unique axisCodes
            # visibleAxisCodes = OrderedSet()
            # for spectrum, visible in validSpectrumViews.items():
            #     for axis in spectrum.axisCodes:
            #         visibleAxisCodes.add(axis)
            #
            # # get mapping of each spectrum onto this list
            # spectrumIndices = {}
            # for spectrum, visible in validSpectrumViews.items():
            #     indices = getAxisCodeMatchIndices(spectrum.axisCodes, visibleAxisCodes, exactMatch=False)  #True)
            #     spectrumIndices[spectrum] = indices
            #     maxLen = max(spectrum.dimensionCount, maxLen)
            #
            # # return if nothing to process
            # if not maxLen:
            #     return 0, None, None, None
            #
            # axisLabels = [', '.join(ax) for ax in visibleAxisCodes]
            #
            # return maxLen, tuple(visibleAxisCodes), spectrumIndices, validSpectrumViews

            # for spectrum, visible in validSpectrumViews.items():
            #
            #     # get the max length of the axisCodes for the displayed spectra
            #     if len(spectrum.axisCodes) > maxLen:
            #         maxLen = len(spectrum.axisCodes)
            #         refAxisCodes = list(spectrum.axisCodes)
            #
            # mappings = {}
            # for spectrum, visible in validSpectrumViews.items():
            #
            #     matchAxisCodes = spectrum.axisCodes
            #
            #     foundMap = getAxisCodeMatch(matchAxisCodes, refAxisCodes, allMatches=True)
            #     mappings.update(foundMap)
            #
            #     # for refAxisCode in refAxisCodes:
            #     #     for matchAxisCode in matchAxisCodes:
            #     #         mapping = getAxisCodeMatch([matchAxisCode], [refAxisCode])
            #     #         for k, v in mapping.items():
            #     #             if v not in mappings:
            #     #                 mappings[v] = set([k])
            #     #             else:
            #     #                 mappings[v].add(k)
            #
            # # example of mappings dict
            # # ('Hn', 'C', 'Nh')
            # # {'Hn': {'Hn'}, 'Nh': {'Nh'}, 'C': {'C'}}
            # # {'Hn': {'H', 'Hn'}, 'Nh': {'Nh'}, 'C': {'C'}}
            # # {'CA': {'C'}, 'Hn': {'H', 'Hn'}, 'Nh': {'Nh'}, 'C': {'CA', 'C'}}
            # # {'CA': {'C'}, 'Hn': {'H', 'Hn'}, 'Nh': {'Nh'}, 'C': {'CA', 'C'}}
            #
            # # far too complicated!
            # axisLabels = [set() for ii in range(len(mappings))]
            #
            # spectrumIndex = {}
            # # go through the spectra again
            # for spectrum, visible in validSpectrumViews.items():
            #
            #     spectrumIndex[spectrum] = [0 for ii in range(len(spectrum.axisCodes))]
            #
            #     # get the spectrum dimension axisCode, and see if is already there
            #     for spectrumDim, spectrumAxis in enumerate(spectrum.axisCodes):
            #
            #         axisTestCodes = tuple(mappings.keys())
            #         if spectrumAxis in axisTestCodes:
            #             spectrumIndex[spectrum][spectrumDim] = axisTestCodes.index(spectrumAxis)
            #             axisLabels[spectrumIndex[spectrum][spectrumDim]].add(spectrumAxis)
            #
            #         else:
            #             # if the axisCode is not in the reference list then find the mapping from the dict
            #             for k, v in mappings.items():
            #                 if spectrumAxis in v:
            #                     # refAxisCodes[dim] = k
            #                     spectrumIndex[spectrum][spectrumDim] = axisTestCodes.index(k)
            #                     axisLabels[axisTestCodes.index(k)].add(spectrumAxis)
            #
            # axisLabels = [', '.join(ax) for ax in axisLabels]
            #
            # return maxLen, axisLabels, spectrumIndex, validSpectrumViews
            # # self.axisCodeOptions.setCheckBoxes(texts=axisLabels, tipTexts=axisLabels)

        else:
            return 0, None, None, None

    def _removeWidget(self, widget, removeTopWidget=False):
        """Destroy a widget and all it's contents
        """

        def deleteItems(layout):
            if layout is not None:
                while layout.count():
                    item = layout.takeAt(0)
                    widget = item.widget()
                    if widget is not None:
                        widget.setVisible(False)
                        widget.setParent(None)
                        del widget

        deleteItems(widget.getLayout())
        if removeTopWidget:
            del widget

    def _fillSpectrumFrame(self, displays):
        """Populate then spectrumFrame with the selectable spectra
        """
        if self._spectraWidget:
            self._spectraWidget.hide()
            self._spectraWidget.setParent(None)
            self._removeWidget(self._spectraWidget, removeTopWidget=True)

        self._spectraWidget = Widget(parent=self.spectrumDisplayOptionsFrame, setLayout=True, hPolicy='minimal',
                                     grid=(2, 1), gridSpan=(self._spectraRows, 2), vAlign='top', hAlign='left')

        # calculate the maximum number of axes
        self.maxLen, self.axisLabels, self.spectrumIndex, self.validSpectrumViews = self._getSpectraFromDisplays(displays)
        if not self.maxLen:
            return

        # modifier for atomCode
        spectraRow = 0
        self.atomCodeFrame = Frame(self._spectraWidget, setLayout=True, showBorder=False, fShape='noFrame',
                                   grid=(spectraRow, 0), gridSpan=(1, self.maxLen + 1),
                                   vAlign='top', hAlign='left')
        self.axisCodeLabel = Label(self.atomCodeFrame, 'Restricted Axes:', grid=(0, 0))

        # remember current selection so can be set after redefining checkboxes
        currentSelection = None
        if self.axisCodeOptions:
            currentSelection = self.axisCodeOptions.getSelectedText()

        self.axisCodeOptions = CheckBoxes(self.atomCodeFrame, selectedInd=None, texts=[],
                                          callback=self._changeAxisCode, grid=(0, 1))
        self.axisCodeOptions.setCheckBoxes(texts=self.axisLabels, tipTexts=self.axisLabels)

        # set current selection back to the checkboxes
        # if currentSelection:
        #     self.axisCodeOptions.setSelectedByText(currentSelection, True, presetAll=True)

        # just clear the 'C' axes - this is the usual configuration
        self.axisCodeOptions.selectAll()
        for ii, box in enumerate(self.axisCodeOptions.checkBoxes):
            if box.text().upper().startswith('C'):
                self.axisCodeOptions.clearIndex(ii)

        # put in a divider
        spectraRow += 1
        HLine(self._spectraWidget, grid=(spectraRow, 0), gridSpan=(1, 4),
              colour=getColours()[SOFTDIVIDER], height=15)

        # add labels for the columns
        spectraRow += 1
        Label(self._spectraWidget, 'Spectrum', grid=(spectraRow, 0))

        # for ii in range(self.maxLen):
        #     Label(self._spectraWidget, 'Tolerance', grid=(spectraRow, ii + 1))
        Label(self._spectraWidget, '(double-width tolerances)', grid=(spectraRow, 1), gridSpan=(1, self.maxLen))

        self.spectraStartRow = spectraRow + 1

        if self.application:
            spectraWidgets = {}  # spectrum.pid, frame dict to show/hide
            for row, spectrum in enumerate(self.validSpectrumViews.keys()):
                spectraRow += 1
                f = _SpectrumRow(parent=self._spectraWidget,
                                 application=self.application,
                                 spectrum=spectrum,
                                 spectrumDisplay=displays[0],
                                 row=spectraRow, startCol=0,
                                 setLayout=True,
                                 visible=self.validSpectrumViews[spectrum])

                spectraWidgets[spectrum.pid] = f

    def _spectrumDisplaySelectionPulldownCallback(self, item):
        """Notifier Callback for selecting a spectrumDisplay
        """
        gid = self.spectrumDisplayPulldown.getText()
        self._fillSpectrumFrame([self.application.getByGid(gid)])


LINKTOPULLDOWNCLASS = 'linkToPulldownClass'
LINKTOACTIVESTATE = True

STOREDISPLAY = 'displaySettings'
STORESEQUENTIAL = 'sequentialStripsWidget'
STOREMARKS = 'markPositionsWidget'
STORECLEAR = 'autoClearMarksWidget'
STOREACTIVE = 'activePulldownClass'
STORELIST = 'listButtons'
STORENMRCHAIN = 'includeNmrChainPullSelection'


class StripPlot(Widget, _commonSettings, SignalBlocking):
    _storedState = {}

    def __init__(self, parent=None,
                 mainWindow=None,
                 callback=None,
                 returnCallback=None,
                 applyCallback=None,
                 includeDisplaySettings=True,
                 includeSequentialStrips=True,
                 includePeakLists=True, includeNmrChains=True, includeNmrChainPullSelection=False,
                 includeSpectrumTable=True,
                 defaultSpectrum=None,
                 activePulldownClass=None,
                 labelText='Display(s): ',
                 **kwds):
        super().__init__(parent, setLayout=True, **kwds)

        # Derive application, project, and current from mainWindow
        self.mainWindow = mainWindow
        if mainWindow:
            self.application = mainWindow.application
            self.project = mainWindow.application.project
            self.current = mainWindow.application.current
            displayText = [display.pid for display in self.application.ui.mainWindow.spectrumDisplays]
        else:
            self.application = None
            self.project = None
            self.current = None
            displayText = []

        self.callback = callback
        self.returnCallback = returnCallback if returnCallback else self.doCallback
        self.applyCallback = applyCallback

        self.includePeakLists = includePeakLists
        self.includeNmrChains = includeNmrChains
        self.includeNmrChainPullSelection = includeNmrChainPullSelection
        self.includeSpectrumTable = includeSpectrumTable
        self.activePulldownClass = activePulldownClass
        self.nmrChain = None

        # cannot set a notifier for displays, as these are not (yet?) implemented and the Notifier routines
        # underpinning the addNotifier call do not allow for it either
        row = 0
        colwidth = 180

        texts = [defaultSpectrum.pid] if (defaultSpectrum and defaultSpectrum is not NO_STRIP) else ([ALL] + displayText)

        if includeDisplaySettings:
            row += 1
            self.displaysWidget = SpectrumDisplaySelectionWidget(self, mainWindow=self.mainWindow, grid=(row, 0), gridSpan=(1, 1), texts=texts, displayText=[],
                                                                 displayWidgetChangedCallback=self._displayWidgetChanged, labelText=labelText)
        else:
            self.displaysWidget = None

        optionTexts = ['Show sequential strips:',
                       'Mark positions:',
                       'Auto clear marks:']
        if self.activePulldownClass is not None:
            optionTexts += ['Link to current {}:'.format(self.activePulldownClass.className)]
        _, maxDim = getTextDimensionsFromFont(textList=optionTexts)
        colwidth = maxDim.width()

        if includeSequentialStrips:
            row += 1
            self.sequentialStripsWidget = CheckBoxCompoundWidget(
                    self,
                    grid=(row, 0), vAlign='top', stretch=(0, 0), hAlign='left',
                    #minimumWidths=(colwidth, 0),
                    fixedWidths=(colwidth, None),
                    orientation='left',
                    labelText=optionTexts[0],
                    checked=False
                    )
        else:
            self.sequentialStripsWidget = None

        row += 1
        self.markPositionsWidget = CheckBoxCompoundWidget(
                self,
                grid=(row, 0), vAlign='top', stretch=(0, 0), hAlign='left',
                #minimumWidths=(colwidth, 0),
                fixedWidths=(colwidth, None),
                orientation='left',
                labelText=optionTexts[1],
                checked=True
                )

        row += 1
        self.autoClearMarksWidget = CheckBoxCompoundWidget(
                self,
                grid=(row, 0), vAlign='top', stretch=(0, 0), hAlign='left',
                #minimumWidths=(colwidth, 0),
                fixedWidths=(colwidth, None),
                orientation='left',
                labelText=optionTexts[2],
                checked=True
                )

        if self.activePulldownClass is not None:
            row += 1
            setattr(self, LINKTOPULLDOWNCLASS, CheckBoxCompoundWidget(
                    self,
                    grid=(row, 0), vAlign='top', stretch=(0, 0), hAlign='left',
                    #minimumWidths=(colwidth, 0),
                    fixedWidths=(colwidth, None),
                    orientation='left',
                    labelText=optionTexts[3],
                    tipText='Set/update current %s when selecting from pulldown' % self.activePulldownClass.className,
                    checked=LINKTOACTIVESTATE
                    ))

        row += 1
        texts = []
        tipTexts = []
        callbacks = []
        buttonTypes = []

        # put hLine and text here

        self.NMRCHAINBUTTON = None

        if includePeakLists and includeNmrChains and includeNmrChainPullSelection:
            HLine(self, grid=(row, 0), gridSpan=(1, 4),
                  colour=getColours()[DIVIDER], height=15)
            row += 1
            Label(self, text='Strip Selection', grid=(row, 0), gridSpan=(1, 4))

        if includePeakLists:
            texts += ['use Peak selection']
            tipTexts += ['Use current selected peaks']
            callbacks += [partial(self._buttonClick, STRIPPLOT_PEAKS)]
            buttonTypes += [STRIPPLOT_PEAKS]

            texts += ['use NmrAtoms from Peak selection']
            tipTexts += ['Use all nmrAtoms from current selected peaks']
            callbacks += [partial(self._buttonClick, STRIPPLOT_NMRATOMSFROMPEAKS)]
            buttonTypes += [STRIPPLOT_NMRATOMSFROMPEAKS]

        if includeNmrChains:
            texts += ['use nmrResidue selection']
            tipTexts += ['Use current selected nmrResidues']
            callbacks += [partial(self._buttonClick, STRIPPLOT_NMRRESIDUES)]
            buttonTypes += [STRIPPLOT_NMRRESIDUES]

        if includeNmrChainPullSelection:
            # get the index of this button and set the required fields
            self.NMRCHAINBUTTON = len(texts)
            texts += ['use nmrChain']
            tipTexts += ['Use nmrResidues in selected nmrChain']
            callbacks += [partial(self._buttonClick, STRIPPLOT_NMRCHAINS)]
            buttonTypes += [STRIPPLOT_NMRCHAINS]

        row += 1
        self.listButtons = RadioButtons(self, texts=texts, tipTexts=tipTexts, callback=self._buttonClick,
                                        grid=(row, 0), direction='v') if texts else None
        if self.listButtons:
            self.listButtons.buttonTypes = buttonTypes

        if self.includeNmrChainPullSelection:
            # add a pulldown to select an nmrChain
            row += 1

            self.ncWidget = NmrChainPulldown(parent=self,
                                             mainWindow=self.mainWindow, default=None,  #first NmrChain in project (if present)
                                             grid=(row, 0), gridSpan=(1, 1), minimumWidths=(0, 100),
                                             showSelectName=True,
                                             sizeAdjustPolicy=QtWidgets.QComboBox.AdjustToContents,
                                             callback=self._selectionPulldownCallback
                                             )

        self._spectraWidget = None
        self.axisCodeOptions = None

        if includeSpectrumTable:
            # create row's of spectrum information
            self._spectraRows = row + len(texts)

            self.spectrumDisplayOptionsFrame = Frame(self, setLayout=True, showBorder=False, fShape='noFrame',
                                                     grid=(1, 1), gridSpan=(row + 2, 1),
                                                     vAlign='top', hAlign='left')

            # add a new pullDown to select the active spectrumDisplay
            self.spectrumDisplayPulldown = SpectrumDisplayPulldown(parent=self.spectrumDisplayOptionsFrame,
                                                                   mainWindow=self.mainWindow, default=None,
                                                                   grid=(1, 1), gridSpan=(1, 1),
                                                                   minimumWidths=(0, 100),
                                                                   showSelectName=True,
                                                                   sizeAdjustPolicy=QtWidgets.QComboBox.AdjustToContents,
                                                                   callback=self._spectrumDisplaySelectionPulldownCallback,
                                                                   labelText='Pick Peaks in Display:'
                                                                   )

            # self._fillSpectrumFrame(self.displaysWidget._getDisplays())

        # add a spacer in the bottom-right corner to stop everything moving
        rows = self.getLayout().rowCount()
        cols = self.getLayout().columnCount()
        Spacer(self, 5, 5,
               QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding,
               grid=(rows + 20, cols + 1), gridSpan=(1, 1))

        self.maxRows = rows
        self._registerNotifiers()

    def storeWidgetState(self):
        """Store the state of the checkBoxes between popups
        """
        if self.displaysWidget:
            StripPlot._storedState[STOREDISPLAY] = self.displaysWidget.getTexts()
        if self.sequentialStripsWidget:
            StripPlot._storedState[STORESEQUENTIAL] = self.sequentialStripsWidget.get()
        StripPlot._storedState[STOREMARKS] = self.markPositionsWidget.get()
        StripPlot._storedState[STORECLEAR] = self.autoClearMarksWidget.get()
        if self.activePulldownClass is not None:
            checked = getattr(self, LINKTOPULLDOWNCLASS).get()
            StripPlot._storedState[STOREACTIVE] = checked
        StripPlot._storedState[STORELIST] = self.listButtons.getIndex()
        if self.includeNmrChainPullSelection:
            StripPlot._storedState[STORENMRCHAIN] = self.ncWidget.getIndex()

    def restoreWidgetState(self):
        """Restore the state of the checkBoxes
        """
        with self.blockWidgetSignals():
            if self.displaysWidget:
                value = StripPlot._storedState.get(STOREDISPLAY, [])
                self.displaysWidget.setTexts(value)
            if self.sequentialStripsWidget:
                value = StripPlot._storedState.get(STORESEQUENTIAL, False)
                self.sequentialStripsWidget.set(value)
            value = StripPlot._storedState.get(STOREMARKS, True)
            self.markPositionsWidget.set(value)
            value = StripPlot._storedState.get(STORECLEAR, True)
            self.autoClearMarksWidget.set(value)
            if self.activePulldownClass is not None:
                value = StripPlot._storedState.get(STOREACTIVE, LINKTOACTIVESTATE)
                getattr(self, LINKTOPULLDOWNCLASS).set(value)
            value = StripPlot._storedState.get(STORELIST, 0)
            try:
                self.listButtons.setIndex(value)
            except:
                # may be out of range
                pass
            if self.includeNmrChainPullSelection:
                value = StripPlot._storedState.get(STORENMRCHAIN, self.includeNmrChainPullSelection)
                self.ncWidget.setIndex(value)
            pass

    def setLabelText(self, label):
        """Set the text for the label attached to the list widget
        """
        self.displaysWidget.setLabelText(label) if self.displaysWidget else None

    def _displayWidgetChanged(self):
        """Handle adding/removing items from display selection
        """
        pass

        # if self.includeSpectrumTable:
        #     self._fillSpectrumFrame(self.displaysWidget._getDisplays())

    def _changeAxisCode(self):
        """Handle clicking the axis code buttons
        """
        pass

    def _buttonClick(self):
        """Handle clicking the peak/nmrChain buttons
        """
        if self.includeNmrChainPullSelection:
            self.ncWidget.setIndex(0, blockSignals=True)

    def _registerNotifiers(self):
        """Notifiers for responding to spectrumViews
        """
        # can't use setNotifier as not guaranteed a parent abstractWrapperObject
        self._spectrumViewNotifier = Notifier(self.project,
                                              [Notifier.CREATE, Notifier.DELETE, Notifier.CHANGE],  # DELETE not registering
                                              SpectrumView.className,
                                              self._spectrumViewChanged,
                                              onceOnly=True)

    def _unRegisterNotifiers(self):
        """Unregister notifiers
        """
        if self._spectrumViewNotifier:
            self._spectrumViewNotifier.unRegister()

    def _spectrumViewChanged(self, data):
        """Respond to spectrumViews being created/deleted, update contents of the spectrumWidgets frame
        """
        if self.includeSpectrumTable:
            # self._fillSpectrumFrame(self.displaysWidget._getDisplays())
            gid = self.spectrumDisplayPulldown.getText()
            self._fillSpectrumFrame([self.application.getByGid(gid)])

    def _spectrumViewVisibleChanged(self):
        """Respond to a visibleChanged in one of the spectrumViews
        """
        if self.includeSpectrumTable:
            # self._fillSpectrumFrame(self.displaysWidget._getDisplays())
            gid = self.spectrumDisplayPulldown.getText()
            self._fillSpectrumFrame([self.application.getByGid(gid)])

    def doCallback(self):
        """Handle the user callback
        """
        if self.callback:
            self.callback()

    def _returnCallback(self):
        """Handle the return from widget callback
        """
        pass

    def _cleanupWidget(self):
        """Cleanup the notifiers that are left behind after the widget is closed
        """
        self._unRegisterNotifiers()

    def _selectionPulldownCallback(self, item):
        """Notifier Callback for selecting NmrChain
        """
        self.nmrChain = self.project.getByPid(item)
        if self.nmrChain is not None and self.NMRCHAINBUTTON is not None:
            # select the nmrChain here
            self.listButtons.setIndex(self.NMRCHAINBUTTON)

        else:
            # do nothing for the minute
            pass


class _SpectrumRow(Frame):
    """Class to make a spectrum row"""

    def __init__(self, parent, application, spectrum, spectrumDisplay, row=0, startCol=0, visible=True, **kwds):
        super().__init__(parent, **kwds)

        # col = 0
        # self.checkbox = CheckBoxCompoundWidget(self, grid=(0, col), gridSpan=(1, 1), hAlign='left',
        #                                        checked=True, labelText=spectrum.pid,
        #                                        fixedWidths=[100, 50])

        self.checkbox = Label(parent, spectrum.pid, grid=(row, startCol), gridSpan=(1, 1), hAlign='left')
        self.checkbox.setEnabled(visible)

        self.spinBoxes = []

        indices = getAxisCodeMatchIndices(spectrum.axisCodes, spectrumDisplay.axisCodes)
        _height = getFontHeight()

        for ii, axisCode in enumerate(spectrum.axisCodes):
            decimals, step = (2, 0.01) if axisCode[0:1] == 'H' else (1, 0.1)
            # col += 1
            if indices[ii] is None:
                continue

            ds = DoubleSpinBoxCompoundWidget(
                    parent, grid=(row, startCol + indices[ii] + 1), gridSpan=(1, 1), hAlign='left',
                    fixedWidths=(None, _height * 4),
                    labelText=axisCode,
                    value=spectrum.assignmentTolerances[ii],
                    decimals=decimals, step=step, range=(step, None),
                    )
            ds.setObjectName(str(spectrum.pid + axisCode))
            self.spinBoxes.append(ds)

            ds.setEnabled(visible)
            ds.setCallback(partial(self._setAssignmentTolerances, ds, spectrum, ii))

        # brush = (*hexToRgbRatio(spectrum.positiveContourColour), CCPNGLWIDGET_REGIONSHADE)
        # self.guiRegion = GLTargetButtonSpinBoxes(parent, application=application,
        #                                          orientation='v', brush=brush,
        #                                          grid=(row, col))

    def _setAssignmentTolerances(self, spinBox, spectrum, ii):
        """Set the tolerance in the attached spectrum from the spinBox value
        """
        assignment = list(spectrum.assignmentTolerances)
        assignment[ii] = float(spinBox.getValue())
        spectrum.assignmentTolerances = tuple(assignment)


SETTINGSCHECKBOX = 'checkBox'


class ModuleSettingsWidget(Widget):  #, _commonSettings):

    def __init__(self, parent=None,
                 mainWindow=None,
                 settingsDict=None,
                 callback=None,
                 returnCallback=None,
                 applyCallback=None,
                 defaultListItem=None,
                 **kwds):
        super().__init__(parent, setLayout=True, **kwds)

        # Derive application, project, and current from mainWindow
        self.mainWindow = mainWindow
        if mainWindow:
            self.application = mainWindow.application
            self.project = mainWindow.application.project
            self.current = mainWindow.application.current
            displayText = [display.pid for display in self.application.ui.mainWindow.spectrumDisplays]
        else:
            self.application = None
            self.project = None
            self.current = None
            displayText = []

        self.callback = callback
        self.returnCallback = returnCallback if returnCallback else self.doCallback
        self.applyCallback = applyCallback

        # cannot set a notifier for displays, as these are not (yet?) implemented and the Notifier routines
        # underpinning the addNotifier call does not allow for it either
        row = 0
        # texts = [ALL] + defaultListItem.pid if defaultListItem else ([ALL] + displayText)
        # self.displaysWidget = SpectrumDisplaySelectionWidget(self, mainWindow=self.mainWindow, grid=(row, 0), gridSpan=(1, 1), texts=[ALL], displayText=[])
        # row += 1
        # self.chainsWidget = ChainSelectionWidget(self, mainWindow=self.mainWindow, grid=(row, 0), gridSpan=(1, 1), texts=[ALL], displayText=[], defaults=[ALL])

        self.checkBoxes = {}
        if settingsDict:
            optionTexts = []
            for item, data in settingsDict.items():
                optionTexts += [data['label']]
            _, maxDim = getTextDimensionsFromFont(textList=optionTexts)
            colwidth = maxDim.width()

            for item, data in settingsDict.items():
                row += 1
                if 'type' in data:
                    widgetType = data['type']
                    if 'kwds' in data:
                        newItem = widgetType(self, self.mainWindow, grid=(row, 0),
                                             callback=data['callBack'] if 'callBack' in data else None,
                                             **data['kwds'],
                                             )
                    else:
                        newItem = widgetType(self, self.mainWindow, grid=(row, 0),
                                             callback=data['callBack'] if 'callBack' in data else None,
                                             **{})
                    # newItem.setCallback(data['callBack'] if 'callBack' in data else None)
                    # self.checkBoxes[item] = {'widget'      : newItem,
                    #                          'item'        : item,
                    #                          'signalFunc'  : None
                    #                          }

                else:
                    newItem = CheckBoxCompoundWidget(
                            self,
                            grid=(row, 0), vAlign='top', stretch=(0, 0), hAlign='left',
                            #minimumWidths=(colwidth, 0),
                            fixedWidths=(colwidth, None),
                            orientation='left',
                            labelText=data['label'] if 'label' in data else '',
                            tipText=data['tipText'] if 'tipText' in data else '',
                            checked=data['checked'] if 'checked' in data else False,
                            callback=data['callBack'] if 'callBack' in data else None,
                            # enabled=data['enabled']
                            )
                    # newItem.setCallback(data['callBack'] if 'callBack' in data else None)
                    if 'enabled' in data:
                        newItem.setEnabled(data['enabled'])

                self.checkBoxes[item] = {'widget'    : newItem,
                                         'item'      : item,
                                         'signalFunc': None
                                         }

                # if data['_init']:
                #     # attach a one-off signal to the checkBox
                #     signalFunc = partial(self._checkInit, newItem, item, data)
                #     self.checkBoxes[item]['signalFunc'] = signalFunc
                #
                #     # connected = newItem.checkBox.connectNotify.connect(self._checkNotifier)
                #     stuff = newItem.checkBox.stateChanged.connect(signalFunc)
                #     print('>>>', stuff, id(stuff))

        # add a spacer in the bottom-right corner to stop everything moving
        rows = self.getLayout().rowCount()
        cols = self.getLayout().columnCount()
        Spacer(self, 5, 5,
               QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding,
               grid=(rows, cols), gridSpan=(1, 1))

        self.setMinimumWidth(self.sizeHint().width())
        self._registerNotifiers()

    def _changeAxisCode(self):
        """Handle clicking the axis code buttons
        """
        pass

    def _checkInit(self, checkBoxItem, item, data):
        """This is a hack so that the state changes when the layout loads
        After the layout initialise, this function is removed
        """
        # remove the one-off signal
        for vals in self.checkBoxes.values():
            if vals['item'] == item:
                checkBoxItem.checkBox.stateChanged.disconnect(vals['signalFunc'])
                # print('>>>_checkInit removed')

        # call the initialise function
        initFunc = data['_init']
        initFunc()

    def _registerNotifiers(self):
        """Notifiers for responding to spectrumViews
        """
        pass

    def _unRegisterNotifiers(self):
        """Unregister notifiers
        """
        pass

    def doCallback(self):
        """Handle the user callback
        """
        if self.callback:
            self.callback()

    def _returnCallback(self):
        """Handle the return from widget callback
        """
        pass

    def _cleanupWidget(self):
        """Cleanup the notifiers that are left behind after the widget is closed
        """
        self._unRegisterNotifiers()

    def _getCheckBox(self, widgetName):
        """Get the required widget from the new setting Widget class
        Should be moved to a new settings class
        """
        if widgetName in self.checkBoxes and SETTINGSCHECKBOX in self.checkBoxes[widgetName]:
            return self.checkBoxes[widgetName][SETTINGSCHECKBOX]


class SpectrumDisplaySelectionWidget(ListCompoundWidget):
    # TODO Change to be a subclass of ObjectSelectionWidget
    def __init__(self, parent=None, mainWindow=None, vAlign='top', stretch=(0, 0), hAlign='left',
                 vPolicy='minimal', fixedWidths=(None, None, None), orientation='left', labelText='Display(s):',
                 tipText='SpectrumDisplay modules to respond to double-click',
                 texts=None, callback=None, displayWidgetChangedCallback=None,
                 defaultListItem=None, displayText=[],
                 **kwds):

        if not texts:
            texts = [ALL] + defaultListItem.pid if defaultListItem else ([ALL] + displayText)

        # Derive application, project, and current from mainWindow
        self.mainWindow = mainWindow
        if mainWindow:
            self.application = mainWindow.application
            self.project = mainWindow.application.project
            self.current = mainWindow.application.current
        else:
            self.application = None
            self.project = None
            self.current = None

        self._displayWidgetChangedCallback = displayWidgetChangedCallback
        self._selectDisplayInListCallback = callback

        super().__init__(parent=parent,
                         vAlign=vAlign, stretch=stretch, hAlign=hAlign, vPolicy=vPolicy,
                         fixedWidths=fixedWidths, orientation=orientation,
                         labelText=labelText, tipText=tipText, texts=texts,
                         callback=self._selectDisplayInList, **kwds)
        if self.project:
            self._notifierRename = Notifier(theObject=self.project,
                                       triggers=[Notifier.RENAME],
                                       targetName='SpectrumDisplay',
                                       callback=self._spectrumDisplayRenamed)
            self._notifierDelete = Notifier(theObject=self.project,
                                       triggers=[Notifier.DELETE],
                                       targetName='SpectrumDisplay',
                                       callback=self._spectrumDisplayDeleted)

        # default to 5 rows
        self.setFixedHeights((None, None, 5 * getFontHeight()))
        self.setPreSelect(self._fillDisplayWidget)

        # handle signals when the items in the displaysWidget have changed
        model = self.listWidget.model()
        model.rowsInserted.connect(self._displayWidgetChanged)
        model.rowsRemoved.connect(self._displayWidgetChanged)
        self.listWidget.cleared.connect(self._displayWidgetChanged)

    def _selectDisplayInList(self):
        """Handle clicking items in display selection
        """
        if self._selectDisplayInListCallback:
            self._selectDisplayInListCallback()

    def _displayWidgetChanged(self):
        """Handle adding/removing items from display selection
        """
        if self._displayWidgetChangedCallback:
            self._displayWidgetChangedCallback()

    def _spectrumDisplayDeleted(self, dataDict, **kwargs):
        obj = dataDict.get(Notifier.OBJECT)
        currentTexts = self.getTexts()
        if obj.pid in currentTexts:
            self.removeTexts([obj.pid])

    def _spectrumDisplayRenamed(self, dataDict, **kwargs):
        obj = dataDict.get(Notifier.OBJECT)
        currentTexts = self.getTexts()
        toRemoveTexts = []
        for i in currentTexts: # could use oldPid from data. not yet available for SpectrumDisplay
            if i != ALL:
                if not self.application.getByGid(i):
                    toRemoveTexts.append(i)
        self.removeTexts(toRemoveTexts)
        self.addText(obj.pid)

    def _changeAxisCode(self):
        """Handle clicking the axis code buttons
        """
        pass

    def _fillDisplayWidget(self):
        """Fill the display box with the currently available spectrumDisplays
        """
        ll = ['> select-to-add <'] + [ALL]
        if self.mainWindow:
            ll += [display.pid for display in self.mainWindow.spectrumDisplays]
        self.pulldownList.setData(texts=ll)

    def _getDisplays(self):
        """Return list of displays to navigate - if needed
        """
        if not self.application:
            return []

        displays = []
        # check for valid displays
        gids = self.getTexts()
        if len(gids) == 0: return displays
        if ALL in gids:
            displays = self.mainWindow.spectrumDisplays
        else:
            displays = [self.application.getByGid(gid) for gid in gids if gid != ALL]
        return displays


    def unRegister(self):
        """Unregister the notifiers; needs to be called when discarding an instance
        """
        try:
            if self._notifierRename is not None:
                self._notifierRename.unRegister()
                del (self._notifierRename)
            if self._notifierDelete is not None:
                self._notifierDelete.unRegister()
                del (self._notifierDelete)
        except:
            pass


class ObjectSelectionWidget(ListCompoundWidget):
    # TODO add missing notifiers
    KLASS = None

    def __init__(self, parent=None, mainWindow=None, vAlign='top', stretch=(0, 0), hAlign='left',
                 vPolicy='minimal', fixedWidths=(None, None, None), orientation='left',
                 labelText=None, tipText=None,
                 texts=None, callback=None, objectWidgetChangedCallback=None,
                 defaultListItem=None, displayText=[],
                 **kwds):

        if not self.KLASS:
            raise RuntimeError('Klass must be specified')

        if not texts:
            texts = [ALL] + defaultListItem.pid if defaultListItem else ([ALL] + displayText)

        if mainWindow:
            self.mainWindow = mainWindow
            self.application = mainWindow.application
            self.project = mainWindow.application.project
        else:
            self.mainWindow = self.application = self.project = None

        self._objectWidgetChangedCallback = objectWidgetChangedCallback
        self._selectObjectInListCallback = callback

        labelText = labelText or 'Select {}:'.format((self.KLASS._pluralLinkName).capitalize())
        tipText = tipText or 'Set active {} for module:'.format((self.KLASS._pluralLinkName).capitalize())

        super().__init__(parent=parent,
                         vAlign=vAlign, stretch=stretch, hAlign=hAlign, vPolicy=vPolicy,
                         fixedWidths=fixedWidths, orientation=orientation,
                         labelText=labelText, tipText=tipText, texts=texts,
                         callback=self._selectObjectInList, **kwds)

        # default to 5 rows
        self.setFixedHeights((None, None, 5 * getFontHeight()))
        self.setPreSelect(self._fillPulldownListWidget)

        # handle signals when the items in the displaysWidget have changed
        model = self.listWidget.model()
        model.rowsInserted.connect(self._objectWidgetChanged)
        model.rowsRemoved.connect(self._objectWidgetChanged)
        self.listWidget.cleared.connect(self._objectWidgetChanged)

    def _selectObjectInList(self):
        """Handle clicking items in object selection
        """
        if self._selectObjectInListCallback:
            self._selectObjectInListCallback()

    def _objectWidgetChanged(self):
        """Handle adding/removing items from object selection
        """
        if self._objectWidgetChangedCallback:
            self._objectWidgetChangedCallback()

    def _changeAxisCode(self):
        """Handle clicking the axis code buttons
        """
        pass

    def _fillPulldownListWidget(self):
        """Fill the pulldownList with the currently available objects
        """
        ll = ['> select-to-add <'] + [ALL]
        if self.project:
            ll += [obj.pid for obj in getattr(self.project, self.KLASS._pluralLinkName, [])]
        self.pulldownList.setData(texts=ll)

    def _getDisplays(self):
        """Return list of objects to navigate - if needed
        """
        pass

    def _getObjects(self):
        """Return list of objects in the listWidget selection
        """
        if not self.project:
            return []

        objects = []
        pids = self.getTexts()
        if len(pids) == 0: return objects

        if ALL in pids:
            objects = getattr(self.project, self.KLASS._pluralLinkName, [])
        else:
            objects = [self.project.getByPid(pid) for pid in pids if pid != ALL]
        return objects


class ChainSelectionWidget(ObjectSelectionWidget):
    KLASS = Chain


class RestraintListSelectionWidget(ObjectSelectionWidget):
    KLASS = RestraintList


if __name__ == '__main__':
    import os
    import sys
    from PyQt5 import QtGui, QtWidgets


    def myCallback(ph0, ph1, pivot, direction):
        print(ph0, ph1, pivot, direction)


    qtApp = QtWidgets.QApplication(['Test Phase Frame'])

    #QtCore.QCoreApplication.setApplicationName('TestPhasing')
    #QtCore.QCoreApplication.setApplicationVersion('0.1')

    widget = QtWidgets.QWidget()
    frame = StripPlot(widget, callback=myCallback)
    widget.show()
    widget.raise_()

    os._exit(qtApp.exec_())
