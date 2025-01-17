"""
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (https://www.ccpn.ac.uk) 2014 - 2024"
__credits__ = ("Ed Brooksbank, Joanna Fox, Morgan Hayward, Victoria A Higman, Luca Mureddu",
               "Eliza Płoskoń, Timothy J Ragan, Brian O Smith, Gary S Thompson & Geerten W Vuister")
__licence__ = ("CCPN licence. See https://ccpn.ac.uk/software/licensing/")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, https://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2024-03-21 16:17:11 +0000 (Thu, March 21, 2024) $"
__version__ = "$Revision: 3.2.4 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

import typing
from functools import partial
from ccpnmodel.ccpncore.api.ccp.molecule.MolSystem import Residue as ApiResidue
from ccpn.core.Chain import Chain
from ccpn.core._implementation.AbstractWrapperObject import AbstractWrapperObject
from ccpn.core.lib import Pid
from ccpn.core.lib.ContextManagers import undoStackBlocking, renameObject, undoBlock, \
    undoBlockWithoutSideBar, notificationEchoBlocking
from ccpn.util import Common as commonUtil
from ccpn.util.decorators import logCommand


class Residue(AbstractWrapperObject):
    """A molecular Residue, contained in a Chain, and containing Atoms.
    Crucial attributes: residueType (e.g. 'ALA'), residueVariant (NEF-based), sequenceCode (e.g. '123')
    """

    #: Short class name, for PID.
    shortClassName = 'MR'
    # Attribute it necessary as subclasses must use superclass className
    className = 'Residue'

    _parentClass = Chain

    #: Name of plural link to instances of class
    _pluralLinkName = 'residues'

    # the attribute name used by current
    _currentAttributeName = 'residues'

    #: List of child classes.
    _childClasses = []

    # Qualified name of matching API class
    _apiClassQualifiedName = ApiResidue._metaclass.qualifiedName()

    # Number of fields that comprise the object's pid; Used to get parent id's
    _numberOfIdFields = 2

    #=========================================================================================
    # CCPN properties
    #=========================================================================================

    @property
    def _apiResidue(self) -> ApiResidue:
        """ API residue matching Residue"""
        return self._wrappedData

    @property
    def sequenceCode(self) -> str:
        """Residue sequence code and id (e.g. '1', '127B') """
        obj = self._wrappedData
        objSeqCode = obj.seqCode
        result = (obj.seqInsertCode or '').strip()
        if objSeqCode is not None:
            result = str(objSeqCode) + result
        return result

    @property
    def _key(self) -> str:
        """Residue ID. Identical to sequenceCode.residueType. Characters translated for pid"""
        return Pid.createId(self.sequenceCode, self.residueType)

    @property
    def _localCcpnSortKey(self) -> typing.Tuple:
        """Local sorting key, in context of parent."""
        return (self._wrappedData.seqId,)

    @property
    def _parent(self) -> Chain:
        """Chain containing residue."""
        return self._project._data2Obj[self._wrappedData.chain]

    chain = _parent

    @property
    def residueType(self) -> str:
        """Residue type name string (e.g. 'ALA')"""
        return self._wrappedData.code3Letter or ''

    @property
    def shortName(self) -> str:
        return self._wrappedData.chemCompVar.chemComp.code1Letter or '?'

    @property
    def ccpCode(self) -> str:
        """Residue sequence ccpcode (e.g. 'Ala', 'Aba') retrieved from the ChemComp"""
        obj = self._wrappedData
        ccpCode = obj.ccpCode
        return ccpCode

    @property
    def linking(self) -> str:
        """linking (substitution pattern) code for residue


        Allowed values are:

         For linear polymers: 'start', 'end', 'middle', 'single', 'break', 'cyclic'
         For other molecules: 'nonlinear'

         'cyclic' and 'break' are used at the end of linear polymer stretches to signify,
         respectively, that the polymer is cyclic, or that the residue is bound to an
         unknown residue or to a cap, so that the linear polymer chain does not continue."""

        molType = self._wrappedData.molType
        if molType in ('protein', 'DNA', 'RNA'):
            linkString = self._wrappedData.linking
            if linkString == 'none':
                return 'single'
            elif linkString in ('start', 'end'):
                return linkString
            else:
                # assert linkString == 'middle', ("Illegal API linking value for linear polymer: %s"
                #                                 % linkString)

                nextResidue = self.nextResidue
                previousResidue = self.previousResidue
                if previousResidue is None:
                    if nextResidue is None:
                        return 'single'
                elif nextResidue is None:
                    chainResidues = self.chain.residues
                    if self is chainResidues[-1]:
                        # Last residue in chain
                        return 'middle'
                    else:
                        nextInLine = chainResidues[chainResidues.index(self) + 1]
                        if nextInLine._wrappedData.linking in ('start', 'none'):
                            # Next in chain is start or non-linear
                            return 'middle'
                        altSelf = nextInLine.previousResidue
                        if (altSelf and altSelf._wrappedData.seqId > nextInLine.seqId
                                and altSelf._wrappedData.linking == 'middle'):
                            # Next residue is cyclic (start of)
                            return 'middle'
                        else:
                            return 'break'
                else:

                    # NBNB The detection of 'cyclic' only works if residues are given in
                    # sequential order. This is not given - but is unlikely ever to break.

                    seqId = self._wrappedData.seqId
                    if (previousResidue._wrappedData.seqId > seqId
                            and previousResidue._wrappedData.linking == 'middle'):
                        return 'cyclic'
                    elif (nextResidue._wrappedData.seqId < seqId
                          and nextResidue._wrappedData.linking == 'middle'):
                        return 'cyclic'
                    else:
                        return 'middle'

        elif molType == 'dummy':
            return 'dummy'

        else:
            # All other types have linking 'non-linear' in the wrapper
            return 'single'
        return self._wrappedData.linking

    @linking.setter
    def linking(self, value: str):

        # NBNB TBD FIXME - this will not work as intended when value is 'nonlinear'

        if value in ('break', 'cyclic'):
            value = 'middle'
        elif value == 'single':
            value = 'none'
        self._wrappedData.linking = value

    @property
    def residueVariant(self) -> typing.Optional[str]:
        """NEF convention Residue variant descriptor (protonation state etc.) for residue"""
        atomNamesRemoved, atomNamesAdded = self._wrappedData.getAtomNameDifferences()
        ll = ['-' + x for x in sorted(atomNamesRemoved)]
        ll.extend('+' + x for x in sorted(atomNamesAdded))
        return ','.join(ll) or None

    @property
    def descriptor(self) -> str:
        """variant descriptor (protonation state etc.) for residue, as defined in the CCPN V2 ChemComp
        description."""
        return self._wrappedData.descriptor

    @descriptor.setter
    def descriptor(self, value: str):
        self._wrappedData.descriptor = value

    @property
    def configuration(self) -> typing.Optional[str]:
        """Residue conformation or other non-covalent distinction.

        Example: cis/trans/None for the peptide bonds N-terminal to a residue"""
        return self._wrappedData.configuration

    @configuration.setter
    def configuration(self, value):
        # TODO implement this as a proper enumeration
        allowedValues = ('cis', 'trans', None)
        if value in allowedValues:
            self._wrappedData.configuration = value
        else:
            raise ValueError("%s configuration must be one of %s" % (self, allowedValues))

    #=========================================================================================
    # property STUBS: hot-fixed later
    #=========================================================================================

    @property
    def atoms(self) -> list['Atom']:
        """STUB: hot-fixed later
        :return: a list of atoms in the Residue
        """
        return []

    #=========================================================================================
    # getter STUBS: hot-fixed later
    #=========================================================================================

    def getAtom(self, relativeId: str) -> 'Atom | None':
        """STUB: hot-fixed later
        :return: an instance of Atom, or None
        """
        return None

    #=========================================================================================
    # Core methods
    #=========================================================================================

    @property
    def nextResidue(self) -> typing.Optional['Residue']:
        """Next residue in sequence, if any, otherwise None"""
        apiResidue = self._wrappedData

        molResidue = apiResidue.molResidue.nextMolResidue
        if molResidue is None:
            result = None
            self._project._logger.debug("No next residue - API ")
        else:
            result = self._project._data2Obj.get(
                    apiResidue.chain.findFirstResidue(seqId=molResidue.serial))

        return result

    @property
    def previousResidue(self) -> typing.Optional['Residue']:
        """Previous residue in sequence, if any,otherwise None"""
        apiResidue = self._wrappedData

        molResidue = apiResidue.molResidue.previousMolResidue
        if molResidue is None:
            result = None
        else:
            result = self._project._data2Obj.get(
                    apiResidue.chain.findFirstResidue(seqId=molResidue.serial))

        return result

    def resetVariantToDefault(self):
        """Reset Residue.residueVariant to the default variant"""
        atomNamesMissing, extraAtomNames = self._wrappedData.getAtomNameDifferences()
        # No need for testing - the names returned are guaranteed to be missing/superfluous
        for atomName in atomNamesMissing:
            self.newAtom(name=atomName)
        for atomName in extraAtomNames:
            self.getAtom(atomName).delete()

    @staticmethod
    def _setFragmentResidues(chainFragment, residues):
        """set the residues connected to the chainFragment
        CCPN Internal - ussed to handle removing reside link from the api
        """
        chainFragment.__dict__['residues'] = tuple(residues)

    @logCommand(get='self')
    def delete(self):
        """delete residue.
        Causes an error when just calling residue._wrappedData.delete()
        new method to delete from the chainFragment
        """
        chainFragment = self._wrappedData.chainFragment
        apiResidue = self._wrappedData

        if self.allNmrResidues:
            raise TypeError('Cannot delete residue that has assigned nmrResidues')

        if self._wrappedData in chainFragment.residues:
            with undoBlock():
                oldResidues = list(chainFragment.residues)
                newResidues = list(chainFragment.residues)
                # delRes = newResidues.pop(newResidues.index(apiResidue))
                # delRes.delete()

                newResidues.pop(newResidues.index(apiResidue))
                self._delete()

                # delete the residue from the fragment (no undo items entered into stack)
                chainFragment.__dict__['residues'] = tuple(newResidues)

                # add new undo item to set the residues in the chainFragment
                with undoStackBlocking() as addUndoItem:
                    addUndoItem(undo=partial(self._setFragmentResidues, chainFragment, oldResidues),
                                redo=partial(self._setFragmentResidues, chainFragment, newResidues))

    @property
    def nmrResidue(self) -> typing.Optional['NmrResidue']:
        """NmrResidue to which Residue is assigned

        NB Residue<->NmrResidue link depends solely on the NmrResidue name.
        So no notifiers on the link - notify on the NmrResidue rename instead.
        """
        try:
            return self._project.getNmrResidue(self._id)
        except:
            return None

    @property
    def allNmrResidues(self) -> tuple['NmrResidue']:
        """AllNmrResidues corresponding to Residue - E.g. (for MR:A.87)
        NmrResidues NR:A.87, NR:A.87+0, NR:A.88-1, NR:A.82+5, etc.
        """
        result = []

        nmrChain = self.chain.nmrChain
        if nmrChain is not None:
            nmrResidue = self.nmrResidue
            if nmrResidue is not None:
                result = [nmrResidue]

            for offset in set(x.relativeOffset for x in nmrChain.nmrResidues):
                if offset is not None:
                    residue = self
                    if offset > 0:
                        for ii in range(offset):
                            residue = residue.previousResidue
                            if residue is None:
                                break
                    elif offset < 0:
                        for ii in range(-offset):
                            residue = residue.nextResidue
                            if residue is None:
                                break
                    #
                    if residue is not None:
                        sequenceCode = '%s%+d' % (residue.sequenceCode, offset)
                        ll = [x for x in nmrChain.nmrResidues if x.sequenceCode == sequenceCode]
                        if ll:
                            result.extend(ll)
        return tuple(sorted(result))

    @property
    def hasAssignedAtoms(self) -> bool:
        """
        :return: True if any of its atoms have an assignment
        """
        return any([a.isAssigned for a in self.atoms])

    #=========================================================================================
    # Implementation methods
    #=========================================================================================

    @classmethod
    def _getAllWrappedData(cls, parent: Chain) -> list:
        """get wrappedData (MolSystem.Residues) for all Residue children of parent Chain"""
        # NB this sorts in seqId order - which is the order we want.
        # If the seqId order does not match the sequence we have a problem anyway.
        # NBNB the doe relies on this sorting order to handle position-specific labeling
        # for substances
        return parent._apiChain.sortedResidues()

    @renameObject()
    @logCommand(get='self')
    def rename(self, sequenceCode: str = None):
        """Reset Residue.sequenceCode (residueType is immutable).
        Renaming to None sets the sequence code to the seqId (serial number equivalent)
        """
        # rename functions from here
        apiResidue = self._wrappedData

        if sequenceCode is None:
            seqCode = apiResidue.seqId
            seqInsertCode = ' '

        else:
            # Parse values from sequenceCode
            code, ss, offset = commonUtil.parseSequenceCode(sequenceCode)
            if code is None or offset is not None:
                raise ValueError("Illegal value for Residue.sequenceCode: %s" % sequenceCode)
            seqCode = code
            seqInsertCode = ss or ' '

        previous = apiResidue.chain.findFirstResidue(seqCode=seqCode, seqInsertCode=seqInsertCode)
        if (previous not in (None, apiResidue)):
            raise ValueError("New sequenceCode %s clashes with existing Residue %s"
                             % (sequenceCode, self._project._data2Obj.get(previous)))

        if apiResidue.seqInsertCode and apiResidue.seqInsertCode != ' ':
            oldSequenceCode = '.'.join((str(apiResidue.seqCode), apiResidue.seqInsertCode))
        else:
            oldSequenceCode = str(apiResidue.seqCode)
        # self._oldPid = self.pid

        apiResidue.seqCode = seqCode
        apiResidue.seqInsertCode = seqInsertCode

        return (oldSequenceCode,)

    def _finaliseAction(self, action: str):
        """Subclassed to handle delete/create
        """
        if action == 'delete':
            # store the old hierarchy information - required for deferred notifiers
            self._oldChain = self.chain
            self._oldAtoms = tuple(self.atoms)
        elif action == 'create':
            self._oldChain = None
            self._oldAtoms = ()

        if not super()._finaliseAction(action):
            return

    #===========================================================================================
    # new<Object> and other methods
    # Call appropriate routines in their respective locations
    #===========================================================================================

    @logCommand(get='self')
    def newAtom(self, name: str, elementSymbol: str = None, **kwds) -> 'Atom':
        """Create new Atom within Residue. If elementSymbol is None, it is derived from the name

        See the Atom class for details.

        Optional keyword arguments can be passed in; see Atom._newAtom for details.

        :param name:
        :param elementSymbol:
        :return: a new Atom instance.
        """
        from ccpn.core.Atom import _newAtom

        return _newAtom(self, name=name, elementSymbol=elementSymbol, **kwds)

    def _removeNonChemAtoms(self):
        """
        Delete from project all the pseudo atoms which are not present in the original chemComp and were added artificially.
        """
        chemAtomNames = self._getChemAtomNames()
        pseudoAtoms = [atom for atom in self.atoms if atom.name not in chemAtomNames]
        with undoBlockWithoutSideBar():
            with notificationEchoBlocking():
                self.project.deleteObjects(*pseudoAtoms)

    @property
    def _chemCompVar(self):
        """
        :return:
        """
        return self._wrappedData.chemCompVar

    def _getChemCompAtomGroups(self):
        """
        """
        atomGroups = {}
        if not self._chemCompVar: return
        atomSets = self._chemCompVar.chemAtomSets
        for atomSet in atomSets:
            if not atomSet.chemAtomSets:
                atomGroups[atomSet.name] = [a.name for a in atomSet.chemAtoms]
            else:
                atomGroups[atomSet.name] = [a.name for a in atomSet.chemAtomSets]

        return atomGroups

    def _addAtomsFromChemSets(self):
        if not self._chemCompVar:
            return
        atomSets = self._chemCompVar.chemAtomSets

    def _getChemAtomNames(self):
        """
        :return: gets the atom names from the chemCompVar obj.
        It uses chemCompVar instead of chemCompVar.chemComp.chemAtoms because the latter includes LinkAtom like 'next_1'
        """
        chemCompVar = self._wrappedData.chemCompVar
        chemAtomNames = []
        if chemCompVar:
            chemAtoms = self._wrappedData.chemCompVar.chemAtoms
            chemAtomNames = [atom.name for atom in chemAtoms]
        return chemAtomNames

#=========================================================================================
# Connections to parents:
#=========================================================================================
