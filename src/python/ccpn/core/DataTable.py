"""
Module Documentation here
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
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2022-05-05 10:40:28 +0100 (Thu, May 05, 2022) $"
__version__ = "$Revision: 3.1.0 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Ed Brooksbank $"
__date__ = "$Date: 2021-10-27 20:54:49 +0100 (Wed, October 27, 2021) $"
#=========================================================================================
# Start of code
#=========================================================================================

from typing import Optional
import pandas as pd
from ccpnmodel.ccpncore.api.ccp.nmr.Nmr import DataTable as ApiDataTable
from ccpn.core._implementation.AbstractWrapperObject import AbstractWrapperObject
from ccpn.core.Project import Project
from ccpn.core.RestraintTable import RestraintTable
from ccpn.core.lib import Pid
from ccpn.core.lib.ContextManagers import newObject, renameObject, ccpNmrV3CoreSetter, ccpNmrV3CoreUndoBlock
from ccpn.core._implementation.DataFrameABC import DataFrameABC
from ccpn.util.decorators import logCommand
from ccpn.util.Logging import getLogger


logger = getLogger()
ALLOWED_METADATA_TYPES = (dict, list, str, int, float, bool, type(None))
_RESTRAINTTABLE = 'restraintTable'


class TableFrame(DataFrameABC):
    """
    Generic data - as a Pandas DataFrame.
    """
    pass


class DataTable(AbstractWrapperObject):
    """Container for pandas dataFrame."""

    #: Short class name, for PID.
    shortClassName = 'DT'
    # Attribute is necessary as subclasses must use superclass className
    className = 'DataTable'

    _parentClass = Project

    #: Name of plural link to instances of class
    _pluralLinkName = 'dataTables'

    #: List of child classes.
    _childClasses = []

    # Qualified name of matching API class
    _apiClassQualifiedName = ApiDataTable._metaclass.qualifiedName()

    # CCPN properties
    @property
    def _apiDataTable(self) -> ApiDataTable:
        """ CCPN api DataTable matching DataTable."""
        return self._wrappedData

    @property
    def _key(self) -> str:
        """id string - ID number converted to string."""
        return self._wrappedData.name.translate(Pid.remapSeparators)

    @property
    def serial(self) -> int:
        """ID number of DataTable, used in Pid and to identify the DataTable."""
        return self._wrappedData.serial

    @property
    def _parent(self) -> Project:
        """Parent (containing) object."""
        return self._project

    @property
    def name(self) -> str:
        """Name of DataTable, part of identifier."""
        return self._wrappedData.name

    @name.setter
    @logCommand(get='self', isProperty=True)
    def name(self, value: str):
        """set name of DataTable."""
        self.rename(value)

    @property
    def data(self) -> TableFrame:
        """Return the pandas dataFrame."""
        return self._wrappedData.data

    @data.setter
    @logCommand(get='self', isProperty=True)
    @ccpNmrV3CoreSetter()
    def data(self, value: TableFrame):
        """Set the data for the dataTable, must be of type TableFrame, pd.DataFrame or None.
        None will create a new empty dataFrame
        pd.DataFrames will be converted to ccpn TableFrames
        """
        if not isinstance(value, (TableFrame, type(None))):
            if isinstance(value, pd.DataFrame):
                value = TableFrame(value)
                getLogger().debug(f'Data must be of type {TableFrame}. The value pd.DataFrame was converted to {TableFrame}.')
            else:
                raise RuntimeError(f'Data must be of type {TableFrame}, pd.DataFrame or None')

        if value is None:
            # create a new, empty table
            self._wrappedData.data = TableFrame()
        else:
            self._wrappedData.data = value

    @property
    def metadata(self) -> dict:
        """Keyword-value dictionary of metadata.
        NB the value is a copy - modifying it will not modify the actual data.
        Use the setMetadata, deleteMetadata, clearMetadata, and updateMetadata
        methods to modify the metadata.

        Dictionary values can be anything that can be exported to JSON,
        including OrderedDict, numpy.ndarray, ccpn.util.Tensor,
        or pandas DataFrame, Series, or Panel.
        """
        return dict((x.name, x.value) for x in self._wrappedData.dataTableParameters)

    @logCommand(get='self')
    def getMetadata(self, name: str):
        """Return value from metadata."""
        apiData = self._wrappedData
        metadata = apiData.findFirstDataTableParameter(name=name)
        if metadata is not None:
            return metadata.value

    @logCommand(get='self')
    @ccpNmrV3CoreUndoBlock()
    def setMetadata(self, name: str, value):
        """Add name:value to metadata, overwriting existing entry."""

        def _checkMetaTypes(value):
            if isinstance(value, dict):
                return all(_checkMetaTypes(val) for val in value.keys()) and all(_checkMetaTypes(val) for val in value.values())
            elif isinstance(value, list):
                return all(_checkMetaTypes(val) for val in value)
            else:
                return isinstance(value, ALLOWED_METADATA_TYPES)
            # could use json.dumps(value) with (TypeError, OverflowError) but allows tuples

        # check that the metadata parameter belongs to the defined list
        if not _checkMetaTypes(value):
            raise ValueError(f'value contains non-serialisable element')

        apiData = self._wrappedData
        metadata = apiData.findFirstDataTableParameter(name=name)
        if metadata is None:
            apiData.newDataTableParameter(name=name, value=value)
        else:
            metadata.value = value

    @logCommand(get='self')
    @ccpNmrV3CoreUndoBlock()
    def deleteMetadata(self, name: str):
        """Delete metadata named 'name'."""
        apiData = self._wrappedData
        metadata = apiData.findFirstDataTableParameter(name=name)
        if metadata is None:
            raise KeyError("No metadata named %s" % name)
        else:
            metadata.delete()

    @logCommand(get='self')
    @ccpNmrV3CoreUndoBlock()
    def clearMetadata(self):
        """Delete all metadata."""
        for metadata in self._wrappedData.dataTableParameters:
            metadata.delete()

    @logCommand(get='self')
    @ccpNmrV3CoreUndoBlock()
    def updateMetadata(self, value: dict):
        """Convenience routine, similar to dict.update().
        Calls self.setMetadata(key, value) for each key,value pair in the input."""
        for key, val in value.items():
            self.setMetadata(key, val)

    @property
    def columns(self) -> list:
        """Return the columns in the dataFrame
        """
        return list(self.data.columns)

    @property
    def nefCompatibleColumns(self):
        """Return the columns in the dataFrame
        """
        return self.data.nefCompatibleColumns()

    @property
    def _restraintTableLink(self) -> Optional[RestraintTable]:
        """Return the link to a reference restraintTable from the metadata
        """
        _pid = self.getMetadata(_RESTRAINTTABLE)
        return self.project.getByPid(_pid)

    @_restraintTableLink.setter
    def _restraintTableLink(self, value):
        """Set the link to a reference restraintTable from the metadata
        :param value: RestraintTable or str
        """
        _rTable = self.project.getByPid(value) if isinstance(value, str) else value
        if not isinstance(_rTable, RestraintTable):
            raise ValueError(f'{self.className}.restraintTableLink is not a RestraintTable')

        self.setMetadata(_RESTRAINTTABLE, value)

    #=========================================================================================
    # Implementation functions
    #=========================================================================================

    @classmethod
    def _getAllWrappedData(cls, parent: Project) -> list:
        """get wrappedData for all DataTables linked to NmrProject."""
        return parent._wrappedData.sortedDataTables()

    @renameObject()
    @logCommand(get='self')
    def rename(self, value: str):
        """Rename DataTable, changing its name and Pid."""
        return self._rename(value)

    @classmethod
    def _restoreObject(cls, project, apiObj):
        """Restore the object and update ccpnInternalData as required
        """
        result = super()._restoreObject(project, apiObj)

        _data = result._wrappedData.data
        if not isinstance(_data, TableFrame):
            # make sure that data is the correct type
            getLogger().debug(f'_restoreObject {result.pid}: data not of type {TableFrame} - resetting')
            result._wrappedData.data = TableFrame()

        return result

    #=========================================================================================
    # CCPN functions
    #=========================================================================================

    #===========================================================================================
    # new<Object> and other methods
    # Call appropriate routines in their respective locations
    #===========================================================================================


#=========================================================================================
# Connections to parents:
#=========================================================================================

@newObject(DataTable)
def _newDataTable(self: Project, name: str = None, data: Optional[TableFrame] = None, comment: str = None) -> DataTable:
    """Create new DataTable.

    See the DataTable class for details.

    data must be of type TableFrame, pd.DataFrame or None.
    If data is None, an empty dataFrame wll be created.
    pd.DataFrames will be converted to ccpn DataFrames.

    :param name: name of the dataTable
    :param data: a TableFrame, Pandas DataFrame instance or None
    :param comment: optional comment string
    :return: a new DataTable instance.
    """
    if not isinstance(data, (TableFrame, type(None))):
        if isinstance(data, pd.DataFrame):
            data = TableFrame(data)
            getLogger().debug(f'Data must be of type {TableFrame}. The value pd.DataFrame was converted to {TableFrame}.')
        else:
            raise RuntimeError(f'Unable to generate new DataTable: data not of type {TableFrame}, pd.DataFrame or None')

    name = DataTable._uniqueName(project=self, name=name)

    apiParent = self._wrappedData

    apiDataTable = apiParent.newDataTable(name=name, details=comment)
    result = self._project._data2Obj.get(apiDataTable)
    if result is None:
        raise RuntimeError('Unable to generate new DataTable item')

    if data is None:
        # create new, empty dataFrame
        result._wrappedData.data = TableFrame()
    else:
        # insert the subclassed pandas dataFrame
        result._wrappedData.data = data
        data._containingObject = result

    return result


def _fetchDataTable(self: Project, name):
    """Get an existing dataTable by name or create a new one
    """
    from ccpn.core.lib.Pid import createPid

    dataTable = self.getByPid(createPid(DataTable.shortClassName, name))
    if not dataTable:
        dataTable = self.newDataTable(name=name)
    return dataTable
