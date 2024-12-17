"""
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (https://www.ccpn.ac.uk) 2014 - 2024"
__credits__ = ("Ed Brooksbank, Morgan Hayward, Victoria A Higman, Luca Mureddu, Eliza Płoskoń",
               "Timothy J Ragan, Brian O Smith, Daniel Thompson",
               "Gary S Thompson & Geerten W Vuister")
__licence__ = ("CCPN licence. See https://ccpn.ac.uk/software/licensing/")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, https://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Geerten Vuister $"
__dateModified__ = "$dateModified: 2024-12-17 22:37:21 +0000 (Tue, December 17, 2024) $"
__version__ = "$Revision: 3.3.0.develop $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from typing import Tuple, Optional, Union, Sequence, List
import numpy as np

from ccpn.core._implementation.AbstractWrapperObject import AbstractWrapperObject
from ccpn.core._implementation._MolecularTemplate import _MolecularTemplate, _newMolecularTemplate
from ccpn.core.Project import Project
from ccpn.core.Substance import Substance, SampleComponent

from ccpn.core.lib.ContextManagers import newObject, renameObject, undoBlock, inactivity, undoStack, newObjectList
from ccpn.core.lib import Pid
from ccpn.core.lib.forceAttribute import forceSetattr, forceGetattr
from ccpn.core.lib.ChainLib import SequenceHandler, CCPCODE, ISVALID, ERRORS

from ccpn.util import Common as commonUtil
from ccpn.util.decorators import logCommand
from ccpn.util.Logging import getLogger

from ccpn.ui.gui.guiSettings import _styleRed

from ccpnmodel.ccpncore.lib.CopyData import copySubTree
from ccpnmodel.ccpncore.api.ccp.molecule.MolSystem import Chain as ApiChain
from ccpnmodel.ccpncore.api.ccp.molecule import Molecule
from ccpnmodel.ccpncore.lib.molecule.MoleculeModify import createMolecule
from ccpnmodel.ccpncore.api.ccp.lims import Sample


NotFound = 'NotFound'  # used to create missing residues


class Chain(AbstractWrapperObject):
    """A molecular Chain, containing one or more Residues
    """
    #-----------------------------------------------------------------------------------------
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

    _ignoreNewApiObjectCallback = True

    #-----------------------------------------------------------------------------------------
    # CCPN properties
    #-----------------------------------------------------------------------------------------

    @property
    def _apiChain(self) -> ApiChain:
        """ CCPN chain matching Chain"""
        return self._wrappedData

    @property
    def _key(self) -> str:
        """short form of name, corrected to use for id"""
        return self._wrappedData.code.translate(Pid.remapSeparators)

    @property
    def name(self) -> str:
        """Name of the chain"""
        return self._wrappedData.code

    @name.setter
    def name(self, value: str):
        self.rename(value)

    # GWV: 15/12/24; backward compatibility
    shortName =name

    @renameObject(blockSidebar=True)
    @logCommand(get='self')
    def rename(self, value: str):
        """Rename Chain, changing its name and pid.
        """
        if (_molecularTemplate := self._molecularTemplate) is None:
            raise RuntimeError(f'Unable to get associated _MolecularTemplate instance')

        if self.nmrChain:
            getLogger().warning(f'{self.__class__.__name__}.rename will lose or change the assigned nmrChain')

        newName = self._uniqueName(parent=self.project, name=value)

        # rename functions from here; renameDecorator will handle undo-ing and notifier blanking
        # and subsequent firing
        oldName = self.name
        # do not use self.name = newName, as this causes infinite recursion!
        # _apiRename will do all API admin
        self._apiRename(newName)
        self._resetIds(recursive=True)
        # rename the associated _MolecularTemplate instance
        _molecularTemplate.rename(newName)

        return (oldName, newName)

    @property
    def compoundName(self) -> str:
        """Name of chemical compound (e.g. 'Lysozyme') making up Chain
        """
        #TODO-DEVEL: change this to refer to substance (if defined)
        if (_molecularTemplate := self._molecularTemplate) is None:
            raise RuntimeError(f'Unable to get associated _MolecularTemplate instance')
        return _molecularTemplate.name

    @property
    def _parent(self) -> Project:
        """Parent (containing) object."""
        return self._project

    @property
    def role(self) -> str:
        """The role of the chain in a molecular complex or sample - free text.
        Examples: 'free', 'bound', 'open', 'closed', 'minor form B', ...
        """
        return self._wrappedData.role

    @role.setter
    def role(self, value: str):
        self._wrappedData.role = value

    @property
    def isCyclic(self) -> bool:
        """True if this is a cyclic polymer.
        """
        if (_molecularTemplate := self._molecularTemplate) is None:
            raise RuntimeError(f'Unable to get associated _MolecularTemplate instance')
        return _molecularTemplate.isCyclic

    @property
    def substances(self) -> list:
        """:return a list of Substances matching to Chain (based on chain.compoundName)
        """
        compoundName = self.compoundName
        return [x for x in self.project.substances if x.name == compoundName]

    @property
    def substance(self) -> Substance | None:
        """:return: the first of the substances, generally the only one or None
        """
        result = self.substances
        if result:
            return result[0]
        else:
            return None

    @property
    def sampleComponents(self) -> Tuple[SampleComponent, ...]:
        """SampleComponents matching to Chain (based on chain.compoundName)
        """
        compoundName = self.compoundName
        return tuple(x for x in self.project.sampleComponents if x.name == compoundName)

    @property
    def nmrChain(self) -> Optional['NmrChain']:
        """NmrChain to which Chain is (optionally) assigned"""
        try:
            return self.project.getNmrChain(self.id)
        except Exception as es:
            getLogger().debug(_styleRed(f'Getting NmrChain yielded error: {es}'))
            return None

    # GWV 20181122: removed setters between Chain/NmrChain, Residue/NmrResidue, Atom/NmrAtom
    # @property.setter
    # def nmrChain(self, value: 'NmrChain'):
    #   if value is None:
    #     raise ValueError("nmrChain cannot be set to None")
    #   else:
    #     value.chain = self

    #-----------------------------------------------------------------------------------------
    # property (STUBS: hot-fixed later)
    #-----------------------------------------------------------------------------------------

    @property
    def _molecularTemplate(self) -> Optional['_MolecularTemplate']:
        """:return The _MolecularTemplate instance associated with self
        or None (if not present).
        """
        # local import to avoid cycles
        from ccpn.core._implementation._MolecularTemplate import _MolecularTemplate
        _pid = Pid.createPid(_MolecularTemplate.shortClassName, self.name)
        return self.project.getByPid(_pid)

    @property
    def atoms(self) -> list['Atom']:
        """STUB: hot-fixed later
        :return: a list of atoms in the Chain
        """
        return []

    @property
    def residues(self) -> list['Residue']:
        """STUB: hot-fixed later
        :return: a list of residues in the Chain
        """
        return []

    #-----------------------------------------------------------------------------------------
    # getter STUBS: hot-fixed later
    #-----------------------------------------------------------------------------------------

    def getAtom(self, relativeId: str) -> 'Atom | None':
        """STUB: hot-fixed later
        :return: an instance of Atom, or None
        """
        return None

    def getResidue(self, relativeId: str) -> 'Residue | None':
        """STUB: hot-fixed later
        :return: an instance of Residue, or None
        """
        return None

    #-----------------------------------------------------------------------------------------
    # methods
    #-----------------------------------------------------------------------------------------

    @logCommand(get='self', prefix='newChain=')
    def clone(self, newName: str = None, useNefAtomNomenclature: bool = True):
        """Make clone (copy) of chain.
        :param newName: the new name for the cloned chain
        :param useNefAtomNomenclature: Flag to use NefAtomNomenclature (defaults to True)
        :return a Chain instance
        """
        return _cloneChain(self, newName=newName, useNefAtomNomenclature=useNefAtomNomenclature)

    def delete(self):
        """Delete self
        """
        _template = self._molecularTemplate
        with undoBlock():
            super().delete()
            _template.delete()

    def _lock(self):
        """Finalise chain so that it can no longer be modified, and add missing data."""
        if (_molecularTemplate := self._molecularTemplate) is None:
            raise RuntimeError(f'Unable to get associated _MolecularTemplate instance')
        with undoBlock():
            _molecularTemplate.lock()

    @logCommand(get='self')
    def renumberResidues(self, offset: int, start: int = None, stop: int = None) -> list['Residue']:
        """Renumber sequenceCode of the residues in range start-stop (inclusive)
        by adding offset.
        NB Will rename residues one by one, and stop on error.

        :param offset: offset to add to the integer part of the sequenceCode.
        :param start: start index of residues to renumber.
                      The start index is the integer starting part of the
                      sequenceCode, e.g. for residue '12B' it is 12.
                      If start is None, there is no lower limit
        :param stop: stop index of residues to renumber.
                     The stop index is the integer as  defined above for the
                     start.
                     If stop is None, there is no upper limit
        :return The list of renumbered residues
        """

        # Must be here to avoid circular imports
        from ccpn.core.lib import MoleculeLib

        residues = self.residues
        if offset > 0:
            residues.reverse()

        changedResidues = []
        with undoBlock():
            for residue in residues:
                _intCode = residue._sequenceCodeAsInteger
                if (    (start is None or _intCode >= start)
                    and (stop is None or _intCode <= stop)
                ):
                    residue.renumber(offset=offset)
                    changedResidues.append(residue)

        #     sequenceCode = residue.sequenceCode
            #     code, ss, unused = commonUtil.parseSequenceCode(sequenceCode)
            #     # assert unused is None
            #     if code is not None:
            #         if ((start is None or code >= start)
            #                 and (stop is None or code <= stop)):
            #             newSequenceCode = MoleculeLib._incrementedSequenceCode(residue.sequenceCode, offset)
            #             residue.rename(newSequenceCode)
            #             changedResidues.append(residue)
            #
            # for residue in changedResidues:
            #     residue._finaliseAction('rename')

        getLogger().info(f"Renumbered {len(changedResidues)} out of {len(residues)} possible residues")
        if offset > 0:
            changedResidues.reverse()

        return changedResidues

    @property
    def sequence(self) -> str:
        """
        :return: the full sequence as a single string of one-letter codes
        """
        sequence = [residue.oneLetterCode for residue in self.residues
                    if residue and residue.oneLetterCode
                    ]
        return ''.join(sequence)

    @property
    def sequenceCcpCodes(self) -> list:
        """
        :return: A list of  CcpCodes used to build the sequence
        """
        ccpCodes = [residue.ccpCode for residue in self.residues]
        return ccpCodes

    @property
    def startNumber(self):
        """
        :return:  int. The first SequenceCode
        """
        codes = self._sequenceCodesAsIntegers
        first = codes[0] if len(codes) > 0 else 1
        return first

    @property
    def _sequenceCodesAsIntegers(self):
        """
        :return: list of sequence codes as integers. If a code cannot be interpreted as int
        it uses nan (float). This is to keep the same length as the residues and to allow
        numerical operations such as min, max or proper sorting.
        """
        _intCodes = []
        for r in self.residues:
            _code = r._sequenceCodeAsInteger
            if isinstance(_code, int):
                _intCodes.append(_code)
            else:
                _intCodes.append(np.nan)
                getLogger().debug3(f'Cannot convert {r.sequenceCode} to integer.')
        return _intCodes

    @property
    def hasAssignedAtoms(self) -> bool:
        """
        :return: True if any of its atoms have an assignment
        """
        return any(a.isAssigned for a in self.atoms)

    @logCommand(get='self')
    def toNmrChain(self, nmrChainName=None, ):
        """ Makes a new NmrChain from its residues/atoms.

        :param nmrChainName: str. Default None to use the same name as the chain. If the name is already taken, it creates a sequential code.
        :return the newly created nmrChain object

        """
        try:
            from ccpn.util.isotopes import DEFAULT_ISOTOPE_DICT
            from ccpn.core.lib.ContextManagers import undoBlockWithoutSideBar
            from ccpn.core.NmrChain import NmrChain

            name = nmrChainName
            if name is not None:
                name = self.name
                if self.project.getByPid(f'{NmrChain.shortClassName}:{name}'):
                    getLogger().warn(f'NmrChain name {name} is already existing.')
                    name = NmrChain._uniqueName(parent=self.project, name=name)

            with undoBlockWithoutSideBar():
                nmrChain = self.project.newNmrChain(
                        shortName=name, )  #  isConnected=True is not possible with a name different from #  (API errors)!
                for residue in self.residues:
                    nmrResidue = nmrChain.newNmrResidue(sequenceCode=residue.sequenceCode,
                                                        residueType=residue.residueType)
                    for atom in residue.atoms:
                        if atom.name:
                            isotopeCode = DEFAULT_ISOTOPE_DICT.get(atom.elementSymbol)
                            nmrResidue.newNmrAtom(atom.name, isotopeCode=isotopeCode)
            return nmrChain

        except Exception as e:
            getLogger().warning(f"Error in creating an NmrChain from Chain: {e}")

    @property
    def moleculeType(self):
        if (_molecularTemplate := self._molecularTemplate) is None:
            raise RuntimeError(f'Unable to get associated _MolecularTemplate instance')
        return _molecularTemplate.moleculeType

    # GWV 15/12/24 backward compatibility
    chainType = moleculeType

    #-----------------------------------------------------------------------------------------
    # Implementation functions
    #-----------------------------------------------------------------------------------------

    # For debugging purposes
    def __init__(self, project: 'Project', wrappedData):
        super().__init__(project, wrappedData)

    @classmethod
    def _getAllWrappedData(cls, parent: Project) -> list:
        """get wrappedData (MolSystem.Chains) for all Chain children of parent NmrProject.molSystem"""
        molSystem = parent._wrappedData.molSystem
        return [] if molSystem is None else molSystem.sortedChains()

    def _apiRename(self: 'Chain', newCode: str):
        """Rename chain in place, fixing all stored references to the chainCode
        Adapted from API renameChain in _ccp.molecule.MolSystem.Chain
        """
        apiChain = self._apiChain
        molSystem = apiChain.molSystem
        oldCode = apiChain.code

        if molSystem.findFirstChain(code=newCode) is not None:
            raise ValueError(f"Cannot rename API Chain %s, name {newCode} already exists")

        with self._apiOverride():
            # Fix apiChain
            apiChain.code = newCode
            parentDict = forceGetattr(molSystem, 'chains')
            del parentDict[oldCode]
            parentDict[newCode] = apiChain
            forceSetattr(apiChain, 'isModified', True)

    def _apiDisconnectFromMolecule(self):
        """Sever the API link between self and an API Molecule instance
        Used by _NewChain and when upgrading to 3.3.0 project
        """
        apiChain = self._apiChain
        apiMolecule = apiChain.molecule
        if apiMolecule is not None and apiChain in apiMolecule.chains:
            forceSetattr(apiChain, 'molecule', None)
            forceSetattr(apiMolecule, 'chains', set())

    # GWV 15/12/24: moved up to be in a more logical place
    # @renameObject()
    # @logCommand(get='self')
    # def rename(self, value: str):
    #     """Rename Chain, changing its name and pid.
    #     """
    #     if (_molecularTemplate := self._molecularTemplate) is None:
    #         raise RuntimeError(f'Unable to get associated _MolecularTemplate instance')
    #
    #     if self.nmrChain:
    #         getLogger().warning(f'{self.__class__.__name__}.rename will lose or change the assigned nmrChain')
    #
    #     newName = self._uniqueName(parent=self.project, name=value)
    #
    #     # rename functions from here; renameDecorator will handle undo-ing and notifier blanking
    #     # and subsequent firing
    #     oldName = self.name
    #     # do not use self.name = newName, as this causes infinite recursion!
    #     # _apiRename will do all API admin
    #     self._apiRename(newName)
    #     self._resetIds(recursive=True)
    #     # rename the associated _MolecularTemplate instance
    #     _molecularTemplate.rename(newName)
    #
    #     return (oldName, newName)


