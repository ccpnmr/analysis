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
__dateModified__ = "$dateModified: 2021-11-04 20:12:04 +0000 (Thu, November 04, 2021) $"
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
from typing import Tuple, Sequence, List, Union, Optional
from functools import partial
from collections.abc import Iterable
from ccpnmodel.ccpncore.api.ccp.nmr import Nmr
from ccpn.core._implementation.AbstractWrapperObject import AbstractWrapperObject
from ccpn.core._implementation.DataFrameABC import DataFrameABC
from ccpn.core.PeakList import PeakList
from ccpn.core.Project import Project
from ccpn.core.Spectrum import Spectrum
from ccpn.core.NmrAtom import NmrAtom
from ccpn.core.lib import Pid
from ccpn.core.lib.ContextManagers import newObject, newV3Object, renameObject, \
    undoBlockWithoutSideBar, undoStackBlocking, undoBlock
from ccpn.util.decorators import logCommand
from ccpn.util.OrderedSet import OrderedSet


CS_UNIQUEID = 'uniqueId'
CS_PID = 'pid'
CS_VALUE = 'value'
CS_VALUEERROR = 'valueError'
CS_FIGUREOFMERIT = 'figureOfMerit'
CS_NMRATOM = 'nmrAtom'
CS_CHAINCODE = 'chainCode'
CS_SEQUENCECODE = 'sequenceCode'
CS_RESIDUETYPE = 'residueType'
CS_ATOMNAME = 'atomName'
CS_SHIFTLISTPEAKS = 'shiftListPeaks'
CS_ALLPEAKS = 'allPeaks'
CS_SHIFTLISTPEAKSCOUNT = 'shiftListPeaksCount'
CS_ALLPEAKSCOUNT = 'allPeaksCount'
CS_COMMENT = 'comment'
CS_ISDELETED = 'isDeleted'
CS_OBJECT = '_object'  # this must match the object search for guiTable

CS_COLUMNS = (CS_UNIQUEID, CS_ISDELETED,
              CS_VALUE, CS_VALUEERROR, CS_FIGUREOFMERIT,
              CS_NMRATOM, CS_CHAINCODE, CS_SEQUENCECODE, CS_RESIDUETYPE, CS_ATOMNAME,
              CS_COMMENT)
CS_TABLECOLUMNS = (CS_UNIQUEID, CS_ISDELETED, CS_PID,
                   CS_VALUE, CS_VALUEERROR, CS_FIGUREOFMERIT,
                   CS_NMRATOM, CS_CHAINCODE, CS_SEQUENCECODE, CS_RESIDUETYPE, CS_ATOMNAME,
                   CS_ALLPEAKS, CS_SHIFTLISTPEAKSCOUNT, CS_ALLPEAKSCOUNT,
                   CS_COMMENT, CS_OBJECT)

# NOTE:ED - these currently match the original V3 classNames - not ChemShift
#   it is the name used in the dataframe and in project._getNextUniqueIdValue
CS_CLASSNAME = 'ChemicalShift'
CS_PLURALNAME = 'chemicalShifts'


