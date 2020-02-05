"""
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2020"
__credits__ = ("Ed Brooksbank, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2020-02-05 09:39:57 +0000 (Wed, February 05, 2020) $"
__version__ = "$Revision: 3.0.0 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from typing import Tuple, Any
from functools import partial
from enum import Enum
from ccpn.core.Project import Project
from ccpn.core.Spectrum import Spectrum
from ccpn.core._implementation.AbstractWrapperObject import AbstractWrapperObject
from ccpn.core.lib import Pid
from ccpnmodel.ccpncore.api.ccp.nmr.Nmr import DataSource as ApiDataSource
from ccpnmodel.ccpncore.api.ccp.nmr.Nmr import SpectrumGroup as ApiSpectrumGroup
from ccpn.util.decorators import logCommand
from ccpn.core.lib.ContextManagers import newObject, ccpNmrV3CoreSetter, renameObject
from ccpn.util.Logging import getLogger


SPECTRUMGROUPSERIES = 'spectrumGroupSeries'
SPECTRUMGROUPSERIESUNITS = 'spectrumGroupSeriesUnits'
SPECTRUMGROUPSERIESTYPE = 'spectrumGroupSeriesType'

class SERIESTYPES(Enum):
    # NOTE:ED - could make this a labelledEnum
    DECIMAL = 0, 'Decimal'
    STRING = 1, 'String'
    PYTHONLITERAL = 2, 'Python Literal'

    def __new__(cls, *args, **kwds):
        obj = object.__new__(cls)
        obj._value_ = args[0]
        return obj

    # ignore the first param since it's already set by __new__
    def __init__(self, _: str, description: str = None):
        self._description_ = description

    def __str__(self):
        return self.value

    # this makes sure that the description is read-only
    @property
    def description(self):
        return self._description_


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
    # GWV hack to alleviate (temporarily) the loss of order on spectra
    #-------------------------------------------------------------------------------------------------------

    SPECTRUM_ORDER = 'spectrum_order'
    @property
    def spectra(self) -> Tuple[Spectrum, ...]:
        """Spectra that make up SpectrumGroup."""
        data2Obj = self._project._data2Obj
        data = [data2Obj[x] for x in self._wrappedData.dataSources]
        data = self._restoreObjectOrder(data, self.SPECTRUM_ORDER)
        return tuple(data)

    @spectra.setter
    @ccpNmrV3CoreSetter()
    def spectra(self, value):
        if not isinstance(value, (tuple,list)):
            raise ValueError('Expected a tuple or list')
        getDataObj = self._project._data2Obj.get
        data = [getDataObj(x) if isinstance(x, str) else x for x in value]
        # Store order
        self._saveObjectOrder(data, self.SPECTRUM_ORDER)
        # Store the api objects
        self._wrappedData.dataSources = [x._wrappedData for x in data]

    @property
    def series(self) -> Tuple[Any, ...]:
        """Returns a tuple of series items for the attached spectra

        series = (val1, val2, ..., valN)

        where val1-valN correspond to the series items in the attached spectra associated with this group
        For a spectrum with no values, returns None in place of Item
        """
        series = ()
        for spectrum in self.spectra:
            series += (spectrum._getSeriesItem(self),)

        return series

    @series.setter
    @ccpNmrV3CoreSetter()
    def series(self, items):
        """Setter for series
        series must be a tuple of items or Nones, the contents of the items are not checked
        Items can be anything but must all be the same type or None
        """
        if not isinstance(items, (tuple, list)):
            raise ValueError('Expected a tuple or list')
        if len(self.spectra) != len(items):
            raise ValueError('Number of items does not match number of spectra in group')
        diffItems = set(type(item) for item in items)
        if len(diffItems) > 2 or (len(diffItems) == 2 and type(None) not in diffItems):
            raise ValueError('Items must be of the same type (or None)')

        for spectrum, item in zip(self.spectra, items):
            spectrum._setSeriesItem(self, item)

    @property
    def seriesUnits(self):
        """Return the seriesUnits for the spectrumGroup
        """
        units = self.getParameter(SPECTRUMGROUPSERIES, SPECTRUMGROUPSERIESUNITS)
        return units

    @seriesUnits.setter
    def seriesUnits(self, value):
        """Set the seriesUnits for the spectrumGroup
        """
        if not isinstance(value, str):
            raise ValueError("seriesUnits must be a string.")

        self.setParameter(SPECTRUMGROUPSERIES, SPECTRUMGROUPSERIESUNITS, value)

    @property
    def seriesType(self):
        """Return the seriesType for the spectrumGroup
        """
        seriesType = self.getParameter(SPECTRUMGROUPSERIES, SPECTRUMGROUPSERIESTYPE)
        return seriesType

    @seriesType.setter
    def seriesType(self, value):
        """Set the seriesType for the spectrumGroup
        """
        if not isinstance(value, int):
            raise ValueError("seriesType must be an int.")

        self.setParameter(SPECTRUMGROUPSERIES, SPECTRUMGROUPSERIESTYPE, value)

    #=========================================================================================
    # Implementation functions
    #=========================================================================================

    def __init__(self, project, wrappedData):
        super().__init__(project=project, wrappedData=wrappedData)

    @classmethod
    def _getAllWrappedData(cls, parent: Project) -> list:
        """get wrappedData for all SpectrumGroups linked to NmrProject"""
        return parent._wrappedData.sortedSpectrumGroups()

    @renameObject()
    @logCommand(get='self')
    def rename(self, value: str):
        """Rename SpectrumGroup, changing its name and Pid.
        """
        self._validateName(value=value, allowWhitespace=False)

        # rename functions from here
        oldName = self.name
        self._wrappedData.__dict__['name'] = value
        return (oldName,)

    def _finaliseAction(self, action: str):
        """Subclassed to handle associated seriesValues instances
        """
        oldPid = self.pid
        super()._finaliseAction(action=action)
        # propagate the rename to associated seriesValues
        if action in ['rename']:
            # rename the items in _seriesValues as they are referenced by pid
            for spectrum in self.spectra:
                spectrum._renameSeriesItems(self, oldPid)

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
