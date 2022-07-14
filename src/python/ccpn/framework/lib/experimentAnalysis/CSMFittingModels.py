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
__dateModified__ = "$dateModified: 2022-07-14 21:56:16 +0100 (Thu, July 14, 2022) $"
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
from collections import defaultdict

import pandas as pd

from ccpn.util.Logging import getLogger
from ccpn.core.lib.Pid import createPid
from ccpn.core.NmrResidue import NmrResidue
from ccpn.core.DataTable import TableFrame
from ccpn.framework.lib.experimentAnalysis.FittingModelABC import FittingModelABC, MinimiserModel, MinimiserResult, _registerModels
from ccpn.framework.lib.experimentAnalysis.SeriesTablesBC import  CSMOutputFrame
import ccpn.framework.lib.experimentAnalysis.SeriesAnalysisVariables as sv
import ccpn.framework.lib.experimentAnalysis.fitFunctionsLib as lf

########################################################################################################################
####################################       Minimisers     ##############################################################
########################################################################################################################

class FractionBindingMinimiser(MinimiserModel):
    """A model based on the fraction bound Fitting equation.
      Eq. 6 from  M.P. Williamson. Progress in Nuclear Magnetic Resonance Spectroscopy 73, 1–16 (2013).
    """

    FITTING_FUNC = lf.fractionBound_func

    def __init__(self, independent_vars=['x'], prefix='', nan_policy=sv.OMIT_MODE, **kwargs):
        kwargs.update({'prefix': prefix, 'nan_policy': nan_policy, 'independent_vars': independent_vars})
        super().__init__(FractionBindingMinimiser.FITTING_FUNC, **kwargs)

    def guess(self, data, x, **kwargs):
        """Estimate initial model parameter values from data."""
        raise NotImplementedError()


class Binding1SiteMinimiser(MinimiserModel):
    """A model based on the oneSiteBindingCurve Fitting equation.
    """

    FITTING_FUNC = lf.oneSiteBinding_func
    MODELNAME = '1_Site_Binding_Model'

    KDstr = sv.KD # They must be exactly as they are defined in the FITTING_FUNC arguments! This was too hard to change!
    BMAXstr = sv.BMAX

    _defaultParams = {KDstr:1,
                      BMAXstr:0.5}


    def __init__(self, independent_vars=['x'], prefix='', nan_policy=sv.OMIT_MODE, **kwargs):
        kwargs.update({'prefix': prefix, 'nan_policy': nan_policy, 'independent_vars': independent_vars})
        super().__init__(Binding1SiteMinimiser.FITTING_FUNC, **kwargs)
        self.name = self.MODELNAME
        self.Kd = None # this will be a Parameter Obj . Set on the fly by the minimiser while inspecting the Fitting Func signature
        self.BMax = None # this will be a Parameter Obj
        self.params = self.make_params(**self._defaultParams)

    def guess(self, data, x, **kws):
        """
        :param data: y values 1D array
        :param x: the x axis values. 1D array
        :param kws:
        :return: dict of params needed for the fitting
        """
        params = self.params
        minKD = np.min(x)
        maxKD = np.max(x)+(np.max(x)*0.5)
        if minKD == maxKD == 0:
            getLogger().warning(f'Fitting model min==max {minKD}, {maxKD}')
            minKD = -1

        params.get(self.KDstr).value = np.mean(x)
        params.get(self.KDstr).min = minKD
        params.get(self.KDstr).max = maxKD
        params.get(self.BMAXstr).value = np.mean(data)
        params.get(self.BMAXstr).min = 0.001
        params.get(self.BMAXstr).max = np.max(data)+(np.max(data)*0.5)
        return params


########################################################################################################################
####################################    DataSeries Models    ###########################################################
########################################################################################################################

class DeltaDeltaShiftsCalculation():
    """
    ChemicalShift Analysis DeltaDeltas shift distance calculation
    """
    ModelName = sv.EUCLIDEAN_DISTANCE
    Info        = 'Calculate The DeltaDelta shifts for a series using the average Euclidean Distance.'
    MaTex       = r'$\sqrt{\frac{1}{N}\sum_{i=0}^N (\alpha_i*\delta_i)^2}$'
    Description = f'{sv.uALPHA}: the factor for each atom of interest;\ni: atom;\nN atom count;\n{sv.uDelta}: delta shift per atom in the series'
    References  = '''
                    1) Eq. (9) M.P. Williamson. Progress in Nuclear Magnetic Resonance Spectroscopy 73, 1–16 (2013).
                    2) Mureddu, L. & Vuister, G. W. Simple high-resolution NMR spectroscopy as a tool in molecular biology.
                       FEBS J. 286, 2035–2042 (2019).
                  '''
    FullDescription = f'{Info} \n {Description}\nSee References: {References}'

    _euclideanCalculationMethod = 'mean' # mean or sum.

    def __init__(self, alphaFactors=None, filteringAtoms=None, excludedResidues=[]):
        super().__init__()
        self._alphaFactors = alphaFactors
        self._filteringAtoms = filteringAtoms
        self._excludedResidueTypes = excludedResidues
        self._euclideanCalculationMethod = 'mean'

    def setAlphaFactors(self, values):
        self._alphaFactors = values

    def setFilteringAtoms(self, values):
        self._filteringAtoms = values

    def setExcludedResidueTypes(self, values):
        self._excludedResidueTypes = values

    def calculateDeltaDeltaShift(self, inputData:TableFrame) -> TableFrame:
        """
        Calculate the DeltaDeltas for an input SeriesTable.
        :param inputData: CSMInputFrame
        :return: outputFrame
        """
        outputFrame = self._getDeltaDeltasOutputFrame(inputData)
        return outputFrame

    #########################
    ### Private functions ###
    #########################

    @staticmethod
    def _calculateDeltaDeltas(data, alphaFactors):
        """
        :param data: 2D array containing A and B coordinates to measure.
        e.g.: for two HN peaks data will be a 2D array, e.g.: [[  8.15842 123.49895][  8.17385 123.98413]]
        :return: float
        """
        deltaDeltas = []
        origin = data[0] # first set of positions (any dimensionality)
        for coord in data:# the other set of positions (same dim as origin)
            dd = lf.euclideanDistance_func(origin, coord, alphaFactors)
            deltaDeltas.append(dd)
        return deltaDeltas

    def _getDeltaDeltasOutputFrame(self, inputData):
        """
        Calculate the DeltaDeltas for an input SeriesTable.
        :param inputData: CSMInputFrame
        :return: outputFrame
        """
        outputFrame = CSMOutputFrame()
        outputFrame._buildColumnHeaders()
        grouppedByCollectionsId = inputData.groupby([sv.COLLECTIONID])
        rowIndex = 1
        while True:
            for collectionId, groupDf in grouppedByCollectionsId:
                groupDf.sort_values([sv.SERIESSTEP], inplace=True)
                dimensions = groupDf[sv.DIMENSION].unique()
                dataPerDimensionDict = {}
                for dim in dimensions:
                    dimRow = groupDf[groupDf[sv.DIMENSION] == dim]
                    dataPerDimensionDict[dim] = dimRow[sv._PPMPOSITION].values
                alphaFactors = []
                for i in dataPerDimensionDict: # get the correct alpha factors per IsotopeCode/dimension and not derive it by atomName.
                    ic = groupDf[groupDf[sv.DIMENSION] == i][sv.ISOTOPECODE].unique()[-1]
                    alphaFactors.append(self._alphaFactors.get(ic, 1))
                values = np.array(list(dataPerDimensionDict.values()))
                seriesValues4residue = values.T  ## take the series values in axis 1 and create a 2D array. e.g.:[[8.15 123.49][8.17 123.98]]
                deltaDeltas = DeltaDeltaShiftsCalculation._calculateDeltaDeltas(seriesValues4residue, alphaFactors)
                csmValue = np.mean(deltaDeltas[1:])      ## first item is excluded from as it is always 0 by definition.
                nmrAtomNames = inputData._getAtomNamesFromGroupedByHeaders(groupDf) # join the atom names from different rows in a list
                seriesSteps = groupDf[sv.SERIESSTEP].unique()
                for delta, seriesStep in zip(deltaDeltas, seriesSteps):
                    # build the outputFrame
                    outputFrame.loc[rowIndex, sv.COLLECTIONID] = collectionId
                    outputFrame.loc[rowIndex, sv.COLLECTIONPID] = groupDf[sv.COLLECTIONPID].values[-1]
                    outputFrame.loc[rowIndex, sv.SERIESSTEPVALUE] = delta
                    outputFrame.loc[rowIndex, sv.SERIESSTEP] = seriesStep
                    outputFrame.loc[rowIndex, sv.DELTA_DELTA] = csmValue
                    outputFrame.loc[rowIndex, sv.GROUPBYAssignmentHeaders] = groupDf[sv.GROUPBYAssignmentHeaders].values[0]
                    outputFrame.loc[rowIndex, sv.NMRATOMNAMES] = nmrAtomNames
                    outputFrame.loc[rowIndex, sv.FLAG] = sv.FLAG_INCLUDED
                    rowIndex += 1
            break
        return outputFrame



