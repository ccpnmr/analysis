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
__modifiedBy__ = "$modifiedBy: Luca Mureddu $"
__dateModified__ = "$dateModified: 2022-10-18 11:20:52 +0100 (Tue, October 18, 2022) $"
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
from ccpn.util.Colour import spectrumColours, hexToRgb, rgbaRatioToHex, _getRandomColours
from ccpn.ui.gui.modules.experimentAnalysis.ExperimentAnalysisFitPlotPanel import FitPlotPanel, _CustomLabel
import numpy as np
import ccpn.ui.gui.modules.experimentAnalysis.ExperimentAnalysisGuiNamespaces as guiNameSpaces
import ccpn.framework.lib.experimentAnalysis.SeriesAnalysisVariables as sv
from ccpn.util.Logging import getLogger
from ccpn.core.lib.Notifiers import Notifier
from ccpn.util.Common import percentage

class CSMFitPlotPanel(FitPlotPanel):

    position = 2
    panelName = guiNameSpaces.CSMFittingPlotPanel

    def __init__(self, guiModule, *args, **Framekwargs):
        FitPlotPanel.__init__(self, guiModule, *args , **Framekwargs)
        self.setXLabel(label='X')
        self.setYLabel(label=guiNameSpaces.RelativeDisplacement)
        self.labels = []

    def getPlottingData(self):
        pass

    def plotCurrentData(self, kd=None, bmax=None, *args):

        collections = self.current.collections
        if not collections:
            self.clearData()
            return

        ## get the raw data from the output dataTable from the pids because contains more information
        outputData = self.guiModule.getSelectedOutputDataTable()
        if outputData is None:
            self.clearData()
            return
        ## Check if the current collection pids are in the Table.
        dataFrame = outputData.data
        pids = [co.pid for co in self.current.collections]
        filtered = dataFrame.getByHeader(sv.COLLECTIONPID, pids)
        if filtered.empty:
            self.clearData()
            return
        lastCollectionPid = filtered[sv.COLLECTIONPID].values[-1]
        ## plot only last selected
        filteredDf = dataFrame[dataFrame[sv.COLLECTIONPID] == lastCollectionPid]
        seriesSteps = filteredDf[sv.SERIESSTEP].values
        seriesStepsValues = filteredDf[sv.SERIESSTEPVALUE].values
        seriesUnits = filteredDf[sv.SERIESUNIT].values
        if len(seriesUnits)>0:
            seriesUnit = seriesUnits[0]
        else:
            seriesUnit = 'Series Unit Not Given'
        peakPids = filteredDf[sv.PEAKPID].values
        objs = [self.project.getByPid(pid) for pid in peakPids]
        modelNames = filteredDf[sv.MODEL_NAME].values
        if len(modelNames)>0:
            modelName = modelNames[0]
        else:
            modelName = None
        model = self.guiModule.backendHandler.getFittingModelByName(modelName)
        if model is None: ## get it from settings
            model = self.guiModule.backendHandler.currentFittingModel
        func = model.getFittingFunc(model)
        if kd is None:
            kd = filteredDf[sv.KD].values[0]
        if bmax is None:
            bmax = filteredDf[sv.BMAX].values[0]
        extra = percentage(50, max(seriesSteps))
        initialPoint = min(seriesSteps)
        finalPoint = max(seriesSteps)+extra
        xf = np.linspace(initialPoint, finalPoint, 3000)
        yf = func(xf, kd, bmax)
        self.currentCollectionLabel.setText('')
        self.bindingPlot.clear()
        self.fittedCurve = self.bindingPlot.plot(xf, yf,  pen=self.bindingPlot.gridPen)
        self.setXLabel(label=seriesUnit)
        spots = []
        for obj, x, y in zip(objs, seriesSteps, seriesStepsValues):
            brush = pg.mkBrush(255, 0, 0)
            dd = {'pos': [0, 0], 'data': 'obj', 'brush': pg.mkBrush(255, 0, 0), 'symbol': 'o', 'size': 10, 'pen': None}  # red default
            dd['pos'] = [x,y]
            dd['data'] = obj
            if obj is None:
                continue
            if hasattr(obj.spectrum, 'positiveContourColour'):  # colour from the spectrum. The only CCPN obj implemeted so far
                brush = pg.functions.mkBrush(hexToRgb(obj.spectrum.positiveContourColour))
                dd['brush'] = brush
            spots.append(dd)
            label = _CustomLabel(obj=obj, textProperty='id')
            self.bindingPlot.addItem(label)
            label.setPos(x,y)
            self.labels.append(label)

        scatter = pg.ScatterPlotItem(spots)
        self.bindingPlot.addItem(scatter)
        self.bindingPlot.scene().sigMouseMoved.connect(self.bindingPlot.mouseMoved)
        self.bindingPlot.zoomFull()
        labelText = f'{lastCollectionPid}'
        if len(self.current.collections) > 1:
            labelText += f' - (Last selected)'
        self.currentCollectionLabel.setText(labelText)
        # self.bindingPlot.fittingHandle.setPos(kd, bmax)

