"""
Module Documentation here
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2021"
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
__dateModified__ = "$dateModified: 2021-10-29 16:58:34 +0100 (Fri, October 29, 2021) $"
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
from ccpnmodel.ccpncore.api.ccp.nmr.Nmr import DataTable as ApiDataTable
from ccpn.core.Project import Project
from ccpn.core._implementation.AbstractWrapperObject import AbstractWrapperObject
from ccpn.core.lib import Pid
from ccpn.core.lib.ContextManagers import newObject, renameObject, ccpNmrV3CoreSetter, ccpNmrV3CoreUndoBlock
from ccpn.core._implementation.DataFrameABC import DataFrameABC
from ccpn.util.decorators import logCommand
from ccpn.util.Logging import getLogger


logger = getLogger()


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
        if not isinstance(value, (TableFrame, type(None))):
            raise RuntimeError(f'data not of type {TableFrame.__class__.__name__}')
        self._wrappedData.data = value

    @property
    def parameters(self) -> dict:
        """Keyword-value dictionary of parameters.
        NB the value is a copy - modifying it will not modify the actual data.
        Use the setParameter, deleteParameter, clearParameters, and updateParameters
        methods to modify the parameters.

        Dictionary values can be anything that can be exported to JSON,
        including OrderedDict, numpy.ndarray, ccpn.util.Tensor,
        or pandas DataFrame, Series, or Panel.
        """
        return dict((x.name, x.value) for x in self._wrappedData.dataTableParameters)

    @logCommand(get='self')
    def getParameter(self, name: str):
        """Return value of parameter."""
        apiData = self._wrappedData
        parameter = apiData.findFirstDataTableParameter(name=name)
        if parameter is not None:
            return parameter.value

    @logCommand(get='self')
    @ccpNmrV3CoreUndoBlock()
    def setParameter(self, name: str, value):
        """Add name:value to parameters, overwriting existing entries."""
        apiData = self._wrappedData
        parameter = apiData.findFirstDataTableParameter(name=name)
        if parameter is None:
            apiData.newDataTableParameter(name=name, value=value)
        else:
            parameter.value = value

    @logCommand(get='self')
    @ccpNmrV3CoreUndoBlock()
    def deleteParameter(self, name: str):
        """Delete parameter named 'name'."""
        apiData = self._wrappedData
        parameter = apiData.findFirstDataTableParameter(name=name)
        if parameter is None:
            raise KeyError("No parameter named %s" % name)
        else:
            parameter.delete()

    @logCommand(get='self')
    @ccpNmrV3CoreUndoBlock()
    def clearParameters(self):
        """Delete all parameters."""
        for parameter in self._wrappedData.dataTableParameters:
            parameter.delete()

    @logCommand(get='self')
    @ccpNmrV3CoreUndoBlock()
    def updateParameters(self, value: dict):
        """Convenience routine, similar to dict.update().
        Calls self.setParameter(key, value) for each key,value pair in the input."""
        for key, val in value.items():
            self.setParameter(key, val)

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

    #=========================================================================================
    # CCPN functions
    #=========================================================================================

    #===========================================================================================
    # new'Object' and other methods
    # Call appropriate routines in their respective locations
    #===========================================================================================


#=========================================================================================
# Connections to parents:
#=========================================================================================

@newObject(DataTable)
def _newDataTable(self: Project, name: str = None, data: Optional[TableFrame] = None, comment: str = None) -> DataTable:
    """Create new DataTable.

    See the DataTable class for details.

    :param name: name of the dataTable
    :param data: a Pandas DataFrame instance
    :param comment: optional comment string
    :return: a new DataTable instance.
    """
    if not isinstance(data, (TableFrame, type(None))):
        raise RuntimeError(f'Unable to generate new DataTable: data not of type {TableFrame.__class__.__name__}')

    name = DataTable._uniqueName(project=self, name=name)

    apiParent = self._wrappedData

    apiDataTable = apiParent.newDataTable(name=name, details=comment)
    result = self._project._data2Obj.get(apiDataTable)
    if result is None:
        raise RuntimeError('Unable to generate new DataTable item')

    if data is None:
        result._wrappedData.data = TableFrame()
    else:
        # insert the subclassed pandas dataFrame
        result._wrappedData.data = data
        data._containingObject = result

    return result
