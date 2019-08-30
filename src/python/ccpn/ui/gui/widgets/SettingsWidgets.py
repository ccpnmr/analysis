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
__modifiedBy__ = "$modifiedBy: CCPN $"
__dateModified__ = "$dateModified: 2017-07-07 16:32:54 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.b5 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtCore import pyqtSignal, pyqtSlot
from ccpn.ui.gui.widgets.CompoundWidgets import ListCompoundWidget
from ccpn.ui.gui.widgets.Widget import Widget
from ccpn.ui.gui.widgets.RadioButtons import RadioButtons
from ccpn.ui.gui.widgets.Spacer import Spacer
from ccpn.ui.gui.widgets.CheckBox import CheckBox
from ccpn.ui.gui.widgets.CheckBoxes import CheckBoxes
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.Frame import Frame
from ccpn.ui.gui.widgets.CompoundWidgets import CheckBoxCompoundWidget, DoubleSpinBoxCompoundWidget
from ccpn.ui.gui.guiSettings import getColours, DIVIDER, SOFTDIVIDER
from ccpn.ui.gui.widgets.HLine import HLine
from ccpn.ui.gui.widgets.PulldownListsForObjects import NmrChainPulldown, SpectrumDisplayPulldown
from ccpn.core.lib.Notifiers import Notifier
from ccpn.ui._implementation.SpectrumView import SpectrumView
from functools import partial
from ccpn.ui.gui.lib.OpenGL.CcpnOpenGLNotifier import GLNotifier
from ccpn.ui.gui.lib.OpenGL.CcpnOpenGLDefs import AXISXUNITS, AXISYUNITS, AXISLOCKASPECTRATIO, \
    SYMBOLTYPES, SYMBOLSIZE, SYMBOLTHICKNESS, ANNOTATIONTYPES, AXISUSEFIXEDASPECTRATIO
from ccpn.ui.gui.widgets.Spinbox import Spinbox
from ccpn.ui.gui.guiSettings import CCPNGLWIDGET_REGIONSHADE
from ccpn.util.Colour import hexToRgbRatio
from ccpn.ui.gui.widgets.GLLinearRegionsPlot import GLTargetButtonSpinBoxes
from ccpn.util.Common import getAxisCodeMatchIndices
from ccpn.util.OrderedSet import OrderedSet


ALL = '<all>'

STRIPPLOT_PEAKS = 'peaks'
STRIPPLOT_NMRRESIDUES = 'nmrResidues'
STRIPPLOT_NMRCHAINS = 'nmrChains'
NO_STRIP = 'noStrip'
LineEditsMinimumWidth = 195


class SpectrumDisplaySettings(Widget):
    # signal for parentWidgets to respond to changes in the widget
    settingsChanged = pyqtSignal(dict)
    symbolsChanged = pyqtSignal(dict)
    stripArrangementChanged = pyqtSignal(int)

    def __init__(self, parent=None,
                 mainWindow=None,
                 spectrumDisplay=None,
                 callback=None, returnCallback=None, applyCallback=None,
                 xAxisUnits=0, xTexts=[], showXAxis=True,
                 yAxisUnits=0, yTexts=[], showYAxis=True,
                 lockAspectRatio=False,
                 useFixedAspectRatio=False,
                 symbolType=0, annotationType=0, symbolSize=9, symbolThickness=2,
                 stripArrangement=0,
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

        # insert widgets into the parent widget
        row = 0
        self.xAxisUnits = Label(parent, text="X Axis Units", grid=(row, 0))
        self.xAxisUnitsButtons = RadioButtons(parent, texts=xTexts,
                                              objectNames=[text + '_x_SDS' for text in xTexts],
                                              selectedInd=xAxisUnits,
                                              callback=self._settingsChanged,
                                              direction='h',
                                              grid=(row, 1), hAlign='l',
                                              tipTexts=None,
                                              )
        # for button in self.xAxisUnitsButtons.radioButtons:
        #     button.setObjectName(button.objectName()+'_x')

        self.xAxisUnits.setVisible(showXAxis)
        self.xAxisUnitsButtons.setVisible(showXAxis)

        row += 1
        self.yAxisUnits = Label(parent, text="Y Axis Units", grid=(row, 0))
        self.yAxisUnitsButtons = RadioButtons(parent, texts=yTexts,
                                              objectNames=[text + '_y_SDS' for text in xTexts],
                                              selectedInd=yAxisUnits,
                                              callback=self._settingsChanged,
                                              direction='h',
                                              grid=(row, 1), hAlign='l',
                                              tipTexts=None)
        # for button in self.yAxisUnitsButtons.radioButtons:
        #     button.setObjectName(button.objectName()+'_y')

        self.yAxisUnits.setVisible(showYAxis)
        self.yAxisUnitsButtons.setVisible(showYAxis)

        row += 1
        self.lockAspect = Label(parent, text="Lock Aspect Ratio", grid=(row, 0))
        self.lockAspectCheckBox = CheckBox(parent, grid=(row, 1), checked=lockAspectRatio, objectName='SDS_lockAspect')
        self.lockAspectCheckBox.clicked.connect(self._settingsChanged)

        row += 1
        self.useFixedAspect = Label(parent, text="     - use Fixed Aspect Ratio", grid=(row, 0))
        self.useFixedAspectCheckBox = CheckBox(parent, grid=(row, 1), checked=useFixedAspectRatio, objectName='SDS_useFixedAspect')
        self.useFixedAspectCheckBox.clicked.connect(self._settingsUseFixedChanged)
        # self.useFixedAspectCheckBox.setEnabled(lockAspectRatio)

        if not self._spectrumDisplay.is1D:
            row += 1
            self.symbolsLabel = Label(parent, text="Symbol Type", grid=(row, 0))
            self.symbol = RadioButtons(parent, texts=['Cross', 'lineWidths', 'Filled lineWidths', 'Plus'],
                                       objectNames=['symSDS_Cross', 'symSDS_lineWidths', 'symSDS_Filled lineWidths', 'symSDS_Plus'],
                                       selectedInd=symbolType,
                                       callback=self._symbolsChanged,
                                       direction='h',
                                       grid=(row, 1), hAlign='l',
                                       tipTexts=None,
                                       )

            row += 1
            self.annotationsLabel = Label(parent, text="Symbol Annotation", grid=(row, 0))
            self.annotationsData = RadioButtons(parent, texts=['Short', 'Full', 'Pid', 'Minimal', 'Peak Id'],
                                                objectNames=['annSDS_Short', 'annSDS_Full', 'annSDS_Pid', 'annSDS_Minimal', 'annSDS_Id'],
                                                selectedInd=annotationType,
                                                callback=self._symbolsChanged,
                                                direction='horizontal',
                                                grid=(row, 1), hAlign='l',
                                                tipTexts=None,
                                                )

        row += 1
        self.symbolSizePixelLabel = Label(parent, text="Symbol Size (pixel)", grid=(row, 0))
        self.symbolSizePixelData = Spinbox(parent, step=1,
                                           min=2, max=50, grid=(row, 1), hAlign='l', objectName='SDS_symbolSize')
        self.symbolSizePixelData.setMinimumWidth(LineEditsMinimumWidth)
        self.symbolSizePixelData.setValue(int(symbolSize))
        self.symbolSizePixelData.valueChanged.connect(self._symbolsChanged)

        row += 1
        self.symbolThicknessLabel = Label(parent, text="Symbol Thickness (point)", grid=(row, 0))
        self.symbolThicknessData = Spinbox(parent, step=1,
                                           min=1, max=20, grid=(row, 1), hAlign='l', objectName='SDS_symbolThickness')
        self.symbolThicknessData.setMinimumWidth(LineEditsMinimumWidth)
        self.symbolThicknessData.setValue(int(symbolThickness))
        self.symbolThicknessData.valueChanged.connect(self._symbolsChanged)

        row += 1
        self.stripArrangementLabel = Label(parent, text="Strip Arrangement", grid=(row, 0))
        self.stripArrangementButtons = RadioButtons(parent, texts=['    ', '    '],
                                                    objectNames=['stripSDS_Row', 'stripSDS_Column'],
                                                    selectedInd=stripArrangement,
                                                    callback=self._stripArrangementChanged,
                                                    direction='horizontal',
                                                    grid=(row, 1), hAlign='l',
                                                    tipTexts=None,
                                                    icons=[('icons/strip-row', (24, 24)),
                                                           ('icons/strip-column', (24, 24))
                                                           ],
                                                    )

        row += 1
        self._spacer = Spacer(parent, 5, 5,
                              QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding,
                              grid=(row, 2), gridSpan=(1, 1))

        self._parent.setContentsMargins(5, 5, 5, 5)

        # connect to the lock changed pyqtSignal
        self._GLSignals = GLNotifier(parent=self._parent)
        self._GLSignals.glAxisLockChanged.connect(self._lockAspectRatioChangedInDisplay)
        self._GLSignals.glSymbolsChanged.connect(self._symbolsChangedInDisplay)

    def getValues(self):
        """Return a dict containing the current settings
        """
        return {AXISXUNITS             : self.xAxisUnitsButtons.getIndex(),
                AXISYUNITS             : self.yAxisUnitsButtons.getIndex(),
                AXISLOCKASPECTRATIO    : self.lockAspectCheckBox.isChecked(),
                AXISUSEFIXEDASPECTRATIO: self.useFixedAspectCheckBox.isChecked(),
                SYMBOLTYPES            : self.symbol.getIndex() if not self._spectrumDisplay.is1D else 0,
                ANNOTATIONTYPES        : self.annotationsData.getIndex() if not self._spectrumDisplay.is1D else 0,
                SYMBOLSIZE             : int(self.symbolSizePixelData.text()),
                SYMBOLTHICKNESS        : int(self.symbolThicknessData.text())
                }

    def _settingsUseFixedChanged(self):
        """If useFixed enabled and lock is disabled then enable lock
        """
        # aL = self.lockAspectCheckBox.isChecked()
        # uFA = self.useFixedAspectCheckBox.isChecked()
        #
        # # enable lockAspect
        # if uFA and not aL:
        #     self.lockAspectCheckBox.setChecked(True)

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
            self.lockAspectCheckBox.setChecked(aDict[GLNotifier.GLVALUES][0])
            self.useFixedAspectCheckBox.setChecked(aDict[GLNotifier.GLVALUES][1])

    @pyqtSlot()
    def _symbolsChanged(self):
        """Handle changing the symbols
        """
        self.symbolsChanged.emit(self.getValues())

    @pyqtSlot(dict)
    def _symbolsChangedInDisplay(self, aDict):
        """Respond to an external change in symbol settings
        """
        if aDict[GLNotifier.GLSPECTRUMDISPLAY] == self._spectrumDisplay:
            values = aDict[GLNotifier.GLVALUES]
            self.blockSignals(True)

            if not self._spectrumDisplay.is1D:
                # only update if Nd
                self.symbol.setIndex(values[SYMBOLTYPES])
                self.annotationsData.setIndex(values[ANNOTATIONTYPES])

            self.symbolSizePixelData.set(values[SYMBOLSIZE])
            self.symbolThicknessData.set(values[SYMBOLTHICKNESS])
            self.blockSignals(False)

    def _stripArrangementChanged(self):
        """Emit a signal if the strip arrangement buttons have been pressed
        """
        self.stripArrangementChanged.emit(self.stripArrangementButtons.getIndex())

    def doCallback(self):
        """Handle the user callback
        """
        if self.callback:
            self.callback()

    def _returnCallback(self):
        """Handle the return from widget callback
        """
        pass


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

        from ccpn.util.Common import getAxisCodeMatch, getAxisCodeMatchIndices

        validSpectrumViews = {}

        # loop through all the selected displays/spectrumViews that are visible
        for dp in displays:

            # ignore undefined displays
            if not dp:
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


class StripPlot(Widget, _commonSettings):

    def __init__(self, parent=None,
                 mainWindow=None,
                 callback=None,
                 returnCallback=None,
                 applyCallback=None,
                 includeDisplaySettings=True,
                 includePeakLists=True, includeNmrChains=True, includeNmrChainPullSelection=False,
                 includeSpectrumTable=True,
                 defaultSpectrum=None,
                 activePulldownClass=None,
                 labelText='Display(s):',
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

        row += 1
        self.sequentialStripsWidget = CheckBoxCompoundWidget(
                self,
                grid=(row, 0), vAlign='top', stretch=(0, 0), hAlign='left',
                #minimumWidths=(colwidth, 0),
                fixedWidths=(colwidth, 30),
                orientation='left',
                labelText='Show sequential strips:',
                checked=False
                )

        row += 1
        self.markPositionsWidget = CheckBoxCompoundWidget(
                self,
                grid=(row, 0), vAlign='top', stretch=(0, 0), hAlign='left',
                #minimumWidths=(colwidth, 0),
                fixedWidths=(colwidth, 30),
                orientation='left',
                labelText='Mark positions:',
                checked=True
                )

        row += 1
        self.autoClearMarksWidget = CheckBoxCompoundWidget(
                self,
                grid=(row, 0), vAlign='top', stretch=(0, 0), hAlign='left',
                #minimumWidths=(colwidth, 0),
                fixedWidths=(colwidth, 30),
                orientation='left',
                labelText='Auto clear marks:',
                checked=True
                )

        if self.activePulldownClass is not None:
            row += 1
            setattr(self, LINKTOPULLDOWNCLASS, CheckBoxCompoundWidget(
                    self,
                    grid=(row, 0), vAlign='top', stretch=(0, 0), hAlign='left',
                    #minimumWidths=(colwidth, 0),
                    fixedWidths=(colwidth, 30),
                    orientation='left',
                    labelText='Link to current %s:' % self.activePulldownClass.className,
                    tipText='Set/update current %s when selecting from pulldown' % self.activePulldownClass.className,
                    checked=False
                    ))

        row += 1
        texts = []
        tipTexts = []
        callbacks = []
        buttonTypes = []

        # put hLine and text here

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
        if includeNmrChains:
            texts += ['use nmrResidue selection']
            tipTexts += ['Use current selected nmrResidues']
            callbacks += [partial(self._buttonClick, STRIPPLOT_NMRRESIDUES)]
            buttonTypes += [STRIPPLOT_NMRRESIDUES]
        if includeNmrChainPullSelection:
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
                                             project=self.project, default=None,  #first NmrChain in project (if present)
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
                                                                   project=self.project, default=None,
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
        if self.nmrChain is not None:
            # select the nmrChain here
            self.listButtons.setIndex(2)

        else:
            # do nothing for the minute
            pass


class _SpectrumRow(Frame):
    "Class to make a spectrum row"

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

        for ii, axisCode in enumerate(spectrum.axisCodes):
            decimals, step = (2, 0.01) if axisCode[0:1] == 'H' else (1, 0.1)
            # col += 1
            if indices[ii] is None:
                continue

            ds = DoubleSpinBoxCompoundWidget(
                    parent, grid=(row, startCol + indices[ii] + 1), gridSpan=(1, 1), hAlign='left',
                    fixedWidths=(30, 50),
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


class SequenceGraphSettings(Widget):  #, _commonSettings):

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
        colwidth = 180

        texts = [ALL] + defaultListItem.pid if defaultListItem else ([ALL] + displayText)

        self.displaysWidget = SpectrumDisplaySelectionWidget(self, mainWindow=self.mainWindow, grid=(row, 0), gridSpan=(1, 1), texts=[ALL], displayText=[])

        self.checkBoxes = {}
        if settingsDict:
            for item, data in settingsDict.items():
                row += 1
                newItem = CheckBoxCompoundWidget(
                        self,
                        grid=(row, 0), vAlign='top', stretch=(0, 0), hAlign='left',
                        #minimumWidths=(colwidth, 0),
                        fixedWidths=(colwidth, 30),
                        orientation='left',
                        labelText=data['label'] if 'label' in data else '',
                        tipText=data['tipText'] if 'tipText' in data else '',
                        checked=data['checked'] if 'checked' in data else False,
                        callback=data['callBack'] if 'callBack' in data else None,
                        # enabled=data['enabled']
                        )
                if 'enabled' in data:
                    newItem.setEnabled(data['enabled'])

                self.checkBoxes[item] = {'checkBox'  : newItem,
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
                print('>>>_checkInit removed')

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

    def __init__(self, parent=None, mainWindow=None, vAlign='top', stretch=(0, 0), hAlign='left',
                 vPolicy='minimal', fixedWidths=(140, 140, 140), orientation='left', labelText='Display(s):',
                 tipText='SpectrumDisplay modules to respond to double-click',
                 texts=None, callback=None, displayWidgetChangedCallback=None,
                 defaultListItem=None, displayText=[],
                 **kwds):

        if not texts:
            texts = [ALL] + defaultListItem.pid if defaultListItem else ([ALL] + displayText)

        self.mainWindow = mainWindow
        self.application = mainWindow.application
        self._displayWidgetChangedCallback = displayWidgetChangedCallback
        self._selectDisplayInListCallback = callback

        super().__init__(parent=parent,
                         vAlign=vAlign, stretch=stretch, hAlign=hAlign, vPolicy=vPolicy,
                         fixedWidths=fixedWidths, orientation=orientation,
                         labelText=labelText, tipText=tipText, texts=texts,
                         callback=self._selectDisplayInList, **kwds)

        self.setFixedHeights((None, None, 40))
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

    sys.exit(qtApp.exec_())