#=========================================================================================
# new<Object> and other methods
# Call appropriate routines in their respective locations
#=========================================================================================

@newObjectList((Chain.className, _MolecularTemplate.className))
def _newChain(project: Project,
              name: str | None = None,
              sequence: list = (),
              startNumber: int = 1,
              moleculeType: str | None = None,
              isCyclic: bool = False,
              useNefAtomNomenclature: bool = True,
              comment: str | None = None
              ):
    """Create a new Chain instance as defined by the sequence
    :param project: the Project instance
    :param str name: name for new chain (optional; defaults to next available from (A, B, C, ...)
    :param sequence: a Sequence[str] or str of one-letter codes defining the chain
    :param int startNumber: number of first residue in sequence
    :param str moleculeType: molecule type; i.e. ('protein','DNA', 'RNA' or other).
    :param useNefAtomNomenclature: flag to define NEF atom nomenclature to be used,
                                   rather than only IUPAC-defined atoms (default=True)
    :param str comment: comment for new chain (optional)
    """
    from ccpn.core.Residue import _newResidue
    from ccpn.core.lib.MoleculeLib import _nextChainCode

    # name, i.e. the chain name
    name = Chain._uniqueName(parent=project, name=name) \
                if name else _nextChainCode(project=project)

    apiProject = project._wrappedData
    apiMolSystem = apiProject.molSystem

    # first create the polymer without any residue definitions.
    # Thus, when we make the chain, no residues are automatically
    # added.
    _template = _newMolecularTemplate(
            project=project,
            name=name,
            comment=f'_MolecularTemplate for Chain {name}',
    )

    # Create the new Chain; since apiMolecule has no residue definitions,
    # it will be an empty chain
    apiMolecule = _template._apiMolecule
    newApiChain = apiMolSystem.newChain(molecule=apiMolecule,
                                        code=name,
                                        )

    if (result := Chain._newInstanceFromApiData(apiObj=newApiChain, project=project)) is None:
        raise RuntimeError('Unable to generate new Chain item')
    if comment:
        result.comment = comment

    # Now define the sequence
    _template.defineSequence(moleculeType = moleculeType,
                           sequence = sequence,
                           isCyclic = isCyclic,
                           startNumber = startNumber,
                           )

    # And add the Residues and Atoms as defined by _MolecularTemplate
    for apiMolResidue in _template._apiMolResidues:
        _newResidue(result, apiMolResidue, useNefAtomNomenclature=useNefAtomNomenclature)

    # Cannot put things on the undo stack because of _checkDelete()
    # in ccpnmodel/ccpncore/api/ccp/molecule/Molecule.py,
    # if apiMolecule.chains is set.
    # Deleting apiChain fails because of its molecule reference.

    # Hence, unset these cross-references in the model and use
    # association by name from hereon
    result._apiDisconnectFromMolecule()

    return (result, _template)


