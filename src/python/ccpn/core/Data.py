"""
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
__dateModified__ = "$dateModified: 2021-11-02 18:40:28 +0000 (Tue, November 02, 2021) $"
__version__ = "$Revision: 3.0.4 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from typing import Optional

from ccpnmodel.ccpncore.lib import Util as coreUtil
from ccpn.core.lib import Pid
from ccpnmodel.ccpncore.api.ccp.nmr.NmrConstraint import Data as ApiData
from ccpnmodel.ccpncore.api.ccp.nmr.NmrConstraint import Parameter as ApiParameter
from ccpn.core._implementation.AbstractWrapperObject import AbstractWrapperObject
from ccpn.core.Project import Project
from ccpn.core.StructureData import StructureData
from ccpn.util.decorators import logCommand
from ccpn.core.lib.ContextManagers import newObject, renameObject


class Data(AbstractWrapperObject):
    """Object storing links to the data structures (PeakLists, Spectra, StructureEnsembles etc.)
    connected to a given DataSet, and their associated calculation parameters."""

    #: Short class name, for PID.
    shortClassName = 'DA'
    # Attribute it necessary as subclasses must use superclass className
    className = 'Data'

    _parentClass = StructureData

    #: Name of plural link to instances of class
    _pluralLinkName = 'data'

    #: List of child classes.
    _childClasses = []

    # Qualified name of matching API class
    _apiClassQualifiedName = ApiData._metaclass.qualifiedName()

    # CCPN properties
    @property
    def _apiData(self) -> ApiData:
        """ CCPN Data object matching Data"""
        return self._wrappedData

    def print(self):
        pass

    @property
    def _key(self) -> str:
        """id string - name"""
        # return self._wrappedData.name
        return self._wrappedData.name.translate(Pid.remapSeparators)

    @property
    def name(self) -> str:
        """name of Data object, used in Pid and to identify the Data object. """
        return self._wrappedData.name

    @name.setter
    def name(self, value: str):
        """set name of Data object."""
        self.rename(value)

    @property
    def _parent(self) -> StructureData:
        """DataSet containing Data."""
        return self._project._data2Obj[self._wrappedData.nmrConstraintStore]

    calculationStep = _parent

    @property
    def attachedObjectPid(self) -> Optional[str]:
        """Pid for attached object - used to calculate the attachedObject

        Remains unchanged also if the object pointed to is renamed or deleted, to
        preserve, as far as possible, the original data."""
        return self._wrappedData.attachedObjectPid

    @attachedObjectPid.setter
    def attachedObjectPid(self, value: str):
        self._wrappedData.attachedObjectPid = value

    @property
    def attachedObject(self) -> Optional[AbstractWrapperObject]:
        """attached object - derived from self.attachedObjectPid.

        If no attached object matching attachedObjectPid can be found
        (object has been renamed, deleted, or the attachedObjectPid is incorrect)
        this attribute has the value None."""
        ss = self._wrappedData.attachedObjectPid
        if ss:
            return self.getByPid(ss)
        else:
            return None

    @attachedObject.setter
    def attachedObject(self, value: str):
        if value:
            self._wrappedData.attachedObjectPid = value.pid
        else:
            self._wrappedData.attachedObjectPid = None

    @property
    def parameters(self) -> dict:
        """Keyword-value dictionary of parameters.
        NB the value is a copy - modifying it will not modify the actual data.
        Use the setParameter, deleteParameter, clearParameters, and updateParameters
        methods to modify the parameters.

        Dictionary values can be anything that can be exported to JSON,
        including OrderedDict, numpy.ndarray, ccpn.util.Tensor,
        or pandas DataFrame, Series, or Panel"""
        return dict((x.name, x.value) for x in self._wrappedData.parameters)

    def setParameter(self, name: str, value):
        """Add name:value to parameters, overwriting existing entries"""
        apiData = self._wrappedData
        parameter = apiData.findFirstParameter(name=name)
        if parameter is None:
            apiData.newParameter(name=name, value=value)
        else:
            parameter.value = value

    def deleteParameter(self, name: str):
        """Delete parameter named 'name'"""
        apiData = self._wrappedData
        parameter = apiData.findFirstParameter(name=name)
        if parameter is None:
            raise KeyError("No parameter named %s" % name)
        else:
            parameter.delete()

    def clearParameters(self):
        """Delete all parameters"""
        for parameter in self._wrappedData.parameters:
            parameter.delete()

    def updateParameters(self, value: dict):
        """Convenience routine, similar to dict.update().
        Calls self.setParameter(key, value) for each key,value pair in the input."""
        for key, val in value.items():
            self.setParameter(key, val)

    #=========================================================================================
    # Implementation functions
    #=========================================================================================

    @classmethod
    def _getAllWrappedData(cls, parent: StructureData) -> list:
        """get wrappedData - all Data children of parent NmrConstraintStore"""
        return parent._wrappedData.sortedData()

    @renameObject()
    @logCommand(get='self')
    def rename(self, value: str):
        """Rename Data, changing its name and Pid.
        """
        name = self._uniqueName(project=self.project, name=value)

        # rename functions from here
        oldName = self.name
        self._oldPid = self.pid

        # GWV: unsure why this is different from  rename() implementations of many other classes?
        coreUtil._resetParentLink(self._wrappedData, 'data', {'name': name})
        return (oldName,)

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

@newObject(Data)
def _newData(self: StructureData, name: str, attachedObjectPid: str = None,
             attachedObject: AbstractWrapperObject = None) -> Data:
    """Create new Data within StructureData.

    See the Data class for details.

    :param name:
    :param attachedObjectPid:
    :param attachedObject:
    :return: a new Data instance.
    """

    project = self.project

    if attachedObject is not None:
        if attachedObjectPid is None:
            attachedObjectPid = attachedObject.pid
        else:
            raise ValueError(
                    "Either attachedObject or attachedObjectPid must be None - values were %s and %s"
                    % (attachedObject, attachedObjectPid))

    apiData = self._wrappedData.newData(name=name, attachedObjectPid=attachedObjectPid)
    result = project._data2Obj.get(apiData)
    if result is None:
        raise RuntimeError('Unable to generate new Data item')

    return result


# Notifiers:
# Data change whenever a parameter is created, deleted, or changed
Project._apiNotifiers.extend(
        (
            ('_notifyRelatedApiObject', {'pathToObject': 'data', 'action': 'change'},
             ApiParameter._metaclass.qualifiedName(), ''),
            ('_notifyRelatedApiObject', {'pathToObject': 'data', 'action': 'change'},
             ApiParameter._metaclass.qualifiedName(), '__init__'),
            ('_notifyRelatedApiObject', {'pathToObject': 'data', 'action': 'change'},
             ApiParameter._metaclass.qualifiedName(), 'delete'),
            )
        )
