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
                 "J.Biomol.Nmr (2016), 66, 111-124, https://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2022-11-24 16:15:05 +0000 (Thu, November 24, 2022) $"
__version__ = "$Revision: 3.1.0 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Ed Brooksbank $"
__date__ = "$Date: 2021-10-27 20:54:49 +0100 (Wed, October 27, 2021) $"
#=========================================================================================
# Start of code
#=========================================================================================

from typing import Optional, Union
import pandas as pd
from ccpnmodel.ccpncore.api.ccp.nmr.NmrConstraint import ViolationTable as ApiViolationTable
from ccpn.core._implementation.AbstractWrapperObject import AbstractWrapperObject
from ccpn.core.StructureData import StructureData
from ccpn.core.RestraintTable import RestraintTable
from ccpn.core.lib import Pid
from ccpn.core.lib.ContextManagers import newObject, renameObject, ccpNmrV3CoreSetter, ccpNmrV3CoreUndoBlock
from ccpn.core._implementation.DataFrameABC import DataFrameABC
from ccpn.util.decorators import logCommand
from ccpn.util.Logging import getLogger


logger = getLogger()
ALLOWED_METADATA_TYPES = (dict, list, str, int, float, bool, type(None))
_RESTRAINTTABLE = 'restraintTable'


class ViolationFrame(DataFrameABC):
    """
    Generic data - as a Pandas DataFrame.
    """
    pass


# register the class with DataFrameABC for json loading/saving
ViolationFrame.register()


class ViolationTable(AbstractWrapperObject):
    """Container for pandas dataFrame."""

    #: Short class name, for PID.
    shortClassName = 'VT'
    # Attribute is necessary as subclasses must use superclass className
    className = 'ViolationTable'

    _isPandasTableClass = True

    _parentClass = StructureData

    #: Name of plural link to instances of class
    _pluralLinkName = 'violationTables'

    #: List of child classes.
    _childClasses = []

    # Qualified name of matching API class
    _apiClassQualifiedName = ApiViolationTable._metaclass.qualifiedName()

    # CCPN properties
    @property
    def _apiViolationTable(self) -> ApiViolationTable:
        """ CCPN api ViolationTable matching ViolationTable."""
        return self._wrappedData

    @property
    def _key(self) -> str:
        """id string - ID number converted to string."""
        return self._wrappedData.name.translate(Pid.remapSeparators)

    @property
    def serial(self) -> int:
        """ID number of ViolationTable, used in Pid and to identify the ViolationTable."""
        return self._wrappedData.serial

    @property
    def _parent(self) -> StructureData:
        """StructureData containing ViolationTable."""
        return self._project._data2Obj[self._wrappedData.nmrConstraintStore]

    structureData = _parent

    @property
    def name(self) -> str:
        """Name of ViolationTable, part of identifier."""
        return self._wrappedData.name

    @name.setter
    @logCommand(get='self', isProperty=True)
    def name(self, value: str):
        """set name of ViolationTable."""
        self.rename(value)

    @property
    def data(self) -> ViolationFrame:
        """Return the pandas dataFrame."""
        return self._wrappedData.data

    @data.setter
    @logCommand(get='self', isProperty=True)
    @ccpNmrV3CoreSetter()
    def data(self, value: ViolationFrame):
        """Set the data for the violationTable, must be of type ViolationFrame, pd.DataFrame or None.
        None will create a new empty dataFrame
        pd.DataFrames will be converted to ViolationFrames
        """
        if not isinstance(value, (ViolationFrame, type(None))):
            if not isinstance(value, pd.DataFrame):
                raise RuntimeError(f'Data must be of type {ViolationFrame}, pd.DataFrame or None')

            value = ViolationFrame(value)
            getLogger().debug(f'Data must be of type {ViolationFrame}. The value pd.DataFrame was converted to {ViolationFrame}.')

        self._wrappedData.data = ViolationFrame() if value is None else value

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
        return {x.name: x.value for x in self._wrappedData.violationTableParameters}

    @logCommand(get='self')
    def getMetadata(self, name: str):
        """Return value from metadata."""
        apiData = self._wrappedData
        metadata = apiData.findFirstViolationTableParameter(name=name)
        if metadata is not None:
            return metadata.value

    @logCommand(get='self')
    @ccpNmrV3CoreUndoBlock(metadata=True)
    def setMetadata(self, name: str, value):
        """Add name:value to metadata, overwriting existing entry."""

        # check that the metadata parameter belongs to the defined list

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
            raise ValueError('value contains non-serialisable element')

        apiData = self._wrappedData
        metadata = apiData.findFirstViolationTableParameter(name=name)
        if metadata is None:
            apiData.newViolationTableParameter(name=name, value=value)
        else:
            metadata.value = value

    @logCommand(get='self')
    @ccpNmrV3CoreUndoBlock()
    def deleteMetadata(self, name: str):
        """Delete metadata named 'name'."""
        apiData = self._wrappedData
        metadata = apiData.findFirstViolationTableParameter(name=name)
        if metadata is None:
            raise KeyError(f'No metadata named {name}')
        else:
            metadata.delete()

    @logCommand(get='self')
    @ccpNmrV3CoreUndoBlock()
    def clearMetadata(self):
        """Delete all metadata."""
        for metadata in self._wrappedData.violationTableParameters:
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
        if not isinstance(_rTable, (RestraintTable, type(None))):
            raise ValueError(f'{self.className}._restraintTableLink is not a RestraintTable, or None')

        self.setMetadata(_RESTRAINTTABLE, _rTable and _rTable.pid)

    #=========================================================================================
    # Implementation functions
    #=========================================================================================

    @classmethod
    def _getAllWrappedData(cls, parent: StructureData) -> list:
        """get wrappedData for all ViolationTables linked to NmrConstraintStore."""
        return parent._wrappedData.sortedViolationTables()

    @renameObject()
    @logCommand(get='self')
    def rename(self, value: str):
        """Rename ViolationTable, changing its name and Pid."""
        return self._rename(value)

    def _rename(self, value: str):
        """Generic rename method that individual classes can use for implementation
        of their rename method to minimises code duplication
        """
        # validate the name from the parent structureData
        name = self._uniqueName(project=self.structureData, name=value)

        # rename functions from here
        oldName = self.name
        self._oldPid = self.pid

        self._wrappedData.name = name

        return (oldName,)

    @classmethod
    def _restoreObject(cls, project, apiObj):
        """Restore the object and update ccpnInternalData as required
        """
        result = super()._restoreObject(project, apiObj)

        _data = result._wrappedData.data
        if not isinstance(_data, ViolationFrame):

            if isinstance(_data, pd.DataFrame):
                # make sure that data is the correct type
                getLogger().debug(f'Restoring object - converting to {ViolationFrame}')
                result._wrappedData.data = ViolationFrame(_data)

            else:
                # make sure that data is the correct type
                getLogger().debug(f'Failed restoring object {result.pid}: data not of type {ViolationFrame} - resetting to an empty table')
                result._wrappedData.data = ViolationFrame()

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

