
from ccpn._AbstractWrapperClass import AbstractWrapperClass
from ccpn._Project import Project
from ccpncore.api.ccp.molecule.MolSystem import MolSystem as Ccpn_MolSystem


class Molecule(AbstractWrapperClass):
  """Molecule or complex, composed of chains."""
  
  # Short class name, for PID.
  shortClassName = 'MO'

  # Name of plural link to instances of class
  _pluralLinkName = 'molecules'
  
  # List of child classes. 
  _childClasses = []
  
  #NBNB TODO add atom links code some time.
  

  # CCPN properties  
  @property
  def ccpnMolSystem(self) -> Ccpn_MolSystem:
    """ CCPN molsystem matching Molecule"""
    return self._wrappedData
  
  
  # @property
  # def id(self) -> str:
  #   """Molecule id: shortName"""
  #   return self._wrappedData.code
    
  @property
  def id(self) -> str:
    """short form of name, used for id"""
    return self._wrappedData.code

  shortName = id
    
  @property
  def _parent(self) -> Project:
    """Parent (containing) object."""
    return self._project
  
  project = _parent
  
  @property
  def name(self) -> str:
    """name of Molecule"""
    return self._wrappedData.name
    
  @name.setter
  def name(self, value:str):
    self._wrappedData.name = value
  
  @property
  def comment(self) -> str:
    """Free-form text comment"""
    return self._wrappedData.details
    
  @comment.setter
  def comment(self, value:str):
    self._wrappedData.details = value
    
    
  # Implementation functions
  @classmethod
  def _getAllWrappedData(cls, parent: Project)-> list:
    """get wrappedData (MolSystems) for all Molecules children of parent Project"""
    return parent._wrappedData.root.sortedMolSystems()

# Connections to parents:
Project._childClasses.append(Molecule)

def newMolecule(parent:Project, shortName:str, name:str=None, 
                comment:str=None) -> Molecule:
  """Create new child Molecule"""
  ccpnProject = parent._wrappedData.root
  ccpnProject.newMolSystem(code=shortName, name=name, details=comment)

Project.newMolecule = newMolecule

# Notifiers:
className = Ccpn_MolSystem._metaclass.qualifiedName()
Project._apiNotifiers.extend(
  ( ('_newObject', {'cls':Molecule}, className, '__init__'),
    ('_finaliseDelete', {}, className, 'delete')
  )
)
