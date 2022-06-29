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
__dateModified__ = "$dateModified: 2022-06-29 11:57:44 +0100 (Wed, June 29, 2022) $"
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
        self.setXLabel(label=guiNameSpaces.ColumnResidueCode)
        self.setYLabel(label=guiNameSpaces.ColumnDdelta)
        self._selectCurrentNRNotifier = Notifier(self.current, [Notifier.CURRENT], targetName='nmrResidues',
                                                 callback=self._selectCurrentNmrResiduesNotifierCallback, onceOnly=True)

        self._defaultAboveThresholdBrushColour  = '#1020aa' # dark blue
        self._defaultBelowThresholdBrushColour  = '#b0b0b0' # light grey
        self._defaultDisappearedBrushColour     = '#000000'  # black

        # self._updateButton = self._toolbarPanel.getButton(guiNameSpaces.UpdateButton)
        # self._updateButton.clicked.connect(self.updatePanel)

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

    def updatePanel(self, *args, **kwargs):
        getLogger().info('Updating CSM barPlot panel')
        dataFrame = self.guiModule.backendHandler.getOutputDataFrame()
        self.plotDataFrame(dataFrame)

    def plotDataFrame(self, dataFrame, xColumnName=sv.RESIDUE_CODE, yColumnName=sv.DELTA_DELTA_MEAN):
        """ Plot the given columns of dataframe as bars """
        getLogger().warning('DEMO version of plotting')
        self.barGraphWidget.clear()
        ## group by threshold value
        aboveDf = dataFrame[dataFrame[yColumnName] >= self.thresholdValue]
        belowDf = dataFrame[dataFrame[yColumnName] < self.thresholdValue]
        self.aboveX = [int(i) for i in aboveDf[xColumnName]]
        self.aboveY = aboveDf[yColumnName]
        self.aboveObjects = [self.project.getByPid(x) for x in aboveDf[sv._ROW_UID]]
        ## below threshold values
        self.belowX = [int(i) for i in belowDf[xColumnName]]
        self.belowY = belowDf[yColumnName]
        self.belowObjects = [self.project.getByPid(x) for x in belowDf[sv._ROW_UID]]

        # TODO disappeared and excluded filter
        self.disappearedX = []
        self.disappearedY = []
        self.disappereadObjects = []
        self.disappearedPeakBrush = ''

        aboveBrush = colourNameToHexDict.get(self.aboveThresholdBrushColour, self._defaultAboveThresholdBrushColour)
        belowBrush = colourNameToHexDict.get(self.belowThresholdBrushColour, self._defaultBelowThresholdBrushColour)
        disappearedBrush = colourNameToHexDict.get(self.disappearedPeakBrush, self._defaultDisappearedBrushColour)

        gradientName = self.aboveThresholdBrushColour
        brushes = colorSchemeTable.get(gradientName, [])

        self.barGraphWidget._lineMoved(aboveX=self.aboveX,
                                       belowX=self.belowX,
                                       disappearedX=self.disappearedX,
                                       ## Y
                                       aboveY=self.aboveY,
                                       belowY=self.belowY,
                                       disappearedY=self.disappearedY,
                                       ## Objects
                                       aboveObjects=self.aboveObjects,
                                       belowObjects=self.belowObjects,
                                       disappearedObjects=self.disappereadObjects,
                                       ## Brush
                                       aboveBrush=aboveBrush,
                                       aboveBrushes=brushes,
                                       belowBrush=belowBrush,
                                       disappearedBrush=disappearedBrush,
                                       )

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
