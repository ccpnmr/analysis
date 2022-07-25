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
__dateModified__ = "$dateModified: 2022-07-25 13:50:14 +0100 (Mon, July 25, 2022) $"
__version__ = "$Revision: 3.1.0 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Luca Mureddu $"
__date__ = "$Date: 2022-02-02 14:08:56 +0000 (Wed, February 02, 2022) $"
#=========================================================================================
# Start of code
#=========================================================================================

import numpy as np
import pandas as pd
from scipy import stats
from ccpn.util.Logging import getLogger
from ccpn.framework.lib.experimentAnalysis.SeriesAnalysisABC import SeriesAnalysisABC
import ccpn.framework.lib.experimentAnalysis.SeriesAnalysisVariables as sv
from ccpn.framework.lib.experimentAnalysis.CSMFittingModels import _registerChemicalShiftMappingModels
import ccpn.framework.lib.experimentAnalysis.fitFunctionsLib as lf


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
        _registerChemicalShiftMappingModels()

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

    @property
    def untraceableValue(self) ->float:
        return self._untraceableValue

    @untraceableValue.setter
    def untraceableValue(self, value):
        if isinstance(value, (float,int)):
            self._untraceableValue = value
        else:
            getLogger().warning(f'Impossible to set untraceableValue to {value}. Use type int or float.')

    def calculateDeltaDeltaShifts(self, inputData, **kwargs):
        """
        Calculate the DeltaDeltas Chemical shift distances for an input SeriesTable.
        :param inputData: CSMInputFrame
        :return: outputFrame
        """
        from ccpn.framework.lib.experimentAnalysis.CSMFittingModels import DeltaDeltaShiftsCalculation
        ddc = DeltaDeltaShiftsCalculation(alphaFactors=self._alphaFactors,
                                          filteringAtoms=self._filteringAtoms,
                                          excludedResidues=self._excludedResidueTypes)
        frame = ddc.calculateDeltaDeltaShift(inputData)
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

        fittingModels = self.fittingModels or kwargs.get(sv.FITTING_MODELS, [])
        ovverideOutputDataTable = True
        outputDataTableName = kwargs.get(sv.OUTPUT_DATATABLE_NAME, None)
        for model in fittingModels:
            fittingModel = model()
            inputDataTable = self.inputDataTables[-1]
            outputFrame = self.calculateDeltaDeltaShifts(inputDataTable.data,
                                                      filteringAtoms=self._filteringAtoms,
                                                      alphaFactors=self._alphaFactors,
                                                      excludedResidues=self._excludedResidueTypes)
            outputFrame = fittingModel.fitSeries(outputFrame)

            if not outputDataTableName:
                outputDataTableName = f'{inputDataTable.name}_output_{fittingModel.ModelName}'.replace(" ", "")
            outputDataTable = self._fetchOutputDataTable(name=outputDataTableName,
                                                         overrideExisting=ovverideOutputDataTable)
            outputDataTable.data = outputFrame
            self.addOutputData(outputDataTable)
        self._needsRefitting = False
        getLogger().info('Fitting InputData completed.')

    def getFirstOutputDataFrame(self):
        """Get the first available dataFrame from the outputDataTable. """
        if len(self.inputDataTables) == 0:
            return
        if not self.getOutputDataTables():
            return
        outputDataTable = self.getOutputDataTables()[0]
        return outputDataTable.data

    def _getGroupedOutputDataFrame(self, *args):
        """ internal. Used to get a df to display in GuiTables
         Return the outputDataFrame containing the fitting and deltaDeltas calculations.
         """
        outDataFrame = self.getFirstOutputDataFrame()
        if outDataFrame is None:
            return
        ## group by id and keep only first row as all duplicated except the series steps, which are not needed here.
        ## reset index otherwise you lose the column collectionId
        outDataFrame = outDataFrame.groupby(sv.COLLECTIONID).first().reset_index()
        outDataFrame[sv._ROW_UID] = np.arange(1, len(outDataFrame)+1)
        outDataFrame[sv.ASHTAG] = outDataFrame[sv._ROW_UID].values
        # add Code+type Column
        outDataFrame.joinNmrResidueCodeType()
        return outDataFrame

    def getThresholdValueForData(self, calculationMode=sv.MAD, factor=1.):
        """ Get the Threshold value for the deltaDeltas.
        :param calculationMode: str, one of ['MAD', 'AAD', 'Mean', 'Median', 'STD']
        :param factor: float. Multiplication factor.
        :return float.

        MAD: Median absolute deviation, (https://en.wikipedia.org/wiki/Median_absolute_deviation)
        AAD: Average absolute deviation, (https://en.wikipedia.org/wiki/Average_absolute_deviation).
        Note, MAD and AAD are often abbreviated the same way, in fact, in scipy MAD is Median absolute deviation,
        whereas in Pandas MAD is Mean absolute deviation!
        """
        factor = factor if factor and factor >0 else 1
        thresholdValue = None
        data = self._getGroupedOutputDataFrame()

        if data is not None:
            if len(data[sv.DELTA_DELTA])>0:
                values = data[sv.DELTA_DELTA].values
                values = values[~np.isnan(values)]  # skip nans
                if calculationMode == sv.MAD:
                    thresholdValue = stats.median_absolute_deviation(values) # in scipy MAD is Median absolute deviation
                if calculationMode == sv.AAD:
                    thresholdValue = data[sv.DELTA_DELTA].mad() # in pandas MAD is Mean absolute deviation !
                else:
                    func = lf.CommonStatFuncs.get(calculationMode, None)
                    if func:
                        thresholdValue = func(values)
        if thresholdValue:
            thresholdValue *= factor
        return thresholdValue

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

