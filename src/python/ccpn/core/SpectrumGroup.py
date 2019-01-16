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
__dateModified__ = "$dateModified: 2017-07-07 16:32:30 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.b4 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from typing import Tuple
from functools import partial
from ccpn.core.Project import Project
from ccpn.core.Spectrum import Spectrum
from ccpn.core._implementation.AbstractWrapperObject import AbstractWrapperObject
from ccpn.core.lib import Pid
from ccpnmodel.ccpncore.api.ccp.nmr.Nmr import DataSource as ApiDataSource
from ccpnmodel.ccpncore.api.ccp.nmr.Nmr import SpectrumGroup as ApiSpectrumGroup
from ccpnmodel.ccpncore.lib import Util as coreUtil
from ccpn.util.decorators import logCommand
from ccpn.core.lib.ContextManagers import newObject, deleteObject, ccpNmrV3CoreSetter, \
    logCommandBlock, undoStackBlocking, renameObject
from ccpn.util.Logging import getLogger


class SpectrumGroup(AbstractWrapperObject):
    """Combines multiple Spectrum objects into a group, so they can be treated as a single object.
    """

    #: Short class name, for PID.
    shortClassName = 'SG'
    # Attribute it necessary as subclasses must use superclass className
    className = 'SpectrumGroup'

    _parentClass = Project

    #: Name of plural link to instances of class
    _pluralLinkName = 'spectrumGroups'

    # the attribute name used by current
    _currentAttributeName = 'spectrumGroup'

    #: List of child classes.
    _childClasses = []

    # Qualified name of matching API class
    _apiClassQualifiedName = ApiSpectrumGroup._metaclass.qualifiedName()

    # CCPN properties
    @property
    def _apiSpectrumGroup(self) -> ApiSpectrumGroup:
        """ CCPN Project SpectrumGroup"""
        return self._wrappedData

    def _getSpectrumGroupChildrenByClass(self, klass):
        """Return the list of spectra attached to the spectrumGroup.
        """
        if klass is Spectrum:
            return tuple(spectrum for spectrum in self.spectra)
        else:
            return []

    @property
    def _key(self) -> str:
        """Residue local ID"""
        return self._wrappedData.name.translate(Pid.remapSeparators)

    @property
    def name(self) -> str:
        """Name of SpectrumGroup, part of identifier"""
        return self._wrappedData.name

    @name.setter
    def name(self, value:str):
        """set name of SpectrumGroup."""
        self.rename(value)

    @property
    def serial(self) -> str:
        """Serial number  of SpectrumGroup, used for sorting"""
        return self._wrappedData.serial

    @property
    def _parent(self) -> Project:
        """Parent (containing) object."""
        return self._project

    @property
    def spectra(self) -> Tuple[Spectrum, ...]:
        """Spectra that make up SpectrumGroup."""
        data2Obj = self._project._data2Obj
        return tuple(data2Obj[x] for x in self._wrappedData.dataSources)

    @spectra.setter
    def spectra(self, value):
        getDataObj = self._project._data2Obj.get
        value = [getDataObj(x) if isinstance(x, str) else x for x in value]
        # self._wrappedData.dataSources = [x._wrappedData for x in value]
        apiSpectra = [x._wrappedData for x in value]
        self._wrappedData.setDataSources(apiSpectra)

    #=========================================================================================
    # Implementation functions
    #=========================================================================================

    @classmethod
    def _getAllWrappedData(cls, parent: Project) -> list:
        """get wrappedData for all SpectrumGroups linked to NmrProject"""
        return parent._wrappedData.sortedSpectrumGroups()

    @logCommand(get='self')
    def rename(self, value: str):
        """Rename SpectrumGroup, changing its name and Pid.
        """
        self._validateName(value=value, allowWhitespace=False)

        with renameObject(self) as addUndoItem:
            oldName = self.name
            self._wrappedData.__dict__['name'] = value

            addUndoItem(undo=partial(self.rename, oldName),
                        redo=partial(self.rename, value))

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

@newObject(SpectrumGroup)
def _newSpectrumGroup(self: Project, name: str, spectra=(), serial: int = None) -> SpectrumGroup:
    """Create new SpectrumGroup

    See the SpectrumGroup class for details.

    :param name: name for the new SpectrumGroup
    :param spectra: optional list of spectra as objects or pids
    :param serial: optional serial number
    :return: a new SpectrumGroup instance.
    """

    if name and Pid.altCharacter in name:
        raise ValueError("Character %s not allowed in ccpn.SpectrumGroup.name" % Pid.altCharacter)

    if spectra:
        getByPid = self._project.getByPid
        spectra = [getByPid(x) if isinstance(x, str) else x for x in spectra]

    apiSpectrumGroup = self._wrappedData.newSpectrumGroup(name=name)
    result = self._data2Obj.get(apiSpectrumGroup)
    if result is None:
        raise RuntimeError('Unable to generate new SpectrumGroup item')

    if serial is not None:
        try:
            result.resetSerial(serial)
        except ValueError:
            getLogger().warning("Could not reset serial of %s to %s - keeping original value"
                                         % (result, serial))
    if spectra:
        result.spectra = spectra

    return result


#EJB 2181206: moved to Project
# Project.newSpectrumGroup = _newSpectrumGroup
# del _newSpectrumGroup


