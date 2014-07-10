
from ccpn._wrapper._AbstractWrapperClass import AbstractWrapperClass
from ccpn._wrapper._Project import Project
from ccpncore.api.ccp.nmr.Nmr import ShiftList as Ccpn_ShiftList

class ChemicalShiftList(AbstractWrapperClass):
  """Chemical Shift list."""
  
  #: Short class name, for PID.
  shortClassName = 'CL'

  #: Name of plural link to instances of class
  _pluralLinkName = 'chemicalShiftLists'
  
  #: List of child classes.
  _childClasses = []

  # CCPN properties  
  @property
  def ccpnShiftList(self) -> Ccpn_ShiftList:
    """ CCPN ShiftList matching ChemicalShiftList"""
    return self._wrappedData
    
  @property
  def id(self) -> str:
    """identifier - serial num ber converted to string"""
    return str(self._wrappedData.serial)

  @property
  def serial(self) -> int:
    """Shift list serial number"""
    return self._wrappedData.serial
    
  @property
  def _parent(self) -> Project:
    """Parent (containing) object."""
    return self._project
  
  project = _parent
  
  @property
  def name(self) -> str:
    """name of ChemicalShiftList"""
    return self._wrappedData.name
    
  @name.setter
  def name(self, value:str):
    self._wrappedData.name = value

  @property
  def unit(self) -> str:
    """Measurement unit of ChemicalShiftList"""
    return self._wrappedData.unit

  @unit.setter
  def unit(self, value:str):
    self._wrappedData.unit = value

  @property
  def isSimulated(self) -> bool:
    """
    is CHemicalShiftList simulated?"""
    return self._wrappedData.isSimulated

  @isSimulated.setter
  def isSimulated(self, value:bool):
    self._wrappedData.isSimulated = value
  
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
    return [x for x in parent._wrappedData.sortedMeasurementLists()
            if x.className == 'ShiftList']

# Connections to parents:
Project._childClasses.append(ChemicalShiftList)

def newChemicalShiftList(parent:Project, name:str=None, unit:str='ppm',
                         isSimulated:bool=False, comment:str=None) -> ChemicalShiftList:
  """Create new child Molecule"""
  parent._wrappedData.newShiftList(name=name, unit=unit, isSimulated=isSimulated,
                                   dtails=comment)

Project.newChemicalShiftList = newChemicalShiftList

# Notifiers:
className = Ccpn_ShiftList._metaclass.qualifiedName()
Project._apiNotifiers.extend(
  ( ('_newObject', {'cls':ChemicalShiftList}, className, '__init__'),
    ('_finaliseDelete', {}, className, 'delete')
  )
)
