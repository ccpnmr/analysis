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
__dateModified__ = "$dateModified: 2022-07-18 18:59:32 +0100 (Mon, July 18, 2022) $"
__version__ = "$Revision: 3.1.0 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Luca Mureddu $"
__date__ = "$Date: 2022-02-02 14:08:56 +0000 (Wed, February 02, 2022) $"
#=========================================================================================
# Start of code
#=========================================================================================

from abc import ABC
from collections import defaultdict
from ccpn.util.OrderedSet import OrderedSet
from ccpn.core.SpectrumGroup import SpectrumGroup
from ccpn.util.Common import flattenLists
import ccpn.framework.lib.experimentAnalysis.SeriesAnalysisVariables as sv
from ccpn.framework.Application import getApplication, getCurrent, getProject
from ccpn.framework.lib.experimentAnalysis.SeriesTablesBC import SeriesFrameBC, InputSeriesFrameBC, ALL_SERIES_DATA_TYPES

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

    @inputDataTables.setter
    def inputDataTables(self, values):
        self._inputDataTables = OrderedSet(values)

    def addInputDataTable(self, dataTable):
        """
        Add a DataTable as inputData
        """
        self._inputDataTables.add(dataTable)

    def clearInputDataTables(self):
        """
        Remove all  DataTable as inputData
        """
        self._inputDataTables = OrderedSet()

    def getOutputDataTables(self, seriesFrameType:str=None):
        """
        Get the attached Lists of DataTables using SeriesFrame with Output format.
        """
        dataTablesByDataType = defaultdict(list)
        for dataTable in self._outputDataTables:
            seriesFrame = dataTable.data
            if dataTable.data is not None:
                if hasattr(seriesFrame, sv.SERIESFRAMETYPE):
                    dataTablesByDataType[seriesFrame.SERIESFRAMETYPE].append(dataTable)
        if seriesFrameType:
            return flattenLists(dataTablesByDataType.get(seriesFrameType))
        else:
            return flattenLists(list(dataTablesByDataType.values()))

    def _fetchOutputDataTable(self, name=None, overrideExisting=True):
        """
        Interanl. Called after 'fit()' to get a valid Datatable to attach the fitting output SeriesFrame
        :param seriesFrameType: str,  A filtering serieFrameType.
        :param overrideExistingOutput: True, to get last available dataTable. False, to create always a new one
        :return: DataTable
        """
        dataTable = None
        if overrideExisting:
            dataTable = self.project.getDataTable(name)
        if not dataTable:
            dataTable = self.project.newDataTable(name)
        return dataTable

    def addOutputData(self, dataTable):
        self._outputDataTables.add(dataTable)

    def removeOutputData(self, dataTable):
        self._outputDataTables.discard(dataTable)

    def _setDataType(self, dataTables, theType):
        """set the dataTable.data (dataFrame) to the given type.
         Used when restored project lost the dataTable.data Type """
        for dataTable in dataTables:
            if not isinstance(dataTable.data, theType):
                dataTable.data.__class__ = theType


    @classmethod
    def fitInputData(self, *args, **kwargs):
        """
        override on custom implementation
        :param args:
        :param kwargs:
        :return: None
            kwargs
            =======================
            :key: outputName: outputDataTable name
            :key: fittingModels:  list of fittingModel classes (not initialised).
                            So to use only the specif given, rather that all available.
            :key: overrideOutputDataTables: bool, True to rewrite the output result in the last available dataTable.
                                    When multiple fittingModels are available, each will output in a different dataTable
                                    according to its definitions.

        """
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

    def newInputDataTableFromSpectrumGroup(self, spectrumGroup:SpectrumGroup, peakListIndices=None, dataTableName:str=None):
        """
        :param spectrumGroup: object of type SpectrumGroup
        :param dataTableName: str, name for a newData table object. Autogenerated if none
        :param peakListIndices: list of int, same length of spectra. Define which peakList index to use.
                               If None, use -1 (last created) as default for all spectra
        :return:
        """
        if not isinstance(spectrumGroup, SpectrumGroup):
            raise TypeError(f'spectrumGroup argument must be a SpectrumGroup Type. Given: {type(spectrumGroup)}')
        project = spectrumGroup.project
        seriesFrame = InputSeriesFrameBC()
        seriesFrame.buildFromSpectrumGroup(spectrumGroup, peakListIndices=peakListIndices)
        dataTable = project.newDataTable(name=dataTableName, data=seriesFrame)
        self._setRestoringMetadata(dataTable, seriesFrame, spectrumGroup)
        return dataTable

    def newCollectionsFromSpectrumGroup(self, spectrumGroup:SpectrumGroup, peakListIndices=None):
        """
        :param spectrumGroup: object of type SpectrumGroup
        :param dataTableName: str, name for a newData table object. Autogenerated if none
        :param peakListIndices: list of int, same length of spectra. Define which peakList index to use.
                             If None, use -1 (last created) as default for all spectra
        :return: a list of collections
        """
        from ccpn.core.lib.PeakCollectionLib import createCollectionsFromSpectrumGroup
        if not isinstance(spectrumGroup, SpectrumGroup):
            raise TypeError(f'spectrumGroup argument must be a SpectrumGroup Type. Given: {type(spectrumGroup)}')
        collections = createCollectionsFromSpectrumGroup(spectrumGroup, peakListIndices)
        return collections

    @staticmethod
    def _setRestoringMetadata(dataTable, seriesFrame, spectrumGroup):
        """ set the metadata needed for restoring the object"""
        dataTable.setMetadata(spectrumGroup.className, spectrumGroup.pid)
        dataTable.setMetadata(sv.SERIESFRAMETYPE, seriesFrame.SERIESFRAMETYPE)

    def _restoreInputDataTableData(self, dataTable):
        """
        Reset variables and Obj type after restoring a project from its metadata.
        :return: dataTable
        """
        spectrumGroupPid = dataTable.metadata.get(SpectrumGroup.className, None)
        spectrumGroup = self.project.getByPid(spectrumGroupPid)
        dataTypeStr = dataTable.metadata.get(sv.SERIESFRAMETYPE, None)
        dataType = ALL_SERIES_DATA_TYPES.get(dataTypeStr, InputSeriesFrameBC)
        data = dataTable.data
        if spectrumGroup and data is not None:
            data.__class__ = dataType
        return dataTable

    @classmethod
    def exportToFile(cls, path, fileType, *args, **kwargs):
        """
        A method to export to an external File
        """
        pass

    def plotResults(self, *args, **kwargs):
        pass


    def __init__(self):

        self.project = getProject()
        self.application = getApplication()
        self.current = getCurrent()
        self._inputDataTables = OrderedSet()
        self._outputDataTables = OrderedSet()
        self._needsRefitting = False

    def __str__(self):
        return f'<{self.__class__.__name__}: {self.seriesAnalysisName}>'

    __repr__ = __str__


