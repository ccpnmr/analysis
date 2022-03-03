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
__dateModified__ = "$dateModified: 2022-03-03 16:41:37 +0000 (Thu, March 03, 2022) $"
__version__ = "$Revision: 3.1.0 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Luca Mureddu $"
__date__ = "$Date: 2022-02-02 14:08:56 +0000 (Wed, February 02, 2022) $"
#=========================================================================================
# Start of code
#=========================================================================================

from abc import ABC, abstractmethod
from ccpn.core.DataTable import TableFrame
from lmfit import Model
from lmfit.model import ModelResult
import ccpn.framework.lib.experimentAnalysis.fitFunctionsLib as lf
import ccpn.framework.lib.experimentAnalysis.SeriesAnalysisVariables as sv
from copy import deepcopy

class FittingModelABC(ABC):
    """
    The top level class for the FittingModel Object.
    """

    ModelName = ''      # The Model name.
    Info = ''           # A brief description of the fitting model.
    Description = ''    # A simplified representation of the used equation(s).
    References = ''     # A list of journal article references. E.g.: DOIs or title/authors/year/journal; web-pages.
    Minimiser = None
    
    @abstractmethod
    def fitSeries(self, inputData:TableFrame, *args, **kwargs) -> TableFrame:
        """
        :param inputData: a TableFrame containing all necessary data for the fitting calculations
        :return: an output TableFrame with fitted data
        """
        pass
    

    def __str__(self):
        return f'<{self.__class__.__name__}: {self.ModelName}>'

    __repr__ = __str__


def _registerModels(cls, fittingModels):
    """
    INTERNAL
    Register the FittingModel class (not-initialised) in the respective Experiment Analysis BaseClass
    :param cls: Experiment Analysis BaseClass e.g.: ChemicalShiftMappingAnalysisBC
    :param fittingModels: list of FittingModels to add to the cls
    :return: None
    """
    for model in fittingModels:
        cls.registerFittingModel(model)


class MinimiserModel(Model):
    """
    The lower base class for the fitting minimisation routines.
    Based on the package LMFIT.
    Called for each row in the input SeriesDataTable.


    Parameters
    ----------
    independent_vars : :obj:`list` of :obj:`str`, optional
        Arguments to the model function that are independent variables
        default is ['x']).
    prefix : str, optional
        String to prepend to parameter names, needed to add two Models
        that have parameter names in common.
    nan_policy : {'raise', 'propagate', 'omit'}, optional
        How to handle NaN and missing values in data. See Notes below.
    **kwargs : optional
        Keyword arguments to pass to :class:`Model`.
    Notes
    -----
    1. `nan_policy` sets what to do when a NaN or missing value is seen in
    the data. Should be one of:
        - `'raise'` : raise a `ValueError` (default)
        - `'propagate'` : do nothing
        - `'omit'` : drop missing data

    usage example:

    """
    FITTING_FUNC = None
    MODELNAME = 'Minimiser'

    def fit(self, data, params=None, weights=None, method='leastsq', iter_cb=None, scale_covar=True, verbose=False,
            fit_kws=None, nan_policy='omit', calc_covar=True, max_nfev=None, **kwargs):

        result = super().fit(data, params=params, weights=weights, method=method,
            iter_cb=iter_cb, scale_covar=scale_covar, verbose=verbose, fit_kws=fit_kws,
            nan_policy=nan_policy, calc_covar=calc_covar, max_nfev=max_nfev, **kwargs)

        # insert the r2 definition. Might be better to subclass the output model and add it implicitly.
        result.r2 = None
        if result.redchi is not None:
            result.r2 = lf.r2_func(redchi=result.redchi, y=data)
        return result


    def guess(self, data, x, **kws):
        pass


class MinimiserResult(ModelResult):
    """Result from the Model fit.

       This has many attributes and methods for viewing and working with the
       results of a fit using Model. It inherits from Minimizer, so that it
       can be used to modify and re-run the fit for the Model.

       """

    def __init__(self, model, params, data=None, weights=None,
                 method=sv.LEASTSQ, fcn_args=None, fcn_kws=None,
                 iter_cb=None, scale_covar=True, nan_policy='omit',
                 calc_covar=True, max_nfev=None, **fit_kws):
        """
        Parameters
        ----------
        model : Model
            Model to use.
        params : Parameters
            Parameters with initial values for model.
        data : array_like, optional
            Data to be modeled.
        weights : array_like, optional
            Weights to multiply ``(data-model)`` for fit residual.
        method : str, optional
            Name of minimization method to use (default is `'leastsq'`).
        fcn_args : sequence, optional
            Positional arguments to send to model function.
        fcn_dict : dict, optional
            Keyword arguments to send to model function.
        iter_cb : callable, optional
            Function to call on each iteration of fit.
        scale_covar : bool, optional
            Whether to scale covariance matrix for uncertainty evaluation.
        nan_policy : {'raise', 'propagate', 'omit'}, optional
            What to do when encountering NaNs when fitting Model.
        calc_covar : bool, optional
            Whether to calculate the covariance matrix (default is True)
            for solvers other than `'leastsq'` and `'least_squares'`.
            Requires the ``numdifftools`` package to be installed.
        max_nfev : int or None, optional
            Maximum number of function evaluations (default is None). The
            default value depends on the fitting method.
        **fit_kws : optional
            Keyword arguments to send to minimization routine.

        """
        self.r2 = None

        super().__init__( model, params, data=data, weights=weights,
                 method=method, fcn_args=fcn_args, fcn_kws=fcn_kws,
                 iter_cb=iter_cb, scale_covar=scale_covar, nan_policy=nan_policy,
                 calc_covar=calc_covar, max_nfev=max_nfev, **fit_kws)
