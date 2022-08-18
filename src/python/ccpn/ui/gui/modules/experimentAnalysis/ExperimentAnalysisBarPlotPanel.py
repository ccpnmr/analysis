#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (https://www.ccpn.ac.uk) 2014 - 2022"
__credits__ = ("Ed Brooksbank, Joanna Fox, Victoria A Higman, Luca Mureddu, Eliza Płoskoń",
               "Timothy J Ragan, Brian O Smith, Gary S Thompson & Geerten W Vuister")
__licence__ = ("CCPN licence. See https://ccpn.ac.uk/software/licensing/")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Luca Mureddu $"
__dateModified__ = "$dateModified: 2022-08-18 18:08:36 +0100 (Thu, August 18, 2022) $"
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
import ccpn.ui.gui.modules.experimentAnalysis.ExperimentAnalysisGuiNamespaces as guiNameSpaces
import ccpn.framework.lib.experimentAnalysis.SeriesAnalysisVariables as sv
from PyQt5 import QtCore, QtWidgets, QtGui
from ccpn.util.Logging import getLogger
from ccpn.ui.gui.modules.experimentAnalysis.ExperimentAnalysisFitPlotPanel import ExperimentAnalysisPlotToolBar
from ccpn.ui.gui.widgets.BarGraphWidget import BarGraphWidget
from ccpn.ui.gui.guiSettings import CCPNGLWIDGET_HEXBACKGROUND, MEDIUM_BLUE, GUISTRIP_PIVOT, CCPNGLWIDGET_HIGHLIGHT, CCPNGLWIDGET_GRID, CCPNGLWIDGET_LABELLING
from ccpn.ui.gui.guiSettings import COLOUR_SCHEMES, getColours, DIVIDER
from ccpn.util.Colour import spectrumColours, hexToRgb, rgbaRatioToHex, _getRandomColours, getGradientBrushByArray, colourNameToHexDict
from ccpn.ui.gui.widgets.Font import Font, getFont
from ccpn.ui.gui.modules.experimentAnalysis.ExperimentAnalysisGuiPanel import GuiPanel
from ccpn.util.Colour import colorSchemeTable

class BarPlotPanel(GuiPanel):

    position = 3
    panelName = 'BarPlotPanel'

    def __init__(self, guiModule, *args, **Framekwargs):
        GuiPanel.__init__(self, guiModule,*args , **Framekwargs)
        self._appearancePanel = self.guiModule.settingsPanelHandler.getTab(guiNameSpaces.Label_GeneralAppearance)
        self._toolbarPanel = self.guiModule.panelHandler.getToolBarPanel()
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
                                             threshouldLine=0.1, grid=(1,0))
        self.barGraphWidget.showThresholdLine(True)
        self.barGraphWidget.xLine.sigPositionChangeFinished.connect(self._thresholdLineMoved)
        self._setBarGraphWidget()
        self.toolbar = ExperimentAnalysisPlotToolBar(parent=self, plotItem=self.barGraphWidget,
                                                     grid=(0, 0), gridSpan=(1, 2), hAlign='l', hPolicy='preferred')

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
            # convert the GuiValue to the CoreColumn name
            dd = guiNameSpaces.getReverseGuiNameMapping()
            value = dd.get(value, value)
        return value

    @property
    def yColumnName(self):
        """Returns selected y Column name """
        value = None
        if self._appearancePanel:
            w = self._appearancePanel.getWidget(guiNameSpaces.WidgetVarName_BarGraphYcolumnName)
            if w:
                value = w.getText()
            # convert the GuiValue to the CoreColumn name
            dd = guiNameSpaces.getReverseGuiNameMapping()
            value = dd.get(value, value)
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
        dataFrame = self.guiModule.backendHandler._getGuiOutputDataFrame()
        if dataFrame is not None:
            self.plotDataFrame(dataFrame)
        else:
            self.barGraphWidget.clear()

    def _updateThresholdValueFromSettings(self, value, *args):
        self.thresholdValue = value

    def _setPlottingData(self, dataFrame, xColumnName, yColumnName):
        """Set the plotting variables from the current Dataframe.\
        """
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
        ## setTicks uses a list of 3 dicts. Major, minor, sub minors ticks. (used for when zooming in-out)
        xaxis.setTicks([list(ticks.items())[9::10], # define steps of 10, show only 10 labels (max zoomed out)
                        list(ticks.items())[4::5],  # steps of 5
                        list(ticks.items())[::1]]) # steps of 1, show all labels
        ## update labels on axes
        self._updateAxisLabels()

    def _updateAxisLabels(self):
        dd = guiNameSpaces.getGuiNameMapping()
        self.setXLabel(label=dd.get(self.xColumnName))
        self.setYLabel(label=dd.get(self.yColumnName))

    def plotDataFrame(self, dataFrame):
        """ Plot the given columns of dataframe as bars
         """
        getLogger().warning('Alpha version of plotting')
        self.barGraphWidget.clear()
        if not self.xColumnName and not self.yColumnName in dataFrame.columns:
            getLogger().warning(f'Column names  not found in dataFrame: {self.xColumnName}, {self.yColumnName}')
            return

        self._setPlottingData(dataFrame, self.xColumnName, self.yColumnName)
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
