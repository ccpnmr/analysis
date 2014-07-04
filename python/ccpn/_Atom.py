
from ccpn._AbstractWrapperClass import AbstractWrapperClass
from ccpn._Project import Project
from ccpn._Residue import Residue
from ccpncore.api.ccp.molecule.MolSystem import Atom as Ccpn_Atom

import array as array

# NBNB TBD add settable linkedAtoms link for non-ChemCOmp links

class Atom(AbstractWrapperClass):
  """Molecular Atom."""
  
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
  def name(self) -> str:
    """Atom name string (e.g. 'HA')"""
    return self._wrappedData.name

  id = name

    
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
