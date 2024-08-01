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
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2024-06-28 21:11:43 +0100 (Fri, June 28, 2024) $"
__version__ = "$Revision: 3.2.4 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from typing import Tuple, Optional, Union, Sequence
import numpy as np
from ccpn.core._implementation.AbstractWrapperObject import AbstractWrapperObject
from ccpn.core.Project import Project
from ccpn.core.Substance import Substance, SampleComponent
from ccpn.core.lib.ContextManagers import newObject, renameObject, undoBlock
from ccpn.core.lib import Pid
from ccpn.util import Common as commonUtil
from ccpn.util.decorators import logCommand
from ccpn.util.Logging import getLogger
from ccpnmodel.ccpncore.lib.CopyData import copySubTree
from ccpnmodel.ccpncore.api.ccp.molecule.MolSystem import Chain as ApiChain
from ccpnmodel.ccpncore.api.ccp.molecule import Molecule
from ccpnmodel.ccpncore.api.ccp.lims import Sample


NotFound = 'NotFound'  # used to create missing residues


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

    #=========================================================================================
    # CCPN properties
    #=========================================================================================

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
    def nmrChain(self) -> Optional['NmrChain']:
        """NmrChain to which Chain is assigned"""
        try:
            return self._project.getNmrChain(self._id)
        except Exception:
            return None

    # GWV 20181122: removed setters between Chain/NmrChain, Residue/NmrResidue, Atom/NmrAtom
    # @property.setter
    # def nmrChain(self, value: 'NmrChain'):
    #   if value is None:
    #     raise ValueError("nmrChain cannot be set to None")
    #   else:
    #     value.chain = self

    #=========================================================================================
    # property STUBS: hot-fixed later
    #=========================================================================================

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

    #=========================================================================================
    # getter STUBS: hot-fixed later
    #=========================================================================================

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

    #=========================================================================================
    # Core methods
    #=========================================================================================

    @logCommand(get='self', prefix='newChain=')
    def clone(self, shortName: str = None):
        """Make copy of chain.
        """
        # extracted as function below.
        # - fires a single notifier for the chain creation

        return _cloneChain(self, shortName=shortName)

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
                if c := residue.shortName:
                    sequence += c
        return sequence

    @property
    def sequenceCcpCodes(self):
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
        :return: list of sequence codes as integers. If a code cannot be interpreted as int it uses nan (float). This is to keep the same lenght as the residues and to allow
        numerical operations such as min, max or proper sorting.
        """
        codes = []
        for r in self.residues:
            try:
                sequenceCode = int(r.sequenceCode)
                codes.append(sequenceCode)
            except Exception as ex:
                codes.append(np.nan)
                getLogger().debug3(f'Cannot convert {r.sequenceCode} to integer. {ex}')
        return codes

    @property
    def hasAssignedAtoms(self) -> bool:
        """
        :return: True if any of its atoms have an assignment
        """
        return any(a.isAssigned for a in self.atoms)

    @logCommand(get='self')
    def toNmrChain(self, nmrChainName=None, ):
        """ Makes a new NmrChain from its ressidues/atoms.

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
            self.project._logger.warning(f"Error in creating an NmrChain from Chain: {e}")

    @property
    def chainType(self):
        return self._wrappedData.molecule.molType

    #=========================================================================================
    # Implementation functions
    #=========================================================================================

    @classmethod
    def _getAllWrappedData(cls, parent: Project) -> list:
        """get wrappedData (MolSystem.Chains) for all Chain children of parent NmrProject.molSystem"""
        molSystem = parent._wrappedData.molSystem
        return [] if molSystem is None else molSystem.sortedChains()

    @renameObject()
    @logCommand(get='self')
    def rename(self, value: str):
        """Rename Chain, changing its shortName and Pid.
        """
        if self.nmrChain:
            getLogger().warning(f'{self.__class__.__name__}.rename will lose or change the assigned nmrChain')

        name = self._uniqueName(parent=self.project, name=value)

        # rename functions from here
        oldName = self.shortName
        # self._oldPid = self.pid
        self._apiChain.renameChain(name)

        return (oldName,)


