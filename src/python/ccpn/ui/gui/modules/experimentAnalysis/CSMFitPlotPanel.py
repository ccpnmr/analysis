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
__dateModified__ = "$dateModified: 2022-07-02 11:31:31 +0100 (Sat, July 02, 2022) $"
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
from PyQt5 import QtCore, QtWidgets, QtGui
from ccpn.ui.gui.guiSettings import CCPNGLWIDGET_HEXBACKGROUND, MEDIUM_BLUE, GUISTRIP_PIVOT, CCPNGLWIDGET_HIGHLIGHT, CCPNGLWIDGET_GRID, CCPNGLWIDGET_LABELLING
from ccpn.ui.gui.guiSettings import COLOUR_SCHEMES, getColours, DIVIDER
from ccpn.util.Colour import spectrumColours, hexToRgb, rgbaRatioToHex, _getRandomColours
from ccpn.ui.gui.widgets.Font import Font, getFont
from ccpn.ui.gui.modules.experimentAnalysis.ExperimentAnalysisGuiPanel import GuiPanel
from ccpn.ui.gui.modules.experimentAnalysis.ExperimentAnalysisFitPlotPanel import FitPlotPanel
import numpy as np
import ccpn.framework.lib.experimentAnalysis.fitFunctionsLib as lf

import ccpn.ui.gui.modules.experimentAnalysis.ExperimentAnalysisGuiNamespaces as guiNameSpaces
from ccpn.ui.gui.modules.experimentAnalysis.ExperimentAnalysisBarPlotPanel import BarPlotPanel
import ccpn.framework.lib.experimentAnalysis.SeriesAnalysisVariables as sv
from ccpn.util.Logging import getLogger
from ccpn.core.lib.Notifiers import Notifier


class CSMFitPlotPanel(FitPlotPanel):

    position = 2
    panelName = guiNameSpaces.CSMFittingPlotPanel

    def __init__(self, guiModule, *args, **Framekwargs):
        FitPlotPanel.__init__(self, guiModule, *args , **Framekwargs)
        self.setXLabel(label='X')
        self.setYLabel(label=guiNameSpaces.RelativeDisplacement)
        # self._selectCurrentNRNotifier = Notifier(self.current, [Notifier.CURRENT], targetName='nmrResidues',
        #                                          callback=self._selectCurrentNmrResiduesNotifierCallback, onceOnly=True)

    def _selectCurrentNmrResiduesNotifierCallback(self, *args):
        getLogger().info('Selected Current. Callback in FitPlot')
        nmrResidues = self.current.nmrResidues
        dataTables = self.guiModule.outputDataTables
        df = None
        if len(dataTables)>0:
            df = dataTables[0].data
        if df is None:
            return
        if len(nmrResidues) > 0:
            self.setXLabel(label=df.SERIESUNITS)
            # get nmrRes form module data or table selection
            # only first as demo
            pid = nmrResidues[0].pid
            selectedDf = df[df[sv._ROW_UID]==pid]
            func = lf.oneSiteBinding_func

            kd = selectedDf[sv.KD].values[0]
            bmax = selectedDf[sv.BMAX].values[0]

            xf = np.linspace(min(df.SERIESSTEPS), max(df.SERIESSTEPS), 1000)
            yf = func(xf, kd, bmax)
            self.plotCurve(xf, yf)

    def plotCurve(self, xs, ys):
        self.bindingPlot.clear()
        self.bindingPlot.plot(xs, ys)

    def clearData(self):
        pass
        #to do when cleaning input data and avoid wrongly displayed curves






