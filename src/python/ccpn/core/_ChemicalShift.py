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
__dateModified__ = "$dateModified: 2021-08-05 18:55:49 +0100 (Thu, August 05, 2021) $"
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
from typing import Optional, Union
from collections import namedtuple
from ccpn.core.Project import Project
from ccpn.core.NmrAtom import NmrAtom
from ccpn.core.lib.ContextManagers import ccpNmrV3CoreSetter, checkDeleted
from ccpn.core.lib import Pid


UNIQUEID = 'uniqueId'
VALUE = 'value'
VALUEERROR = 'valueError'
FIGUREOFMERIT = 'figureOfMerit'
NMRATOM = 'nmrAtom'
CHAINCODE = 'chainCode'
SEQUENCECODE = 'sequenceCode'
RESIDUETYPE = 'residueType'
ATOMNAME = 'atomName'
SHIFTLISTPEAKS = 'shiftListPeaks'
ALLPEAKS = 'allPeaks'
SHIFTLISTPEAKSCOUNT = 'shiftListPeaksCount'
ALLPEAKSCOUNT = 'allPeaksCount'
COMMENT = 'comment'
ISDELETED = 'isDeleted'

SHIFTCOLUMNS = (UNIQUEID, ISDELETED,
                VALUE, VALUEERROR, FIGUREOFMERIT,
                NMRATOM, CHAINCODE, SEQUENCECODE, RESIDUETYPE, ATOMNAME,
                COMMENT)
SHIFTTABLECOLUMNS = (UNIQUEID, ISDELETED,
                     VALUE, VALUEERROR, FIGUREOFMERIT,
                     NMRATOM, CHAINCODE, SEQUENCECODE, RESIDUETYPE, ATOMNAME,
                     ALLPEAKS, SHIFTLISTPEAKSCOUNT, ALLPEAKSCOUNT,
                     COMMENT)

SHIFTNAME = 'ChemicalShift'
PLURALSHIFTNAME = 'chemicalShifts'

MINFOM = 0.0
MAXFOM = 1.0

ShiftParameters = namedtuple('ShiftParameters', f'{UNIQUEID} {ISDELETED} {VALUE} {VALUEERROR} {FIGUREOFMERIT} '
                                                f'{NMRATOM} {CHAINCODE} {SEQUENCECODE} {RESIDUETYPE} {ATOMNAME} '
                                                f'{COMMENT} ')


