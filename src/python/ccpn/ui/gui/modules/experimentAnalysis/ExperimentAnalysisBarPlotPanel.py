#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (https://www.ccpn.ac.uk) 2014 - 2023"
__credits__ = ("Ed Brooksbank, Joanna Fox, Victoria A Higman, Luca Mureddu, Eliza Płoskoń",
               "Timothy J Ragan, Brian O Smith, Gary S Thompson & Geerten W Vuister")
__licence__ = ("CCPN licence. See https://ccpn.ac.uk/software/licensing/")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, https://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Luca Mureddu $"
__dateModified__ = "$dateModified: 2023-05-04 14:06:22 +0100 (Thu, May 04, 2023) $"
__version__ = "$Revision: 3.1.1 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Luca Mureddu $"
__date__ = "$Date: 2022-05-20 12:59:02 +0100 (Fri, May 20, 2022) $"
#=========================================================================================
# Start of code
#=========================================================================================

import pyqtgraph as pg
from PyQt5 import QtCore
from ccpn.util.Logging import getLogger
from ccpn.core.lib.Notifiers import Notifier
import ccpn.framework.lib.experimentAnalysis.SeriesAnalysisVariables as sv
import ccpn.ui.gui.modules.experimentAnalysis.ExperimentAnalysisGuiNamespaces as guiNameSpaces
from ccpn.util.Colour import colorSchemeTable, hexToRgb, rgbaRatioToHex, colourNameToHexDict
from ccpn.ui.gui.modules.experimentAnalysis.ExperimentAnalysisGuiPanel import GuiPanel
from ccpn.ui.gui.modules.experimentAnalysis.ExperimentAnalysisToolBars import BarPlotToolBar
from ccpn.ui.gui.widgets.BarGraphWidget import BarGraphWidget, TICKOPTIONS, AllTicks, MinimalTicks
from ccpn.ui.gui.guiSettings import CCPNGLWIDGET_HEXBACKGROUND, GUISTRIP_PIVOT, CCPNGLWIDGET_HIGHLIGHT, CCPNGLWIDGET_LABELLING
from ccpn.ui.gui.guiSettings import getColours, DIVIDER
from ccpn.ui.gui.widgets.Font import getFont
from ccpn.ui.gui.widgets.Label import Label
import numpy as np
import ccpn.framework.lib.experimentAnalysis.SeriesAnalysisVariables as seriesVariables
import pandas as pd