class _ChemicalShiftListFrame(DataFrameABC):
    """
    ChemicalShiftList data - as a Pandas DataFrame.
    CCPNInternal - only for access from ChemicalShiftList
    """
    # NOT USED YET
    # Class added to wrap the model data in a core class
    # functionality can be moved from main class below to here at some point as required
    # - currently not using undo/redo ability of superclass
    pass


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

        # internal lists to hold the current chemicalShifts and deletedChemicalShift
        self._shifts = []
        self._deletedShifts = []

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

    def _recalculatePeakShifts(self, nmrResidues, shifts):
        # update the assigned nmrAtom chemical shift values - notify the nmrResidues and chemicalShifts
        for sh in shifts:
            sh._recalculateShiftValue()
        for nmr in nmrResidues:
            nmr._finaliseAction('change')
        for sh in shifts:
            sh._finaliseAction('change')

    @spectra.setter
    @logCommand(get='self', isProperty=True)
    def spectra(self, _spectra: Optional[Sequence[Union[Spectrum, str]]]):
        """Set the list of spectra attached to the chemicalShiftList
        List must be iterable and of type Spectrum or str
        :param _spectra: Iterable or None
        """
        if _spectra:
            if not isinstance(_spectra, Iterable):
                raise ValueError(f'ChemicalShiftList.spectra must be an iterable of items of type Spectrum or str')
            getByPid = self._project.getByPid
            _spectra = [getByPid(x) if isinstance(x, str) else x for x in _spectra]
            if not all(isinstance(val, Spectrum) for val in _spectra):
                raise ValueError(f'ChemicalShiftList.spectra must be an iterable of items of type Spectrum or str')
        else:
            _spectra = []

        # add a spectrum/remove a spectrum
        _createSpectra = set(_spectra) - set(self.spectra)
        _deleteSpectra = set(self.spectra) - set(_spectra)
        _createNmr = self._getNmrAtomsFromSpectra(_createSpectra)  # new nmrAtoms to add
        _deleteNmr = self._getNmrAtomsFromSpectra(_deleteSpectra)  # old nmrAtoms to update

        _thisNmr = self._getNmrAtoms()  # current nmrAtoms referenced in shiftLift

        # nmrAtoms with peakCount = 0 -> these are okay
        _oldNmrPks = set(nmr for nmr in _thisNmr if self not in [pk.spectrum.chemicalShiftList for pk in nmr.assignedPeaks])

        _newNmr = _createNmr - _oldNmrPks
        if (_newNmr & _thisNmr):
            raise RuntimeError(f'ChemicalShiftList.spectra: nmrAtoms already in list')
        _nmrs = _deleteNmr | _oldNmrPks
        nmrResidues = set(nmr.nmrResidue for nmr in _nmrs)
        shifts = set(cs for nmrAt in _nmrs for cs in nmrAt.chemicalShifts if cs and not cs.isDeleted)

        with undoBlock():
            with undoStackBlocking() as addUndoItem:
                addUndoItem(undo=partial(self._recalculatePeakShifts, nmrResidues, shifts))

            self._wrappedData.experiments = set(x._wrappedData.experiment for x in _spectra)

            for nmrAtom in _newNmr:
                self.newChemicalShift(nmrAtom=nmrAtom)

            self._recalculatePeakShifts(nmrResidues, shifts)
            with undoStackBlocking() as addUndoItem:
                addUndoItem(redo=partial(self._recalculatePeakShifts, nmrResidues, shifts))

    def _getNmrAtomsFromSpectra(self, spectra):
        """Get the list of nmrAtoms in the supplied spectra
        """
        _newNmr = set(nmrAtom
                      for spec in spectra
                      for pList in spec.peakLists if not pList.isSimulated
                      for pk in pList.peaks
                      for aNmrAtoms in pk.assignedNmrAtoms
                      for nmrAtom in aNmrAtoms
                      ) - {None}
        return _newNmr

    def _getNmrAtoms(self):
        """Get the list of nmrAtoms
        """
        try:
            _data = self._wrappedData.data
            _oldNmrAtoms = _data[_data[CS_ISDELETED] == False][CS_NMRATOM]
            _oldNmr = set(self.project.getByPid(nmr) for nmr in _oldNmrAtoms) - {None}  # remove any Nones
        except:
            # dataframe may not have been created yet
            _oldNmr = set()
        return _oldNmr

    def _OldChemicalShifts(self):
        """STUB: hot-fixed later
        """
        return ()

    @property
    def chemicalShifts(self):
        """Return the shifts belonging to ChemicalShiftList
        """
        return self._shifts

    def getChemicalShift(self, nmrAtom: Union[NmrAtom, str, None] = None, uniqueId: Union[int, None] = None,
                         _includeDeleted: bool = False):
        """Return a chemicalShift by nmrAtom or uniqueId
        Shift is returned as a namedTuple
        """
        if nmrAtom and uniqueId:
            raise ValueError('ChemicalShiftList.getChemicalShift: use either nmrAtom or uniqueId')

        _data = self._wrappedData.data
        if _data is None:
            return

        rows = None
        if nmrAtom:
            # get shift by nmrAtom
            nmrAtom = self.project.getByPid(nmrAtom) if isinstance(nmrAtom, str) else nmrAtom
            if not isinstance(nmrAtom, (NmrAtom, type(None))):
                raise ValueError('ChemicalShiftList.getChemicalShift: nmrAtom must be of type NmrAtom or str')
            if nmrAtom:
                # search dataframe
                rows = _data[_data[CS_NMRATOM] == nmrAtom.pid]

        elif uniqueId is not None:
            # get shift by uniqueId
            if not isinstance(uniqueId, int):
                raise ValueError('ChemicalShiftList.getChemicalShift: uniqueId must be an int')

            # search dataframe
            rows = _data[_data[CS_UNIQUEID] == uniqueId]

        if rows is not None:
            if len(rows) > 1:
                raise RuntimeError('ChemicalShiftList.getChemicalShift: bad number of shifts in list')
            if len(rows) == 1:
                uniqueId = rows.iloc[0].uniqueId
                _shs = [sh for sh in self._shifts if sh._uniqueId == uniqueId]
                if _shs and len(_shs) == 1:
                    return _shs[0]
                else:
                    if _includeDeleted:
                        _shs = [sh for sh in self._deletedShifts if sh._uniqueId == uniqueId]
                        if _shs and len(_shs) == 1:
                            return _shs[0]

                    raise ValueError('ChemicalShiftList.getChemicalShift: shift not found')

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
        from ccpn.core.ChemicalShift import _newChemicalShift as _newShift

        # name = _incrementObjectName(self.project, self._pluralLinkName, self.name)
        ncsl = self.project.newChemicalShiftList()

        # duplicate the chemicalShiftList dataframe - remove the deleted shifts (not required)
        # will copy the correct type if changed to _ChemicalShiftListFrame
        df = self._wrappedData.data.copy()
        df = df[df[CS_ISDELETED] == False]
        df.set_index(df[CS_UNIQUEID], inplace=True, )
        ncsl._wrappedData.data = df

        # make a new list of uniqueIds
        _newIds = [self.project._getNextUniqueIdValue(CS_CLASSNAME) for _ in range(len(df))]
        df[CS_UNIQUEID] = _newIds

        # create the new shift objects
        for ii in range(len(df)):
            _row = df.iloc[ii]

            # create a new shift with the uniqueId from the dataframe
            shift = _newShift(ncsl, _ignoreUniqueId=True)
            _uniqueId = int(_row[CS_UNIQUEID])
            shift._resetUniqueId(_uniqueId)
            ncsl._shifts.append(shift)

            # add the new object to the _pid2Obj dict
            self.project._finalisePid2Obj(shift, 'create')

            # add the shift to the nmrAtom
            shift._restoreObject()

        ncsl.autoUpdate = autoUpdate
        for att in ['unit', 'isSimulated', 'comment']:
            setattr(ncsl, att, getattr(self, att, None))

        # setting the spectra will autoUpdate as required
        ncsl.spectra = self.spectra if includeSpectra else ()
        # # old chemicalShifts
        # list(map(lambda cs: cs.copyTo(ncsl), self.chemicalShifts))

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

    def _getShiftByUniqueId(self, uniqueId):
        """Get the shift data from the dataFrame by the uniqueId
        """
        try:
            return self._wrappedData.data.loc[uniqueId]
        except Exception as es:
            raise ValueError(f'ChemicalShiftList._getShiftByUniqueId: uniqueId {uniqueId} not found')

    def _getShiftAttribute(self, uniqueId, name, attribType):
        """Get the named attribute from the chemicalShift with supplied uniqueId

        Check the attribute for None, nan, inf, etc., and cast to attribType
        CCPN Internal - Pandas dataframe changes values after saving through api
        """
        row = self._getShiftByUniqueId(uniqueId)
        if name in row:
            # get the value and cast to the correct type
            _val = row[name]
            return None if (_val is None or (_val != _val)) else attribType(_val)
        else:
            raise ValueError(f'ChemicalShiftList._getShiftAttribute: attribute {name} not found in chemicalShift')

    def _setShiftAttribute(self, uniqueId, name, value):
        """Set the attribute of the chemicalShift with the supplied uniqueId
        """
        row = self._getShiftByUniqueId(uniqueId)
        if name in row:
            try:
                self._wrappedData.data.loc[uniqueId, name] = value
            except Exception as es:
                raise ValueError(f'ChemicalShiftList._setShiftAttribute: error setting attribute {name} in chemicalShift {self}')

        else:
            raise ValueError(f'ChemicalShiftList._setShiftAttribute: attribute {name} not found in chemicalShift {self}')

    def _getShiftAttributes(self, uniqueId, startName, endName, attribTypes):
        """Get the named attributes from the chemicalShift with supplied uniqueId
        """
        row = self._getShiftByUniqueId(uniqueId)
        if startName in row and endName in row:
            _val = row[startName:endName]
            _val = tuple(None if (val is None or (val != val)) else attribType(val) for val, attribType in zip(_val, attribTypes))
            return _val
        else:
            raise ValueError(f'ChemicalShiftList._getShiftAttributes: attribute {startName}|{endName} not found in chemicalShift')

    def _setShiftAttributes(self, uniqueId, startName, endName, value):
        """Set the attributes of the chemicalShift with the supplied uniqueId
        """
        row = self._getShiftByUniqueId(uniqueId)
        if startName in row and endName in row:
            try:
                self._wrappedData.data.loc[uniqueId, startName:endName] = value
            except Exception as es:
                raise ValueError(f'ChemicalShiftList._setShiftAttributes: error setting attribute {startName}|{endName} in chemicalShift {self}')

        else:
            raise ValueError(f'ChemicalShiftList._setShiftAttributes: attribute {startName}|{endName} not found in chemicalShift {self}')

    def _undoRedoShifts(self, shifts):
        """update to shifts after undo/redo
        shifts should be a simple, non-nested dict of int:<shift> pairs
        """
        # keep the same shift list
        self._shifts[:] = shifts

    def _undoRedoDeletedShifts(self, deletedShifts):
        """update to deleted shifts after undo/redo
        deletedShifts should be a simple, non-nested dict of int:<deletedShift> pairs
        """
        # keep the same deleted shift list
        self._deletedShifts[:] = deletedShifts

    def _setDeleted(self, shift, state):
        """Set the deleted state of the shift
        """
        shift._deleted = state

    @property
    def _data(self):
        """Helper method to get the stored dataframe
        CCPN Internal
        """
        return self._wrappedData.data

    def _searchChemicalShifts(self, nmrAtom=None, uniqueId=None):
        """Return True if the nmrAtom/uniqueId already exists in the chemicalShifts dataframe
        """
        if nmrAtom and uniqueId:
            raise ValueError('ChemicalShiftList._searchChemicalShifts: use either nmrAtom or uniqueId')

        if self._wrappedData.data is None:
            return

        if nmrAtom:
            # get shift by nmrAtom
            nmrAtom = self.project.getByPid(nmrAtom) if isinstance(nmrAtom, str) else nmrAtom
            if not isinstance(nmrAtom, NmrAtom):
                raise ValueError('ChemicalShiftList._searchChemicalShifts: nmrAtom must be of type NmrAtom, str')

            # search dataframe for single element
            _data = self._wrappedData.data
            rows = _data[_data[CS_NMRATOM] == nmrAtom.pid]
            return len(rows) > 0

        elif uniqueId is not None:
            # get shift by uniqueId
            if not isinstance(uniqueId, int):
                raise ValueError(f'ChemicalShiftList._searchChemicalShifts: uniqueId must be an int - {uniqueId}')

            # search dataframe for single element
            _data = self._wrappedData.data
            rows = _data[_data[CS_UNIQUEID] == uniqueId]
            return len(rows) > 0

    def delete(self):
        """Delete the chemicalShiftList and associated chemicalShifts
        """
        shifts = list(self._shifts)

        with undoBlock():
            for sh in shifts:
                _oldShifts = self._shifts[:]
                _oldDeletedShifts = self._deletedShifts[:]

                self._shifts.remove(sh)
                self._deletedShifts.append(sh)  # not sorted - sort?

                _newShifts = self._shifts[:]
                _newDeletedShifts = self._deletedShifts[:]

                sh._deleteWrapper(self, _newDeletedShifts, _newShifts, _oldDeletedShifts, _oldShifts)

            self._delete()

    #=========================================================================================
    # CCPN functions
    #=========================================================================================

    def _updateEdgeToAlpha1(self):
        """Move chemicalShifts from model shifts to pandas dataFrame

        version 3.0.4 -> 3.1.0.alpha update
        dataframe now stored in _wrappedData.data
        CCPN Internal
        """
        # skip for no shifts
        if not self._oldChemicalShifts:
            return

        with undoBlockWithoutSideBar():
            # create a new dataframe
            shifts = []
            for row, oldShift in enumerate(self._oldChemicalShifts):
                newRow = oldShift._getShiftAsTuple()
                if not newRow.isDeleted:
                    # ignore deleted as not needed - this SHOULDN'T happen here, but just to be safe
                    shifts.append(newRow)

                # delete the old shift
                oldShift.delete()

            # instantiate the dataframe
            df = pd.DataFrame(shifts, columns=CS_COLUMNS)
            df.set_index(df[CS_UNIQUEID], inplace=True, )  # drop=False)

            # set as the new subclassed DataFrameABC - not using yet, may have undo/redo issues
            self._wrappedData.data = df  #_ChemicalShiftListFrame(df)

    @classmethod
    def _restoreObject(cls, project, apiObj):
        """Subclassed to allow for initialisations on restore, not on creation via newChemicalShiftList
        """
        from ccpn.util.Logging import getLogger
        from ccpn.core.ChemicalShift import _newChemicalShift as _newShift

        chemicalShiftList = super()._restoreObject(project, apiObj)

        # keep a list of the update methods
        # this needs to be traversed on order from the latest version that the project has been saved under
        versionUpdates = (('3.0.4', cls._updateEdgeToAlpha1),
                          ('3.1.0', None),  # current version - just used for debug logging
                          )

        # check version history (defaults to 3.0.4)
        history = project.versionHistory[-1]

        try:
            # get the index of the saved version, this SHOULD always work
            startIndex = [_ver for _ver, _ in versionUpdates].index(history)
        except:
            raise RuntimeError(f'ChemicalShiftList._restoreObject: current version is not defined {history}')

        lastIndex = len(versionUpdates)

        # iterate through the updates
        for (ver, func), (nextVer, _) in zip(versionUpdates[startIndex:lastIndex - 1], versionUpdates[startIndex + 1:lastIndex]):
            getLogger().debug(f'updating version {ver} -> {nextVer}')
            func(chemicalShiftList)

        # create a set of new shift objects linked to the pandas rows - discard deleted
        _data = chemicalShiftList._wrappedData.data

        if _data is not None:
            # check that is the new DataFrameABC class, update as required - for later use
            # if not isinstance(_data, DataFrameABC):
            #     getLogger().debug(f'updating classType {chemicalShiftList} -> _ChemicalShiftListFrame')
            #     _data = _ChemicalShiftListFrame(_data)

            _data = _data[_data[CS_ISDELETED] == False]
            _data.set_index(_data[CS_UNIQUEID], inplace=True, )  # drop=False)

            chemicalShiftList._wrappedData.data = _data

            maxUniqueId = project._queryNextUniqueIdValue(CS_CLASSNAME)
            for ii in range(len(_data)):
                _row = _data.iloc[ii]

                # create a new shift with the uniqueId from the old shift
                shift = _newShift(chemicalShiftList, _ignoreUniqueId=True)
                _uniqueId = int(_row[CS_UNIQUEID])
                shift._resetUniqueId(_uniqueId)

                # set the new _nextUniqueId for the chemicalsShifts
                maxUniqueId = max(maxUniqueId, _uniqueId)
                project._setNextUniqueIdValue(CS_CLASSNAME, maxUniqueId + 1)

                chemicalShiftList._shifts.append(shift)

                # add the new object to the _pid2Obj dict
                project._finalisePid2Obj(shift, 'create')

                # restore the nmrAtom, etc., for the new shift
                shift._restoreObject()

        return chemicalShiftList

    #===========================================================================================
    # new'Object' and other methods
    # Call appropriate routines in their respective locations
    #===========================================================================================

    @logCommand(get='self')
    def newChemicalShift(self, value: float = None, valueError: float = None, figureOfMerit: float = 1.0,
                         nmrAtom: Union[NmrAtom, str, None] = None,
                         chainCode: str = None, sequenceCode: str = None, residueType: str = None, atomName: str = None,
                         comment: str = None
                         ):
        """Create new ChemicalShift within ChemicalShiftList.

        See the ChemicalShift class for details.

        :param value: float shift value
        :param valueError: float
        :param figureOfMerit: float, default = 1.0
        :param nmrAtom: nmrAtom as object or pid, or None if not required
        :param comment: optional comment string
        :return: a new ChemicalShift tuple.
        """

        data = self._wrappedData.data
        if nmrAtom:
            _nmrAtom = self.project.getByPid(nmrAtom) if isinstance(nmrAtom, str) else nmrAtom
            if not _nmrAtom:
                raise ValueError(f'ChemicalShiftList.newChemicalShift: nmrAtom {_nmrAtom} not found')
        if data is not None and nmrAtom and nmrAtom.pid in list(data[CS_NMRATOM]):
            raise ValueError(f'ChemicalShiftList.newChemicalShift: nmrAtom {nmrAtom} already exists')

        shift = self._newChemicalShiftObject(atomName, chainCode, comment, data, figureOfMerit, nmrAtom, residueType, sequenceCode, value, valueError)

        return shift

    @newV3Object()
    def _newChemicalShiftObject(self, atomName, chainCode, comment, data, figureOfMerit, nmrAtom, residueType, sequenceCode, value, valueError):
        """Create a new pure V3 ChemicalShift object
        Method is wrapped with create/delete notifier
        """
        from ccpn.core.ChemicalShift import _getByTuple, _newChemicalShift as _newShift

        # make new tuple - verifies contents
        _row = _getByTuple(self, value, valueError, figureOfMerit,
                           nmrAtom, chainCode, sequenceCode, residueType, atomName,
                           comment)
        _nextUniqueId = self.project._getNextUniqueIdValue(CS_CLASSNAME)
        # add to dataframe - this is in undo stack and marked as modified
        _dfRow = pd.DataFrame(((_nextUniqueId, False, value, valueError, figureOfMerit, None) + _row[6:],), columns=CS_COLUMNS)

        if data is None:
            # set as the new subclassed DataFrameABC
            self._wrappedData.data = _dfRow  # _ChemicalShiftListFrame(_dfRow)
        else:
            self._wrappedData.data = self._wrappedData.data.append(_dfRow)

        _data = self._wrappedData.data
        _data.set_index(_data[CS_UNIQUEID], inplace=True, )  # drop=False)

        # create new shift object
        # new Shift only needs chemicalShiftList and uniqueId - properties are linked to dataframe
        shift = _newShift(self, _ignoreUniqueId=True)
        shift._resetUniqueId(int(_nextUniqueId))
        if nmrAtom:
            shift.nmrAtom = nmrAtom

        _oldShifts = self._shifts[:]
        self._shifts.append(shift)
        _newShifts = self._shifts[:]

        with undoBlockWithoutSideBar():
            # add an undo/redo item to recover shifts
            with undoStackBlocking() as addUndoItem:
                addUndoItem(undo=partial(self._undoRedoShifts, _oldShifts),
                            redo=partial(self._undoRedoShifts, _newShifts))

        return shift

    @logCommand(get='self')
    def deleteChemicalShift(self, nmrAtom: Union[None, NmrAtom, str] = None, uniqueId: int = None):
        """Delete a chemicalShift by nmrAtom or uniqueId
        """
        if nmrAtom and uniqueId:
            raise ValueError('ChemicalShiftList.deleteChemicalShift: use either nmrAtom or uniqueId')

        if self._wrappedData.data is None:
            return

        if nmrAtom:
            # get shift by nmrAtom
            nmrAtom = self.project.getByPid(nmrAtom) if isinstance(nmrAtom, str) else nmrAtom
            if not isinstance(nmrAtom, NmrAtom):
                raise ValueError('ChemicalShiftList.deleteChemicalShift: nmrAtom must be of type NmrAtom, str')

            # search dataframe for single element
            _data = self._wrappedData.data
            rows = _data[_data[CS_NMRATOM] == nmrAtom.pid]
            if len(rows) > 1:
                raise RuntimeError('ChemicalShiftList.deleteChemicalShift: bad number of shifts in list')
            elif len(rows) == 0:
                raise ValueError(f'ChemicalShiftList.deleteChemicalShift: nmrAtom {nmrAtom.pid} not found')

            self._deleteChemicalShiftObject(rows)

        elif uniqueId is not None:
            # get shift by uniqueId
            if not isinstance(uniqueId, int):
                raise ValueError('ChemicalShiftList.deleteChemicalShift: uniqueId must be an int')

            # search dataframe for single element
            _data = self._wrappedData.data
            rows = _data[_data[CS_UNIQUEID] == uniqueId]
            if len(rows) > 1:
                raise RuntimeError('ChemicalShiftList.deleteChemicalShift: bad number of shifts in list')
            elif len(rows) == 0:
                raise ValueError(f'ChemicalShiftList.deleteChemicalShift: uniqueId {uniqueId} not found')

            self._deleteChemicalShiftObject(rows)

    def _deleteChemicalShiftObject(self, rows):
        """Update the dataframe and handle notifiers
        """
        _oldShifts = self._shifts[:]
        _oldDeletedShifts = self._deletedShifts[:]

        uniqueId = rows.iloc[0].uniqueId
        _shs = [sh for sh in self._shifts if sh._uniqueId == uniqueId]
        _val = _shs[0]

        self._shifts.remove(_val)
        self._deletedShifts.append(_val)  # not sorted - sort?

        _newShifts = self._shifts[:]
        _newDeletedShifts = self._deletedShifts[:]

        _val._deleteWrapper(self, _newDeletedShifts, _newShifts, _oldDeletedShifts, _oldShifts)


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

    :param name: name for the new chemicalShiftList
    :param unit: unit type as str, e.g. 'ppm'
    :param autoUpdate: True/False - automatically update chemicalShifts when assignments change
    :param isSimulated: True/False
    :param comment: optional user comment
    :return: a new ChemicalShiftList instance.
    """

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

    # instantiate a new empty dataframe
    df = pd.DataFrame(columns=CS_COLUMNS)
    df.set_index(df[CS_UNIQUEID], inplace=True, )

    # set as the new subclassed DataFrameABC
    apiChemicalShiftList.data = df  # _ChemicalShiftListFrame(df)

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

    if spectra:
        getByPid = self._project.getByPid
        spectra = [getByPid(x) if isinstance(x, str) else x for x in spectra]

    dd = {'name'   : name, 'unit': unit, 'autoUpdate': autoUpdate, 'isSimulated': isSimulated,
          'details': comment}
    if spectra:
        dd.update({'experiments': OrderedSet([spec._wrappedData.experiment for spec in spectra])})

    apiChemicalShiftList = self._wrappedData.getShiftList(**dd)
    result = self._data2Obj.get(apiChemicalShiftList)
    return result


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