class _ChemicalShift():
    """Chemical Shift, containing a ChemicalShift value for the NmrAtom they belong to.

    Chemical shift values are continuously averaged over peaks assigned to the NmrAtom,
    (unless this behaviour is turned off)

    ChemicalShift objects are sorted by uniqueId.
    """

    #: Short class name, for PID.
    shortClassName = 'CS'
    # Attribute it necessary as subclasses must use superclass className
    className = 'ChemicalShift'

    # _parentClass = ChemicalShiftList

    #: Name of plural link to instances of class
    _pluralLinkName = 'chemicalShifts'

    # the attribute name used by current
    _currentAttributeName = 'chemicalShifts'

    def __init__(self, chemicalShiftList, _ignoreUniqueId=False):
        """Create a new instance of v3 Shift
        """
        self._chemicalShiftList = chemicalShiftList
        self._project = chemicalShiftList.project
        self._uniqueId = None if _ignoreUniqueId else self.project._getNextUniqueIdValue(SHIFTNAME)
        # All properties are derived from the chemicalShiftList pandas dataframe

    def __repr__(self):
        """Object string representation; compatible with application.get()
        """
        return ("<%s-Deleted>" % self.pid) if self.isDeleted else ("<%s>" % self.pid)

    def __str__(self):
        """Readable string representation; potentially subclassed
        """
        return ("<%s-Deleted>" % self.pid) if self.isDeleted else ("<%s>" % self.pid)

    #=========================================================================================
    # CCPN Properties
    #=========================================================================================

    @property
    def project(self) -> 'Project':
        """The Project (root)containing the object.
        """
        return self._project

    @property
    def pid(self) -> Pid.Pid:
        """Identifier for the object, unique within the project.
        Set automatically from the short class name, the parent chemicalShiftList and object.uniqueId
        E.g. 'CS:default.1'
        """
        return Pid.Pid.new(self.shortClassName, self._chemicalShiftList.name, self._uniqueId)

    @property
    def longPid(self) -> Pid.Pid:
        """Identifier for the object, unique within the project.
        Set automatically from the full class name, the parent chemicalShiftList and object.uniqueId
        E.g. 'ChemicalShift:default.1'
        """
        return Pid.Pid(Pid.PREFIXSEP.join((self.className, self._uniqueId)))

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
        # not sure why this sometimes returns a numpy bool
        return bool(self._chemicalShiftList._getShiftAttribute(self._uniqueId, ISDELETED))

    @property
    def _deleted(self) -> bool:
        """True if this object is deleted.
        CCPN Internal - allows internal deletion of the ChemicalShift
        """
        # not sure why this sometimes returns a numpy bool
        return bool(self._chemicalShiftList._getShiftAttribute(self._uniqueId, ISDELETED))

    @_deleted.setter
    @ccpNmrV3CoreSetter()
    def _deleted(self, value: bool):
        if not isinstance(value, bool):
            raise ValueError(f'{self.className}.isDeleted must be True/False')
        self._chemicalShiftList._setShiftAttribute(self._uniqueId, ISDELETED, value)

    #~~~~~~~~~~~~~~~~

    @property
    @checkDeleted()
    def value(self) -> Optional[float]:
        """shift value of ChemicalShift, in unit as defined in the ChemicalShiftList.
        """
        return self._chemicalShiftList._getShiftAttribute(self._uniqueId, VALUE)

    @value.setter
    @checkDeleted()
    @ccpNmrV3CoreSetter()
    def value(self, val: Optional[float]):
        if not isinstance(val, (float, type(None))):
            raise ValueError(f'{self.className}.value must be of type float or None')
        _nmrAtomPid = self._chemicalShiftList._getShiftAttribute(self._uniqueId, NMRATOM)
        if _nmrAtomPid:
            raise ValueError(f'{self.className}.value cannot be changed with attached nmrAtom')
        self._chemicalShiftList._setShiftAttribute(self._uniqueId, VALUE, val)

    #~~~~~~~~~~~~~~~~

    @property
    @checkDeleted()
    def valueError(self) -> Optional[float]:
        """shift valueError of ChemicalShift, in unit as defined in the ChemicalShiftList.
        """
        return self._chemicalShiftList._getShiftAttribute(self._uniqueId, VALUEERROR)

    @valueError.setter
    @checkDeleted()
    @ccpNmrV3CoreSetter()
    def valueError(self, value: Optional[float]):
        if not isinstance(value, (float, type(None))):
            raise ValueError(f'{self.className}.valueError must be of type float or None')
        self._chemicalShiftList._setShiftAttribute(self._uniqueId, VALUEERROR, value)

    #~~~~~~~~~~~~~~~~

    @property
    @checkDeleted()
    def figureOfMerit(self) -> Optional[float]:
        """Figure of Merit for ChemicalShift, between 0.0 and 1.0 inclusive.
        """
        return self._chemicalShiftList._getShiftAttribute(self._uniqueId, FIGUREOFMERIT)

    @figureOfMerit.setter
    @checkDeleted()
    @ccpNmrV3CoreSetter()
    def figureOfMerit(self, value: Optional[float]):
        if not isinstance(value, (float, type(None))):
            raise ValueError(f'{self.className}.figureOfMerit must be of type float or None')
        if value is not None and not (MINFOM <= value <= MAXFOM):
            raise ValueError(f'{self.className}.figureOfMerit must be in range [{MINFOM} - {MAXFOM}]')
        self._chemicalShiftList._setShiftAttribute(self._uniqueId, FIGUREOFMERIT, value)

    #~~~~~~~~~~~~~~~~

    @property
    @checkDeleted()
    def nmrAtom(self) -> Optional[NmrAtom]:
        """Attached NmrAtom.
        """
        _nmrAtomPid = self._chemicalShiftList._getShiftAttribute(self._uniqueId, NMRATOM)
        return self.project.getByPid(_nmrAtomPid)

    @nmrAtom.setter
    @checkDeleted()
    @ccpNmrV3CoreSetter()
    def nmrAtom(self, value: Union[NmrAtom, str, None]):
        # NOTE:ED - handle updating shift values
        if value is None:
            # clear the nmrAtom and derived values
            self._chemicalShiftList._setShiftAttributes(self._uniqueId, NMRATOM, ATOMNAME, (None, None, None, None, None))
        else:
            _nmrAtom = self._project.getByPid(value) if isinstance(value, str) else value
            if not _nmrAtom:
                raise ValueError(f'{self.className}.nmrAtom: {value} not found')
            if not isinstance(_nmrAtom, NmrAtom):
                raise ValueError(f'{self.className}.nmrAtom: {value} must be of type NmrAtom')

            if self._chemicalShiftList._searchChemicalShifts(nmrAtom=_nmrAtom):
                raise ValueError(f'{self.className}.nmrAtom: {_nmrAtom.pid} already exists')

            # nmrAtom and derived properties
            self._chemicalShiftList._setShiftAttributes(self._uniqueId, NMRATOM, ATOMNAME,
                                                        (str(_nmrAtom.pid),) + tuple(val or None for val in _nmrAtom.pid.fields))

    #~~~~~~~~~~~~~~~~

    @property
    @checkDeleted()
    def chainCode(self) -> Optional[str]:
        """chainCode for attached nmrAtom.
        """
        return self._chemicalShiftList._getShiftAttribute(self._uniqueId, CHAINCODE)

    @chainCode.setter
    @checkDeleted()
    @ccpNmrV3CoreSetter()
    def chainCode(self, value: Optional[str]):
        if not isinstance(value, (str, type(None))):
            raise ValueError(f'{self.className}.chainCode must be of type str or None')
        _nmrAtomPid = self._chemicalShiftList._getShiftAttribute(self._uniqueId, NMRATOM)
        if _nmrAtomPid:
            raise RuntimeError(f'{self.className}.chainCode: derived value, cannot modify when nmrAtom is set')
        # only set if the nmrAtom has not been set
        self._chemicalShiftList._setShiftAttribute(self._uniqueId, CHAINCODE, value)

    #~~~~~~~~~~~~~~~~

    @property
    @checkDeleted()
    def sequenceCode(self) -> Optional[str]:
        """sequenceCode for attached nmrAtom.
        """
        return self._chemicalShiftList._getShiftAttribute(self._uniqueId, SEQUENCECODE)

    @sequenceCode.setter
    @checkDeleted()
    @ccpNmrV3CoreSetter()
    def sequenceCode(self, value: Optional[str]):
        if not isinstance(value, (str, type(None))):
            raise ValueError(f'{self.className}.sequenceCode must be of type str or None')
        _nmrAtomPid = self._chemicalShiftList._getShiftAttribute(self._uniqueId, NMRATOM)
        if _nmrAtomPid:
            raise RuntimeError(f'{self.className}.sequenceCode: derived value, cannot modify when nmrAtom is set')
        # only set if the nmrAtom has not been set
        self._chemicalShiftList._setShiftAttribute(self._uniqueId, SEQUENCECODE, value)

    #~~~~~~~~~~~~~~~~

    @property
    @checkDeleted()
    def residueType(self) -> Optional[str]:
        """residueType for attached nmrAtom.
        """
        return self._chemicalShiftList._getShiftAttribute(self._uniqueId, RESIDUETYPE)

    @residueType.setter
    @checkDeleted()
    @ccpNmrV3CoreSetter()
    def residueType(self, value: Optional[str]):
        if not isinstance(value, (str, type(None))):
            raise ValueError(f'{self.className}.residueType must be of type str or None')
        _nmrAtomPid = self._chemicalShiftList._getShiftAttribute(self._uniqueId, NMRATOM)
        if _nmrAtomPid:
            raise RuntimeError(f'{self.className}.residueType: derived value, cannot modify when nmrAtom is set')
        # only set if the nmrAtom has not been set
        self._chemicalShiftList._setShiftAttribute(self._uniqueId, RESIDUETYPE, value)

    #~~~~~~~~~~~~~~~~

    @property
    @checkDeleted()
    def atomName(self) -> Optional[str]:
        """atomName for attached nmrAtom.
        """
        return self._chemicalShiftList._getShiftAttribute(self._uniqueId, ATOMNAME)

    @atomName.setter
    @checkDeleted()
    @ccpNmrV3CoreSetter()
    def atomName(self, value: Optional[str]):
        if not isinstance(value, (str, type(None))):
            raise ValueError(f'{self.className}.atomName must be of type str or None')
        _nmrAtomPid = self._chemicalShiftList._getShiftAttribute(self._uniqueId, NMRATOM)
        if _nmrAtomPid:
            raise RuntimeError(f'{self.className}.atomName: derived value, cannot modify when nmrAtom is set')
        # only set if the nmrAtom has not been set
        self._chemicalShiftList._setShiftAttribute(self._uniqueId, ATOMNAME, value)

    #~~~~~~~~~~~~~~~~

    @property
    @checkDeleted()
    def comment(self) -> Optional[str]:
        """comment for attached nmrAtom.
        """
        return self._chemicalShiftList._getShiftAttribute(self._uniqueId, COMMENT)

    @comment.setter
    @checkDeleted()
    @ccpNmrV3CoreSetter()
    def comment(self, value: Optional[str]):
        if not isinstance(value, (str, type(None))):
            raise ValueError(f'{self.className}.comment must be of type str or None')
        self._chemicalShiftList._setShiftAttribute(self._uniqueId, COMMENT, value)

    #~~~~~~~~~~~~~~~~

    @property
    @checkDeleted()
    def assignedPeaks(self) -> Optional[tuple]:
        """Assigned peaks for attached nmrAtom belonging to this chemicalShiftList.
        """
        _nmrAtomPid = self._chemicalShiftList._getShiftAttribute(self._uniqueId, NMRATOM)
        _nmrAtom = self.project.getByPid(_nmrAtomPid)
        if _nmrAtom:
            return tuple(set(pp for pp in _nmrAtom.assignedPeaks if pp.chemicalShiftList == self))
        # NOTE:ED - check

    @property
    @checkDeleted()
    def allAssignedPeaks(self) -> Optional[tuple]:
        """All assigned peaks for attached nmrAtom.
        """
        _nmrAtomPid = self._chemicalShiftList._getShiftAttribute(self._uniqueId, NMRATOM)
        _nmrAtom = self.project.getByPid(_nmrAtomPid)
        if _nmrAtom:
            return tuple(set(_nmrAtom.assignedPeaks))
        # NOTE:ED - check

    #=========================================================================================
    # Implementation functions
    #=========================================================================================

    def _resetUniqueId(self, value):
        """Reset the uniqueId
        CCPN Internal
        """
        if self._chemicalShiftList._searchChemicalShifts(uniqueId=value):
            raise ValueError(f'ChemicalShiftList._resetUniqueId: uniqueId {value} already exists')
        self._uniqueId = value
        # NOTE:ED - link to pandas and shiftList - not used yet

    def _finaliseAction(self, action: str):
        """Do wrapper level finalisation, and execute all notifiers
        action is one of: 'create', 'delete', 'change', 'rename'
        """

        if self.project._notificationBlanking:
            return

        # TODO:ED - handle notifiers

    def delete(self):
        """Delete the shift
        """
        raise RuntimeError(f'{self.className}.delete: Please use ChemicalShiftList.deleteChemicalShift()')

    #=========================================================================================
    # CCPN functions
    #=========================================================================================

    def _getAsTuple(self):
        """Return the contents of the shift as a tuple.
        """
        newRow = (self._uniqueId,
                  self.isDeleted,
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
        return pd.DataFrame((_row,), columns=SHIFTCOLUMNS)

    #===========================================================================================
    # new'Object' and other methods
    # Call appropriate routines in their respective locations
    #===========================================================================================

    def _tryToRecover(self):
        """Routine to try to recover an object that has not loaded correctly to repair integrity
        """
        pass


# TODO:ED - need new decorator
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
