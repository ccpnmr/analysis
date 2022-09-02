"""
This module defines base classes for Series Analysis
"""
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
__dateModified__ = "$dateModified: 2022-08-25 16:21:44 +0100 (Thu, August 25, 2022) $"
__version__ = "$Revision: 3.1.0 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Luca Mureddu $"
__date__ = "$Date: 2022-02-02 14:08:56 +0000 (Wed, February 02, 2022) $"
#=========================================================================================
# Start of code
#=========================================================================================

import pandas as pd
from ccpn.util.Logging import getLogger
import ccpn.framework.lib.experimentAnalysis.SeriesAnalysisVariables as sv
from ccpn.framework.lib.experimentAnalysis.SeriesAnalysisABC import SeriesAnalysisABC
from ccpn.framework.lib.experimentAnalysis.RelaxationModels import FittingModels, CalculationModels
from ccpn.framework.lib.experimentAnalysis.BlankModels import BlankFittingModel, BlankCalculationModel

class RelaxationAnalysisBC(SeriesAnalysisABC):
    """
    Relaxation Analysis Non-Gui module.
    """
    seriesAnalysisName = sv.RelaxationAnalysis
    _allowedPeakProperties = [sv._HEIGHT, sv._VOLUME]

    def __init__(self):
        super().__init__()
        self.fittingModels = self._registerModels([BlankFittingModel] + FittingModels)
        self.calculationModels = self._registerModels([BlankCalculationModel] + CalculationModels)
        fittingModel = self._getFirstModel(self.fittingModels)
        calculationModel = self._getFirstModel(self.calculationModels)
        if fittingModel:
            self._currentFittingModel = fittingModel()
        if calculationModel:
            self._currentCalculationModel = calculationModel()


    def fitInputData(self):
        """
        Perform calculation using the currentFittingModel and currentCalculationModel to the inputDataTables
        and save outputs to a single newDataTable.
        Resulting dataTables are available in the outputDataTables.
        :return: None. Creates a new output dataTable in outputDataTables
        """
        getLogger().warning(sv.UNDER_DEVELOPMENT_WARNING)

        if len(self.inputDataTables) == 0:
            getLogger().warning('Cannot run any fitting models. Add a valid inputData first')
            return

        inputFrame = self.inputDataTables[-1].data
        fittingFrame = self.currentFittingModel.fitSeries(inputFrame)
        calculationFrame = self.currentCalculationModel.calculateValues(inputFrame)
        # merge the frames on CollectionPid/id, Assignment, model-results/statistics and calculation
        cdf = calculationFrame[[sv.COLLECTIONPID] + self.currentCalculationModel.modelArgumentNames] #keep only minimal info and not duplicates to the fitting frame (except the collectionPid)
        merged = pd.merge(fittingFrame, cdf, on=[sv.COLLECTIONPID], how='left')
        #  .reset_index(drop=True, inplace=True)
        fittingFrame.to_csv('/Users/luca/Documents/temp/fittingFrame.csv')
        calculationFrame.to_csv('/Users/luca/Documents/temp/calculationFrame.csv')
        merged.to_csv('/Users/luca/Documents/temp/merged.csv')
        outputDataTable = self._fetchOutputDataTable(name= f'Untitled_output', overrideExisting=True)
        outputDataTable.data = merged
        self.addOutputData(outputDataTable)
