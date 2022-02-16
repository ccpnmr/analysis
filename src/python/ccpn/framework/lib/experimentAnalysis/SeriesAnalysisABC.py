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
__dateModified__ = "$dateModified: 2022-02-16 11:55:11 +0000 (Wed, February 16, 2022) $"
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
from ccpn.util.OrderedSet import OrderedSet
from ccpn.core.DataTable import DataTable
from ccpn.core.SpectrumGroup import SpectrumGroup
from collections import defaultdict
import ccpn.framework.lib.experimentAnalysis.SeriesAnalysisVariables as sv

class SeriesAnalysisABC(ABC):
    """
    The top level class for SeriesAnalysis modules.
    """

    seriesAnalysisName = ''
    fittingModels = OrderedSet()

    @property
    def inputDataTables(self, ) -> list:
        """
        Get the attached input DataTables
        Lists of DataTables.
        Add decorator to ensure the input dataFrame is of the write type as in the subclass.
        (especially when restoring a project)
        """
        return list(self._inputDataTables)


    def addInputDataTable(self, dataTable):
        """
        Add a DataTable as inputData
        """
        self._inputDataTables.add(dataTable)


    def getOutputDataTable(self, seriesFrameType:str=None):
        """
        Get the attached Lists of DataTables using SeriesFrame with Output format.
        """
        dataTablesByDataType = defaultdict(list)
        for dataTable in self._outputDataTables:
            seriesFrame = dataTable.data
            if dataTable.data:
                if hasattr(seriesFrame, sv.SERIESFRAMETYPE):
                    dataTablesByDataType[seriesFrame.SERIESFRAMETYPE].append(dataTable)
        if seriesFrameType:
            dataTablesByDataType.get(seriesFrameType)
        else:
            return list(dataTablesByDataType.values())

    def _fetchOutputDataTable(self, name=None, seriesFrameType=None, overrideExisting=True):
        """
        Interanl. Called after 'fit()' to get a valid Datatable to attach the fitting output SeriesFrame
        :param seriesFrameType: str,  A filtering serieFrameType.
        :param overrideExistingOutput: True, to get last available dataTable. False, to create always a new one
        :return: DataTable
        """
        dataTable = None
        if overrideExisting:
            dataTables = self.getOutputDataTable(seriesFrameType)
            if dataTables:
                dataTable = dataTables[-1]
        if not dataTable:
            dataTable = self.project.newDataTable(name)
        return dataTable

    def addOutputData(self, dataTable):
        self._outputDataTables.add(dataTable)

    def removeOutputData(self, dataTable):
        self._outputDataTables.discard(dataTable)


    @classmethod
    def fit(self, *args, **kwargs):
        """
        ovveride on custom implementation
        :param args:
        :param kwargs:
        :return: None
            kwargs
            =======================
            fittingModels:  list of fittingModel classes (not initialised).
                            So to use only the specif given, rather that all available.
            overrideOutputDataTables: bool, True to rewrite the output result in the last available dataTable.
                                    When multiple fittingModels are available, each will output in a different dataTable
                                    according to its definitions.

        """
        # TODO add logger system with params used in calculations
        pass

    @classmethod
    def registerFittingModel(cls, fittingModel):
        """
        A method to register a FittingModel object.
        See the FittingModelABC for more information
        """
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
        dd = {model.ModelName:model for model in self.fittingModels}
        return dd.get(modelName, None)


    @staticmethod
    def newDataTableFromSpectrumGroup(spectrumGroup:SpectrumGroup, seriesTableType:str,
                                      thePeakProperty:str, dataTableName:str=None, **kwargs):
        """
        :param spectrumGroup: object of type SpectrumGroup
        :param seriesTableType: str, One of sv.INPUT_SERIESFRAME_TYPES e.g.: sv.RELAXATION_INPUT_FRAME
        :param dataTableName: str, name for a newData table object. Autogenerated if none
        :param kwargs:
        :return:
        """
        from ccpn.framework.lib.experimentAnalysis.SeriesTablesBC import SeriesFrameBC
        if not isinstance(spectrumGroup, SpectrumGroup):
            raise TypeError(f'spectrumGroup argument must be a SpectrumGroup Type. Given: {type(spectrumGroup)}')

        project = spectrumGroup.project
        seriesFrame = SeriesFrameBC()
        seriesFrame.buildFromSpectrumGroup(spectrumGroup, thePeakProperty)
        dataTable = project.newDataTable(name=dataTableName, data=seriesFrame)
        return dataTable

    @classmethod
    def exportToFile(cls, path, fileType, *args, **kwargs):
        """
        A method to export to an external File
        """
        pass

    def __init__(self, application):

        self.application = application
        self.project = self.application.project
        self._inputDataTables = OrderedSet()
        self._outputDataTables = OrderedSet()



    def __str__(self):
        return f'<{self.__class__.__name__}: {self.seriesAnalysisName}>'

    __repr__ = __str__



