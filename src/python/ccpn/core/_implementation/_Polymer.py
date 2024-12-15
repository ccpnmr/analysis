"""
This class defines the Polymer object: a class to hold
polymer information, i.e. the sequence of residues and
their topology.
Currently maintained by the API as a Molecule instance
and associated ChemComps.
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (https://www.ccpn.ac.uk) 2014 - 2024"
__credits__ = ("Ed Brooksbank, Morgan Hayward, Victoria A Higman, Luca Mureddu, Eliza Płoskoń",
               "Timothy J Ragan, Brian O Smith, Daniel Thompson",
               "Gary S Thompson & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license",
               )
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y"
                )
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Geerten Vuister $"
__dateModified__ = "$dateModified: 2024-12-15 18:51:29 +0000 (Sun, December 15, 2024) $"
__version__ = "$Revision: 3.3.0.develop $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: geertenv $"
__date__ = "$Date: 2024-12-04 9:42:30 +0100 (Wed, December 4, 2024) $"
#=========================================================================================
# Start of code
#=========================================================================================
#
from typing import Tuple, Optional, Union, Sequence, List
from functools import partial

# from ccpnmodel.ccpncore.lib.CopyData import copySubTree
# from ccpnmodel.ccpncore.api.ccp.molecule.MolSystem import Chain as ApiChain
from ccpnmodel.ccpncore.api.ccp.molecule.Molecule import Molecule as ApiMolecule
# from ccpnmodel.ccpncore.lib.molecule.MoleculeModify import createMolecule


from ccpn.core._implementation.AbstractWrapperObject import AbstractWrapperObject
from ccpn.core.Project import Project
from ccpn.core.lib.ContextManagers import newObject, renameObject, undoBlock, inactivity, undoStack, \
    apiNotificationBlanking
from ccpn.core.lib import Pid
from ccpn.core.lib.forceAttribute import forceSetattr, forceGetattr
from ccpn.core.lib.ChainLib import SequenceHandler, CCPCODE, ISVALID, ERRORS

from ccpn.framework.Application import getProject

from ccpn.util import Common as commonUtil
from ccpn.util.decorators import logCommand
from ccpn.util.Logging import getLogger



class _Polymer(AbstractWrapperObject):
    """A class to hold polymer information, i.e. the sequence of residues and
    their topology.
    """
    #-----------------------------------------------------------------------------------------

    #: Short class name, for PID.
    shortClassName = 'PM'
    # Attribute it necessary as subclasses must use superclass className
    className = '_Polymer'

    _parentClass = Project

    #: Name of plural link to instances of class
    _pluralLinkName = '_polymers'

    # the attribute name used by current
    _currentAttributeName = None

    #: List of child classes.
    _childClasses = []

    # Qualified name of matching API class
    _apiClassQualifiedName = ApiMolecule._metaclass.qualifiedName()

    _ignoreNewApiObjectCallback = True

    #-----------------------------------------------------------------------------------------

    @property
    def name(self):
        """:return The name of self
        """
        return self._wrappedData.name

    def _apiRename(self, newName: str):
        """Rename apiMolecule in place, fixing all stored references to its name
        Adapted from API renameChain in _ccp.molecule.MolSystem.Chain
        """
        apiMolecule = self._apiMolecule
        root = apiMolecule.root
        oldName = apiMolecule.name

        if root.findFirstMolecule(name=newName) is not None:
            raise ValueError(f"Cannot rename API Molecule, name {newName} already exists")

        root.__dict__['override'] = True
        try:
            # Fix apiMolecule
            parentDict = root.__dict__['molecules']
            del parentDict[oldName]
            apiMolecule.name = newName
            parentDict[newName] = apiMolecule

        finally:
            # reset override and set isModified
            root.__dict__['override'] = False
            apiMolecule.__dict__['isModified'] = True

    @renameObject()
    def rename(self, newName: str):
        """Rename self, changing its name and pid.
        """
        if newName == self.name:
            return
        oldName = self.name
        self._apiRename(newName)
        self._resetIds(recursive=False)
        return (oldName, newName)

    @property
    def moleculeType(self) -> str:
        """:return The type of molecule
        """
        return 'undefined' if self._apiMolecule.molType is None else self._apiMolecule.molType

    @property
    def molecularMass(self):
        """:return The molecular mass of the molecule
        """
        return self._wrappedData.molecularMass

    @property
    def isCyclic(self) -> bool:
        """:return True if sequence is cyclic, False otherwise
        """
        return self._apiMolecule.isStdCyclic

    def lock(self):
        """Lock self for any changes
        """
        self._apiMolecule.isFinalised = True

    @property
    def isLocked(self) -> bool:
        """:return the locked status of self
        """
        return self._apiMolecule.isFinalised

    @property
    def chain(self):
        """:return The Chain instance associated with self
        or None (if not present).
        """
        # local import to avoid cycles
        from ccpn.core.Chain import Chain
        _pid = Pid.createPid(Chain.shortClassName, self.name)
        return self.project.getByPid(_pid)

    #-----------------------------------------------------------------------------------------
    # Methods
    #-----------------------------------------------------------------------------------------

    def _deleteSequence(self):
        """Delete the polymer sequence
        Routine for undo-ing
        """
        _apiRoot = self._apiMolecule.root
        forceSetattr(_apiRoot, 'override', True)
        for apiRes in list(self._apiMolecule.sortedMolResidues()):
            apiRes.delete()
        forceSetattr(_apiRoot, 'override', False)

    def defineSequence(self,
                       moleculeType: str,
                       sequence: list | tuple,
                       isCyclic: bool = False,
                       startNumber: int = 1,
                       override: bool = False
                      ):
        """
        Add residue definitions from sequence, using SequenceHandler to parse.
        :param moleculeType: molecule type; one of ('protein', 'DNA', 'RNA', 'other')
        :param sequence: a sequence (list, tuple, str) of molecule type; see chain for details
        :return self
        """
        if self.isLocked and not override:
            raise RuntimeError(f'Cannot define the sequence without unlocking {self}')

        # Parse the sequence
        sequenceHandler: SequenceHandler = SequenceHandler(self.project, moleculeType=moleculeType)
        ccpCodes:list = []
        if sequence is not None:
            # parse the sequence  --> list of ccpCodes
            sequenceMap: dict = sequenceHandler.parseSequence(sequence)
            if not sequenceMap[ISVALID]:
                errorsIndices = sequenceMap.get(ERRORS, [])
                errors = ', '.join(map(str, errorsIndices))
                msg = f'The given sequence is not valid. Found errors at positions(s): {errors}'
                raise ValueError(msg)

            ccpCodes = sequenceMap.get(CCPCODE)

        if ccpCodes:
            with undoStack() as addUndoItem:
                # Have to unassign the 'chains' attribute and re-assign afterward
                # as we (might) have used apiMolecule to create a chain
                _apiChains = forceGetattr(self._apiMolecule, 'chains')
                forceSetattr(self._apiMolecule, 'chains', set())
                # method in ccpnmodel/ccpncore/lib/_ccp/molecule/Molecule/Molecule.py
                self._apiMolecule.extendMolResidues( sequence=ccpCodes,
                                                     molType=moleculeType,
                                                     startNumber=startNumber,
                                                     isCyclic=isCyclic
                                                    )
                forceSetattr(self._apiMolecule, 'chains', _apiChains)

                addUndoItem(undo=self._deleteSequence,
                            redo=partial(self.defineSequence,
                                 moleculeType=moleculeType,
                                 sequence=sequence,
                                 isCyclic=isCyclic,
                                 startNumber=startNumber,
                                 override=True,
                                 )
                )

                self.lock()

        return self

    #-----------------------------------------------------------------------------------------
    # CCPN properties
    #-----------------------------------------------------------------------------------------

    # For debugging purposes
    def __init__(self, project: 'Project', wrappedData):
        super().__init__(project, wrappedData)

    @classmethod
    def _getAllWrappedData(cls, parent: Project) -> list:
        """get wrappedData for all _Polymer children of the
        root parent project; i.e. apiNmrProject.root
        """
        root = parent._wrappedData.root
        return [] if root is None else root.sortedMolecules()

    @property
    def _apiMolecule(self) -> ApiMolecule:
        """ API Molecule instance"""
        return self._wrappedData

    @property
    def _apiMolResidues(self) -> list:
        """:return: the list of API MolResidues instances
        """
        return list(self._apiMolecule.sortedMolResidues())

    def _getApiMolResidue(self, seqId: str | int):
        """:return: the API MolResidue with seqId or None if it does not exist
        """
        _molResiduesDict = dict((str(mr.seqCode), mr) for mr in self._apiMolResidues)
        return _molResiduesDict.get(str(seqId), None)

    @property
    def _key(self) -> str:
        """Residue ID. Identical to name. Characters translated for pid"""
        return self._wrappedData.name.translate(Pid.remapSeparators)

    @property
    def _localCcpnSortKey(self) -> tuple:
        """Local sorting key, in context of parent."""
        return (self._wrappedData._uniqueId,)

    @property
    def _parent(self) -> Project:
        """Project containing Polymer instance.
        """
        return getProject()

    #-----------------------------------------------------------------------------------------

    def __len__(self) -> int:
        return len(self._apiMolResidues)

    def __str__(self):
        _locked = 'locked' if self.isLocked else 'unlocked'
        return f'<{self.pid} ({self.moleculeType}, {_locked})>'

    __repr__ = __str__


#=========================================================================================
# New<object> methods
#=========================================================================================

@newObject(_Polymer)
def _newPolymer(project: Project, name: str, comment: str = None) -> _Polymer:
    """Create a new _Polymer instance
    """
    apiProject = project._wrappedData

    # check if name exists
    if (_dummy := apiProject.root.findFirstMolecule(name=name)) is not None:
        raise ValueError(f'Unable to generate API Molecule instance; {name!r} already exists')

    apiMolecule = apiProject.root.newMolecule(name=name)

    if (result := _Polymer._newInstanceFromApiData(apiObj=apiMolecule, project=project)) is None:
        raise RuntimeError(f'Unable to generate _Polymer instance {name!r}')

    if comment:
        # avoid triggering logging, notification, ...
        with inactivity():
            apiMolecule.details = comment

    return result
