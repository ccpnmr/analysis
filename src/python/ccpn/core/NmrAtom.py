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
__dateModified__ = "$dateModified: 2020-04-22 11:35:30 +0100 (Wed, April 22, 2020) $"
__version__ = "$Revision: 3.0.1 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from typing import Union, Tuple
from functools import partial
from ccpn.core.NmrResidue import NmrResidue
from ccpn.core.Project import Project
from ccpn.core._implementation.AbstractWrapperObject import AbstractWrapperObject
from ccpn.core.lib import Pid
from ccpn.core.lib.Util import AtomIdTuple
from ccpnmodel.ccpncore.api.ccp.nmr import Nmr
from ccpnmodel.ccpncore.lib import Constants
from ccpn.util.Common import name2IsotopeCode
from ccpn.util.decorators import logCommand
from ccpn.core.lib.ContextManagers import newObject, renameObject, undoBlock, renameObjectContextManager
from ccpn.util.Logging import getLogger


class NmrAtom(AbstractWrapperObject):
    """NmrAtom objects are used for assignment. An NmrAtom within an assigned NmrResidue is
    by definition assigned to the Atom with the same name (if any).

    NmrAtoms serve as a way of connecting a named nucleus to an observed chemical shift,
    and peaks are assigned to NmrAtoms. Renaming an NmrAtom (or its containing NmrResidue or
    NmrChain) automatically updates peak assignments and ChemicalShifts that use the NmrAtom,
    preserving the link.

    NmrAtom names must start with the atom type, ('H' for proton, 'D' for deuterium, 'C' for
    carbon, etc.), with '?' for 'unknown."""

    #: Short class name, for PID.
    shortClassName = 'NA'
    # Attribute it necessary as subclasses must use superclass className
    className = 'NmrAtom'

    _parentClass = NmrResidue

    #: Name of plural link to instances of class
    _pluralLinkName = 'nmrAtoms'

    # the attribute name used by current
    _currentAttributeName = 'nmrAtoms'

    #: List of child classes.
    _childClasses = []

    # Qualified name of matching API class
    _apiClassQualifiedName = Nmr.Resonance._metaclass.qualifiedName()

    # CCPN properties
    @property
    def _apiResonance(self) -> Nmr.Resonance:
        """ CCPN atom matching Atom"""
        return self._wrappedData

    @property
    def _parent(self) -> NmrResidue:
        """Parent (containing) object."""
        if self._wrappedData.resonanceGroup in self._project._data2Obj:
            return self._project._data2Obj[self._wrappedData.resonanceGroup]

    nmrResidue = _parent

    @property
    def _key(self) -> str:
        """Atom name string (e.g. 'HA') regularised as used for ID"""
        return self._wrappedData.name.translate(Pid.remapSeparators)

    @property
    def _localCcpnSortKey(self) -> Tuple:
        """Local sorting key, in context of parent."""

        # We want sorting by name, even though Resonances have serials
        return (self._key,)

    @property
    def _idTuple(self) -> AtomIdTuple:
        """ID as chainCode, sequenceCode, residueType, atomName namedtuple
        NB Unlike the _id and key, these do NOT have reserved characters mapped to '^'
        NB _idTuple replaces empty strings with None"""
        parent = self._parent
        ll = [parent._parent.shortName, parent.sequenceCode, parent.residueType, self.name]
        return AtomIdTuple(*(x or None for x in ll))

    @property
    def name(self) -> str:
        """Atom name string (e.g. 'HA')"""
        return self._wrappedData.name

    @name.setter
    def name(self, value: str):
        """set Atom name"""
        self.rename(value)

    @property
    def serial(self) -> int:
        """NmrAtom serial number - set at creation and unchangeable"""
        return self._wrappedData.serial

    # @property
    # def comment(self) -> str:
    #     """Free-form text comment"""
    #     return self._wrappedData.details
    #
    # @comment.setter
    # def comment(self, value: str):
    #     self._wrappedData.details = value

    #from ccpn.core.Atom import Atom: This will break the import sequence
    @property
    def atom(self) -> 'Atom':
        """Atom to which NmrAtom is assigned. NB resetting the atom will rename the NmrAtom"""
        return self._project.getAtom(self._id)

    # # GWV 20181122: removed setters between Chain/NmrChain, Residue/NmrResidue, Atom/NmrAtom
    # @atom.setter
    # def atom(self, value: 'Atom'):
    #     if value is None:
    #         self.deassign()
    #     else:
    #         self._wrappedData.atom = value._wrappedData

    @property
    def isotopeCode(self) -> str:
        """isotopeCode of NmrAtom. Set automatically on creation (from NmrAtom name)
        and cannot be changed later"""
        return self._wrappedData.isotopeCode

    @property
    def boundNmrAtoms(self) -> 'NmrAtom':
        """NmrAtoms directly bound to this one, as calculated from assignment and
        NmrAtom name matches (NOT from peak assignment)"""
        getDataObj = self._project._data2Obj.get
        ll = self._wrappedData.getBoundResonances()
        result = [getDataObj(x) for x in ll]

        nmrResidue = self.nmrResidue
        if nmrResidue.residue is None:
            # NmrResidue is unassigned. Add ad-hoc protein interresidue bonds
            if self.name == 'N':
                for rx in (nmrResidue.previousNmrResidue, nmrResidue.getOffsetNmrResidue(-1)):
                    if rx is not None:
                        na = rx.getNmrAtom('C')
                        if na is not None:
                            result.append(na)
            elif self.name == 'C':
                for rx in (nmrResidue.nextNmrResidue, nmrResidue.getOffsetNmrResidue(1)):
                    if rx is not None:
                        na = rx.getNmrAtom('N')
                        if na is not None:
                            result.append(na)
        #
        return result

    @property
    def assignedPeaks(self) -> Tuple['Peak']:
        """All Peaks assigned to the NmrAtom"""
        apiResonance = self._wrappedData
        apiPeaks = [x.peakDim.peak for x in apiResonance.peakDimContribs]
        apiPeaks.extend([x.peakDim.peak for x in apiResonance.peakDimContribNs])

        data2Obj = self._project._data2Obj
        return sorted(data2Obj[x] for x in set(apiPeaks))

    @logCommand(get='self')
    def deassign(self):
        """Reset NmrAtom back to its originalName, cutting all assignment links"""
        self._wrappedData.name = None

    @logCommand(get='self')
    def assignTo(self, chainCode: str = None, sequenceCode: Union[int, str] = None,
                 residueType: str = None, name: str = None, mergeToExisting=False) -> 'NmrAtom':
        """Assign NmrAtom to naming parameters) and return the reassigned result

        If the assignedTo NmrAtom already exists the function raises ValueError.
        If mergeToExisting is True it instead merges the current NmrAtom into the target
        and returns the merged target. NB Merging is NOT undoable

        WARNING: is mergeToExisting is True, always use in the form "x = x.assignTo(...)",
        as the call 'x.assignTo(...) may cause the source x object to be deleted.

        Passing in empty parameters (e.g. chainCode=None) leaves the current value unchanged. E.g.:
        for NmrAtom NR:A.121.ALA.HA calling with sequenceCode=124 will assign to
        (chainCode='A', sequenceCode=124, residueType='ALA', atomName='HA')


        The function works as:

        nmrChain = project.fetchNmrChain(shortName=chainCode)

        nmrResidue = nmrChain.fetchNmrResidue(sequenceCode=sequenceCode, residueType=residueType)

        (or nmrChain.fetchNmrResidue(sequenceCode=sequenceCode) if residueType is None)
        """

        oldPid = self.longPid
        clearUndo = False
        undo = self._apiResonance.root._undo
        apiResonance = self._apiResonance
        apiResonanceGroup = apiResonance.resonanceGroup

        with undoBlock():
            if sequenceCode is not None:
                sequenceCode = str(sequenceCode) or None

            # set missing parameters to existing values
            chainCode = chainCode or apiResonanceGroup.nmrChain.code
            sequenceCode = sequenceCode or apiResonanceGroup.sequenceCode
            residueType = residueType or apiResonanceGroup.residueType
            name = name or apiResonance.name

            for ss in chainCode, sequenceCode, residueType, name:
                if ss and Pid.altCharacter in ss:
                    raise ValueError("Character %s not allowed in ccpn.NmrAtom id : %s.%s.%s.%s"
                                     % (Pid.altCharacter, chainCode, sequenceCode, residueType, name))

            isotopeCode = self.isotopeCode
            if name and isotopeCode not in (None, '?'):
                # Check for isotope match
                if name2IsotopeCode(name) not in (isotopeCode, None):
                    raise ValueError("Cannot reassign %s type NmrAtom to %s" % (isotopeCode, name))

            oldNmrResidue = self.nmrResidue
            nmrChain = self._project.fetchNmrChain(chainCode)
            if residueType:
                nmrResidue = nmrChain.fetchNmrResidue(sequenceCode, residueType)
            else:
                nmrResidue = nmrChain.fetchNmrResidue(sequenceCode)

            if name:
                # result is matching NmrAtom, or (if None) self
                result = nmrResidue.getNmrAtom(name) or self
            else:
                # No NmrAtom can match, result is self
                result = self

            if nmrResidue is oldNmrResidue:
                if name != self.name:
                    # NB self.name can never be returned as None

                    if result is self:
                        self._wrappedData.name = name or None

                    elif mergeToExisting:
                        clearUndo = True
                        result._wrappedData.absorbResonance(self._apiResonance)
                        self._project._logger.warning("Merging (1) %s into %s. Merging is NOT undoable."
                                                      % (oldPid, result.longPid))

                    else:
                        raise ValueError("New assignment clash with existing assignment,"
                                         " and merging is disallowed")

            else:

                if result is self:
                    if nmrResidue.getNmrAtom(self.name) is None:
                        self._apiResonance.resonanceGroup = nmrResidue._apiResonanceGroup
                        if name != self.name:
                            self._wrappedData.name = name or None
                    elif name is None or oldNmrResidue.getNmrAtom(name) is None:
                        if name != self.name:
                            self._wrappedData.name = name or None
                        self._apiResonance.resonanceGroup = nmrResidue._apiResonanceGroup
                    else:
                        self._wrappedData.name = None  # Necessary to avoid name clashes
                        self._apiResonance.resonanceGroup = nmrResidue._apiResonanceGroup
                        self._wrappedData.name = name

                elif mergeToExisting:
                    # WARNING if we get here undo is no longer possible
                    clearUndo = True
                    result._wrappedData.absorbResonance(self._apiResonance)
                    self._project._logger.warning("Merging (2) %s into %s. Merging is NOT undoable."
                                                  % (oldPid, result.longPid))
                else:
                    raise ValueError("New assignment clash with existing assignment,"
                                     " and merging is disallowed")
            #
            if undo is not None and clearUndo:
                undo.clear()

        return result

    @property
    def chemicalShifts(self) -> Tuple:
        "Returns ChemicalShift objects connected to NmrAtom"
        getDataObj = self._project._data2Obj.get
        return tuple(sorted(getDataObj(x) for x in self._wrappedData.shifts))

    #=========================================================================================
    # Implementation functions
    #=========================================================================================

    @classmethod
    def _getAllWrappedData(cls, parent: NmrResidue) -> list:
        """get wrappedData (ApiResonance) for all NmrAtom children of parent NmrResidue
        """
        return parent._wrappedData.sortedResonances()

    def _finaliseAction(self, action: str):
        """Subclassed to handle associated ChemicalShift instances
        """
        super()._finaliseAction(action=action)

        # propagate the rename to associated ChemicalShift instances
        if action in ['rename', 'delete', 'change']:
            for cs in self.chemicalShifts:
                cs._finaliseAction(action=action)

    def _setIsotopeCode(self, value):
        # value must be defined, if not set then can set to arbitrary value '?'
        # this means it can still be set at any isotopeCode later, otherwise need to undo or create new nmrAtom
        self._wrappedData.isotopeCode = value if value else '?'

    @logCommand(get='self')
    def rename(self, value: str = None):
        """Rename the NmrAtom, changing its name, Pid, and internal representation."""

        # NBNB TODO change so you can set names of the form '@123' (?)

        # NB This is a VERY special case
        # - API code and notifiers will take care of resetting id and Pid
        self._validateName(value=value, allowWhitespace=False, allowNone=True)

        with renameObjectContextManager(self) as addUndoItem:
            oldName = self.name

            isotopeChanged = False
            isotopeCode = self._wrappedData.isotopeCode
            newIsotopeCode = name2IsotopeCode(value)            # this could be None for undefined
            if newIsotopeCode is not None:
                if isotopeCode == '?':
                    self._wrappedData.isotopeCode = newIsotopeCode
                    isotopeChanged = True
                elif newIsotopeCode != isotopeCode:
                    raise ValueError("Cannot rename %s type NmrAtom to %s - invalid isotopeCode" % (isotopeCode, value))

            try:
                self._wrappedData.name = value
            except Exception as es:
                raise ValueError("Cannot rename %s type NmrAtom to %s" % (isotopeCode, value))

            if isotopeChanged:
                addUndoItem(redo=partial(self._setIsotopeCode, newIsotopeCode))

            addUndoItem(undo=partial(self.rename, oldName),
                        redo=partial(self.rename, value))

            if isotopeChanged:
                addUndoItem(undo=partial(self._setIsotopeCode, isotopeCode))

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

#GWV 20181122: moved to Atom class
# def getter(self: Atom) -> Optional[NmrAtom]:
#     try:
#         return self._project.getNmrAtom(self._id)
#     except:
#         return None
#
#
# def setter(self: Atom, value: NmrAtom):
#     oldValue = self.nmrAtom
#     if oldValue is value:
#         return
#     elif value is None:
#         raise ValueError("Cannot set Atom.nmrAtom to None")
#     elif oldValue is not None:
#         raise ValueError("New assignment of Atom clashes with existing assignment")
#     else:
#         value.atom = self
#
#
# Atom.nmrAtom = property(getter, setter, None, "NmrAtom to which Atom is assigned")
#
# del getter
# del setter


@newObject(NmrAtom)
def _newNmrAtom(self: NmrResidue, name: str = None, isotopeCode: str = None,
                comment: str = None, serial: int = None) -> NmrAtom:
    """Create new NmrAtom within NmrResidue. If name is None, use default name
        (of form e.g. 'H@211', 'N@45', ...)

    See the NmrAtom class for details

    :param name: string name of the new nmrAtom
    :param isotopeCode: isotope code
    :param comment: optional string comment
    :param serial: optional serial number.
    :return: a new NmrAtom instance.
    """
    nmrProject = self._project._wrappedData
    resonanceGroup = self._wrappedData

    if not isinstance(name, (str, type(None))):
        raise TypeError('Name {} must be of type string (or None)'.format(name))
    if not isinstance(isotopeCode, (str, type(None))):
        raise TypeError('isotopeCode {} must be of type string (or None)'.format(isotopeCode))

    # Set isotopeCode if empty
    if not isotopeCode:
        if name:
            isotopeCode = name2IsotopeCode(name) or '?'
        else:
            isotopeCode = '?'

    # Deal with reserved names
    # serial = None
    if name:
        # Check for name clashes

        previous = self.getNmrAtom(name.translate(Pid.remapSeparators))
        if previous is not None:
            raise ValueError("%s already exists" % previous.longPid)

        # Deal with reserved names
        index = name.find('@')
        if index >= 0:
            try:
                serial = int(name[index + 1:])
                obj = nmrProject.findFirstResonance(serial=serial)
            except ValueError:
                obj = None
            if obj is not None:
                previous = self._project._data2Obj[obj]
                if '@' in obj.name:
                    # Two NmrAtoms both with same @serial. Error
                    raise ValueError("Cannot create NmrAtom:%s.%s - reserved atom name clashes with %s"
                                     % (self._id, name, previous.longPid))
                else:
                    # We can renumber obj to free the serial for the new NmrAtom
                    newSerial = obj.parent._serialDict['resonances'] + 1
                    try:
                        previous.resetSerial(newSerial)
                        # modelUtil.resetSerial(obj, newSerial, 'resonances')
                    except ValueError:
                        self.project._logger.warning(
                                "Could not reset serial of %s to %s - keeping original value" % (previous, serial)
                                )
                    previous._finaliseAction('rename')

    dd = {'resonanceGroup': resonanceGroup, 'isotopeCode': isotopeCode}
    if serial is None:
        dd['name'] = name
    if comment is None:
        dd['details'] = name

    # NOTE:ED - check violated name, replaces the isotopeCode with '?' - follows v2 model check
    checkIsotopeCode = isotopeCode.upper()
    if name and not name.startswith(checkIsotopeCode):
        from ccpn.util.Constants import isotopeRecords

        record = isotopeRecords.get(checkIsotopeCode)
        if record:
            isValid = name.startswith(record.symbol)
            if not isValid:
                getLogger().warning("Invalid isotopeCode %s for nmrAtom name %s, setting isotopeCode to '?'" % (isotopeCode, name))
                dd['isotopeCode'] = '?'

    obj = nmrProject.newResonance(**dd)
    result = self._project._data2Obj.get(obj)
    if result is None:
        raise RuntimeError('Unable to generate new NmrAtom item')

    if serial is not None:
        try:
            result.resetSerial(serial)
        except ValueError:
            getLogger().warning("Could not reset serial of %s to %s - keeping original value"
                                % (result, serial))

    return result


def _fetchNmrAtom(self: NmrResidue, name: str):
    """Fetch NmrAtom with name=name, creating it if necessary

    :param name: string name for new nmrAto if created
    :return: new or existing nmrAtom
    """
    # resonanceGroup = self._wrappedData

    with undoBlock():
        result = (self.getNmrAtom(name.translate(Pid.remapSeparators)) or
                  self.newNmrAtom(name=name))

        if result is None:
            raise RuntimeError('Unable to generate new NmrAtom item')

    return result


def _produceNmrAtom(self: Project, atomId: str = None, chainCode: str = None,
                    sequenceCode: Union[int, str] = None,
                    residueType: str = None, name: str = None) -> NmrAtom:
    """Get chainCode, sequenceCode, residueType and atomName from dot-separated atomId or Pid
    or explicit parameters, and find or create an NmrAtom that matches
    Empty chainCode gets NmrChain:@- ; empty sequenceCode get a new NmrResidue"""

    with undoBlock():

        # Get ID parts to use
        if sequenceCode is not None:
            sequenceCode = str(sequenceCode) or None
        params = [chainCode, sequenceCode, residueType, name]
        if atomId:
            if any(params):
                raise ValueError("_produceNmrAtom: other parameters only allowed if atomId is None")
            else:
                # Remove colon prefix, if any
                atomId = atomId.split(Pid.PREFIXSEP, 1)[-1]
                for ii, val in enumerate(Pid.splitId(atomId)):
                    if val:
                        params[ii] = val
                chainCode, sequenceCode, residueType, name = params

        if name is None:
            raise ValueError("NmrAtom name must be set")

        elif Pid.altCharacter in name:
            raise ValueError("Character %s not allowed in ccpn.NmrAtom.name" % Pid.altCharacter)

        # Produce chain
        nmrChain = self.fetchNmrChain(shortName=chainCode or Constants.defaultNmrChainCode)
        nmrResidue = nmrChain.fetchNmrResidue(sequenceCode=sequenceCode, residueType=residueType)
        result = nmrResidue.fetchNmrAtom(name)

        if result is None:
            raise RuntimeError('Unable to generate new NmrAtom item')

    return result


#EJB 20181203: moved to NmrResidue
# NmrResidue.newNmrAtom = _newNmrAtom
# del _newNmrAtom
# NmrResidue.fetchNmrAtom = _fetchNmrAtom

#EJB 20181203: moved to nmrAtom
# Project._produceNmrAtom = _produceNmrAtom

# Notifiers:
className = Nmr.Resonance._metaclass.qualifiedName()
Project._apiNotifiers.extend(
        (('_finaliseApiRename', {}, className, 'setImplName'),
         ('_finaliseApiRename', {}, className, 'setResonanceGroup'),
         )
        )
for clazz in Nmr.AbstractPeakDimContrib._metaclass.getNonAbstractSubtypes():
    className = clazz.qualifiedName()
    Project._apiNotifiers.extend(
            (('_modifiedLink', {'classNames': ('NmrAtom', 'Peak')}, className, 'create'),
             ('_modifiedLink', {'classNames': ('NmrAtom', 'Peak')}, className, 'delete'),
             )
            )
