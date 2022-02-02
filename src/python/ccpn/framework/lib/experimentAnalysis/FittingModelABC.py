"""
This module defines base classes for Series Analysis
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2022"
__credits__ = ("Ed Brooksbank, Joanna Fox, Victoria A Higman, Luca Mureddu, Eliza Płoskoń",
               "Timothy J Ragan, Brian O Smith, Gary S Thompson & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Luca Mureddu $"
__dateModified__ = "$dateModified: 2022-02-02 19:07:11 +0000 (Wed, February 02, 2022) $"
__version__ = "$Revision: 3.0.4 $"
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


class FittingModelABC(ABC):
    """
    The top level class for the FittingModel Object.

    # TODO: think about if required input/out ColumnDefinitions,  input/output ColumnFormats
    """

    ModelName = ''      # The Model name.
    Info = ''           # A brief description of the fitting model.
    Description = ''    # A simplified representation of the used equation(s).
    References = ''     # A list of journal article references. E.g.: DOIs or title/authors/year/journal; web-pages.

    @abstractmethod
    def fit(self, inputData:TableFrame, *args, **kwargs) -> TableFrame:
        """
        :param inputData: a TableFrame containing all necessary data for the fitting calculations
        :return: an output TableFrame with fitted data
        """
        pass

    def __init__(self):
        pass

    def __str__(self):
        return f'<{self.__class__.__name__}: {self.ModelName}>'

    __repr__ = __str__



class T1FittingModel(FittingModelABC):
    """
    Relaxation Analysis top class modules.
    """
    ModelName = 'T1'

    def fit(self, inputData:TableFrame, *args, **kwargs) -> TableFrame:
        pass