@newObject(Chain)
def _createChainFromSubstance(self: Substance,
                              shortName: str = None,
                              role: str = None,
                              comment: str = None,
                              expandFromAtomSets: bool = True,
                              addPseudoAtoms: bool = True,
                              addNonstereoAtoms: bool = True,
                              ) -> Chain:
    """Create new Chain that matches Substance

    :param shortName:
    :param role:
    :param comment: optional comment string
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
        raise ValueError(f"{previous.pid} already exists")

    newApiChain = apiMolSystem.newChain(molecule=apiMolecule, code=shortName, role=role,
                                        details=comment)
    # if (result := Chain._newInstanceFromApiData(apiObj=newApiChain)) is None:
    # need to restore the complete chain-tree structure
    if (result := AbstractWrapperObject._restoreObject(project=self.project, apiObj=newApiChain)) is None:
        raise RuntimeError('Unable to generate new Chain item')

    # for residue in result.residues:
    #     # Necessary as CCPN V2 default protonation states do not match the NEF / V3 standard
    #     residue.resetVariantToDefault()

    if expandFromAtomSets:
        from ccpn.core.lib.MoleculeLib import expandChainAtoms

        expandChainAtoms(result,
                         replaceStarWithPercent=True,
                         addPseudoAtoms=addPseudoAtoms,
                         addNonstereoAtoms=addNonstereoAtoms,
                         setBoundsForAtomGroups=True,
                         atomNamingSystem='PDB_REMED',
                         pseudoNamingSystem='AQUA')

    return result


def _getChainFromSubstance(self: Substance, shortName: str = None, role: str = None,
                           comment: str = None, serial: int = None) -> Chain:
    """Get existing Chain that matches Substance

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

    # get the chain if it exists
    previous = self._project.getChain(shortName.translate(Pid.remapSeparators))
    return previous


