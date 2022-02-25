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
__dateModified__ = "$dateModified: 2022-02-25 15:14:19 +0000 (Fri, February 25, 2022) $"
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

class DeltaDeltaCalculation(FittingModelABC):
    """
    #TODO: Inspect --> not sure if this should be a Fitting model. As is not really fitting anything. It only contains math.
    ChemicalShift Analysis DeltaDelta calculation model
    """
    ModelName = sv.DELTA_DELTA
    Info = 'Calculate The DeltaDelta shifts for a series.'
    Description = ' CSP = √∑𝛂(𝛿i)^ '
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

    def fitSeries(self, inputData:CSMInputFrame, *args, **kwargs) -> CSMOutputFrame:
        """
        Calculate the DeltaDeltas for an input SeriesTable.
        :param inputData:
        :param args:
        :param kwargs:
        :return:
        """
        outputDataDict = defaultdict(list)
        grouppingHeaders = [sv.CHAIN_CODE, sv.RESIDUE_CODE, sv.RESIDUE_TYPE]
        for assignmentValues, grouppedDF in inputData.groupby(grouppingHeaders):
            ## filter by the specific atoms of interest
            atomFiltered = grouppedDF[grouppedDF[sv.ATOM_NAME].isin(self._filteringAtoms)]
            ## take the series values in axis 1 and create a 2D array. e.g.:[[8.15 123.49][8.17 123.98]]
            seriesValues4residue = atomFiltered[inputData.valuesHeaders].values.T
            ## get the deltaDeltas
            deltaDelta = self._calculateDeltaDelta(data=seriesValues4residue)
            ## build new row for the output dataFrame.
            for i, assignmentHeader in enumerate(grouppingHeaders):
                outputDataDict[assignmentHeader].append(list(assignmentValues)[i])
            outputDataDict[sv.ATOM_NAMES].append(','.join(self._filteringAtoms))
            outputDataDict[sv.DELTA_DELTA].append(deltaDelta)
        outputFrame = CSMOutputFrame()
        outputFrame.setDataFromDict(outputDataDict)
        return outputFrame


    def _calculateDeltaDelta(self, data):
        """
        :param data: 2D array containing A and B coordinates to measure.
        e.g.: for two HN peaks data will be array [[  8.15842 123.49895][  8.17385 123.98413]]
        :return: float
        """
        deltaDeltas = []
        origin = data[0] # first set of positions (any dimensionality)
        for coord in data[1:]:# the other set of positions (same dim as origin)
            dd = lf.euclideanDistance_func(origin, coord, self._alphaFactors)
            deltaDeltas.append(dd)
        deltaDelta = np.mean(deltaDeltas) # mean but could be an option to be a sum
        return deltaDelta


class OneSiteBindingModel(FittingModelABC):
    """
    ChemicalShift Analysis: One Site-Binding Curve calculation model
    """
    ModelName = sv.ONE_BINDING_SITE_MODEL
    Info = 'Fit data to using the One-Binding-Site model.'
    Description = ' ... '
    References = '''
                    1) Eq. (x) M.P. Williamson. Progress in Nuclear Magnetic Resonance Spectroscopy 73, 1–16 (2013).
                    2) ....
                    
                  '''


    def fitSeries(self, inputData:TableFrame, *args, **kwargs) -> TableFrame:
        pass




class FractionBindingModel(MinimiserModel):
    """A model based on the fraction bound Fitting equation.
      Eq. 6 from  M.P. Williamson. Progress in Nuclear Magnetic Resonance Spectroscopy 73, 1–16 (2013).
    """

    FITTING_FUNC = lf.fractionBound_func

    def __init__(self, independent_vars=['x'], prefix='', nan_policy='raise', **kwargs):
        kwargs.update({'prefix': prefix, 'nan_policy': nan_policy, 'independent_vars': independent_vars})
        super().__init__(FractionBindingModel.FITTING_FUNC, **kwargs)

    def guess(self, data, x, **kwargs):
        """Estimate initial model parameter values from data."""
        raise NotImplementedError()


class Simple1SiteModel(MinimiserModel):
    """A model based on the oneSiteBindingCurve Fitting equation.
    """

    FITTING_FUNC = lf.oneSiteBinding_func

    def __init__(self, independent_vars=['x'], prefix='', nan_policy='raise', **kwargs):
        kwargs.update({'prefix': prefix, 'nan_policy': nan_policy, 'independent_vars': independent_vars})
        super().__init__(Simple1SiteModel.FITTING_FUNC, **kwargs)

    def guess(self, data, x, **kwargs):
        """Estimate initial model parameter values from data."""
        raise NotImplementedError()




def _registerChemicalShiftMappingModels():
    """
    Register the ChemicalShiftMapping specific Models
    """
    from ccpn.framework.lib.experimentAnalysis.ChemicalShiftMappingAnalysisBC import ChemicalShiftMappingAnalysisBC
    models = [DeltaDeltaCalculation]
    _registerModels(ChemicalShiftMappingAnalysisBC, models)
