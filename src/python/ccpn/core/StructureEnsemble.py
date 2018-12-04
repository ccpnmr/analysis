"""
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2017"
__credits__ = ("Wayne Boucher, Ed Brooksbank, Rasmus H Fogh, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license",
               "or ccpnmodel.ccpncore.memops.Credits.CcpnLicense for licence text")
__reference__ = ("For publications, please use reference from http://www.ccpn.ac.uk/v3-software/downloads/license",
                 "or ccpnmodel.ccpncore.memops.Credits.CcpNmrReference")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: CCPN $"
__dateModified__ = "$dateModified: 2017-07-07 16:32:30 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.b3 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

import collections

from ccpn.core.Project import Project
from ccpn.core._implementation.AbstractWrapperObject import AbstractWrapperObject
from ccpn.core.lib import Pid
from ccpn.core.lib import Undo
from ccpn.util.StructureData import EnsembleData
from ccpnmodel.ccpncore.api.ccp.molecule.MolStructure import StructureEnsemble as ApiStructureEnsemble
from ccpn.util.decorators import logCommand
from ccpn.core.lib.ContextManagers import newObject, deleteObject, ccpNmrV3CoreSetter, logCommandBlock
from ccpn.util.Logging import getLogger


logger = getLogger()


class StructureEnsemble(AbstractWrapperObject):
    """Ensemble of coordinate structures."""

    #: Short class name, for PID.
    shortClassName = 'SE'
    # Attribute is necessary as subclasses must use superclass className
    className = 'StructureEnsemble'

    _parentClass = Project

    #: Name of plural link to instances of class
    _pluralLinkName = 'structureEnsembles'

    #: List of child classes.
    _childClasses = []

    # Qualified name of matching API class
    _apiClassQualifiedName = ApiStructureEnsemble._metaclass.qualifiedName()

    # CCPN properties
    @property
    def _apiStructureEnsemble(self) -> ApiStructureEnsemble:
        """ CCPN api StructureEnsemble matching StructureEnsemble"""
        return self._wrappedData

    @property
    def _key(self) -> str:
        """id string - ID number converted to string"""
        return str(self._wrappedData.ensembleId)

    @property
    def serial(self) -> int:
        """ID number of StructureEnsemble, used in Pid and to identify the StructureEnsemble. """
        return self._wrappedData.ensembleId

    @property
    def _parent(self) -> Project:
        """Parent (containing) object."""
        return self._project

    @property
    def name(self) -> str:
        """Name of StructureEnsemble, part of identifier"""
        return self._wrappedData.name

    @property
    def data(self) -> EnsembleData:
        """EnsembleData (Pandas DataFrame) with structure data.

        Note that modifying the data via setValues, 'data[column] = ' or 'data.column = '
        will be echoed and put on the undo stack.
        Changing the data by direct pandas access will not."""
        apiObj = self._wrappedData.findFirstParameter(name='data')
        if apiObj is None:
            return None
        else:
            return apiObj.value

    @data.setter
    def data(self, value: EnsembleData):
        wrappedData = self._wrappedData
        if isinstance(value, EnsembleData):
            apiObj = wrappedData.findFirstParameter(name='data')
            if apiObj is None:
                wrappedData.newParameter(name='data', value=value)
            else:
                apiObj.value = value
        else:
            raise TypeError("Value is not of type EnsembleData")
        #
        value._containingObject = self

    @property
    def comment(self) -> str:
        """Free-form text comment"""
        return self._wrappedData.details

    @comment.setter
    def comment(self, value: str):
        self._wrappedData.details = value

    def resetModels(self):
        """Remove models without data, add models to reflect modelNumbers present"""
        data = self.data
        if data.shape[0]:
            # data present
            modelNumbers = set(x for x in data['modelNumber'] if x is not None)
            serial2Model = collections.OrderedDict((x.serial, x) for x in self.models)

            # remove models without data
            for serial, model in serial2Model.items():
                if serial not in modelNumbers:
                    model.delete()

            # Add model for model-less data
            for modelNumber in modelNumbers:
                if modelNumber not in serial2Model:
                    self.newModel(serial=modelNumber)

    #=========================================================================================
    # Implementation functions
    #=========================================================================================

    @classmethod
    def _getAllWrappedData(cls, parent: Project) -> list:
        """get wrappedData for all NmrConstraintStores linked to NmrProject"""
        return parent._wrappedData.molSystem.sortedStructureEnsembles()

    def rename(self, value: str):
        """Rename StructureEnsemble, changing its name and Pid.

        NB, the serial remains immutable."""

        if not isinstance(value, str):
            raise TypeError("StructureEnsemble name must be a string")  # ejb catch non-string
        if not value:
            raise ValueError("StructureEnsemble name must be set")  # ejb catch empty string
        if Pid.altCharacter in value:
            raise ValueError("Character %s not allowed in ccpn.StructureEnsemble.name" % Pid.altCharacter)
        #
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ ejb

        self._startCommandEchoBlock('rename', value)
        try:
            self._wrappedData.name = value
        finally:
            self._endCommandEchoBlock()

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

@newObject(StructureEnsemble)
def _newStructureEnsemble(self: Project, serial: int = None, name: str = None, data: EnsembleData = None,
                          comment: str = None) -> StructureEnsemble:
    """Create new StructureEnsemble.

    See the StructureEnsemble class for details.

    :param name:
    :param data:
    :param comment:
    :param serial: optional serial number.
    :return: a new StructureEnsemble instance.
    """

    nmrProject = self._wrappedData

    if serial is None:
        ll = nmrProject.root.structureEnsembles
        serial = max(x.ensembleId for x in ll) + 1 if ll else 1
    params = {'molSystem': nmrProject.molSystem, 'ensembleId': serial, 'details': comment}
    if name:
        params['name'] = name

    newApiStructureEnsemble = nmrProject.root.newStructureEnsemble(**params)
    result = self._data2Obj[newApiStructureEnsemble]
    if result is None:
        raise RuntimeError('Unable to generate new StructureEnsemble item')

    if serial is not None:
        try:
            result.resetSerial(serial)
        except ValueError:
            self.project._logger.warning("Could not reset serial of %s to %s - keeping original value"
                                         % (result, serial))

    if data is None:
        result.data = EnsembleData()
    else:
        logger.warning("EnsembleData successfully set on new StructureEnsemble were not echoed - too large")

        # result.data = EnsembleData()    # ejb
        result.data = data
        data._containingObject = result
        for modelNumber in sorted(data['modelNumber'].unique()):
            result.newModel(serial=modelNumber, label='Model_%s' % modelNumber)

    # TODO:ED CHECK, but should be okay
    # # Set up undo
    # apiObjectsCreated = [newApiStructureEnsemble]
    # apiObjectsCreated.extend(newApiStructureEnsemble.sortedModels())
    # apiObjectsCreated.extend(newApiStructureEnsemble.parameters)
    # undo.newItem(Undo._deleteAllApiObjects, nmrProject.root._unDelete,
    #              undoArgs=(apiObjectsCreated,),
    #              redoArgs=(apiObjectsCreated, (nmrProject, nmrProject.root)))

    return result


# Connections to parents:
Project.newStructureEnsemble = _newStructureEnsemble
del _newStructureEnsemble

# Notifiers:
