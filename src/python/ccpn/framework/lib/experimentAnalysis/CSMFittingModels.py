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
__dateModified__ = "$dateModified: 2022-03-04 18:51:50 +0000 (Fri, March 04, 2022) $"
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
from lmfit.models import update_param_vals
from collections import defaultdict
from ccpn.util.Logging import getLogger
from ccpn.core.DataTable import TableFrame
from ccpn.framework.lib.experimentAnalysis.FittingModelABC import FittingModelABC, MinimiserModel,  _registerModels
from ccpn.framework.lib.experimentAnalysis.SeriesTablesBC import CSMInputFrame, CSMOutputFrame, CSMBindingOutputFrame
import ccpn.framework.lib.experimentAnalysis.SeriesAnalysisVariables as sv
import ccpn.framework.lib.experimentAnalysis.fitFunctionsLib as lf
from ccpn.core.lib.Pid import createPid

########################################################################################################################
####################################       Minimisers     ##############################################################
########################################################################################################################


class FractionBindingMinimiser(MinimiserModel):
    """A model based on the fraction bound Fitting equation.
      Eq. 6 from  M.P. Williamson. Progress in Nuclear Magnetic Resonance Spectroscopy 73, 1–16 (2013).
    """

    FITTING_FUNC = lf.fractionBound_func

    def __init__(self, independent_vars=['x'], prefix='', nan_policy='raise', **kwargs):
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

    def __init__(self, independent_vars=['x'], prefix='', nan_policy='raise', **kwargs):
        kwargs.update({'prefix': prefix, 'nan_policy': nan_policy, 'independent_vars': independent_vars})
        super().__init__(Binding1SiteMinimiser.FITTING_FUNC, **kwargs)
        self.name = self.MODELNAME

    def guess(self, data, x, **kwargs):
        """Estimate initial model parameter values from data."""
        raise NotImplementedError()



########################################################################################################################
####################################    DataSeries Models    ###########################################################
########################################################################################################################


class DeltaDeltaShiftsCalculation():
    """
    ChemicalShift Analysis DeltaDeltas shift distance calculation
    """
    ModelName = sv.DELTA_DELTA
    Info = 'Calculate The DeltaDelta shifts for a series.'
    Description = ' CSP = √∑𝛂(𝛿i)^2 '
    References = '''
                    1) Eq. (9) M.P. Williamson. Progress in Nuclear Magnetic Resonance Spectroscopy 73, 1–16 (2013).
                    2) Mureddu, L. & Vuister, G. W. Simple high-resolution NMR spectroscopy as a tool in molecular biology.
                       FEBS J. 286, 2035–2042 (2019).
                  '''

    _alphaFactors = [sv.DEFAULT_H_ALPHAFACTOR, sv.DEFAULT_N_ALPHAFACTOR]
    _filteringAtoms = [sv._H, sv._N]
    _excludedResidueTypes = []

    def __init__(self, alphaFactors=None, filteringAtoms=None, excludedResidues=None,):
        super().__init__()
        self._alphaFactors = alphaFactors or DeltaDeltaShiftsCalculation._alphaFactors
        self._filteringAtoms = filteringAtoms or DeltaDeltaShiftsCalculation._filteringAtoms
        self._excludedResidueTypes = excludedResidues or DeltaDeltaShiftsCalculation._excludedResidueTypes

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
        outputFrame = DeltaDeltaShiftsCalculation._getDeltaDeltasOutputFrame(inputData, **kwargs)
        return outputFrame

    @staticmethod
    def _calculateDeltaDeltas(data, alphaFactors):
        """
        :param data: 2D array containing A and B coordinates to measure.
        e.g.: for two HN peaks data will be array [[  8.15842 123.49895][  8.17385 123.98413]]
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
            newUid = createPid('NR', *newUid)
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

    Minimiser = Binding1SiteMinimiser

    def fitSeries(self, inputData:TableFrame, rescale=True, *args, **kwargs) -> TableFrame:

        ddc = DeltaDeltaShiftsCalculation()
        frame = ddc.calculateDeltaDeltaShift(inputData, **kwargs)
        xArray = np.array(inputData.SERIESSTEPS)
        #TODO  rescale option
        outputDataDict = defaultdict(list)
        for ix, row in frame.iterrows():
            seriesValues = row[frame.valuesHeaders]
            yArray = seriesValues.values
            model = self.Minimiser()
            params = model.make_params(kd=1, bmax=0.5)
            params['kd'].min = 0.1
            params['kd'].max = 10
            params['bmax'].min = 0.001
            params['bmax'].max = 1
            result = None #replace with class obj?
            try:
                result = model.fit(yArray, params, x=xArray)
            except:
                getLogger().warning(f'Fitting Failed for: {row[sv._ROW_UID]} data.')
            outputDataDict[sv._ROW_UID].append(row[sv._ROW_UID])
            for i, assignmentHeader in enumerate(inputData.assignmentHeaders[:-1]):  ## build new row for the output dataFrame as DefaultDict.
                outputDataDict[assignmentHeader].append(row[assignmentHeader])  ## add common assignments definitions
            outputDataDict['ModelName'].append(model.MODELNAME)
            for nn, vv in zip([sv.MINIMISER_METHOD, sv.R2, sv.CHISQUARE, sv.REDUCEDCHISQUARE, sv.AKAIKE, sv.BAYESIAN],
                          ['method', 'r2', 'chisqr','redchi', 'aic', 'bic']):
                outputDataDict[nn].append(getattr(result, vv, None))
            vv = ['kd', 'bmax']
            if result is not None:
                for j in vv:
                    param = result.params.get(j)
                    outputDataDict[j].append(param.value)
                    outputDataDict[f'{j}_err'].append(param.stderr)
            else:
                for j in vv :
                    outputDataDict[j].append(None)
                    outputDataDict[f'{j}_err'].append(None)

            outputDataDict['minimiser'].append(result)
        outputFrame = CSMBindingOutputFrame()
        outputFrame.setDataFromDict(outputDataDict)
        outputFrame.setSeriesUnits(inputData.SERIESUNITS)
        outputFrame.setSeriesSteps(inputData.SERIESSTEPS)
        outputFrame._assignmentHeaders = inputData.assignmentHeaders
        outputFrame._valuesHeaders = inputData.valuesHeaders
        return outputFrame







def _registerChemicalShiftMappingModels():
    """
    Register the ChemicalShiftMapping specific Models
    """
    from ccpn.framework.lib.experimentAnalysis.ChemicalShiftMappingAnalysisBC import ChemicalShiftMappingAnalysisBC
    models = [OneSiteBindingModel]
    _registerModels(ChemicalShiftMappingAnalysisBC, models)
