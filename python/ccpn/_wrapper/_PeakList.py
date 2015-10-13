"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (www.ccpn.ac.uk) 2014 - $Date$"
__credits__ = "Wayne Boucher, Rasmus H Fogh, Simon P Skinner, Geerten W Vuister"
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

from ccpn import AbstractWrapperObject
from ccpn import Project
from ccpn import Spectrum
from ccpn import ChemicalShiftList
from ccpncore.api.ccp.nmr.Nmr import PeakList as ApiPeakList


class PeakList(AbstractWrapperObject):
  """Peak List."""
  
  #: Short class name, for PID.
  shortClassName = 'PL'
  # Attribute it necessary as subclasses must use superclass className
  className = 'PeakList'

  #: Name of plural link to instances of class
  _pluralLinkName = 'peakLists'
  
  #: List of child classes.
  _childClasses = []

  # CCPN properties  
  @property
  def _apiPeakList(self) -> ApiPeakList:
    """ API peakLists matching PeakList"""
    return self._wrappedData
    
  @property
  def _key(self) -> str:
    """id string - serial number converted to string"""
    return str(self._wrappedData.serial)

  @property
  def serial(self) -> int:
    """serial number, key attribute for PeakList"""
    return self._wrappedData.serial
    
  @property
  def _parent(self) -> Spectrum:
    """Spectrum containing Peaklist."""
    return  self._project._data2Obj[self._wrappedData.dataSource]
  
  spectrum = _parent
  
  @property
  def name(self) -> str:
    """name of PeakList"""
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

  @property
  def isSimulated(self) -> bool:
    """Is peakList simulated"""
    return self._wrappedData.isSimulated

  @isSimulated.setter
  def isSimulated(self, value:bool):
    self._wrappedData.isSimulated = value

  @property
  def chemicalShiftList(self) -> ChemicalShiftList:
    """ChemicalShiftList associated with PeakList."""
    return self._project._data2Obj.get(self._wrappedData.shiftList)

  @chemicalShiftList.setter
  def chemicalShiftList(self, value):

    value = self.getByPid(value) if isinstance(value, str) else value
    apiPeakList = self._wrappedData
    apiPeakList.shiftList = None if value is None else value._wrappedData
    
  # Implementation functions
  @classmethod
  def _getAllWrappedData(cls, parent: Spectrum)-> list:
    """get wrappedData (PeakLists) for all PeakList children of parent Spectrum"""
    return parent._wrappedData.sortedPeakLists()

# Connections to parents:
Spectrum._childClasses.append(PeakList)

def newPeakList(self:Spectrum,name:str=None, comment:str=None,
             isSimulated:bool=False) -> PeakList:
  """Create new child PeakList"""
  apiDataSource = self._wrappedData
  obj = apiDataSource.newPeakList(name=name, details=comment, isSimulated=isSimulated)
  return self._project._data2Obj.get(obj)

Spectrum.newPeakList = newPeakList

# Notifiers:
className = ApiPeakList._metaclass.qualifiedName()
Project._apiNotifiers.extend(
  ( ('_newObject', {'cls':PeakList}, className, '__init__'),
    ('_finaliseDelete', {}, className, 'delete'),
    ('_finaliseUnDelete', {}, className, 'undelete'),
  )
)
