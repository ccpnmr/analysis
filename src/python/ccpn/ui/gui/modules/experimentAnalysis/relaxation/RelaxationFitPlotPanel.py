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
from PyQt5 import QtCore, QtWidgets, QtGui
from ccpn.ui.gui.modules.experimentAnalysis.ExperimentAnalysisFitPlotPanel import FitPlotPanel, _CustomLabel
import numpy as np
import ccpn.ui.gui.modules.experimentAnalysis.ExperimentAnalysisGuiNamespaces as guiNameSpaces
import ccpn.framework.lib.experimentAnalysis.SeriesAnalysisVariables as sv
from ccpn.util.Logging import getLogger
from ccpn.util.Common import percentage
from ccpn.util.Colour import hexToRgb, colourNameToHexDict

class RelaxationFitPlotPanel(FitPlotPanel):

    panelName = guiNameSpaces.RelaxationFittingPlotPanel

    def __init__(self, guiModule, *args, **Framekwargs):
        FitPlotPanel.__init__(self, guiModule, *args , **Framekwargs)
        self.setXLabel(label='X')
        self.setYLabel(label='Height') #hardcoded get it from the fittingModel

        self.labels = []

    def getPlottingData(self):
        pass

    def plotCurrentData(self, decay=None, amplitude=None, *args):
        """
        #Todo. check current collections are in the collections used to create the outputDataTable.
        :param decay:
        :param amplitude:
        :param args:
        :return:
        """
        collections = self.current.collections
        outputData = self.guiModule.getSelectedOutputDataTable()
        if outputData is None:
            return
        dataFrame = outputData.data

        for collection in collections:
            filteredDf = dataFrame[dataFrame[sv.COLLECTIONPID] == collection.pid]
            modelName = filteredDf[sv.MODEL_NAME].values[-1]
            model = self.guiModule.backendHandler.getFittingModelByName(modelName)
            if model is None: ## get it from settings
                model = self.guiModule.backendHandler.currentFittingModel

            seriesSteps = filteredDf[sv.SERIESSTEP].values
            seriesStepsValues = filteredDf[model.PeakProperty].values #could add option to normalise
            seriesUnit = filteredDf[sv.SERIESUNIT].values[-1]
            peakPids = filteredDf[sv.PEAKPID].values
            objs = [self.project.getByPid(pid) for pid in peakPids]

            # seriesStepsValues = model.Minimiser()._scaleMinMaxData(seriesStepsValues)
            yArray = seriesStepsValues
            func = model.getFittingFunc(model)
            try: #todo need to change this to don't be hardcoded for sv.DECAY-AMPLITUDE but take it from the model.
                if decay is None:
                    decay = float(filteredDf[sv.DECAY].values[0])
                if amplitude is None:
                    amplitude = float(filteredDf[sv.AMPLITUDE].values[0])
                extra = percentage(50, max(seriesSteps))
                initialPoint = min(seriesSteps)
                finalPoint = max(seriesSteps)+extra
                xf = np.linspace(initialPoint, finalPoint, 3000)
                yf = func(xf, decay, amplitude)
                self.currentCollectionLabel.setText('')
                self.bindingPlot.clear()
                self.fittedCurve = self.bindingPlot.plot(xf, yf,  pen=self.bindingPlot.gridPen)
                self.setXLabel(label=seriesUnit)
                spots = []
                for obj, x, y in zip(objs, seriesSteps, yArray):
                    brush = pg.mkBrush(255, 0, 0)
                    dd = {'pos': [0, 0], 'data': 'obj', 'brush': pg.mkBrush(255, 0, 0), 'symbol': 'o', 'size': 10, 'pen': None}  # red default
                    dd['pos'] = [x,y]
                    dd['data'] = obj
                    excludedBrush = None
                    if hasattr(obj.spectrum, 'positiveContourColour'):  # colour from the spectrum. The only CCPN obj implemeted so far
                        brush = pg.functions.mkBrush(hexToRgb(obj.spectrum.positiveContourColour))
                        # if obj.pid in self.guiModule.backendHandler.exclusionHandler.peaks:
                        #     grey = colourNameToHexDict.get('grey', '#808080')
                        #     excludedBrush = brush = pg.functions.mkBrush(hexToRgb('#808080'))
                        dd['brush'] = brush
                    spots.append(dd)
                    label = _CustomLabel(obj=obj, brush=excludedBrush, textProperty='id')
                    self.bindingPlot.addItem(label)
                    label.setPos(x,y)
                    self.labels.append(label)

                scatter = pg.ScatterPlotItem(spots)
                self.bindingPlot.addItem(scatter)
                self.bindingPlot.scene().sigMouseMoved.connect(self.bindingPlot.mouseMoved)
                self.bindingPlot.zoomFull()
                self.currentCollectionLabel.setText(collection.pid)
                self.bindingPlot.fittingHandle.setPos(decay, amplitude)
            except Exception as error:
                getLogger().warning(f'Error plotting: {error}')

    def _replot(self, *args, **kwargs):
        pos = kwargs.get('pos', [])
        decay = None
        amplitude = None
        if pos and len(pos) > 0:
            decay = pos[0]
            amplitude = pos[1]
        collections = self.current.collections
        outputData = self.guiModule.getSelectedOutputDataTable()
        if outputData is None:
            return
        dataFrame = outputData.data
        if len(collections)== 0:
            return
        collection = collections[-1]
        filteredDf = dataFrame[dataFrame[sv.COLLECTIONPID] == collection.pid]
        seriesSteps = filteredDf[sv.SERIESSTEP].values
        modelName = filteredDf[sv.MODEL_NAME].values[-1]
        model = self.guiModule.backendHandler.getFittingModelByName(modelName)
        if model is None:  ## get it from settings
            model = self.guiModule.backendHandler.currentFittingModel
        func = model.getFittingFunc(model)
        try:  # todo need to change this to don't be hardcoded for sv.DECAY-AMPLITUDE but take it from the model.
            if decay is None:
                decay = filteredDf[sv.DECAY].values[0]
            if amplitude is None:
                amplitude = filteredDf[sv.AMPLITUDE].values[0]
            extra = percentage(50, max(seriesSteps))
            initialPoint = min(seriesSteps)
            finalPoint = max(seriesSteps) + extra
            xf = np.linspace(initialPoint, finalPoint, 3000)
            yf = func(xf, decay, amplitude)
            if self.fittedCurve is not None:
                self.bindingPlot.removeItem(self.fittedCurve)
            self.fittedCurve = self.bindingPlot.plot(xf, yf, pen=self.bindingPlot.gridPen)
            # self.bindingPlot.zoomFull()
            label = f'decay: {round(decay,2)} \namplitude: {round(amplitude,2)}'
            self.bindingPlot.crossHair.hLine.label.setText(label)
        except Exception as error:
            getLogger().warning(f'Error plotting: {error}')