#=========================================================================================
# new<Object> and other methods
# Call appropriate routines in their respective locations
#=========================================================================================

@newObject(Chain)
def _newApiChain(self: Project, apiMolecule, shortName, role, comment):
    apiMolSystem = self._wrappedData.molSystem
    apiMolecule.isFinalised = True
    newApiChain = apiMolSystem.newChain(molecule=apiMolecule, code=shortName, role=role,
                                        details=comment)

    result = self._project._data2Obj[newApiChain]

    return result


def _getChain(self: Project, sequence: Union[str, Sequence[str]], compoundName: str = None,
              startNumber: int = 1, molType: str = None, isCyclic: bool = False,
              shortName: str = None, role: str = None, comment: str = None,
              serial: int = None) -> Chain:
    pass


# @newObject(Chain)
@undoBlock()
def _createChain(self: Project, compoundName: str = None,
                 sequence: str = None,
                 startNumber: int = 1, molType: str = None, isCyclic: bool = False,
                 shortName: str = None, role: str = None, comment: str = None,
                 expandFromAtomSets: bool = True,
                 addPseudoAtoms: bool = True,
                 addNonstereoAtoms: bool = True,
                 **kwargs,
                 ) -> Chain:
    """Create new chain from sequence of residue codes, using default variants.

    Automatically creates the corresponding polymer Substance if the compoundName is not already taken

    See the Chain class for details.
    :param sequence: str or list of str. Only for standard Residues. One of the following options:
                                - string of Code1Letter un-separated or space/comma-separated;
                                - string of Code3Letter/CcpCodes space/comma-separated; if Only one residue, must be given as a List
                                - list of single strings either of Code1Letter or Code3Letter or CcpCodes

    :param str compoundName: name of new Substance (e.g. 'Lysozyme') Defaults to 'Molecule_n
    :param str molType: molType ('protein','DNA', 'RNA'). Needed only if sequence is a string.
    :param int startNumber: number of first residue in sequence
    :param str shortName: shortName for new chain (optional)
    :param str role: role for new chain (optional)
    :param str comment: comment for new chain (optional)
    :param bool expandFromAtomSets: Create new Atoms corresponding to the ChemComp AtomSets definitions.
                Eg. H1, H2, H3 equivalent atoms will add a new H% atom. This will facilitate assignments workflows.
                See ccpn.core.lib.MoleculeLib.expandChainAtoms for details.
    :return: a new Chain instance.
    """
    from ccpn.core.lib.ChainLib import SequenceHandler, CCPCODE, ISVALID, ERRORS

    ccpCodes = []
    if sequence is not None:
        sequenceHandler = SequenceHandler(self.project, moleculeType=molType)
        sequenceMap = sequenceHandler.parseSequence(sequence)
        isValid = sequenceMap[ISVALID]
        if not isValid:
            errorsIndices = sequenceMap.get(ERRORS, [])
            errors = ', '.join(map(str, errorsIndices))
            msg = f'''The given sequence is not valid. Found errors at positions(s): {errors} '''
            raise ValueError(msg)
        ccpCodes = sequenceMap.get(CCPCODE)

    apiMolSystem = self._wrappedData.molSystem
    shortName = (
        Chain._uniqueName(parent=self, name=shortName)
        if shortName
        else apiMolSystem.nextChainCode()
    )
    previous = self._project.getChain(shortName.translate(Pid.remapSeparators))
    if previous is not None:
        raise ValueError(f"'{previous.longPid}' already exists")

    apiRefComponentStore = self._apiNmrProject.sampleStore.refSampleComponentStore
    # if compoundName is None:
    #     name = Substance._uniqueName(self.project)

    compoundName = Substance._uniqueName(self.project, name=compoundName)

    if apiRefComponentStore.findFirstComponent(name=compoundName) is None:
        name = Chain._uniqueName(parent=self, name=compoundName)

    else:
        raise ValueError(
                "Substance '%s' already exists. Try choosing a new molecule name.\n"
                "If you want to create a second identical chain from an existing substance, please clone the chain."
                % compoundName)

    substance = self.createPolymerSubstance(sequence=ccpCodes, name=name,
                                            startNumber=startNumber, molType=molType,
                                            isCyclic=isCyclic, comment=comment)

    apiMolecule = substance._apiSubstance.molecule

    # try:
    if True:
        result = _newApiChain(self, apiMolecule, shortName, role, comment)
        if result and expandFromAtomSets:
            from ccpn.core.lib.MoleculeLib import expandChainAtoms

            expandChainAtoms(result,
                             replaceStarWithPercent=True,
                             addPseudoAtoms=addPseudoAtoms,
                             addNonstereoAtoms=addNonstereoAtoms,
                             setBoundsForAtomGroups=True,
                             atomNamingSystem='PDB_REMED',
                             pseudoNamingSystem='AQUA')

    # except Exception as es:
    #     if substance:
    # clean up and remove the created substance
    # substance.delete()
    # raise RuntimeError('Unable to generate new Chain item') from es

    for residue in result.residues:
        # Necessary as CCPN V2 default protonation states do not match tne NEF / V3 standard
        residue.resetVariantToDefault()
        if not residue.residueType:
            with undoBlock():
                self.project.deleteObjects(*residue.atoms)

    return result


