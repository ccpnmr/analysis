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


from abc import ABC, abstractmethod
from ccpn.util.OrderedSet import OrderedSet
from ccpn.core.DataTable import TableFrame



class SeriesAnalysisABC(ABC):
    """
    The top level class for SeriesAnalysis modules.
    """

    seriesAnalysisName = ''
    fittingModels = OrderedSet()

    @classmethod
    def inputData(cls) -> TableFrame:
        """
        Get the attached input table
        """
        pass

    @classmethod
    def outputData(cls) -> TableFrame:
        """
        Get the attached output table
        """
        pass

    @classmethod
    def fit(self, data) -> TableFrame:
        """
        ovveride on custom implementation
        :param data: TableFrame
        :return: TableFrame
        """
        return data

    @classmethod
    def registerFittingModel(cls, fittingModel):
        """
        A method to register a FittingModel object.
        See the FittingModelABC for more information
        """
        from ccpn.framework.lib.experimentAnalysis.FittingModelABC import FittingModelABC
        if not isinstance(fittingModel, FittingModelABC):
            raise ValueError(f'The provided {fittingModel} is not of instance {FittingModelABC}.')
        cls.fittingModels.add(fittingModel)

    @classmethod
    def deRegisterFittingModel(cls, fittingModel):
        """
        A method to de-register a fitting Model
        """
        cls.fittingModels.discard(fittingModel)

    def getFittingModelByName(self, modelName):
        """
        Convenient method to get a registered FittingModel Object  by its name
        :param modelName: str
        :return:
        """
        for fittingModel in self.fittingModels:
            if fittingModel.ModelName == modelName:
                return fittingModel

    @classmethod
    def exportToFile(cls, path, fileType, *args, **kwargs):
        """
        A method to export to an external File
        """
        pass

    def __init__(self):
        pass

    def __str__(self):
        return f'<{self.__class__.__name__}: {self.seriesAnalysisName}>'

    __repr__ = __str__



