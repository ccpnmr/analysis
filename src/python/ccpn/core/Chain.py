"""
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2019"
__credits__ = ("Ed Brooksbank, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: CCPN $"
__dateModified__ = "$dateModified: 2017-07-07 16:32:27 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.b5 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

import collections
import typing
from functools import partial
from ccpn.util import Common as commonUtil
from ccpn.core._implementation.AbstractWrapperObject import AbstractWrapperObject
from ccpn.core.Project import Project
from ccpn.core.Substance import Substance
from ccpn.core.Substance import SampleComponent
from ccpnmodel.ccpncore.lib.CopyData import copySubTree
from ccpnmodel.ccpncore.api.ccp.molecule.MolSystem import Chain as ApiChain
from ccpnmodel.ccpncore.api.ccp.molecule import Molecule
from ccpnmodel.ccpncore.api.ccp.lims import Sample
from ccpn.core.lib import Pid
from typing import Tuple, Optional, Union, Sequence, Iterable
from ccpn.util.decorators import logCommand
from ccpn.core.lib.ContextManagers import newObject, deleteObject, ccpNmrV3CoreSetter, \
    renameObject, undoBlock, undoStackBlocking
from ccpn.util.Logging import getLogger


class Chain(AbstractWrapperObject):
    """A molecular Chain, containing one or more Residues."""

    #: Short class name, for PID.
    shortClassName = 'MC'
    # Attribute it necessary as subclasses must use superclass className
    className = 'Chain'

    _parentClass = Project

    #: Name of plural link to instances of class
    _pluralLinkName = 'chains'

    # the attribute name used by current
    _currentAttributeName = 'chains'

    #: List of child classes.
    _childClasses = []

    # Qualified name of matching API class
    _apiClassQualifiedName = ApiChain._metaclass.qualifiedName()

    # CCPN properties
    @property
    def _apiChain(self) -> ApiChain:
        """ CCPN chain matching Chain"""
        return self._wrappedData

    @property
    def _key(self) -> str:
        """short form of name, corrected to use for id"""
        return self._wrappedData.code.translate(Pid.remapSeparators)

    @property
    def shortName(self) -> str:
        """short form of name"""
        return self._wrappedData.code

    @shortName.setter
    def shortName(self, value: str):
        self.rename(value)

    # GWV: more logical attribute!
    name = shortName

    @property
    def compoundName(self) -> str:
        """Short name of chemical compound (e.g. 'Lysozyme') making up Chain"""
        return self._wrappedData.molecule.name

    # Api does not allow setting of compoundName
    # @compoundName.setter
    # def compoundName(self, value: str):
    #     self._wrappedData.molecule.name = value
    #
    @property
    def _parent(self) -> Project:
        """Parent (containing) object."""
        return self._project

    @property
    def role(self) -> str:
        """The role of the chain in a molecular complex or sample - free text. Could be 'free',
        ''bound', 'open', 'closed', 'minor form B', ..."""
        return self._wrappedData.role

    @role.setter
    def role(self, value: str):
        self._wrappedData.role = value

    @property
    def isCyclic(self) -> bool:
        """True if this is a cyclic polymer."""
        return self._wrappedData.molecule.isStdCyclic

    # @property
    # def comment(self) -> str:
    #     """Free-form text comment"""
    #     return self._none2str(self._wrappedData.details)
    #
    # @comment.setter
    # def comment(self, value: str):
    #     self._wrappedData.details = self._str2none(value)

    @property
    def substances(self) -> Tuple[Substance, ...]:
        """Substances matching to Chain (based on chain.compoundName)"""
        compoundName = self.compoundName
        return tuple(x for x in self.project.substances if x.name == compoundName)

    @property
    def sampleComponents(self) -> Tuple[SampleComponent, ...]:
        """SampleComponents matching to Chain (based on chain.compoundName)"""
        compoundName = self.compoundName
        return tuple(x for x in self.project.sampleComponents if x.name == compoundName)

    @property
    def nmrChain(self) -> typing.Optional['NmrChain']:
        "NmrChain to which Chain is assigned"
        try:
            return self._project.getNmrChain(self._id)
        except:
            return None

    # GWV 20181122: removed setters between Chain/NmrChain, Residue/NmrResidue, Atom/NmrAtom
    # @property.setter
    # def nmrChain(self, value: 'NmrChain'):
    #   if value is None:
    #     raise ValueError("nmrChain cannot be set to None")
    #   else:
    #     value.chain = self

    # CCPN functions
    @logCommand(get='self', prefix='newChain=')
    def clone(self, shortName: str = None):
        """Make copy of chain."""

        apiChain = self._wrappedData
        apiMolSystem = apiChain.molSystem
        dataObj = self._project._data2Obj

        if shortName is None:
            shortName = apiMolSystem.nextChainCode()

        if apiMolSystem.findFirstChain(code=shortName) is not None:
            raise ValueError("Project already has one Chain with shortName %s" % shortName)

        topObjectParameters = {'code'            : shortName,
                               'pdbOneLetterCode': shortName[0]}

        # with logCommandBlock(prefix='newChain=', get='self') as log:
        #     log('clone')

        with undoBlock():
            newApiChain = copySubTree(apiChain, apiMolSystem, maySkipCrosslinks=True,
                                      topObjectParameters=topObjectParameters)
            result = self._project._data2Obj.get(newApiChain)

            # Add intra-chain generic bonds
            for apiGenericBond in apiMolSystem.genericBonds:
                ll = []
                for aa in apiGenericBond.atoms:
                    if aa.residue.chain is apiChain:
                        ll.append(dataObj[aa])
                if len(ll) == 2:
                    relativeIds = list(x._id.split(Pid.IDSEP, 1)[1] for x in ll)
                    newAtoms = list(result.getAtom(x) for x in relativeIds)
                    newAtoms[0].addInterAtomBond(newAtoms[1])

        return result

    def _lock(self):
        """Finalise chain so that it can no longer be modified, and add missing data."""
        with undoBlock():
            self._wrappedData.molecule.isFinalised = True

    @logCommand(get='self')
    def renumberResidues(self, offset: int, start: int = None,
                         stop: int = None):
        """Renumber residues in range start-stop (inclusive) by adding offset

        The residue number is the integer starting part of the sequenceCode,
        e.g. residue '12B' is renumbered to '13B' (offset=1)

        if start (stop) is None, there is no lower (upper) limit

        NB Will rename residues one by one, and stop on error."""

        # Must be here to avoid circular imports
        from ccpn.core.lib import MoleculeLib

        residues = self.residues
        if offset > 0:
            residues.reverse()

        changedResidues = []

        with undoBlock():
            for residue in residues:
                sequenceCode = residue.sequenceCode
                code, ss, unused = commonUtil.parseSequenceCode(sequenceCode)
                # assert unused is None
                if code is not None:
                    if ((start is None or code >= start)
                            and (stop is None or code <= stop)):
                        newSequenceCode = MoleculeLib._incrementedSequenceCode(residue.sequenceCode, offset)
                        residue.rename(newSequenceCode)
                        changedResidues.append(residue)

            for residue in changedResidues:
                residue._finaliseAction('rename')

        if start is not None and stop is not None:
            if len(changedResidues) != stop + 1 - start:
                getLogger().warning("Only %s residues found in range %s tos %s" % (len(changedResidues), start, stop))

    @property
    def sequence(self):
        """
        :return: the full sequence as a single string of one letter codes
        """
        sequence = ''
        for residue in self.residues:
            if residue is not None:
                c = residue.shortName
                if c:
                    sequence += c
        return sequence

    @property
    def hasAssignedAtoms(self) -> bool:
        """
        :return: True if any of its atoms have an assignment
        """
        return any([a.isAssigned for a in self.atoms])

    def _toNmrChain(self):
        ''' Makes an Nmr Chain from the chain '''
        try:
            nmrChain = self.project.newNmrChain(isConnected=True)
            for residue in self.residues:
                nmrResidue = nmrChain.newNmrResidue(sequenceCode=residue.sequenceCode, residueType=residue.residueType)
                atomNames = [atom.name for atom in residue.atoms]
                for atomName in atomNames:
                    if atomName:
                        nmrResidue.newNmrAtom(atomName)
        except Exception as e:
            self.project._logger.warning("Error in creating an NmrChain from Chain: %s"
                                         % e)

    #=========================================================================================
    # Implementation functions
    #=========================================================================================

    @classmethod
    def _getAllWrappedData(cls, parent: Project) -> list:
        """get wrappedData (MolSystem.Chains) for all Chain children of parent NmrProject.molSystem"""
        molSystem = parent._wrappedData.molSystem
        if molSystem is None:
            return []
        else:
            return molSystem.sortedChains()

    @logCommand(get='self')
    def rename(self, value: str):
        """Rename Chain, changing its shortName and Pid.
        """
        self._validateName(value=value, allowWhitespace=False)

        with renameObject(self) as addUndoItem:
            oldName = self.shortName
            self._apiChain.renameChain(value)

            addUndoItem(undo=partial(self.rename, oldName),
                        redo=partial(self.rename, value))

