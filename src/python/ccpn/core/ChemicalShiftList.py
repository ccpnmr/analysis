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
__dateModified__ = "$dateModified: 2020-11-02 17:47:51 +0000 (Mon, November 02, 2020) $"
__version__ = "$Revision: 3.0.1 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from typing import Tuple, Sequence, List
from functools import partial
from ccpn.util import Common as commonUtil
from ccpn.util.OrderedSet import OrderedSet
from ccpn.core.PeakList import PeakList
from ccpn.core.Project import Project
from ccpn.core.Spectrum import Spectrum
from ccpn.core._implementation.AbstractWrapperObject import AbstractWrapperObject
from ccpn.core.lib import Pid
from ccpnmodel.ccpncore.api.ccp.nmr import Nmr
from ccpn.util.decorators import logCommand
from ccpn.core.lib.ContextManagers import newObject, renameObject
from ccpn.util.Common import _incrementObjectName

class ChemicalShiftList(AbstractWrapperObject):
    """An object containing Chemical Shifts. Note: the object is not a (subtype of a) Python list.
    To access all ChemicalShift objects, use chemicalShiftList.chemicalShifts.

    A chemical shift list named 'default' is used by default for new experiments,
    and is created if necessary."""

    #: Short class name, for PID.
    shortClassName = 'CL'
    # Attribute it necessary as subclasses must use superclass className
    className = 'ChemicalShiftList'

    _parentClass = Project

    #: Name of plural link to instances of class
    _pluralLinkName = 'chemicalShiftLists'

    # the attribute name used by current
    _currentAttributeName = 'chemicalShiftLists'

    #: List of child classes.
    _childClasses = []

    # Qualified name of matching API class
    _apiClassQualifiedName = Nmr.ShiftList._metaclass.qualifiedName()

    def __init__(self, project: Project, wrappedData: Nmr.ShiftList):

        self._wrappedData = wrappedData
        self._project = project
        defaultName = 'Shifts%s' % wrappedData.serial
        self._setUniqueStringKey(defaultName)
        super().__init__(project, wrappedData)

    # CCPN properties
    @property
    def _apiShiftList(self) -> Nmr.ShiftList:
        """ CCPN ShiftList matching ChemicalShiftList"""
        return self._wrappedData

    @property
    def _key(self) -> str:
        """name, regularised as used for id"""
        return self._wrappedData.name.translate(Pid.remapSeparators)

    @property
    def serial(self) -> int:
        """Shift list serial number"""
        return self._wrappedData.serial

    @property
    def _parent(self) -> Project:
        """Parent (containing) object."""
        return self._project

    @property
    def name(self) -> str:
        """name of ChemicalShiftList. """
        return self._wrappedData.name

    @name.setter
    def name(self, value:str):
        """set name of ChemicalShiftList."""
        self.rename(value)

    @property
    def unit(self) -> str:
        """Measurement unit of ChemicalShiftList. Should always be 'ppm'"""
        return self._wrappedData.unit

    @unit.setter
    def unit(self, value: str):
        self._wrappedData.unit = value

    @property
    def autoUpdate(self) -> bool:
        """Automatically update Chemical Shifts from assigned peaks - True/False"""
        return self._wrappedData.autoUpdate

    @autoUpdate.setter
    def autoUpdate(self, value: bool):
        self._wrappedData.autoUpdate = value

    @property
    def isSimulated(self) -> bool:
        """True if the ChemicalShiftList is simulated."""
        return self._wrappedData.isSimulated

    @isSimulated.setter
    def isSimulated(self, value: bool):
        self._wrappedData.isSimulated = value

    # @property
    # def comment(self) -> str:
    #     """Free-form text comment"""
    #     return self._wrappedData.details
    #
    # @comment.setter
    # def comment(self, value: str):
    #     self._wrappedData.details = value

    @property
    def spectra(self) -> Tuple[Spectrum, ...]:
        """ccpn.Spectra that use ChemicalShiftList to store chemical shifts"""
        ff = self._project._data2Obj.get
        return tuple(sorted(ff(y) for x in self._wrappedData.experiments
                            for y in x.dataSources))

    @spectra.setter
    def spectra(self, value: Sequence[Spectrum]):
        self._wrappedData.experiments = set(x._wrappedData.experiment for x in value)

    #=========================================================================================
    # Implementation functions
    #=========================================================================================

    @logCommand(get='self')
    def duplicate(self, includeSpectra=False, autoUpdate=False):
        """
        :param includeSpectra: move the spectra to the newly created ChemicalShiftList
        :param autoUpdate: automatically update according to the project changes.
        :return: a duplicated copy of itself containing all chemicalShifts.
        """
        name = _incrementObjectName(self.project, self._pluralLinkName, self.name)
        ncsl = self.project.newChemicalShiftList(name)
        ncsl.spectra = self.spectra if includeSpectra else ()
        ncsl.autoUpdate = autoUpdate
        for att in ['unit', 'isSimulated', 'comment']:
            setattr(ncsl, att, getattr(self, att, None))
        list(map(lambda cs: cs.copyTo(ncsl), self.chemicalShifts))

    @classmethod
    def _getAllWrappedData(cls, parent: Project) -> List[Nmr.ShiftList]:
        """get wrappedData (ShiftLists) for all ShiftList children of parent Project"""
        return list(x for x in parent._apiNmrProject.sortedMeasurementLists()
                    if x.className == 'ShiftList')

    @renameObject()
    @logCommand(get='self')
    def rename(self, value: str):
        """Rename ChemicalShiftList, changing its name and Pid.
        """
        commonUtil._validateName(self.project, ChemicalShiftList, value=value, allowWhitespace=False)

        # rename functions from here
        oldName = self.name
        self._wrappedData.name = value
        return (oldName,)

    #=========================================================================================
    # CCPN functions
    #=========================================================================================

    #===========================================================================================
    # new'Object' and other methods
    # Call appropriate routines in their respective locations
    #===========================================================================================

    @logCommand(get='self')
    def newChemicalShift(self, value: float, nmrAtom,
                          valueError: float = 0.0, figureOfMerit: float = 1.0,
                          comment: str = None, **kwds):
        """Create new ChemicalShift within ChemicalShiftList.

        See the ChemicalShift class for details.

        Optional keyword arguments can be passed in; see Peak._newPeak for details.

        :param value:
        :param nmrAtom: nmrAtom as object or pid
        :param valueError:
        :param figureOfMerit:
        :param comment: optional comment string
        :return: a new ChemicalShift instance.
        """
        from ccpn.core.ChemicalShift import _newChemicalShift

        return _newChemicalShift(self, value, nmrAtom, valueError=valueError,
                                 figureOfMerit=figureOfMerit, comment=comment, **kwds)


