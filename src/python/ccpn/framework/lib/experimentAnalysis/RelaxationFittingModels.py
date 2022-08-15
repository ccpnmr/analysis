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
__dateModified__ = "$dateModified: 2022-08-15 16:47:20 +0100 (Mon, August 15, 2022) $"
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


#####################################################
###########        Minimisers        ################
#####################################################

class _RelaxationBaseMinimiser(MinimiserModel):
    """
    A base model for T1/T2
    """
    AMPLITUDEstr = sv.AMPLITUDE # They must be exactly as they are defined in the FITTING_FUNC arguments! This was too hard to change!
    DECAYstr = sv.DECAY
    _defaultParams = {
                        AMPLITUDEstr:1,
                        DECAYstr:0.5
                      }

    def __init__(self, independent_vars=['x'], prefix='', nan_policy=sv.OMIT_MODE, **kwargs):
        kwargs.update({'prefix': prefix, 'nan_policy': nan_policy, 'independent_vars': independent_vars})
        super().__init__(T1Minimiser.FITTING_FUNC, **kwargs)
        self.name = self.MODELNAME
        self.amplitude = None  # this will be a Parameter Obj . Set on the fly by the minimiser while inspecting the Fitting Func signature
        self.decay = None  # this will be a Parameter Obj
        self.params = self.make_params(**self._defaultParams)

    def guess(self, data, x, **kws):
        """
        :param data: y values 1D array
        :param x: the x axis values. 1D array
        :param kws:
        :return: dict of params needed for the fitting
        """
        params = self.params
        minDecay = np.min(x)
        maxDecay = np.max(x) + (np.max(x) * 0.5)
        if minDecay == maxDecay == 0:
            getLogger().warning(f'Fitting model min==max {minDecay}, {maxDecay}')
            minDecay = -1
        params.get(self.DECAYstr).value = np.mean(x)
        params.get(self.DECAYstr).min = minDecay
        params.get(self.DECAYstr).max = maxDecay
        params.get(self.AMPLITUDEstr).value = np.mean(data)
        params.get(self.AMPLITUDEstr).min = 0.001
        params.get(self.AMPLITUDEstr).max = np.max(data) + (np.max(data) * 0.5)
        return params

class T1Minimiser(_RelaxationBaseMinimiser):
    """
    A model based on the T1 fitting function.
    """
    FITTING_FUNC = lf.T1_func
    MODELNAME = 'T1_Model'


class T2Minimiser(_RelaxationBaseMinimiser):
    """
    A model based on the T2 fitting function.
    """
    FITTING_FUNC = lf.T2_func


#####################################################
###########       FittingModel       ################
#####################################################

class _RelaxationBaseFittingModel(FittingModelABC):
    """
    A Base model class for T1/T2
    """
    PeakProperty = 'height'

    def fitSeries(self, inputData:TableFrame, rescale=True, *args, **kwargs) -> TableFrame:
        """
        :param inputData:
        :param rescale:
        :param args:
        :param kwargs:
        :return:
        """
        getLogger().warning(sv.UNDER_DEVELOPMENT_WARNING)
        ## Keep only one IsotopeCode as we are using only Height/Volume
        inputData = inputData[inputData[sv.ISOTOPECODE] == inputData[sv.ISOTOPECODE].iloc[0]]
        grouppedByCollectionsId = inputData.groupby([sv.COLLECTIONID])
        for collectionId, groupDf in grouppedByCollectionsId:
            groupDf.sort_values([sv.SERIESSTEP], inplace=True)
            seriesSteps = groupDf[sv.SERIESSTEP]
            seriesValues = groupDf[sv._HEIGHT]
            xArray = seriesSteps.values
            yArray = seriesValues.values

            minimiser = self.Minimiser()
            try:
                params = minimiser.guess(yArray, xArray)
                result = minimiser.fit(yArray, params, x=xArray)
            except:
                getLogger().warning(f'Fitting Failed for collectionId: {collectionId} data.')
                params = minimiser.params
                result = MinimiserResult(minimiser, params)
            inputData.loc[collectionId, sv.MODEL_NAME] = self.ModelName
            inputData.loc[collectionId, sv.MINIMISER_METHOD] = minimiser.method
            for ix, row in groupDf.iterrows():
                for resultName, resulValue in result.getAllResultsAsDict().items():
                    inputData.loc[ix, resultName] = resulValue
        return inputData

class T1FittingModel(_RelaxationBaseFittingModel):
    """
    T1 model class containing fitting equations
    """
    ModelName   = sv.T1
    Info        = '''
                  '''
    Description = '''
                  '''
    References  = '''
                  '''
    Minimiser = T1Minimiser
    MaTex = ''

class T2FittingModel(_RelaxationBaseFittingModel):
    """
    T2 model class containing fitting equations
    """
    ModelName   = sv.T2
    Info        = '''
                  '''
    Description = ''''''
    References  = '''
                  '''
    Minimiser = T2Minimiser
    MaTex = ''


#####################################################
###########      Register models    #################
#####################################################

RELAXATION_MODELS_DICT = {
    sv.T1 : T1FittingModel,
    sv.T2 : T2FittingModel,
    }


def _registerFittingModels():
    from ccpn.framework.lib.experimentAnalysis.RelaxationAnalysisBC import RelaxationAnalysisBC
    models = [T2FittingModel]#, T2FittingModel]
    for model in models:
        RelaxationAnalysisBC.registerFittingModel(model)
    return models