#=========================================================================================

@newObject(Chain)
def _newApiChain(self: Project, apiMolecule, shortName, role, comment):
    apiMolSystem = self._wrappedData.molSystem
    apiMolecule.isFinalised = True
    newApiChain = apiMolSystem.newChain(molecule=apiMolecule, code=shortName, role=role,
                                        details=comment)


    result = self._project._data2Obj[newApiChain]

    return result

# @newObject(Chain)
@undoBlock()
def _createChain(self: Project, sequence: Union[str, Sequence[str]], compoundName: str = None,
                 startNumber: int = 1, molType: str = None, isCyclic: bool = False,
                 shortName: str = None, role: str = None, comment: str = None,
                 serial: int = None) -> Chain:
    """Create new chain from sequence of residue codes, using default variants.

    Automatically creates the corresponding polymer Substance if the compoundName is not already taken

    See the Chain class for details.

    :param Sequence sequence: string of one-letter codes or sequence of residue types
                                E.g. 'HMRQPPLVT' or ('HMRQPPLVT',) 
                                or ('ala', 'ala', 'ala')
    :param str compoundName: name of new Substance (e.g. 'Lysozyme') Defaults to 'Molecule_n
    :param str molType: molType ('protein','DNA', 'RNA'). Needed only if sequence is a string.
    :param int startNumber: number of first residue in sequence
    :param str shortName: shortName for new chain (optional)
    :param str role: role for new chain (optional)
    :param str comment: comment for new chain (optional)
    :param serial: optional serial number.
    :return: a new Chain instance.
    """

    # check sequence is valid first
    # either string, or list/tuple of strings
    # list must all be 3 chars long if more than 1 element in list
    if not sequence:
        raise TypeError('sequence must be defined')

    if isinstance(sequence, str):

        # alpha string
        if not sequence.isalpha():
            raise TypeError('sequence contains bad characters: %s' % str(sequence))

        sequence = sequence.upper()

    elif isinstance(sequence, Iterable):

        # iterable
        if len(sequence) == 1:

            # single element in a list
            sequence = sequence[0]
            if not isinstance(sequence, str):
                raise TypeError('sequence is not a valid string: %s' % str(sequence))
            elif not sequence.isalpha():
                raise TypeError('sequence contains bad characters: %s' % str(sequence))

            sequence = sequence.upper()

        elif len(sequence) > 1:
            # iterate through all elements
            newSeq = []
            for s in sequence:

                if not isinstance(s, str):
                    raise TypeError('sequence element is not a valid string: %s' % str(s))
                elif len(s) != 3:
                    raise TypeError('sequence elements must be 3 characters: %s' % str(s))
                elif not s.isalpha():
                    raise TypeError('sequence element contains bad characters: %s' % str(s))

                newSeq.append(s.upper())
            sequence = tuple(newSeq)

        else:
            raise TypeError('sequence is not a valid string: %s' % str(sequence))
    else:
        raise TypeError('sequence is not a valid string: %s' % str(sequence))

    apiMolSystem = self._wrappedData.molSystem
    if not shortName:
        shortName = apiMolSystem.nextChainCode()
    else:
        self._validateName(value=shortName, allowWhitespace=False)

    previous = self._project.getChain(shortName.translate(Pid.remapSeparators))
    if previous is not None:
        raise ValueError("'%s' already exists" % previous.longPid)

    apiRefComponentStore = self._apiNmrProject.sampleStore.refSampleComponentStore
    if compoundName is None:
        name = self._uniqueSubstanceName()
    elif apiRefComponentStore.findFirstComponent(name=compoundName) is None:
        self._validateName(value=compoundName, allowWhitespace=False)

        name = compoundName
    else:
        raise ValueError(
                "Substance '%s' already exists. Try Substance.createChain function instead?"
                % compoundName)

    substance = self.createPolymerSubstance(sequence=sequence, name=name,
                                            startNumber=startNumber, molType=molType,
                                            isCyclic=isCyclic, comment=comment)

    apiMolecule = substance._apiSubstance.molecule

    try:
        result = _newApiChain(self, apiMolecule, shortName, role, comment)

    except Exception as es:
        if substance:
            # clean up and remove the created substance
            substance.delete()
        raise RuntimeError('Unable to generate new Chain item')

    if serial is not None:
        try:
            result.resetSerial(serial)
        except ValueError:
            getLogger().warning("Could not reset serial of %s to %s - keeping original value"
                                % (result, serial))

    for residue in result.residues:
        # Necessary as CCPN V2 default protonation states do not match tne NEF / V3 standard
        residue.resetVariantToDefault()

    return result


