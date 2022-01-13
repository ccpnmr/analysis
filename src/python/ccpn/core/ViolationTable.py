"""
Module Documentation here
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
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2022-01-13 17:23:25 +0000 (Thu, January 13, 2022) $"
__version__ = "$Revision: 3.0.4 $"
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
from ccpnmodel.ccpncore.api.ccp.nmr.NmrConstraint import ViolationTable as ApiViolationTable
from ccpn.core.StructureData import StructureData
from ccpn.core._implementation.AbstractWrapperObject import AbstractWrapperObject
from ccpn.core.lib import Pid
from ccpn.core.lib.ContextManagers import newObject, renameObject, ccpNmrV3CoreSetter, ccpNmrV3CoreUndoBlock
from ccpn.core._implementation.DataFrameABC import DataFrameABC
from ccpn.util.decorators import logCommand
from ccpn.util.Logging import getLogger


logger = getLogger()


class ViolationFrame(DataFrameABC):
    """
    Generic data - as a Pandas DataFrame.
    """
    pass


class ViolationTable(AbstractWrapperObject):
    """Container for pandas dataFrame."""

    #: Short class name, for PID.
    shortClassName = 'VT'
    # Attribute is necessary as subclasses must use superclass className
    className = 'ViolationTable'

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
        """Set the data for the violationTable, must be of type ViolationFrame or None.
        None will create a new empty dataFrame
        """
        if not isinstance(value, (ViolationFrame, type(None))):
            if isinstance(value, pd.DataFrame):
                value = ViolationFrame(value)
                getLogger().warning(f'Data must be of type {ViolationFrame}. The value pd.DataFrame was converted to {ViolationFrame}.')
            else:
                raise RuntimeError(f'Data must be of type {ViolationFrame}, pd.DataFrame or None')

        if value is None:
            # create a new, empty table
            self._wrappedData.data = ViolationFrame()
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
        return dict((x.name, x.value) for x in self._wrappedData.violationTableParameters)

    @logCommand(get='self')
    def getMetadata(self, name: str):
        """Return value from metadata."""
        apiData = self._wrappedData
        metadata = apiData.findFirstViolationTableParameter(name=name)
        if metadata is not None:
            return metadata.value

    @logCommand(get='self')
    @ccpNmrV3CoreUndoBlock()
    def setMetadata(self, name: str, value):
        """Add name:value to metadata, overwriting existing entry."""
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
            raise KeyError("No metadata named %s" % name)
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

    @classmethod
    def _restoreObject(cls, project, apiObj):
        """Restore the object and update ccpnInternalData as required
        """
        result = super()._restoreObject(project, apiObj)

        _data = result._wrappedData.data
        if not isinstance(_data, ViolationFrame):
            # make sure that data is the correct type
            getLogger().debug(f'_restoreObject {result.pid}: data not of type {ViolationFrame} - resetting')
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
def _newViolationTable(self: StructureData, name: str = None, data: Optional[ViolationFrame] = None, comment: str = None) -> ViolationTable:
    """Create new ViolationTable.

    See the ViolationTable class for details.

    data must be of type ViolationFrame or None.
    If data is None, an empty dataFrame wll be created.

    :param name: name of the violationTable
    :param data: a ViolationFrame, Pandas DataFrame instance or None
    :param comment: optional comment string
    :return: a new ViolationTable instance.
    """
    if not isinstance(data, (ViolationFrame, type(None))):
        if isinstance(data, pd.DataFrame):
            data = ViolationFrame(data)
            getLogger().warning(f'Data must be of type {ViolationFrame}. The value pd.DataFrame was converted to {ViolationFrame}.')
        else:
            raise RuntimeError(f'Unable to generate new ViolationTable: data not of type {ViolationFrame}, pd.DataFrame or None')

    name = ViolationTable._uniqueName(project=self, name=name)

    apiParent = self._wrappedData

    apiViolationTable = apiParent.newViolationTable(name=name, details=comment)
    result = self._project._data2Obj.get(apiViolationTable)

    if result is None:
        raise RuntimeError('Unable to generate new ViolationTable item')

    if data is None:
        # create new, empty dataFrame
        result._wrappedData.data = ViolationFrame()
    else:
        # insert the subclassed pandas dataFrame
        result._wrappedData.data = data
        data._containingObject = result

    return result
