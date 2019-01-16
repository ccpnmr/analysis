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
from ccpn.framework.constants import CCPNMR_PREFIX

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

    #-------------------------------------------------------------------------------------------------------
    # GWV hack to alleviate (temporarily) the loass of order on spectra
    #-------------------------------------------------------------------------------------------------------

    SPECTRUM_ORDER = 'spectrum_order'
    @property
    def spectra(self) -> Tuple[Spectrum, ...]:
        """Spectra that make up SpectrumGroup."""
        data2Obj = self._project._data2Obj
        data = [data2Obj[x] for x in self._wrappedData.dataSources]

        pids = self.getParameter(CCPNMR_PREFIX, self.SPECTRUM_ORDER)
        spectra = data
        # see if we can use the pids dict to reconstruct the order
        if pids is not None:
            dataDict = dict([(s.pid, s) for s in data])
            spectra = [dataDict[p] for p in pids if p in dataDict]
            if len(spectra) != len(data):
                # we failed
                spectra = data
        return tuple(spectra)

    @spectra.setter
    def spectra(self, value):
        getDataObj = self._project._data2Obj.get
        value = [getDataObj(x) if isinstance(x, str) else x for x in value]
        # store pids in order
        pids = [v.pid for v in value]
        self.setParameter(CCPNMR_PREFIX, self.SPECTRUM_ORDER, pids)
        self._wrappedData.dataSources = [x._wrappedData for x in value]

    #=========================================================================================
    # Implementation functions
    #=========================================================================================

    def __init__(self, project, wrappedData):
        super().__init__(project=project, wrappedData=wrappedData)

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
