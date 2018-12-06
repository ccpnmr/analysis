"""
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================

__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2017"
__credits__ = ("Wayne Boucher, Ed Brooksbank, Rasmus H Fogh, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license",
               "or ccpnmodel.ccpncore.memops.Credits.CcpnLicense for licence text")
__reference__ = ("For publications, please use reference from http://www.ccpn.ac.uk/v3-software/downloads/license",
                 "or ccpnmodel.ccpncore.memops.Credits.CcpNmrReference")

#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: CCPN $"
__dateModified__ = "$dateModified: 2017-07-07 16:32:27 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.b4 $"
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
from typing import Tuple, Optional, Union, Sequence
from ccpn.util.decorators import logCommand
from ccpn.core.lib.ContextManagers import newObject, deleteObject, ccpNmrV3CoreSetter, logCommandBlock
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

    @property
    def compoundName(self) -> str:
        """Short name of chemical compound (e.g. 'Lysozyme') making up Chain"""
        return self._wrappedData.molecule.name

    # GWV: more logical attribute!
    name = compoundName

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

    @property
    def comment(self) -> str:
        """Free-form text comment."""
        return self._wrappedData.details

    @comment.setter
    def comment(self, value: str):
        self._wrappedData.details = value

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
    def clone(self, shortName: str = None):
        """Make copy of chain."""

        apiChain = self._wrappedData
        apiMolSystem = apiChain.molSystem
        dataObj = self._project._data2Obj

        if shortName is None:
            shortName = apiMolSystem.nextChainCode()

        if apiMolSystem.findFirstChain(code=shortName) is not None:
            raise ValueError("Project already has one Chain with shortName %s" % shortName)

        topObjectParameters = {'code': shortName,
                               'pdbOneLetterCode': shortName[0]}
        self._startCommandEchoBlock('clone', shortName, parName='newChain')
        # # Blanking notification ruins sidebar handling of new chain
        # self._project.blankNotification()
        try:
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

        finally:
            # self._project.unblankNotification()
            self._endCommandEchoBlock()
        #
        return result

    def _lock(self):
        """Finalize chain so that it can no longer be modified, and add missing data."""
        self._startCommandEchoBlock('_lock')
        try:
            self._wrappedData.molecule.isFinalised = True
        finally:
            self._endCommandEchoBlock()

    # Implementation functions

    def rename(self, value: str):
        """Rename Chain, changing its shortName and Pid."""
        # from ccpn.util.Common import contains_whitespace
        #
        # if not isinstance(value, str):
        #   raise TypeError("Chain name must be a string")  # ejb catch non-string
        # if not value:
        #   raise ValueError("Chain name must be set")  # ejb catch empty string
        # if Pid.altCharacter in value:
        #   raise ValueError("Character %s not allowed in ccpn.Chain.name" % Pid.altCharacter)
        # if contains_whitespace(value):
        #   raise ValueError("whitespace not allowed in ccpn.Chain.name")

        _validateName('Chain name', value=value, includeWhitespace=True)

        previous = self._project.getChain(value.translate(Pid.remapSeparators))
        if previous not in (None, self):
            raise ValueError("%s already exists" % previous.longPid)

        # if value:
        #   previous = self._project.getChain(value.translate(Pid.remapSeparators))
        #   if previous not in (None, self):
        #     raise ValueError("%s already exists" % previous.longPid)
        # else:
        #   raise ValueError("Chain name must be set")

        self._startCommandEchoBlock('rename', value)
        try:
            self._apiChain.renameChain(value)
            self._finaliseAction('rename')
            self._finaliseAction('change')
        finally:
            self._endCommandEchoBlock()

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
        self._startCommandEchoBlock('renumberResidues', offset,
                                    values={'start': start, 'stop': stop})
        try:
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

        finally:
            self._endCommandEchoBlock()
            for residue in changedResidues:
                residue._finaliseAction('rename')
                residue._finaliseAction('change')

        if start is not None and stop is not None:
            if len(changedResidues) != stop + 1 - start:
                self._project._logger.warning("Only %s residues found in range %s tos %s"
                                              % (len(changedResidues), start, stop))

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


#=========================================================================================

def _validateName(attrib: str, value: str, includeWhitespace: bool = False):
    from ccpn.util.Common import contains_whitespace

    if not isinstance(value, str):
        raise TypeError("%s must be a string" % attrib)  # ejb catch non-string
    if not value:
        raise ValueError("%s must be set" % attrib)  # ejb catch empty string
    if Pid.altCharacter in value:
        raise ValueError("Character %s not allowed in %s" % (Pid.altCharacter, attrib))
    if includeWhitespace and contains_whitespace(value):
        raise ValueError("whitespace not allowed in %s" % attrib)

    # will only get here if all the tests pass
    return True


@newObject(Chain)
def _createChain(self: Project, sequence: Union[str, Sequence[str]], compoundName: str = None,
                 startNumber: int = 1, molType: str = None, isCyclic: bool = False,
                 shortName: str = None, role: str = None, comment: str = None,
                 serial: int = None) -> Chain:
    """Create new chain from sequence of residue codes, using default variants.

    Automatically creates the corresponding polymer Substance if the compoundName is not already taken

    See the Chain class for details.

    :param Sequence sequence: string of one-letter codes or sequence of residue types
    :param str compoundName: name of new Substance (e.g. 'Lysozyme') Defaults to 'Molecule_n
    :param str molType: molType ('protein','DNA', 'RNA'). Needed only if sequence is a string.
    :param int startNumber: number of first residue in sequence
    :param str shortName: shortName for new chain (optional)
    :param str role: role for new chain (optional)
    :param str comment: comment for new chain (optional)
    :param serial: optional serial number.
    :return: a new Chain instance.
    """

    apiMolSystem = self._wrappedData.molSystem
    if not shortName:
        shortName = apiMolSystem.nextChainCode()
    else:
        _validateName('shortName', value=shortName, includeWhitespace=False)  # ejb - test the name

    previous = self._project.getChain(shortName.translate(Pid.remapSeparators))
    if previous is not None:
        raise ValueError("%s already exists" % previous.longPid)

    apiRefComponentStore = self._apiNmrProject.sampleStore.refSampleComponentStore
    if compoundName is None:
        name = self._uniqueSubstanceName()
    elif apiRefComponentStore.findFirstComponent(name=compoundName) is None:
        _validateName('compoundName', value=compoundName, includeWhitespace=False)  # ejb - test the name

        name = compoundName
    else:
        raise ValueError(
                "Substance named %s already exists. Try Substance.createChain function instead?"
                % compoundName)

    substance = self.createPolymerSubstance(sequence=sequence, name=name,
                                            startNumber=startNumber, molType=molType,
                                            isCyclic=isCyclic, comment=comment)

    apiMolecule = substance._apiSubstance.molecule
    apiMolecule.isFinalised = True
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
