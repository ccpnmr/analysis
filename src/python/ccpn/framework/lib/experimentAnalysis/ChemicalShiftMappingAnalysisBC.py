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

from ccpn.util.Logging import getLogger
from ccpn.framework.lib.experimentAnalysis.SeriesAnalysisABC import SeriesAnalysisABC
import ccpn.framework.lib.experimentAnalysis.SeriesAnalysisVariables as sv
from ccpn.framework.lib.experimentAnalysis.CSMappingModels import FittingModels, CalculationModels


class ChemicalShiftMappingAnalysisBC(SeriesAnalysisABC):
    """
    Chemical Shift Mapping Analysis Non-Gui module.
    # needed settings:
    """
    seriesAnalysisName = sv.ChemicalShiftMappingAnalysis

    def __init__(self):
        super().__init__()

        self._filteringAtoms = sv.DEFAULT_FILTERING_ATOMS
        self._alphaFactors = sv.DEFAULT_ALPHA_FACTORS
        self._excludedResidueTypes = sv.DEFAULT_EXCLUDED_RESIDUES
        self._untraceableValue = 1.0 # default value for replacing NaN values in the DeltaDeltas column
        self.fittingModels = self._registerModels(FittingModels)
        self.calculationModels = self._registerModels(CalculationModels)
        fittingModel = self._getFirstModel(self.fittingModels)
        calculationModel = self._getFirstModel(self.calculationModels)
        if fittingModel:
            self._currentFittingModel = fittingModel()
        if calculationModel:
            self._currentCalculationModel = calculationModel(self._alphaFactors)


    @property
    def inputDataTables(self, ) -> list:
        """
        List of inputDataTables.
        """
        dataTables = super(ChemicalShiftMappingAnalysisBC, self).inputDataTables
        for dataTable in dataTables:
            self._restoreInputDataTableData(dataTable)
        return dataTables


    def getAlphaFactor(self, isotopeCode):
        """Get the Alpha Factor for the DeltaDeltas calculation
        :param isotopeCode =  str, one of 1H, 15N, 13C or Other"""
        if isotopeCode not in self._alphaFactors:
            getLogger().warning(f'Cannot find alphaFactor for {isotopeCode}. Use one of "1H", "15N", "13C" or "Other"')
            return 1
        return self._alphaFactors.get(isotopeCode)

    def setAlphaFactor(self, _1H=None, _15N=None, _13C=None, _Other=None):
        """Set the Alpha Factor for the DeltaDeltas calculation by IsotopeCode.
             Factors are usually values between 0.1-1
        """
        if isinstance(_1H, (float, int)):
            self._alphaFactors.update({sv._1H:_1H})
        if isinstance(_15N, (float, int)):
            self._alphaFactors.update({sv._15N: _15N})
        if isinstance(_13C, (float, int)):
            self._alphaFactors.update({sv._13C:_13C})
        if isinstance(_Other, (float, int)):
            self._alphaFactors.update({sv._OTHER: _Other})

    def calculateDeltaDeltaShifts(self, inputData, **kwargs):
        """
        Calculate the DeltaDeltas Chemical shift distances for an input SeriesTable.
        :param inputData: CSMInputFrame
        :return: outputFrame
        """
        from ccpn.framework.lib.experimentAnalysis.CSMappingModels import EuclideanCalculationModel
        if self.currentCalculationModel is None: # it shouldn't happen
            self.currentCalculationModel = EuclideanCalculationModel(alphaFactors=self._alphaFactors)
        frame = self.currentCalculationModel.calculateValues(inputData)
        return frame

    def fitInputData(self, *args, **kwargs):
        """
        Perform the registered FittingModels to the inputDataTables and add the outputs to a newDataTable or
         override last available.
        :param args:
        :param kwargs:
            :key: outputName:       outputDataTable name
            :key: fittingModels:    list of fittingModel classes (not initialised).So to use only the specif given,
                                    rather than all available.
            :key: overrideOutputDataTables: bool, True to rewrite the output result in the last available dataTable.
                                    When multiple fittingModels are available, each will output in a different dataTable
                                    according to its definitions.
        :return: None
        """
        getLogger().info('Started fitting InputData...')
        if not self.inputDataTables:
            raise RuntimeError('CSM. Cannot run any fitting models. Add a valid inputData first')

        fittingModel = self.currentFittingModel
        if not fittingModel:
            raise RuntimeError('CSM. Cannot run any fitting models. Select a FittingModel first')
        ovverideOutputDataTable = True
        outputDataTableName = kwargs.get(sv.OUTPUT_DATATABLE_NAME, None)

        inputDataTable = self.inputDataTables[-1]
        outputFrame = self.calculateDeltaDeltaShifts(inputDataTable.data)
        outputFrame = fittingModel.fitSeries(outputFrame)

        if not outputDataTableName:
            outputDataTableName = f'{inputDataTable.name}_output_{fittingModel.ModelName}'.replace(" ", "")
        outputDataTable = self._fetchOutputDataTable(name=outputDataTableName,
                                                     overrideExisting=ovverideOutputDataTable)
        outputDataTable.data = outputFrame
        self.addOutputData(outputDataTable)
        self._needsRefitting = False
        getLogger().info('Fitting InputData completed.')


    def plotResults(self, *args, **kwargs):
        getLogger().warning('Not implemented yet. Available: plotDeltaDeltas')

    def plotDeltaDeltas(self, deltaDeltaShiftsFrame,
                        yColumnName=sv.DELTA_DELTA,
                        unitLabels = 'minimal',
                        unitLabelRotation=45,
                        majorTick=5,
                        minorTicks=1,
                        orientation='v',
                        *args, **kwargs):
        """
        Plot a bargraph of the deltaDeltas
        :param deltaDeltaShiftsFrame:
        :param yColumnName:
        :param unitLabels:
                        - minimal: only RESIDUE_CODE
                        - full: RESIDUE_TYPE + RESIDUE_CODE
        :param unitLabelRotation: degree of the text rotation
        :param unitLabelsInterval:
                        - None: default show all labels as in the original data
                        - int: e.g.: 5 show a scale at 5 numbers gaps. [0,5,10,15,20...]
        :param orientation : v or h
        :param args:
        :param kwargs:
        :return:
        """
        pass