#EJB 20181206; moved to Project
# Project.createChain = _createChain
# del _createChain


@newObject(Chain)
def _createChainFromSubstance(self: Substance, shortName: str = None, role: str = None,
                              comment: str = None, serial: int = None) -> Chain:
    """Create new Chain that matches Substance

    :param shortName:
    :param role:
    :param comment: optional comment string
    :param serial: optional serial number.
    :return: a new Chain instance.
    """

    if self.substanceType != 'Molecule':
        raise ValueError("Only Molecule Substances can be used to create chains")

    apiMolecule = self._apiSubstance.molecule
    if apiMolecule is None:
        raise ValueError("API MolComponent must have attached ApiMolecule in order to create chains")

    apiMolSystem = self._project._apiNmrProject.molSystem
    if shortName is None:
        shortName = apiMolSystem.nextChainCode()

    previous = self._project.getChain(shortName.translate(Pid.remapSeparators))
    if previous is not None:
        raise ValueError("%s already exists" % previous.longPid)

    newApiChain = apiMolSystem.newChain(molecule=apiMolecule, code=shortName, role=role,
                                        details=comment)

    result = self._project._data2Obj[newApiChain]
    if result is None:
        raise RuntimeError('Unable to generate new Chain item')

    if serial is not None:
        try:
            result.resetSerial(serial)
        except ValueError:
            getLogger().warning("Could not reset serial of %s to %s - keeping original value"
                                % (result, serial))

    for residue in result.residues:
        # Necessary as CCPN V2 default protonation states do not match the NEF / V3 standard
        residue.resetVariantToDefault()

    return result


