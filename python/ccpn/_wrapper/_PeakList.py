"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
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

from ccpn._wrapper._AbstractWrapperClass import AbstractWrapperClass
from ccpn._wrapper._Project import Project
from ccpn._wrapper._Spectrum import Spectrum
from ccpncore.api.ccp.nmr.Nmr import PeakList as Ccpn_PeakList


class PeakList(AbstractWrapperClass):
  """Peak List."""
  
  #: Short class name, for PID.
  shortClassName = 'PL'

  #: Name of plural link to instances of class
  _pluralLinkName = 'peakLists'
  
  #: List of child classes.
  _childClasses = []
  

  # CCPN properties  
  @property
  def ccpnPeakList(self) -> Ccpn_PeakList:
    """ CCPN peakLists matching PeakList"""
    return self._wrappedData
    
  @property
  def id(self) -> str:
    """id string - serial number converted to string"""
    return str(self._wrappedData.serial)

  @property
  def serial(self) -> int:
    """serial number, key attribute for PeakList"""
    return self._wrappedData.serial
    
  @property
  def _parent(self) -> Spectrum:
    """Parent (containing) object."""
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

  # NBNB WILL NOT WORK until we implement the ShiftList class
  @property
  def shiftList(self) -> AbstractWrapperClass:
    ccpn_shiftList = self._wrappedData.shiftList
    if ccpn_shiftList is None:
      return None
    else:
      return self._project._data2Obj[ccpn_shiftList]

  @shiftList.setter
  def shiftList(self, value:AbstractWrapperClass):
    if value is None:
      self._wrappedData.shiftList = None
    else:
      self._wrappedData.shiftList = value._wrappedData

    
    
  # Implementation functions
  @classmethod
  def _getAllWrappedData(cls, parent: Spectrum)-> list:
    """get wrappedData (PeakLists) for all PeakList children of parent Spectrum"""
    return parent._wrappedData.sortedPeakLists()

# Connections to parents:
Spectrum._childClasses.append(PeakList)

def newPeakList(parent:Spectrum,name:str=None, comment:str=None,
             isSimulated:bool=False) -> PeakList:
  """Create new child PeakList"""
  ccpnDataSource = parent._wrappedData
  ccpnDataSource.newPeakList(name=name, details=comment, isSimulated=isSimulated)

Spectrum.newPeakList = newPeakList

# Notifiers:
className = Ccpn_PeakList._metaclass.qualifiedName()
Project._apiNotifiers.extend(
  ( ('_newObject', {'cls':PeakList}, className, '__init__'),
    ('_finaliseDelete', {}, className, 'delete')
  )
)
