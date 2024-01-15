"""
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (https://www.ccpn.ac.uk) 2014 - 2024"
__credits__ = ("Ed Brooksbank, Joanna Fox, Morgan Hayward, Victoria A Higman, Luca Mureddu",
               "Eliza Płoskoń, Timothy J Ragan, Brian O Smith, Gary S Thompson & Geerten W Vuister")
__licence__ = ("CCPN licence. See https://ccpn.ac.uk/software/licensing/")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, https://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2024-01-15 18:52:11 +0000 (Mon, January 15, 2024) $"
__version__ = "$Revision: 3.2.2 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

import collections
import pandas as pd

from ccpnmodel.ccpncore.api.ccp.molecule.MolStructure import StructureEnsemble as ApiStructureEnsemble
from ccpn.core.Project import Project
from ccpn.core._implementation.AbstractWrapperObject import AbstractWrapperObject
from ccpn.core.lib import Pid
from ccpn.core.lib.ContextManagers import newObject, renameObject
from ccpn.util.StructureData import EnsembleData
from ccpn.util.decorators import logCommand
from ccpn.util.Logging import getLogger


logger = getLogger()


class StructureEnsemble(AbstractWrapperObject):
    """Ensemble of coordinate structures."""

    #: Short class name, for PID.
    shortClassName = 'SE'
    # Attribute is necessary as subclasses must use superclass className
    className = 'StructureEnsemble'

    _isPandasTableClass = True

    _parentClass = Project

    #: Name of plural link to instances of class
    _pluralLinkName = 'structureEnsembles'

    #: List of child classes.
    _childClasses = []

    # Qualified name of matching API class
    _apiClassQualifiedName = ApiStructureEnsemble._metaclass.qualifiedName()

    #=========================================================================================
    # CCPN properties
    #=========================================================================================

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
        will be echoed and put on the undo-stack.
        Changing the data by direct pandas access will not."""
        apiObj = self._wrappedData.findFirstParameter(name='data')
        return None if apiObj is None else apiObj.value

    @data.setter
    def data(self, value: EnsembleData):
        wrappedData = self._wrappedData
        if not isinstance(value, EnsembleData):
            raise TypeError("Value is not of type EnsembleData")

        apiObj = wrappedData.findFirstParameter(name='data')
        if apiObj is None:
            wrappedData.newParameter(name='data', value=value)
        else:
            apiObj.value = value

        value._containingObject = self

    #=========================================================================================
    # property STUBS: hot-fixed later
    #=========================================================================================

    @property
    def models(self) -> list['Model']:
        """STUB: hot-fixed later
        :return: a list of models in the StructureEnsemble
        """
        return []

    #=========================================================================================
    # getter STUBS: hot-fixed later
    #=========================================================================================

    def getModel(self, relativeId: str) -> 'Model | None':
        """STUB: hot-fixed later
        :return: an instance of Model, or None
        """
        return None

    #=========================================================================================
    # Core methods
    #=========================================================================================

    def resetModels(self):
        """Remove models without data, add models to reflect modelNumbers present"""
        data = self.data
        if data.shape[0]:
            # data present
            modelNumbers = {x for x in data['modelNumber'] if x is not None}
            serial2Model = collections.OrderedDict((x.serial, x) for x in self.models)

            # remove models without data
            for serial, model in serial2Model.items():
                if serial not in modelNumbers:
                    model.delete()

            # Add model for model-less data
            for modelNumber in modelNumbers:
                if modelNumber not in serial2Model:
                    _model = self.newModel()
                    _model._resetSerial(modelNumber)

    @renameObject()
    @logCommand(get='self')
    def rename(self, value: str):
        """Rename StructureEnsemble, changing its name and Pid.
        NB, the serial remains immutable.
        """
        return self._rename(value)

    #=========================================================================================
    # Implementation methods
    #=========================================================================================

    @classmethod
    def _getAllWrappedData(cls, parent: Project) -> list:
        """get wrappedData for all NmrConstraintStores linked to NmrProject"""
        return parent._wrappedData.molSystem.sortedStructureEnsembles()

    @classmethod
    def _restoreObject(cls, project, apiObj):
        """Restore the object and update ccpnInternalData as required
        """
        result = super()._restoreObject(project, apiObj)

        _data = result.data
        if _data is None:
            # make sure that data is the correct type
            getLogger().debug(f'{result.pid}: data is not defined - resetting to an empty table')
            result.data = EnsembleData()

        elif not isinstance(_data, EnsembleData):

            if isinstance(_data, pd.DataFrame):
                # make sure that data is the correct type
                getLogger().debug(f'Restoring object - converting to {EnsembleData}')
                result.data = EnsembleData(_data)

            else:
                # make sure that data is the correct type
                getLogger().debug(
                        f'Failed restoring object {result.pid}: data not of type {EnsembleData} - resetting to an empty table')
                result.data = EnsembleData()

        return result

    #===========================================================================================
    # new<Object> and other methods
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
            _label = f'my{Model.className}_{modelNumber}'
            _model = result.newModel(label=_label)
            _model._resetSerial(modelNumber)

    return result

#EJB 20181204: moved to Project
# Project.newStructureEnsemble = _newStructureEnsemble
# del _newStructureEnsemble

# Notifiers:
