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
__dateModified__ = "$dateModified: 2022-08-25 10:13:01 +0100 (Thu, August 25, 2022) $"
__version__ = "$Revision: 3.1.0 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Luca Mureddu $"
__date__ = "$Date: 2022-02-02 14:08:56 +0000 (Wed, February 02, 2022) $"
#=========================================================================================
# Start of code
#=========================================================================================

import numpy as np
from scipy import stats
from abc import ABC
from collections import defaultdict
from ccpn.util.OrderedSet import OrderedSet
from ccpn.util.Logging import getLogger

import ccpn.framework.lib.experimentAnalysis.SeriesAnalysisVariables as sv
from ccpn.core.SpectrumGroup import SpectrumGroup
from ccpn.framework.Application import getApplication, getCurrent, getProject
from ccpn.framework.lib.experimentAnalysis.SeriesTablesBC import SeriesFrameBC, InputSeriesFrameBC, ALL_SERIES_DATA_TYPES
import ccpn.framework.lib.experimentAnalysis.fitFunctionsLib as lf

class SeriesAnalysisABC(ABC):
    """
    The top level class for SeriesAnalysis modules.
    """
    seriesAnalysisName = ''

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

    def getFirstOutputDataFrame(self):
        """Get the first available dataFrame from the outputDataTable. """
        if len(self.inputDataTables) == 0:
            return
        if not self.getOutputDataTables():
            return
        outputDataTable = self.getOutputDataTables()[0]
        return outputDataTable.data

    def getOutputDataTables(self, seriesFrameType:str=None):
        """
        Get the attached Lists of DataTables using SeriesFrame with Output format.
        """
        from ccpn.util.Common import flattenLists # circular imports in common
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

    @property
    def untraceableValue(self) -> float:
        return self._untraceableValue

    @untraceableValue.setter
    def untraceableValue(self, value):
        if isinstance(value, (float, int)):
            self._untraceableValue = value
        else:
            getLogger().warning(f'Impossible to set untraceableValue to {value}. Use type int or float.')

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

    @property
    def currentFittingModel(self):
        """ The working fittingModel in the module.
         E.g.: the initiated ExponentialDecayModel. See models for docs. """
        if self._currentFittingModel is None:
            getLogger().warn('Fitting Model not set.')
            return
        return self._currentFittingModel

    @currentFittingModel.setter
    def currentFittingModel(self, model):
        self._currentFittingModel = model

    @property
    def currentCalculationModel(self):
        """ The working CalculationModel in the module.
        E.g.: the initiated EuclidianModel for ChemicalshiftMapping. See models for docs. """
        if self._currentCalculationModel is None:
            getLogger().warn('CalculationModel not set.')
            return
        return self._currentCalculationModel

    @currentCalculationModel.setter
    def currentCalculationModel(self, model):
        self._currentCalculationModel = model

    def registerModel(self, model):
        """
        A method to register a Model object, either FittingModel or CalculationModel.
        See the FittingModelABC for more information
        """
        from ccpn.framework.lib.experimentAnalysis.FittingModelABC import FittingModelABC, CalculationModel
        if issubclass(model, CalculationModel):
            self.calculationModels.update({model.ModelName: model})
            return
        if issubclass(model, FittingModelABC):
            self.fittingModels.update({model.ModelName: model})
        return

    def deRegisterModel(self, model):
        """
        A method to de-register a  Model
        """
        self.calculationModels.pop(model.ModelName, None)
        self.fittingModels.pop(model.ModelName, None)

    def getFittingModelByName(self, modelName):
        """
        Convenient method to get a registered FittingModel Object  by its name
        :param modelName: str
        :return:
        """
        return self.fittingModels.get(modelName, None)

    def _getFirstModel(self, models):
        """
        Get the first Model in the dict
        :param models: dict of FittingModels or CalculationModels
        :return:
        """
        first = next(iter(models), iter({}))
        model = models.get(first)
        return model



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

    def _getGuiOutputDataFrame(self, dataFrame=None, *args):
        """ internal. Used to get a df to display in GuiTables
         Return the outputDataFrame grouped by Collection IDs.
         """
        # TODO needs more error checking
        if dataFrame is None:
            dataFrame = self.getFirstOutputDataFrame()
        if dataFrame is None:
            return
        if not sv.COLLECTIONID in dataFrame:
            return dataFrame
        ## group by id and keep only first row as all duplicated except the series steps, which are not needed here.
        ## reset index otherwise you lose the column collectionId
        outDataFrame = dataFrame.groupby(sv.COLLECTIONID).first().reset_index()
        outDataFrame[sv._ROW_UID] = np.arange(1, len(outDataFrame)+1)
        outDataFrame[sv.ASHTAG] = outDataFrame[sv._ROW_UID].values
        # add Code+type Column
        outDataFrame.joinNmrResidueCodeType()
        return outDataFrame

    def getThresholdValueForData(self, data, columnName, calculationMode=sv.MAD, factor=1.):
        """ Get the Threshold value for the ColumnName values.
        :param data: pd.dataFrame
        :param columnName: str. a column name presents in the data(frame)
        :param calculationMode: str, one of ['MAD', 'AAD', 'Mean', 'Median', 'STD']
        :param factor: float. Multiplication factor.
        :return float.

        MAD: Median absolute deviation, (https://en.wikipedia.org/wiki/Median_absolute_deviation)
        AAD: Average absolute deviation, (https://en.wikipedia.org/wiki/Average_absolute_deviation).
        Note, MAD and AAD are often abbreviated the same way, in fact, in scipy MAD is Median absolute deviation,
        whereas in Pandas MAD is Mean absolute deviation!
        """
        factor = factor if factor and factor >0 else 1
        thresholdValue = None
        if data is not None:
            if len(data[columnName])>0:
                values = data[columnName].values
                values = values[~np.isnan(values)]  # skip nans
                if calculationMode == sv.MAD:
                    thresholdValue = stats.median_absolute_deviation(values) # in scipy MAD is Median absolute deviation
                if calculationMode == sv.AAD:
                    thresholdValue = data[columnName].mad() # in pandas MAD is Mean absolute deviation !
                else:
                    func = lf.CommonStatFuncs.get(calculationMode, None)
                    if func:
                        thresholdValue = func(values)
        if thresholdValue:
            thresholdValue *= factor
        return thresholdValue

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

    def _registerModels(self, models):
        """Register multiple models in the main class """
        dd = {}
        for model in models:
            self.registerModel(model)
            dd[model.ModelName] = model
        return dd

    def plotResults(self, *args, **kwargs):
        pass


    def __init__(self):

        self.project = getProject()
        self.application = getApplication()
        self.current = getCurrent()
        self._inputDataTables = OrderedSet()
        self._outputDataTables = OrderedSet()
        self._untraceableValue = 1.0   # default value for replacing NaN values in untraceableValues.
        self.fittingModels = dict()
        self.calculationModels = dict()
        self._currentFittingModel = None     ## e.g.: ExponentialDecay for relaxation
        self._currentCalculationModel = None ## e.g.: HetNoe for Relaxation
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
