"""
Module Documentation here
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (https://www.ccpn.ac.uk) 2014 - 2023"
__credits__ = ("Ed Brooksbank, Joanna Fox, Victoria A Higman, Luca Mureddu, Eliza Płoskoń",
               "Timothy J Ragan, Brian O Smith, Gary S Thompson & Geerten W Vuister")
__licence__ = ("CCPN licence. See https://ccpn.ac.uk/software/licensing/")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, https://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2023-05-23 15:26:51 +0100 (Tue, May 23, 2023) $"
__version__ = "$Revision: 3.1.1 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Ed Brooksbank $"
__date__ = "$Date: 2023-05-19 17:54:26 +0100 (Fri, May 19, 2023) $"
#=========================================================================================
# Start of code
#=========================================================================================

from typing import Sequence, Union, Optional, Tuple

from ccpn.core.Project import Project
from ccpn.core.Atom import Atom
from ccpn.core.lib import Pid
from ccpn.core.lib.Util import AtomIdTuple
from ccpn.core._implementation.AbstractWrapperObject import AbstractWrapperObject
from ccpn.core.lib.ContextManagers import newObject, ccpNmrV3CoreSetter
from ccpn.util.Logging import getLogger
from ccpn.util import Common as commonUtil
from ccpn.util.decorators import logCommand
from ccpnmodel.ccpncore.api.ccp.molecule.MolSystem import GenericBond as ApiBond


class Bond(AbstractWrapperObject):
    """A molecular Bond."""

    #: Class name and Short class name, for PID.
    shortClassName = 'MB'
    # Attribute it necessary as subclasses must use superclass className
    className = 'Bond'

    _parentClass = Project
    _parentClassName = Project.__class__.__name__ 

    # Name of plural link to instance of class
    _pluralLinkName = 'bonds'

    #: List of child classes.
    _childClasses = []

    # Qualified name of matching API class
    _apiClassQualifiedName = ApiBond._metaclass.qualifiedName()

    # CCPN properties
    @property
    def _apiBond(self) -> ApiBond:
        """CCPN bond matching Bond."""
        return self._wrappedData

    @property
    def _key(self) -> str:
        """Bond name string used for ID.
        """
        return Pid.IDDASH.join([atm.id for atm in self.atoms])

    @property
    def _idTuple(self) -> Tuple:
        """ID as chainCode, sequenceCode, residueType, atomName namedtuple pair for the atoms comprising the bond.
        Unlike the _id and key, these do NOT have reserved characters mapped to '^'
        _idTuple replaces empty strings with None.
        """
        ll = [atm._idTuple for atm in self.atoms]
        return tuple(x or None for atm in ll for x in atm)

    @property
    def _parent(self) -> Project:
        """Project containing Bond."""
        return self._project

    project = _parent

    @property
    def atoms(self) -> Tuple[Atom]:
        """Get/set the atoms in the bond.
        """
        getDataObj = self._project._data2Obj.get
        return tuple(getDataObj(atm) for atm in self._wrappedData.sortedAtoms())

    @property
    def bondType(self) -> str:
        """Free-form text bondType.
        """
        return self._wrappedData.bondType

    @bondType.setter
    @logCommand(get='self', isProperty=True)
    @ccpNmrV3CoreSetter()
    def bondType(self, value: str):
        """set optional bondType.
        """
        if value and isinstance(value, str):
            self._wrappedData.setBondType(value)

        else:
            raise ValueError("bondType must be a string.")
        
    #=========================================================================================
    # Implementation functions
    #=========================================================================================

    @classmethod
    def _getAllWrappedData(cls, parent: Project) -> list:
        """get wrappedData (MolSystem.GenericBonds) for all Bond children of parent Project.
        """
        molSystem = parent._wrappedData.molSystem
        return [] if molSystem is None else molSystem.sortedGenericBonds()

    def _finaliseAction(self, action: str, **actionKwds):
        """Subclassed to handle delete/create.
        """
        if action == 'delete':
            # store the old hierarchy information - may be required for deferred notifiers
            self._oldAtoms = self.atoms
        elif action == 'create':
            self._oldAtoms = None

        if not super()._finaliseAction(action, **actionKwds):
            return

    #=========================================================================================
    # CCPN functions
    #=========================================================================================

    #=========================================================================================
    # new<Object> and other methods
    # Call appropriate routines in their respective locations
    #=========================================================================================


#=========================================================================================
# Connections to parents:
#=========================================================================================

@newObject(Bond)
def _newBond(self: Project, atoms: Sequence[Union[Atom, str]], bondType: Optional[str] = None) -> Bond:
    """Create new Bond in project.

    See the Bond class for details.

    :return: a new Bond instance.
    """
    if not atoms:
        raise TypeError('atoms must be a sequence of Atoms')

    getByPid = self._project.getByPid
    atoms = list(filter(None, map(lambda x: getByPid(x) if isinstance(x, str) else x, atoms)))
    dd = {'atoms': [atm._wrappedData for atm in atoms]}

    if bondType is not None:
        if not isinstance(bondType, str):
            raise TypeError("bondType must be a string")
        dd['bondType'] = bondType

    apiBond = self._wrappedData.molSystem.newGenericBond(**dd)
    result = self._project._data2Obj[apiBond]
    if result is None:
        raise RuntimeError('Unable to generate new Bond item')

    return result
