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
__dateModified__ = "$dateModified: 2022-10-12 15:27:11 +0100 (Wed, October 12, 2022) $"
__version__ = "$Revision: 3.1.0 $"
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
import ccpn.framework.lib.experimentAnalysis.SeriesAnalysisVariables as sv
import ccpn.ui.gui.modules.experimentAnalysis.ExperimentAnalysisGuiNamespaces as guiNameSpaces
from ccpn.util.Colour import colorSchemeTable, hexToRgb, rgbaRatioToHex, colourNameToHexDict
from ccpn.ui.gui.modules.experimentAnalysis.ExperimentAnalysisGuiPanel import GuiPanel
from ccpn.ui.gui.modules.experimentAnalysis.ExperimentAnalysisFitPlotPanel import ExperimentAnalysisPlotToolBar
from ccpn.ui.gui.widgets.BarGraphWidget import BarGraphWidget
from ccpn.ui.gui.guiSettings import CCPNGLWIDGET_HEXBACKGROUND, GUISTRIP_PIVOT, CCPNGLWIDGET_HIGHLIGHT, CCPNGLWIDGET_LABELLING
from ccpn.ui.gui.guiSettings import getColours, DIVIDER
from ccpn.ui.gui.widgets.Font import getFont
from ccpn.ui.gui.widgets.Label import Label

class BarPlotPanel(GuiPanel):

    position = 3
    panelName = 'BarPlotPanel'

    def __init__(self, guiModule, *args, **Framekwargs):
        GuiPanel.__init__(self, guiModule,*args , **Framekwargs)
        self._appearancePanel = self.guiModule.settingsPanelHandler.getTab(guiNameSpaces.Label_GeneralAppearance)
        self._toolbarPanel = self.guiModule.panelHandler.getToolBarPanel()
        self._plottedDf = None
        self._aboveX = []
        self._belowX = []
        self._untraceableX = []
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
                                             threshouldLine=0.1, grid=(1,0), gridSpan=(1, 2))
        self.barGraphWidget.showThresholdLine(True)
        self.barGraphWidget.xLine.sigPositionChangeFinished.connect(self._thresholdLineMoved)
        self._setBarGraphWidget()
        self.toolbar = ExperimentAnalysisPlotToolBar(parent=self, plotItem=self.barGraphWidget,
                                                     grid=(0, 0), gridSpan=(1, 2), hAlign='l', hPolicy='preferred')
        self.currentCollectionLabel = Label(self, text='', grid=(0, 1), hAlign='r',)

    def setXLabel(self, label=''):
        self.barGraphWidget.plotWidget.setLabel('bottom', label)

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
        getLogger().info('Updating  barPlot panel')
        dataFrame = self.guiModule.getGuiOutputDataFrame()
        if dataFrame is not None:
            self.plotDataFrame(dataFrame)
        else:
            self.barGraphWidget.clear()

    def _updateThresholdValueFromSettings(self, value, *args):
        self.thresholdValue = value

    def _setPlottingData(self, dataFrame, xColumnName, yColumnName):
        """Set the plotting variables from the current Dataframe.\
        """
        if not xColumnName in dataFrame:
            return False
        if not yColumnName in dataFrame:
            return False
        # we need the index as seriesIds
        dataFrame.set_index(sv.ASHTAG, drop=False, inplace=True)
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
        ## set ticks for the xAxis. As they Xs are strs, Need to create a dict Index:Value
        ticks = dict(zip(dataFrame[xColumnName].index, dataFrame[xColumnName].values))
        xaxis = self._getAxis('bottom')
        ##TODO set as an option to use major-minor or show all
        # setTicks uses a list of 3 dicts. Major, minor, sub minors ticks. (used for when zooming in-out)
        xaxis.setTicks([list(ticks.items())[9::10], # define steps of 10, show only 10 labels (max zoomed out)
                        list(ticks.items())[4::5],  # steps of 5
                        list(ticks.items())[::1]]) # steps of 1, show all labels
        ## update labels on axes
        self._updateAxisLabels()
        self._plottedDf = dataFrame
        return True

    def _setCurrentObjs(self, df, ix):
        from ccpn.ui.gui.modules.experimentAnalysis.ExperimentAnalysisGuiModuleBC import getPeaksFromCollection
        if df is not None:
            pid = df.loc[ix, sv.COLLECTIONPID]
            collection = self.project.getByPid(pid)
            peaks = getPeaksFromCollection(collection)
            self.current.peaks = peaks
            self.current.collection = collection

    def _mouseDoubleClickEvent(self, x, y):
        from ccpn.ui.gui.modules.experimentAnalysis.ExperimentAnalysisGuiModuleBC import _navigateToPeak
        self._setCurrentObjs(self._plottedDf, x)
        _navigateToPeak(self.guiModule, self.current.peaks[-1])

    def _mouseSingleClickEvent(self, x, y):
        self._setCurrentObjs(self._plottedDf, x)

    def _mouseHoverCallbackEvent(self, barIndex, x, y):
        if self._plottedDf is not None:
            posTxt = f'Y:{y:.2f}'
            if barIndex is not None:
                pid = self._plottedDf.loc[barIndex, sv.COLLECTIONPID]
                txt = f'{pid} -- {posTxt}'
                self.currentCollectionLabel.setText(txt)
            else:
                self.currentCollectionLabel.clear()

    def _updateAxisLabels(self):
        self.setXLabel(label=self.xColumnName)
        self.setYLabel(label=self.yColumnName)

    def plotDataFrame(self, dataFrame):
        """ Plot the given columns of dataframe as bars
         """
        getLogger().warning('Alpha version of plotting')
        self.barGraphWidget.clear()
        self._updateAxisLabels()

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