#EJB 20181206: moved to Substance
# Substance.createChain = _createChainFromSubstance
# del _createChainFromSubstance


def getter(self: Substance) -> Tuple[Chain, ...]:
    name = self.name
    return tuple(x for x in self._project.chains if x.compoundName == name)


Substance.chains = property(getter, None, None,
                            "ccpn.Chains that correspond to ccpn.Substance (if defined)"
                            )


def getter(self: SampleComponent) -> Tuple[Chain, ...]:
    name = self.name
    return tuple(x for x in self._project.chains if x.compoundName == name)


SampleComponent.chains = property(getter, None, None,
                                  "ccpn.Chains that correspond to ccpn.SampleComponent (if defined)"
                                  )

del getter

# Clean-up

Chain.clone.__annotations__['return'] = Chain

# Connections to parents:
# No 'new' function - chains are made elsewhere


# Notifiers:
# Crosslinks: substance
className = Molecule.Molecule._metaclass.qualifiedName()
Project._apiNotifiers.extend(
        (('_modifiedLink', {'classNames': ('Chain', 'Substance')}, className, 'create'),
         ('_modifiedLink', {'classNames': ('Chain', 'Substance')}, className, 'delete'),
         )
        )
# Crosslinks: sampleComponent
className = Sample.SampleComponent._metaclass.qualifiedName()
Project._apiNotifiers.extend(
        (('_modifiedLink', {'classNames': ('Chain', 'SampleComponent')}, className, 'addChainCode'),
         ('_modifiedLink', {'classNames': ('Chain', 'SampleComponent')}, className, 'removeChainCode'),
         ('_modifiedLink', {'classNames': ('Chain', 'SampleComponent')}, className, 'setChainCodes'),
         )
        )