#EJB 20181206: moved to Substance
# Substance.createChain = _createChainFromSubstance
# del _createChainFromSubstance

def _checkChemCompExists(project, ccpCode):
    memopsRoot = project._wrappedData.root
    if chemComp := memopsRoot.findFirstChemComp(ccpCode=ccpCode):
        return chemComp
    return


def _fetchChemCompFromFile(project, filePath):
    """
    Load a ChemComp from a xml file if not already present in the project, otherwise return the one available.
    :param project: v3 project object.
    :param filePath: xml file path  for the chemcomp. Xml filename must contain the same strings as defined  in the
    guid inside the file.
    :return: The API chemComp object
    """
    from ccpnmodel.ccpncore.xml.memops.Implementation import loadFromStream
    from ccpn.util.Path import aPath, joinPath
    from ccpn.framework.PathsAndUrls import CCPN_API_DIRECTORY

    filePathObj = aPath(filePath)
    memopsRoot = project._wrappedData.root
    basename = filePathObj.basename
    ll = basename.split('+')  # assuming the file is an old xml type with + separators or created from Chembuild.
    if len(ll) > 1:
        ccpCode = ll[1]
        chemComp = memopsRoot.findFirstChemComp(ccpCode=ccpCode)  # Check if the chemcomp is already loaded
        if chemComp:
            return chemComp
    topObjId = ll[-1]
    chemComp = memopsRoot.findFirstChemComp(topObjId=topObjId)  # Check if the chemcomp is already loaded
    if chemComp:
        getLogger().warning('A ChemComp with the same topObjId is already loaded. Returning the pre-existing.')
    else:
        with open(filePath) as stream:
            chemComp = loadFromStream(stream, topObject=memopsRoot, topObjId=topObjId, )
            #update the 3letterCode because is needed on  V3 for some reasons...
            if chemComp and not chemComp.code3Letter:
                chemComp.__dict__['code3Letter'] = chemComp.ccpCode.upper()
    # need to copy the xml file to the project to be reopened
    # Not sure why is not done automatically or about a better way of doing it
    chemCompProjectSubPath = aPath(CCPN_API_DIRECTORY) / 'ccp' / 'molecule' / 'ChemComp'
    chemCompProjectPath = joinPath(project.projectPath, chemCompProjectSubPath)
    filePathObj.copyFile(chemCompProjectPath, overwrite=True)
    return chemComp


