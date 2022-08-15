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
__dateModified__ = "$dateModified: 2022-08-15 19:08:15 +0100 (Mon, August 15, 2022) $"
__version__ = "$Revision: 3.1.0 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Luca Mureddu $"
__date__ = "$Date: 2022-05-20 12:59:02 +0100 (Fri, May 20, 2022) $"
#=========================================================================================
# Start of code
#=========================================================================================

import numpy as np
from ccpn.ui.gui.widgets.BarGraphWidget import BarGraphWidget
import pyqtgraph as pg
from PyQt5 import QtCore, QtWidgets, QtGui
from ccpn.ui.gui.guiSettings import CCPNGLWIDGET_HEXBACKGROUND, MEDIUM_BLUE, GUISTRIP_PIVOT, CCPNGLWIDGET_HIGHLIGHT, CCPNGLWIDGET_GRID, CCPNGLWIDGET_LABELLING
from ccpn.ui.gui.guiSettings import COLOUR_SCHEMES, getColours, DIVIDER
from ccpn.util.Colour import spectrumColours, hexToRgb, rgbaRatioToHex, _getRandomColours, getGradientBrushByArray, colourNameToHexDict
from ccpn.ui.gui.widgets.Font import Font, getFont
from ccpn.ui.gui.modules.experimentAnalysis.ExperimentAnalysisGuiPanel import GuiPanel
from ccpn.util.Colour import colorSchemeTable
import ccpn.ui.gui.modules.experimentAnalysis.ExperimentAnalysisGuiNamespaces as guiNameSpaces
from ccpn.ui.gui.modules.experimentAnalysis.ExperimentAnalysisBarPlotPanel import BarPlotPanel
import ccpn.framework.lib.experimentAnalysis.SeriesAnalysisVariables as sv
from ccpn.util.Logging import getLogger
from ccpn.core.lib.Notifiers import Notifier

class CSMBarPlotPanel(BarPlotPanel):

    position = 3
    panelName = guiNameSpaces.CSMBarPlotPanel

    def __init__(self, guiModule, *args, **Framekwargs):
        BarPlotPanel.__init__(self, guiModule, *args , **Framekwargs)

        # self._selectCurrentNRNotifier = Notifier(self.current, [Notifier.CURRENT], targetName='nmrResidues',
        #                                          callback=self._selectCurrentNmrResiduesNotifierCallback, onceOnly=True)

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


    def updatePanel(self, *args, **kwargs):
        getLogger().info('Updating CSM barPlot panel')
        dataFrame = self.guiModule.backendHandler._getGuiOutputDataFrame()
        if dataFrame is not None:
            self.plotDataFrame(dataFrame)
        else:
            self.barGraphWidget.clear()

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
        getLogger().warning('DEMO version of plotting')
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
        self._setBarGraphZoomFromData(dataFrame)


    def _setBarGraphZoomFromData(self, dataFrame):
        """ Set the zoom without  considering the untraceable values"""
        pass
        # ydata = dataFrame[yColumnName]
        # xdata = [int(i) for i in dataFrame[xColumnName]]
        # self.barGraphWidget.setXRange(np.min(xdata), np.max(xdata))
        # self.barGraphWidget.setYRange(ydata.min(), ydata.max())

    def _selectCurrentNmrResiduesNotifierCallback(self, *args):
        getLogger().info('Selected Current. Callback in BarPlot')
        nmrResidues = self.current.nmrResidues
        if len(nmrResidues) > 0:
            pss = [str(nmrResidue.sequenceCode) for nmrResidue in nmrResidues]
            self._selectBarLabels(pss)

    def _selectBarLabels(self, values):
        """
        Double check this routine for leakage.
        :param values:
        :return:
        """
        for bar in self.barGraphWidget.barGraphs:
            for label in bar.labels:
                if label.text() in values:
                    label.setSelected(True)
                    label.setBrush(self.selectedLabelPen)
                    label.setVisible(True)
                else:
                    label.setSelected(False)
                    label.setBrush(QtGui.QColor(bar.brush))
                    if label.isBelowThreshold and not self.barGraphWidget.customViewBox.allLabelsShown:
                        label.setVisible(False)