#=========================================================================================
# Connections to parents:
#=========================================================================================

def getter(self: Spectrum) -> ChemicalShiftList:
    return self._project._data2Obj.get(self._apiDataSource.experiment.shiftList)


def setter(self: Spectrum, value: ChemicalShiftList):
    value = self.getByPid(value) if isinstance(value, str) else value
    if isinstance(value, ChemicalShiftList):
        self._apiDataSource.experiment.shiftList = value._apiShiftList


Spectrum.chemicalShiftList = property(getter, setter, None,
                                      "ccpn.ChemicalShiftList used for ccpn.Spectrum")


def getter(self: PeakList) -> ChemicalShiftList:
    return self._project._data2Obj.get(self._wrappedData.shiftList)


def setter(self: PeakList, value: ChemicalShiftList):
    value = self.getByPid(value) if isinstance(value, str) else value
    self._apiPeakList.shiftList = None if value is None else value._apiShiftList


PeakList.chemicalShiftList = property(getter, setter, None,
                                      "ChemicalShiftList associated with PeakList.")
del getter
del setter

#=========================================================================================

@newObject(ChemicalShiftList)
def _newChemicalShiftList(self: Project, name: str = None, unit: str = 'ppm', autoUpdate: bool = True,
                          isSimulated: bool = False, serial: int = None, comment: str = None,
                          spectra=()) -> ChemicalShiftList:
    """Create new ChemicalShiftList.

    See the ChemicalShiftList class for details.

    :param name:
    :param unit:
    :param autoUpdate:
    :param isSimulated:
    :param comment:
    :param serial: optional serial number.
    :return: a new ChemicalShiftList instance.
    """

    # EJB 20181212: this is from refactored
    # GWV 20181210: deal with already existing names by incrementing
    # name = name.translate(Pid.remapSeparators)
    # # find a name that is unique
    # found = (self.getChemicalShiftList(name) is not None)
    # while found:
    #     name = commonUtil.incrementName(name)
    #     found = (self.getChemicalShiftList(name) is not None)

    if spectra:
        getByPid = self._project.getByPid
        spectra = [getByPid(x) if isinstance(x, str) else x for x in spectra]

    if not name:
        name = ChemicalShiftList._nextAvailableName(ChemicalShiftList, self)
    commonUtil._validateName(self, ChemicalShiftList, name)

    dd = {'name': name, 'unit': unit, 'autoUpdate': autoUpdate, 'isSimulated': isSimulated,
          'details': comment}
    if spectra:
        dd.update({'experiments': OrderedSet([spec._wrappedData.experiment for spec in spectra])})

    apiChemicalShiftList = self._wrappedData.newShiftList(**dd)
    result = self._data2Obj.get(apiChemicalShiftList)
    if result is None:
        raise RuntimeError('Unable to generate new ChemicalShiftList item')

    if serial is not None:
        try:
            result.resetSerial(serial)
        except ValueError:
            self.project._logger.warning("Could not reset serial of %s to %s - keeping original value"
                                         % (result, serial))

    return result


