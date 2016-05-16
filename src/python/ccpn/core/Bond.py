"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (www.ccpn.ac.uk) 2014 - $Date$"
__credits__ = "Wayne Boucher, Rasmus H Fogh, Simon P Skinner, Geerten W Vuister"
__license__ = ("CCPN license. See www.ccpn.ac.uk/license"
              "or ccpnmodel.ccpncore.memops.Credits.CcpnLicense for license text")
__reference__ = ("For publications, please use reference from www.ccpn.ac.uk/license"
                " or ccpnmodel.ccpncore.memops.Credits.CcpNmrReference")

#=========================================================================================
# Last code modification:
#=========================================================================================
__author__ = "$Author$"
__date__ = "$Date$"
__version__ = "$Revision$"

#=========================================================================================
# Start of code
#=========================================================================================

from ccpn.util import Pid
from ccpn.core._implementation.AbstractWrapperObject import AbstractWrapperObject
from ccpn.core.Project import Project
from ccpn.core.Atom import Atom
from ccpnmodel.ccpncore.api.ccp.molecule.MolSystem import GenericBond as ApiGenericBond
from typing import Tuple, List


class Bond(AbstractWrapperObject):
  """Non-standard Chemical bond
  - used for bonds that are neither sequential nor defined in the residue template
  (e.g. disulfide bonds."""
  
  #: Short class name, for PID.
  shortClassName = 'MB'
  # Attribute it necessary as subclasses must use superclass className
  className = 'Bond'

  #: Name of plural link to instances of class
  _pluralLinkName = 'bonds'
  
  #: List of child classes.
  _childClasses = []

  # Qualified name of matching API class
  _apiClassQualifiedName = ApiGenericBond._metaclass.qualifiedName()
  

  # CCPN properties  
  @property
  def _apiGenericBond(self) -> ApiGenericBond:
    """ CCPN Project GenericBond"""
    return self._wrappedData

  @property
  def _key(self) -> str:
    """Residue local ID"""
    return Pid.IDSEP.join(x._id for x in self.atoms)

  @property
  def _parent(self) -> Project:
    """Parent (containing) object."""
    return self._project

  @property
  def bondType(self) -> str:
    """Bond type of bond"""
    return self._wrappedData.bondType

  @bondType.setter
  def bondType(self, value):
    self._wrappedData.bondType = value

  @property
  def atoms(self) -> Tuple[Atom, Atom]:
    """Atoms linked by Bond."""
    data2Obj = self._project._data2Obj
    return tuple(sorted(data2Obj[x] for x in self._wrappedData.atoms))

  # Implementation functions
  @classmethod
  def _getAllWrappedData(cls, parent:Project)-> list:
    """get wrappedData for all SpectrumGroups linked to NmrProject"""
    return parent._wrappedData.molSystem.sortedGenericBonds()


def _newBond(self:Project, atoms:Tuple[Atom,Atom]) -> Bond:
  """Create new SpectrumGroup"""
  return self._data2Obj.get(self._wrappedData.molSystem.newGenericBond(atoms=[x._wrappedData for x in atoms]))

    
# Connections to parents:
Project._childClasses.append(Bond)
Project.newBond = _newBond
del _newBond


# reverse link Atom.bonds
def getter(self:Atom) -> Tuple[Bond, ...]:
  data2Obj = self._project._data2Obj
  return tuple(sorted(data2Obj[x] for x in self._wrappedData.sortedGenericBonds()))

Atom.bonds = property(getter, None, None, "Non-standard bonds involving Atom.")
del getter

# Notifiers:
# NB The link to NmrAtom is immutable - does need a link notifier
# rename bonds when atom is renamed
Atom.setupCoreNotifier('rename', AbstractWrapperObject._finaliseRelatedObjectFromRename,
                          {'pathToObject':'bonds', 'action':'rename'})