@newObject(ViolationTable)
def _newViolationTable(self: StructureData, name: str = None, data: Optional[ViolationFrame] = None,
                       _restraintTableLink: Union[RestraintTable, str, None] = None,
                       comment: str = None) -> ViolationTable:
    """Create new ViolationTable.

    See the ViolationTable class for details.

    data must be of type ViolationFrame, pd.DataFrame or None.
    If data is None, an empty dataFrame wll be created.
    pd.DataFrame's will be converted to ViolationFrame.

    :param name: name of the violationTable
    :param data: a ViolationFrame, Pandas DataFrame instance or None
    :param comment: optional comment string
    :return: a new ViolationTable instance.
    """
    if isinstance(data, ViolationFrame):
        pass

    elif data is None:
        # create new, empty ViolationFrame
        data = ViolationFrame()

    elif isinstance(data, pd.DataFrame):
        # convert type from panda's dataFrame
        data = ViolationFrame(data)
        getLogger().debug(f'The data of type pd.DataFrame was converted to {ViolationFrame}.')

    else:
        raise ValueError(f'Unable to generate new ViolationTable: data not of type {ViolationFrame}, pd.DataFrame or None')

    _restraintTableLink = self.project.getByPid(_restraintTableLink) if isinstance(_restraintTableLink, str) else _restraintTableLink
    if not isinstance(_restraintTableLink, (RestraintTable, type(None))):
        raise ValueError(f'Unable to generate new ViolationTable: restraintTable not of type {RestraintTable}')

    # get unique name from the parent structureData
    name = ViolationTable._uniqueName(project=self.project, name=name)

    apiParent = self._wrappedData

    apiViolationTable = apiParent.newViolationTable(name=name, details=comment)
    result = self._project._data2Obj.get(apiViolationTable)

    if result is None:
        raise RuntimeError('Unable to generate new ViolationTable item')

    # set the data and back-link
    result._wrappedData.data = data
    data._containingObject = result
    if _restraintTableLink:
        result._restraintTableLink = _restraintTableLink

    return result