#EJB 20181206; moved to Project
# Project.createChain = _createChain
# del _createChain


@newObject(Chain)
def _createChainFromSubstance(self: Substance, shortName: str = None, role: str = None,
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
        raise ValueError(f"{previous.longPid} already exists")

    newApiChain = apiMolSystem.newChain(molecule=apiMolecule, code=shortName, role=role,
                                        details=comment)

    result = self._project._data2Obj[newApiChain]
    if result is None:
        raise RuntimeError('Unable to generate new Chain item')

    for residue in result.residues:
        # Necessary as CCPN V2 default protonation states do not match the NEF / V3 standard
        residue.resetVariantToDefault()

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


@newObject(Chain)
def _cloneChain(self: Chain, shortName: str = None):
    """Make copy of chain.
    """

    # _newApiObject no longer fires a ny notifiers. Single notifier is now handled by the decorator
    # FIXME This is broken for Non-Standard Residues. (probably never tested as it never implemented in V3)
    # Check if there are Non-standards. Clone is not yet available for Non-Standards
    from ccpn.core.lib.ChainLib import SequenceHandler

    chain = self
    sequenceHandler = SequenceHandler(chain.project, moleculeType=chain.chainType)
    standardCcpCodes = sequenceHandler.getAvailableCcpCodes(standardsOnly=True)
    ccpCodes = chain.sequenceCcpCodes
    nonStandardResidues = set()
    for ccpCode in ccpCodes:
        if ccpCode not in standardCcpCodes:
            nonStandardResidues.add(ccpCode)
    if len(nonStandardResidues) > 0:
        nstdResiduesStr = ', '.join(list(nonStandardResidues))
        raise ValueError(f'The chain {chain} contains Non-Standard Residue(s): "{nstdResiduesStr}". '
                         f'Clone is not yet available for this chain')

    apiChain = self._wrappedData
    apiMolSystem = apiChain.molSystem
    dataObj = self._project._data2Obj

    if shortName is None:
        shortName = apiMolSystem.nextChainCode()

    if apiMolSystem.findFirstChain(code=shortName) is not None:
        raise ValueError("Project already has one Chain with shortName %s" % shortName)

    topObjectParameters = {'code'            : shortName,
                           'pdbOneLetterCode': shortName[0]}

    with undoBlock():
        try:
            newApiChain = copySubTree(apiChain, apiMolSystem, maySkipCrosslinks=True,
                                      topObjectParameters=topObjectParameters)
        except Exception as es:
            # put in an error trap but now doesn't seem to re-create the error
            raise ValueError('Error cloning chain - %s' % str(es)) from es

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
                newAtoms[0].addInterAtomBond(newAtoms[1], apiGenericBond.bondType)

    return result


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
