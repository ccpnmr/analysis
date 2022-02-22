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
__dateModified__ = "$dateModified: 2022-02-22 16:06:27 +0000 (Tue, February 22, 2022) $"
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
from ccpn.framework.lib.experimentAnalysis.FittingModelABC import FittingModelABC, MinimiserModel
import numpy as np
import lmfit.lineshapes as func
from lmfit.models import update_param_vals


class ExponentialModel(MinimiserModel):
    """A model based on an exponential decay function.
    The model has two Parameters: `amplitude` (:math:`A`) and `decay`
    (:math:`\tau`) and is defined as:
        f(x; A, \tau) = A e^{-x/\tau}
    """

    FITTING_FUNC = func.exponential

    def __init__(self, independent_vars=['x'], prefix='', nan_policy='raise', **kwargs):
        kwargs.update({'prefix': prefix, 'nan_policy': nan_policy, 'independent_vars': independent_vars})
        super().__init__(ExponentialModel.FITTING_FUNC, **kwargs)

    def guess(self, data, x, **kwargs):
        """Estimate initial model parameter values from data."""
        try:
            sval, oval = np.polyfit(x, np.log(abs(data) + 1.e-15), 1)
        except TypeError:
            sval, oval = 1., np.log(abs(max(data) + 1.e-9))
        pars = self.make_params(amplitude=np.exp(oval), decay=-1.0 / sval)
        return update_param_vals(pars, self.prefix, **kwargs)


class T1FittingModel(FittingModelABC):
    """
    T1 model class containing fitting equations
    """
    ModelName   = 'T1'

    Info        = '''
                    A model based on an exponential decay function.
                    The model has two Parameters: `amplitude` (`A`) and `decay` (`\ tau`)
                    '''
    Description = ''' A e^{ -x / \ tau }'''
    References = '''
                    1) https://en.wikipedia.org/wiki/Exponential_decay
                 '''

    Minimiser = ExponentialModel

    def fitSeries(self, inputData:TableFrame, *args, **kwargs) -> TableFrame:
        pass





def _registerChemicalShiftMappingModels():
    from ccpn.framework.lib.experimentAnalysis.RelaxationAnalysisBC import RelaxationAnalysisBC
    models = [T1FittingModel]
    for model in models:
        RelaxationAnalysisBC.registerFittingModel(model)


