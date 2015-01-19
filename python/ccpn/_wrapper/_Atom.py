"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (www.ccpn.ac.uk) 2014 - $Date: 2014-06-04 18:13:10 +0100 (Wed, 04 Jun 2014) $"
__credits__ = "Wayne Boucher, Rasmus H Fogh, Simon Skinner, Geerten Vuister"
__license__ = ("CCPN license. See www.ccpn.ac.uk/license"
              "or ccpncore.memops.Credits.CcpnLicense for license text")
__reference__ = ("For publications, please use reference from www.ccpn.ac.uk/license"
                " or ccpncore.memops.Credits.CcpNmrReference")

#=========================================================================================
# Last code modification:
#=========================================================================================
__author__ = "$Author: rhfogh $"
__date__ = "$Date: 2014-06-04 18:13:10 +0100 (Wed, 04 Jun 2014) $"
__version__ = "$Revision: 7686 $"

#=========================================================================================
# Start of code
#=========================================================================================

from ccpn._wrapper._AbstractWrapperObject import AbstractWrapperObject
from ccpn._wrapper._AbstractWrapperObject import AtomAssignment
from ccpn._wrapper._Project import Project
from ccpn._wrapper._Residue import Residue
from ccpncore.api.ccp.molecule.MolSystem import Atom as Ccpn_Atom
from ccpncore.lib import pid as Pid

# NBNB TBD add settable linkedAtoms link for non-ChemComp links ???

# NBNB TBD modify to deal with StructureAtoms and RestraintAtoms CombiClass?

class Atom(AbstractWrapperObject):
  """Molecular Atom.

  NBNB TBD rewrite - move to under Project, ... OR NOT ???"""

  #: Short class name, for PID.
  shortClassName = 'MA'

  #: Name of plural link to instances of class
  _pluralLinkName = 'atoms'
  
  #: List of child classes.
  _childClasses = []
  

  # CCPN properties  
  @property
  def ccpnAtom(self) -> Ccpn_Atom:
    """ CCPN atom matching Atom"""
    return self._wrappedData


  @property
  def _parent(self) -> Residue:
    """Parent (containing) object."""
    return self._project._data2Obj[self._wrappedData.residue]
  
  residue = _parent
    
  @property
  def id(self) -> str:
    """Atom name string (e.g. 'HA')"""
    return self._wrappedData.name.translate(Pid.remapSeparators)

  name = id

  @property
  def assignment(self) -> str:
    """AtomAssignment named tuple (chainCode, sequenceCode, residueType, name)"""
    return AtomAssignment( *(self._parent.assignment + (self.name,)))

  # Utility functions
    
  # Implementation functions
  @classmethod
  def _getAllWrappedData(cls, parent: Residue)-> list:
    """get wrappedData (MolSystem.Atoms) for all Atom children of parent Residue"""
    return parent._wrappedData.sortedAtoms()
    
    
def newAtom(parent:Residue, name:str) -> Atom:
  """Create new child Atom"""
  project = parent._project
  ccpnResidue = parent._wrappedData

  raise NotImplementedError("Creation of new Atoms not yet implemented")

  # NBNB TBD
  # requires changing of descriptor and chemCompVar,
  # interaction with structure ensembles, ...
    
    
    
# Connections to parents:

Residue._childClasses.append(Atom)

Residue.newAtom = newAtom

# Notifiers:
className = Ccpn_Atom._metaclass.qualifiedName()
Project._apiNotifiers.extend(
  ( ('_newObject', {'cls':Atom}, className, '__init__'),
    ('_finaliseDelete', {}, className, 'delete')
  )
)