def _getChemicalShiftList(self: Project, name: str = None, unit: str = 'ppm', autoUpdate: bool = True,
                          isSimulated: bool = False, serial: int = None, comment: str = None,
                          spectra=()) -> ChemicalShiftList:
    """Create new ChemicalShiftList.

    See the ChemicalShiftList class for details.

    :param name:
    :param unit:
    :param autoUpdate:
    :param isSimulated:
    :param comment:
    :param serial: optional serial number.
    :return: a new ChemicalShiftList instance.
    """

    # EJB 20181212: this is from refactored
    # GWV 20181210: deal with already existing names by incrementing
    # name = name.translate(Pid.remapSeparators)
    # # find a name that is unique
    # found = (self.getChemicalShiftList(name) is not None)
    # while found:
    #     name = commonUtil.incrementName(name)
    #     found = (self.getChemicalShiftList(name) is not None)

    if spectra:
        getByPid = self._project.getByPid
        spectra = [getByPid(x) if isinstance(x, str) else x for x in spectra]

    # if not name:
    #     name = ChemicalShiftList._nextAvailableName(ChemicalShiftList, self)
    # # match the error message to the attribute
    # commonUtil._validateName(self, ChemicalShiftList, name)

    dd = {'name': name, 'unit': unit, 'autoUpdate': autoUpdate, 'isSimulated': isSimulated,
          'details': comment}
    if spectra:
        dd.update({'experiments': OrderedSet([spec._wrappedData.experiment for spec in spectra])})

    apiChemicalShiftList = self._wrappedData.getShiftList(**dd)
    result = self._data2Obj.get(apiChemicalShiftList)
    return result


#EJB 20181205: moved to Project
# Project.newChemicalShiftList = _newChemicalShiftList
# del _newChemicalShiftList

# Notifiers
className = Nmr.ShiftList._metaclass.qualifiedName()
Project._apiNotifiers.extend(
        (('_finaliseApiRename', {}, className, 'setName'),
         ('_modifiedLink', {'classNames': ('ChemicalShiftList', 'Spectrum')}, className, 'addExperiment'),
         ('_modifiedLink', {'classNames': ('ChemicalShiftList', 'Spectrum')}, className,
          'removeExperiment'),
         ('_modifiedLink', {'classNames': ('ChemicalShiftList', 'Spectrum')}, className, 'setExperiments'),
         ('_modifiedLink', {'classNames': ('ChemicalShiftList', 'PeakList')}, className, 'addPeakList'),
         ('_modifiedLink', {'classNames': ('ChemicalShiftList', 'PeakList')}, className, 'removePeakList'),
         ('_modifiedLink', {'classNames': ('ChemicalShiftList', 'PeakList')}, className, 'setPeakLists'),
         )
        )
Project._apiNotifiers.append(('_modifiedLink', {'classNames': ('ChemicalShiftList', 'PeakList')},
                              Nmr.PeakList._metaclass.qualifiedName(), 'setSpecificShiftList')
                             )
className = Nmr.Experiment._metaclass.qualifiedName()
Project._apiNotifiers.extend(
        (('_modifiedLink', {'classNames': ('ChemicalShiftList', 'Spectrum')}, className, 'setShiftList'),
         ('_modifiedLink', {'classNames': ('ChemicalShiftList', 'PeakList')}, className, 'setShiftList'),
         )
        )
