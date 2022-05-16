"""
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (https://www.ccpn.ac.uk) 2014 - 2022"
__credits__ = ("Ed Brooksbank, Joanna Fox, Victoria A Higman, Luca Mureddu, Eliza Płoskoń",
               "Timothy J Ragan, Brian O Smith, Gary S Thompson & Geerten W Vuister")
__licence__ = ("CCPN licence. See https://ccpn.ac.uk/software/licensing/")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2022-05-16 10:48:21 +0100 (Mon, May 16, 2022) $"
__version__ = "$Revision: 3.1.0 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from typing import Tuple, Any
import numpy as np
from ccpnmodel.ccpncore.api.ccp.nmr.Nmr import DataSource as ApiDataSource
from ccpnmodel.ccpncore.api.ccp.nmr.Nmr import SpectrumGroup as ApiSpectrumGroup
from ccpn.core.Project import Project
from ccpn.core.Spectrum import Spectrum
from ccpn.core._implementation.AbstractWrapperObject import AbstractWrapperObject
from ccpn.core.lib import Pid
from ccpn.core.lib.ContextManagers import newObject, ccpNmrV3CoreSetter, renameObject
from ccpn.util.decorators import logCommand
from ccpn.util.Logging import getLogger
from ccpn.util.DataEnum import DataEnum


class SeriesTypes(DataEnum):
    """
    Class to handle series types in spectrumGroups
    """
    FLOAT = 0, 'Float'
    INTEGER = 1, 'Integer'
    STRING = 2, 'String'
    PYTHONLITERAL = 3, 'Python Literal'


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

    # internal namespace
    _COMMENT = 'comment'
    _SERIES = 'series'
    _SERIESUNITS = 'seriesUnits'
    _SERIESTYPE = 'seriesType'
    _POSITIVECONTOURCOLOUR = 'positiveContourColour'
    _NEGATIVECONTOURCOLOUR = 'negativeContourColour'
    _SLICECOLOUR = 'sliceColour'

    #=========================================================================================
    # CCPN properties
    #=========================================================================================

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
    def name(self, value: str):
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
    def comment(self) -> str:
        """Free-form text comment"""
        comment = self._getInternalParameter(self._COMMENT)
        return comment

    @comment.setter
    @logCommand(get='self', isProperty=True)
    @ccpNmrV3CoreSetter()
    def comment(self, value: str):
        """set optional comment of SpectrumGroup."""
        if not isinstance(value, (str, type(None))):
            raise ValueError("comment must be a string/None.")

        self._setInternalParameter(self._COMMENT, value)

    @property
    def sliceColour(self) -> str:
        """1D slice colour for group"""
        colour = self._getInternalParameter(self._SLICECOLOUR)
        return colour

    @sliceColour.setter
    @logCommand(get='self', isProperty=True)
    @ccpNmrV3CoreSetter()
    def sliceColour(self, value: str):
        """1D slice colour for group"""
        if not isinstance(value, (str, type(None))):
            raise ValueError("sliceColour must be a string/None.")

        self._setInternalParameter(self._SLICECOLOUR, value)

    @property
    def positiveContourColour(self) -> str:
        """nD positive contour colour for group"""
        colour = self._getInternalParameter(self._POSITIVECONTOURCOLOUR)
        return colour

    @positiveContourColour.setter
    @logCommand(get='self', isProperty=True)
    @ccpNmrV3CoreSetter()
    def positiveContourColour(self, value: str):
        """nD positive contour colour for group"""
        if not isinstance(value, (str, type(None))):
            raise ValueError("positiveContourColour must be a string/None.")

        self._setInternalParameter(self._POSITIVECONTOURCOLOUR, value)

    @property
    def negativeContourColour(self) -> str:
        """nD negative contour colour for group"""
        colour = self._getInternalParameter(self._NEGATIVECONTOURCOLOUR)
        return colour

    @negativeContourColour.setter
    @logCommand(get='self', isProperty=True)
    @ccpNmrV3CoreSetter()
    def negativeContourColour(self, value: str):
        """nD negative contour colour for group"""
        if not isinstance(value, (str, type(None))):
            raise ValueError("negativeContourColour must be a string/None.")

        self._setInternalParameter(self._NEGATIVECONTOURCOLOUR, value)

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
    @logCommand(get='self', isProperty=True)
    @ccpNmrV3CoreSetter()
    def spectra(self, value):
        if not isinstance(value, (tuple, list)):
            raise ValueError('Expected a tuple or list')
        getDataObj = self._project._data2Obj.get
        data = [getDataObj(x) if isinstance(x, str) else x for x in value]
        # Store order
        self._saveObjectOrder(data, self.SPECTRUM_ORDER)
        # Store the api objects
        self._wrappedData.dataSources = [x._wrappedData for x in data]

    def addSpectrum(self, spectrum, seriesValue=None):
        """Add a spectrum Instance to the spectrum group

        :param spectrum: a Spectrum instance to be added to the group
        :param seriesValue: a value associated with this series
        """
        if not isinstance(spectrum, Spectrum):
            raise RuntimeError('Can only add Spectrum instances to a spectrumGroup; got %s' % spectrum)

        # For now: cumbersome; TODO the setter on self.spectra should disappear
        _spectra = list(self.spectra)
        _spectra.append(spectrum)

        _series = list(self.series)
        _series.append(seriesValue)

        self.spectra = _spectra
        self.series = _series

    @property
    def series(self) -> Tuple[Any, ...]:
        """Returns a tuple of series items for the attached spectra

        series = (val1, val2, ..., valN)

        where val1-valN correspond to the series items in the attached spectra associated with this group
        For a spectrum with no values, returns None in place of Item
        """
        # series = ()
        # for spectrum in self.spectra:
        #     series += (spectrum._getSeriesItem(self),)
        result = [sp._getSeriesItem(self) for sp in self.spectra]
        return tuple(result)

    @series.setter
    @logCommand(get='self', isProperty=True)
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
        units = self._getInternalParameter(self._SERIESUNITS)
        return units

    @seriesUnits.setter
    @logCommand(get='self', isProperty=True)
    @ccpNmrV3CoreSetter()
    def seriesUnits(self, value):
        """Set the seriesUnits for the spectrumGroup
        """
        if not isinstance(value, (str, type(None))):
            raise ValueError("seriesUnits must be a string or None.")

        self._setInternalParameter(self._SERIESUNITS, value)

    @property
    def seriesType(self):
        """Return the seriesType for the spectrumGroup
        """
        seriesType = self._getInternalParameter(self._SERIESTYPE)
        return seriesType

    @seriesType.setter
    @logCommand(get='self', isProperty=True)
    @ccpNmrV3CoreSetter()
    def seriesType(self, value):
        """Set the seriesType for the spectrumGroup
        """
        if not isinstance(value, (int, type(None))):
            raise ValueError("seriesType must be an int or None.")

        self._setInternalParameter(self._SERIESTYPE, value)

    @property
    def seriesPeakHeightForPosition(self):
        """
        return: Pandas DataFrame with the following structure:
                Index: multiIndex => axisCodes as levels;
                Columns => NR_ID: ID for the nmrResidue(s) assigned to the peak if available
                           Spectrum series values sorted by ascending values, if series values are not set, then the
                           spectrum name is used instead.

                        |  NR_ID  |   SP1     |    SP2    |   SP3
            H     N     |         |           |           |
           -------------+-------- +-----------+-----------+---------
            7.5  104.3  | A.1.ARG |    10     |  100      | 1000

            """
        from ccpn.core.lib.peakUtils import getSpectralPeakHeights

        return getSpectralPeakHeights(self.spectra)

    @property
    def seriesPeakHeightForNmrResidue(self):
        """
        return: Pandas DataFrame with the following structure:
                Index:  ID for the nmrResidue(s) assigned to the peak ;
                Columns => Spectrum series values sorted by ascending values, if series values are not set, then the
                           spectrum name is used instead.

                       |   SP1     |    SP2    |   SP3
            NR_ID      |           |           |           |
           ------------+-----------+-----------+-----------+---------
            A.1.ARG    |    10     |  100      | 1000

            """
        from ccpn.core.lib.peakUtils import getSpectralPeakHeightForNmrResidue

        return getSpectralPeakHeightForNmrResidue(self.spectra)

    def sortSpectraBySeries(self, reverse=True):
        if not None in self.series:
            series = np.array(self.series)
            if reverse:
                ind = series.argsort()[::-1]
            else:
                ind = series.argsort()
            self.spectra = list(np.array(self.spectra)[ind])
            self.series = list(series[ind])

    def sortSpectraByName(self, reverse=True):
        from ccpn.util.Common import sortObjectByName

        spectra = list(self.spectra)
        sortObjectByName(spectra, reverse=reverse)
        self.spectra = spectra

    def clone(self):
        # name = _incrementObjectName(self.project, self._pluralLinkName, self.name)
        newSpectrumGroup = self.project.newSpectrumGroup(name=self.name, spectra=self.spectra)
        attrNames = ['series', 'seriesType', 'seriesUnits', 'sliceColour',
                     'positiveContourColour', 'negativeContourColour', 'comment']
        for name in attrNames:
            val = getattr(self, name, None)
            try:
                setattr(newSpectrumGroup, name, val)
            except Exception as e:
                getLogger().warning('Error cloning: %s. Invalid attr: %s - %s' % (self.pid, name, str(e)))

        return newSpectrumGroup

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
        name = self._uniqueName(project=self.project, name=value)

        # rename functions from here
        oldName = self.name
        self._oldPid = self.pid
        self._wrappedData.__dict__['name'] = name

        return (oldName,)

    def _finaliseAction(self, action: str):
        """Subclassed to handle associated seriesValues instances
        """
        oldPid = self.pid
        if not super()._finaliseAction(action):
            return

        # propagate the rename to associated seriesValues
        if action in ['rename']:
            # rename the items in _seriesValues as they are referenced by pid
            for spectrum in self.spectra:
                spectrum._renameSeriesItems(self, oldPid)

    @classmethod
    def _restoreObject(cls, project, apiObj):
        """Restore the object and update ccpnInternalData
        """
        SPECTRUMGROUP = 'spectrumGroup'
        SPECTRUMGROUPCOMMENT = 'spectrumGroupComment'
        SPECTRUMGROUPPOSITIVECONTOURCOLOUR = 'spectrumGroupPositiveContourColour'
        SPECTRUMGROUPNEGATIVECONTOURCOLOUR = 'spectrumGroupNegativeContourColour'
        SPECTRUMGROUPSLICECOLOUR = 'spectrumGroupSliceColour'
        SPECTRUMGROUPSERIES = 'spectrumGroupSeries'
        SPECTRUMGROUPSERIESUNITS = 'spectrumGroupSeriesUnits'
        SPECTRUMGROUPSERIESTYPE = 'spectrumGroupSeriesType'

        result = super()._restoreObject(project, apiObj)

        for namespace, param, newVar in [(SPECTRUMGROUP, SPECTRUMGROUPCOMMENT, cls._COMMENT),
                                         (SPECTRUMGROUP, SPECTRUMGROUPPOSITIVECONTOURCOLOUR, cls._POSITIVECONTOURCOLOUR),
                                         (SPECTRUMGROUP, SPECTRUMGROUPNEGATIVECONTOURCOLOUR, cls._NEGATIVECONTOURCOLOUR),
                                         (SPECTRUMGROUP, SPECTRUMGROUPSLICECOLOUR, cls._SLICECOLOUR),
                                         (SPECTRUMGROUPSERIES, SPECTRUMGROUPSERIESUNITS, cls._SERIESUNITS),
                                         (SPECTRUMGROUPSERIES, SPECTRUMGROUPSERIESTYPE, cls._SERIESTYPE),
                                         ]:
            if result.hasParameter(namespace, param):
                # move the internal parameter to the correct namespace
                value = result.getParameter(namespace, param)
                result.deleteParameter(namespace, param)
                result._setInternalParameter(newVar, value)

        return result

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
def _newSpectrumGroup(self: Project, name: str, spectra=(), **kwds) -> SpectrumGroup:
    """Create new SpectrumGroup

    See the SpectrumGroup class for details.

    :param name: name for the new SpectrumGroup
    :param spectra: optional list of spectra as objects or pids
    :return: a new SpectrumGroup instance.
    """

    if name and Pid.altCharacter in name:
        raise ValueError("Character %s not allowed in ccpn.SpectrumGroup.name" % Pid.altCharacter)

    name = SpectrumGroup._uniqueName(project=self, name=name)

    if spectra:
        getByPid = self._project.getByPid
        spectra = [getByPid(x) if isinstance(x, str) else x for x in spectra]

    apiSpectrumGroup = self._wrappedData.newSpectrumGroup(name=name)
    result = self._data2Obj.get(apiSpectrumGroup)
    if result is None:
        raise RuntimeError('Unable to generate new SpectrumGroup item')

    if spectra:
        result.spectra = spectra

    for param, value in kwds.items():
        if hasattr(result, param):
            setattr(result, param, value)
        else:
            getLogger().warning('%s does not have parameter "%s"; unable to set' %
                                (result, param)
                                )
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
