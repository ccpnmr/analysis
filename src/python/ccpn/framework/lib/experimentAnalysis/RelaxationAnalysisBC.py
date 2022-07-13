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
__dateModified__ = "$dateModified: 2022-07-13 11:03:43 +0100 (Wed, July 13, 2022) $"
__version__ = "$Revision: 3.1.0 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Luca Mureddu $"
__date__ = "$Date: 2022-02-02 14:08:56 +0000 (Wed, February 02, 2022) $"
#=========================================================================================
# Start of code
#=========================================================================================

from ccpn.framework.lib.experimentAnalysis.SeriesAnalysisABC import SeriesAnalysisABC
import ccpn.framework.lib.experimentAnalysis.SeriesAnalysisVariables as sv
from ccpn.framework.lib.experimentAnalysis.RelaxationFittingModels import _registerRelaxationModels, RELAXATION_MODELS_DICT
from ccpn.util.Logging import getLogger

class RelaxationAnalysisBC(SeriesAnalysisABC):
    """
    Relaxation Analysis Non-Gui module.
    """
    seriesAnalysisName = sv.RelaxationAnalysis

    def __init__(self):
        super().__init__()
        _registerRelaxationModels()


    def fitInputData(self, *args, **kwargs):
        """
        Perform the registered FittingModels to the inputDataTables and add the outputs to a newDataTable or
         override last available.
        :param args:
        :param kwargs:
            :key: modelName:        If given, find and use only this model. E.g.: T1
            :key: fittingModels:    Alternatively to a specific model name,
                                    provide a list of fittingModel classes (not initialised). Use only the specif given,
                                    rather than all available.
            :key: overrideOutputDataTables: bool, True to rewrite the output result in the last available dataTable.
                                    When multiple fittingModels are available, each will output in a different dataTable
                                    according to its definitions.
        :return: None. Creates a new output dataTable in outputDataTables
        """
        getLogger().warning(sv.UNDER_DEVELOPMENT_WARNING)

        if not self.inputDataTables:
            raise RuntimeError('Cannot run any fitting models. Add a valid inputData first')
        fittingModel = RELAXATION_MODELS_DICT.get(kwargs.get(sv.MODEL_NAME))
        if fittingModel is not None:
            fittingModels = [fittingModel]
        else:
            fittingModels = self.fittingModels or kwargs.get(sv.FITTING_MODELS, [])
        ovverideOutputDataTable = kwargs.get(sv.OVERRIDE_OUTPUT_DATATABLE, True)
        for model in fittingModels:
            fittingModel = model()
            inputDataTable = self.inputDataTables[-1]
            outputFrame = fittingModel.fitSeries(inputDataTable.data)
            outputName = f'{inputDataTable.name}_output_{fittingModel.ModelName}'
            outputDataTable = self._fetchOutputDataTable(name=outputName,
                                                   overrideExisting=ovverideOutputDataTable)
            outputDataTable.data = outputFrame
            self.addOutputData(outputDataTable)
