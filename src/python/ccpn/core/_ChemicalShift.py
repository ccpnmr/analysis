"""
Module Documentation here
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
__dateModified__ = "$dateModified: 2021-08-17 02:16:06 +0100 (Tue, August 17, 2021) $"
__version__ = "$Revision: 3.0.4 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Ed Brooksbank $"
__date__ = "$Date: 2021-08-02 10:55:54 +0100 (Mon, August 02, 2021) $"
#=========================================================================================
# Start of code
#=========================================================================================

import pandas as pd
from collections import OrderedDict
from functools import partial
from typing import Optional, Union
from collections import namedtuple
from ccpn.core.Project import Project
from ccpn.core.NmrAtom import NmrAtom
from ccpn.core.ChemicalShiftList import ChemicalShiftList
from ccpn.core.lib.ContextManagers import ccpNmrV3CoreSetter, checkDeleted, \
    undoBlockWithoutSideBar, undoStackBlocking, deleteV3Object
from ccpn.core.lib import Pid
from ccpn.core.lib.Notifiers import NotifierBase
from ccpn.core.ChemicalShiftList import CS_UNIQUEID, CS_ISDELETED, CS_VALUE, CS_VALUEERROR, CS_FIGUREOFMERIT, \
    CS_NMRATOM, CS_CHAINCODE, CS_SEQUENCECODE, CS_RESIDUETYPE, CS_ATOMNAME, \
    CS_SHIFTLISTPEAKS, CS_ALLPEAKS, CS_SHIFTLISTPEAKSCOUNT, CS_ALLPEAKSCOUNT, \
    CS_COMMENT, CS_OBJECT, \
    CS_COLUMNS, CS_TABLECOLUMNS, CS_CLASSNAME, CS_PLURALNAME
from ccpn.util.Common import makeIterableList


MINFOM = 0.0
MAXFOM = 1.0

ShiftParameters = namedtuple('ShiftParameters', f'{CS_UNIQUEID} {CS_ISDELETED} {CS_VALUE} {CS_VALUEERROR} {CS_FIGUREOFMERIT} '
                                                f'{CS_NMRATOM} {CS_CHAINCODE} {CS_SEQUENCECODE} {CS_RESIDUETYPE} {CS_ATOMNAME} '
                                                f'{CS_COMMENT} ')


class _ChemicalShift(NotifierBase):
    """Chemical Shift, containing a ChemicalShift value for the NmrAtom they belong to.

    Chemical shift values are continuously averaged over peaks assigned to the NmrAtom,
    (unless this behaviour is turned off)

    ChemicalShift objects are sorted by uniqueId.
    """

    #: Short class name, for PID.
    shortClassName = 'SH'
    # Attribute it necessary as subclasses must use superclass className
    className = '_ChemicalShift'

    _parentClass = ChemicalShiftList

    #: Name of plural link to instances of class
    _pluralLinkName = '_chemicalShifts'

    _childClasses = []
    _isGuiClass = False

    # the attribute name used by current - not done yet
    _currentAttributeName = '_chemicalShifts'

    def __init__(self, chemicalShiftList, _ignoreUniqueId=False):
        """Create a new instance of v3 Shift
        """
        self._chemicalShiftList = chemicalShiftList
        self._project = chemicalShiftList.project
        self._uniqueId = None if _ignoreUniqueId else self.project._getNextUniqueIdValue(CS_CLASSNAME)
        self._deletedId = None
        self._isDeleted = False
        # All properties are derived from the chemicalShiftList pandas dataframe

    def __str__(self):
        """Readable string representation; potentially subclassed
        """
        return ("<%s-Deleted>" % self.pid) if self._isDeleted else ("<%s>" % self.pid)

    def __repr__(self):
        """Object string representation; compatible with application.get()
        """
        return f"'{self.__str__()}'"

    #=========================================================================================
    # CCPN Properties
    #=========================================================================================

    @property
    def project(self) -> 'Project':
        """The Project (root)containing the object.
        """
        return self._project

    @property
    def id(self) -> str:
        """Identifier for the object, used to generate the pid and longPid.
        Generated by combining the id of the containing object, i.e. the checmialShift instance,
        with the value of one or more key attributes that uniquely identify the object in context
        E.g. 'default.1'
        """
        return self._deletedId if self._isDeleted else Pid.IDSEP.join((self._chemicalShiftList.name, str(self._uniqueId)))

    @property
    def pid(self) -> Pid.Pid:
        """Identifier for the object, unique within the project.
        Set automatically from the short class name, the parent chemicalShiftList and object.uniqueId
        E.g. 'SH:default.1'
        """
        return Pid.Pid(Pid.PREFIXSEP.join((self.shortClassName, self.id)))

    @property
    def longPid(self) -> Pid.Pid:
        """Identifier for the object, unique within the project.
        Set automatically from the full class name, the parent chemicalShiftList and object.uniqueId
        E.g. '_ChemicalShift:default.1'
        """
        return Pid.Pid(Pid.PREFIXSEP.join((self.className, self.id)))

    @property
    def _parent(self):
        """ChemicalShiftList containing ChemicalShift.
        """
        return self._chemicalShiftList

    chemicalShiftList = _parent

    #=========================================================================================
    # Class Properties and methods
    #=========================================================================================

    @property
    def uniqueId(self) -> int:
        """unique identifier of ChemicalShift.
        """
        return self._uniqueId

    @property
    def isDeleted(self) -> bool:
        """True if this object is deleted.
        """
        return self._isDeleted

    @property
    def _deleted(self) -> bool:
        """True if this object is deleted.
        CCPN Internal - allows internal deletion of the ChemicalShift
        sets/clears the value in the chemicalShiftLists dataframe
        """
        return self._chemicalShiftList._getShiftAttribute(self._uniqueId, CS_ISDELETED, bool)

    @_deleted.setter
    def _deleted(self, value: bool):
        if not isinstance(value, bool):
            raise ValueError(f'{self.className}.isDeleted must be True/False')
        self._chemicalShiftList._setShiftAttribute(self._uniqueId, CS_ISDELETED, value)

    #~~~~~~~~~~~~~~~~

    @property
    # @checkDeleted()
    def value(self) -> Optional[float]:
        """shift value of ChemicalShift, in unit as defined in the ChemicalShiftList.
        """
        return self._chemicalShiftList._getShiftAttribute(self._uniqueId, CS_VALUE, float)

    @value.setter
    # @checkDeleted()
    @ccpNmrV3CoreSetter()
    def value(self, val: Optional[float]):
        if not isinstance(val, (float, type(None))):
            raise ValueError(f'{self.className}.value must be of type float or None')
        _nmrAtomPid = self._chemicalShiftList._getShiftAttribute(self._uniqueId, CS_NMRATOM, str)
        if _nmrAtomPid:
            raise ValueError(f'{self.className}.value cannot be changed with attached nmrAtom')
        self._chemicalShiftList._setShiftAttribute(self._uniqueId, CS_VALUE, val)

    #~~~~~~~~~~~~~~~~

    @property
    # @checkDeleted()
    def valueError(self) -> Optional[float]:
        """shift valueError of ChemicalShift, in unit as defined in the ChemicalShiftList.
        """
        return self._chemicalShiftList._getShiftAttribute(self._uniqueId, CS_VALUEERROR, float)

    @valueError.setter
    # @checkDeleted()
    @ccpNmrV3CoreSetter()
    def valueError(self, value: Optional[float]):
        if not isinstance(value, (float, type(None))):
            raise ValueError(f'{self.className}.valueError must be of type float or None')
        _nmrAtomPid = self._chemicalShiftList._getShiftAttribute(self._uniqueId, CS_NMRATOM, str)
        if _nmrAtomPid:
            raise ValueError(f'{self.className}.value cannot be changed with attached nmrAtom')
        self._chemicalShiftList._setShiftAttribute(self._uniqueId, CS_VALUEERROR, value)

    #~~~~~~~~~~~~~~~~

    @property
    # @checkDeleted()
    def figureOfMerit(self) -> Optional[float]:
        """Figure of Merit for ChemicalShift, between 0.0 and 1.0 inclusive.
        """
        return self._chemicalShiftList._getShiftAttribute(self._uniqueId, CS_FIGUREOFMERIT, float)

    @figureOfMerit.setter
    # @checkDeleted()
    @ccpNmrV3CoreSetter()
    def figureOfMerit(self, value: Optional[float]):
        if not isinstance(value, (float, type(None))):
            raise ValueError(f'{self.className}.figureOfMerit must be of type float or None')
        if value is not None and not (MINFOM <= value <= MAXFOM):
            raise ValueError(f'{self.className}.figureOfMerit must be in range [{MINFOM} - {MAXFOM}]')
        self._chemicalShiftList._setShiftAttribute(self._uniqueId, CS_FIGUREOFMERIT, value)

    #~~~~~~~~~~~~~~~~

    @property
    # @checkDeleted()
    def nmrAtom(self) -> Optional[NmrAtom]:
        """Attached NmrAtom.
        """
        _nmrAtomPid = self._chemicalShiftList._getShiftAttribute(self._uniqueId, CS_NMRATOM, str)
        return self.project.getByPid(_nmrAtomPid)

    @nmrAtom.setter
    # @checkDeleted()
    @ccpNmrV3CoreSetter()
    def nmrAtom(self, value: Union[NmrAtom, str, None]):
        nat = self.nmrAtom
        print(f'     change nmrAtom   {self} {value}')
        if value is None:
            if nat is None:
                return

            # clear the nmrAtom and derived values
            self._chemicalShiftList._setShiftAttributes(self._uniqueId, CS_NMRATOM, CS_ATOMNAME, (None, None, None, None, None))
            nat._chemicalShifts.remove(self)

        else:
            _nmrAtom = self._project.getByPid(value) if isinstance(value, str) else value
            if not _nmrAtom:
                raise ValueError(f'{self.className}.nmrAtom: {value} not found')
            if _nmrAtom == nat:
                return

            if not isinstance(_nmrAtom, NmrAtom):
                raise ValueError(f'{self.className}.nmrAtom: {value} must be of type NmrAtom')

            if self._chemicalShiftList._searchChemicalShifts(nmrAtom=_nmrAtom):
                raise ValueError(f'{self.className}.nmrAtom: {_nmrAtom.pid} already exists')

            # nmrAtom and derived properties
            self._chemicalShiftList._setShiftAttributes(self._uniqueId, CS_NMRATOM, CS_ATOMNAME,
                                                        (str(_nmrAtom.pid),) + tuple(val or None for val in _nmrAtom.pid.fields))

            if nat:
                nat._chemicalShifts.remove(self)
            _nmrAtom._chemicalShifts.append(self)

            if self._chemicalShiftList.autoUpdate:
                value, valueError = _nmrAtom._recalculateShiftValue(self._chemicalShiftList.spectra)

                self._chemicalShiftList._setShiftAttribute(self._uniqueId, CS_VALUE, value)
                self._chemicalShiftList._setShiftAttribute(self._uniqueId, CS_VALUEERROR, valueError)

    #~~~~~~~~~~~~~~~~

    @property
    # @checkDeleted()
    def chainCode(self) -> Optional[str]:
        """chainCode for attached nmrAtom.
        """
        return self._chemicalShiftList._getShiftAttribute(self._uniqueId, CS_CHAINCODE, str)

    @chainCode.setter
    # @checkDeleted()
    @ccpNmrV3CoreSetter()
    def chainCode(self, value: Optional[str]):
        if not isinstance(value, (str, type(None))):
            raise ValueError(f'{self.className}.chainCode must be of type str or None')
        _nmrAtomPid = self._chemicalShiftList._getShiftAttribute(self._uniqueId, CS_NMRATOM, str)
        if _nmrAtomPid:
            raise RuntimeError(f'{self.className}.chainCode: derived value, cannot modify when nmrAtom is set')
        # only set if the nmrAtom has not been set
        self._chemicalShiftList._setShiftAttribute(self._uniqueId, CS_CHAINCODE, value)

    #~~~~~~~~~~~~~~~~

    @property
    # @checkDeleted()
    def sequenceCode(self) -> Optional[str]:
        """sequenceCode for attached nmrAtom.
        """
        return self._chemicalShiftList._getShiftAttribute(self._uniqueId, CS_SEQUENCECODE, str)

    @sequenceCode.setter
    # @checkDeleted()
    @ccpNmrV3CoreSetter()
    def sequenceCode(self, value: Optional[str]):
        if not isinstance(value, (str, type(None))):
            raise ValueError(f'{self.className}.sequenceCode must be of type str or None')
        _nmrAtomPid = self._chemicalShiftList._getShiftAttribute(self._uniqueId, CS_NMRATOM, str)
        if _nmrAtomPid:
            raise RuntimeError(f'{self.className}.sequenceCode: derived value, cannot modify when nmrAtom is set')
        # only set if the nmrAtom has not been set
        self._chemicalShiftList._setShiftAttribute(self._uniqueId, CS_SEQUENCECODE, value)

    #~~~~~~~~~~~~~~~~

    @property
    # @checkDeleted()
    def residueType(self) -> Optional[str]:
        """residueType for attached nmrAtom.
        """
        return self._chemicalShiftList._getShiftAttribute(self._uniqueId, CS_RESIDUETYPE, str)

    @residueType.setter
    # @checkDeleted()
    @ccpNmrV3CoreSetter()
    def residueType(self, value: Optional[str]):
        if not isinstance(value, (str, type(None))):
            raise ValueError(f'{self.className}.residueType must be of type str or None')
        _nmrAtomPid = self._chemicalShiftList._getShiftAttribute(self._uniqueId, CS_NMRATOM, str)
        if _nmrAtomPid:
            raise RuntimeError(f'{self.className}.residueType: derived value, cannot modify when nmrAtom is set')
        # only set if the nmrAtom has not been set
        self._chemicalShiftList._setShiftAttribute(self._uniqueId, CS_RESIDUETYPE, value)

    #~~~~~~~~~~~~~~~~

    @property
    # @checkDeleted()
    def atomName(self) -> Optional[str]:
        """atomName for attached nmrAtom.
        """
        return self._chemicalShiftList._getShiftAttribute(self._uniqueId, CS_ATOMNAME, str)

    @atomName.setter
    # @checkDeleted()
    @ccpNmrV3CoreSetter()
    def atomName(self, value: Optional[str]):
        if not isinstance(value, (str, type(None))):
            raise ValueError(f'{self.className}.atomName must be of type str or None')
        _nmrAtomPid = self._chemicalShiftList._getShiftAttribute(self._uniqueId, CS_NMRATOM, str)
        if _nmrAtomPid:
            raise RuntimeError(f'{self.className}.atomName: derived value, cannot modify when nmrAtom is set')
        # only set if the nmrAtom has not been set
        self._chemicalShiftList._setShiftAttribute(self._uniqueId, CS_ATOMNAME, value)

    #~~~~~~~~~~~~~~~~

    @property
    # @checkDeleted()
    def comment(self) -> Optional[str]:
        """comment for attached nmrAtom.
        """
        return self._chemicalShiftList._getShiftAttribute(self._uniqueId, CS_COMMENT, str)

    @comment.setter
    # @checkDeleted()
    @ccpNmrV3CoreSetter()
    def comment(self, value: Optional[str]):
        if not isinstance(value, (str, type(None))):
            raise ValueError(f'{self.className}.comment must be of type str or None')
        self._chemicalShiftList._setShiftAttribute(self._uniqueId, CS_COMMENT, value)

    #~~~~~~~~~~~~~~~~

    @property
    # @checkDeleted()
    def assignedPeaks(self) -> Optional[tuple]:
        """Assigned peaks for attached nmrAtom belonging to this chemicalShiftList.
        """
        assigned = self.allAssignedPeaks
        if assigned is not None:
            return tuple(pp for pp in assigned if pp.spectrum.chemicalShiftList == self)

    @property
    # @checkDeleted()
    def allAssignedPeaks(self) -> Optional[tuple]:
        """All assigned peaks for attached nmrAtom.
        """
        _nmrAtomPid = self._chemicalShiftList._getShiftAttribute(self._uniqueId, CS_NMRATOM, str)
        _nmrAtom = self.project.getByPid(_nmrAtomPid)
        if _nmrAtom:
            return tuple(set(makeIterableList(_nmrAtom.assignedPeaks)))

    #=========================================================================================
    # Implementation functions
    #=========================================================================================

    def _resetUniqueId(self, value):
        """Reset the uniqueId
        CCPN Internal - although not sure whether actually required here
        """
        if self._chemicalShiftList._searchChemicalShifts(uniqueId=value):
            raise ValueError(f'{self.className}._resetUniqueId: uniqueId {value} already exists')
        self._uniqueId = int(value)

    def _finaliseAction(self, action: str):
        """Do wrapper level finalisation, and execute all notifiers
        action is one of: 'create', 'delete', 'change', 'rename'
        """
        project = self.project
        if action == 'delete':
            # housekeeping -
            #   handle the modifying of __str__/__repr__ here so that it does not require
            #   extra calls to _isDeleted which may crash on loose objects in the undo deque (or elsewhere)
            #   update the pid2Obj list
            self._flaggedForDelete = True
            self._deletedId = str(self.id)
            self._deleted = True
            self._isDeleted = True
            project._finalisePid2Obj(self, 'delete')
        else:
            self._flaggedForDelete = False
            self._deleted = False
            self._isDeleted = False
            project._finalisePid2Obj(self, 'create')

        if project._notificationBlanking:
            # do not call external notifiers
            # structures should be in a valid state at this point
            return

        # notify any external objects - these should NOT modify any objects/structures
        className = self.className
        # NB 'AbstractWrapperObject' not currently in use (Sep 2016), but kept for future needs
        iterator = (project._context2Notifiers.setdefault((name, action), OrderedDict())
                    for name in (className, 'AbstractWrapperObject'))
        pendingNotifications = project._pendingNotifications

        if action == 'rename':
            # Special case - cannot rename chemicalShift
            pass

        else:
            # Normal case - just call notifiers - as per AbstractWrapperObject
            if project._notificationSuspension and action != 'delete':
                # NB Deletion notifiers must currently be executed immediately
                for dd in iterator:
                    for notifier, onceOnly in dd.items():
                        pendingNotifications.append((notifier, onceOnly, self))
            else:
                for dd in iterator:
                    for notifier in tuple(dd):
                        notifier(self)

        return True

    def delete(self):
        """Delete the shift
        """
        raise RuntimeError(f'{self.className}.delete: Please use ChemicalShiftList.deleteChemicalShift()')

    def _restoreObject(self):
        """enable a notifier on the attached nmrAtom
        CCPN Internal - called from first creation from _restoreObject
        """
        _nmrAtom = self.nmrAtom
        # must assume that the shift value is correct at this point
        if _nmrAtom:
            _nmrAtom._chemicalShifts.append(self)

    def getByPid(self, pid: str):
        """Get an arbitrary data object from either its pid (e.g. 'SP:HSQC2') or its longPid
        (e.g. 'Spectrum:HSQC2')

        Returns None for invalid or unrecognised input strings.
        """
        if pid is None or len(pid) is None:
            return None

        obj = None

        # return if the pid does not conform to a pid definition
        if not Pid.Pid.isValid(pid):
            return None

        pid = Pid.Pid(pid)
        dd = self._project._pid2Obj.get(pid.type)
        if dd is not None:
            obj = dd.get(pid.id)
        if obj is not None and obj._isDeleted:
            raise RuntimeError(f'{self.className}.getByPid "%s" defined a deleted object' % pid)
        return obj

    #=========================================================================================
    # CCPN functions
    #=========================================================================================

    def _getAsTuple(self):
        """Return the contents of the shift as a tuple.
        """
        if self._isDeleted:
            raise RuntimeError(f'{self.className}._getAsTuple: shift is deleted')

        newRow = (self._uniqueId,
                  self._isDeleted,
                  self.value,
                  self.valueError,
                  self.figureOfMerit,
                  ) + \
                 (str(self.nmrAtom.pid) if self.nmrAtom else None,) + \
                 (tuple(val or None for val in self.nmrAtom.pid.fields) if self.nmrAtom else
                  (None, None, None, None)) + \
                 (self.comment,)
        newRow = ShiftParameters(*newRow)

        return newRow

    def _getAsPandasSeries(self):
        """Return the contents of the shift as a pandas series
        """
        _row = self._getAsTuple()
        return pd.DataFrame((_row,), columns=CS_COLUMNS)

    def _recalculateShiftValue(self):
        """Calculate the shift value
        """
        nmrAtom = self.nmrAtom
        if self._chemicalShiftList.autoUpdate:
            # with undoBlockWithoutSideBar():
            if nmrAtom:
                value, valueError = nmrAtom._recalculateShiftValue(self._chemicalShiftList.spectra)
            else:
                value, valueError = None, None

            # update the dataframe
            self._chemicalShiftList._setShiftAttribute(self._uniqueId, CS_VALUE, value)
            self._chemicalShiftList._setShiftAttribute(self._uniqueId, CS_VALUEERROR, valueError)

    def _renameNmrAtom(self, nmrAtom):
        """Update the values in the table for the renamed nmrAtom
        """
        if nmrAtom and self._chemicalShiftList._getShiftAttribute(self._uniqueId, CS_NMRATOM, str) != nmrAtom.pid:
            # nmrAtom and derived properties
            self._chemicalShiftList._setShiftAttributes(self._uniqueId, CS_NMRATOM, CS_ATOMNAME,
                                                        (str(nmrAtom.pid),) + tuple(val or None for val in nmrAtom.pid.fields))

    #===========================================================================================
    # new'Object' and other methods
    # Call appropriate routines in their respective locations
    #===========================================================================================

    def _tryToRecover(self):
        """Routine to try to recover an object that has not loaded correctly to repair integrity
        """
        pass

    @deleteV3Object()
    def _deleteWrapper(self, chemicalShiftList, _newDeletedShifts, _newShifts, _oldDeletedShifts, _oldShifts):
        """Delete a pure V3 ChemicalShift object
        Method is wrapped with create/delete notifier
        CCPN Internal - Not standalone - requires functionality from ChemicalShiftList
        """
        # add an undo/redo item to recover shifts
        with undoStackBlocking() as addUndoItem:
            # replace the contents of the internal list with the original/recovered items
            addUndoItem(undo=partial(chemicalShiftList._undoRedoShifts, _oldShifts),
                        redo=partial(chemicalShiftList._undoRedoShifts, _newShifts))
            addUndoItem(undo=partial(chemicalShiftList._undoRedoDeletedShifts, _oldDeletedShifts),
                        redo=partial(chemicalShiftList._undoRedoDeletedShifts, _newDeletedShifts))


def _newChemicalShift(chemicalShiftList, _ignoreUniqueId: bool = False
                      ):
    """Create a new chemicalShift attached to the chemicalShiftList.

    An nmrAtom can be attached to the shift as required.
    If attached (chainCode, sequenceCode, residueType, atomName) will be derived from the nmrAtom.pid
    If nmrAtom suplied as None, they can be set as string values.

    :param chemicalShiftList: parent chemicalShiftList
    :return: a new ChemicalShift instance.
    """

    result = _ChemicalShift(chemicalShiftList, _ignoreUniqueId=_ignoreUniqueId)
    if result is None:
        raise RuntimeError('ChemicalShiftList._newChemicalShift: unable to generate new ChemicalShift item')

    return result


def _getByTuple(chemicalShiftList,
                value: float = None, valueError: float = None, figureOfMerit: float = 1.0,
                nmrAtom: Union[NmrAtom, str, None] = None,
                chainCode: str = None, sequenceCode: str = None, residueType: str = None, atomName: str = None,
                comment: str = None):
    """Create a new tuple object from the supplied parameters
    Check whether a valid tuple can be created, otherwise raise the appropriate errors
    CCPN Internal
    """
    # check whether the parameters are valid
    if nmrAtom and any((chainCode, sequenceCode, residueType, atomName)):
        # compare with parameter not the found nmrAtom
        raise ValueError('Cannot set nmrAtom and derived Properties at the same time')

    # now check with the 'found' nmrAtom
    nmrAtom = chemicalShiftList.project.getByPid(nmrAtom) if isinstance(nmrAtom, str) else nmrAtom

    if not isinstance(nmrAtom, (NmrAtom, type(None))):
        raise ValueError('nmrAtom must be of type nmrAtom or None')
    if not all(isinstance(val, (str, type(None))) for val in (chainCode, sequenceCode, residueType, atomName)):
        raise ValueError('chainCode, sequenceCode, residueType, atomName must be of type str or None')
    if not all(isinstance(val, (float, type(None))) for val in (value, valueError, figureOfMerit)):
        raise ValueError('value, valueError, figureOfMerit must be of type float or None')
    if figureOfMerit is not None and not (MINFOM <= figureOfMerit <= MAXFOM):
        raise ValueError(f'figureOfMerit must be in range [{MINFOM} - {MAXFOM}]')

    newRow = (None,
              None,
              value,
              valueError,
              figureOfMerit,
              ) + \
             (((str(nmrAtom.pid),) + tuple(val or None for val in nmrAtom.pid.fields)) if nmrAtom else
              (None, chainCode or None, sequenceCode or None, residueType or None, atomName or None)) + \
             (comment,)
    newRow = ShiftParameters(*newRow)

    return newRow
