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
__dateModified__ = "$dateModified: 2022-08-09 15:59:57 +0100 (Tue, August 09, 2022) $"
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
from ccpn.framework.lib.experimentAnalysis.CSMFittingModels import ChemicalShiftCalculationModels
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
        self._selectCurrentCONotifier = Notifier(self.current, [Notifier.CURRENT], targetName='collections',
                                                 callback=self._currentCollectionCallback, onceOnly=True)

    def getPlottingData(self):
        pass

    def _currentCollectionCallback(self, *args):
        getLogger().info('Selected Current. Callback in FitPlot')
        collections = self.current.collections
        dataFrame = self.guiModule.backendHandler.getFirstOutputDataFrame()

        for collection in collections:
            filteredDf = dataFrame[dataFrame[sv.COLLECTIONPID] == collection.pid]
            seriesSteps = filteredDf[sv.SERIESSTEP].values
            seriesStepsValues = filteredDf[sv.SERIESSTEPVALUE].values
            seriesUnit = filteredDf[sv.SERIESUNIT].values[-1]
            peakPids = filteredDf[sv.PEAKPID].values
            objs = [self.project.getByPid(pid) for pid in peakPids]
            modelName = filteredDf[sv.MODEL_NAME].values[-1]
            model = ChemicalShiftCalculationModels.get(modelName)
            if model is None: ## get it from settings
                model = self.guiModule.getCurrentFittingModel()
            func = model.getFittingFunc(model)
            kd = filteredDf[sv.KD].values[0]
            bmax = filteredDf[sv.BMAX].values[0]
            xf = np.linspace(min(seriesSteps), max(seriesSteps), 1000)
            yf = func(xf, kd, bmax)
            self.bindingPlot.clear()
            self.bindingPlot.plot(xf, yf)
            self.setXLabel(label=seriesUnit)
            spots = []
            for obj, x, y in zip(objs, seriesSteps, seriesStepsValues):
                dd = {'pos': [0, 0], 'data': 'obj', 'brush': pg.mkBrush(255, 0, 0), 'symbol': 'o', 'size': 10, 'pen': None}  # red default
                dd['pos'] = [x,y]
                dd['data'] = obj
                if hasattr(obj.spectrum, 'positiveContourColour'):  # colour from the spectrum. The only CCPN obj implemeted so far
                    dd['brush'] = pg.functions.mkBrush(hexToRgb(obj.spectrum.positiveContourColour))
                spots.append(dd)

            scatter = pg.ScatterPlotItem(spots)
            self.bindingPlot.addItem(scatter)


    def plotCurve(self, xs, ys):
        self.bindingPlot.clear()
        self.bindingPlot.plot(xs, ys)

    def clearData(self):
        pass
        #to do when cleaning input data and avoid wrongly displayed curves

    def close(self):
        self._selectCurrentCONotifier.unRegister()




