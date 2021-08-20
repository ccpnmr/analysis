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
__dateModified__ = "$dateModified: 2021-08-20 19:19:59 +0100 (Fri, August 20, 2021) $"
__version__ = "$Revision: 3.0.4 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

import collections
from ccpnmodel.ccpncore.api.ccp.molecule.MolStructure import StructureEnsemble as ApiStructureEnsemble
from ccpn.core.Project import Project
from ccpn.core._implementation.AbstractWrapperObject import AbstractWrapperObject
from ccpn.core.lib import Pid
from ccpn.core.lib.ContextManagers import newObject, renameObject
from ccpn.util.StructureData import EnsembleData
from ccpn.util.decorators import logCommand
from ccpn.util.Logging import getLogger
from ccpn.util import Common as commonUtil


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
        # return str(self._wrappedData.ensembleId)
        # return str(self.name) + '_' + str(self.serial)
        return self._wrappedData.name.translate(Pid.remapSeparators)

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

    @name.setter
    def name(self, value: str):
        """set name of StructureEnsemble."""
        self.rename(value)

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

    @renameObject()
    @logCommand(get='self')
    def rename(self, value: str):
        """Rename StructureEnsemble, changing its name and Pid.
        NB, the serial remains immutable.
        """
        return self._rename(value)

    #=========================================================================================
    # CCPN functions
    #=========================================================================================

    #===========================================================================================
    # new'Object' and other methods
    # Call appropriate routines in their respective locations
    #===========================================================================================

    @logCommand(get='self')
    def newModel(self, label: str = None, comment: str = None, **kwds):
        """Create new Model.

        See the Model class for details.

        Optional keyword arguments can be passed in; see Model._newModel for details.

        :param label: new name for the model.
        :param comment: optional comment string.
        :return: a new Model instance.
        """
        from ccpn.core.Model import _newModel

        return _newModel(self, label=label, comment=comment, **kwds)


#=========================================================================================
# Connections to parents:
#=========================================================================================

@newObject(StructureEnsemble)
def _newStructureEnsemble(self: Project, name: str = None, data: EnsembleData = None,
                          comment: str = None) -> StructureEnsemble:
    """Create new StructureEnsemble.

    See the StructureEnsemble class for details.

    :param name: name of the structureEnsemble
    :param data: an EnsembleData instance
    :param comment: any comment string
    :return: a new StructureEnsemble instance.
    """
    # avoiding circular import
    from ccpn.core.Model import Model

    name = StructureEnsemble._uniqueName(project=self, name=name)

    nmrProject = self._wrappedData

    ll = nmrProject.root.structureEnsembles
    serial = max(x.ensembleId for x in ll) + 1 if ll else 1
    params = {'molSystem': nmrProject.molSystem, 'ensembleId': serial, 'details': comment}
    if name:
        params['name'] = name

    newApiStructureEnsemble = nmrProject.root.newStructureEnsemble(**params)
    result = self._data2Obj[newApiStructureEnsemble]
    if result is None:
        raise RuntimeError('Unable to generate new StructureEnsemble item')

    # if serial is not None:
    #     try:
    #         result.resetSerial(serial)
    #     except ValueError:
    #         self.project._logger.warning("Could not reset serial of %s to %s - keeping original value"
    #                                      % (result, serial))

    if data is None:
        result.data = EnsembleData()

    else:
        result.data = data
        data._containingObject = result
        for modelNumber in sorted(data['modelNumber'].unique()):
            # _validateName
            _label = 'my%s_%s' % (Model.className, modelNumber)
            result.newModel(serial=modelNumber, label=_label)

    return result

#EJB 20181204: moved to Project
# Project.newStructureEnsemble = _newStructureEnsemble
# del _newStructureEnsemble

# Notifiers:
