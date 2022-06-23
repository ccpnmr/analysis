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
__dateModified__ = "$dateModified: 2022-06-23 16:37:36 +0100 (Thu, June 23, 2022) $"
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
from ccpn.util.Logging import getLogger
from ccpn.core.lib.Pid import createPid
from ccpn.core.NmrResidue import NmrResidue
from ccpn.core.DataTable import TableFrame
from ccpn.framework.lib.experimentAnalysis.FittingModelABC import FittingModelABC, MinimiserModel, MinimiserResult, _registerModels
from ccpn.framework.lib.experimentAnalysis.SeriesTablesBC import CSMInputFrame, CSMOutputFrame, CSMBindingOutputFrame
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
        params.get(self.KDstr).value = np.mean(x)
        params.get(self.KDstr).min = np.min(x)
        params.get(self.KDstr).max = np.max(x)+(np.max(x)*0.5)
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
    Description = 'Alpha: the factor for each nuclei of interest.'
    References  = '''
                    1) Eq. (9) M.P. Williamson. Progress in Nuclear Magnetic Resonance Spectroscopy 73, 1–16 (2013).
                    2) Mureddu, L. & Vuister, G. W. Simple high-resolution NMR spectroscopy as a tool in molecular biology.
                       FEBS J. 286, 2035–2042 (2019).
                  '''
    FullDescription = f'{Info} \n {Description}\nSee References: {References}'
    _alphaFactors = [sv.DEFAULT_H_ALPHAFACTOR, sv.DEFAULT_N_ALPHAFACTOR]
    _filteringAtoms = [sv._H, sv._N]
    _excludedResidueTypes = []
    _euclideanCalculationMethod = 'mean' # mean or sum.

    def __init__(self, alphaFactors=None, filteringAtoms=None, excludedResidues=None,):
        super().__init__()
        self._alphaFactors = alphaFactors or DeltaDeltaShiftsCalculation._alphaFactors
        self._filteringAtoms = filteringAtoms or DeltaDeltaShiftsCalculation._filteringAtoms
        self._excludedResidueTypes = excludedResidues or DeltaDeltaShiftsCalculation._excludedResidueTypes
        self._euclideanCalculationMethod = 'mean'

    def setAlphaFactors(self, values):
        self._alphaFactors = values

    def setFilteringAtoms(self, values):
        self._filteringAtoms = values

    def setExcludedResidueTypes(self, values):
        self._excludedResidueTypes = values

    def calculateDeltaDeltaShift(self, inputData:TableFrame, **kwargs) -> TableFrame:
        """
        Calculate the DeltaDeltas for an input SeriesTable.
        :param inputData: CSMInputFrame
        :param args:
        :param kwargs:
            FilteringAtoms   = ['H','N'],
            AlphaFactors     = [1, 0.142],
            ExcludedResidues = ['PRO'] # The string type as it appears in the NmrResidue type. These will be removed.
            Defaults if not given
        :return: outputFrame
        """
        _kwargs = { 'FilteringAtoms':self._filteringAtoms,
                    'AlphaFactors': self._alphaFactors,
                    'ExcludedResidues' : self._excludedResidueTypes}
        _kwargs.update(kwargs)
        outputFrame = DeltaDeltaShiftsCalculation._getDeltaDeltasOutputFrame(inputData, **_kwargs)
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

    @staticmethod
    def _getDeltaDeltasOutputFrame(inputData, **kwargs):
        """
        Calculate the DeltaDeltas for an input SeriesTable.
        :param inputData: CSMInputFrame
        :param args:
        :param kwargs:
            FilteringAtoms   = ['H','N'],
            AlphaFactors     = [1, 0.142],
            ExcludedResidues = ['PRO'] # The string type as it appears in the NmrResidue type. These will be removed.
            Defaults if not given
        :return: outputFrame
        """
        outputDataDict = defaultdict(list)
        grouppingHeaders = [sv.CHAIN_CODE, sv.RESIDUE_CODE, sv.RESIDUE_TYPE]
        _filteringAtoms = kwargs.get(sv.FILTERINGATOMS, DeltaDeltaShiftsCalculation._filteringAtoms)
        _alphaFactors =  kwargs.get(sv.ALPHAFACTORS, DeltaDeltaShiftsCalculation._alphaFactors)
        _excludedResidues = kwargs.get(sv.EXCLUDEDRESIDUETYPES, DeltaDeltaShiftsCalculation._excludedResidueTypes)
        tobeDropped = inputData[inputData[sv.RESIDUE_TYPE].isin(_excludedResidues)]     ## drop rows with excluded ResidueTypes. Should just be set to NaN but keep in?.
        inputData.drop(tobeDropped.index, axis=0, inplace=True)
        for assignmentValues, grouppedDF in inputData.groupby(grouppingHeaders):        ## Group by Assignments except the atomName
            atomFiltered = grouppedDF[grouppedDF[sv.ATOM_NAME].isin(_filteringAtoms)]   ## filter by the specific atoms of interest
            seriesValues4residue = atomFiltered[inputData.valuesHeaders].values.T       ## take the series values in axis 1 and create a 2D array. e.g.:[[8.15 123.49][8.17 123.98]]
            deltaDeltas = DeltaDeltaShiftsCalculation._calculateDeltaDeltas(seriesValues4residue, _alphaFactors)  ## get the deltaDeltas
            newUid = grouppedDF[grouppingHeaders].values[0].astype('str')
            newUid = createPid(NmrResidue.shortClassName, *newUid)
            outputDataDict[sv._ROW_UID].append(newUid)
            for i, assignmentHeader in enumerate(grouppingHeaders):                     ## build new row for the output dataFrame as DefaultDict.
                outputDataDict[assignmentHeader].append(list(assignmentValues)[i])      ## add common assignments definitions
            outputDataDict[sv.ATOM_NAMES].append(','.join(_filteringAtoms))             ## add atom names
            for colnam, oper in zip([sv.DELTA_DELTA_MEAN, sv.DELTA_DELTA_SUM, sv.DELTA_DELTA_STD],[np.mean, np.sum, np.std]):  ## add calculated values from Deltadeltas
                outputDataDict[colnam].append(oper(deltaDeltas[1:]))                    ## first item is excluded from as it is always 0 by definition.
            for _dd, valueHeaderName in zip(deltaDeltas,inputData.valuesHeaders):       ## add single steps Deltadelta value
                outputDataDict[valueHeaderName].append(_dd)
        outputFrame = CSMOutputFrame()
        DeltaDeltaShiftsCalculation._finaliseOutputFrame(grouppingHeaders, inputData, outputFrame, outputDataDict)
        return outputFrame

    @staticmethod
    def _finaliseOutputFrame(grouppingHeaders, inputData, outputFrame, outputDataDict):
        """private completion method """
        outputFrame.setDataFromDict(outputDataDict)
        outputFrame.setSeriesUnits(inputData.SERIESUNITS)
        outputFrame.setSeriesSteps(inputData.SERIESSTEPS)
        outputFrame._assignmentHeaders = grouppingHeaders + [sv.ATOM_NAMES]
        outputFrame._valuesHeaders = inputData.valuesHeaders


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
        getLogger().warning(sv.UNDER_DEVELOPMENT_WARNING)
        ddc = DeltaDeltaShiftsCalculation()
        frame = ddc.calculateDeltaDeltaShift(inputData, **kwargs)
        xArray = np.array(inputData.SERIESSTEPS)
        #TODO Missing rescale option
        outputDataDict = defaultdict(list)
        fittingResults = []
        for ix, row in frame.iterrows():
            seriesValues = row[frame.valuesHeaders]
            yArray = seriesValues.values
            model = self.Minimiser()
            params = model.guess(yArray, xArray)
            try:
                result = model.fit(yArray, params, x=xArray)
            except:
                getLogger().warning(f'Fitting Failed for: {row[sv._ROW_UID]} data.')
                result = MinimiserResult(model, params)
            fittingResults.append(result)
            outputDataDict[sv._ROW_UID].append(row[sv._ROW_UID])
            for i, assignmentHeader in enumerate(inputData.assignmentHeaders[:-1]):  ## build new row for the output dataFrame as DefaultDict.
                outputDataDict[assignmentHeader].append(row[assignmentHeader])  ## add common assignments definitions
            outputDataDict['ModelName'].append(model.MODELNAME)
            for resultName, resulValue in result.getAllResultsAsDict().items():
                outputDataDict[resultName].append(resulValue)
            # outputDataDict['minimiser'].append(result)
        outputFrame = CSMBindingOutputFrame()
        outputFrame.setDataFromDict(outputDataDict)
        outputFrame.setSeriesUnits(inputData.SERIESUNITS)
        outputFrame.setSeriesSteps(inputData.SERIESSTEPS)
        outputFrame._assignmentHeaders = inputData.assignmentHeaders
        outputFrame._valuesHeaders = inputData.valuesHeaders
        return outputFrame


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