# reverse link Spectrum.spectrumGroups
def getter(self: Spectrum) -> Tuple[SpectrumGroup, ...]:
    data2Obj = self._project._data2Obj
    return tuple(sorted(data2Obj[x] for x in self._wrappedData.spectrumGroups))


def setter(self: Spectrum, value):
    self._wrappedData.spectrumGroups = [x._wrappedData for x in value]


#
Spectrum.spectrumGroups = property(getter, setter, None,
                                   "SpectrumGroups that contain Spectrum")
del getter
del setter

# Extra Notifiers to notify changes in Spectrum-SpectrumGroup link
className = ApiSpectrumGroup._metaclass.qualifiedName()
Project._apiNotifiers.extend(
        (('_modifiedLink', {'classNames': ('Spectrum', 'SpectrumGroup')}, className, 'addDataSource'),
         ('_modifiedLink', {'classNames': ('Spectrum', 'SpectrumGroup')}, className, 'removeDataSource'),
         ('_modifiedLink', {'classNames': ('Spectrum', 'SpectrumGroup')}, className, 'setDataSources'),
         )
        )
className = ApiDataSource._metaclass.qualifiedName()
Project._apiNotifiers.extend(
        (('_modifiedLink', {'classNames': ('Spectrum', 'SpectrumGroup')}, className, 'addSpectrumGroup'),
         ('_modifiedLink', {'classNames': ('Spectrum', 'SpectrumGroup')}, className, 'removeSpectrumGroup'),
         ('_modifiedLink', {'classNames': ('Spectrum', 'SpectrumGroup')}, className, 'setSpectrumGroups'),
         )
        )

#-------------------------------------------------------------------------------------------------------
# GWV hack to alleviate (temporarily) the loass of order on spectra
# Hotfix api routines; UGLY!!!
#-------------------------------------------------------------------------------------------------------
from ccpnmodel.ccpncore.api.ccp.nmr.Nmr import SpectrumGroup as _ApiSpectrumGroup
from ccpnmodel.ccpncore.api.ccp.nmr.Nmr import DataSource
from ccpnmodel.ccpncore.memops.ApiError import ApiError


def _setDataSources(self, values):
    """
    Set for ccp.nmr.Nmr.SpectrumGroup.dataSources
    """
    dataDict = self.__dict__
    # xx = values
    # values = set(values)
    if (len(values) != len(set(values))):
        raise ApiError("""%s.setDataSources:
     values may not contain duplicates""" % self.qualifiedName
                       + ": %s" % (self,)
                       )

    for value in values:
        if (not isinstance(value, DataSource)):
            raise ApiError("""%s.setDataSources:
       value is not of class ccp.nmr.Nmr.DataSource""" % self.qualifiedName
                           + ": %s" % (value,)
                           )

    topObject = dataDict.get('topObject')
    currentValues = dataDict.get('dataSources')
    notInConstructor = not (dataDict.get('inConstructor'))

    root = topObject.__dict__.get('memopsRoot')
    notOverride = not (root.__dict__.get('override'))
    notIsReading = not (topObject.__dict__.get('isReading'))
    notOverride = (notOverride and notIsReading)
    if (notIsReading):
        if (notInConstructor):
            if (not (topObject.__dict__.get('isModifiable'))):
                raise ApiError("""%s.setDataSources:
         Storage not modifiable""" % self.qualifiedName
                               + ": %s" % (topObject,)
                               )

    if (dataDict.get('isDeleted')):
        raise ApiError("""%s.setDataSources:
     called on deleted object""" % self.qualifiedName
                       )

    for obj in values:
        if (obj.__dict__.get('isDeleted')):
            raise ApiError("""%s.setDataSources:
       an object in values is deleted""" % self.qualifiedName
                           )

    try:
        if (values == currentValues):
            return

    except ValueError as ex:
        pass
    except TypeError as ex:
        pass
    if (notOverride):
        xx1 = dataDict.get('topObject')
        for value in values:
            yy1 = value.__dict__.get('topObject')
            if (not (xx1 is yy1)):
                raise ApiError("""%s.setDataSources:
         Link dataSources between objects from separate partitions
          - memops.Implementation.TopObject does not match""" % self.qualifiedName
                               + ": %s:%s" % (self, value)
                               )

    for cv in currentValues:
        if (not (cv in values)):
            oldSelves = cv.__dict__.get('spectrumGroups')
            oldSelves.remove(self)

    for cv in values:
        if (not (cv in currentValues)):
            oldSelves = cv.__dict__.get('spectrumGroups')
            oldSelves.add(self)

    dataDict['dataSources'] = values
    if (notIsReading):
        if (notInConstructor):
            topObject.__dict__['isModified'] = True

    # doNotifies

    if ((notInConstructor and notOverride)):

        _notifies = self.__class__._notifies

        ll1 = _notifies['']
        for notify in ll1:
            notify(self)

        ll = _notifies.get('setDataSources')
        if ll:
            for notify in ll:
                if notify not in ll1:
                    notify(self)

    if ((notInConstructor and notIsReading)):
        # register Undo functions

        _undo = root._undo
        if _undo is not None:
            _undo.newItem(self.setDataSources, self.setDataSources,
                          undoArgs=(currentValues,), redoArgs=(values,))

# hotfixing
_ApiSpectrumGroup.setDataSources = _setDataSources