class BarPlotPanel(GuiPanel):

    position = 3
    panelName = guiNameSpaces.BarPlotPanel

    def __init__(self, guiModule, *args, **Framekwargs):
        GuiPanel.__init__(self, guiModule,*args , **Framekwargs)
        self._appearancePanel = self.guiModule.settingsPanelHandler.getTab(guiNameSpaces.Label_GeneralAppearance)
        self._toolbarPanel = self.guiModule.panelHandler.getToolBarPanel()
        self._viewMode = guiNameSpaces.PlotViewMode_Mirrored
        self._plottedDf = None
        self._aboveX = []
        self._belowX = []
        self._untraceableX = []
        self._errorHeights = {}
        ## Y
        self._aboveY = []
        self._belowY = []
        self._untraceableY = []
        ## Objects
        self._aboveObjects = []
        self._belowObjects = []
        self._untraceableObjects = []
        ## Brush
        self._aboveBrush = guiNameSpaces.BAR_aboveBrushHex
        self._belowBrush = guiNameSpaces.BAR_belowBrushHex
        self._untraceableBrush = guiNameSpaces.BAR_untracBrushHex
        self._gradientbrushes = []
        self._tresholdLineBrush = None
        self._gradientbrushes = []

        _thresholdValueW = self._appearancePanel.getWidget(guiNameSpaces.WidgetVarName_ThreshValue)
        if _thresholdValueW:
            self.barGraphWidget.xLine.setPos(_thresholdValueW.getValue())
            self.barGraphWidget.showThresholdLine(True)
            _thresholdValueW.doubleSpinBox.valueChanged.connect(self._updateThresholdValueFromSettings)

        #     current
        self._selectCurrentCONotifier = Notifier(self.current, [Notifier.CURRENT], targetName='collections',
                                                 callback=self._currentCollectionCallback, onceOnly=True)

        self.guiModule.mainTableChanged.connect(self._mainTableChanged)
        self.guiModule.mainTableSortingChanged.connect(self._mainTableChanged)


    def initWidgets(self):
        ## this colour def could go in an higher position as they are same for all possible plots
        colour = rgbaRatioToHex(*getColours()[CCPNGLWIDGET_LABELLING])
        self.backgroundColour = getColours()[CCPNGLWIDGET_HEXBACKGROUND]
        self.gridPen = pg.functions.mkPen(colour, width=1, style=QtCore.Qt.SolidLine)
        self.gridFont = getFont()
        self.originAxesPen = pg.functions.mkPen(hexToRgb(getColours()[GUISTRIP_PIVOT]), width=1,
                                                style=QtCore.Qt.DashLine)
        self.fittingLinePen = pg.functions.mkPen(hexToRgb(getColours()[DIVIDER]), width=0.5, style=QtCore.Qt.DashLine)
        self.selectedPointPen = pg.functions.mkPen(rgbaRatioToHex(*getColours()[CCPNGLWIDGET_HIGHLIGHT]), width=4)
        self.selectedLabelPen = pg.functions.mkBrush(rgbaRatioToHex(*getColours()[CCPNGLWIDGET_HIGHLIGHT]), width=4)
        self.barGraphWidget = BarGraphWidget(self, application=self.application, backgroundColour=self.backgroundColour,
                                             actionCallback=self._mouseDoubleClickEvent,
                                             selectionCallback=self._mouseSingleClickEvent,
                                             hoverCallback=self._mouseHoverCallbackEvent,
                                             selectionBoxEnabled = False,
                                             threshouldLine=0.1, grid=(1,0), gridSpan=(1, 2))
        self.barGraphWidget.showThresholdLine(True)

        self.barGraphWidget.xLine.sigPositionChangeFinished.connect(self._thresholdLineMoved)
        self._setBarGraphWidget()
        self.toolbar = BarPlotToolBar(parent=self, plotItem=self.barGraphWidget, guiModule=self.guiModule,
                                                     grid=(0, 0),  hAlign='l', hPolicy='preferred')
        self.currentCollectionLabel = Label(self , text='', grid=(0, 1), hAlign='r',)

    @property
    def viewMode(self):
        return self._viewMode

    def setViewMode(self, mode):
        if mode not in guiNameSpaces.PlotViewModes:
            raise RuntimeError(f'View Mode {mode} not implemented')
        self._viewMode = mode

    def setXLabel(self, label='', includeSortingLabel=True):

        htmlLabel = f'''<p><strong>{label}</strong></p> '''

        if includeSortingLabel:
            sortingLabel, sortOrder = self.guiModule._getSortingHeaderFromMainTable()
            if self.viewMode == guiNameSpaces.PlotViewMode_SecondaryStructure:
                sortingLabel, sortOrder = sv.NMRRESIDUECODE, 0  # this viewmode is only sorted by ResidueCode (ascending)

            if sortingLabel not in [label, '', ' ', None] :
                upSymbol = guiNameSpaces.TRIANGLE_UP_HTML
                downSymbol =  guiNameSpaces.TRIANGLE_DOWN_HTML
                sortOrderIcon = upSymbol if sortOrder == 0 else downSymbol
                sortingLabel = f' (Sorted by {sortingLabel} {sortOrderIcon})'
                htmlLabel = f''' <p><strong>{label}</strong> <em>{sortingLabel}</em></p> ''' #Use HTML to have different fonts in the same label.

        self.barGraphWidget.plotWidget.setLabel('bottom', htmlLabel)

    def setYLabel(self, label=''):
        self.barGraphWidget.plotWidget.setLabel('left', label)

    def _getAxis(self, axisName):
        return self.barGraphWidget.plotWidget.plotItem.getAxis(axisName)

    def _setBarGraphWidget(self):
        self.barGraphWidget.setViewBoxLimits(0, None, 0, None)
        self.barGraphWidget.xLine.hide()
        self.barGraphWidget.plotWidget.plotItem.getAxis('bottom').setPen(self.gridPen)
        self.barGraphWidget.plotWidget.plotItem.getAxis('left').setPen(self.gridPen)
        self.barGraphWidget.plotWidget.plotItem.getAxis('bottom').tickFont = self.gridFont
        self.barGraphWidget.plotWidget.plotItem.getAxis('left').tickFont = self.gridFont

    def _thresholdLineMoved(self):
        pos = self.barGraphWidget.xLine.pos().y()
        if self._appearancePanel:
            w = self._appearancePanel.getWidget(guiNameSpaces.WidgetVarName_ThreshValue)
            if w:
                with w.blockWidgetSignals():
                    w.setValue(pos)
        self.updatePanel()

    def _mainTableChanged(self):
        if self.viewMode == guiNameSpaces.PlotViewMode_SecondaryStructure:
            getLogger().debug2(f'BarGraph-view {self.viewMode}: Sorting/Filtering on the main table does not change the Plot.')
            return
        self.updatePanel()

    @property
    def xColumnName(self):
        """Returns selected colour name """
        value = None
        if self._appearancePanel:
            w = self._appearancePanel.getWidget(guiNameSpaces.WidgetVarName_BarGraphXcolumnName)
            if w:
                value = w.getText()
        return value

    @property
    def yColumnName(self):
        """Returns selected y Column name """
        value = None
        if self._appearancePanel:
            w = self._appearancePanel.getWidget(guiNameSpaces.WidgetVarName_BarGraphYcolumnName)
            if w:
                value = w.getText()
        return value

    @property
    def thresholdValue(self):
        return self.barGraphWidget.xLine.pos().y()

    @thresholdValue.setter
    def thresholdValue(self, value):
        self.barGraphWidget.xLine.setPos(value)

    @property
    def aboveThresholdBrushColour(self):
        """Returns selected colour name """
        value = None
        if self._appearancePanel:
            w = self._appearancePanel.getWidget(guiNameSpaces.WidgetVarName_AboveThrColour)
            if w:
                value = w.getText()
        return value

    @aboveThresholdBrushColour.setter
    def aboveThresholdBrushColour(self, colourName):
        if self._appearancePanel:
            w = self._appearancePanel.getWidget(guiNameSpaces.WidgetVarName_AboveThrColour)
            if w:
                w.select(colourName)

    @property
    def belowThresholdBrushColour(self):
        """Returns selected colour name"""
        value = None
        if self._appearancePanel:
            w = self._appearancePanel.getWidget(guiNameSpaces.WidgetVarName_BelowThrColour)
            if w:
                value = w.getText()
        return value

    @belowThresholdBrushColour.setter
    def belowThresholdBrushColour(self, colourName):
        if self._appearancePanel:
            w = self._appearancePanel.getWidget(guiNameSpaces.WidgetVarName_BelowThrColour)
            if w:
                w.select(colourName)
    @property
    def untraceableBrushColour(self):
        """Returns selected colour name"""
        value = None
        if self._appearancePanel:
            w = self._appearancePanel.getWidget(guiNameSpaces.WidgetVarName_UntraceableColour)
            if w:
                value = w.getText()
        return value

    @untraceableBrushColour.setter
    def untraceableBrushColour(self, colourName):
        if self._appearancePanel:
            w = self._appearancePanel.getWidget(guiNameSpaces.WidgetVarName_UntraceableColour)
            if w:
                w.select(colourName)
    @property
    def thresholdBrushColour(self):
        """Returns selected colour name"""
        value = None
        if self._appearancePanel:
            w = self._appearancePanel.getWidget(guiNameSpaces.WidgetVarName_ThrColour)
            if w:
                value = w.getText()
        return value

    @thresholdBrushColour.setter
    def thresholdBrushColour(self, colourName):
        if self._appearancePanel:
            w = self._appearancePanel.getWidget(guiNameSpaces.WidgetVarName_ThrColour)
            if w:
                w.select(colourName)

    def updatePanel(self, *args, **kwargs):
        getLogger().debug('Updating  barPlot panel')
        dataFrame = self.guiModule.getVisibleDataFrame(includeHiddenColumns=True)

        if dataFrame is None:
            self.barGraphWidget.clear()
            return

        if self.viewMode == guiNameSpaces.PlotViewMode_SecondaryStructure:
            chainWidget = self._appearancePanel.getWidget(guiNameSpaces.WidgetVarName_Chain)
            if chainWidget is not None:
                pid = chainWidget.getText()
                chain = self.project.getByPid(pid)
                dataFrame =  self.filterBySecondaryStructure(dataFrame, chain)
        self.plotDataFrame(dataFrame)


    def _updateThresholdValueFromSettings(self, value, *args):
        self.thresholdValue = value

    def filterBySecondaryStructure(self, dataFrame, chain):
        df = dataFrame
        backboneAtomsComb = ['H,N', 'Hn,Nh'] # hack while developing the feature. This has to be replaced with information from the MoleculeDefinitions
        codes = chain._sequenceCodesAsIntegers
        expandedSequenceResCodes = np.arange(min(codes), max(codes) + 1)  #make sure we have all residues codes ( chain can have gaps if altered by the users)
        filteredDf = pd.DataFrame()
        bbRows = []
        # filterDataFrame by the chain code first
        chainCode = chain.name
        df = df[df[seriesVariables.NMRCHAINNAME] == chainCode]
        for resCode in expandedSequenceResCodes:
            availableResiduesCodes = df[seriesVariables.NMRRESIDUECODE].values
            if not str(resCode) in availableResiduesCodes:
                filteredDf.loc[resCode, df.columns] = 0
                filteredDf.loc[resCode, seriesVariables.NMRRESIDUECODE] = str(resCode)
                filteredDf.loc[resCode, seriesVariables.NMRCHAINNAME] = chainCode
                continue
            nmrResiduesCodeDF = df[df[seriesVariables.NMRRESIDUECODE] == str(resCode)]
            # search for the BB atoms
            for ix, row in nmrResiduesCodeDF.iterrows():
                atomNames = row[seriesVariables.NMRATOMNAMES]
                if not isinstance(atomNames, str):
                    continue
                if atomNames in backboneAtomsComb:
                    bbRows.append(row)
                    filteredDf.loc[resCode, df.columns] = row.values
        filteredDf[sv.INDEX] = np.arange(1, len(filteredDf) + 1)
        return filteredDf


    def _setPlottingData(self, dataFrame, xColumnName, yColumnName):
        """Set the plotting variables from the current Dataframe.\
        """
        if not xColumnName in dataFrame:
            return False
        if not yColumnName in dataFrame:
            return False

        # set the index exactly in the same order as given (sorted by Gui Table)
        # dataFrame[sv.ASHTAG] = np.arange(1, len(dataFrame)+1)
        dataFrame.set_index(sv.INDEX, drop=False, inplace=True)

        ## group by threshold value
        aboveDf = dataFrame[dataFrame[yColumnName] >= self.thresholdValue]
        belowDf = dataFrame[dataFrame[yColumnName] < self.thresholdValue]
        untraceableDd = dataFrame[dataFrame[yColumnName].isnull()]
        _aboveXdf = aboveDf[xColumnName]
        self._aboveX = _aboveXdf.index
        self._aboveY = aboveDf[yColumnName]
        self._aboveObjects = [self.project.getByPid(x) for x in aboveDf[sv.COLLECTIONPID]]
        ## below threshold values
        _belowX = belowDf[xColumnName]
        self._belowX = _belowX.index
        self._belowY = belowDf[yColumnName]
        self._belowObjects = [self.project.getByPid(x) for x in belowDf[sv.COLLECTIONPID]]
        ## untraceable values
        _untraceableX = untraceableDd[xColumnName]
        self._untraceableX = _untraceableX.index
        self._untraceableY = [self.guiModule.backendHandler.untraceableValue] * len(untraceableDd[yColumnName])
        self._untraceableObjects = [self.project.getByPid(x) for x in untraceableDd[sv.COLLECTIONPID]]
        ## Brushes
        self._aboveBrush = colourNameToHexDict.get(self.aboveThresholdBrushColour, guiNameSpaces.BAR_aboveBrushHex)
        self._belowBrush = colourNameToHexDict.get(self.belowThresholdBrushColour, guiNameSpaces.BAR_belowBrushHex)
        self._untraceableBrush = colourNameToHexDict.get(self.untraceableBrushColour, guiNameSpaces.BAR_untracBrushHex)
        self._tresholdLineBrush = colourNameToHexDict.get(self.thresholdBrushColour, guiNameSpaces.BAR_thresholdLineHex)
        self._gradientbrushes = colorSchemeTable.get(self.aboveThresholdBrushColour, []) #in case there is one.
        index = dataFrame[xColumnName].index
        # get the errors
        errorColumn = f'{yColumnName}{sv._ERR}'
        if errorColumn in dataFrame.columns:
            xError = index
            yError = dataFrame[yColumnName].values
            topError = dataFrame[errorColumn].values
            self._errorHeights = {'xError': xError.values, 'yError': yError, 'topError': topError}
        ## set ticks for the xAxis. As they Xs are strs, Need to create a dict Index:Value
        labels = dataFrame[xColumnName].values
        coordinates = dataFrame[xColumnName].index
        self._setTicks(labels, coordinates)
        ## update labels on axes
        self._updateAxisLabels()
        self._plottedDf = dataFrame
        return True

    def _setTicks(self, labels, coordinates):
        """
        :param labels: list or 1d array of strings.  the values to be shown on the x-axis of the plot
        :param coordinates:  list or 1d array of int or floats.  the coordinates where to place the labels
        :return:
        """
        ticks = dict(zip(coordinates, labels))
        xaxis = self._getAxis('bottom')
        if self.barGraphWidget._tickOption == MinimalTicks:
            # setTicks uses a list of 3 dicts. Major, minor, sub minors ticks. (used for when zooming in-out)
            xaxis.setTicks([list(ticks.items())[9::10],  # define steps of 10, show only 10 labels (max zoomed out)
                            list(ticks.items())[4::5],  # steps of 5
                            list(ticks.items())[::1]])  # steps of 1, show all labels
        else:
            ## setTicks show all (equivalent to 1 for each Major, minor or sub minor
            xaxis.setTicks([list(ticks.items())[::1],
                            list(ticks.items())[::1],
                            list(ticks.items())[::1]])

    def _setCurrentObjs(self, df, ix):
        from ccpn.ui.gui.modules.experimentAnalysis.ExperimentAnalysisGuiModuleBC import getPeaksFromCollection
        if df is not None:
            pid = df.loc[ix, sv.COLLECTIONPID]
            collection = self.project.getByPid(pid)
            if self.current.collection != collection:
                peaks = getPeaksFromCollection(collection)
                self.current.peaks = peaks
                self.current.collection = collection

    def _mouseDoubleClickEvent(self, x, y):
        from ccpn.ui.gui.modules.experimentAnalysis.ExperimentAnalysisGuiModuleBC import _navigateToPeak
        self._setCurrentObjs(self._plottedDf, x)
        if len(self.current.peaks)>0:
            _navigateToPeak(self.guiModule, self.current.peaks[-1])

    def _mouseSingleClickEvent(self, x, y):
        self._setCurrentObjs(self._plottedDf, x)

    def _mouseHoverCallbackEvent(self, barIndex, x, y):
        if self._plottedDf is not None:
            posTxt = f'{y:.3f}'
            if barIndex is not None:
                pid = self._plottedDf.loc[barIndex, sv.COLLECTIONPID]
                barValue = self._plottedDf.loc[barIndex, self.yColumnName]
                if barValue:
                    barValue = f'{barValue:.3f}'
                    txt = f'{pid} -- {self.yColumnName}:{barValue} -- (Y:{posTxt})'
                    self.currentCollectionLabel.setText(txt)
            else:
                self.currentCollectionLabel.clear()

    def _updateAxisLabels(self):
        self.setXLabel(label=self.xColumnName)
        self.setYLabel(label=self.yColumnName)

    def fitYZoom(self):
        self.barGraphWidget.fitYZoom()

    def fitXZoom(self):
        self.barGraphWidget.fitXZoom()

    def plotDataFrame(self, dataFrame):
        """ Plot the given columns of dataframe as bars
         """
        self.barGraphWidget.clear()
        self._updateAxisLabels()
        self.barGraphWidget.hideButtons()

        if not self.xColumnName and not self.yColumnName in dataFrame.columns:
            getLogger().warning(f'Column names  not found in dataFrame: {self.xColumnName}, {self.yColumnName}')
            return

        success = self._setPlottingData(dataFrame, self.xColumnName, self.yColumnName)
        if not success:
            return
        self.barGraphWidget._lineMoved(aboveX=self._aboveX,
                                       belowX=self._belowX,
                                       disappearedX=self._untraceableX,
                                       ## Y
                                       aboveY=self._aboveY,
                                       belowY=self._belowY,
                                       disappearedY=self._untraceableY,
                                       ## errors
                                       errorHeight = self._errorHeights,
                                       ## Objects
                                       aboveObjects=self._aboveObjects,
                                       belowObjects=self._belowObjects,
                                       disappearedObjects=self._untraceableObjects,
                                       ## Brush
                                       aboveBrush=self._aboveBrush,
                                       aboveBrushes=self._gradientbrushes,
                                       belowBrush=self._belowBrush,
                                       disappearedBrush=self._untraceableBrush,
                                       )
        self.barGraphWidget.xLine.setPen(self._tresholdLineBrush)

        # movAv = dataFrame[self.yColumnName].rolling(window=7).mean()
        # self.rollingAverageLine = self.barGraphWidget.plotWidget.plotItem.plot(dataFrame.index.values, movAv.values)
        # self.scatters = self.barGraphWidget.plotWidget.plotItem.plot(dataFrame.index.values, dataFrame, symbol='o', brush=self._aboveBrush)

    def toggleErrorBars(self, setVisible=True):
        if self.barGraphWidget.errorBars:
            self.barGraphWidget.errorBars.setVisible(setVisible)

    def toggleBars(self, setVisible=True):
            self.barGraphWidget.setBarsVisible(setVisible)

    def _currentCollectionCallback(self, *args):
        # select collection on table.
        backendHandler = self.guiModule.backendHandler
        df = self._plottedDf
        if df is None:
            return
        pids = [co.pid for co in self.current.collections]
        filtered =  df[df[sv.COLLECTIONPID].isin(pids)]
        if filtered.empty:
            return
        barNumbers = filtered[sv.INDEX].values
        self.barGraphWidget._selectBarNumbers(selected=barNumbers)