class OneSiteBindingModel(FittingModelABC):
    """
    ChemicalShift Analysis: One Site-Binding Curve calculation model
    """
    ModelName = sv.ONE_BINDING_SITE_MODEL
    Info = 'Fit data to using the One-Binding-Site model.'
    Description = ' ... '
    References = '''
                    1) Eq. (x) M.P. Williamson. Progress in Nuclear Magnetic Resonance Spectroscopy 73, 1–16 (2013).
                  '''
    MaTex = ''
    Minimiser = Binding1SiteMinimiser

    def fitSeries(self, inputData:TableFrame, rescale=True, *args, **kwargs) -> TableFrame:
        """

        :param inputData:
        :param rescale:
        :param args:
        :param kwargs:
        :return:

        groupbyCollecID
        get series steps as x
        get Series Values as y
        fill the stats
        """
        getLogger().warning(sv.UNDER_DEVELOPMENT_WARNING)

        #TODO Missing rescale option
        grouppedByCollectionsId = inputData.groupby([sv.COLLECTIONID])

        for collectionId, groupDf in grouppedByCollectionsId:
            groupDf.sort_values([sv.SERIESSTEP], inplace=True)
            seriesSteps = groupDf[sv.SERIESSTEP]
            seriesValues = groupDf[sv.SERIESSTEPVALUE]
            xArray = seriesSteps.values
            yArray = seriesValues.values
            if sv.FLAG_EXCLUDED in groupDf[sv.FLAG]:
                yArray = np.full(seriesValues.values.shape, fill_value=np.nan)
            model = self.Minimiser()
            try:
                params = model.guess(yArray, xArray)
                result = model.fit(yArray, params, x=xArray)
            except:
                if sv.FLAG_EXCLUDED in groupDf[sv.FLAG]:
                    getLogger().warning(f'Fitting skipped for collectionId: {collectionId} data.')
                else:
                    getLogger().warning(f'Fitting Failed for collectionId: {collectionId} data.')
                params = model.params
                result = MinimiserResult(model, params)


            inputData.loc[collectionId, sv.MODEL_NAME] = model.MODELNAME
            # inputData.loc[collectionId, sv.MINIMISER_METHOD] =
            for resultName, resulValue in result.getAllResultsAsDict().items():
                inputData.loc[collectionId, resultName] = resulValue
        return inputData


class FractionBindingModel(FittingModelABC):
    """
    ChemicalShift Analysis: FractionBinding fitting Curve calculation model
    """
    ModelName = sv.FRACTION_BINDING_MODEL
    Info = 'Fit data to using the Fraction Binding model.'
    Description = ' ... '
    References = '''
                '''
    MaTex = ''
    Minimiser = FractionBindingMinimiser

    def fitSeries(self, inputData:TableFrame, rescale=True, *args, **kwargs) -> TableFrame:
        getLogger().critical(sv.NIY_WARNING)
        return inputData

########################################################################################################################
########################################################################################################################

ChemicalShiftCalculationModes = {DeltaDeltaShiftsCalculation.ModelName: DeltaDeltaShiftsCalculation,
                                 }
ChemicalShiftCalculationModels = {OneSiteBindingModel.ModelName: OneSiteBindingModel,
                                  FractionBindingModel.ModelName: FractionBindingModel}

def _registerChemicalShiftMappingModels():
    """
    Register the ChemicalShiftMapping specific Models
    """
    from ccpn.framework.lib.experimentAnalysis.ChemicalShiftMappingAnalysisBC import ChemicalShiftMappingAnalysisBC
    models = [OneSiteBindingModel]
    _registerModels(ChemicalShiftMappingAnalysisBC, models)
