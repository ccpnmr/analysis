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
__dateModified__ = "$dateModified: 2022-08-15 11:37:34 +0100 (Mon, August 15, 2022) $"
__version__ = "$Revision: 3.1.0 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Luca Mureddu $"
__date__ = "$Date: 2022-02-02 14:08:56 +0000 (Wed, February 02, 2022) $"
#=========================================================================================
# Start of code
#=========================================================================================

from ccpn.core.DataTable import TableFrame
import ccpn.framework.lib.experimentAnalysis.SeriesAnalysisVariables as sv
from ccpn.framework.lib.experimentAnalysis.FittingModelABC import FittingModelABC, MinimiserModel, MinimiserResult
from ccpn.framework.lib.experimentAnalysis.SeriesTablesBC import RelaxationOutputFrame, _getOutputFrameFromInputFrame
from ccpn.util.Logging import getLogger
import numpy as np
from collections import defaultdict
from lmfit.models import update_param_vals
import ccpn.framework.lib.experimentAnalysis.fitFunctionsLib as lf



###############################################################
###########  T2 Relaxation Minimiser/Fitting Models   #########
###############################################################

class ExponentialModel(MinimiserModel):
    """
    A model based on an exponential decay function.
    """

    FITTING_FUNC = lf.exponential_func

    def __init__(self, independent_vars=['x'], prefix='', nan_policy=sv.OMIT_MODE, **kwargs):
        kwargs.update({'prefix': prefix, 'nan_policy': nan_policy, 'independent_vars': independent_vars})
        super().__init__(ExponentialModel.FITTING_FUNC, **kwargs)

    def guess(self, data, x, **kws):
        """
        :param data: y values 1D array
        :param x: the x axis values. 1D array
        :param kws:
        :return: dict of params needed for the fitting
        """
        params = self.make_params(amplitude=max(data), decay=np.mean(x))
        params['amplitude'].min = min(data)
        params['amplitude'].max = max(data) + max(data) * 0.5
        params['decay'].min = min(x)
        params['decay'].max = max(x) + max(x) * 0.5
        return params


class T2FittingModel(FittingModelABC):
    """
    T2 model class containing fitting equations
    """
    ModelName   = sv.T2

    Info        = '''
                  A model based on an exponential decay function.
                  The model has two Parameters: `amplitude` (`A`) and `decay` (`tau`)
                  '''
    Description = ''' A * e^{ -x / tau }'''
    References  = '''
                  1) https://en.wikipedia.org/wiki/Exponential_decay
                  '''

    Minimiser = ExponentialModel

    def fitSeries(self, inputData: TableFrame, rescale=True, *args, **kwargs) -> TableFrame:

        getLogger().warning(sv.UNDER_DEVELOPMENT_WARNING)
        xArray = np.array(inputData.SERIESSTEPS)
        minimiserResults = []
        outputFrame = _getOutputFrameFromInputFrame(inputData, outputFrameType=RelaxationOutputFrame)
        for ix, row in inputData.iterrows():
            seriesValues = row[inputData.valuesHeaders]
            yArray = seriesValues.values
            modelMinimiser = self.Minimiser()
            modelMinimiser.label = row[sv._ROW_UID]
            params = modelMinimiser.guess(yArray, xArray)
            try:
                minimiserResult = modelMinimiser.fit(yArray, params, x=xArray)
            except:
                getLogger().warning(f'Fitting Failed for: {row[sv._ROW_UID]} data.')
                minimiserResult = MinimiserResult(modelMinimiser, params, method=modelMinimiser.method)
            minimiserResults.append(minimiserResult)

        return outputFrame

###############################################################
###########  T2 Relaxation Minimiser/Fitting Models   #########
###############################################################

class T1Model(MinimiserModel):
    """
    A model based on an exponential decay function.
    """

    FITTING_FUNC = lf.T1_func

    def __init__(self, independent_vars=['x'], prefix='', nan_policy=sv.OMIT_MODE, **kwargs):
        kwargs.update({'prefix': prefix, 'nan_policy': nan_policy, 'independent_vars': independent_vars})
        super().__init__(ExponentialModel.FITTING_FUNC, **kwargs)

    def guess(self, data, x, **kws):
        """
        :param data: y values 1D array
        :param x: the x axis values. 1D array
        :param kws:
        :return: dict of params needed for the fitting
        """
        params = self.make_params(amplitude=max(data), decay=np.mean(x))
        params['amplitude'].min = min(data)
        params['amplitude'].max = max(data) + max(data) * 0.5
        params['decay'].min = min(x)
        params['decay'].max = max(x) + max(x) * 0.5
        return params

class T1FittingModel(FittingModelABC):
    """
    T2 model class containing fitting equations
    """
    ModelName   = sv.T1

    Info        = '''
                  The model has two Parameters: `amplitude` (`A`) and `decay` (`tau`)
                  '''
    Description = ''' A *(1- e^{-x / tau })'''
    References  = '''
                  '''
    Minimiser = T1Model

    def fitSeries(self, inputData: TableFrame, rescale=True, *args, **kwargs) -> TableFrame:
        """Perform the fitting routine to the input DataTable. Return an output dataTable"""
        getLogger().warning(sv.UNDER_DEVELOPMENT_WARNING)
        xArray = np.array(inputData.SERIESSTEPS)
        minimiserResults = []
        outputFrame = _getOutputFrameFromInputFrame(inputData, outputFrameType=RelaxationOutputFrame)
        for ix, row in inputData.iterrows():
            seriesValues = row[inputData.valuesHeaders]
            yArray = seriesValues.values
            modelMinimiser = self.Minimiser()
            modelMinimiser.label = row[sv._ROW_UID]
            params = modelMinimiser.guess(yArray, xArray)
            try:
                minimiserResult = modelMinimiser.fit(yArray, params, x=xArray)
            except:
                getLogger().warning(f'Fitting Failed for: {row[sv._ROW_UID]} data.')
                minimiserResult = MinimiserResult(modelMinimiser, params, method=modelMinimiser.method)
            minimiserResults.append(minimiserResult)
        return outputFrame


#####################################################
###########      Register models    #################
#####################################################

RELAXATION_MODELS_DICT = {
    sv.T1 : T1FittingModel,
    sv.T2 : T2FittingModel,
    }


def _registerFittingModels():
    from ccpn.framework.lib.experimentAnalysis.RelaxationAnalysisBC import RelaxationAnalysisBC
    models = [T1FittingModel, T2FittingModel]
    for model in models:
        RelaxationAnalysisBC.registerFittingModel(model)
    return models

