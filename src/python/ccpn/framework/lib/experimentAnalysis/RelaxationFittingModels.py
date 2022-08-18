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
__dateModified__ = "$dateModified: 2022-08-18 13:02:01 +0100 (Thu, August 18, 2022) $"
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
    FITTING_FUNC = lf.exponentialDecay_func
    AMPLITUDEstr = sv.AMPLITUDE # They must be exactly as they are defined in the FITTING_FUNC arguments! This was too hard to change!
    DECAYstr = sv.DECAY
    _defaultParams = {
                        AMPLITUDEstr:1,
                        DECAYstr:0.5
                      }


    def __init__(self, independent_vars=['x'], prefix='', nan_policy=sv.RAISE_MODE, **kwargs):
        kwargs.update({'prefix': prefix, 'nan_policy': nan_policy, 'independent_vars': independent_vars})
        super().__init__(lf.exponentialDecay_func, **kwargs)
        self.name = self.MODELNAME
        self.amplitude = None  # this will be a Parameter Obj . Set on the fly by the minimiser while inspecting the Fitting Func signature
        self.decay = None  # this will be a Parameter Obj

    def guess(self, data, x, **kwargs):
        """Estimate initial model parameter values from data."""
        try:
            sval, oval = np.polyfit(x, np.log(abs(data)+1.e-15), 1)
        except TypeError:
            sval, oval = 1., np.log(abs(max(data)+1.e-9))
        params = self.make_params(amplitude=np.exp(oval), decay=-1.0/sval)
        return update_param_vals(params, self.prefix, **kwargs)


class InversionRecoveryMinimiser(_RelaxationBaseMinimiser):
    """
    A model based on the T1 fitting function.
    """
    FITTING_FUNC = lf.inversionRecovery_func
    MODELNAME = 'InversionRecoveryMinimiser'


class ExponentialDecayMinimiser(_RelaxationBaseMinimiser):
    """
    A model based on the Exponential Decay fitting function.
    """
    FITTING_FUNC = lf.exponentialDecay_func
    MODELNAME = 'ExponentialDecayMinimiser'

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
        self._rawData.clear()
        getLogger().warning(sv.UNDER_DEVELOPMENT_WARNING)
        ## Keep only one IsotopeCode as we are using only Height/Volume

        inputData = inputData[inputData[sv.ISOTOPECODE] == inputData[sv.ISOTOPECODE].iloc[0]]
        grouppedByCollectionsId = inputData.groupby([sv.COLLECTIONID])
        for collectionId, groupDf in grouppedByCollectionsId:
            groupDf.sort_values([sv.SERIESSTEP], inplace=True)
            seriesSteps = groupDf[sv.SERIESSTEP]
            seriesValues = groupDf[sv._HEIGHT]
            pid = groupDf[sv.COLLECTIONPID].values[-1]
            xArray = seriesSteps.values
            yArray = seriesValues.values
            self._xRawData = xArray
            self._rawData.append(yArray)
            self._rawIndexes.append(pid)
            if self.applyScaleMinMax:
                yArray = self.scaleMinMax(yArray)
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
        print(self._rawData)
        return inputData

class InversionRecoveryFittingModel(_RelaxationBaseFittingModel):
    """
    InversionRecovery model class containing fitting equation and fitting information
    """
    ModelName   = sv.InversionRecovery
    Info        = '''
                  NIY
                  '''
    Description = '''
                  NIY
                  '''
    References  = '''
                  NIY
                  '''
    Minimiser = InversionRecoveryMinimiser
    MaTex =  r'$amplitude*(1 - e^{-time/decay})$'

class ExponentialDecayFittingModel(_RelaxationBaseFittingModel):
    """
    ExponentialDecay FittingModel model class containing fitting equation and fitting information
    """
    ModelName   = sv.ExponentialDecay
    Info        = '''
                  NIY
                  '''
    Description = '''
                  NIY
                  '''
    References  = '''
                  NIY
                  '''
    Minimiser = ExponentialDecayMinimiser
    MaTex = r'$amplitude *(e^{-time/decay})$'


#####################################################
###########      Register models    #################
#####################################################
Models = [
            ExponentialDecayFittingModel,
            InversionRecoveryFittingModel,
        ]




