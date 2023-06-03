"""
This module defines base classes for Series Analysis
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (https://www.ccpn.ac.uk) 2014 - 2023"
__credits__ = ("Ed Brooksbank, Joanna Fox, Victoria A Higman, Luca Mureddu, Eliza Płoskoń",
               "Timothy J Ragan, Brian O Smith, Gary S Thompson & Geerten W Vuister")
__licence__ = ("CCPN licence. See https://ccpn.ac.uk/software/licensing/")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, https://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Luca Mureddu $"
__dateModified__ = "$dateModified: 2023-05-22 11:52:49 +0100 (Mon, May 22, 2023) $"
__version__ = "$Revision: 3.1.1 $"
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
import pandas as pd
from abc import ABC
from ccpn.util.OrderedSet import OrderedSet
from ccpn.util.Logging import getLogger
from ccpn.core.SpectrumGroup import SpectrumGroup
from ccpn.core.DataTable import DataTable
from ccpn.util.traits.TraitBase import TraitBase
from ccpn.util.traits.CcpNmrTraits import Any, List, Bool, Odict, CString, Set
from ccpn.framework.Application import getApplication, getCurrent, getProject
from ccpn.framework.lib.experimentAnalysis.SeriesTablesBC import SeriesFrameBC, InputSeriesFrameBC
import ccpn.framework.lib.experimentAnalysis.fitFunctionsLib as lf
import ccpn.framework.lib.experimentAnalysis.SeriesAnalysisVariables as sv


class SeriesAnalysisABC(ABC):
    """
    The top level class for SeriesAnalysis modules.
    """
    seriesAnalysisName = ''
    _allowedPeakProperties = [sv._HEIGHT, sv._VOLUME, sv._PPMPOSITION, sv._LINEWIDTH]
    _minimisedProperty = None  # the property currently used to perform the fitting routines. Default height, but can be anything.

    @property
    def inputDataTables(self) -> list:
        """
        Get the attached input DataTables
        Lists of DataTables.
        """
        self._ensureDataType()
        return list(self._inputDataTables)

    @inputDataTables.setter
    def inputDataTables(self, values):
        self._inputDataTables = OrderedSet(values)
        self._ensureDataType()

    def addInputDataTable(self, dataTable):
        """
        Add a DataTable as inputData
        """
        self._inputDataTables.add(dataTable)

    def removeInputDataTable(self, dataTable):
        """
        Remove a DataTable as inputData
        """
        self._inputDataTables.discard(dataTable)

    def clearInputDataTables(self):
        """
        Remove all  DataTable as inputData
        """
        self._inputDataTables = OrderedSet()

    @property
    def outputDataTableName(self):
        """The name for the outputDataTable created after a fitData routine """
        return self._outputDataTableName

    @outputDataTableName.setter
    def outputDataTableName(self, name):
        self._outputDataTableName = name

    @property
    def resultDataTable(self):
        """ The dataTable  which will be displayed on tables"""
        return self._resultDataTable

    @resultDataTable.setter
    def resultDataTable(self, dataTable):
        self._resultDataTable = dataTable

    def _fetchOutputDataTable(self, name=None):
        """
        Interanl. Called after 'fit()' to get a valid Datatable to attach the fitting output SeriesFrame
        :param seriesFrameType: str,  A filtering serieFrameType.
        :return: DataTable
        """
        dataTable = self.project.getDataTable(name)
        if dataTable:
            # restore the type in case is from a reopened project.
            dataTable.data.__class__ = SeriesFrameBC

        if not dataTable:
            dataTable = self.project.newDataTable(name)
        ## update the exclusionHandler
        if not self._exclusionHandler._dataTable:
            self._exclusionHandler._dataTable = dataTable
        self._exclusionHandler.save()
        ## update the DATATABLETYPE
        dataTable.setMetadata(sv.DATATABLETYPE, sv.SERIESANALYSISOUTPUTDATA)
        dataTable.setMetadata(sv.SERIESFRAMETYPE,  sv.SERIESANALYSISOUTPUTDATA)
        return dataTable

    def getMergedResultDataFrame(self):
        """Get the SelectedOutputDataTable  merged  by the collection pid
        """
        dataTable = self.resultDataTable
        if dataTable is None:
            return
        dataFrame = dataTable.data
        if len(dataFrame)==0:
            return
        if not sv.COLLECTIONPID in dataFrame:
            return dataFrame
        ## group by id and keep only first row as all duplicated except the series steps, which are not needed here.
        ## reset index otherwise you lose the column collectionId
        outDataFrame = dataFrame.groupby(sv.COLLECTIONPID).first().reset_index()
        outDataFrame.set_index(sv.COLLECTIONPID, drop=False, inplace=True)

        # add the rawData as new columns (Transposed from column to row)
        lastSeenSeriesStep = None
        for ix, ys in dataFrame.groupby(sv.COLLECTIONPID)[[sv.SERIES_STEP_X, sv.SERIES_STEP_Y]]:
            for seriesStep, seriesValue in zip(ys[sv.SERIES_STEP_X].astype(str).values, ys[sv.SERIES_STEP_Y].values):
                if seriesStep == lastSeenSeriesStep:
                    seriesStep += sv.SEP # this is the case when two series Steps are the same! Cannot create two identical columns or 1 will disappear
                outDataFrame.loc[ix, seriesStep] = seriesValue
                lastSeenSeriesStep = seriesStep

        # drop columns that should not be on the Gui. To remove: peak properties (dim, height, ppm etc)
        toDrop = sv.PeakPropertiesHeaders + [sv._SNR, sv.DIMENSION, sv.ISOTOPECODE, sv.NMRATOMNAME, sv.NMRATOMPID]
        # toDrop += sv.ALL_EXCLUDED
        toDrop += ['None',  'None_'] #not sure yet where they come from
        outDataFrame.drop(toDrop, axis=1, errors='ignore', inplace=True)

        outDataFrame[sv.COLLECTIONID] = outDataFrame[sv.COLLECTIONID]
        ## sort by NmrResidueCode if available otherwise by COLLECTIONID
        if outDataFrame[sv.NMRRESIDUECODE].astype(str).str.isnumeric().all():
            outDataFrame.sort_values(by=sv.NMRRESIDUECODE, key=lambda x: x.astype(int), inplace =True)
        else:
            outDataFrame.sort_values(by=sv.COLLECTIONID, inplace=True)
        ## apply an ascending ASHTAG. This is needed for tables and BarPlotting
        outDataFrame[sv.INDEX] = np.arange(1, len(outDataFrame) + 1)
        ## put ASHTAG as first header
        outDataFrame.insert(0, sv.INDEX, outDataFrame.pop(sv.INDEX))
        return outDataFrame

    @property
    def inputCollection(self):
        """The parent collection containing all subPeakCollections """
        return self._inputCollection

    @inputCollection.setter
    def inputCollection(self, collection):
        """The parent collection containing all subPeakCollections """
        self._inputCollection = collection

    @property
    def inputSpectrumGroups(self):
        return list(self._inputSpectrumGroups)

    def addInputSpectrumGroup(self, spectrumGroup):
        """Add a spectrumGroup to the inputList. Used to create InputDataTables"""
        self._inputSpectrumGroups.add(spectrumGroup)

    def removeInputSpectrumGroup(self, spectrumGroup):
        """Remove a spectrumGroup to the inputList. Used to create InputDataTables"""
        self._inputSpectrumGroups.discard(spectrumGroup)

    def clearInputSpectrumGroups(self):
        """Remove  spectrumGroups to the inputList. Used to create InputDataTables"""
        self._inputSpectrumGroups.clear()

    @property
    def exclusionHandler(self):
        """Get an object containing all excluded pids"""
        exclusionHandler = self._exclusionHandler
        dataTable = self.project.getDataTable(self.outputDataTableName)
        if dataTable is not None:
            exclusionHandler._dataTable = dataTable
        return exclusionHandler

    @property
    def untraceableValue(self) -> float:
        return self._untraceableValue

    @untraceableValue.setter
    def untraceableValue(self, value):
        if isinstance(value, (float, int)):
            self._untraceableValue = value
        else:
            getLogger().warning(f'Impossible to set untraceableValue to {value}. Use type int or float.')

    def fitInputData(self) -> DataTable:
        """
        Perform calculations using the currentFittingModel and currentCalculationModel to the inputDataTables
        and save outputs to a single newDataTable.
        1) Perform the CalculationModel routines (which do not do any fitting (e.g.: exponential decay)  but only a plain calculation)
        2) Use the result frame from the Calculation model as input for the FittingModel.
        We must follow this order.

        Sometime only a calculation model is necessary, in that case set calculationModel._disableFittingModels to True.

        Resulting dataTables are available in the outputDataTables.
        :return: output dataTable . Creates a new output dataTable in outputDataTables
        """
        getLogger().warning(sv.UNDER_DEVELOPMENT_WARNING)

        if len(self.inputDataTables) == 0:
            raise RuntimeError('Cannot run any fitting models. Add a valid inputData first')

        outputFrame = self.currentCalculationModel.calculateValues(self.inputDataTables)
        self._minimisedProperty =  self.currentCalculationModel._minimisedProperty
        if not self.currentCalculationModel._disableFittingModels:
            outputFrame = self.currentFittingModel.fitSeries(outputFrame)

        outputFrame.joinNmrResidueCodeType()
        outputDataTable = self._fetchOutputDataTable(name=self._outputDataTableName)
        outputDataTable.data = outputFrame
        self._setMinimisedPropertyFromModels()
        return outputDataTable

        # if self.currentCalculationModel._disableFittingModels:
        #     data = calculationFrame
        # else:
        #     # merge the frames on CollectionPid/id, Assignment, model-results/statistics and calculation
        #     # keep only minimal info and not duplicates to the fitting frame (except the collectionPid)
        #     if self.currentCalculationModel.ModelName == sv.BLANKMODELNAME:
        #         inputFrame = self.inputDataTables[-1].data
        #     else:
        #         inputFrame = calculationFrame
        #     fittingFrame = self.currentFittingModel.fitSeries(inputFrame)
        #     if sv.CALCULATION_MODEL in calculationFrame.columns:
        #         cdf = calculationFrame[[ sv.COLLECTIONPID, sv.CALCULATION_MODEL] + self.currentCalculationModel.modelArgumentNames]
        #     else:
        #         cdf = calculationFrame[[sv.COLLECTIONPID] + self.currentCalculationModel.modelArgumentNames]
        #     data = pd.merge(fittingFrame, cdf, on=[sv.COLLECTIONPID], how='left')
        fittingFrame.joinNmrResidueCodeType()
        outputDataTable = self._fetchOutputDataTable(name=self._outputDataTableName)
        outputDataTable.data = data
        self.resultDataTable = outputDataTable
        return outputDataTable

    def _setMinimisedPropertyFromModels(self):
        """ Set the _minimisedProperty from the current models.
         Calculation model has priority, otherwise use the fitting model unless disabled."""

        self._minimisedProperty =  self.currentCalculationModel._minimisedProperty
        if self._minimisedProperty is None and not self.currentCalculationModel._disableFittingModels:
            self._minimisedProperty = self.currentFittingModel._minimisedProperty

    def _rebuildInputData(self):
        """Rebuild all the inputData tables from the defined SpectrumGroups."""
        inputCollection = self.inputCollection
        for spGroup in self.inputSpectrumGroups:
            for inputData in self.inputDataTables:
                inputData.data.buildFromSpectrumGroup(spGroup, parentCollection=inputCollection)

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

    def getCalculationModelByName(self, modelName):
        """
        Convenient method to get a registered Calculation Object  by its name
        :param modelName: str
        :return:
        """
        return self.calculationModels.get(modelName, None)

    def _getFirstModel(self, models):
        """
        Get the first Model in the dict
        :param models: dict of FittingModels or CalculationModels
        :return:
        """
        first = next(iter(models), iter({}))
        model = models.get(first)
        return model

    def newInputDataTableFromSpectrumGroup(self, spectrumGroup:SpectrumGroup,
                                           peakListIndices=None, dataTableName:str=None,
                                           experimentName:str=None):
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
        inputCollection = self.inputCollection
        seriesFrame = InputSeriesFrameBC()
        seriesFrame.buildFromSpectrumGroup(spectrumGroup,
                                           parentCollection=inputCollection,
                                           peakListIndices=peakListIndices,
                                           experimentName = experimentName
                                           )
        dataTable = project.newDataTable(name=dataTableName, data=seriesFrame)
        dataTable.setMetadata(sv.DATATABLETYPE, sv.SERIESANALYSISINPUTDATA)
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

    def _ensureDataType(self):
        """
        Reset variables and Obj type after restoring a project from its metadata.
        :return: dataTable
        """
        for dataTable in self._inputDataTables:
            if not isinstance(dataTable.data.__class__ , InputSeriesFrameBC):
                dataTable.data.__class__ = InputSeriesFrameBC

    def _isPidInDataTables(self, header, pid):
        """Check if a pid is in the inputDataTables.
         :param header: str, dataTable header e.g.: sv.PeakPid
         :param pid: str, the pid to search in the column
         :return bool. True if pid in data"""
        if len(self.inputDataTables) > 0:
            for inputDataTable in self.inputDataTables:
                data = inputDataTable.data
                filteredData = data.getByHeader(header, [pid])
                if not filteredData.empty:
                    return True
        return False

    def _getChainsFromDataFrame(self, df):
        nmrChainCodesFromDf = df[sv.NMRCHAINNAME].unique()
        nmrChains = [self.project.getNmrChain(c) for c in nmrChainCodesFromDf]
        chains = [nmrChain.chain for nmrChain in nmrChains]
        return chains

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

    def _getSeriesStepValues(self):
        """ Get the series values from the first input SpectrumGroups"""

        for spectrumGroup in self.inputSpectrumGroups:
            if spectrumGroup.series and  len(spectrumGroup.series)>0:
                return list(spectrumGroup.series) # not yet implemented with multiple SG.
        return []

    def plotResults(self, *args, **kwargs):
        pass

    def __init__(self):
        self.project = getProject()
        self.application = getApplication()
        self.current = getCurrent()
        self._inputDataTables = OrderedSet()
        self._inputSpectrumGroups = OrderedSet()
        self._inputCollection = None
        self._outputDataTableName = sv.SERIESANALYSISOUTPUTDATA
        self._resultDataTable = None
        self._untraceableValue = 1.0   # default value for replacing NaN values in untraceableValues.
        self.fittingModels = dict()
        self.calculationModels = dict()
        self._currentFittingModel = None     ## e.g.: ExponentialDecay for relaxation
        self._currentCalculationModel = None ## e.g.: HetNoe for Relaxation
        self._needsRefitting = False
        self._needsRebuildingInputDataTables = False
        self._exclusionHandler = ExclusionHandler()

    def close(self):
        self.exclusionHandler.save()
        self.clearInputDataTables()
        self._currentCalculationModel = None
        self._currentFittingModel = None

    def __str__(self):
        return f'<{self.__class__.__name__}: {self.seriesAnalysisName}>'

    __repr__ = __str__


class ExclusionHandler(TraitBase):
    """ A class that holds pids of objects to be excluded from calculations. E.g.: peaks from fitting etc.
    Available Objects: (traitName are taken from the object's _pluralLinkName property):
        - peaks
        - collections
        - nmrResidues
        - nmrAtoms
        - spectra
    Use save/restore to save/restore traits as metadata into/from a datatable
    """

    _traitNames = [f'{tag}s' for tag in sv.EXCLUDED_OBJECTS]

    def __init__(self, dataTable=None, *args, **kwargs):
        super().__init__()
        self._dataTable = dataTable # used to store/restore exclusions as metadata
        for name in self._traitNames:
            self.add_traits(**{name:List()})
            self.update({name:[]}) ## ensures all starts correctly and a list works as a list!

    def clear(self):
        """Reset all to empty """
        for name in self._traitNames:
            self.update({name:[]})

    def updataDataTable(self):
        """ Update the datatable data flags
         to do, update the dataFrame with True/False if the pid is in Data
            syntax DataFrame.loc[condition, (column_1, column_2)] = new_value
        """
        df = self._dataTable.data
        ## eg: for peaks to be like:
        # for pid in self.excluded_peakPids:
        #     df.loc[df[sv.PEAKPID] == pid, 'excluded_peakPids'] = True
        # self._dataTable.data = df
        pass

    def save(self):
        """Save metadata do the dataTable """
        if not self._dataTable:
            getLogger().warn('Impossible to save to DataTable. No DataTable available.')
            return
        self._dataTable.updateMetadata(self.asDict())

    def restore(self):
        """Restore metadata from the dataTable """
        if not self._dataTable:
            getLogger().warn('Impossible restore from DataTable. No DataTable available.')
            return
        for name, value in self._dataTable.metadata.items():
            if name in self._traitNames:
                self.update({name: value})


####
## Below objects are not implemeted yet and will be done with NTDB definitions

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
