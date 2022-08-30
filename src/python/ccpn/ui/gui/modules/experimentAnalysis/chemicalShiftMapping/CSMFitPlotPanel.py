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
        self._selectCurrentCONotifier = Notifier(self.current, [Notifier.CURRENT], targetName='collections',
                                                 callback=self._currentCollectionCallback, onceOnly=True)
        self.labels = []

    def getPlottingData(self):
        pass

    def plotCurrentData(self, kd=None, bmax=None, *args):
        collections = self.current.collections
        dataFrame = self.guiModule.backendHandler.getLastOutputDataFrame()

        for collection in collections:
            filteredDf = dataFrame[dataFrame[sv.COLLECTIONPID] == collection.pid]
            seriesSteps = filteredDf[sv.SERIESSTEP].values
            seriesStepsValues = filteredDf[sv.SERIESSTEPVALUE].values
            seriesUnit = filteredDf[sv.SERIESUNIT].values[-1]
            peakPids = filteredDf[sv.PEAKPID].values
            objs = [self.project.getByPid(pid) for pid in peakPids]
            modelName = filteredDf[sv.MODEL_NAME].values[-1]
            model = self.guiModule.backendHandler.getFittingModelByName(modelName)
            if model is None: ## get it from settings
                model = self.guiModule.getCurrentFittingModel()
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
            self.currentCollectionLabel.setText(collection.pid)
            self.bindingPlot.fittingHandle.setPos(kd, bmax)

    def _replot(self, *args, **kwargs):
        pos = kwargs.get('pos', [])
        kd = None
        bmax = None
        if pos and len(pos) > 0:
            kd = pos[0]
            bmax = pos[1]
        collections = self.current.collections
        dataFrame = self.guiModule.backendHandler.getLastOutputDataFrame()
        if len(collections)== 0:
            return
        collection = collections[-1]
        filteredDf = dataFrame[dataFrame[sv.COLLECTIONPID] == collection.pid]
        seriesSteps = filteredDf[sv.SERIESSTEP].values
        modelName = filteredDf[sv.MODEL_NAME].values[-1]
        model = self.guiModule.backendHandler.getFittingModelByName(modelName)
        if model is None:  ## get it from settings
            model = self.guiModule.getCurrentFittingModel()
        func = model.getFittingFunc(model)
        if kd is None:
            kd = filteredDf[sv.KD].values[0]
        if bmax is None:
            bmax = filteredDf[sv.BMAX].values[0]
        extra = percentage(50, max(seriesSteps))
        initialPoint = min(seriesSteps)
        finalPoint = max(seriesSteps) + extra
        xf = np.linspace(initialPoint, finalPoint, 3000)
        yf = func(xf, kd, bmax)
        if self.fittedCurve is not None:
            self.bindingPlot.removeItem(self.fittedCurve)
        self.fittedCurve = self.bindingPlot.plot(xf, yf, pen=self.bindingPlot.gridPen)
        # self.bindingPlot.zoomFull()
        label = f'Kd: {round(kd,2)} \nbmax: {round(bmax,2)}'
        self.bindingPlot.crossHair.hLine.label.setText(label)

    def _currentCollectionCallback(self, *args):
        getLogger().info('Selected Current. Callback in FitPlot')
        self.plotCurrentData()

    def close(self):
        self._selectCurrentCONotifier.unRegister()




