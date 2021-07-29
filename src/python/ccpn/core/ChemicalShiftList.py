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
__dateModified__ = "$dateModified: 2021-07-29 20:47:58 +0100 (Thu, July 29, 2021) $"
__version__ = "$Revision: 3.0.4 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

import pandas as pd
from typing import Tuple, Sequence, List, Union

from ccpnmodel.ccpncore.api.ccp.nmr import Nmr
from ccpn.core._implementation.AbstractWrapperObject import AbstractWrapperObject
from ccpn.core.PeakList import PeakList
from ccpn.core.Project import Project
from ccpn.core.Spectrum import Spectrum
from ccpn.core.NmrAtom import NmrAtom
from ccpn.core.lib import Pid
from ccpn.core.lib.ContextManagers import newObject, renameObject
from ccpn.util.decorators import logCommand
from ccpn.util.OrderedSet import OrderedSet


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
    def name(self, value: str):
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

    @property
    def spectra(self) -> Tuple[Spectrum, ...]:
        """ccpn.Spectra that use ChemicalShiftList to store chemical shifts"""
        ff = self._project._data2Obj.get
        return tuple(sorted(ff(y) for x in self._wrappedData.experiments
                            for y in x.dataSources))

    @spectra.setter
    def spectra(self, value: Sequence[Spectrum]):
        self._wrappedData.experiments = set(x._wrappedData.experiment for x in value)

    def getShift(self, nmrAtom: Union[None, NmrAtom, str] = None, uniqueId: int = None):
        """Return a chemicalShift by nmrAtom or uniqueId
        Shift is returned as a namedTuple
        """
        # NOTE:ED consider returning an AttrDict to allow chemicalShift properties

        if nmrAtom and uniqueId:
            raise ValueError('Please use either nmrAtom or uniqueId')

        _data = self._wrappedData.data
        if _data is None:
            return

        rows = None
        if nmrAtom:
            # get shift by nmrAtom
            nmrAtom = self.project.getByPid(nmrAtom) if isinstance(nmrAtom, str) else nmrAtom
            if not isinstance(nmrAtom, (NmrAtom, type(None))):
                raise ValueError('chemicalShiftList.getShift: nmrAtom must be of type NmrAtom or str')
            elif nmrAtom:
                # search table
                rows = _data[_data['nmrAtom'] == nmrAtom.pid]
        elif uniqueId:
            # get shift by uniqueId
            if not isinstance(uniqueId, int):
                raise ValueError('chemicalShiftList.getShift: uniqueId must be an int')
            else:
                # search table
                rows = _data[_data['uniqueId'] == uniqueId]

        if rows is not None:
            if len(rows) > 1:
                raise RuntimeError('chemicalShiftList.getShift: returned too many shifts')
            # return the row as a Pandas namedTuple
            for row in rows.itertuples():
                return row

    # new shift

    # delete shift

    # copy/clone shift

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
        # name = _incrementObjectName(self.project, self._pluralLinkName, self.name)
        ncsl = self.project.newChemicalShiftList()
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
        return self._rename(value)

    #=========================================================================================
    # CCPN functions
    #=========================================================================================

    def _updateEdgeToAlpha1(self):
        """Move chemicalShifts from model shifts to pandas dataFrame

        version 3.0.4 -> 3.1.0.alpha update
        dataframe now stored in _wrappedData.data
        """

        # skip for no shifts
        if not self.chemicalShifts:
            return

        # create a new dataframe
        shifts = []
        for row, shift in enumerate(self.chemicalShifts):
            newRow = shift._getShiftAsTuple()
            shifts.append(newRow)

            # delete the old shift
            shift.delete()

        # instantiate the dataframe
        df = pd.DataFrame(shifts,
                          columns=['uniqueId',
                                   'value', 'valueError', 'figureOfMerit',
                                   'nmrAtom', 'nmrChain', 'sequenceCode', 'residueType', 'atomName',
                                   'comment'])

        # put into model
        self._wrappedData.data = df

    @classmethod
    def _restoreObject(cls, project, apiObj):
        """Subclassed to allow for initialisations on restore, not on creation via newChemicalShiftList
        """
        from ccpn.util.Logging import getLogger

        chemicalShiftList = super()._restoreObject(project, apiObj)

        # keep a list of the update methods
        # this needs to be traversed on order from the latest version that the project has been saved under
        versionUpdates = (('3.0.4', cls._updateEdgeToAlpha1),
                          ('3.1.0', None),  # current version - just used for debug logging
                          )

        # check version history, default to 3.0.4
        history = (project.versionHistory and project.versionHistory[-1]) or '3.0.4'

        try:
            # get the index of the saved version, this SHOULD always work
            startIndex = [_ver for _ver, _func in versionUpdates].index(history)
        except:
            raise RuntimeError(f'ChemicalShiftList._restoreObject: current version is not defined {history}')

        lastIndex = len(versionUpdates)

        # iterate through the updates
        for (ver, func), (nextVer, _) in zip(versionUpdates[startIndex:lastIndex - 1], versionUpdates[startIndex + 1:lastIndex]):
            getLogger().debug(f'>>> updating version {ver} -> {nextVer}')
            func(chemicalShiftList)

        return chemicalShiftList

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
                          isSimulated: bool = False, comment: str = None,
                          spectra=()) -> ChemicalShiftList:
    """Create new ChemicalShiftList.

    See the ChemicalShiftList class for details.

    :param name:
    :param unit:
    :param autoUpdate:
    :param isSimulated:
    :param comment:
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

    name = ChemicalShiftList._uniqueName(project=self, name=name)

    dd = {'name'   : name, 'unit': unit, 'autoUpdate': autoUpdate, 'isSimulated': isSimulated,
          'details': comment}
    if spectra:
        dd.update({'experiments': OrderedSet([spec._wrappedData.experiment for spec in spectra])})

    apiChemicalShiftList = self._wrappedData.newShiftList(**dd)
    result = self._data2Obj.get(apiChemicalShiftList)
    if result is None:
        raise RuntimeError('Unable to generate new ChemicalShiftList item')

    return result


def _getChemicalShiftList(self: Project, name: str = None, unit: str = 'ppm', autoUpdate: bool = True,
                          isSimulated: bool = False, comment: str = None,
                          spectra=()) -> ChemicalShiftList:
    """Create new ChemicalShiftList.

    See the ChemicalShiftList class for details.

    :param name:
    :param unit:
    :param autoUpdate:
    :param isSimulated:
    :param comment:
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

    dd = {'name'   : name, 'unit': unit, 'autoUpdate': autoUpdate, 'isSimulated': isSimulated,
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
