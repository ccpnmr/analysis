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

from typing import List, Union, Sequence
from abc import ABC, abstractmethod
from ccpn.util.OrderedSet import OrderedSet
from ccpn.core.DataTable import TableFrame
import ccpn.framework.lib.experimentAnalysis.SeriesAnalysisVariables as sv
import numpy as np
from lmfit import Model
from lmfit.models import update_param_vals
import lmfit.lineshapes as func

gaussian_func    = func.gaussian
lorentzian_func  = func.lorentzian
linear_func      = func.linear
parabolic_func   = func.parabolic
exponential_func = func.exponential
lognormal_func   = func.lognormal
pearson7_func    = func.pearson7
students_t_func  = func.students_t
powerlaw_func    = func.powerlaw




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