def _newChainFromChemComp(project, chemComp,
                          chainCode: str = None,
                          expandFromAtomSets=True,
                          addPseudoAtoms=False,
                          addNonstereoAtoms=False,
                          ):
    """
    :param project:
    :param chemComp: the chemComp object. Use _fetchChemCompFromFile(project, chemCompFilePath)
    :param chainCode: str. the code that will appear on sidebar.

    :return: A new chain containing only one residue corresponding to the small molecule and its atoms.
            Atoms are named as defined in the chemComp file.
            Residue name is set from the chemComp ccpCode.
            Note. Also a substance will be added in the project.

    """
    if chemComp:
        with undoBlock():
            root = project._wrappedData.root
            moleculeName = chemComp.ccpCode
            while root.findFirstMolecule(name=moleculeName):
                moleculeName = f'{moleculeName}_1'
            molecule = project._wrappedData.root.newMolecule(name=moleculeName)
            chemCompVar = (chemComp.findFirstChemCompVar(linking='none') or chemComp.findFirstChemCompVar())
            molResidue = molecule.newMolResidue(seqCode=1, chemCompVar=chemCompVar)
            refSampleComponentStore = project._wrappedData.sampleStore.refSampleComponentStore
            mcompp = refSampleComponentStore.newMolComponent(name=moleculeName)
            # will need to add to mcompp all possible info we can harvest from the chemcomp. This will appear in the substance
            # create a v3 chain. which is not frozen to changes.
            apiMolSystem = project._wrappedData.molSystem
            chainCode = Chain._uniqueName(project, name=chainCode)
            newApiChain = apiMolSystem.newChain(molecule=molecule, code=chainCode)
            chain = project._data2Obj[newApiChain]
            if expandFromAtomSets:
                from ccpn.core.lib.MoleculeLib import expandChainAtoms

                expandChainAtoms(chain,
                                 replaceStarWithPercent=True,
                                 addPseudoAtoms=addPseudoAtoms,
                                 addNonstereoAtoms=addNonstereoAtoms,
                                 setBoundsForAtomGroups=True,
                                 )

            return chain


def _cloneChain(chain: Chain, newName: str = None, useNefAtomNomenclature: bool = True) -> Chain:
    """Make copy of chain with newName (defaults to next chain code A, B, C, ...)
    :param chain: the Chain instance to be cloned
    :param newName: the new name for the cloned chain
    :param useNefAtomNomenclature: Flag to use NefAtomNomenclature (defaults to True)
    :return a Chain instance
    """
    #TODO-DEVELOP: deal with bonds
    from ccpn.core.lib.MoleculeLib import _nextChainCode

    project = chain.project

    # name, i.e. the chain name
    _name = Chain._uniqueName(parent=project, name=newName) \
                if newName else _nextChainCode(project=project)

    _sequence = [res.ccpCode for res in chain.residues]
    result = _newChain(project,
                       name=_name,
                       sequence=_sequence,
                       startNumber=chain.startNumber,
                       moleculeType=chain.moleculeType,
                       isCyclic=chain.isCyclic,
                       useNefAtomNomenclature=useNefAtomNomenclature,
                       comment=f'Clone of {chain}'
    )

    return result


#=========================================================================================
# getter's
#=========================================================================================
#TODO-DEVELOP: remove these

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
