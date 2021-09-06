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
__dateModified__ = "$dateModified: 2021-09-06 17:58:20 +0100 (Mon, September 06, 2021) $"
__version__ = "$Revision: 3.0.4 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

import math
from typing import Union, Tuple, Sequence
from functools import partial
from ccpn.core.NmrResidue import NmrResidue
from ccpn.core.Project import Project
from ccpn.core._implementation.AbstractWrapperObject import AbstractWrapperObject
from ccpn.core._implementation.AbsorbResonance import absorbResonance
from ccpn.core.lib import Pid
from ccpn.core.lib.Util import AtomIdTuple
from ccpnmodel.ccpncore.api.ccp.nmr import Nmr
from ccpnmodel.ccpncore.lib import Constants
from ccpn.util.Common import makeIterableList
from ccpn.util.decorators import logCommand
from ccpn.util.isotopes import isotopeCode2Nucleus, getIsotopeRecords
from ccpn.core.lib.ContextManagers import newObject, undoBlock, renameObjectContextManager, undoStackBlocking
from ccpn.core.lib.ContextManagers import newObject, renameObject, deleteV3Object, \
    undoBlock, undoStackBlocking
from ccpn.util.Logging import getLogger


# ASSIGNEDPEAKSCHANGED = '_assignedPeaksChanged'
UnknownIsotopeCode = '?'


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

    def __init__(self, project: Project, wrappedData):

        # internal lists to hold the current chemicalShifts
        self.chemShifts = []

        super().__init__(project, wrappedData)

    # CCPN properties
    @property
    def _apiResonance(self) -> Nmr.Resonance:
        """ CCPN atom matching Atom"""
        return self._wrappedData

    @property
    def _parent(self) -> NmrResidue:
        """Parent (containing) object."""
        return self._project._data2Obj.get(self._wrappedData.resonanceGroup)

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

    #from ccpn.core.Atom import Atom: This will break the import sequence
    @property
    def atom(self) -> 'Atom':
        """Atom to which NmrAtom is assigned. NB resetting the atom will rename the NmrAtom"""
        return self._project.getAtom(self._id)

    @property
    def isotopeCode(self) -> str:
        """isotopeCode of NmrAtom. Used to facilitate the nmrAtom assignment."""
        value = self._wrappedData.isotopeCode
        if value == self._NONE_VALUE_STRING:
            value = None
        return value

    def _setIsotopeCode(self, value):
        """
        :param value:  value must be defined, if not set then can set to arbitrary value '?'
        this means it can still be set at any isotopeCode later, otherwise
        need to undo or create new nmrAtom

        CCPNINTERNAL: used in _newNmrAtom, Peak.assignDimension
        """
        if not isinstance(value, (str, type(None))):
            raise ValueError('isotopeCode must be of type string (or None); got {}'.format(value))
        if value is not None and value not in getIsotopeRecords().keys():
            raise ValueError('Invalid isotopeCode {}'.format(value))
        self._wrappedData.isotopeCode = value if value else self._NONE_VALUE_STRING

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
        return tuple(data2Obj[x] for x in set(apiPeaks))

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

            # isotopeCode = self.isotopeCode
            # if name and isotopeCode not in (None, '?'):
            #     # Check for isotope match
            #     if name2IsotopeCode(name) not in (isotopeCode, None):
            #         raise ValueError("Cannot reassign %s type NmrAtom to %s" % (isotopeCode, name))  Why? Yes you can!

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
                        # self._wrappedData.name = name or None
                        self.rename(name or None)

                    elif mergeToExisting:
                        result.mergeNmrAtoms(self)

                    else:
                        raise ValueError("New assignment clash with existing assignment,"
                                         " and merging is disallowed")

            else:

                if result is self:
                    if nmrResidue.getNmrAtom(self.name) is None:
                        self._apiResonance.resonanceGroup = nmrResidue._apiResonanceGroup
                        if name != self.name:
                            # self._wrappedData.name = name or None
                            self.rename(name or None)

                    elif name is None or oldNmrResidue.getNmrAtom(name) is None:
                        if name != self.name:
                            # self._wrappedData.name = name or None
                            self.rename(name or None)

                        self._apiResonance.resonanceGroup = nmrResidue._apiResonanceGroup
                    else:
                        # self._wrappedData.name = None  # Necessary to avoid name clashes
                        self.rename(None)
                        self._apiResonance.resonanceGroup = nmrResidue._apiResonanceGroup
                        # self._wrappedData.name = name
                        self.rename(name or None)

                elif mergeToExisting:
                    result.mergeNmrAtoms(self)

                else:
                    raise ValueError("New assignment clash with existing assignment,"
                                     " and merging is disallowed")

        return result

    @logCommand(get='self')
    def mergeNmrAtoms(self, nmrAtoms: Sequence['NmrAtom']):
        nmrAtoms = makeIterableList(nmrAtoms)
        nmrAtoms = [self.project.getByPid(nmrAtom) if isinstance(nmrAtom, str) else nmrAtom for nmrAtom in nmrAtoms]
        if not all(isinstance(nmrAtom, NmrAtom) for nmrAtom in nmrAtoms):
            raise TypeError('nmrAtoms can only contain items of type NmrAtom')
        if self in nmrAtoms:
            raise TypeError('nmrAtom cannot be merged with itself')

        with undoBlock():
            for nmrAtom in nmrAtoms:
                absorbResonance(self, nmrAtom)

                # TODO:ED - update shifts

    @property
    def _oldChemicalShifts(self) -> Tuple:
        """Returns ChemicalShift objects connected to NmrAtom"""
        getDataObj = self._project._data2Obj.get
        return tuple(sorted(getDataObj(x) for x in self._wrappedData.shifts))

    def _getAttribute(self, attrName) -> Tuple:
        """Returns contents of api attribute
        """
        if hasattr(self._wrappedData, attrName):
            return getattr(self._wrappedData, attrName)

        raise TypeError('nmrAtom does not have attribute {}'.format(attrName))

    #=========================================================================================
    # Implementation functions
    #=========================================================================================

    @classmethod
    def _restoreObject(cls, project, apiObj):
        """Subclassed to replace unknown isotopCodes"""
        result = super(NmrAtom, cls)._restoreObject(project=project, apiObj=apiObj)

        # Update Unknown to None
        if result.isotopeCode == UnknownIsotopeCode:
            result._setIsotopeCode(None)

        return result

    @classmethod
    def _getAllWrappedData(cls, parent: NmrResidue) -> list:
        """get wrappedData (ApiResonance) for all NmrAtom children of parent NmrResidue
        """
        return parent._wrappedData.sortedResonances()

    def _setApiName(self, name):
        # set a serial format name of the form ?@<n> from the current serial number
        # functionality provided by the api
        self._wrappedData.name = None

    @renameObject()
    def _makeUniqueName(self) -> str:
        """Generate a unique name in the form @n (e.g. @_123) or @symbol_n (e.g. @H_34)
        :return the generated name
        """
        if self.isotopeCode is not None and (symbol := isotopeCode2Nucleus(self.isotopeCode)) is not None and len(symbol) > 0:
            _name = '@%s_%d' % (symbol[0:1], self._uniqueId)
        else:
            _name = '@_%d' % self._uniqueId
        return _name

    # Sub-class two methods to get '@' names
    @classmethod
    def _defaultName(cls) -> str:
        return '@'

    @classmethod
    def _uniqueName(cls, project, name=None) -> str:
        """Subclassed to get the '@' default name behavior"""
        if name is None:
            id = project._queryNextUniqueIdValue(cls.className)
            name = '%s_%d' %(cls._defaultName(), id)
        return super(NmrAtom, cls)._uniqueName(project=project, name=name)

    @renameObject()
    @logCommand(get='self')
    def rename(self, value: str = None):
        """Rename the NmrAtom, changing its name, Pid, and internal representation.
        """

        # NB This is a VERY special case
        # - API code and notifiers will take care of resetting id and Pid; GWV: not!

        if value == self.name: return

        if value is None:
            value = self._makeUniqueName()
            getLogger().debug('Renaming an %s without a specified value. Name set to the auto-generated option: %s.' %(self, value))

        previous = self._parent.getNmrAtom(value.translate(Pid.remapSeparators))
        if previous is not None:
            raise ValueError('NmrAtom.rename: "%s" conflicts with' % (value, previous))

        # with renameObjectContextManager(self) as addUndoItem:
        isotopeCode = self.isotopeCode
        oldName = self.name
        self._oldPid = self.pid

        # clear the isotopeCode so that the name may be changed (model restriction)
        self._wrappedData.isotopeCode = UnknownIsotopeCode
        self._wrappedData.name = value
        # set isotopeCode to the correct value
        self._wrappedData.isotopeCode = isotopeCode if isotopeCode else UnknownIsotopeCode # self._NONE_VALUE_STRING

        self._childActions.append(self._renameChemicalShifts)
        self._finaliseChildren.extend((sh, 'change') for sh in self.chemShifts)

        return (oldName,)

    def _renameChemicalShifts(self):
        # update chemicalShifts
        for cs in self.chemShifts:
            cs._renameNmrAtom(self)

    def delete(self):
        """Delete self and update the chemicalShift values
        """
        shifts = list(self.chemShifts)

        with undoBlock():
            for sh in shifts:
                sh.nmrAtom = None
            # delete the nmrAtom - notifiers handled by decorator
            self._delete()

    #=========================================================================================
    # CCPN functions
    #=========================================================================================

    def _recalculateShiftValue(self, spectra, simulatedPeakScale: float = 0.0001):
        """Get a new shift value from the assignedPeaks
        """

        apiResonance = self._wrappedData
        sum1 = sum2 = N = 0.0
        peakDims = []
        peaks = set()

        for contrib in apiResonance.peakDimContribs:

            if contrib.isDeleted:
                # Function may be called during PeakDimContrib deletion
                continue

            peakDim = contrib.peakDim
            apiPeak = peakDim.peak

            if apiPeak.isDeleted or peakDim.isDeleted or apiPeak.figOfMerit == 0.0:
                continue

            apiPeakList = apiPeak.peakList
            spectrum = self.project._data2Obj[apiPeakList].spectrum
            if spectrum not in spectra:
                continue

            # NBNB TBD: Old Rasmus comment - peak splittings are not yet handled in V3. TBD add them
            value = peakDim.realValue
            weight = apiPeak.figOfMerit

            if apiPeakList.isSimulated:
                weight *= simulatedPeakScale

            peakDims.append(peakDim)
            peaks.add(apiPeak)

            vw = value * weight
            sum1 += vw
            sum2 += value * vw
            N += weight

        if N > 0.0:
            mean = sum1 / N
            mean2 = sum2 / N
            sigma2 = abs(mean2 - (mean * mean))
            sigma = math.sqrt(sigma2)

        else:
            return None, None

        return mean, sigma

    #=========================================================================================
    # new'Object' and other methods
    # Call appropriate routines in their respective locations
    #=========================================================================================


