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
__dateModified__ = "$dateModified: 2022-06-27 13:23:36 +0100 (Mon, June 27, 2022) $"
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
from ccpn.util.Colour import spectrumColours, hexToRgb, rgbaRatioToHex, _getRandomColours
from ccpn.ui.gui.widgets.Font import Font, getFont
from ccpn.ui.gui.modules.experimentAnalysis.ExperimentAnalysisGuiPanel import GuiPanel
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


    def plotDataFrame(self, dataFrame):
        """ DEMO """
        getLogger().warning('DEMO version of plotting')
        xs = []
        ys = []
        obs = []
        self.disappearedX = []
        self.disappearedY = []
        self.disappereadObjects = []
        self.aboveX = [int(x) for x in dataFrame[sv.RESIDUE_CODE]]
        self.aboveY = dataFrame[sv.DELTA_DELTA_MEAN]
        self.aboveObjects = [self.project.getByPid(x) for x in dataFrame[sv._ROW_UID]]
        self.belowX = []
        self.belowY = []
        self.belowObjects = []
        self.aboveBrush = 'g'
        self.belowBrush = 'r'
        self.disappearedPeakBrush = 'b'

        self.barGraphWidget.clear()
        self.barGraphWidget._lineMoved(aboveX=self.aboveX,
                                       aboveY=self.aboveY,
                                       aboveObjects=self.aboveObjects,
                                       belowX=self.belowX,
                                       belowY=self.belowY,
                                       belowObjects=self.belowObjects,
                                       belowBrush=self.belowBrush,
                                       aboveBrush=self.aboveBrush,
                                       disappearedX=self.disappearedX,
                                       disappearedY=self.disappearedY,
                                       disappearedObjects=self.disappereadObjects,
                                       disappearedBrush=self.disappearedPeakBrush,
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
