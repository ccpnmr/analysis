"""
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2019"
__credits__ = ("Ed Brooksbank, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: CCPN $"
__dateModified__ = "$dateModified: 2017-07-07 16:32:28 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.b4 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

import typing
import pandas as pd
import collections
from ccpn.core._implementation.AbstractWrapperObject import AbstractWrapperObject
from ccpn.core.StructureEnsemble import StructureEnsemble
from ccpn.util.StructureData import EnsembleData
from ccpnmodel.ccpncore.api.ccp.molecule.MolStructure import Model as ApiModel
from ccpn.util.decorators import logCommand
from ccpn.core.lib.ContextManagers import newObject, deleteObject, ccpNmrV3CoreSetter, \
    logCommandBlock, undoBlock
from ccpn.util.Logging import getLogger


logger = getLogger()


class ModelData:
    """
    A view of a single model within an ensemble.

    Once created, a ModelData object *should* behave exactly like an Ensemble.
    If it doesn't, please report it as a bug.

    Note that ModelData objects are only valid when linked to an existing StructureEnsemble
    and that self._modelNumber must match
    """

    def __init__(self, model: 'Model' = None) -> None:

        # Model CCPN object that contains ModelData. The object is ONLY valid when self._model is set
        self._model = model

    @property
    def _modelNumber(self) -> int:
        # Serial number for model containing ModelData
        return self._model.serial

    @property
    def _ensemble(self) -> EnsembleData:
        """EnsembleData object on which the ModelData are a view"""
        return self._model.structureEnsemble.data

    @property
    def _modelNumberIndices(self) -> typing.Tuple[int, int]:
        """Get indices (in the pandas sense, elements of the index column,
        in theory need not be integers). These should be used with self._ensemble.loc"""
        data = self._ensemble
        if data is not None:
            # NB, you have to do this with a Series,
            # as new DataFrames are automatically reset to 1-start index
            modelNumberSeries = data['modelNumber']
            modelFilter = modelNumberSeries[modelNumberSeries == self._modelNumber]
            if modelFilter.shape[0] > 0:
                modelStart = modelFilter.index[0]
                modelEnd = modelFilter.index[-1]
                return (modelStart, modelEnd)
        # No data found for the model:
        return None

    def __str__(self) -> str:
        # This relies on the EnsembleData.__str__ having (only) the class name and the number of
        # models before the first ','
        s = str(self._ensemble).split(',', 1)[1]
        return '<ModelData model=%s (%s' % (self._modelNumber, s)

    def __getattr__(self, attr: str) -> typing.Any:

        if hasattr(self._ensemble, attr):
            if attr in self._ensemble.columns:
                # Use __getitem__
                return self[attr]

            elif attr == 'index':
                mni = self._modelNumberIndices
                if mni is None:
                    # This should give an empty series of whatever type the index is (?)
                    return pd.Series(self._ensemble.index[0:0])
                else:
                    # Set e to a slice of the ensemble data
                    e = self._ensemble.loc[mni[0]:mni[1]]
                    # e.reset_index(inplace=True, drop=True)

            else:
                # This is not a column - the indices are irrelevant. Just work on the full ensemble
                e = self._ensemble

            #
            return ChainedAssignmentWarningSuppressor(getattr(e, attr))

        else:
            raise AttributeError("'Model' object has no attribute '{}'".format(attr))

    def __getitem__(self, key: str) -> typing.Any:

        if key in self._ensemble.columns:
            mni = self._modelNumberIndices
            if mni is None:
                # No data present - return empty series, paying attention to type
                return pd.Series(dtype=self._ensemble.dtypes[key])
            else:
                # Set get item from a slice of the ensemble data
                e = self._ensemble.loc[mni[0]:mni[1]]
                # e.reset_index(inplace=True, drop=True)
                return e[key]

        else:
            # Should probably throw an error, but anyway we leave that to pandas
            try:
                return self._ensemble.__getitem__(key)
            except:
                raise KeyError("'Model' object has no key '{}'".format(key))

    def __setitem__(self, key: str, value: typing.Any) -> None:

        # Works by creating a view on the ensemble and using the ensemble.__setitem__ on that.

        mni = self._modelNumberIndices
        if mni is None:
            raise ValueError("Cannot set column values, model %s has no data" % self._model)

        else:
            e = self._ensemble.loc[mni[0]:mni[1]]
            # e.reset_index(inplace=True, drop=True)

            pd.set_option('chained_assignment', None)
            # NB This switch is a nasty hack, done to get the echoing and undoing to work
            structureEnsemble = e._containingObject
            e._containingObject = self._model
            try:
                e[key] = value
            finally:
                e._containingObject = structureEnsemble
                pd.set_option('chained_assignment', 'warn')


class Model(AbstractWrapperObject):
    """ ccpn.Model - Structural Model, or one member of the structure ensemble."""

    #: Short class name, for PID.
    shortClassName = 'MD'

    # Attribute it necessary as subclasses must use superclass className
    className = 'Model'

    _parentClass = StructureEnsemble

    #: Name of plural link to instances of class
    _pluralLinkName = 'models'

    #: List of child classes.
    _childClasses = []

    # Qualified name of matching API class
    _apiClassQualifiedName = ApiModel._metaclass.qualifiedName()

    # Sentinel, to check if modelData view object has been created
    _modelData = None

    # CCPN properties
    @property
    def _apiModel(self) -> ApiModel:
        """ API Model matching Model"""
        return self._wrappedData

    @property
    def _key(self) -> str:
        """id string - ID number converted to string"""
        return str(self._wrappedData.serial)

    @property
    def serial(self) -> int:
        """ID number of Model, used in Pid and to identify the Model. """
        return self._wrappedData.serial

    @property
    def _parent(self) -> StructureEnsemble:
        """StructureEnsemble containing Model."""
        return self._project._data2Obj[self._wrappedData.structureEnsemble]

    structureEnsemble = _parent

    @property
    def label(self) -> str:
        """title of Model -  a line of free-form text."""
        return self._wrappedData.name

    @label.setter
    def label(self, value):
        self._wrappedData.name = value

    @property
    def data(self) -> ModelData:
        """Model data pandas object - a view on the data in the StructureEnsemble."""
        result = self._modelData
        if result is None:
            result = self._modelData = ModelData(model=self)
        #
        return result

    # @property
    # def comment(self) -> str:
    #     """Free-form text comment"""
    #     return self._wrappedData.details
    #
    # @comment.setter
    # def comment(self, value: str):
    #     self._wrappedData.details = value

    def clearData(self):
        """Remove all data for model by successively calling the deleteRow method
        """
        data = self.structureEnsemble.data
        if data is not None:

            containingObject = data._containingObject  # supresses the creation of intermediate

            from ccpn.core.lib.ContextManagers import logCommandBlock

            with logCommandBlock(get='self') as log:
                log('clearData')

                if 'modelNumber' in data.columns:
                    # If there are no modelNumbers, we must be in the process of deleting
                    # the modelNumbers column, or some similar shenanigans.
                    # Anyway, you do not clear the data if there are none to clear. OK.
                    data.deleteSelectedRows(modelNumbers=int(self.serial))

        else:
            logger.debug('StructureEnsemble %s contains no data for %s'.format(self.structureEnsemble.pid, self.pid))

    #=========================================================================================
    # Implementation functions
    #=========================================================================================

    @classmethod
    def _getAllWrappedData(cls, parent: StructureEnsemble) -> list:
        """get wrappedData - all Model children of parent StructureEnsemble"""
        return parent._wrappedData.sortedModels()

    def delete(self):
        """Delete should notify structureEnsemble of a delete.
        """
        with undoBlock():
            self.clearData()
            super().delete()

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

@newObject(Model)
def _newModel(self: StructureEnsemble, serial: int = None, label: str = None, comment: str = None) -> Model:
    """Create new Model.

    See the Model class for details.

    :param label:
    :param comment:
    :param serial: optional serial number.
    :return: a new Model instance.
    """

    structureEnsemble = self._wrappedData

    newApiModel = structureEnsemble.newModel(name=label, details=comment)
    result = self._project._data2Obj.get(newApiModel)
    if result is None:
        raise RuntimeError('Unable to generate new Model item')

    if serial is not None:
        try:
            result.resetSerial(serial)
        except ValueError:
            self.project._logger.warning("Could not reset serial of %s to %s - keeping original value"
                                         % (result, serial))

    return result


#EJB 20181204: moved to StructureEnsemble
# StructureEnsemble.newModel = _newModel
# del _newModel

#EJB 20181122: moved to _finaliseAction
# Notifiers:
# Model._setupCoreNotifier('delete', Model.clearData)


class ChainedAssignmentWarningSuppressor:
    """
    Suppress Pandas' warnings about chained assignment when using an assignment strategy
    known to not suffer from chained assignment.
    """

    def __init__(self, f: typing.Any) -> None:
        self.__f = f

    def __call__(self, *args, **kwargs) -> typing.Any:
        pd.set_option('chained_assignment', None)
        o = self.__f(*args, **kwargs)
        pd.set_option('chained_assignment', 'warn')
        return o

    def __getitem__(self, key: str) -> typing.Any:
        return self.__f[key]

    def __setitem__(self, key: str, value: typing.Any):
        pd.set_option('chained_assignment', None)
        self.__f[key] = value
        pd.set_option('chained_assignment', 'warn')

    def __get__(self, obj: typing.Any) -> typing.Any:
        return self.__f

    def __set__(self, obj: typing.Any, value: typing.Any) -> None:
        self.__f = value

    def __repr__(self) -> typing.Any:
        return self.__f.__repr__()

    def __str__(self) -> str:
        return self.__f.__str__()