#=========================================================================================
# Connections to parents:
#=========================================================================================


@newObject(NmrAtom)
def _newNmrAtom(self: NmrResidue, name: str = None, isotopeCode: str = None, comment: str = None, **kwds) -> NmrAtom:
    """Create new NmrAtom within NmrResidue.
    See the NmrAtom class for details

    :param name: string name of the new nmrAtom; If name is None, generate a default name of form
                 e.g. '@_123, @H_211', '@N_45', ...
    :param isotopeCode: optional isotope code
    :param comment: optional string comment
    :return: a new NmrAtom instance.
    """

    apiNmrProject = self._project._wrappedData
    resonanceGroup = self._wrappedData

    if not isinstance(name, (str, type(None))):
        raise TypeError('Name {} must be of type string (or None)'.format(name))

    if name is None or len(name) == 0:
        # generate (temporary) default name, to be changed later after we created the object
        _name = NmrAtom._uniqueName(self.project)

    else:
        # Check for name clashes
        _name = name
        previous = self.getNmrAtom(_name.translate(Pid.remapSeparators))
        if previous is not None:
            raise ValueError('newNmrAtom: name "%s" clashes with %s' % (name, previous))

    # Create the api object
    # Always create first with unknown isotopeCode
    dd = {'resonanceGroup': resonanceGroup, 'isotopeCode': UnknownIsotopeCode, 'name':_name}
    obj = apiNmrProject.newResonance(**dd)

    if (result := self._project._data2Obj.get(obj)) is None:
        raise RuntimeError('Unable to generate new NmrAtom item')

    # Check/set isotopeCode; it has to be set after the creation to avoid API errors.
    result._setIsotopeCode(isotopeCode)

    # adjust the name if it was not supplied; needed to create the nmrAtom first to get an uniqueId, used by rename()
    if name is None:
        with undoStackBlocking():
            result.rename()

    if comment is not None and len(comment) > 0:
        result.comment = comment

    # Set additional optional attributes supplied as kwds arguments
    for key, value in kwds:
        setattr(result, key, value)

    return result


def _fetchNmrAtom(self: NmrResidue, name: str, isotopeCode=None):
    """Fetch NmrAtom with name=name, creating it if necessary

    :param name: string name for new nmrAto if created
    :return: new or existing nmrAtom
    """
    # resonanceGroup = self._wrappedData

    with undoBlock():
        result = (self.getNmrAtom(name.translate(Pid.remapSeparators)) or
                  self.newNmrAtom(name=name, isotopeCode=isotopeCode))

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
