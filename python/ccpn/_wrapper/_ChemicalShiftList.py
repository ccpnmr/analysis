"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
from ccpncore.util import pid as Pid

__copyright__ = "Copyright (C) CCPN project (www.ccpn.ac.uk) 2014 - $Date$"
__credits__ = "Wayne Boucher, Rasmus H Fogh, Simon Skinner, Geerten Vuister"
__license__ = ("CCPN license. See www.ccpn.ac.uk/license"
              "or ccpncore.memops.Credits.CcpnLicense for license text")
__reference__ = ("For publications, please use reference from www.ccpn.ac.uk/license"
                " or ccpncore.memops.Credits.CcpNmrReference")

#=========================================================================================
# Last code modification:
#=========================================================================================
__author__ = "$Author$"
__date__ = "$Date$"
__version__ = "$Revision$"

#=========================================================================================
# Start of code
#=========================================================================================

from ccpn._wrapper._AbstractWrapperObject import AbstractWrapperObject
from ccpn._wrapper._Project import Project
from ccpncore.api.ccp.nmr.Nmr import ShiftList as ApiShiftList


class ChemicalShiftList(AbstractWrapperObject):
  """Chemical Shift list."""
  
  #: Short class name, for PID.
  shortClassName = 'CL'

  #: Name of plural link to instances of class
  _pluralLinkName = 'chemicalShiftLists'
  
  #: List of child classes.
  _childClasses = []

  # CCPN properties  
  @property
  def apiShiftList(self) -> ApiShiftList:
    """ CCPN ShiftList matching ChemicalShiftList"""
    return self._wrappedData
    
  @property
  def _key(self) -> str:
    """name, regularised as used for id"""
    return self._wrappedData.name.translate(Pid.remapSeparators)

  @property
  def serial(self) -> int:
    """Shift list name"""
    return self._wrappedData.name
    
  @property
  def _parent(self) -> Project:
    """Parent (containing) object."""
    return self._project
  
  @property
  def name(self) -> str:
    """name of ChemicalShiftList"""
    return self._wrappedData.name

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
  obj = parent._wrappedData.newShiftList(name=name, unit=unit, isSimulated=isSimulated,
                                         details=comment)
  return parent._data2Obj.get(obj)

Project.newChemicalShiftList = newChemicalShiftList

# Notifiers:
className = ApiShiftList._metaclass.qualifiedName()
Project._apiNotifiers.extend(
  ( ('_newObject', {'cls':ChemicalShiftList}, className, '__init__'),
    ('_finaliseDelete', {}, className, 'delete')
  )
)