class GroupingNmrAtomABC(ABC):
    """
    Class for defining grouping nmrAtoms in a seriesAnalysis
    """

    groupType = None
    groupInfo = None
    nmrAtomNames = None
    excludeResidueTypes = None
    includedResidueTypes = None

    def __init__(self):
        pass

    def _getResidueFullName(self):
        pass

    def __str__(self):
        return f'<{self.__class__.__name__}: {self.groupType}>'

    __repr__ = __str__


class GroupingBackboneNmrAtoms(GroupingNmrAtomABC):

    groupType = 'Backbone'
    groupInfo = 'Follow the backbone atoms in a series Analysis'
    nmrAtomNames = ['H', 'N', 'CA', 'C', 'HA',]
    excludeResidueTypes = ['Proline']
    includedResidueTypes = None

class GroupingSideChainNmrAtoms(GroupingNmrAtomABC):

    groupType = 'SideChain'
    groupInfo = 'Follow the SideChain atoms in a series Analysis'
    nmrAtomNames = []
    excludeResidueTypes = ['Glycine']
    includedResidueTypes = None

class GroupingBBandSSNmrAtoms(GroupingNmrAtomABC):

    groupType = 'Backbone+SideChain'
    groupInfo = 'Follow the Backbone and SideChain atoms in a series Analysis'
    nmrAtomNames = GroupingBackboneNmrAtoms.nmrAtomNames+GroupingSideChainNmrAtoms.nmrAtomNames
    excludeResidueTypes = GroupingBackboneNmrAtoms.excludeResidueTypes+GroupingSideChainNmrAtoms.excludeResidueTypes
    includedResidueTypes = None

class GroupingMethylNmrAtoms(GroupingNmrAtomABC):

    groupType = 'Methyl'
    groupInfo = 'Follow the Methyl atoms in a series Analysis'
    nmrAtomNames = []
    excludeResidueTypes = None
    includedResidueTypes = ['Alanine', 'Leucine', 'Valine', 'Isoleucine', 'Threonine', 'Methionine']

class GroupingCustomNmrAtoms(GroupingNmrAtomABC):

    groupType = 'Custom'
    groupInfo = 'Follow custom atoms in a series Analysis'
    nmrAtomNames = []
    excludeResidueTypes = None
    includedResidueTypes = None

ALL_GROUPINGNMRATOMS = {
                        GroupingBackboneNmrAtoms.groupType:GroupingBackboneNmrAtoms,
                        GroupingSideChainNmrAtoms.groupType:GroupingSideChainNmrAtoms,
                        GroupingBBandSSNmrAtoms.groupType:GroupingBBandSSNmrAtoms,
                        GroupingMethylNmrAtoms.groupType:GroupingMethylNmrAtoms,
                        GroupingCustomNmrAtoms.groupType:GroupingCustomNmrAtoms
                        }
