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
__dateModified__ = "$dateModified: 2022-03-01 09:23:44 +0000 (Tue, March 01, 2022) $"
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
import numpy as np
import lmfit.lineshapes as func
from lmfit.models import update_param_vals
from scipy.optimize import curve_fit
from collections import defaultdict
from ccpn.util.Logging import getLogger
from ccpn.core.DataTable import TableFrame
from ccpn.framework.lib.experimentAnalysis.FittingModelABC import FittingModelABC, MinimiserModel,  _registerModels
from ccpn.framework.lib.experimentAnalysis.SeriesTablesBC import CSMInputFrame, CSMOutputFrame
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

    def __init__(self, independent_vars=['x'], prefix='', nan_policy='raise', **kwargs):
        kwargs.update({'prefix': prefix, 'nan_policy': nan_policy, 'independent_vars': independent_vars})
        super().__init__(Binding1SiteMinimiser.FITTING_FUNC, **kwargs)

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

    _alphaFactors = (sv.DEFAULT_H_ALPHAFACTOR, sv.DEFAULT_N_ALPHAFACTOR)
    _filteringAtoms = (sv._H, sv._N)

    def __init__(self, alphaFactors=None, filteringAtoms=None):
        super().__init__()

        if alphaFactors:
            self.setAlphaFactors(alphaFactors)

        if filteringAtoms:
            self.setFilteringAtoms(filteringAtoms)

    def setAlphaFactors(self, values):
        self._alphaFactors = values

    def setFilteringAtoms(self, values):
        self._filteringAtoms = values

    def calculateDeltaDeltaShift(self, inputData:TableFrame, **kwargs) -> TableFrame:
        """
        Calculate the DeltaDeltas for an input SeriesTable.
        :param inputData: CSMInputFrame
        :param args:
        :param kwargs: FilteringAtoms=('H','N'), AlphaFactors=(1, 0.142), defaults if not given
        :return: CSMOutputFrame
        """
        outputFrame = DeltaDeltaShiftsCalculation._getDeltaDeltasOutputFrame(inputData, **kwargs)
        return outputFrame

    @staticmethod
    def _getDeltaDeltasOutputFrame(inputData, **kwargs):
        """
        Calculate the DeltaDeltas for an input SeriesTable.
        :param inputData: CSMInputFrame
        :param args:
        :param kwargs: FilteringAtoms=('H','N'), AlphaFactors=(1, 0.142), defaults if not given
        :return: dict
        """
        outputFrame = CSMOutputFrame()
        outputDataDict = defaultdict(list)
        grouppingHeaders = [sv.CHAIN_CODE, sv.RESIDUE_CODE, sv.RESIDUE_TYPE]
        _filteringAtoms = kwargs.get(sv.FILTERINGATOMS, DeltaDeltaShiftsCalculation._filteringAtoms)
        _alphaFactors =  kwargs.get(sv.ALPHAFACTORS, DeltaDeltaShiftsCalculation._alphaFactors)
        for assignmentValues, grouppedDF in inputData.groupby(grouppingHeaders):
            ## filter by the specific atoms of interest
            atomFiltered = grouppedDF[grouppedDF[sv.ATOM_NAME].isin(_filteringAtoms)]
            ## take the series values in axis 1 and create a 2D array. e.g.:[[8.15 123.49][8.17 123.98]]
            seriesValues4residue = atomFiltered[inputData.valuesHeaders].values.T
            ## get the deltaDeltas
            deltaDeltas = DeltaDeltaShiftsCalculation._calculateDeltaDeltas(seriesValues4residue, _alphaFactors)
            ## build new row for the output dataFrame.
            for i, assignmentHeader in enumerate(grouppingHeaders):
                outputDataDict[assignmentHeader].append(list(assignmentValues)[i])
            outputDataDict[sv.ATOM_NAMES].append(','.join(_filteringAtoms))
            outputDataDict[sv.DELTA_DELTA_MEAN].append(np.mean(deltaDeltas[1:])) #first is excluded from mean as it is 0.
            outputDataDict[sv.DELTA_DELTA_SUM].append(np.sum(deltaDeltas))
            outputDataDict[sv.DELTA_DELTA_STD].append(np.std(deltaDeltas[1:]))
            for _dd, valueHeaderName in zip(deltaDeltas,inputData.valuesHeaders):
                outputDataDict[valueHeaderName].append(_dd)
        outputFrame.setDataFromDict(outputDataDict)
        outputFrame.setSeriesUnits(inputData.SERIESUNITS)
        outputFrame.setSeriesSteps(inputData.SERIESSTEPS)
        outputFrame._assignmentHeaders = grouppingHeaders + [sv.ATOM_NAMES]
        outputFrame._valuesHeaders = inputData.valuesHeaders
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


    def fitSeries(self, inputData:TableFrame, *args, **kwargs) -> TableFrame:

        ddc = DeltaDeltaShiftsCalculation()
        frame = ddc.calculateDeltaDeltaShift(inputData, **kwargs)
        for ix, seriesValues in frame[frame.valuesHeaders].iterrows():
            print('EEE', seriesValues)









def _registerChemicalShiftMappingModels():
    """
    Register the ChemicalShiftMapping specific Models
    """
    from ccpn.framework.lib.experimentAnalysis.ChemicalShiftMappingAnalysisBC import ChemicalShiftMappingAnalysisBC
    models = [OneSiteBindingModel]
    _registerModels(ChemicalShiftMappingAnalysisBC, models)
